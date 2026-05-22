#!/usr/bin/env python3
"""Query bundled GraphLink Genshin character and worldview graph data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "references"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def text_blob(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("label", "raw_label", "entity_type", "category", "importance"):
        value = row.get(key)
        if value:
            parts.append(str(value))
    parts.extend(str(x) for x in row.get("aliases", []) if x)
    parts.extend(str(x) for x in row.get("notes", []) if x)
    for side in ("incoming", "outgoing"):
        for edge in row.get(side, []):
            parts.extend(str(edge.get(k, "")) for k in ("source", "relation", "target"))
            parts.extend(str(x) for x in edge.get("notes", []) if x)
    return "\n".join(parts).lower()


def compact_edges(edges: list[dict[str, Any]], limit: int, side: str, current_label: str) -> list[dict[str, Any]]:
    compacted = []
    for edge in edges[:limit]:
        source = edge.get("source")
        target = edge.get("target")
        if side == "incoming":
            target = current_label
        elif side == "outgoing":
            source = current_label
        compacted.append(
            {
                "edge_id": edge.get("edge_id"),
                "source": source,
                "relation": edge.get("relation"),
                "target": target,
                "notes": edge.get("notes", []),
            }
        )
    return compacted


def compact_node(dataset: str, row: dict[str, Any], edge_limit: int, paths_by_id: dict[str, Any]) -> dict[str, Any]:
    result = {
        "dataset": dataset,
        "id": row.get("id"),
        "label": row.get("label"),
        "aliases": row.get("aliases", []),
        "type": row.get("entity_type") or row.get("category"),
        "importance": row.get("importance", ""),
        "notes": row.get("notes", []),
        "degree": row.get("degree", {}),
        "incoming": compact_edges(row.get("incoming", []), edge_limit, "incoming", row.get("label", "")),
        "outgoing": compact_edges(row.get("outgoing", []), edge_limit, "outgoing", row.get("label", "")),
    }
    if row.get("id") in paths_by_id:
        result["path"] = paths_by_id[row["id"]].get("path", [])
        result["depth"] = paths_by_id[row["id"]].get("depth")
    return result


def load_dataset(dataset: str) -> dict[str, Any]:
    base = REFS / dataset
    graph_name = "character_graph.json" if dataset == "characters" else "worldview_graph.json"
    graph = load_json(base / graph_name)
    lookup = load_json(base / "lookup_by_name.json")
    paths_by_id: dict[str, Any] = {}
    path_file = base / "paths.jsonl"
    if path_file.exists():
        paths_by_id = {row["id"]: row for row in load_jsonl(path_file)}
    by_id = {row["id"]: row for row in graph}
    return {"graph": graph, "lookup": lookup, "by_id": by_id, "paths_by_id": paths_by_id}


def find_matches(data: dict[str, Any], name: str | None, search: str | None, ids: list[str], limit: int) -> list[dict[str, Any]]:
    by_id = data["by_id"]
    ordered_ids: list[str] = []

    for node_id in ids:
        if node_id in by_id:
            ordered_ids.append(node_id)

    if name:
        for node_id in data["lookup"].get(name, []):
            ordered_ids.append(node_id)
        needle = name.lower()
        for row in data["graph"]:
            if needle in text_blob(row):
                ordered_ids.append(row["id"])

    if search:
        needle = search.lower()
        for row in data["graph"]:
            if needle in text_blob(row):
                ordered_ids.append(row["id"])

    seen = set()
    matches = []
    for node_id in ordered_ids:
        if node_id not in seen and node_id in by_id:
            seen.add(node_id)
            matches.append(by_id[node_id])
        if len(matches) >= limit:
            break
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["characters", "worldview", "both"], default="both")
    parser.add_argument("--name", help="Exact or fuzzy character/concept name.")
    parser.add_argument("--search", help="Keyword search across labels, aliases, notes, and edge labels.")
    parser.add_argument("--id", action="append", default=[], help="Node id to fetch. May be repeated.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum matches per dataset.")
    parser.add_argument("--edge-limit", type=int, default=20, help="Maximum incoming/outgoing edges per match.")
    args = parser.parse_args()

    if not (args.name or args.search or args.id):
        parser.error("provide --name, --search, or --id")

    datasets = ["characters", "worldview"] if args.dataset == "both" else [args.dataset]
    output = {"query": {"name": args.name, "search": args.search, "ids": args.id}, "matches": []}

    for dataset in datasets:
        data = load_dataset(dataset)
        matches = find_matches(data, args.name, args.search, args.id, args.limit)
        output["matches"].extend(
            compact_node(dataset, row, args.edge_limit, data["paths_by_id"]) for row in matches
        )

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
