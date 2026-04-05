# 当前风险

> 文档版本：L1-Phase8-v2

## 已降级风险

- Phase 7 治理闭环风险已关闭。
- JRPG 第二类型包复用风险已关闭。
- Phase 8 运行时 HUD 可见性与输入焦点问题已定位并修复，但对应防回归清单仍需固化，见 [08_Phase8_Retrospective_And_Phase9_Checklist.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/08_Phase8_Retrospective_And_Phase9_Checklist.md)。

## Phase 8 当前风险

| 风险 | 严重度 | 说明 | 缓解措施 |
|------|--------|------|----------|
| C++ 编译兼容性 | 中 | 项目层新增多对 C++ 文件，可能与现有模块依赖或 UHT 生成冲突 | Build.cs 正确配置依赖；每个 Batch 完成后立即编译验证 |
| 编辑器级运行时冒烟验证缺口 | 中高 | `--no-editor` 与 simulated 回归无法覆盖默认地图、默认 GameMode、场景可见性、HUD 可见与按钮可点击等真实交互问题 | 将编辑器内 Play 冒烟纳入后续阶段验收，并按复盘文档补齐清单 |
| 骰子/棋子动画占位 | 低 | Phase 1 动画为占位函数，视觉效果有限 | 不阻塞功能验收，后续阶段补充 |
| 3D 资产缺失 | 低 | Phase 1 使用基础几何体，无美术资源 | 功能验证优先，不影响逻辑正确性 |
| Build IR 与实际执行偏差 | 中 | 14 步 Build IR 是理论设计，执行中可能发现参数与集成细节需要调整 | Execution Agent 按 Batch 执行，每步验证后再继续 |
| 现有 230 条测试回归 | 低 | Phase 8 新增产物可能影响现有测试 | M4 统一回归验证 |

## 仍保留的长期风险

- 若下一阶段扩展到 Phase 2 网络多人，GameMode/GameState 的 Replication 改造量较大。
- 若后续新增第三个 genre pack，Skill Template Pack 目录结构仍需继续验证通用性。
