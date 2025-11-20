import math

# ASSUMPTIONS
#   ATTACKER
#     HAS ONE WEAPON
#     ALWAYS HITS
#     CONTINOUS RATE OF FIRE
#     NO FORCED CRITICALS
#     NO CRITICAL
#     NO EFFECTIVE RANGE (everyone is close to each other)
#     INSTANT DAMAGE
#     ALWAYS DEAL MAX DAMAGE (ie. fully charged)
#   DEFENDER
#     IS A TRAINING DUMMY

# # ATTACKER - TRACER
# damage = 6 # per bullet
# bullets_per_shot = 2
# fire_rate = 20
# reload_time = 1.0  # how long to reload the weapon.
# ammo = 40  # shots, not bullets
# armor_piercing = False
# # DEFENDER - REINHART
# health = 400
# shields = 0
# armor = 300


attacker = 'ANA'
damage = 75 # per bullet
bullets_per_shot = 1
fire_rate = 1.25
reload_time = 1.5
ammo = 5
armor_piercing = True
defender = 'REINHART'
health = 400
shields = 0
armor = 300

print(f"{attacker} vs {defender}")
print("==================")

# armor reduces damage by 50% but only to a max of 7.
armor_mitigation_value = damage if armor_piercing else damage * .50 if damage < 14 else damage - 7
print(f"{armor_mitigation_value=}")

# bad name
armor_protection = armor / armor_mitigation_value
print(f"{armor_protection=}")

bullets_til_death = math.ceil(((health + shields) / damage) + armor_protection)
print(f"{bullets_til_death=}")

# Wrong when BTD is twice AMMO.  modulo?
reload_amount = math.floor(bullets_til_death / ammo)
print(f"{reload_amount=}")

reload_time_taken = reload_time * reload_amount
print(f"{reload_time_taken=}")

# Shots Til Death Example.
# 15 BTD
# 1 BPS  15 STD
# 2 BPS   7 STD  - dies faster
shots_til_death = math.ceil(bullets_til_death / bullets_per_shot)
print(f"{shots_til_death=}")

# Seconds Til Death Example.
# 10 ShotsTD
# 1 FR  10 SecTD
# 2 FR   5 SecTD  - dies faster
seconds_til_death = (shots_til_death) / fire_rate + reload_time_taken
print(f"{seconds_til_death=:.2f}")
