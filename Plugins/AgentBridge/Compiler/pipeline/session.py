"""
Compiler Pipeline Session

职责：
  - 定义五阶段编排会话的数据结构
  - 提供 session.json 的序列化 / 反序列化
  - 提供阶段推进与阶段输入路径查询
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from jsonschema import Draft7Validator


PLUGIN_DIR = Path(__file__).resolve().parents[2]
SESSION_SCHEMA_PATH = PLUGIN_DIR / "Schemas" / "compiler_session.schema.json"
SESSION_FILE_NAME = "session.json"
MIN_STAGE = 1
DEFAULT_SESSION_VERSION = "1.0"
SUPPORTED_SESSION_VERSIONS = {"1.0", "2.0"}
MAX_STAGE_BY_VERSION = {
    "1.0": 5,
    "2.0": 7,
}
MAX_STAGE = MAX_STAGE_BY_VERSION[DEFAULT_SESSION_VERSION]
VALID_STATUSES = {"pending", "running", "completed", "failed"}
VALID_GENERATOR_PROVIDERS = {"llm", "mcp_agent", "heuristic_fallback"}
RUN_ID_PATTERN = re.compile(r"^run-\d{8}-\d{6}-[0-9a-fA-F]{4,12}$")


def _load_session_schema() -> Dict[str, Any]:
    """加载 Compiler Session Schema。"""
    with SESSION_SCHEMA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _validate_session_payload(payload: Dict[str, Any]) -> None:
    """用 schema 校验 session 数据，不通过时抛出 ValueError。"""
    validator = Draft7Validator(_load_session_schema())
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    if not errors:
        return

    details = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        details.append(f"{location}: {error.message}")
    raise ValueError("CompilerSession schema 校验失败: " + " | ".join(details))


def _normalize_session_version(session_version: Optional[str]) -> str:
    """归一化 session_version；旧 session 缺失时按 v1.0 处理。"""
    version = session_version or DEFAULT_SESSION_VERSION
    if version not in SUPPORTED_SESSION_VERSIONS:
        raise ValueError(f"不支持的 session_version: {version}")
    return version


def get_max_stage(session_version: Optional[str] = None) -> int:
    """根据 session_version 返回当前管线最大阶段数。"""
    return MAX_STAGE_BY_VERSION[_normalize_session_version(session_version)]


def generate_run_id(now: Optional[datetime] = None) -> str:
    """生成 Phase 11 Run Workspace 使用的 run_id。"""
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    short_hash = uuid.uuid4().hex[:4]
    return f"run-{timestamp}-{short_hash}"


def _validate_run_id(run_id: str) -> None:
    """校验 run_id 是否符合 Phase 11 运行空间命名规范。"""
    if not RUN_ID_PATTERN.match(run_id):
        raise ValueError(
            "非法 run_id，必须符合 run-{yyyyMMdd}-{HHmmss}-{short_hash}，"
            f"实际 {run_id}"
        )


def _apply_legacy_defaults(payload: Dict[str, Any]) -> Dict[str, Any]:
    """给旧 session 补默认字段，保证缺失 session_version 时可读回。"""
    normalized = dict(payload)
    normalized.setdefault("session_version", DEFAULT_SESSION_VERSION)
    normalized.setdefault("fast_mode", False)
    return normalized


def _stage_key(stage_num: int, session_version: Optional[str] = None) -> str:
    """将阶段号统一转换为 stage_1 ~ stage_n 键名。"""
    max_stage = get_max_stage(session_version)
    if stage_num < MIN_STAGE or stage_num > max_stage:
        raise ValueError(f"stage_num 必须在 {MIN_STAGE}-{max_stage} 之间，实际 {stage_num}")
    return f"stage_{stage_num}"


@dataclass
class CompilerSession:
    """Compiler 会话对象，兼容 v1.0 五阶段与 v2.0 七阶段。"""

    session_id: str
    created_at: str
    gdd_path: str
    target_phase: str
    output_dir: str
    current_stage: int = MIN_STAGE
    stage_outputs: Dict[str, str] = field(default_factory=dict)
    status: str = "pending"
    session_version: str = DEFAULT_SESSION_VERSION
    run_id: Optional[str] = None
    fast_mode: bool = False
    generator_provider: Optional[str] = None

    def __post_init__(self) -> None:
        """基础字段校正与轻量自检。"""
        self.output_dir = str(Path(self.output_dir))
        self.session_version = _normalize_session_version(self.session_version)
        self.fast_mode = bool(self.fast_mode)

        if self.session_version == "2.0" and not self.run_id:
            self.run_id = generate_run_id()
        if self.run_id:
            _validate_run_id(self.run_id)

        if self.status not in VALID_STATUSES:
            raise ValueError(f"非法 status: {self.status}")
        if self.generator_provider is not None and self.generator_provider not in VALID_GENERATOR_PROVIDERS:
            raise ValueError(f"非法 generator_provider: {self.generator_provider}")
        _stage_key(self.current_stage, self.session_version)

        for stage_name in self.stage_outputs:
            if not re.match(r"^stage_\d+$", stage_name):
                raise ValueError(f"非法 stage_outputs key: {stage_name}")
            stage_num = int(stage_name.split("_", 1)[1])
            _stage_key(stage_num, self.session_version)

    @property
    def max_stage(self) -> int:
        """当前 session 对应的最大阶段数。"""
        return get_max_stage(self.session_version)

    @property
    def is_promotable(self) -> bool:
        """判断当前 run 是否可 promote。fast_mode 或 heuristic_fallback 均不可 promote。"""
        if self.fast_mode:
            return False
        if self.generator_provider == "heuristic_fallback":
            return False
        return True

    @property
    def session_path(self) -> Path:
        """session.json 的标准保存路径。"""
        return Path(self.output_dir) / SESSION_FILE_NAME

    def get_stage_output_path(self, stage_num: int) -> str | None:
        """获取指定阶段已登记的输出路径。"""
        return self.stage_outputs.get(_stage_key(stage_num, self.session_version))

    def has_stage_output(self, stage_num: int) -> bool:
        """检查某阶段产物是否已登记且路径真实存在。"""
        output_path = self.get_stage_output_path(stage_num)
        return bool(output_path and Path(output_path).exists())

    def get_stage_input_path(self, stage_num: int) -> str:
        """
        获取某阶段默认输入路径。

        Stage 1 没有上游 JSON，直接返回 GDD 路径。
        Stage 2-N 返回上一阶段的登记产物路径。
        """
        if stage_num <= MIN_STAGE:
            return self.gdd_path
        _stage_key(stage_num, self.session_version)
        return self.stage_outputs.get(_stage_key(stage_num - 1, self.session_version), "")

    def advance_stage(self) -> bool:
        """
        在当前阶段产物存在时推进到下一阶段。

        返回：
          - True：推进成功，或最后一阶段完成后已标记 completed
          - False：当前阶段产物不存在，无法推进
        """
        current_output = self.get_stage_output_path(self.current_stage)
        if not current_output or not Path(current_output).exists():
            return False

        if self.current_stage < self.max_stage:
            self.current_stage += 1
            self.status = "pending"
        else:
            self.status = "completed"
        return True

    def to_dict(self) -> Dict[str, Any]:
        """导出为可序列化字典。"""
        payload = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "gdd_path": self.gdd_path,
            "target_phase": self.target_phase,
            "output_dir": self.output_dir,
            "current_stage": self.current_stage,
            "stage_outputs": dict(self.stage_outputs),
            "status": self.status,
            "session_version": self.session_version,
            "fast_mode": self.fast_mode,
        }
        if self.run_id:
            payload["run_id"] = self.run_id
        if self.generator_provider:
            payload["generator_provider"] = self.generator_provider
        return payload

    def save(self, session_path: str | Path | None = None) -> str:
        """保存 session.json，并在写入前执行 schema 校验。"""
        target_path = Path(session_path) if session_path else self.session_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        payload = self.to_dict()
        _validate_session_payload(payload)

        with target_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        return str(target_path)

    @classmethod
    def load(cls, session_path: str | Path) -> "CompilerSession":
        """从 session.json 读回会话对象。"""
        target_path = Path(session_path)
        with target_path.open("r", encoding="utf-8") as file:
            payload = _apply_legacy_defaults(json.load(file))

        _validate_session_payload(payload)
        return cls(**payload)


def create_session(
    gdd_path: str,
    target_phase: str,
    output_dir: str,
    session_version: str = DEFAULT_SESSION_VERSION,
    run_id: Optional[str] = None,
    fast_mode: bool = False,
) -> CompilerSession:
    """创建一个新的 CompilerSession。"""
    return CompilerSession(
        session_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        gdd_path=gdd_path,
        target_phase=target_phase,
        output_dir=str(Path(output_dir)),
        current_stage=MIN_STAGE,
        stage_outputs={},
        status="pending",
        session_version=session_version,
        run_id=run_id,
        fast_mode=fast_mode,
    )
