# Base Skill Domains

## 当前状态
📦 **占位目录** - 第一阶段暂未实现

## 未来扩展

Base Skill Domains 是跨项目、跨类型都可复用的通用编译骨架。

### 计划包含的域

1. **Design & Project State Intake Domain**
   - 设计输入读取
   - 项目现状采集
   - 基线快照加载

2. **Baseline Understanding Domain**
   - 项目模型构建
   - Spec 基线构建
   - 能力地图构建

3. **Delta Scope Analysis Domain**
   - 增量意图分析
   - 受影响域检测
   - 回归需求检测

4. **Product & Scope Domain**
   - 产品范围定义
   - 阶段目标管理

5. **Runtime & Gameplay Domain**
   - 游戏逻辑编译
   - 运行时连线

6. **World & Level Domain**
   - 场景布局生成
   - 地图结构编译

7. **Presentation & Asset Domain**
   - UI 生成
   - Audio 配置
   - 资产管理

8. **Config & Platform Domain**
   - 配置生成
   - 平台适配

9. **QA & Validation Domain**
   - 验证规则生成
   - 测试用例生成

10. **Planning & Governance Domain**
    - 执行计划生成
    - 治理规则应用

## 第一阶段实现

第一阶段只实现了最小的 Intake 和 Routing 能力，位于：
- `Scripts/compiler/intake/`
- `Scripts/compiler/routing/`

完整的 Base Skill Domains 将在后续阶段补充。
