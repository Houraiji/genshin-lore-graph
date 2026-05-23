#!/usr/bin/env python3
"""Fetch live Genshin character basics from Biligame 原神WIKI."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


FILTER_URL = "https://wiki.biligame.com/ys/%E8%A7%92%E8%89%B2%E7%AD%9B%E9%80%89"
DETAIL_BASE = "https://wiki.biligame.com/ys/"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": FILTER_URL,
}

FIELD_ALIASES = {
    "称号": "title",
    "全名/本名": "full_name",
    "所属地区": "region",
    "出身地区": "origin",
    "种族": "race",
    "性别": "gender",
    "稀有度": "rarity",
    "常驻/限定": "availability",
    "神之眼": "vision",
    "神之心": "gnosis",
    "武器类型": "weapon",
    "始基力": "arkhe",
    "羁绊属性": "bond_attribute",
    "命之座": "constellation",
    "特殊料理": "special_dish",
    "实装日期": "release_date",
    "TAG": "tags",
    "介绍": "description",
}

DETAIL_FIELDS = list(FIELD_ALIASES)


class FetchError(RuntimeError):
    pass


def fetch_text(url: str, timeout: int) -> str:
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            return data.decode(charset, errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise FetchError(str(exc)) from exc


def normalize_spaces(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    return value.strip()


def strip_tags(fragment: str) -> str:
    fragment = re.sub(r"<!--.*?-->", "", fragment, flags=re.S)
    fragment = re.sub(r"<script\b.*?</script>", "", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<style\b.*?</style>", "", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<span\b[^>]*class=\"[^\"]*smw-highlighter[^\"]*\"[^>]*>.*?</span>\s*</span>", "", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<span\b[^>]*class=\"[^\"]*smw-highlighter[^\"]*\"[^>]*>.*?</span>", "", fragment, flags=re.S | re.I)
    alt_values = re.findall(r"<img\b[^>]*\balt=\"([^\"]+)\"", fragment, flags=re.I)
    fragment = re.sub(r"<img\b[^>]*>", "", fragment, flags=re.I)
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    text = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(text)
    text = normalize_spaces(text)
    if not text and alt_values:
        text = html.unescape(alt_values[0])
    text = re.sub(r"\.(png|jpg|jpeg|webp)$", "", text, flags=re.I)
    return normalize_spaces(text)


def normalize_lookup_name(value: str) -> str:
    value = html.unescape(value or "")
    value = value.replace("（", "(").replace("）", ")")
    value = re.sub(r"\s+", "", value)
    return value.strip()


def detail_name_from_input(value: str) -> str | None:
    match = re.search(r"https?://wiki\.biligame\.com/ys/[^\s?#]+", html.unescape(value or ""))
    if not match:
        return None

    parsed = urllib.parse.urlparse(match.group(0))
    if parsed.netloc != "wiki.biligame.com" or not parsed.path.startswith("/ys/"):
        return None

    raw_name = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    name = urllib.parse.unquote(raw_name).replace("_", " ").strip()
    name = re.split(r"[，,。；;：:\]\)）>\"']", name, 1)[0].strip()
    if not name or name == "角色筛选":
        return None
    return name


def name_candidates(name: str) -> list[str]:
    raw = html.unescape(name or "").strip()
    detail_name = detail_name_from_input(raw)
    source = detail_name or raw
    cleaned = re.sub(r"\s+", " ", source).strip()
    compact = normalize_lookup_name(source)
    candidates = [cleaned, compact]

    for match in re.findall(r"[（(]([^（）()]+)[）)]", source):
        candidates.append(match.strip())
        candidates.extend(part.strip() for part in re.split(r"[/／、,，]", match) if part.strip())

    without_parens = re.sub(r"[（(][^（）()]+[）)]", "", source).strip()
    candidates.append(without_parens)
    candidates.extend(part.strip() for part in re.split(r"[/／、,，]", without_parens) if part.strip())

    seen = set()
    result = []
    for candidate in candidates:
        candidate = candidate.strip()
        key = normalize_lookup_name(candidate)
        if candidate and key not in seen:
            seen.add(key)
            result.append(candidate)
    return result


def parse_filter_characters(filter_html: str) -> dict[str, dict[str, Any]]:
    pattern = re.compile(
        r"<tr\b(?P<tr>[^>]*)>.*?<td>\s*<a href=\"(?P<href>/ys/[^\"]+)\" title=\"(?P<name>[^\"]+)\">\s*<img\b[^>]*头像",
        re.S,
    )
    characters: dict[str, dict[str, Any]] = {}
    for match in pattern.finditer(filter_html):
        attrs = match.group("tr")
        params = {
            key: html.unescape(value)
            for key, value in re.findall(r'data-param(\d+)="([^"]*)"', attrs)
        }
        name = html.unescape(match.group("name")).strip()
        entry = {
            "name": name,
            "url": urllib.parse.urljoin(DETAIL_BASE, match.group("href")),
            "rarity": params.get("1", ""),
            "weapon": params.get("2", ""),
            "element": params.get("3", ""),
            "gender": params.get("4", ""),
            "region_or_origin": params.get("5", ""),
            "tags": params.get("6", ""),
            "availability": params.get("7", ""),
            "bonus_stat": params.get("8", ""),
            "arkhe": params.get("9", ""),
            "body_type": params.get("10", ""),
        }
        characters[normalize_lookup_name(name)] = entry
    return characters


def detail_url_for_name(name: str) -> str:
    return DETAIL_BASE + urllib.parse.quote(name, safe="")


def first_infobox_table(page_html: str) -> str | None:
    match = re.search(
        r"<table class=\"wikitable\" style=\"margin-top:0px;width:100%;\">.*?</table>",
        page_html,
        flags=re.S,
    )
    return match.group(0) if match else None


def parse_detail_fields(page_html: str) -> dict[str, str]:
    table = first_infobox_table(page_html)
    if not table:
        return {}

    fields: dict[str, str] = {}
    row_pattern = re.compile(
        r"<tr\b[^>]*>\s*<th\b[^>]*>(?P<key>.*?)</th>\s*<td\b[^>]*>(?P<value>.*?)</td>\s*</tr>",
        flags=re.S | re.I,
    )
    for match in row_pattern.finditer(table):
        key = strip_tags(match.group("key"))
        value = strip_tags(match.group("value"))
        if key and value:
            fields[key] = value
    return fields


def parse_page_title(page_html: str) -> str:
    match = re.search(r"<h2><span\b[^>]*></span><span class=\"mw-headline\" id=\"[^\"]+\">(.*?)</span></h2>", page_html, re.S)
    if match:
        return strip_tags(match.group(1))
    match = re.search(r"<meta itemprop=\"name\" content=\"([^\"]+)\"", page_html)
    if match:
        return html.unescape(match.group(1)).split(" - ", 1)[0].strip()
    return ""


def parse_modified_time(page_html: str) -> dict[str, str]:
    result: dict[str, str] = {}
    match = re.search(r'<meta property="article:modified_time" content="([^"]+)"', page_html)
    if match:
        result["article_modified_time"] = html.unescape(match.group(1))
    match = re.search(r'id="footer-info-lastmod">\s*(.*?)</li>', page_html, re.S)
    if match:
        result["footer_last_modified"] = strip_tags(match.group(1))
    match = re.search(r"更新日期：\s*<span>(.*?)</span>", page_html, re.S)
    if match:
        result["wiki_update_date"] = strip_tags(match.group(1))
    return result


def parse_character_detail(page_html: str) -> dict[str, Any]:
    raw_fields = parse_detail_fields(page_html)
    normalized_fields: dict[str, str] = {}
    for label in DETAIL_FIELDS:
        if label in raw_fields:
            normalized_fields[FIELD_ALIASES[label]] = raw_fields[label]

    tags_value = normalized_fields.get("tags")
    tags = [item.strip() for item in re.split(r"[、,，]", tags_value or "") if item.strip()]

    return {
        "page_title": parse_page_title(page_html),
        "fields": normalized_fields,
        "raw_fields": {key: raw_fields[key] for key in DETAIL_FIELDS if key in raw_fields},
        "tags": tags,
        "page_updated": parse_modified_time(page_html),
    }


def resolve_character_name(name: str, filter_characters: dict[str, dict[str, Any]]) -> tuple[str, dict[str, Any] | None, list[str]]:
    candidates = name_candidates(name)
    for candidate in candidates:
        entry = filter_characters.get(normalize_lookup_name(candidate))
        if entry:
            return entry["name"], entry, candidates
    return candidates[0] if candidates else name, None, candidates


def query_character(name: str, timeout: int = 15, skip_filter: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "found": False,
        "query": name,
        "normalized_query": name_candidates(name),
        "confirmed_in_filter": False,
        "filter_url": FILTER_URL,
        "detail_url": None,
        "character": None,
        "lookup_mode": None,
        "detail_attempts": [],
        "error": None,
    }

    filter_characters: dict[str, dict[str, Any]] = {}
    if not skip_filter:
        try:
            filter_characters = parse_filter_characters(fetch_text(FILTER_URL, timeout))
        except FetchError as exc:
            result["error"] = {"stage": "filter", "message": str(exc)}

    resolved_name, filter_entry, candidates = resolve_character_name(name, filter_characters)
    result["normalized_query"] = candidates
    result["confirmed_in_filter"] = filter_entry is not None
    result["filter_entry"] = filter_entry

    trial_names = [resolved_name] + [candidate for candidate in candidates if candidate != resolved_name]
    seen = set()
    errors = []
    detail_attempts = []
    for trial_name in trial_names:
        key = normalize_lookup_name(trial_name)
        if not key or key in seen:
            continue
        seen.add(key)
        detail_url = filter_entry["url"] if filter_entry and normalize_lookup_name(filter_entry["name"]) == key else detail_url_for_name(trial_name)
        detail_attempts.append({"name": trial_name, "url": detail_url})
        try:
            page_html = fetch_text(detail_url, timeout)
        except FetchError as exc:
            errors.append({"stage": "detail", "url": detail_url, "message": str(exc)})
            continue

        details = parse_character_detail(page_html)
        if details["fields"]:
            result.update(
                {
                    "found": True,
                    "detail_url": detail_url,
                    "lookup_mode": "filter_confirmed_detail" if filter_entry is not None else "direct_detail",
                    "detail_attempts": detail_attempts,
                    "character": {
                        "name": details["page_title"] or trial_name,
                        "source_name": trial_name,
                        "confirmed_in_filter": filter_entry is not None,
                        "filter_entry": filter_entry,
                        **details,
                    },
                    "error": None,
                }
            )
            return result

        errors.append({"stage": "detail_parse", "url": detail_url, "message": "character infobox not found"})

    if errors:
        result["error"] = errors[0] if len(errors) == 1 else {"stage": "detail", "attempts": errors}
    result["detail_attempts"] = detail_attempts
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Character name or GraphLink label.")
    parser.add_argument("--timeout", type=int, default=15, help="Network timeout in seconds.")
    parser.add_argument("--skip-filter", action="store_true", help="Skip the role filter page and try detail pages directly.")
    args = parser.parse_args()

    output = query_character(args.name, timeout=args.timeout, skip_filter=args.skip_filter)
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
