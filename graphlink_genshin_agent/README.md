# GraphLink 原神人物关系图谱

来源：https://open.graphlink.cc/GraphVisualizationShare?id=6964957435d5c31deca9f855

本目录把 GraphLink 分享页中的图谱数据整理成便于 agent 读取的结构。原图是有向图：边从 `source` 指向 `target`，关系名来自边的 `data.title` 或 `style.labelText`。

## 推荐读取顺序

1. 先读 `manifest.json` 获取来源、抓取时间、文件清单和总体数量。
2. 用 `lookup_by_name.json` 把用户提到的人物名/别名解析为节点 id。
3. 用 `character_graph.json` 读取该节点的 `incoming` 与 `outgoing` 关系。
4. 需要批量检索或向量化时，读取 `nodes.jsonl` 与 `relationships.jsonl`。
5. 需要核对原始 GraphLink 字段时，查看 `source/raw_graph.json`。

## 主要文件

- `nodes.jsonl`: 每行一个实体，字段包括 `id`, `label`, `aliases`, `entity_type`, `importance`, `notes`, `degree`。
- `relationships.jsonl`: 每行一条有向关系，字段包括 `source`, `relation`, `target`, `notes`, `created_at`。
- `character_graph.json`: 已按实体聚合，适合回答“某个人物和谁有什么关系”。
- `ontology_model.json`: 站点额外加载的“原神世界观”本体模型。

## 数据规模

- 人物/实体关系图：613 个节点，585 条关系。
- 世界观本体模型：135 个节点，134 条关系。

## 备注

图中 `NPC`, `人类象限`, `魔神象限`, `原魔象限` 等均按原站点类型保留；未强行删去地点、物件、伏笔等非人物节点，因为它们经常参与人物关系推理。
