from __future__ import annotations

import argparse
import csv
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent
ROSTER_CSV = DATA_DIR / "data-heroes.hidden.csv"
HEALTH_CSV = DATA_DIR / "hero-health.csv"
WEAPONS_JSON = DATA_DIR / "hero-weapons.json"

NUMBER_PATTERN = re.compile(r"[-+]?\d*\.?\d+")


def parse_number(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace(",", "")
    match = NUMBER_PATTERN.search(cleaned)
    if match:
        return float(match.group())
    return None


def parse_all_numbers(value: Optional[str]) -> List[float]:
    if value is None:
        return []
    cleaned = str(value).replace(",", "")
    return [float(match) for match in NUMBER_PATTERN.findall(cleaned)]


@dataclass
class Weapon:
    name: str
    shots_per_second: float
    damage_per_shot: float
    dps_firing: float
    clip_size: Optional[float]
    reload_time: float
    crit_chance: float
    description: str


@dataclass
class HeroStats:
    role: str
    name: str
    url: str
    health: float
    armor: float
    weapon: Weapon


class FighterState:
    def __init__(self, hero: HeroStats) -> None:
        self.hero = hero
        self.health = float(hero.health)
        self.armor = float(hero.armor)
        self.max_health = float(hero.health)
        self.max_armor = float(hero.armor)
        self.weapon = hero.weapon
        self.ammo: Optional[float] = None if hero.weapon.clip_size is None else float(hero.weapon.clip_size)
        self.reload_timer: float = 0.0
        self.took_damage_this_round = False

    @property
    def alive(self) -> bool:
        return self.health > 0

    def attack(self) -> Tuple[float, str]:
        """Return raw damage dealt this round plus a short description."""
        if not self.alive:
            return 0.0, "Eliminated"

        if self.reload_timer > 0:
            self.reload_timer = max(0.0, self.reload_timer - 1.0)
            if self.reload_timer == 0 and self.weapon.clip_size is not None:
                self.ammo = float(self.weapon.clip_size)
            return 0.0, "Reloading"

        shots_per_second = self.weapon.shots_per_second
        log: List[str] = []

        # Base damage reference before crits
        damage = 0.0
        if shots_per_second <= 0 and self.weapon.dps_firing > 0:
            damage = self.weapon.dps_firing
            log.append("sustained DPS")
        else:
            if self.weapon.clip_size is None:
                shots_fired = shots_per_second
            else:
                if self.ammo is None:
                    self.ammo = float(self.weapon.clip_size)
                available = min(self.ammo, shots_per_second)
                shots_fired = available
                self.ammo -= available
                if self.ammo <= 0 and self.weapon.reload_time > 0:
                    self.reload_timer = self.weapon.reload_time
                    self.ammo = 0.0
                    log.append("clip empty")
            damage = max(0.0, shots_fired) * self.weapon.damage_per_shot
            if self.weapon.clip_size is not None:
                log.append(f"{shots_fired:.1f} shots")

        crit = False
        if self.weapon.crit_chance > 0 and random.random() < self.weapon.crit_chance:
            damage *= 2
            crit = True
            log.append("CRIT")

        if self.hero.role.lower() == "damage":
            damage *= 1.05
            log.append("+5% DPS passive")

        if crit:
            descriptor = ", ".join(log)
        else:
            descriptor = ", ".join(log) if log else "standard fire"
        return damage, descriptor

    def apply_damage(self, incoming_damage: float) -> Tuple[float, bool]:
        """Apply incoming damage, return net damage taken and armor-break flag."""
        if not self.alive or incoming_damage <= 0:
            self.took_damage_this_round = False
            return 0.0, False

        armor_before = self.armor
        total_taken = 0.0
        effective_damage = incoming_damage

        if self.armor > 0:
            effective_damage *= 0.70  # 30% mitigation while armor remains
            armor_absorb = min(self.armor, effective_damage)
            self.armor -= armor_absorb
            remaining = effective_damage - armor_absorb
            self.health -= remaining
            total_taken = effective_damage
        else:
            if self.hero.role.lower() == "tank":
                effective_damage *= 0.90  # tank passive mitigation once armor is gone
            self.health -= effective_damage
            total_taken = effective_damage

        self.health = max(self.health, 0.0)
        self.took_damage_this_round = total_taken > 0
        armor_broken = armor_before > 0 and self.armor == 0
        return total_taken, armor_broken

    def apply_support_regen(self) -> Optional[float]:
        if self.hero.role.lower() != "support":
            return None
        if self.took_damage_this_round or not self.alive:
            return None
        missing = self.max_health - self.health
        if missing <= 0:
            return None
        heal = min(15.0, missing)
        self.health += heal
        return heal


def load_roster() -> Dict[str, Dict[str, str]]:
    roster: Dict[str, Dict[str, str]] = {}
    with ROSTER_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            roster[row["name"]] = {
                "role": row["role"],
                "url": row["url"],
            }
    return roster


def load_health() -> Dict[str, Dict[str, float]]:
    health_data: Dict[str, Dict[str, float]] = {}
    with HEALTH_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            health = float(row["health"]) if row["health"] else 0.0
            armor = float(row["armor"]) if row["armor"] else 0.0
            health_data[row["name"]] = {
                "health": health,
                "armor": armor,
            }
    return health_data


def parse_weapon_entry(entry: dict) -> Weapon:
    rof_text = entry.get("rate_of_fire") or ""
    rate_value = parse_number(rof_text) or 0.0
    shots_per_volley = parse_number(entry.get("shots_per_volley")) or 1.0
    descriptor = entry.get("effect_type") or ""
    additional_details = entry.get("additional_details") or []
    damage_values = parse_all_numbers((entry.get("damage") or {}).get("damage"))
    dps_hint = None
    for detail in additional_details:
        if "damage per second" in detail.lower():
            dps_hint = parse_number(detail)
            break

    rof_lower = rof_text.lower()
    shots_per_second = rate_value
    if "volley" in rof_lower or "burst" in rof_lower:
        shots_per_second = rate_value * shots_per_volley

    damage_per_shot = 0.0
    if shots_per_second > 0 and dps_hint:
        damage_per_shot = dps_hint / shots_per_second
    elif damage_values:
        damage_per_shot = max(damage_values)
    else:
        damage_per_shot = dps_hint or 0.0

    if shots_per_second == 0 and damage_per_shot > 0:
        shots_per_second = 1.0

    dps_firing = dps_hint or (damage_per_shot * shots_per_second)
    ammo_raw = entry.get("ammo")
    clip_size = parse_number(ammo_raw)
    reload_time = parse_number(entry.get("reload_time")) or 0.0
    headshot = entry.get("headshot") or ""
    keywords = entry.get("keywords") or []
    crit_chance = 0.1 if ("✓" in headshot or "critical" in [k.lower() for k in keywords]) else 0.0
    return Weapon(
        name=entry.get("name", "Unknown Weapon"),
        shots_per_second=shots_per_second,
        damage_per_shot=damage_per_shot,
        dps_firing=dps_firing,
        clip_size=clip_size,
        reload_time=reload_time,
        crit_chance=crit_chance,
        description=descriptor,
    )


def load_weapons() -> Dict[str, Weapon]:
    with WEAPONS_JSON.open(encoding="utf-8") as handle:
        records = json.load(handle)
    hero_weapons: Dict[str, Weapon] = {}
    for record in records:
        weapons = record.get("weapons") or []
        if not weapons:
            continue
        # Pick the first weapon as default; could be extended to smarter selection
        weapon = parse_weapon_entry(weapons[0])
        hero_weapons[record["name"]] = weapon
    return hero_weapons


def assemble_heroes() -> List[HeroStats]:
    roster = load_roster()
    health = load_health()
    weapons = load_weapons()
    heroes: List[HeroStats] = []
    for name, info in roster.items():
        if name not in health or name not in weapons:
            continue
        heroes.append(
            HeroStats(
                role=info["role"],
                name=name,
                url=info["url"],
                health=health[name]["health"],
                armor=health[name]["armor"],
                weapon=weapons[name],
            )
        )
    if len(heroes) < 2:
        raise RuntimeError("Insufficient hero data to run a fight.")
    return heroes


def describe_fighter(hero: HeroStats) -> str:
    return (
        f"{hero.name} ({hero.role}) — {hero.health:.0f} HP + {hero.armor:.0f} armor | "
        f"{hero.weapon.name}: {hero.weapon.dps_firing:.1f} DPS"
    )


def simulate_fight(hero_a: HeroStats, hero_b: HeroStats, max_rounds: int) -> None:
    fighter_a = FighterState(hero_a)
    fighter_b = FighterState(hero_b)

    print("Selected heroes:")
    print(f"  {describe_fighter(hero_a)}")
    print(f"  {describe_fighter(hero_b)}")
    print("=" * 60)

    round_number = 1
    while fighter_a.alive and fighter_b.alive and round_number <= max_rounds:
        dmg_a, info_a = fighter_a.attack()
        dmg_b, info_b = fighter_b.attack()

        taken_b, armor_break_b = fighter_b.apply_damage(dmg_a)
        taken_a, armor_break_a = fighter_a.apply_damage(dmg_b)

        regen_a = fighter_a.apply_support_regen()
        regen_b = fighter_b.apply_support_regen()

        print(f"Round {round_number}")
        print(
            f"  {hero_a.name} deals {taken_b:.1f} dmg ({info_a}) "
            f"-> {hero_b.name} HP {fighter_b.health:.1f} / Armor {fighter_b.armor:.1f}"
        )
        if armor_break_b:
            print(f"    {hero_b.name}'s armor is broken!")
        if regen_b:
            print(f"    {hero_b.name} regains {regen_b:.1f} HP from Support passive.")

        print(
            f"  {hero_b.name} deals {taken_a:.1f} dmg ({info_b}) "
            f"-> {hero_a.name} HP {fighter_a.health:.1f} / Armor {fighter_a.armor:.1f}"
        )
        if armor_break_a:
            print(f"    {hero_a.name}'s armor is broken!")
        if regen_a:
            print(f"    {hero_a.name} regains {regen_a:.1f} HP from Support passive.")

        print("-" * 60)

        round_number += 1

    if fighter_a.alive and not fighter_b.alive:
        print(f"{hero_a.name} wins with {fighter_a.health:.1f} HP remaining!")
    elif fighter_b.alive and not fighter_a.alive:
        print(f"{hero_b.name} wins with {fighter_b.health:.1f} HP remaining!")
    elif not fighter_a.alive and not fighter_b.alive:
        print("Both heroes fall simultaneously — it's a draw!")
    else:
        print("Stalemate reached — maximum rounds exceeded.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate an Overwatch 2 hero duel.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    parser.add_argument("--max-rounds", type=int, default=30, help="Maximum rounds before declaring a draw.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    heroes = assemble_heroes()
    hero_a, hero_b = random.sample(heroes, 2)
    simulate_fight(hero_a, hero_b, args.max_rounds)


if __name__ == "__main__":
    main()
