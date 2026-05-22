# GraphLink 原神世界观图谱

来源：https://open.graphlink.cc/GraphVisualizationShare?id=6964957435d5c31deca9f855&type=ontology

本目录把 GraphLink 分享页的 `type=ontology` 图谱整理成便于 agent 读取的结构。该图更偏向世界观/本体层级：边从 `source` 指向 `target`，关系名缺失时统一标记为 `包含/关联`。

## 推荐读取顺序

1. 先读 `manifest.json` 确认来源、抓取时间和文件清单。
2. 用 `lookup_by_name.json` 将概念名解析为节点 id。
3. 用 `worldview_graph.json` 查询某个概念的上下游关系。
4. 用 `worldview_tree.json` 或 `paths.jsonl` 理解从“提瓦特世界”等根节点展开的层级。
5. 需要批量检索或向量化时，读取 `nodes.jsonl` 与 `relationships.jsonl`。

## 数据规模

- 世界观节点：135
- 有向关系：134
- 根节点：1
- 叶子节点：110
- 最大路径深度：5

## Schema 摘要

- `nodes.jsonl`: `id`, `label`, `aliases`, `category`, `notes`, `degree`, `position`。
- `relationships.jsonl`: `source`, `relation`, `target`, `notes`, `directed`。
- `paths.jsonl`: `label`, `depth`, `path`, `leaf`。

原始 GraphLink JSON 保存在 `source/raw_ontology_model.json`，标准化过程中没有删除节点。
