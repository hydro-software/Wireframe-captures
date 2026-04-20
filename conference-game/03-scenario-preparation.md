# 03 - Scenario Preparation

This document describes how Bernard (or any domain expert) creates game scenarios.

## Overview

A scenario = one plant, a couple of months of data, with loss areas defined (size, category, subcategory) and maintenance events marked. Bernard prepares this using real (anonymized) or realistic data.

## What Bernard Provides

### 1. Plant Info
- Plant name (fictional, e.g., "Centrale de Moulins")
- Capacity in kW (e.g., 450)
- River name (e.g., "La Dordogne")
- Country

### 2. Intro Video
A short video (30-90 seconds) showing the plant: the river, the intake, the powerhouse, the turbine hall. This gives players context before they play.

- Format: MP4 or WebM
- Resolution: 1920x1080 recommended
- Stored locally in the scenario folder
- Can be filmed on a phone — doesn't need to be professional

### 3. Production Data (CSV)
Daily or sub-daily power/energy data for the scenario period (~60 days).

**Expected CSV format:**
```csv
datetime,value
2025-01-01 00:00,120.5
2025-01-01 00:15,118.3
2025-01-01 00:30,121.0
...
```

Or daily aggregated:
```csv
date,energy_kwh
2025-01-01,8540
2025-01-02,8230
2025-01-03,7980
...
```

The preparation tool will accept either format and aggregate to daily if needed.

### 4. Rain Data (CSV)
Daily rainfall from a nearby weather station.

```csv
date,rain_mm
2025-01-01,0.0
2025-01-02,12.3
2025-01-03,24.1
...
```

### 5. River Flow Data (CSV)
Daily average river flow from a hydrometric station.

```csv
date,flow_m3s
2025-01-01,8.2
2025-01-02,9.1
2025-01-03,14.5
...
```

### 6. Loss Areas (CSV) — Answer Key
This is the answer key. Bernard marks which days/periods are losses, what caused them, and the loss size.

```csv
start_date,end_date,category,subcategory,expected_kwh_per_day,description
2025-01-04,2025-01-04,breakdown,turbine_failure,8500,"Turbine trip — zero production despite normal flow"
2025-01-07,2025-01-08,environmental,flood,8500,"Flood event — intake submerged, safety shutdown"
2025-01-12,2025-01-12,maintenance,planned_inspection,8200,"Planned annual inspection"
2025-01-15,2025-01-16,grid_constraint,grid_outage,8300,"Grid outage in the area"
2025-01-19,2025-01-19,operational,reservoir_management,8400,"Reservoir flush ordered by authority"
2025-01-25,2025-01-25,data_issue,meter_gap,8100,"Flow sensor communication loss — data gap"
```

**Fields**:
- `start_date`, `end_date`: The period of the loss
- `category`: One of: `breakdown`, `maintenance`, `environmental`, `operational`, `grid_constraint`, `data_issue`
- `subcategory`: The specific subcategory (see table below)
- `expected_kwh_per_day`: What production *should* have been (Bernard's expert estimate). The tool uses this to calculate loss size
- `description`: Explanation shown to the player in results

**Valid subcategories:**

| Category | Subcategories |
|----------|---------------|
| breakdown | `turbine_failure`, `generator_failure`, `electrical_fault`, `intake_blockage`, `other_mechanical` |
| maintenance | `planned_inspection`, `overhaul_repair`, `cleaning`, `regulatory_inspection` |
| environmental | `flood`, `ice_frost`, `debris`, `drought_low_water`, `sediment` |
| operational | `reservoir_management`, `testing_commissioning`, `manual_stop`, `reduced_operation` |
| grid_constraint | `grid_outage`, `curtailment`, `regulatory_limit`, `voltage_frequency` |
| data_issue | `meter_gap`, `calibration_error`, `communication_loss`, `sensor_failure` |

### 7. Maintenance Events (CSV)
Clickable informational dots on the production timeline. These give players contextual clues.

```csv
date,label
2025-01-05,Restart turbine after trip
2025-01-09,Clear debris from intake
2025-01-12,Start annual inspection
2025-01-13,End inspection — restart
2025-01-20,Normal operation resumed
2025-01-26,Replace flow sensor
```

**Guidelines for maintenance events**:
- Place them near loss areas to give clues (e.g., "restart turbine" after a breakdown)
- Include some events that are *not* near losses (normal operations) to avoid making it too easy
- Use short, operator-style language
- Aim for 8-15 events per scenario

## Preparation Tool

A CLI tool converts Bernard's CSVs into game-ready JSON:

```bash
npx tsx tools/prepare-scenario.ts \
  --id SC-001 \
  --name "Centrale de Moulins" \
  --capacity 450 \
  --river "La Dordogne" \
  --country France \
  --production data/SC-001_production.csv \
  --rain data/SC-001_rain.csv \
  --flow data/SC-001_flow.csv \
  --losses data/SC-001_losses.csv \
  --maintenance data/SC-001_maintenance.csv \
  --video data/SC-001_intro.mp4 \
  --electricity-price 0.14
```

### What the Tool Does

1. **Reads and validates** all CSV files
2. **Aggregates** sub-daily production to daily energy (kWh) if needed
3. **Aligns** all series to the same date range
4. **Calculates loss size** per loss area: `sum((expected_kwh_per_day - actual_kwh) for each day in range)`
5. **Calculates revenue loss**: `loss_size_kwh × electricity_price`
6. **Assigns loss zone numbers** (Loss 1, Loss 2, etc.) in chronological order
7. **Copies the intro video** to the scenario folder
8. **Outputs** scenario JSON files to `scenarios/SC-XXX/`

### Output: Scenario JSON Files

**`scenarios/SC-001/config.json`**
```json
{
  "id": "SC-001",
  "plantName": "Centrale de Moulins",
  "capacityKw": 450,
  "river": "La Dordogne",
  "country": "France",
  "periodStart": "2025-01-01",
  "periodEnd": "2025-02-28",
  "difficulty": "standard",
  "timeLimitSec": 300,
  "normalCompletionTimeSec": 180,
  "numLosses": 6,
  "totalRevenueLossEur": 11630,
  "introVideo": "intro.mp4"
}
```

**`scenarios/SC-001/production.json`**
```json
[
  { "date": "2025-01-01", "energyKwh": 8540 },
  { "date": "2025-01-02", "energyKwh": 8230 }
]
```

**`scenarios/SC-001/rain.json`**
```json
[
  { "date": "2025-01-01", "rainMm": 0.0 },
  { "date": "2025-01-02", "rainMm": 12.3 }
]
```

**`scenarios/SC-001/flow.json`**
```json
[
  { "date": "2025-01-01", "flowM3s": 8.2 },
  { "date": "2025-01-02", "flowM3s": 9.1 }
]
```

**`scenarios/SC-001/maintenance.json`**
```json
[
  { "date": "2025-01-05", "label": "Restart turbine after trip" },
  { "date": "2025-01-09", "label": "Clear debris from intake" },
  { "date": "2025-01-12", "label": "Start annual inspection" },
  { "date": "2025-01-13", "label": "End inspection — restart" }
]
```

**`scenarios/SC-001/losses.json`** (answer key — NOT sent to the browser during gameplay)
```json
[
  {
    "zoneId": 1,
    "startDate": "2025-01-04",
    "endDate": "2025-01-04",
    "category": "breakdown",
    "subcategory": "turbine_failure",
    "description": "Turbine trip — zero production despite normal flow of 12 m3/s",
    "expectedKwhPerDay": 8500,
    "actualKwh": 0,
    "expectedKwh": 8500,
    "lossSizeKwh": 8500,
    "revenueLossEur": 1190
  }
]
```

## What Gets Sent to the Browser

During gameplay, the frontend receives:
- `config.json` — plant info and game settings
- `production.json` — full production series
- `rain.json` — full rain series
- `flow.json` — full flow series
- `indicators.json` — additional indicators (if any)
- `maintenance.json` — maintenance event dots (dates + labels)

**NOT sent**: `losses.json` — the answer key stays on the server until submission.

The player must identify loss areas themselves by drawing on the chart. There are no pre-marked loss zones visible during gameplay.

## Bernard's Workflow

```
1. Pick a real plant's data (anonymize names)
         ↓
2. Film a short intro video of the plant (phone is fine)
         ↓
3. Export production CSV from Naia or from the operator's system
         ↓
4. Export rain CSV (from Meteo-France or Naia)
         ↓
5. Export flow CSV (from Hubeau or Naia)
         ↓
6. Open the production data in a spreadsheet
         ↓
7. Identify loss periods visually (days where production doesn't match flow/rain)
         ↓
8. For each loss: determine category, subcategory, and expected production
         ↓
9. Create the losses CSV: start_date, end_date, category, subcategory, expected_kwh_per_day, description
         ↓
10. Create maintenance events CSV: date, label (from operator logbook)
         ↓
11. Run the preparation tool
         ↓
12. Review: does the chart look right? Are the loss areas clear enough?
         ↓
13. Playtest: can someone find and diagnose these losses from the chart?
         ↓
14. Adjust if needed (make clues more obvious, add/remove losses or maintenance events)
```

## Guidelines for Bernard

### Making Good Scenarios

- **Aim for 5-8 loss areas per scenario** (Standard mode)
- **Mix easy and hard losses**: include 2-3 obvious ones (zero production + normal flow = breakdown) and 2-3 subtle ones (partial production reduction during high flow = constraint)
- **Use realistic patterns**: operators should recognize these as plausible situations
- **Vary the causes**: don't make 5 out of 8 losses the same category
- **Include at least one of each**: if possible, have each of the 6 categories represented
- **The context must tell the story**: if you mark a loss as "environmental", make sure the rain/flow data on those days actually shows a weather event
- **Maintenance events as clues**: place them strategically. A "restart turbine" dot the day after a zero-production period is a strong clue for "breakdown"
- **`expected_kwh_per_day` must be realistic**: use the average production of surrounding normal days as a reference

### Common Pitfalls

- **Loss area not visible**: if the production bar on a loss day is still high relative to expected, the loss won't be obvious enough to draw. Make sure there's a clear visual gap.
- **Ambiguous causes**: some losses could reasonably be 2 categories. That's fine for the real world, but for a game, make sure there's a "best" answer. Use maintenance dots and the description to make it clear.
- **Too many losses**: >8 losses in a 5-minute game = players can't finish. Keep it manageable.
- **All easy or all hard**: mix it up. Start with obvious losses to build confidence, then challenge them.
- **No maintenance events near losses**: maintenance dots are the main contextual clue. Without them, some losses become impossible to classify.

## Number of Scenarios Needed

| Conference Duration | Minimum Scenarios | Ideal |
|--------------------|-------------------|-------|
| Half day | 3 | 5 |
| Full day | 5 | 8 |
| Multi-day | 8 | 10+ |

Players who replay get a different scenario. With 5 scenarios and random assignment, the chance of two adjacent players getting the same one is 20% — acceptable.

## Scenario Validation Checklist

Before a scenario is considered ready:

- [ ] All CSVs load without errors in the preparation tool
- [ ] Intro video plays correctly (30-90s, reasonable quality)
- [ ] Chart looks correct: production, rain, and flow align visually
- [ ] Each loss area is visually identifiable on the chart (production clearly below expected)
- [ ] Context indicators (rain, flow) support the correct diagnosis
- [ ] Maintenance events give useful clues without being too obvious
- [ ] Subcategories are unambiguous given the available data
- [ ] `expected_kwh_per_day` values are realistic (comparable to surrounding normal days)
- [ ] Descriptions are clear and educational
- [ ] Revenue loss figures are plausible
- [ ] At least 2 team members can playtest and score >50%
- [ ] No accidental data that reveals the real plant identity
