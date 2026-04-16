# AGENT_UE5 Baseline Realization and Design Space Policy

## 1. 一句话结论

Baseline 域必须像 Gameplay 域一样，拥有 Design Space Discovery -> Realization Candidates -> Convergence 的正式路径；区别只在于 Baseline 域通常更保守、更强调 UX 与产品完整性。

---

## 2. Baseline 域的三类分法

### 2.1 Presence-Only Baseline Domains

只要求存在，不要求进入发散创造。

适用场景：
- GDD 对该项没有设计描述
- 该项与 gameplay 无强耦合
- 该项使用通用标准实现即可满足

产物：最小 Fragment（spec_fragments 中 realization_class = "presence_only"），design_decision_log 为空。

示例：Logo/Splash 页、基础退出逻辑

### 2.2 Realization-Eligible Baseline Domains

允许进入 Design Space Discovery。

适用场景：
- GDD 对该项有设计描述
- 该项与 gameplay 有耦合
- 该项影响 gameplay feel
- 用户要求创造性设计

产物：完整的 design_space_report 条目 + realization_candidates 条目 + converged 选择 + Fragment 含 design_decision_log。

示例：HUD 布局（因为内容取决于 gameplay 域）、主菜单（因为选项取决于游戏模式）

### 2.3 Clarification-Gated Baseline Domains

不宜擅自实现，需先确认。

适用场景：
- 目标平台未确定（影响输入映射、分辨率设置）
- 网络模式未确定（影响暂停语义、玩家列表 UI）
- 持久化策略未确定（影响设置保存、存档系统）

产物：Clarification Gate 中标记为 clarification_required，回答后升级为 presence_only 或 realization_eligible。

---

## 3. Baseline Domain Skill 结构

每个 Baseline Domain Skill 与 Gameplay Domain Skill 结构完全同构：

```
SkillTemplates/
  baseline/
    {baseline_name}/
      manifest.yaml
      system_prompt.md
      domain_prompt.md
      evaluator_prompt.md
      input_selector.yaml
      output_schema.json
```

Presence-only 模板比 realization_eligible 模板更轻量，但结构相同。

---

## 4. Baseline Fragment 结构

```json
{
  "skill_instance_id": "skill-baseline-settings",
  "template_id": "baseline.settings.presence_only",
  "status": "completed",
  "emitted_families": ["settings_spec"],
  "spec_fragments": {
    "settings_spec": {
      "capability": "game_settings_panel",
      "required_controls": [
        "master_volume_slider",
        "sfx_volume_slider",
        "window_mode_selector",
        "resolution_selector",
        "apply_button",
        "back_button"
      ],
      "deferred_controls": [
        "music_volume_slider",
        "graphics_quality_preset",
        "key_rebinding"
      ],
      "persistence": "session_only",
      "realization_class": "presence_only"
    }
  },
  "design_decision_log": [],
  "assumptions": [
    {
      "assumption": "采用 presence_only 最低实现标准",
      "basis": "Root Skill Contract 标注该项为 presence_only"
    }
  ],
  "open_questions": [],
  "capability_gaps": [],
  "confidence": { "coverage": 1.0, "consistency": 1.0 }
}
```

---

## 5. Start Screen 能力级定义

Start Screen 作为 Baseline 项采用能力级定义，不绑定具体实现方式：

```json
{
  "start_screen_spec": {
    "capability": "pre_menu_entry_shell",
    "required_elements": [
      "project_identity_display",
      "user_interaction_trigger",
      "navigate_to_main_menu"
    ],
    "default_implementation": "independent_level",
    "alternative_implementations": [
      "main_menu_pre_state",
      "frontend_shell_page"
    ],
    "realization_class": "presence_only"
  }
}
```

能力要求与实现方式解耦。presence_only 使用默认实现；realization_eligible 可通过 Design Space Discovery 选择替代实现。
