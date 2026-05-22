---
name: genshin-lore-graph
description: Genshin Impact / 原神 lore graph knowledge from bundled GraphLink data. Use when answering questions about 原神 characters, NPCs, factions, family/mentor/enemy relationships, character notes, Teyvat worldbuilding, ontology/worldview hierarchy, regions, organizations, gods, abyss/Khaenri'ah lore, or when an agent needs grounded Genshin relationship/world-setting context.
---

# Genshin Lore Graph

Use this skill to ground 原神/Genshin Impact answers in the bundled GraphLink graph data rather than memory alone.

## Data Layout

- `references/characters/`: character/entity relationship graph.
  - `nodes.jsonl`: one entity per line.
  - `relationships.jsonl`: one directed relation per line.
  - `character_graph.json`: per-node `incoming` and `outgoing` adjacency.
  - `lookup_by_name.json`: exact labels and aliases to node ids.
  - `stats.json`: counts, type distribution, top-degree entities.
- `references/worldview/`: world ontology graph.
  - `nodes.jsonl`: one worldview concept per line.
  - `relationships.jsonl`: one directed relation per line.
  - `worldview_graph.json`: per-node adjacency.
  - `worldview_tree.json`: hierarchy expanded from the root.
  - `paths.jsonl`: root-to-node paths for hierarchy lookup.
  - `lookup_by_name.json`: concept labels and aliases to node ids.

The graph source is GraphLink share id `6964957435d5c31deca9f855`.

## Quick Workflow

1. For a user asking about a specific character/concept, run `scripts/query_genshin_graph.py --name "<term>" --dataset both`.
2. For broad or fuzzy questions, run `scripts/query_genshin_graph.py --search "<keyword>" --dataset both --limit 10`.
3. Read only the returned matching records first. Load full JSON/JSONL files only when the answer needs broader traversal or statistics.
4. Treat edges as directed: `source --relation--> target`. Mention direction if it matters.
5. When combining character relationships with setting context, check both datasets and state which graph supplied which fact if ambiguity matters.

## Answering Guidance

- Prefer names, relationship labels, notes, and hierarchy paths from the bundled files.
- Preserve uncertainty from the graph. If a node note says "伏笔" or poses a question, present it as an open clue, not confirmed canon.
- If multiple labels/aliases resolve to different ids, compare surrounding relationships before choosing.
- Do not invent missing reciprocal relationships. If the graph only says `A --父亲--> B`, report that direction unless another edge confirms the inverse.
- For current game version, release dates, or official canon updates beyond the bundled graph, browse or ask for updated source data before asserting freshness.

## Query Script

Examples:

```bash
python scripts/query_genshin_graph.py --name "钟离" --dataset characters
python scripts/query_genshin_graph.py --name "提瓦特世界" --dataset worldview
python scripts/query_genshin_graph.py --search "坎瑞亚" --dataset both --limit 20
```

The script returns compact JSON with node metadata, notes, incoming/outgoing relationships, and worldview paths when available.
