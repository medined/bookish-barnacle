## Fight Simulation Plan

1. **Data ingestion**
   - Parse `data-heroes.hidden.csv` to build the hero roster (role, name, cached URL) for random selection.
   - Load `hero-health.csv` for base health and armor pools; treat empty armor cells as zero.
   - Read `hero-weapons.json` to grab each hero’s primary weapon metadata (name, damage per shot, fire rate, ammo, reload).
   - Join the three sources into a single structure keyed by hero name; stop with an error if a hero is missing health or weapon data.

2. **Hero selection**
   - Use `random.sample` to pick two distinct heroes each run; allow a `--seed` flag for reproducibility.
   - Print each hero’s role, total health/armor, and weapon summary before the fight to explain matchup dynamics.

3. **Combat model (Overwatch-informed heuristics)**
   - Simulate turn-based rounds representing one second: each hero fires their primary weapon, applying sustained DPS (`damage_per_shot × shots_per_second`).
   - Track ammo and reloads; skip damage during reload turns based on weapon reload duration.
   - Apply armor mitigation: while armor remains, reduce incoming damage by 30% (or subtract 5 from hits over 10 damage) and drain armor before health.
   - Layer role passives:
     - Tanks: flat 10% incoming damage reduction once armor is gone (proxy for Tank passive damage mitigation).
     - DPS: +5% damage to represent their movement speed/accuracy passive.
     - Support: if they avoid damage for a round, add a small heal tick (e.g., 15 HP) to model their passive regeneration.
   - Optionally include low-probability crits for precision weapons (double damage on crit).

4. **Fight resolution**
   - Repeat rounds until one hero’s health ≤ 0; announce winner, remaining HP, and key events (armor breaks, crits, reload stalls).
   - If both heroes drop ≤ 0 in the same round, declare a draw or run a sudden-death roll.

5. **CLI ergonomics**
   - Provide flags like `--seed`, `--round-log/--no-log`, `--show-calcs` for verbosity control.
   - Keep data fully local (use `.cache` if deeper hero info is needed); avoid network requests.
   - Run via `uv run python fight.py` (and `uv add` for optional deps like `rich`) to stay aligned with project tooling.
