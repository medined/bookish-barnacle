from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, Iterable, Optional
from urllib.parse import quote

from bs4 import BeautifulSoup


ROOT = Path(__file__).parent
HERO_SOURCE = ROOT / "data-heroes.hidden.csv"
CACHE_DIR = ROOT / ".cache" / "hero-pages"
OUTPUT = ROOT / "hero-shields.csv"

NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")


def read_heroes() -> Iterable[Dict[str, str]]:
    with HERO_SOURCE.open(encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def page_path(url: str) -> Path:
    return CACHE_DIR / f"{quote(url, safe='')}.html"


def extract_shields(soup: BeautifulSoup) -> Optional[float | int]:
    for key in ("shield", "shields"):
        section = soup.find(attrs={"data-source": key})
        if section:
            value = _first_number(section.get_text(" ", strip=True))
            if value is not None:
                return value

    for label in soup.select(".pi-data-label"):
        text = label.get_text(" ", strip=True).lower()
        if not text.startswith("shield"):
            continue
        value_container = label.find_next(class_="pi-data-value")
        if value_container:
            value = _first_number(value_container.get_text(" ", strip=True))
            if value is not None:
                return value
    return None


def _first_number(text: str) -> Optional[float | int]:
    match = NUMBER_PATTERN.search(text)
    if not match:
        return None
    value = float(match.group(0))
    return int(value) if value.is_integer() else value


def main() -> None:
    rows = []
    for hero in read_heroes():
        file_path = page_path(hero["url"])
        if not file_path.exists():
            continue
        soup = BeautifulSoup(file_path.read_text(encoding="utf-8"), "html.parser")
        shields = extract_shields(soup)
        rows.append(
            {
                "role": hero["role"],
                "name": hero["name"],
                "shields": shields if shields is not None else "",
            }
        )

    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["role", "name", "shields"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
