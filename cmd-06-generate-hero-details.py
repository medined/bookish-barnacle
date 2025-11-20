from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable

HEALTH_CSV = Path("hero-health.csv")
SHIELDS_CSV = Path("hero-shields.csv")
WEAPONS_JSON = Path("hero-weapons.json")
OUTPUT_CSV = Path("data-hero-details.csv")

NUMBER_PATTERN = re.compile(r"[-+]?\d*\.?\d+")


def parse_numbers(value: Any) -> list[float]:
    if value is None:
        return []
    return [float(match) for match in NUMBER_PATTERN.findall(str(value).replace(",", ""))]


def parse_number(value: Any) -> float | None:
    numbers = parse_numbers(value)
    return numbers[0] if numbers else None


def format_number(value: float | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def parse_fire_rate(text: str | None) -> float:
    if not text:
        return 0.0

    lowered = text.lower()
    numbers = parse_numbers(text)
    if not numbers:
        return 0.0

    if any(keyword in lowered for keyword in ("shots/s", "shots per second", "shots/second", "rounds per second", "rounds/s", "volleys/s")):
        return max(numbers)

    if ("shot per" in lowered or "swing per" in lowered or "shot every" in lowered or "swing every" in lowered) and "second" in lowered:
        if len(numbers) >= 2 and numbers[1] > 0:
            return numbers[0] / numbers[1]
        if numbers[0] > 0:
            return 1 / numbers[0]

    if "seconds" in lowered or "second" in lowered:
        seconds = numbers[0]
        if seconds > 0:
            return 1 / seconds

    return max(numbers)


def pick_weapon(weapons: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    for weapon in weapons:
        damage_text = (weapon.get("damage") or {}).get("damage")
        if damage_text:
            return weapon
    return next(iter(weapons), None)


def load_weapon_stats() -> dict[str, dict[str, float | None]]:
    with WEAPONS_JSON.open(encoding="utf-8") as handle:
        records = json.load(handle)

    stats: dict[str, dict[str, float | None]] = {}
    for record in records:
        weapon = pick_weapon(record.get("weapons") or [])
        if not weapon:
            continue

        damage_text = (weapon.get("damage") or {}).get("damage", "")
        damage_per_bullet = parse_number(damage_text) or 0.0
        bullets_per_shot = parse_number(weapon.get("shots_per_volley")) or 1.0
        fire_rate = parse_fire_rate(weapon.get("rate_of_fire"))

        # Beam-style weapons list DPS in the damage field; treat that as damage/shot at 1 shot per second.
        if fire_rate == 0 and "per second" in str(damage_text).lower():
            fire_rate = 1.0

        reload_time = parse_number(weapon.get("reload_time")) or 0.0
        ammo = parse_number(weapon.get("ammo"))

        stats[record["name"]] = {
            "damage_per_bullet": damage_per_bullet,
            "bullets_per_shot": bullets_per_shot,
            "fire_rate": fire_rate,
            "reload_time": reload_time,
            "ammo": ammo,
        }
    return stats


def load_health() -> list[dict[str, Any]]:
    with HEALTH_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_shields() -> dict[str, float]:
    shields: dict[str, float] = {}
    with SHIELDS_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            shields[row["name"]] = float(row["shields"]) if row.get("shields") else 0.0
    return shields


def build_rows() -> list[dict[str, Any]]:
    health_rows = load_health()
    shield_map = load_shields()
    weapon_map = load_weapon_stats()

    rows: list[dict[str, Any]] = []
    for row in health_rows:
        name = row["name"]
        weapon_stats = weapon_map.get(name)
        if not weapon_stats:
            continue

        health = float(row["health"]) if row.get("health") else 0.0
        armor = float(row["armor"]) if row.get("armor") else 0.0
        shields = shield_map.get(name, 0.0)

        rows.append(
            {
                "role": row["role"],
                "name": name,
                "damage_per_bullet": weapon_stats["damage_per_bullet"],
                "bullets_per_shot": weapon_stats["bullets_per_shot"],
                "fire_rate": weapon_stats["fire_rate"],
                "reload_time": weapon_stats["reload_time"],
                "ammo": weapon_stats["ammo"],
                "armor_piercing": True,
                "health": health,
                "shields": shields,
                "armor": armor,
            }
        )
    return rows


def write_csv(rows: list[dict[str, Any]]) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "role",
        "name",
        "damage_per_bullet",
        "bullets_per_shot",
        "fire_rate",
        "reload_time",
        "ammo",
        "armor_piercing",
        "health",
        "shields",
        "armor",
    ]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "role": row["role"],
                    "name": row["name"],
                    "damage_per_bullet": format_number(row["damage_per_bullet"]),
                    "bullets_per_shot": format_number(row["bullets_per_shot"]),
                    "fire_rate": format_number(row["fire_rate"]),
                    "reload_time": format_number(row["reload_time"]),
                    "ammo": format_number(row["ammo"]),
                    "armor_piercing": row["armor_piercing"],
                    "health": format_number(row["health"]),
                    "shields": format_number(row["shields"]),
                    "armor": format_number(row["armor"]),
                }
            )


def main() -> None:
    rows = build_rows()
    if not rows:
        raise SystemExit("No hero data found; cannot write CSV.")
    write_csv(rows)


if __name__ == "__main__":
    main()
