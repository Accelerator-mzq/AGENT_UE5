# ForgeUE_codex Manifest 集成契约

> 本文档定义 AgentBridge 如何消费 ForgeUE_codex P4 流水线产出的 `UEAssetManifest`，把外部多模态资产生成结果接入本项目 UE5 执行链。

## 上游契约

来源项目：`D:/ClaudeProject/ForgeUE_codex`(独立 Python 包，与本项目同机部署)。

来源模块：`framework.engine_bridge.unreal.contract.manifest_builder.build_manifest`。

产物：每个 ForgeUE_codex run 在 `<UEProject>/Content/Generated/<run_id>/` 下写出三个文件——
- `manifest.json` —— `UEAssetManifest` 序列化(**必须**)
- `import_plan.json` —— `UEImportPlan` 序列化(可选)
- `evidence.json` —— 上游执行 evidence(本桥不消费)

支持的 schema_version：**`1.0.0`**。上游升级到 2.x 时桥会在 `parse_manifest` 早期 raise `ValueError`。

## asset_kind 覆盖范围

来源 `_KIND_MAP`(`manifest_builder.py`)：

| modality.shape | asset_kind | UE prefix |
|---|---|---|
| image.raster | texture | T_ |
| image.sprite_sheet | texture | T_ |
| audio.waveform | sound_wave | S_ |
| mesh.gltf/fbx/obj | static_mesh | SM_ |
| material.definition | material | M_ |
| video.mp4 | file_media_source | MS_ |

## 三种 bridge_mode

| mode | 状态 | 副作用 | 用途 |
|---|---|---|---|
| `simulated` | **已实现** | 无 | 契约校验、handoff_runner 单元测试、CI/CD 离线门禁 |
| `bridge_python` | NotImplementedError stub | 调 UE Python Editor API | 未来 milestone：在 UE Editor 进程内导入 |
| `bridge_rc_api` | NotImplementedError stub | 调 Remote Control API(30010) | 未来 milestone：远程触发导入 |

## 两种调用入口

### A. 通过 handoff_runner(标准入口)

在 `run_plan.workflow_sequence` 加一步 `workflow_type: "import_assets"`：

```json
{
  "step_id": "import_forgeue_run_p4_full",
  "workflow_type": "import_assets",
  "params": {
    "manifest_path": "<absolute path to manifest.json>",
    "plan_path": "<absolute path to import_plan.json>",
    "bridge_mode": "simulated"
  }
}
```

dispatch 入口：`Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py` 的 `execute_run_plan`。

### B. 独立 CLI(排查、ad-hoc 集成)

```bash
python Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py \
  --manifest <path-to-manifest.json> \
  [--plan <path-to-import_plan.json>] \
  [--bridge-mode simulated]
```

成功：JSON 到 stdout、exit 0。失败：错误到 stderr、exit 非 0。

## 跨项目部署约束

ForgeUE_codex 的 `UEAssetManifest` 设计**假定 payload 文件已经物理位于 `<UEProject>/Content/Generated/<run_id>/`**(见 `manifest_builder.py` 模块 docstring)。这意味着：

1. **同机部署**：ForgeUE_codex 的 `UEOutputTarget.project_root` 必须配置成本项目工程根 `D:/UnrealProjects/Mvpv4TestCodex/`。
2. **跨机部署**：需要在两机之间提前同步 `Content/Generated/<run_id>/` 目录，本桥不负责文件搬运。

## 未实现部分 / 后续工作

- `bridge_python`：进入 UE Editor 进程实现真正导入。预计落点：在 `Plugins/AgentBridge/Source/AgentBridge/Private/` 加 `ImportFromForgeUEManifest` 蓝图节点，桥到 Python `forgeue_manifest_importer.import_from_manifest(..., bridge_mode="bridge_python")`。
- `bridge_rc_api`：通过 `bridge.remote_control_client` 远程触发同样的导入。
- evidence 回写：当前桥只 read manifest + plan，**不消费 evidence.json**，也不写回成功/失败 evidence。后续可加 evidence cross-check(对比 ForgeUE_codex 上游 evidence 与本侧导入结果)。
- 资产清单覆盖：当前 5+1 种 asset_kind 都在 simulated 模式下走通用 `_simulate_asset`；bridge_python 接入时需要按 asset_kind 分派到 UE 对应导入器。

## 版本约束

- 本桥支持 manifest `schema_version == "1.0.0"`。
- 上游 ForgeUE_codex 升级 schema 时，本桥应同步更新 `_SUPPORTED_SCHEMA_VERSIONS` 集合(当前以单值字符串硬编码)。
- fixture 同步：`Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/` 下的 manifest/import_plan 是从 `D:/ClaudeProject/ForgeUE_codex/demo_artifacts/p4_demo/test_p4_full_pipeline_writes_m0/...` 复制的真实输出，上游变更时应重新复制(避免契约漂移)。
