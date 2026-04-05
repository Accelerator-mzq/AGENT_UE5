# 当前阶段目标

> 状态：Phase 8 正式开发期

## 1. 当前目标

1. 完成 Skill-First Compiler Reset：用 6 阶段主链（Intake → Planner → SkillRuntime → CrossReview → Lowering → Execution）替代旧的编译链路。
2. 以 MonopolyGame Phase 1（本地多人大富翁）作为唯一垂直切片，端到端走通 GDD → Compiler → Build IR → C++ 代码 → 可运行游戏。
3. 验证 Reviewed Handoff v2 作为 Compiler→Execution 唯一边界的可行性。
4. 验证 Skill Template Pack 三层结构（Template / Instance / Artifact）的设计。

## 2. 当前成功标准

- Compiler 主链 5 阶段全部产出合法 JSON（11 个文件）— **已达成**
- Cross-Review 审查通过，无 blocker — **已达成**
- Build IR 14 个步骤可映射到 C++ 类 — **已达成**
- M3 垂直切片：12 个验证检查点全部通过 — **进行中**
- M4 兼容性：现有 230 条系统测试不被破坏 — **待验证**

## 3. 当前假设

- Phase 8 仅做 MonopolyGame Phase 1（本地热座 2-4 人），不做 Phase 2 网络多人。
- Phase 1 不实现：拍卖、交易、抵押、建房/旅馆、机会卡、公共基金卡、AI 对手。
- UMG Widget 布局全部纯 C++ 构建，不依赖蓝图编辑器手动排版。
- 3D 资产使用基础几何体（Box/Cylinder），不追求美术质量。
