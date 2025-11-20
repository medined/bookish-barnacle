from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import quote

from bs4 import BeautifulSoup


ROOT = Path(__file__).parent
HERO_SOURCE = ROOT / "data-heroes.hidden.csv"
CACHE_DIR = ROOT / ".cache" / "hero-pages"
OUTPUT = ROOT / "hero-ability-damage.csv"

TARGET_LABELS = {
    "dmg. amplification": "damage_amplification",
    "dmg. reduction": "damage_reduction",
    "duration": "duration",
}


def iter_heroes() -> Iterable[Dict[str, str]]:
    with HERO_SOURCE.open(encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def hero_page_path(url: str) -> Path:
    return CACHE_DIR / f"{quote(url, safe='')}.html"


def section_title(node) -> str:
    current = node
    while current:
        current = current.previous_sibling
        if current is None:
            break
        name = getattr(current, "name", None)
        if name and name.lower().startswith("h"):
            return current.get_text(strip=True)
    return ""


def read_ability_rows(soup: BeautifulSoup) -> Iterable[Dict[str, str]]:
    for ability in soup.select(".ability-details"):
        header = ability.select_one(".ability-box .header")
        if not header:
            continue
        if section_title(ability).strip().lower() != "abilities":
            continue
        name = header.find(string=True, recursive=False)
        if name:
            ability_name = name.strip()
        else:
            ability_name = header.get_text(" ", strip=True)
        ability_name = " ".join(ability_name.split())
        if not ability_name:
            continue

        stats: Dict[str, str] = {}
        for row in ability.select(".data-row"):
            label_el = row.select_one(".data-row-header")
            value_el = row.select_one(".data-row-value")
            if not label_el or not value_el:
                continue
            label = " ".join(label_el.get_text(" ", strip=True).split())
            label = label.rstrip(":").strip().lower()
            key = TARGET_LABELS.get(label)
            if not key:
                continue
            value = " ".join(value_el.get_text(" ", strip=True).split())
            stats[key] = value

        has_amp = bool(stats.get("damage_amplification"))
        has_red = bool(stats.get("damage_reduction"))
        if not (has_amp or has_red):
            continue

        if stats:
            yield {
                "ability_name": ability_name,
                **stats,
            }


def main() -> None:
    rows: List[Dict[str, str]] = []
    for hero in iter_heroes():
        page_path = hero_page_path(hero["url"])
        if not page_path.exists():
            continue
        soup = BeautifulSoup(page_path.read_text(encoding="utf-8"), "html.parser")
        for ability in read_ability_rows(soup):
            rows.append(
                {
                    "hero_name": hero["name"],
                    "ability_name": ability["ability_name"],
                    "damage_amplification": ability.get("damage_amplification", ""),
                    "damage_reduction": ability.get("damage_reduction", ""),
                    "duration": ability.get("duration", ""),
                }
            )

    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "hero_name",
                "ability_name",
                "damage_amplification",
                "damage_reduction",
                "duration",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
