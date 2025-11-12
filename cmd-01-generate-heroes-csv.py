from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

BASE_URL = "https://overwatch.fandom.com"
HEROES_URL = f"{BASE_URL}/wiki/Heroes"
REQUEST_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 CodexBot/1.0"
)
OUTPUT_PATH = Path("data-heroes.hidden.csv")


def fetch_html(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def extract_heroes(html: str) -> List[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    navbox = soup.select_one("table.navbox")
    if navbox is None:
        raise RuntimeError("Could not find the hero navbox on the Heroes page.")

    heroes: List[dict[str, str]] = []
    current_role: Optional[str] = None

    for row in navbox.select("tr"):
        header = row.find("th", class_="navbox-group")
        if header:
            current_role = header.get_text(strip=True)

        if not current_role:
            continue

        for cell in row.find_all("td"):
            link = _first_named_link(cell)
            if not link:
                continue

            name = link.get_text(strip=True)
            href = urljoin(BASE_URL, link["href"])
            heroes.append({"role": current_role, "name": name, "url": href})

    if not heroes:
        raise RuntimeError("No hero entries were parsed from the navbox.")

    return heroes


def _first_named_link(cell: Tag) -> Optional[Tag]:
    for link in cell.select("a[href]"):
        text = link.get_text(strip=True)
        href = link.get("href", "")
        if not text or not href.startswith("/wiki/"):
            continue
        if text in {"Tank", "Damage", "Support"}:
            continue
        return link
    return None


def main() -> None:
    html = fetch_html(HEROES_URL)
    heroes = extract_heroes(html)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["role", "name", "url"])
        writer.writeheader()
        writer.writerows(heroes)

    for hero in heroes:
        print(f"{hero['name']} ({hero['role']}): {hero['url']}")


if __name__ == "__main__":
    main()
