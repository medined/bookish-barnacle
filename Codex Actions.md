# Codex Actions

## 1

The https://overwatch.fandom.com/wiki/Heroes web page has a list of heroes on the left side of the page. The first hero is "Juno" and the last hero is "Wrecking Ball". Write a script using beutiful soup to script the list of heroes and the website that is linked to each name.

---

update main.py to save the list to a csv file. Call it data-heroes.hidden.csv

## 2

create a script that uses the URL from data-heroes.hidden.csv to extract the health for each hero. There might be multiple health values. take the first one. Ignore any information that is not a number.

for the doomfirst character, The health value you extract should be 375.

---

some if the pages might have armor values? can you check?

## 3

Look at the page for the Hazard character at https://overwatch.fandom.com/wiki/Hazard. He weapon is "Bonespur"  which seems to be in the Abilities section. There is an anchor called "Abilities" and inside that section is information where type is "weapon". Is it possible to reliably find that section and extract information about the weapon on the hero pages?

---

Great. Write a script that extracts weapons for each hero in the data-heroes.hidden.csv and saves the information to a json file. Extract these fields:

effect_type
blocked_by - this should be a list.
damage - there are various type of damage, so make this a dict.
falloff_range
headshot
rate_of_fire
shots_per_volley
ammo_comsumption
ammo
reload_time
projectile_speed
projectile_radious
spread - this is a list also.
additional_details - a list
keywords - a list

---

i like the idea of a cache for the hero detail page ... implement that feature.

---

generate the weapons json for every hero.

## 5

generae a plan for a script that picks two heroes at random from the data-heroes.hidden.csv file to fight each other. Use the heroes health, armor, and weapons from the relevant csv file. Use what you know about the overwatch 2 game to inform the plan.

---

turn fight.py into a one-page html/javascript application. let the user pick the two heroes from lists. Then have them fight and display the rounds and results. I don't want a web server ... just the standalone html page.

---

does fight.html have the hero list from data-heroes.hidden.csv embedded into the page? Currently, the dropdown form elements have no content.

---

the selects are empty. can you use selenium to test the html?

---

add another button next to "fight" called "Duel 100" that runs 100 fights then displays the win/lose rate for each hero. The idea is to get an average over many fights.

---

are the duels always two rounds long or is the web page just displaying the first two rounds out of many?

---

vertify that armor is being accounted for. What effect does armor have?

## 6

I tried to update the hero-data json inside fight.html but I broke something. Now the hero dropdowns have no entries. Use selenium and unit tests to fix my mistake.

## 7

I need to extract the abilities of each hero in the data-heroes.hidden.csv file. I am only interested in ability that include "Dmg. amplification", "Dmg. reduction", and "duration". Look at Zenyatta as an example. She has an "Orb of Discord" ability with "Dmg. amplification" and "duration". Can you look at each hero's page, check for those three values, then find the ability name and create a csv file of <hero name>, <ability name>, <damage amplification>, <damage reduction>, <duration>. Let me know if anything is unclear.

---

that's nearly correct. I was not clear enough. 

Only write the information to hero-ability-damage.csv if the ability has values for amplification and/or reduction.

---

just like you extracted the abilities, now extract the shield information.  Using Zenyatta as an example, she has shields of 175.

