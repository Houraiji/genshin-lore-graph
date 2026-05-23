#!/usr/bin/env python3
"""Combine live Biligame character basics with bundled GraphLink lore graph matches."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from query_biligame_character import FILTER_URL, name_candidates, query_character
from query_genshin_graph import compact_node, find_matches, load_dataset


GRAPHLINK_SOURCE = "open.GraphLink.cc/Genshin share id 6964957435d5c31deca9f855 (bundled local JSON/JSONL)"


def graph_matches(
    names: str | list[str],
    dataset: str,
    limit: int,
    edge_limit: int,
) -> list[dict[str, Any]]:
    terms = [names] if isinstance(names, str) else names
    datasets = ["characters", "worldview"] if dataset == "both" else [dataset]
    matches: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for current in datasets:
        data = load_dataset(current)
        dataset_count = 0
        for term in terms:
            rows = find_matches(data, term, None, [], limit)
            for row in rows:
                key = (current, row["id"])
                if key in seen:
                    continue
                seen.add(key)
                matches.append(compact_node(current, row, edge_limit, data["paths_by_id"]))
                dataset_count += 1
                if dataset_count >= limit:
                    break
            if dataset_count >= limit:
                break
    return matches


def graph_query_terms(name: str, biligame: dict[str, Any]) -> list[str]:
    values: list[str] = [name]
    values.extend(biligame.get("normalized_query") or [])

    character = biligame.get("character") or {}
    values.extend(
        value
        for value in [
            character.get("source_name"),
            character.get("name"),
            character.get("page_title"),
            (character.get("fields") or {}).get("full_name"),
        ]
        if value
    )

    terms: list[str] = []
    seen: set[str] = set()
    for value in values:
        for candidate in name_candidates(value):
            if candidate not in seen:
                seen.add(candidate)
                terms.append(candidate)
    return terms


def query_context(args: argparse.Namespace) -> dict[str, Any]:
    biligame: dict[str, Any]
    if args.offline:
        biligame = {
            "found": False,
            "query": args.name,
            "offline": True,
            "filter_url": FILTER_URL,
            "detail_url": None,
            "character": None,
            "error": {"stage": "offline", "message": "Biligame lookup skipped because --offline was set."},
        }
    else:
        try:
            biligame = query_character(args.name, timeout=args.timeout)
            biligame["offline"] = False
        except Exception as exc:  # Keep graph lookup available even if live parsing changes.
            biligame = {
                "found": False,
                "query": args.name,
                "offline": False,
                "filter_url": FILTER_URL,
                "detail_url": None,
                "character": None,
                "error": {"stage": "biligame", "message": str(exc)},
            }

    terms = graph_query_terms(args.name, biligame)
    matches = graph_matches(terms, args.dataset, args.limit, args.edge_limit)

    return {
        "query": {
            "name": args.name,
            "graph_query_terms": terms,
            "dataset": args.dataset,
            "offline": args.offline,
            "limit": args.limit,
            "edge_limit": args.edge_limit,
        },
        "sources": {
            "biligame_filter": FILTER_URL,
            "biligame_character_detail": biligame.get("detail_url"),
            "graphlink_local": GRAPHLINK_SOURCE,
        },
        "biligame_character": biligame,
        "graph_matches": matches,
        "answer_hints": [
            "Use biligame_character.fields for live basic character profile data when found.",
            "Use graph_matches for GraphLink relationship edges, notes, and worldview paths.",
            "Keep Biligame facts and GraphLink graph notes distinguishable in answers.",
            "Treat GraphLink notes containing 伏笔/猜测/问题 as clues or annotations, not official confirmation.",
            "Do not treat --offline, network errors, or parser errors as proof that a Biligame character page does not exist.",
            "If biligame_character.found is false, answer from graph_matches and mention the live lookup status precisely; retry without --offline or with the Biligame detail URL when basic profile data matters.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Character or concept name.")
    parser.add_argument("--dataset", choices=["characters", "worldview", "both"], default="both")
    parser.add_argument("--limit", type=int, default=8, help="Maximum graph matches per dataset.")
    parser.add_argument("--edge-limit", type=int, default=20, help="Maximum incoming/outgoing edges per graph match.")
    parser.add_argument("--timeout", type=int, default=15, help="Biligame network timeout in seconds.")
    parser.add_argument("--offline", action="store_true", help="Skip Biligame network lookup and only query local GraphLink data.")
    args = parser.parse_args()

    json.dump(query_context(args), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
