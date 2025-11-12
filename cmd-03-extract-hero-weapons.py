from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup, Tag

CSV_DEFAULT_PATH = Path("data-heroes.hidden.csv")
OUTPUT_DEFAULT_PATH = Path("hero-weapons.json")
CACHE_DIR_DEFAULT = Path(".cache/hero-pages")
REQUEST_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 CodexBot/1.0"
)


@dataclass
class Hero:
    role: str
    name: str
    url: str


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract weapon information for each hero and save as JSON."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=CSV_DEFAULT_PATH,
        help=f"CSV file with hero role, name, and url (default: {CSV_DEFAULT_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DEFAULT_PATH,
        help=f"Destination JSON file (default: {OUTPUT_DEFAULT_PATH})",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=CACHE_DIR_DEFAULT,
        help=f"Directory for cached hero pages (default: {CACHE_DIR_DEFAULT})",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable reading from or writing to the HTML cache.",
    )
    return parser.parse_args(argv)


def read_heroes(csv_path: Path) -> list[Hero]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Could not find hero CSV at {csv_path}")

    heroes: list[Hero] = []
    with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            role = (row.get("role") or "").strip()
            name = (row.get("name") or "").strip()
            url = (row.get("url") or "").strip()
            if not (role and name and url):
                continue
            heroes.append(Hero(role=role, name=name, url=url))
    return heroes


def fetch_html(url: str, *, cache_dir: Optional[Path] = None) -> str:
    cache_path: Optional[Path] = None
    if cache_dir:
        cache_path = _cache_file_for_url(cache_dir, url)
        if cache_path.exists():
            print(f"Cache hit for {url}", file=sys.stderr)
            return cache_path.read_text(encoding="utf-8")

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    html = response.text
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(html, encoding="utf-8")
    return html


def extract_weapons(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    abilities_heading = _find_abilities_heading(soup)
    if not abilities_heading:
        return []

    weapons: list[dict[str, Any]] = []
    for node in _iter_ability_nodes(abilities_heading):
        weapon = _parse_weapon_node(node)
        if weapon:
            weapons.append(weapon)
    return weapons


def _find_abilities_heading(soup: BeautifulSoup) -> Optional[Tag]:
    heading_ids = [
        "Abilities",
        "Weapons_&_Abilities",
        "Weapons_%26_Abilities",
        "Weapons_and_Abilities",
    ]
    for heading_id in heading_ids:
        span = soup.find("span", id=heading_id)
        if span:
            parent = span.find_parent("h2")
            if parent:
                return parent

    for h2 in soup.find_all("h2"):
        headline = h2.find(class_="mw-headline")
        if headline and "abilities" in headline.get_text(strip=True).lower():
            return h2
    return None


def _iter_ability_nodes(heading: Tag):
    for sibling in heading.find_next_siblings():
        if getattr(sibling, "name", None) == "h2":
            break
        if isinstance(sibling, Tag) and "ability-details" in sibling.get("class", []):
            yield sibling


def _parse_weapon_node(node: Tag) -> Optional[dict[str, Any]]:
    header = node.select_one(".ability-box .header")
    if not header:
        return None
    ability_name = header.get_text(strip=True)

    type_blocks = _extract_type_blocks(node)
    ability_type = (type_blocks.get("type") or "").strip().lower()
    if not ability_type.startswith("weapon"):
        return None

    stats = _extract_stats(node)
    effect_type = type_blocks.get("effect type")
    blocked_by = _extract_blocked_by(node)
    additional_details = _extract_additional_details(node)
    keywords = _extract_keywords(node)
    damage = _extract_damage(stats)

    def stat_value(key: str) -> Optional[str]:
        data = stats.get(key)
        return data["text"] if data else None

    spread_parts = stats.get("spread", {}).get("parts") if stats.get("spread") else []

    return {
        "name": ability_name,
        "effect_type": effect_type,
        "blocked_by": blocked_by,
        "damage": damage,
        "falloff_range": stat_value("falloff_range"),
        "headshot": stat_value("headshot"),
        "rate_of_fire": stat_value("rate_of_fire"),
        "shots_per_volley": stat_value("shots_per_volley"),
        "ammo_comsumption": stat_value("ammo_consumption"),
        "ammo": stat_value("ammo"),
        "reload_time": stat_value("reload_time"),
        "projectile_speed": stat_value("projectile_speed"),
        "projectile_radious": stat_value("projectile_radius"),
        "spread": spread_parts,
        "additional_details": additional_details,
        "keywords": keywords,
    }


def _extract_type_blocks(node: Tag) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for block in node.select(".type-section .type-block"):
        header = block.select_one(".type-header")
        if not header:
            continue
        label = header.get_text(" ", strip=True).lower()
        text = block.get_text(" ", strip=True)
        value = text.replace(header.get_text(" ", strip=True), "", 1).strip()
        blocks[label] = value or None
    return blocks


def _extract_stats(node: Tag) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for row in node.select(".stats .data-row"):
        header_el = row.select_one(".data-row-header")
        value_el = row.select_one(".data-row-value")
        if not header_el or not value_el:
            continue
        label = header_el.get_text(" ", strip=True)
        key = _normalize_key(label)
        key = _dedupe_key(key, stats)
        parts = [part.strip() for part in value_el.stripped_strings if part.strip()]
        text = " ".join(parts)
        stats[key] = {"label": label, "text": text or None, "parts": parts}
    return stats


def _normalize_key(label: str) -> str:
    import re

    key = label.strip().lower()
    key = key.replace("%", "percent")
    key = re.sub(r"[^a-z0-9]+", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key


def _dedupe_key(key: str, stats: dict[str, Any]) -> str:
    if key not in stats:
        return key
    index = 2
    while f"{key}_{index}" in stats:
        index += 1
    return f"{key}_{index}"


def _extract_blocked_by(node: Tag) -> list[str]:
    panel = node.select_one(".interaction-panel")
    blocked: list[str] = []
    if not panel:
        return blocked
    for span in panel.select(".image-border span[title]"):
        title = span.get("title", "").strip()
        lowered = title.lower()
        if lowered.startswith("blocked by"):
            entry = title.split("Blocked by", 1)[1].strip(" .")
            if entry:
                blocked.append(entry)
    return blocked


def _extract_additional_details(node: Tag) -> list[str]:
    details: list[str] = []
    for item in node.select(".ability-notes ul li"):
        text = item.get_text(" ", strip=True)
        if text and text not in details:
            details.append(text)
    return details


def _extract_keywords(node: Tag) -> list[str]:
    keywords: list[str] = []
    for kw in node.select(".keyword .keyword-title"):
        text = kw.get_text(" ", strip=True)
        if text and text not in keywords:
            keywords.append(text)
    return keywords


def _extract_damage(stats: dict[str, dict[str, Any]]) -> dict[str, Optional[str]]:
    damage: dict[str, Optional[str]] = {}
    for key, data in stats.items():
        label = data["label"].lower()
        if "damage" in label or "dmg" in label:
            damage[key] = data["text"]
    return damage


def _cache_file_for_url(cache_dir: Path, url: str) -> Path:
    safe_name = quote_plus(url, safe="")
    return cache_dir / f"{safe_name}.html"


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    heroes = read_heroes(args.input)
    cache_dir: Optional[Path] = None if args.no_cache else args.cache_dir
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for hero in heroes:
        try:
            html = fetch_html(hero.url, cache_dir=cache_dir)
            weapons = extract_weapons(html)
            results.append(
                {
                    "role": hero.role,
                    "name": hero.name,
                    "url": hero.url,
                    "weapons": weapons,
                }
            )
            print(f"Extracted weapons for {hero.name}", file=sys.stderr)
        except Exception as exc:
            print(
                f"Failed to extract weapons for {hero.name} ({hero.url}): {exc}",
                file=sys.stderr,
            )

    with args.output.open("w", encoding="utf-8") as outfile:
        json.dump(results, outfile, ensure_ascii=False, indent=2)
        outfile.write("\n")


if __name__ == "__main__":
    main()
