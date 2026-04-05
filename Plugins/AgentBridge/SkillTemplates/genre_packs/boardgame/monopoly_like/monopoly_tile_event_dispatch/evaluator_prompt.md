# Evaluator Prompt — Tile Event Dispatch 自检

## 必过检查项

1. **28 格完整性**：tile_data_table 是否恰好包含 28 条记录，索引 0..27？
2. **类型覆盖**：8 种格子类型是否全部出现在 tile_types 中？
3. **数据一致性**：tile_data_table 中每个格子的 type 是否都在 tile_types 枚举中？
4. **颜色组闭合**：color_groups 中引用的 tile_indices 是否都存在于 tile_data_table 中？对应格子是否都是 PROPERTY 类型？
5. **事件矩阵完整**：event_dispatch_matrix 是否覆盖全部 8 种格子类型？
6. **Phase 1 留空**：CHANCE 和 COMMUNITY 的事件是否标记为 phase1_placeholder？
7. **税务金额**：TAX 类型格子是否有 tax_amount 字段？
8. **价格/租金**：PROPERTY 类型格子是否都有 price 和 base_rent？非 PROPERTY 格子这两个字段是否为 null？
