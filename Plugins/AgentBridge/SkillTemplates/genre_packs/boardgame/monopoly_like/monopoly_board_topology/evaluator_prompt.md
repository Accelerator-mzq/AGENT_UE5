# Evaluator Prompt — Board Topology 自检

请对你生成的 board_topology_spec 进行以下检查：

## 必过检查项

1. **索引完整性**：tile_index_list 是否包含 0 到 tile_count-1 的所有索引，无缺口无重复？
2. **角格一致性**：corner_tiles 中的 start/jail_visit/free_parking/go_to_jail 索引是否都出现在 tile_index_list 中，且标记为 is_corner=true？
3. **闭合性**：is_closed_loop 是否为 true？adjacency_rule 是否正确描述了环形闭合？
4. **每边格数**：tiles_per_side × 4 - 4 是否等于 tile_count？（四边共享四个角格）
5. **方向一致**：movement_direction 是否与 GDD 一致？
6. **Phase 范围**：是否有任何超出 Phase 1 的内容？

## 如果检查失败
- 标记 confidence.coverage 为较低值
- 在 review_hints 中说明具体问题
- 在 open_questions 中列出不确定点
