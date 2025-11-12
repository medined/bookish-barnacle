from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import requests
from bs4 import BeautifulSoup

CSV_DEFAULT_PATH = Path("data-heroes.hidden.csv")
REQUEST_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 CodexBot/1.0"
)
NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")


@dataclass
class Hero:
    role: str
    name: str
    url: str


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract the first listed health value for each Overwatch hero."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=CSV_DEFAULT_PATH,
        help=f"CSV file with hero role, name, and url (default: {CSV_DEFAULT_PATH})",
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


def fetch_html(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.text


def extract_stats(html: str) -> dict[str, Optional[float | int]]:
    soup = BeautifulSoup(html, "html.parser")
    health = _extract_stat(soup, data_source="health", label_prefix="health")
    armor = _extract_stat(soup, data_source="armor", label_prefix="armor")

    if health is None:
        raise RuntimeError("Could not locate a numeric health value on the page.")

    return {"health": health, "armor": armor}


def _extract_stat(
    soup: BeautifulSoup, *, data_source: str, label_prefix: str
) -> Optional[float | int]:
    section = soup.find(attrs={"data-source": data_source})
    if section is not None:
        value = _first_number(section.get_text(" ", strip=True))
        if value is not None:
            return value

    for label in soup.select(".pi-data-label"):
        if label.get_text(strip=True).lower().startswith(label_prefix.lower()):
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
    number = float(match.group(0))
    return int(number) if number.is_integer() else number


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    heroes = read_heroes(args.input)

    writer = csv.writer(sys.stdout)
    writer.writerow(["role", "name", "health", "armor"])

    for hero in heroes:
        try:
            html = fetch_html(hero.url)
            stats = extract_stats(html)
            writer.writerow(
                [
                    hero.role,
                    hero.name,
                    stats["health"],
                    stats["armor"] if stats["armor"] is not None else "",
                ]
            )
        except Exception as exc:
            print(
                f"Failed to extract health for {hero.name} ({hero.url}): {exc}",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
