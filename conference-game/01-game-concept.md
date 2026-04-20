# 01 - Game Concept & Rules

## Elevator Pitch

"Can you spot and diagnose what's costing this plant money?" — A timed challenge where hydropower operators look at a Naia-style dashboard showing production, rain, and river flow, draw expected production lines to identify losses, classify each loss by category and subcategory, and estimate loss size. The fastest and most accurate diagnostician wins.

## Goals

1. **Engagement**: Draw conference attendees to the Naia booth with a competitive, fun challenge
2. **Discovery**: Let operators experience Naia's core value proposition (loss identification = lost revenue) hands-on
3. **Lead generation**: Capture contact details of qualified prospects (plant operators)
4. **Brand recall**: Participants walk away remembering Naia as "the tool that shows you where you're losing money"

## Core Gameplay

### Game Flow

1. **START** — Player presses the start button on the welcome screen
2. **Intro Video** — Short video showing the plant (configurable per scenario, stored locally). Gives the player context: location, river, capacity, typical operation
3. **GO!** — Player presses "GO" when ready
4. **Gameplay** — Draw loss areas, classify causes, estimate sizes (5 minutes)
5. **Summary Result** — Quick score overview with rank
6. **Add Email** — On-screen keyboard to enter email address for detailed results
7. **Classement** — Live leaderboard + button to start a new game. Detailed results sent by email only

### What the Player Sees

A Naia-style dashboard showing a plant over ~2 months:
- **Production bars** (daily energy, kWh) — the main chart
- **Rain indicator** (inverted bars above the chart) — precipitation pattern
- **River flow indicator** (line overlaid) — water availability
- **Maintenance event dots** — clickable dots on the production line showing interventions (e.g., "restart turbine", "clean grille"). These give contextual clues
- **Left panel** with toggleable additional indicators (extra flow stations, comparators)

### What the Player Does

1. **Identify losses**: Draw a line on the production graph indicating what production *should* have been. The gap between this line and actual production = the loss area
2. **Classify each loss**: Select the **category** (6 options) and **subcategory** (3-5 options per category) from a dropdown
3. **The loss size is automatically calculated** from the drawn line vs. actual production (surface area between the curves)
4. Repeat for all losses they can find within the time limit

### What the Player Is Reasoning About

| They see... | Clues to use | Likely cause |
|-------------|-------------|--------------|
| High rain + high flow + zero production | Flow was there, production stopped suddenly | Breakdown |
| Zero production on a calm, normal day | No weather event, perhaps a maintenance dot nearby | Maintenance |
| Extreme rain + extreme flow + zero production | Flood conditions visible in rain/flow data | Environmental |
| Production at 50% despite full flow | No external reason, operator choice | Operational |
| Flat-capped production despite high flow | Comparator plant also capped → grid issue | Grid/Constraint |
| Zero readings but flow is normal, gap pattern | Maintenance dot says "sensor replaced" | Data Issue |

### Maintenance Event Dots

Clickable dots placed on the production line at specific dates. When clicked, a popup shows a short maintenance note (e.g., "Restart turbine", "Clean intake grille", "Replace flow sensor"). These:
- Give contextual clues for diagnosis (a "restart turbine" dot next to a zero-production period → breakdown)
- Mirror real Naia where operators log interventions
- Are provided by Bernard in the scenario data

## Scoring System

Scoring is on **3 levels** per identified loss area:

### Level 1: Category (max 10 pts per loss)

| Diagnosis | Points |
|-----------|--------|
| Correct category | +10 |
| Wrong category | -5 |

### Level 2: Subcategory (max 5 pts per loss)

| Diagnosis | Points |
|-----------|--------|
| Correct subcategory | +5 |
| Wrong subcategory | -2 |

### Level 3: Loss Size Estimation (max 10 pts per loss)

Based on accuracy of the drawn line vs. Bernard's reference loss size:

| Accuracy | Points | Formula |
|----------|--------|---------|
| 100% | 10 | `max(0, (accuracy - 0.80) / 0.20 × 10)` |
| 98% | 9 | Rounded to nearest integer |
| 90% | 5 | |
| 80% | 0 | |
| <80% | 0 | |

**Accuracy** = `1 - abs(player_loss_size - actual_loss_size) / actual_loss_size`

The "loss size" is the area (in kWh) between the player's drawn expected-production line and the actual production bars, for the days covered by that loss.

### Maximum per Loss Area

A perfectly identified loss scores: 10 (category) + 5 (subcategory) + 10 (size) = **25 points**. Plus time bonus/penalty on top.

### Penalties for False Losses

If a player marks an area as a loss where Bernard has not defined one: **-5 points** (to discourage guessing).

### Time Bonus / Penalty

Each scenario has a **normal completion time** parameter (configured by Bernard, e.g., 180 seconds). This is the expected time for a competent operator to finish.

| Situation | Points |
|-----------|--------|
| Faster than normal | **+1 point per second** faster |
| Slower than normal | **-1 point per 5 seconds** slower |

Examples (normal = 180s):
- Finished in 150s → 30 seconds faster → **+30 points**
- Finished in 200s → 20 seconds slower → **-4 points** (20/5 = 4)
- Finished in 300s → 120 seconds slower → **-24 points**

The time limit still applies (game ends when timer runs out), but the time bonus/penalty is based on completion time vs. normal completion time, not vs. the time limit.

### Final Score

```
score = sum(per_loss_points) + time_bonus_or_penalty
```

## Loss Categories & Subcategories

| # | Category | Subcategories |
|---|----------|---------------|
| 1 | **Breakdown** | Turbine failure · Generator failure · Electrical fault · Intake/canal blockage · Other mechanical |
| 2 | **Maintenance** | Planned inspection · Overhaul/repair · Cleaning · Regulatory inspection |
| 3 | **Environmental** | Flood · Ice/frost · Debris · Drought/low water · Sediment |
| 4 | **Operational** | Reservoir management · Testing/commissioning · Manual stop · Reduced operation |
| 5 | **Grid/Constraint** | Grid outage · Curtailment · Regulatory limit · Voltage/frequency issue |
| 6 | **Data Issue** | Meter gap · Calibration error · Communication loss · Sensor failure |

These map to the real Naia loss taxonomy (7 categories with 69 subtypes) but are simplified for a timed game.

## Timing

| Mode | Time Limit | Expected Losses | Notes |
|------|-----------|-----------------|-------|
| Standard | 5 min | 5-8 losses | Single mode. All players get the same time |

**Fixed at 5 minutes.** No mode switching — keeps it simple and fair for the leaderboard.

## Why This Works for Operators

- **Familiar context**: They read these exact patterns every day on their own plants
- **Competitive**: "I know more about hydro than you" — operators are proud of their expertise
- **Low barrier**: The intro video gives enough context even for non-experts
- **Three skill layers**: Finding the loss, classifying the cause, and estimating the size — rewards deep expertise
- **Aha moment**: Even if they get some wrong, they realize "a tool that does this automatically would save me time and money"
