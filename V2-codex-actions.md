# Action

## 1

The script, steven-fight-v2.py has algorithm showing how a hero can attack a training dummy. 

The script needs the following information for a hero.

name
role
damage_per_bullet
bullets_per_shot
fire_rate
reload_time
ammo
armor_piercing = True
health
shields
armor

The CSV files hold this information spread across several files. Gather the information into one file called 'data-hero-details.csv'.

## 2

# Abilities
# Nano Boost
#   AMP: +50% dealt (only for Hero)
#   RED: -50% taken (only for Target Dummy)
# Amplification Matrix,
#   AMP: +100% dealt (only for Hero)
# Orbital Ray
#   AMP: +30% dealt (only for Hero)
# Caduceus Staff
#   AMP: +30% dealt  (only for Hero)
# Orb of Discord (defensive debuf)
#   AMP: +25% taken  (only for Hero, last ability to take effect)
#
# DMG:  100
# Nano: DMG * +50%
# RAY:  DMG * +30%
#    -------- 180
# ORB:  SUBTOTAL * 1.25 = 225
