# 05 - Registration, Scoreboard & Email

## Registration (Post-Game)

Registration happens **after** the game, not before. The player plays first (no friction), then enters their email to see detailed results. This maximizes both play rate and lead capture quality — players who leave their email are genuinely interested.

### Data Model (SQLite — Local)

```sql
CREATE TABLE game_aliases (
    alias             TEXT NOT NULL,     -- user-chosen pseudonym
    conference_id     TEXT NOT NULL,
    first_seen_at     TEXT DEFAULT (datetime('now')),
    last_seen_at      TEXT DEFAULT (datetime('now')),
    participant_id    TEXT REFERENCES game_participants(id),  -- linked when email is entered
    PRIMARY KEY (alias, conference_id)
);

CREATE TABLE game_participants (
    id                TEXT PRIMARY KEY,  -- UUID
    first_name        TEXT,
    last_name         TEXT,
    email             TEXT,
    company           TEXT,
    role              TEXT,              -- plant_operator, owner, engineer, consultant, student, other
    email_consent     INTEGER DEFAULT 1, -- boolean
    marketing_consent INTEGER DEFAULT 0, -- boolean
    conference_id     TEXT NOT NULL,      -- e.g., "hydro-2025-grenoble"
    created_at        TEXT DEFAULT (datetime('now'))
);

CREATE TABLE game_sessions (
    id                TEXT PRIMARY KEY,  -- UUID
    alias             TEXT NOT NULL,     -- player's pseudonym (entered before the game)
    participant_id    TEXT REFERENCES game_participants(id),  -- NULL until email entered
    conference_id     TEXT NOT NULL,
    scenario_id       TEXT NOT NULL,
    started_at        TEXT NOT NULL,
    ended_at          TEXT,
    time_limit_sec    INTEGER DEFAULT 300,
    time_used_sec     INTEGER,
    status            TEXT DEFAULT 'in_progress',  -- in_progress, completed, abandoned
    practice_skipped  INTEGER DEFAULT 0, -- boolean: did the player skip the 30s tutorial?

    -- Scoring
    total_score       INTEGER DEFAULT 0,
    losses_found      INTEGER DEFAULT 0,
    losses_correct    INTEGER DEFAULT 0,
    false_losses      INTEGER DEFAULT 0,
    missed_losses     INTEGER DEFAULT 0,
    category_points   INTEGER DEFAULT 0,
    subcategory_points INTEGER DEFAULT 0,
    size_points       INTEGER DEFAULT 0,
    time_bonus        INTEGER DEFAULT 0,  -- positive = faster, negative = slower than normal
    revenue_found     REAL DEFAULT 0,
    revenue_missed    REAL DEFAULT 0,

    -- Sync tracking
    synced_to_sheets  INTEGER DEFAULT 0, -- boolean
    sync_status       TEXT DEFAULT 'pending',  -- pending, unverified, verified
    synced_at         TEXT,
    console_id        TEXT,              -- C1 or C2

    created_at        TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_sessions_alias ON game_sessions(alias, conference_id);

CREATE TABLE game_selections (
    id                  TEXT PRIMARY KEY,  -- UUID
    session_id          TEXT NOT NULL REFERENCES game_sessions(id),
    zone_id             INTEGER,           -- NULL if false loss (no matching answer key zone)
    start_date          TEXT NOT NULL,
    end_date            TEXT NOT NULL,
    drawn_expected_kwh  TEXT,              -- JSON array of daily expected values drawn by player
    loss_size_kwh       REAL,              -- calculated from drawn line
    selected_category   TEXT NOT NULL,
    selected_subcategory TEXT NOT NULL,
    is_correct_category INTEGER,           -- boolean, set after submission
    is_correct_subcategory INTEGER,        -- boolean, set after submission
    size_accuracy       REAL,              -- 0.0 to 1.0, set after submission
    category_points     INTEGER,
    subcategory_points  INTEGER,
    size_points         INTEGER,
    is_false_loss       INTEGER DEFAULT 0, -- boolean: player drew a loss where there isn't one
    selected_at         TEXT DEFAULT (datetime('now'))
);
```

### Flow

1. Player presses JOUER → alias entry screen
2. Player enters alias → `game_aliases` row upserted (update `last_seen_at` if exists)
3. Intro video → practice (skippable) → countdown → game starts
4. Session created with `alias` set, `participant_id = NULL`
5. After game → summary screen → player enters email + name
6. Participant record created (or matched by email), linked to session AND to the alias row
7. Email sent with detailed results
8. If player skips email → session saved with `participant_id = NULL`, score still on leaderboard under the alias

### Returning Players (Multiple Plays)

- **Same alias** → detected on alias entry, PASSER button highlighted in practice screen
- Each attempt is a **new session** (new `game_sessions` row)
- **Scenario assignment**: round-robin, excluding scenarios already played by this alias at this conference (query `SELECT DISTINCT scenario_id FROM game_sessions WHERE alias = ? AND conference_id = ?`). Once all scenarios are exhausted, any can be replayed.
- **Email pre-fill**: if the alias is linked to a participant, the email + name fields are pre-filled on the results screen (still editable + re-confirmed)
- **Leaderboard**: only the **best score** per alias is shown, with `(N parties)` annotation
- **No hard limit** on number of plays — queue dynamics naturally limit it at a conference; for the online post-conference version, consider a soft rate limit (e.g., 3 plays per hour per alias) to prevent bots

### GDPR

| Requirement | Implementation |
|-------------|---------------|
| Consent for results email | Explicit checkbox (pre-checked) |
| Consent for marketing | Separate checkbox, unchecked by default |
| Data minimization | Name, email, company — nothing more |
| Right to erasure | Admin can delete by email |
| Retention | Auto-delete 90 days after conference |
| Privacy notice | Link on email input form |
| Data location | Local SQLite on game PC + Google Sheets (EU) |

## Classement (Leaderboard)

### Architecture: Same PC, Second Window

The leaderboard runs as a second browser window on the game PC, connected to a TV/monitor via HDMI:

```
Game PC
├── Chrome Window 1 (primary screen): http://localhost:3000 → game
└── Chrome Window 2 (secondary screen): http://localhost:3000/classement → leaderboard
```

Both windows are served by the same local Nuxt server. No network, no SSE, no separate computer.

### Scoreboard Data

```
GET /api/scoreboard?conference_id=hydro-2025-grenoble

{
  "conferenceId": "hydro-2025-grenoble",
  "stats": {
    "totalPlayers": 47,       // unique aliases
    "totalGames": 62,         // total sessions (plays)
    "averageScore": 89,
    "highestScore": 142,
    "totalLossesFound": 312,
    "totalRevenueDiagnosed": 387420
  },
  "leaderboard": [
    {
      "rank": 1,
      "alias": "HydroPro42",
      "bestScore": 142,       // max across all games for this alias
      "gamesPlayed": 3,       // shown small on the Classement
      "lossesFound": 7,       // from the best game
      "lastPlayedAt": "2025-06-15T10:15:00Z"
    }
  ],
  "currentGame": {
    "alias": "Marie42",
    "timeRemaining": 222,
    "lossesFound": 2,
    "status": "playing"
  }
}
```

### Real-Time Updates

Since both windows run on the same machine:
- Scoreboard page polls `localhost:3000/api/scoreboard` every 3 seconds
- Sub-millisecond response time (local SQLite query)
- No SSE or WebSocket needed — polling is simpler and sufficient for localhost

### Scoreboard Display
- Full-screen page at `/classement?conference=hydro-2025-grenoble`
- Top 10 with animated entry when a new score enters the ranking
- Chrome fullscreen (F11) on the TV
- No interaction needed — auto-updates
- All labels in French: "Classement", "Joueurs aujourd'hui", "Moyenne", "Record", "En jeu"

## Google Sheets Sync (Shared Leaderboard + Backup)

### Purpose
- **Shared leaderboard**: When running 2 consoles, Google Sheets is the single source of truth for the combined Classement
- **Backup**: If a game PC fails, all data is in the cloud
- **Remote monitoring**: Check scores from a phone or other device
- **CRM export**: Sheets is already in a format marketers can use

### How It Works

After each completed game session, the server appends a row to a Google Sheet and **verifies** it was written correctly:

```
| Session ID | Console | Timestamp | Alias | First Name | Last Name | Email | Company | Score | Losses Found | Scenario | Marketing Consent |
|-----------|---------|-----------|-------|-----------|-----------|-------|---------|-------|-------------|----------|-------------------|
| abc-123   | C1      | 2025-06-15 10:15 | HydroPro42 | Pierre | Martin | pierre@edf.fr | EDF Hydro | 142 | 7 | SC-001 | Oui |
```

The Alias column is used to aggregate scores for the combined leaderboard (best score per alias, with games-played count). Multiple rows per alias are expected for players who play several times.

### Sync with Write Verification

Conference WiFi is unreliable. The sync must be **robust** — we cannot silently lose scores. The process:

```
1. WRITE: Append row to Google Sheet
         ↓
2. VERIFY: Read back the last rows, check if our session_id appears
         ↓
   ┌─── Found? ───┐
   │ YES           │ NO
   │               │
   ▼               ▼
3a. Mark as       3b. Mark as UNVERIFIED
    synced_to_       in SQLite, retry
    sheets = 1       in 30 seconds
```

```typescript
// server/services/sheets-sync.ts

async function syncAndVerify(session: GameSession, participant: Participant) {
  try {
    // Step 1: Write
    await sheets.spreadsheets.values.append({
      spreadsheetId: SHEETS_ID,
      range: 'Results!A:L',
      valueInputOption: 'USER_ENTERED',
      requestBody: {
        values: [[
          session.id,
          process.env.CONSOLE_ID || 'C1',  // identifies which console
          new Date().toISOString(),
          session.alias,                    // pseudonym chosen before play
          participant?.firstName ?? '',
          participant?.lastName ?? '',
          participant?.email ?? '',
          participant?.company ?? '',
          session.totalScore,
          session.lossesFound,
          session.scenarioId,
          participant?.marketingConsent ? 'Oui' : 'Non'
        ]]
      }
    })

    // Step 2: Verify — read back last 20 rows, check our session_id
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEETS_ID,
      range: 'Results!A:A',  // just the session_id column
    })
    const allIds = response.data.values?.flat() || []
    
    if (allIds.includes(session.id)) {
      // Step 3a: Verified — mark as synced
      markAsSynced(session.id, 'verified')
    } else {
      // Step 3b: Write succeeded but verification failed — retry later
      markAsSynced(session.id, 'unverified')
    }
  } catch (error) {
    // Network error — stay in queue, retry later
    console.warn('Sheets sync failed, will retry:', error.message)
  }
}

// Background retry: every 30 seconds, retry unsynced + unverified rows
setInterval(async () => {
  const pending = db.select().from(gameSessions)
    .where(
      and(
        eq(gameSessions.status, 'completed'),
        or(
          eq(gameSessions.syncedToSheets, 0),        // never synced
          eq(gameSessions.syncStatus, 'unverified')   // synced but not verified
        )
      )
    )
    .all()

  for (const session of pending) {
    await syncAndVerify(session, getParticipant(session.participantId))
  }
}, 30_000)
```

### Classement: Reading from Google Sheets

When running **2 consoles**, the Classement reads from Google Sheets (not local SQLite) to show the **combined** leaderboard:

```typescript
// server/api/scoreboard.get.ts

async function getLeaderboard(conferenceId: string) {
  // Try Google Sheets first (combined leaderboard)
  try {
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEETS_ID,
      range: 'Results!A:K',
    })
    // Parse rows, sort by score descending, return top 10
    return buildLeaderboardFromSheets(response.data.values)
  } catch (error) {
    // Fallback: local SQLite only (this console's scores)
    return buildLeaderboardFromSQLite(conferenceId)
  }
}
```

The Classement page polls every 5 seconds. When WiFi is available → combined leaderboard from both consoles. When WiFi is down → local leaderboard only (with a small indicator "⚠ Mode local").

### Sync Status in Admin Panel

The admin panel shows sync health per session:

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ `verified` | Written to Sheets AND confirmed | None |
| ⏳ `unverified` | Written but not yet confirmed | Auto-retry every 30s |
| ❌ `pending` | Not yet written (no internet) | Auto-retry every 30s |
| 🔄 `retrying` | Currently retrying | Wait |

Staff can also trigger a **Force Sync** from the admin panel to immediately retry all pending rows.

### Setup
1. Create a Google Sheet (shared with team)
2. Create a service account in Google Cloud Console
3. Share the Sheet with the service account email
4. Place the JSON key on **both** game PCs
5. Set in `.env` on each PC:
   - `GOOGLE_SHEETS_ID` — same sheet ID on both
   - `GOOGLE_CREDENTIALS_PATH` — path to service account JSON
   - `CONSOLE_ID` — `C1` on console 1, `C2` on console 2
   - `MULTI_CONSOLE=true` — enables Sheets-based leaderboard reading

## Results Email (via Infomaniak SMTP)

### Trigger
- Sent after the player enters their email and clicks "VOIR MES RÉSULTATS"
- Via Infomaniak SMTP (`mail.infomaniak.com:587` with STARTTLS)
- Uses Nodemailer — standard Node.js SMTP library
- If offline: queued in SQLite, sent when connection returns
- Sent from: `game@naia.energy`
- Reply-to: `contact@naia.energy`

### Email Configuration

```typescript
// server/services/email.ts
import nodemailer from 'nodemailer'

const transporter = nodemailer.createTransport({
  host: 'mail.infomaniak.com',
  port: 587,
  secure: false, // STARTTLS
  auth: {
    user: process.env.SMTP_USER,     // game@naia.energy
    pass: process.env.SMTP_PASSWORD,
  },
})
```

### Content

**Subject**: Vos résultats Naia — Score : {score} pts 🎯

**Body** (HTML template with plain text fallback — nicely formatted):

```
Bonjour {firstName},

Merci d'avoir relevé le Défi Détection de Pertes Naia !

VOS RÉSULTATS
━━━━━━━━━━━━
Score :      {totalScore} points
Classement : #{rank} sur {totalPlayers} joueurs
Centrale :   {plantName} ({capacityKw} kW)

PERTES IDENTIFIÉES
━━━━━━━━━━━━━━━━━━
{for each loss}
✅ Perte {n} ({dates}) : {category} > {subcategory}
   Catégorie : ✅ +10 | Sous-catégorie : ✅ +5 | Taille : 95% → 8 pts
   « {description} »

❌ Perte {n} ({dates}) : Vous avez dit {playerCategory} > {playerSubcategory}
   Correct : {correctCategory} > {correctSubcategory}
   Catégorie : ❌ -5 | Sous-catégorie : ❌ -2 | Taille : 82% → 1 pt
   « {description} »

⬜ Manquée ({dates}) : {correctCategory} > {correctSubcategory}
   « {description} »
{end for}

Bonus temps : {timeBonus} ({timeDiff} secondes par rapport au temps normal)

IMPACT FINANCIER
━━━━━━━━━━━━━━━
Pertes correctement identifiées : {revenueFound} €
Pertes totales de la centrale : {totalRevenueLoss} € / an

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Chaque centrale a des pertes comme celles-ci.
Naia les détecte automatiquement.

    [ 🚀 ESSAYER NAIA GRATUITEMENT ]
    → https://naia.energy/signup?utm_source=conference-game&utm_campaign={conferenceId}&email={email}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

L'équipe Naia
naia.energy
```

The CTA button in the email links to the **Naia signup page** (`naia.energy/signup`) with UTM tracking parameters and pre-filled email.

## Admin Panel

### Features
- **View participants**: table with name, email, company, score, scenario
- **Export CSV**: download all participants for CRM import
- **Game stats**: total games, average score, completion rate, most-found losses
- **Reset session**: clear a stuck game
- **Scenario management**: enable/disable scenarios
- **Sync status**: show which rows have been synced to Google Sheets
- **Force sync**: manually trigger Google Sheets sync

### Access
- URL: `/admin?key={admin_secret}`
- Single shared secret (not a full auth system)
- Mobile-friendly for staff use on phones (over local WiFi or internet)

### CSV Export Format

```csv
first_name,last_name,email,company,score,losses_found,rank,scenario,played_at,marketing_consent
Pierre,Martin,pierre@example.com,EDF Hydro,142,7,1,SC-001,2025-06-15T10:15:00Z,true
Sophie,Laurent,sophie@cnr.fr,CNR,128,6,2,SC-003,2025-06-15T11:30:00Z,false
```

Ready for import into HubSpot, Pipedrive, or similar CRM.
