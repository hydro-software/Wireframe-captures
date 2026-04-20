# Naia Points — v1 (HTML prototype)

Interactive HTML wireframes for the **Naia Points** community loyalty app — the member loyalty & community platform built on top of Naia Business Insight (naia.energy).

## Live prototype

**→ https://hydro-software.github.io/Designs-wireframes/naia-points-v1/**

French (FR) only for now. German and English will follow once the content is validated.

## What to click

### Member portal (`/naia-points-v1/`)

- **Tableau de bord** (`index.html`) — KPIs, points chart (Chart.js with plausible 12-week data), activity feed, quick-action tiles, upcoming visit card.
- **Gagner des points** (`earn.html`) — 4 tabs (Plateforme · Communauté · Apprentissage · Parrainage). Includes the **parrainage** tab with referral code, share buttons, filleul history and invite form.
- **Récompenses** (`rewards.html`) — catalogue grouped by category (Accès · Produit · Reconnaissance · Marchandise), plus redemption history tab. Try the **Échanger** buttons for the confirm → alert flow.
- **Classement** (`leaderboard.html`) — podium top 3, full ranking with highlighted self-row (#14), side panel with progression stats.
- **Profil** (`profile.html`) — 5 tabs: Vue d'ensemble (tier progression), Mes centrales, Badges (5 earned + 2 locked), Historique points, Préférences (notifications + language).
- **Communauté** (`community.html`) — Forum (6 threads with categories + top contributors side panel), Annuaire membres (8 operator cards), Base de connaissances (6 articles).
- **Visites de centrales** (`visits.html`) — Hero CTA + **Proposer une visite modal**, grid of 6 upcoming visits with date stamps, "Mes visites" tab.
- **Intelligence de marché** (`market.html`) — Featured premium newsletter, regular + premium editions archive, regulatory alerts with urgency levels.
- **Opportunités** (`opportunities.html`) — Simulations BTM (4 runs with ROI), peer performance (anonymised), co-investment (locked — Ambassador tier).

### Admin portal (`/naia-points-v1/admin/`)

Distinguished by an **orange banner** at the top.

- **Tableau de bord** (`admin/index.html`) — 5 KPIs, points issued vs. redeemed chart + member growth chart, pending queue (4 items), activity feed, top activities / top rewards / tier distribution.
- **Membres** (`admin/members.html`) — searchable table (8 rows), invite modal, click a row to open the **member drawer** (right-side, 560 px) with profile, recent activity and actions.
- **Activités** (`admin/activities.html`) — 15 earning rules with toggle, category, point value, trigger, limit. Create-activity modal.
- **Avantages** (`admin/benefits.html`) — 3 tabs: pending queue (4 items with approve/reject), catalogue (15 rewards), history.
- **Visites** (`admin/visits.html`) — 3 tabs: to validate (3 proposals as cards), scheduled (8 rows), past.
- **Contenu** (`admin/content.html`) — Newsletter list (published + drafts), KB moderation (2 pending), forum moderation (1 flagged post).
- **Opportunités** (`admin/opportunities.html`) — BTM simulations log, co-investment table, beta access requests.
- **Paramètres** (`admin/settings.html`) — 5 tabs: Programme (tier thresholds + budget), API Naia (connection + event toggles), Notifications, Branding, Équipe admin.

## Demo-worthy interactions

- **Cross-portal switch**: bottom-left of every sidebar. Member → "Portail admin →" · Admin → "← Portail membre".
- **Profile dropdown**: click avatar in bottom-left (sidebar). Works on all 17 pages. Click "Mon profil" from the member portal → navigates to `profile.html`.
- **Modal + drawer keyboard**: `Esc` closes any open modal or drawer.
- **Tab state**: tabs remember the tab within a page but don't persist across navigations (deliberate — keeps URLs simple).
- **Toggles everywhere**: click the blue/grey pill switches on `admin/activities.html`, `admin/settings.html`, `profile.html` preferences.

## Tech stack

- Tailwind CSS v4 (Play CDN, no build step)
- Inter font (Google Fonts, weights 400/500/600/700)
- Lucide icons (CDN)
- Chart.js 4.4.0 (CDN) — 3 charts (member dashboard points, admin issued/redeemed, admin member growth)
- Custom `css/style.css` for tokens + components
- Shared sidebar / topbar / profile dropdown injected from `js/app.js` at `DOMContentLoaded` (reads `<body data-portal data-page data-title data-subtitle>`)

No build, no framework, no bundler. Static HTML — just `git push` and GitHub Pages rebuilds in ~30-60 s.

## Brand tokens

```
--naia-navy:  #1A2B4A    (sidebar gradient, navy buttons)
--naia-cyan:  #00B4D8    (primary accent, active sidebar item, links)
--naia-green: #8DC63F    (points earned, rewards/positive)
--naia-gold:  #f59e0b    (tier gold, premium content)
```

## Iteration workflow

1. Edit any `.html`, `.css`, or `.js` file locally (`C:\Dev\Designs-wireframes\naia-points-v1\`).
2. Commit and push to `main` — GitHub Pages auto-rebuilds.
3. Refresh the live URL after ~45 s (first build takes longer).

## Supersedes

This prototype replaces the Figma Make v20 project at <https://www.figma.com/make/iPF5VJzHQW6BgtTP6MZPjK/B2B-Loyalty-Web-App> for day-to-day iteration. Figma is kept as the historical visual reference; all future edits happen here.

## Related

- Spec / implementation plan: `C:\Dev\naia-points-app\input\implementation-plan.md`
- Requirements: `C:\Dev\naia-points-app\input\requirements-gathering.md`
- Production app (WIP): <https://github.com/hydro-software/naia-points-app> (private)
