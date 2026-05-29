# Baseline Realization Divergence — 落地证据

> 生成时间：2026-05-29
> 分支：fix/baseline-realization-divergence
> 任务：Task 1–4 完成

---

## 1. 改动综述

### Task 1（抽纯函数）
从 `_build_baseline_spec_fragment` 中抽出 `_selected_realization_from_converged(converged_pack)` 纯函数，处理三级键名回退（`chosen_candidate_name` → `chosen_candidate` → `selected_candidate_id`），并补充 4 条单元测试。

### Task 2（baseline 写入 selected_realization）
`_build_baseline_spec_fragment` baseline 分支：当 `realization_class == "realization_eligible"` 且 `converged_pack` 不为 None 时，写入 `selected_realization` 字段；`presence_only` 节点不写。新增 3 条测试。

### Task 3（去 HUD 硬编码）
`_build_discovered_fragment` 的 baseline 分支从硬编码 HUD 逻辑改为通过 `_capability_map(root_skill_contract)` 按 `capability_id` 动态查找 capability；同时将 `converged_pack` 传入 `_build_baseline_spec_fragment`。新增 2 条集成测试。

### Task 4（HUD required_elements 保留 + 回归证据）——本次
在 `_build_discovered_fragment` baseline 分支、拿到 capability 之后、调用 `_build_baseline_spec_fragment` 之前，插入 HUD 专属保留逻辑：当 `capability_id == "baseline-hud"` 时，从 `constraint_fields["ui.required_hud_fields"]["value"]` 读取硬约束值覆盖 capability 的 `required_elements`，使用 `{**capability, ...}` 生成新 dict 避免污染共享引用。更新测试 fixture 使 HUD capability 值与 constraint 值故意不同，验证保留行为确实生效。

---

## 2. HUD 语义保留证据

### 两来源不等（真实 run 数据）

| 来源 | required_elements |
|------|-------------------|
| `baseline_capabilities` HUD capability 自带值 | `['current_turn', 'current_player', 'player_cash', 'dice_result']` |
| `constraint_fields["ui.required_hud_fields"]["value"]`（旧语义锁定值） | `['current_player', 'player_cash', 'turn_number']` |

两者**不相等**。设计文档 §2.3/§3 裁定：HUD 的 `required_elements` 必须以 `constraint_fields` 锁定硬约束为准。

### 保留决策
Task 3 引入泛化路径后，若不加保留，HUD 产出的 `required_elements` 将静默变为 capability 自带值，违反 GDD 锁定约束。Task 4 加入 HUD 专属保留逻辑：

```python
# HUD 拥有 GDD 锁定的 required_hud_fields 硬约束，required_elements 以此为准
# （保留 Task 3 前语义，避免泛化后静默改变 HUD 产出）；其余 baseline 用 capability 自带值。
if node.get("capability_id") == "baseline-hud":
    hud_required = (
        root_skill_contract.get("constraint_fields", {})
        .get("ui.required_hud_fields", {})
        .get("value")
    )
    if hud_required is not None:
        # 用新 dict 覆盖，避免原地修改 _capability_map 缓存的共享引用
        capability = {**capability, "required_elements": hud_required}
```

**结论**：HUD 产出的 `required_elements` 仍为 `['current_player', 'player_cash', 'turn_number']`（constraint 锁定值），新增了 `selected_realization` 字段（由 converged_pack 驱动）。

---

## 3. 测试输出

```
PASS test_selected_realization_from_converged_maps_choices
PASS test_selected_realization_from_converged_empty
PASS test_selected_realization_from_converged_uses_fallback_key
PASS test_selected_realization_from_converged_third_level_fallback
PASS test_baseline_eligible_emits_selected_realization
PASS test_baseline_presence_only_no_selected_realization
PASS test_baseline_eligible_without_converged_pack_no_field
PASS test_discovered_baseline_uses_capability_by_id_not_hardcoded_hud
PASS test_discovered_baseline_hud_semantics_preserved

All 9 passed
```

---

## 4. 契约校验输出

```
[OK] Plugins\AgentBridge\Schemas\examples\forgeue_import_evidence_example.json
[OK] Plugins\AgentBridge\Schemas\examples\get_actor_bounds.example.json
[OK] Plugins\AgentBridge\Schemas\examples\get_actor_state.example.json
[OK] Plugins\AgentBridge\Schemas\examples\get_asset_metadata.example.json
[OK] Plugins\AgentBridge\Schemas\examples\get_component_state.example.json
[OK] Plugins\AgentBridge\Schemas\examples\get_current_project_state.example.json
[OK] Plugins\AgentBridge\Schemas\examples\get_dirty_assets.example.json
[OK] Plugins\AgentBridge\Schemas\examples\get_material_assignment.example.json
[OK] Plugins\AgentBridge\Schemas\examples\list_level_actors.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_batch_manifest.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_build_ir_v2.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_clarification_gate_report.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_converged_realization_pack.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_cross_review_report_v2.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_design_decision_log.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_design_space_report.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_naming_resolution_log.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_realization_candidates.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_reviewed_handoff_v3.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_root_skill_contract.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_run_comparison.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_skill_fragment_v2.example.json
[OK] Plugins\AgentBridge\Schemas\examples\phase11_skill_graph.example.json
[OK] Plugins\AgentBridge\Schemas\examples\reviewed_handoff_greenfield.example.json
[OK] Plugins\AgentBridge\Schemas\examples\run_map_check.example.json
[OK] Plugins\AgentBridge\Schemas\examples\run_plan_greenfield.example.json
[OK] Plugins\AgentBridge\Schemas\examples\write_operation_feedback.example.json

========== Summary ==========
Checked examples       : 27
Passed                 : 27
Failed                 : 0

[SUCCESS] 全部 example 校验通过，本地校验链正常。
```

---

## 5. 结论

- **发散落地达成**：`realization_eligible` baseline 节点在 `converged_pack` 存在时自动写入 `selected_realization`，`presence_only` 节点不受影响。
- **HUD 语义不变**：`required_elements` 继续来自 `constraint_fields` 锁定值 `['current_player', 'player_cash', 'turn_number']`，GDD 硬约束得到守护。
- **去硬编码完成**：非 HUD 的 baseline 节点（如 Audio Foundation）正确使用自身 capability 的 `required_elements`，不受 HUD 保留逻辑影响。
- **契约不破**：validate_examples --strict 27/27 通过，退出码 0。
- **测试回归**：9 条测试全部 PASS，含两条刻意让 HUD capability 值与 constraint 值不同的守护用例。
