#!/bin/env python

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

armor_mitigation_value = damage if armor_piercing else damage * .50 if damage < 14 else damage - 7
armor_protection = armor / armor_mitigation_value
bullets_til_death = math.ceil(((health + shields) / damage) + armor_protection)
reload_amount = math.floor(bullets_til_death / ammo)
#
# When ammo=5 and bullets_til_death=10, the reload_amount should be 1, not two.
#
if bullets_til_death % ammo == 0:
    reload_amount -= 1

reload_time_taken = reload_time * reload_amount
shots_til_death = math.ceil(bullets_til_death / bullets_per_shot)
seconds_til_death = (shots_til_death) / fire_rate + reload_time_taken

print(f"  {attacker} will defeat {defender} in {seconds_til_death} seconds.")