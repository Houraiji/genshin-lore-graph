---
name: genshin-lore-graph
description: Genshin Impact / 原神 lore graph knowledge from bundled GraphLink data plus live Biligame character profile lookup. Use when answering questions about 原神 characters, basic character info, NPCs, factions, family/mentor/enemy relationships, character notes, Teyvat worldbuilding, ontology/worldview hierarchy, regions, organizations, gods, abyss/Khaenri'ah lore, or when an agent needs grounded Genshin relationship/world-setting context.
---

# Genshin Lore Graph

Use this skill to ground 原神/Genshin Impact answers in live Biligame character profile data plus bundled GraphLink relationship/worldview graph data rather than memory alone.

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

Live character basics come from Biligame 原神WIKI:

- `https://wiki.biligame.com/ys/角色筛选`
- character detail pages such as `https://wiki.biligame.com/ys/钟离`

## Quick Workflow

1. For a user asking about a specific character, run `scripts/query_genshin_context.py --name "<term>"` first.
2. For a concept or broad fuzzy search, run `scripts/query_genshin_graph.py --search "<keyword>" --dataset both --limit 10`.
3. If the user provides a Biligame detail URL such as `https://wiki.biligame.com/ys/爱诺`, pass that URL as `--name`; the script will extract the page name and query both Biligame and GraphLink.
4. Use `--offline` only when network access is unavailable or the user explicitly wants local-only behavior.
5. Read only the returned matching records first. Load full JSON/JSONL files only when the answer needs broader traversal or statistics.
6. Treat edges as directed: `source --relation--> target`. Mention direction if it matters.

## Answering Guidance

- Prefer Biligame fields for live basic character profile data: title, full name, region, origin, race, gender, rarity, vision/gnosis, weapon, constellation, special dish, release date, tags, and intro.
- Prefer GraphLink names, relationship labels, notes, and hierarchy paths for lore graph relationships and setting context.
- Keep Biligame facts and GraphLink graph notes distinguishable when the source matters.
- Never claim that a character has no Biligame page just because an offline lookup, network request, or parser failed. Say the live lookup status precisely, then answer from GraphLink if available.
- If Biligame basics are important and the first live lookup fails, retry with the exact Biligame detail URL or `scripts/query_biligame_character.py --name "<term>" --skip-filter` before concluding the page is unavailable.
- Preserve uncertainty from the graph. If a node note says "伏笔" or poses a question, present it as an open clue, not confirmed canon.
- If multiple labels/aliases resolve to different ids, compare surrounding relationships before choosing.
- Do not invent missing reciprocal relationships. If the graph only says `A --父亲--> B`, report that direction unless another edge confirms the inverse.
- For current game version, release dates, or official canon updates beyond the bundled graph, browse or ask for updated source data before asserting freshness.

## Query Script

Examples:

```bash
python scripts/query_genshin_context.py --name "钟离"
python scripts/query_genshin_context.py --name "凯亚" --edge-limit 10
python scripts/query_genshin_context.py --name "https://wiki.biligame.com/ys/爱诺"
python scripts/query_genshin_context.py --name "派蒙" --offline
python scripts/query_genshin_graph.py --name "钟离" --dataset characters
python scripts/query_genshin_graph.py --name "提瓦特世界" --dataset worldview
python scripts/query_genshin_graph.py --search "坎瑞亚" --dataset both --limit 20
```

`query_genshin_context.py` returns compact JSON with `biligame_character`, `graph_matches`, `sources`, and `answer_hints`. `query_genshin_graph.py` remains available for local graph-only queries.
