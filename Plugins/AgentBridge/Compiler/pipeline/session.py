"""
Compiler Pipeline Session

职责：
  - 定义五阶段编排会话的数据结构
  - 提供 session.json 的序列化 / 反序列化
  - 提供阶段推进与阶段输入路径查询
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft7Validator


PLUGIN_DIR = Path(__file__).resolve().parents[2]
SESSION_SCHEMA_PATH = PLUGIN_DIR / "Schemas" / "compiler_session.schema.json"
SESSION_FILE_NAME = "session.json"
MIN_STAGE = 1
MAX_STAGE = 5
VALID_STATUSES = {"pending", "running", "completed", "failed"}


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


def _stage_key(stage_num: int) -> str:
    """将阶段号统一转换为 stage_1 ~ stage_5 键名。"""
    if stage_num < MIN_STAGE or stage_num > MAX_STAGE:
        raise ValueError(f"stage_num 必须在 {MIN_STAGE}-{MAX_STAGE} 之间，实际 {stage_num}")
    return f"stage_{stage_num}"


@dataclass
class CompilerSession:
    """Compiler 五阶段会话对象。"""

    session_id: str
    created_at: str
    gdd_path: str
    target_phase: str
    output_dir: str
    current_stage: int = MIN_STAGE
    stage_outputs: Dict[str, str] = field(default_factory=dict)
    status: str = "pending"

    def __post_init__(self) -> None:
        """基础字段校正与轻量自检。"""
        self.output_dir = str(Path(self.output_dir))
        if self.status not in VALID_STATUSES:
            raise ValueError(f"非法 status: {self.status}")
        _stage_key(self.current_stage)

    @property
    def session_path(self) -> Path:
        """session.json 的标准保存路径。"""
        return Path(self.output_dir) / SESSION_FILE_NAME

    def get_stage_output_path(self, stage_num: int) -> str | None:
        """获取指定阶段已登记的输出路径。"""
        return self.stage_outputs.get(_stage_key(stage_num))

    def has_stage_output(self, stage_num: int) -> bool:
        """检查某阶段产物是否已登记且路径真实存在。"""
        output_path = self.get_stage_output_path(stage_num)
        return bool(output_path and Path(output_path).exists())

    def get_stage_input_path(self, stage_num: int) -> str:
        """
        获取某阶段默认输入路径。

        Stage 1 没有上游 JSON，直接返回 GDD 路径。
        Stage 2-5 返回上一阶段的登记产物路径。
        """
        if stage_num <= MIN_STAGE:
            return self.gdd_path
        return self.stage_outputs.get(_stage_key(stage_num - 1), "")

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

        if self.current_stage < MAX_STAGE:
            self.current_stage += 1
            self.status = "pending"
        else:
            self.status = "completed"
        return True

    def to_dict(self) -> Dict[str, Any]:
        """导出为可序列化字典。"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "gdd_path": self.gdd_path,
            "target_phase": self.target_phase,
            "output_dir": self.output_dir,
            "current_stage": self.current_stage,
            "stage_outputs": dict(self.stage_outputs),
            "status": self.status,
        }

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
            payload = json.load(file)

        _validate_session_payload(payload)
        return cls(**payload)


def create_session(gdd_path: str, target_phase: str, output_dir: str) -> CompilerSession:
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
    )
