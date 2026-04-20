# 06 - Technical Implementation

## Architecture

Single Nuxt 3 application running **locally** on the game PC — frontend and backend in one project. No cloud dependency during gameplay.

```
┌─────────────────────────────────────────────────────────┐
│              Game PC                                     │
│                                                          │
│  Chrome Window 1 (game)     Chrome Window 2 (scoreboard) │
│  localhost:3000             localhost:3000/scoreboard     │
│  Primary screen             TV / secondary screen        │
│         │                          │                     │
│         │ REST API                 │ Polling (3s)        │
│         ▼                          ▼                     │
│  ┌──────────────────────────────────────────────┐       │
│  │        Nuxt 3 (Nitro server)                  │       │
│  │                                               │       │
│  │  server/api/register.post.ts                  │       │
│  │  server/api/start.post.ts                     │       │
│  │  server/api/submit.post.ts                    │       │
│  │  server/api/results/[id].get.ts               │       │
│  │  server/api/scoreboard.get.ts                 │       │
│  │  server/api/admin/*                           │       │
│  │                                               │       │
│  │  SQLite (game.db)       Scenarios (JSON+MP4)  │       │
│  │  participants           scenarios/SC-001/     │       │
│  │  sessions                 config.json         │       │
│  │  selections               production.json     │       │
│  │                           losses.json         │       │
│  │                           maintenance.json    │       │
│  │                           intro.mp4           │       │
│  └──────────────────────────────────────────────┘       │
│         │                                                │
│         │ Background sync (when internet available)      │
│         ▼                                                │
│  Google Sheets API → cloud backup + remote monitoring    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Framework | Nuxt 3 (Vue 3 + TypeScript) | Same as Naia — consistent look & feel |
| UI Library | Nuxt UI | Same as Naia |
| Charts | uPlot | Same as Naia — fast time-series rendering |
| Drawing | HTML5 Canvas overlay | Custom drawing layer on top of uPlot chart |
| State | Pinia | Same as Naia |
| Server | Nitro (built into Nuxt) | No separate backend needed |
| Database | SQLite via better-sqlite3 | Zero-config, file-based, local |
| ORM | Drizzle ORM | Lightweight, TypeScript-native |
| Cloud sync | Google Sheets API v4 | Background backup, remote monitoring |
| Email | Infomaniak SMTP via Nodemailer | Send results when internet available |
| Video | HTML5 `<video>` | Local MP4/WebM files, no streaming |

## Key Data Structures

### Scenario Data (JSON files)

**`config.json`** — sent to browser
```typescript
interface ScenarioConfig {
  id: string                    // "SC-001"
  plantName: string             // "Centrale de Moulins"
  capacityKw: number            // 450
  river: string                 // "La Dordogne"
  country: string               // "France"
  periodStart: string           // "2025-01-01"
  periodEnd: string             // "2025-02-28"
  difficulty: 'easy' | 'standard' | 'hard'
  timeLimitSec: number          // 300
  normalCompletionTimeSec: number // 180 — expected time for a competent operator
  numLosses: number             // 6
  introVideo: string            // "intro.mp4"
}
```

**`production.json`** — sent to browser
```typescript
interface ProductionDay {
  date: string                  // "2025-01-01"
  energyKwh: number             // 8540
}
```

**`rain.json`** — sent to browser
```typescript
interface RainDay {
  date: string
  rainMm: number
}
```

**`flow.json`** — sent to browser
```typescript
interface FlowDay {
  date: string
  flowM3s: number
}
```

**`maintenance.json`** — sent to browser (contextual clues)
```typescript
interface MaintenanceEvent {
  date: string                  // "2025-01-05"
  label: string                 // "Restart turbine after trip"
}
```

**`indicators.json`** — additional indicators available in the panel
```typescript
interface AdditionalIndicator {
  id: string                    // "flow-station-b"
  label: string                 // "Station B — upstream"
  type: 'flow' | 'rain' | 'comparator'
  unit: string                  // "m3/s" or "kWh" or "mm"
  data: Array<{ date: string; value: number }>
}
```

**`losses.json`** — answer key, NEVER sent to browser during gameplay
```typescript
interface LossZone {
  zoneId: number                // 1, 2, 3...
  startDate: string
  endDate: string
  category: LossCategory
  subcategory: string           // e.g., "turbine_failure"
  description: string           // Bernard's explanation
  expectedKwhPerDay: number     // What production should have been
  actualKwh: number             // Sum of actual production in the period
  expectedKwh: number           // Sum of expected production in the period
  lossSizeKwh: number           // expectedKwh - actualKwh
  revenueLossEur: number
}

type LossCategory = 'breakdown' | 'maintenance' | 'environmental'
  | 'operational' | 'grid_constraint' | 'data_issue'
```

### Game State (Pinia Store)

```typescript
interface GameState {
  // Session
  participantId: string | null
  sessionId: string | null
  scenario: ScenarioConfig | null

  // Game flow (register happens AFTER gameplay, detailed results only by email)
  status: 'idle' | 'video' | 'countdown' | 'playing' | 'submitting' | 'summary' | 'email_input' | 'classement'

  // Timer
  timeRemaining: number         // seconds
  timeLimitSec: number

  // Chart data
  production: ProductionDay[]
  rain: RainDay[]
  flow: FlowDay[]
  maintenanceEvents: MaintenanceEvent[]
  additionalIndicators: AdditionalIndicator[]
  activeIndicators: string[]    // IDs of toggled-on indicators

  // Drawing state
  drawingMode: boolean
  currentDrawing: DrawnLoss | null

  // Player's identified losses
  drawnLosses: DrawnLoss[]

  // Results (populated after submit)
  results: GameResults | null
}

interface DrawnLoss {
  id: string                    // client-generated UUID
  startDate: string
  endDate: string
  expectedKwhPerDay: number[]   // one value per day in the range (drawn line heights)
  lossSizeKwh: number           // calculated: sum(expected - actual) for each day
  category: LossCategory | null
  subcategory: string | null
  confirmed: boolean            // has the player confirmed category + subcategory?
}

interface GameResults {
  totalScore: number
  rank: number
  totalPlayers: number
  categoryPoints: number
  subcategoryPoints: number
  sizePoints: number
  timeBonus: number             // positive = faster, negative = slower
  revenueFound: number
  revenueMissed: number
  totalRevenueLoss: number
  breakdown: Array<{
    type: 'correct' | 'wrong_category' | 'wrong_subcategory' | 'missed' | 'false_loss'
    playerLoss: DrawnLoss | null
    answerKeyLoss: LossZone | null
    categoryPoints: number
    subcategoryPoints: number
    sizePoints: number
    sizeAccuracy: number
    totalPoints: number
  }>
}
```

## API Endpoints

### `POST /api/register`

```typescript
// Request
{ firstName: string, lastName: string, email: string, company?: string,
  role?: string, emailConsent: boolean, marketingConsent: boolean,
  conferenceId: string }

// Response
{ participantId: string }
```

### `POST /api/start`

```typescript
// Request
{ participantId: string }

// Response — includes scenario data but NOT the answer key
{
  sessionId: string,
  scenario: ScenarioConfig,
  production: ProductionDay[],
  rain: RainDay[],
  flow: FlowDay[],
  maintenanceEvents: MaintenanceEvent[],
  additionalIndicators: AdditionalIndicator[]
  // NO losses — player must find them!
}
```

### `POST /api/submit`

```typescript
// Request
{
  sessionId: string,
  drawnLosses: Array<{
    startDate: string,
    endDate: string,
    expectedKwhPerDay: number[],
    lossSizeKwh: number,
    category: LossCategory,
    subcategory: string
  }>,
  timeUsedSec: number
}

// Response — full results including correct answers
{ results: GameResults }
```

### `GET /api/results/:id`
Returns same `GameResults` for a completed session.

### `GET /api/scoreboard?conferenceId=xxx`
Returns leaderboard + stats. Polled every 3s by scoreboard window.

## Scoring Engine (Server-Side)

```typescript
// server/services/scoring.ts

interface ScoringInput {
  drawnLosses: DrawnLoss[]
  answerKey: LossZone[]
  production: ProductionDay[]
  timeUsedSec: number
  normalCompletionTimeSec: number
}

function calculateScore(input: ScoringInput): GameResults {
  const { drawnLosses, answerKey, production, timeUsedSec, normalCompletionTimeSec } = input
  let totalScore = 0
  let categoryPoints = 0
  let subcategoryPoints = 0
  let sizePoints = 0
  const breakdown = []

  // Match drawn losses to answer key losses
  const matched = matchLossesToAnswerKey(drawnLosses, answerKey)

  for (const match of matched) {
    if (match.type === 'matched') {
      // Player found a real loss
      const { playerLoss, answerLoss } = match

      // Level 1: Category (+10 / -5)
      const catCorrect = playerLoss.category === answerLoss.category
      const catPts = catCorrect ? 10 : -5
      categoryPoints += catPts

      // Level 2: Subcategory (+5 / -2)
      const subCorrect = playerLoss.subcategory === answerLoss.subcategory
      const subPts = subCorrect ? 5 : -2
      subcategoryPoints += subPts

      // Level 3: Size accuracy (0-10)
      const accuracy = calculateSizeAccuracy(playerLoss.lossSizeKwh, answerLoss.lossSizeKwh)
      const sizePts = Math.round(Math.max(0, (accuracy - 0.80) / 0.20 * 10))
      sizePoints += sizePts

      const total = catPts + subPts + sizePts
      totalScore += total

      breakdown.push({
        type: catCorrect ? 'correct' : 'wrong_category',
        playerLoss, answerKeyLoss: answerLoss,
        categoryPoints: catPts, subcategoryPoints: subPts,
        sizePoints: sizePts, sizeAccuracy: accuracy,
        totalPoints: total
      })
    } else if (match.type === 'false_loss') {
      // Player drew a loss where there isn't one
      totalScore -= 5
      breakdown.push({
        type: 'false_loss',
        playerLoss: match.playerLoss, answerKeyLoss: null,
        categoryPoints: 0, subcategoryPoints: 0,
        sizePoints: 0, sizeAccuracy: 0,
        totalPoints: -5
      })
    } else if (match.type === 'missed') {
      // Answer key loss that player didn't find
      breakdown.push({
        type: 'missed',
        playerLoss: null, answerKeyLoss: match.answerLoss,
        categoryPoints: 0, subcategoryPoints: 0,
        sizePoints: 0, sizeAccuracy: 0,
        totalPoints: 0
      })
    }
  }

  // Time bonus/penalty (vs. normal completion time)
  const timeDiff = normalCompletionTimeSec - timeUsedSec  // positive = faster
  let timeBonus
  if (timeDiff >= 0) {
    timeBonus = timeDiff  // +1 point per second faster
  } else {
    timeBonus = Math.ceil(timeDiff / 5)  // -1 point per 5 seconds slower (negative)
  }
  totalScore += timeBonus

  // Revenue
  const correctLosses = breakdown.filter(b => b.type === 'correct' || b.type === 'wrong_category')
  const revenueFound = correctLosses.reduce((sum, b) => sum + (b.answerKeyLoss?.revenueLossEur ?? 0), 0)
  const totalRevenueLoss = answerKey.reduce((sum, l) => sum + l.revenueLossEur, 0)

  return {
    totalScore, rank: 0, totalPlayers: 0,
    categoryPoints, subcategoryPoints, sizePoints, timeBonus,
    revenueFound, revenueMissed: totalRevenueLoss - revenueFound,
    totalRevenueLoss, breakdown
  }
}
```

### Loss Matching Algorithm

A player's drawn loss "matches" an answer key loss if their date ranges **overlap significantly** (>50% overlap with the answer key's range):

```typescript
function matchLossesToAnswerKey(drawn: DrawnLoss[], answerKey: LossZone[]) {
  const results = []
  const matchedAnswerIds = new Set<number>()

  for (const playerLoss of drawn) {
    // Find the best-matching answer key loss
    let bestMatch = null
    let bestOverlap = 0

    for (const answerLoss of answerKey) {
      if (matchedAnswerIds.has(answerLoss.zoneId)) continue
      const overlap = calculateDateOverlap(playerLoss, answerLoss)
      const overlapRatio = overlap / getDateRangeDays(answerLoss)
      if (overlapRatio > 0.5 && overlapRatio > bestOverlap) {
        bestMatch = answerLoss
        bestOverlap = overlapRatio
      }
    }

    if (bestMatch) {
      matchedAnswerIds.add(bestMatch.zoneId)
      results.push({ type: 'matched', playerLoss, answerLoss: bestMatch })
    } else {
      results.push({ type: 'false_loss', playerLoss })
    }
  }

  // Add missed losses
  for (const answerLoss of answerKey) {
    if (!matchedAnswerIds.has(answerLoss.zoneId)) {
      results.push({ type: 'missed', answerLoss })
    }
  }

  return results
}
```

### Size Accuracy Calculation

```typescript
function calculateSizeAccuracy(playerSizeKwh: number, actualSizeKwh: number): number {
  if (actualSizeKwh === 0) return playerSizeKwh === 0 ? 1.0 : 0.0
  return Math.max(0, 1 - Math.abs(playerSizeKwh - actualSizeKwh) / actualSizeKwh)
}

// Points: linear from 80% (0 pts) to 100% (10 pts)
// Formula: max(0, (accuracy - 0.80) / 0.20 * 10), rounded
```

## Chart Implementation

### uPlot Configuration

The game chart is a customized uPlot instance showing:

1. **Production bars** (primary series) — daily kWh, same visual as Naia aggregated
2. **Rain bars** (inverted, top of chart) — same as Naia slots 1-2
3. **Flow line** (overlaid) — same as Naia slots 3-5
4. **Maintenance dots** — rendered as circle markers on the production series
5. **Additional indicators** — toggled on/off, rendered as additional lines or bars
6. **Drawing overlay** — HTML5 Canvas layer on top of uPlot for the player's drawn lines

### Drawing Layer

A transparent canvas element positioned exactly over the uPlot chart area. Handles:

```typescript
// Drawing interaction
class DrawingLayer {
  private canvas: HTMLCanvasElement
  private chart: uPlot
  private currentLoss: { startIdx: number, points: number[] } | null

  onMouseDown(e: MouseEvent) {
    // Convert pixel X to date index
    const dateIdx = this.pixelToDateIndex(e.offsetX)
    this.currentLoss = { startIdx: dateIdx, points: [] }
  }

  onMouseMove(e: MouseEvent) {
    if (!this.currentLoss) return
    // Convert pixel Y to kWh value (this is the expected production level)
    const kwhValue = this.pixelToKwh(e.offsetY)
    // Convert pixel X to date index
    const dateIdx = this.pixelToDateIndex(e.offsetX)
    // Store the expected value for this day
    this.currentLoss.points[dateIdx - this.currentLoss.startIdx] = kwhValue
    this.redraw()
  }

  onMouseUp(e: MouseEvent) {
    if (!this.currentLoss) return
    const endIdx = this.pixelToDateIndex(e.offsetX)
    // Calculate loss area (gap between drawn line and actual production)
    const lossSizeKwh = this.calculateLossArea(this.currentLoss)
    // Emit event to open cause selector
    this.emit('lossDrawn', {
      startDate: this.dates[this.currentLoss.startIdx],
      endDate: this.dates[endIdx],
      expectedKwhPerDay: this.currentLoss.points,
      lossSizeKwh
    })
  }

  private calculateLossArea(drawing: Drawing): number {
    let total = 0
    for (let i = 0; i < drawing.points.length; i++) {
      const expected = drawing.points[i]
      const actual = this.production[drawing.startIdx + i].energyKwh
      total += Math.max(0, expected - actual)
    }
    return total
  }

  redraw() {
    // Clear canvas
    // Draw all confirmed loss areas (shaded regions)
    // Draw current in-progress loss area
    // Draw maintenance dots
  }
}
```

### Simplified Drawing Mode

For players who want to be faster:
1. Click on a start date
2. Click on an end date
3. System draws a flat line at the average of surrounding normal days
4. Player can drag the line up/down to adjust
5. Loss area updates in real-time

### Maintenance Dot Rendering

```typescript
// Rendered as circles on the production bars at specific dates
hooks: {
  draw: [
    (u: uPlot) => {
      const ctx = u.ctx
      for (const event of maintenanceEvents) {
        const x = u.valToPos(dateToTimestamp(event.date), 'x', true)
        const y = u.valToPos(getProductionForDate(event.date), 'y', true)

        // Draw dot
        ctx.beginPath()
        ctx.arc(x, y - 8, 6, 0, Math.PI * 2)
        ctx.fillStyle = '#1A5F7A'
        ctx.fill()
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 2
        ctx.stroke()
      }
    }
  ]
}

// Click detection: check distance from click to each dot
canvas.addEventListener('click', (e) => {
  for (const event of maintenanceEvents) {
    const dotX = u.valToPos(dateToTimestamp(event.date), 'x', true)
    const dotY = u.valToPos(getProductionForDate(event.date), 'y', true) - 8
    const dist = Math.sqrt((e.offsetX - dotX) ** 2 + (e.offsetY - dotY) ** 2)
    if (dist < 12) {
      showMaintenancePopup(event, dotX, dotY)
      return
    }
  }
})
```

## Google Sheets Sync (with Write Verification)

See chapter 05 for the detailed sync + verification logic. Key points:
- After writing a row, the console **reads it back** to verify it was persisted
- Unverified and pending rows are retried every 30 seconds
- When `MULTI_CONSOLE=true`, the Classement reads from Sheets (combined leaderboard from all consoles)
- When offline, falls back to local SQLite leaderboard with a "⚠ Mode local" indicator

```typescript
// server/services/sheets-sync.ts
import { google } from 'googleapis'

const auth = new google.auth.GoogleAuth({
  keyFile: process.env.GOOGLE_CREDENTIALS_PATH,
  scopes: ['https://www.googleapis.com/auth/spreadsheets']
})
const sheets = google.sheets({ version: 'v4', auth })

// Write + verify — see chapter 05 for full implementation
async function syncAndVerify(session: GameSession, participant: Participant) {
  // 1. Append row (includes session.id and CONSOLE_ID for deduplication)
  // 2. Read back to verify session.id appears in the sheet
  // 3. Mark as 'verified', 'unverified', or keep 'pending'
}

// Background retry every 30 seconds
setInterval(() => retryPendingAndUnverified(), 30_000)
```

## Deployment (Local)

### Build & Run

```bash
# One-time setup
npm install
npm run build

# Run on game day
node .output/server/index.mjs
# → http://localhost:3000 (game)
# → http://localhost:3000/scoreboard (leaderboard)
```

### Windows Convenience Script (`start.bat`)

```batch
@echo off
echo Starting Naia Conference Game...
cd /d "%~dp0"
start "" "http://localhost:3000"
timeout /t 2 >nul
start "" "http://localhost:3000/scoreboard"
node .output/server/index.mjs
```

### Environment Variables

```env
# .env
CONFERENCE_ID=hydro-2025-grenoble
ADMIN_SECRET=change-me

# Google Sheets sync (required for multi-console, optional for single)
GOOGLE_SHEETS_ID=1abc...xyz
GOOGLE_CREDENTIALS_PATH=./credentials/service-account.json
CONSOLE_ID=C1                    # C1 or C2 — identifies this console
MULTI_CONSOLE=false              # true = leaderboard reads from Sheets (combined)

# Email via Infomaniak SMTP (game works without)
SMTP_HOST=mail.infomaniak.com
SMTP_PORT=587
SMTP_USER=game@naia.energy
SMTP_PASSWORD=xxxx
SMTP_FROM=game@naia.energy
```

