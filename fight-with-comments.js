const csvPath = "data-hero-details.csv";
// Cached inline CSV used when the external file is unavailable.
const INLINE_CSV = `role,name,damage_per_bullet,bullets_per_shot,fire_rate,reload_time,ammo,armor_piercing,health,shields,armor
Tank,D.Va,2,11,6.67,0,,True,225,0,325
Tank,Doomfist,5,11,3,0.4,4,True,375,0,0
Tank,Hazard,7.5,10,1.75,2.3,8,True,275,0,225
Tank,Junker Queen,8,10,1.33,1.5,8,True,375,0,0
Tank,Mauga,4,1,18,2.2,300,True,425,0,150
Tank,Orisa,14,1,10,3,,True,150,0,300
Tank,Ramattra,5,1,25,1,100,True,250,0,100
Tank,Reinhardt,100,1,1.04,0,,True,250,0,300
Tank,Roadhog,6.5,25,1.25,1.5,6,True,600,0,0
Tank,Sigma,15,2,0.67,0,,True,200,275,0
Tank,Winston,70,1,1,1.7,120,True,275,0,200
Tank,Wrecking Ball,5,1,25,1.6,80,True,300,150,175
Tank,Zarya,95,1,1,1.5,100,True,175,225,0
Damage,Ashe,35,1,3.9,0.5,12,True,250,0,0
Damage,Bastion,25,1,5,1.2,25,True,250,0,100
Damage,Cassidy,70,1,2,1.5,6,True,250,0,0
Damage,Echo,17,3,2.97,1.5,12,True,150,75,0
Damage,Freja,25,1,4.81,1.6,15,True,225,0,0
Damage,Genji,27,3,1.14,1.5,24,True,250,0,0
Damage,Hanzo,125,1,2,0,,True,250,0,0
Damage,Junkrat,45,1,1.5,1.5,5,True,250,0,0
Damage,Mei,5,1,20,1.5,140,True,300,0,0
Damage,Pharah,40,1,1.25,1.5,6,True,225,0,0
Damage,Reaper,5.75,20,2,1.5,8,True,300,0,0
Damage,Sojourn,9,1,16,1.2,45,True,225,0,0
Damage,Soldier: 76,19,1,9,1.5,30,True,250,0,0
Damage,Sombra,8,1,20,1.2,60,True,225,0,0
Damage,Symmetra,60,1,1,1.5,100,True,125,150,0
Damage,Torbjörn,70,1,1.96,2,18,True,225,0,75
Damage,Tracer,6,2,20,1,40,True,175,0,0
Damage,Venture,35,1,1.67,1.75,8,True,250,0,0
Damage,Widowmaker,14,1,10,1.5,35,True,225,0,0
Support,Ana,75,1,1.25,1.5,15,True,250,0,0
Support,Baptiste,25,3,1.7,1.5,36,True,250,0,0
Support,Brigitte,45,1,1.667,0,,True,200,0,50
Support,Illari,70,1,2,1.5,14,True,250,0,0
Support,Juno,7.5,12,1.29,1.5,180,True,75,150,0
Support,Kiriko,60,1,2,1,15,True,225,0,0
Support,Lifeweaver,6,2,11,1.5,100,True,200,50,0
Support,Lúcio,20,4,1.07,1.5,20,True,225,0,0
Support,Mercy,20,1,5,1.4,25,True,225,0,0
Support,Moira,65,1,1,0,,True,225,0,0
Support,Wuyang,10,1,3,1.5,20,True,225,0,0
Support,Zenyatta,50,1,2.5,1.5,25,True,75,175,0`;
// Attacker ability multipliers; "applyToSubtotal" controls when the multiplier is applied.
const ABILITIES = [
  {
    id: "nano",
    label: "Nano Boost",
    multiplier: 1.5,
    applyToSubtotal: false,
  },
  {
    id: "amp",
    label: "Amplification Matrix",
    multiplier: 2.0,
    applyToSubtotal: false,
  },
  {
    id: "ray",
    label: "Orbital Ray",
    multiplier: 1.3,
    applyToSubtotal: false,
  },
  {
    id: "caduceus",
    label: "Caduceus Staff",
    multiplier: 1.3,
    applyToSubtotal: false,
  },
  {
    id: "discord",
    label: "Orb of Discord",
    multiplier: 1.25,
    applyToSubtotal: true,
  },
];
const DEFENDER_ABILITIES = [
  { id: "nano_def", label: "Nano Boost", damageReduction: 0.5 },
];

async function loadCsv(path) {
  // Prefer the external CSV; fall back to the inline copy if fetch fails.
  try {
    const response = await fetch(path);
    if (response.ok) {
      const text = await response.text();
      if (text.trim()) {
        return text;
      }
    }
  } catch (err) {
    // fall back to inline data below
  }
  if (INLINE_CSV) {
    return INLINE_CSV;
  }
  throw new Error(`Failed to load ${path}`);
}

function parseCsv(text) {
  // Convert CSV text into an array of hero objects with numeric fields.
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const [headerLine, ...rows] = lines;
  const headers = headerLine.split(",");
  return rows.map((line) => {
    const cols = line.split(",");
    const record = {};
    headers.forEach((h, i) => {
      record[h] = cols[i] ?? "";
    });
    return {
      role: record.role,
      name: record.name,
      damagePerBullet: parseFloat(record.damage_per_bullet) || 0,
      bulletsPerShot: parseFloat(record.bullets_per_shot) || 1,
      fireRate: parseFloat(record.fire_rate) || 0,
      reloadTime: parseFloat(record.reload_time) || 0,
      ammo: record.ammo === "" ? Infinity : parseFloat(record.ammo),
      armorPiercing: String(record.armor_piercing).toLowerCase() === "true",
      health: parseFloat(record.health) || 0,
      shields: parseFloat(record.shields) || 0,
      armor: parseFloat(record.armor) || 0,
    };
  });
}

function armorMitigationPerBullet(damage, armorPiercing) {
  // Armor halves small hits or subtracts 7 from larger hits unless the shot pierces armor.
  if (armorPiercing) return damage;
  if (damage < 14) return damage * 0.5;
  return damage - 7;
}

function applyAbilities(baseDamage, activeIds) {
  // Multiply base damage by active attacker buffs; apply Discord after other multipliers.
  const baseMultipliers = ABILITIES.filter(
    (a) => activeIds.has(a.id) && !a.applyToSubtotal,
  ).map((a) => a.multiplier);
  const subtotalMultiplier = baseMultipliers.reduce((acc, m) => acc * m, 1);
  let damage = baseDamage * subtotalMultiplier;

  const discord = ABILITIES.find((a) => a.id === "discord");
  if (discord && activeIds.has(discord.id)) {
    damage *= discord.multiplier;
  }
  return damage;
}

function applyDefenderAbilities(damage, activeIds) {
  // Apply defender-side reductions to the incoming damage.
  let modified = damage;
  DEFENDER_ABILITIES.forEach((ability) => {
    if (activeIds.has(ability.id)) {
      modified *= ability.damageReduction;
    }
  });
  return modified;
}

function computeTimeToKill(
  attacker,
  defender,
  activeAttackerAbilityIds,
  activeDefenderAbilityIds,
) {
  // Core math: build damage per bullet, factor in armor, then compute bullets, reloads, and time-to-kill.
  const damage = applyDefenderAbilities(
    applyAbilities(attacker.damagePerBullet, activeAttackerAbilityIds),
    activeDefenderAbilityIds,
  );
  if (damage <= 0 || attacker.bulletsPerShot <= 0 || attacker.fireRate <= 0) {
    return {
      seconds: Infinity,
      bullets: Infinity,
      reloads: 0,
      note: "Missing or zeroed weapon stats.",
    };
  }

  const mitigation = armorMitigationPerBullet(damage, attacker.armorPiercing);
  const armorProtection = mitigation > 0 ? defender.armor / mitigation : 0;
  const bulletsTilDeath = Math.ceil(
    (defender.health + defender.shields) / damage + armorProtection,
  );

  let reloads = 0;
  if (Number.isFinite(attacker.ammo) && attacker.ammo > 0) {
    reloads = Math.floor(bulletsTilDeath / attacker.ammo);
    if (bulletsTilDeath % attacker.ammo === 0) reloads -= 1;
    reloads = Math.max(0, reloads);
  }

  const reloadTimeTaken = reloads * attacker.reloadTime;
  const shotsTilDeath = Math.ceil(bulletsTilDeath / attacker.bulletsPerShot);
  const secondsTilDeath = shotsTilDeath / attacker.fireRate + reloadTimeTaken;

  return {
    seconds: secondsTilDeath,
    bullets: bulletsTilDeath,
    reloads,
  };
}

function renderHeroCard(el, hero, title) {
  if (!hero) {
    el.innerHTML = `<h2>${title}</h2><p class="muted">Select a hero to see details.</p>`;
    return;
  }
  const lines =
    title === "Attacker"
      ? [
          `Damage per bullet: ${hero.damagePerBullet}`,
          `Bullets per shot: ${hero.bulletsPerShot}`,
          `Fire rate: ${hero.fireRate} shots/s`,
          `Reload time: ${hero.reloadTime || 0}s`,
          `Ammo: ${Number.isFinite(hero.ammo) ? hero.ammo : "∞"}`,
          `Armor piercing: ${hero.armorPiercing ? "yes" : "no"}`,
        ]
      : [
          `Health: ${hero.health}`,
          `Shields: ${hero.shields}`,
          `Armor: ${hero.armor}`,
        ];
  const heading = `<h2><span class="hero-name">${hero.name}</span> <span class="hero-role">${title}</span></h2>`;
  el.innerHTML = `${heading}${lines.map((line) => `<p>${line}</p>`).join("")}`;
}

function renderSummary(result, attacker, defender) {
  const summary = document.getElementById("summary");
  const noteEl = document.getElementById("note");
  if (!attacker || !defender) {
    summary.innerHTML = "";
    noteEl.textContent = "";
    return;
  }
  if (!result || !isFinite(result.seconds)) {
    summary.innerHTML = `<div class="metric"><h4>Time to kill</h4><strong class="warning">N/A</strong></div>`;
    noteEl.textContent = "Unable to compute: missing stats for attacker.";
    return;
  }
  const prevSignature = summary.dataset.signature || "";
  const signature = `${result.seconds.toFixed(2)}-${result.bullets}-${result.reloads}`;
  summary.innerHTML = `
          <div class="metric">
            <h4>Time to kill</h4>
            <strong>${result.seconds.toFixed(2)} s</strong>
          </div>
          <div class="metric">
            <h4>Bullets needed</h4>
            <strong>${result.bullets}</strong>
            <div class="muted">Reloads: ${result.reloads}</div>
          </div>
        `;
  summary.dataset.signature = signature;
  if (signature !== prevSignature) {
    const ttkCard = summary.querySelector(".metric:nth-child(1)");
    const bulletsCard = summary.querySelector(".metric:nth-child(2)");
    [ttkCard, bulletsCard].forEach((el) => {
      if (!el) return;
      // Restart the flash animation by forcing a reflow before re-adding the class.
      el.classList.remove("flash");
      void el.offsetWidth; // force reflow
      el.classList.add("flash");
    });
  }
}

async function init() {
  const text = await loadCsv(csvPath);
  const heroes = parseCsv(text);
  const attackerSelect = document.getElementById("attackerSelect");
  const defenderSelect = document.getElementById("defenderSelect");
  const attackerAbilityToggles = document.getElementById(
    "attackerAbilityToggles",
  );
  const defenderAbilityToggles = document.getElementById(
    "defenderAbilityToggles",
  );
  const activeAttackerAbilities = new Set();
  const activeDefenderAbilities = new Set();

  heroes.forEach((hero) => {
    // Populate both dropdowns with the same hero list.
    const optA = document.createElement("option");
    optA.value = hero.name;
    optA.textContent = hero.name;
    const optB = optA.cloneNode(true);
    attackerSelect.appendChild(optA);
    defenderSelect.appendChild(optB);
  });

  // Limit the dropdown viewport to roughly 5 rows while keeping all options available via scrolling.
  attackerSelect.setAttribute("size", "5");
  defenderSelect.setAttribute("size", "5");

  attackerSelect.selectedIndex = 0;
  defenderSelect.selectedIndex = heroes.length > 1 ? 1 : 0;

  const attackerCard = document.getElementById("attackerCard");
  const defenderCard = document.getElementById("defenderCard");
  const form = document.getElementById("fightForm");

  ABILITIES.forEach((ability) => {
    // Build buttons that toggle each attacker buff on/off.
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ability-button";
    btn.textContent = ability.label;
    btn.dataset.abilityId = ability.id;
    btn.addEventListener("click", () => {
      if (activeAttackerAbilities.has(ability.id)) {
        activeAttackerAbilities.delete(ability.id);
        btn.classList.remove("active");
      } else {
        activeAttackerAbilities.add(ability.id);
        btn.classList.add("active");
      }
      update();
    });
    attackerAbilityToggles.appendChild(btn);
  });

  DEFENDER_ABILITIES.forEach((ability) => {
    // Build buttons that toggle each defender mitigation on/off.
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ability-button";
    btn.textContent = ability.label;
    btn.dataset.abilityId = ability.id;
    btn.addEventListener("click", () => {
      if (activeDefenderAbilities.has(ability.id)) {
        activeDefenderAbilities.delete(ability.id);
        btn.classList.remove("active");
      } else {
        activeDefenderAbilities.add(ability.id);
        btn.classList.add("active");
      }
      update();
    });
    defenderAbilityToggles.appendChild(btn);
  });

  function update() {
    // Whenever selections or toggles change, recalc stats and repaint the UI.
    const attacker = heroes.find((h) => h.name === attackerSelect.value);
    const defender = heroes.find((h) => h.name === defenderSelect.value);
    renderHeroCard(attackerCard, attacker, "Attacker");
    renderHeroCard(defenderCard, defender, "Defender");
    const result =
      attacker && defender
        ? computeTimeToKill(
            attacker,
            defender,
            activeAttackerAbilities,
            activeDefenderAbilities,
          )
        : null;
    renderSummary(result, attacker, defender);
  }

  attackerSelect.addEventListener("change", update);
  defenderSelect.addEventListener("change", update);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
  });

  update();
}

init().catch((err) => {
  document.getElementById("summary").innerHTML =
    '<div class="metric"><h4>Error</h4><strong class="warning">Could not load hero data.</strong></div>';
  console.error(err);
});
