# Genshin Lore Graph

> 基于 GraphLink 公开图谱整理的原神人物关系与世界观设定数据集，并封装为可供 Agent 检索使用的 Skill。

**GitHub About 描述建议：**

```text
基于 open.GraphLink.cc/Genshin 公开人物关系图与世界观图谱整理的原神 Lore Graph，提供 JSON/JSONL 数据与 Codex/Claude Code Skill。
```

## 项目简介

本仓库将 GraphLink 上公开分享的原神人物关系图和世界观图谱整理为更适合 AI Agent 读取、检索和推理的文件结构。

它不是一个游戏攻略库，也不是官方设定集；更准确地说，它是一个面向 Agent 的结构化 Lore Graph：把角色、NPC、组织、神明、种族、事件、地点、概念以及它们之间的关系转换为标准化的节点、边、邻接表、层级树和查询脚本。

数据来源：`open.GraphLink.cc/Genshin`

## 数据规模

| 数据集 | 节点数 | 关系数 | 说明 |
| --- | ---: | ---: | --- |
| 人物/实体关系图 | 613 | 585 | 角色、NPC、神明、魔物、组织、事件、物件、伏笔等 |
| 世界观图谱 | 135 | 134 | 提瓦特世界观、本体层级、组织、种族、能力、等级等 |

世界观图谱额外整理了树状结构和根到节点路径：

- 根节点：1
- 叶子节点：110
- 最大路径深度：5

## 目录结构

```text
.
├── graphlink_genshin_agent/
│   ├── nodes.jsonl
│   ├── relationships.jsonl
│   ├── character_graph.json
│   ├── lookup_by_name.json
│   ├── ontology_model.json
│   └── source/
├── graphlink_genshin_ontology_agent/
│   ├── nodes.jsonl
│   ├── relationships.jsonl
│   ├── worldview_graph.json
│   ├── worldview_tree.json
│   ├── paths.jsonl
│   ├── lookup_by_name.json
│   └── source/
└── skills/
    └── genshin-lore-graph/
        ├── SKILL.md
        ├── references/
        │   ├── characters/
        │   └── worldview/
        └── scripts/
            ├── query_biligame_character.py
            ├── query_genshin_context.py
            └── query_genshin_graph.py
```

## 主要文件说明

### 人物关系图

位于 `graphlink_genshin_agent/`。

- `nodes.jsonl`：一行一个人物或实体，包含 `id`, `label`, `aliases`, `entity_type`, `importance`, `notes`, `degree` 等字段。
- `relationships.jsonl`：一行一条有向关系，包含 `source`, `relation`, `target`, `notes`, `created_at` 等字段。
- `character_graph.json`：按实体聚合的邻接表，适合回答“某个人物和谁有什么关系”。
- `lookup_by_name.json`：名称和别名到节点 id 的索引。
- `source/raw_graph.json`：GraphLink 原始图谱 JSON，保留用于溯源。

### 世界观图谱

位于 `graphlink_genshin_ontology_agent/`。

- `nodes.jsonl`：一行一个世界观节点。
- `relationships.jsonl`：一行一条世界观层级或关联关系。
- `worldview_graph.json`：按节点聚合的上下游关系。
- `worldview_tree.json`：从根节点展开的世界观树。
- `paths.jsonl`：根节点到每个节点的路径，适合层级检索。
- `source/raw_ontology_model.json`：GraphLink 原始世界观 JSON。

## Skill 用法

仓库内提供了 `genshin-lore-graph` Skill，可安装到 Codex 或 Claude Code 的 skills 目录中，让 Agent 在回答原神角色关系、NPC、组织、神明、世界观、本体层级等问题时自动查阅本地数据。

Skill 路径：

```text
skills/genshin-lore-graph/
```

常用 Skill 安装命令：

```powershell
# Codex, Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills"
Copy-Item -Recurse -Force ".\skills\genshin-lore-graph" "$env:USERPROFILE\.codex\skills\"

# Claude Code, Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills"
Copy-Item -Recurse -Force ".\skills\genshin-lore-graph" "$env:USERPROFILE\.claude\skills\"
```

```bash
# Codex, macOS/Linux
mkdir -p ~/.codex/skills
cp -R skills/genshin-lore-graph ~/.codex/skills/

# Claude Code, macOS/Linux
mkdir -p ~/.claude/skills
cp -R skills/genshin-lore-graph ~/.claude/skills/
```

融合查询脚本示例：

```bash
python skills/genshin-lore-graph/scripts/query_genshin_context.py --name "钟离"
python skills/genshin-lore-graph/scripts/query_genshin_context.py --name "凯亚" --edge-limit 10
python skills/genshin-lore-graph/scripts/query_genshin_context.py --name "派蒙" --offline
```

`query_genshin_context.py` 会优先从 Biligame 原神WIKI读取角色基础资料，再合并本地 GraphLink 图谱中的关系、备注和世界观路径。`--offline` 会跳过联网查询，只读取本地图谱。

本地图谱查询示例：

```bash
python skills/genshin-lore-graph/scripts/query_genshin_graph.py --name "钟离" --dataset characters
python skills/genshin-lore-graph/scripts/query_genshin_graph.py --name "提瓦特世界" --dataset worldview
python skills/genshin-lore-graph/scripts/query_genshin_graph.py --search "坎瑞亚" --dataset both --limit 20
```

返回结果会包含：

- Biligame 角色基础信息：称号、全名/本名、地区、出身、种族、性别、稀有度、神之眼/神之心、武器、命之座、实装日期、TAG、介绍等。
- GraphLink 图谱信息：匹配节点、别名、类型/重要度、备注、入边关系、出边关系、世界观路径。
- 来源信息：Biligame 角色筛选页、角色详情页、本地 GraphLink 图谱说明。

## 适合的使用场景

- 给 Agent 提供原神角色关系的本地知识库。
- 检索角色之间的亲属、师徒、敌对、组织、剧情事件关系。
- 查询提瓦特世界观中的组织、种族、能力、等级等层级。
- 构建 RAG、知识图谱问答、剧情推理或角色关系可视化应用。
- 将 GraphLink 图谱转换为 JSONL、邻接表、路径树等更适合程序读取的结构。

## 注意事项

- 图谱边是有向的：`source --relation--> target`。不要默认关系可反向成立。
- 图中保留了“伏笔”“猜测”“问题”等原始备注。此类内容应作为线索或整理者注记，不应直接当作官方定论。
- 数据基于公开 GraphLink 分享页在整理时的内容，不保证与游戏最新版本同步。
- 受原始资料覆盖范围限制，图谱难免存在缺失、滞后或未记录关系；建议在需要高准确性或最新剧情时结合网络搜索、官方资料一起交叉验证。
- 完整图谱文件体量较大，直接塞进提示词容易 token 爆炸；推荐优先使用 Skill 查询脚本、`lookup_by_name.json`、`paths.jsonl` 等索引文件按需读取。
- 本仓库不隶属于 HoYoverse、miHoYo 或 GraphLink。
- 原神相关名称、设定和商标归其权利方所有；本仓库仅用于非商业的学习、研究和 Agent 检索实验。
