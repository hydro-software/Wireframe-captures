# 02 - Architecture & Tech Stack

## Decision: Local-First Standalone App

The game is built as a **standalone application** that runs **locally** on the game PC at the conference. It replicates the Naia dashboard look & feel but has its own codebase, its own data, and its own deployment.

### Why Local-First

| Factor | Benefit |
|--------|---------|
| **Conference WiFi is unreliable** | Game works without internet. No loading delays, no outages. Players never wait. |
| **Developer focus** | The developer stays 100% on the product (issues 215-225, security). The game can be built by Claude Code or a separate person. |
| **Zero production risk** | Game bugs cannot affect real customers. No shared database, no shared deployment. |
| **Simple deployment** | Copy folder to game PC, run `npm start`. No cloud infrastructure to manage on-site. |
| **Instant response** | Local SQLite = sub-millisecond queries. No network latency on the chart or scoring. |

### Data Strategy: PostgreSQL vs. SQLite

The main Naia platform uses PostgreSQL + TimescaleDB. For the conference game, two options were considered:

| Factor | PostgreSQL (reuse Naia stack) | SQLite + Google Sheets |
|--------|-------------------------------|------------------------|
| **Offline support** | ❌ Requires running PG server | ✅ File-based, always works |
| **Setup complexity** | ❌ PG install + config on game PC | ✅ Zero-config, npm install |
| **Code reuse** | ⚠️ Some Drizzle schemas reusable | ❌ Different schema, fresh code |
| **Deployment** | ❌ PG service + Nuxt server | ✅ Single `node` process |
| **Backup** | ❌ pg_dump needed | ✅ Copy one file |
| **Cloud sync** | Built-in (if online) | Via Google Sheets API |
| **Data volume** | Overkill (<1000 rows) | Perfect fit |

**Decision: SQLite + Google Sheets.** The game has minimal data (participants + scores), needs to run fully offline, and must be deployable by copying a folder. PostgreSQL adds complexity without benefit here. Google Sheets provides cloud backup and real-time remote monitoring when WiFi is available.

```
Game PC (primary)                    Cloud (backup + remote access)
┌─────────────────┐                  ┌─────────────────────┐
│ SQLite (game.db) │ ──── sync ────→ │ Google Sheets        │
│ All game data    │                  │ Participants + scores│
│ Scenarios (JSON) │                  │ Real-time view       │
│ Videos (local)   │                  │ CRM-ready export     │
└─────────────────┘                  └─────────────────────┘
```

- **SQLite**: Primary data store. All game state, participants, scores
- **Google Sheets**: Background sync after each game session. Serves as cloud backup and allows remote monitoring (e.g., from a phone)
- **Sync is fire-and-forget**: If internet is down, data is safe in SQLite. Sync catches up when connection returns

### Multi-Console Support (2 Arcade Cabinets)

Both consoles run independently with their own SQLite database. Google Sheets acts as the **shared backend** for the combined leaderboard.

```
Console 1                          Console 2
┌─────────────────┐                ┌─────────────────┐
│ Nuxt server     │                │ Nuxt server     │
│ SQLite (local)  │                │ SQLite (local)  │
│ Game + classement│               │ Game + classement│
└────────┬────────┘                └────────┬────────┘
         │ write + verify                    │ write + verify
         ▼                                   ▼
    ┌─────────────────────────────────────────────┐
    │         Google Sheets (cloud)                │
    │  Shared leaderboard — both consoles          │
    │  read from here for the combined classement  │
    └─────────────────────────────────────────────┘
         │                                   │
         ▼                                   ▼
    TV (classement)                    TV (classement)
    reads from GSheets                 reads from GSheets
    via its console                    via its console
```

**Why no LAN?** The game PCs (laptops) may not have ethernet ports, and conference WiFi is the only network available. Google Sheets over WiFi is simpler than setting up a local network.

**Sync reliability**: Since conference WiFi can be unreliable, the sync includes **write verification** — after writing a row, the console reads it back to confirm. If verification fails, the row is re-queued. See chapter 05 for details.

**Fallback**: If WiFi is completely down, each console shows its own local leaderboard (SQLite only). When WiFi returns, both sync and the combined leaderboard rebuilds automatically.

### Classement: Second Browser Window on Same PC

No separate computer needed for the scoreboard. Each game PC runs two browser windows:
1. **Game window** (primary screen) — the gameplay interface
2. **Classement window** (secondary screen/TV) — `/classement` page in a separate Chrome window

Both served by the same local Nuxt server on `localhost:3000`.

### What We Reuse from Naia

- **Visual design**: Same color scheme, fonts, layout patterns, Nuxt UI components
- **Chart library**: uPlot for rendering production bars, rain, and flow indicators
- **Domain concepts**: Loss categories, indicator overlays, aggregated daily view
- **Gameplay screen**: 100% identical to the real Naia dashboard — the game doubles as a live product demo. Only a chronometer is added on top.

### What We Don't Reuse

- Backend (FastAPI, Celery, Alembic) — replaced by lightweight Node/Nuxt server
- Database (PostgreSQL + TimescaleDB) — replaced by SQLite
- Authentication (JWT, RBAC) — replaced by simple game session tokens
- Data ingestion pipeline — scenarios are pre-processed, loaded as static JSON

## Tech Stack

### Frontend
- **Nuxt 3** (Vue 3 + TypeScript) — same as Naia, consistent look
- **Nuxt UI** — same component library as Naia
- **uPlot** — same chart library as Naia, extended with drawing interaction
- **Pinia** — state management for game state

### Backend
- **Nuxt server routes** (`server/api/`) — no separate backend needed
- Nuxt 3's built-in server (Nitro) handles API routes, keeping everything in one project

### Database
- **SQLite** (via `better-sqlite3` or Drizzle ORM) — lightweight, zero-config, file-based
- Perfect for a conference game: <1000 records total, no concurrent write pressure
- Easy to backup (copy one file), easy to reset

### Cloud Sync
- **Google Sheets API** — append rows after each game session
- Uses a service account key (JSON file on the game PC)
- Sheets document shared with the team for real-time monitoring

### Video
- **Local MP4/WebM files** — stored in `scenarios/SC-XXX/intro.mp4`
- HTML5 `<video>` element, no streaming service needed

### Email
- **Infomaniak SMTP** — send results email via authenticated SMTP using the naia.energy domain
- Server: `mail.infomaniak.com`, port 587 (STARTTLS)
- Uses Nodemailer with SMTP transport (standard Node.js library)
- Credentials stored in `.env` on the game PC
- Sent from: `game@naia.energy`
- Queued locally if offline, sent when connection returns

> **Note**: Infomaniak (our hosting provider for naia.energy) does not offer a transactional email API like Gmail API or Resend. Instead, it provides standard SMTP access on `mail.infomaniak.com:587` with STARTTLS authentication. This is simpler than an API approach — just configure Nodemailer with SMTP credentials. No OAuth, no API keys, no Google Cloud Console setup needed.

## UI Language

**All screens are in French.** The game targets French-speaking hydropower operators at conferences in France, Belgium, and Switzerland. All UI labels, buttons, messages, error texts, and the scoreboard ("Classement") are in French.

## Project Structure

```
naia-conference-game/
├── app/                          # Nuxt 3 app directory
│   ├── pages/
│   │   ├── index.vue             # Welcome / attract screen ("Bienvenue")
│   │   ├── intro.vue             # Intro video player
│   │   ├── play.vue              # Main gameplay (drawing + diagnosis)
│   │   ├── results.vue           # Score breakdown + email input + CTA
│   │   ├── classement.vue        # Public leaderboard (2nd screen)
│   │   └── admin.vue             # Staff admin panel
│   ├── components/
│   │   ├── game/
│   │   │   ├── Chart.vue         # uPlot chart with drawing interaction
│   │   │   ├── DrawingLayer.vue  # Canvas overlay for line drawing
│   │   │   ├── IndicatorPanel.vue # Left panel: toggle additional indicators
│   │   │   ├── MaintenanceDot.vue # Clickable maintenance event popup
│   │   │   ├── CauseSelector.vue # Category + subcategory picker popup
│   │   │   ├── LossList.vue      # Bottom list of identified losses
│   │   │   ├── Timer.vue         # Countdown timer / chronometer
│   │   │   ├── ScoreBar.vue      # Top bar: timer + score + progress
│   │   │   ├── CountdownOverlay.vue # 3-2-1-GO
│   │   │   ├── ResultsBreakdown.vue # Post-game details per loss
│   │   │   ├── RevenueImpact.vue # EUR display
│   │   │   ├── OnScreenKeyboard.vue # Virtual keyboard for email input
│   │   │   └── CTAPanel.vue      # Sign up button + new game button
│   │   └── scoreboard/
│   │       ├── Leaderboard.vue   # Top 10 table ("Classement")
│   │       └── NowPlaying.vue    # Current game status
│   ├── composables/
│   │   ├── useGameState.ts       # Game flow state machine
│   │   ├── useGameChart.ts       # Chart data loading + indicator toggling
│   │   ├── useDrawing.ts         # Line drawing on chart + loss area calculation
│   │   ├── useScoring.ts         # Client-side score display
│   │   └── useTimer.ts           # Countdown logic
│   └── stores/
│       └── game.ts               # Pinia store
│
├── server/
│   ├── api/
│   │   ├── start.post.ts
│   │   ├── submit.post.ts
│   │   ├── results/[id].get.ts
│   │   ├── send-results.post.ts  # Send results email
│   │   ├── scoreboard.get.ts
│   │   └── admin/
│   │       ├── participants.get.ts
│   │       ├── export.get.ts
│   │       └── settings.post.ts
│   ├── db/
│   │   ├── schema.ts             # Drizzle ORM schema
│   │   ├── index.ts              # DB connection (SQLite)
│   │   └── seed.ts               # Initial data
│   ├── services/
│   │   ├── scoring.ts            # Scoring engine (server-side, authoritative)
│   │   ├── scenarios.ts          # Load scenario data from JSON files
│   │   ├── sheets-sync.ts        # Google Sheets background sync
│   │   └── email.ts              # Send results email via Infomaniak SMTP
│   └── utils/
│       └── loss-area.ts          # Calculate loss area from drawn line
│
├── scenarios/                    # Game scenario data
│   ├── SC-001/
│   │   ├── config.json
│   │   ├── production.json
│   │   ├── rain.json
│   │   ├── flow.json
│   │   ├── indicators.json       # Additional available indicators
│   │   ├── maintenance.json      # Maintenance event dots
│   │   ├── losses.json           # Answer key (server-only)
│   │   └── intro.mp4             # Plant intro video
│   ├── SC-002/
│   │   └── ...
│   └── ...
│
├── tools/
│   └── prepare-scenario.ts       # CLI: Bernard's CSV → JSON converter
│
├── public/
│   └── images/                   # Naia logo, category icons
│
├── nuxt.config.ts
├── package.json
├── .env.example
└── start.bat                     # Double-click to start on Windows
```

## Deployment: Game Day

### Primary: Run Locally

```bash
# On the game PC (Windows/Mac/Linux)
cd naia-conference-game
npm run build
node .output/server/index.mjs
# Game at http://localhost:3000
# Classement at http://localhost:3000/classement (open on 2nd screen)
```

Or with a convenience script (`start.bat` on Windows):
```batch
@echo off
cd /d "%~dp0"
node .output/server/index.mjs
```

### Scoreboard on Second Screen

1. Connect a TV/monitor as extended display
2. Open Chrome on the second screen: `http://localhost:3000/classement`
3. Press F11 for fullscreen

No network, no separate computer, no HDMI stick needed.

### Cloud Backup

Google Sheets syncs in the background. If WiFi is available, scores appear in the shared sheet within seconds. If not, they sync when connection returns.
