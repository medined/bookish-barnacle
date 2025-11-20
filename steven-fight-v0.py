# ASSUMPTIONS
#   ATTACKER
#     HAS ONE WEAPON
#   DEFENDER
#     IS A TRAINING DUMMY

# ATTACKER
damage = 6 # per bullet
bullets_per_shot = 2
fire_rate = 20
reload_time = 1.0  # how long to reload the weapon.

# DEFENDER
health = 400
shields = 0
armor = 300

print("REINHART vs TRACER")
print("==================")

# armor reduces damage by 50% but only to a max of 7.
armor_mitigation_value = damage * .50 if damage < 14 else damage - 7
print(f"{armor_mitigation_value=}")

# bad name
armor_protection = armor / armor_mitigation_value
print(f"{armor_protection=}")

bullets_til_death = ((health + shields) / damage) + armor_protection
print(f"{bullets_til_death=:.2f}")

shots_til_death = bullets_til_death / bullets_per_shot
print(f"{shots_til_death=:.2f}")

seconds_til_death = shots_til_death / fire_rate
print(f"{seconds_til_death=:.2f}")
