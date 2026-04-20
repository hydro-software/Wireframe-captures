# Naia Conference Game - Specification

A timed challenge where hydropower operators spot production losses on a Naia-style dashboard by drawing expected production lines, classifying each loss by category and subcategory, and estimating loss size. Built as a standalone local-first app with the same look & feel as the real Naia platform.

## Spec Documents

1. [Game Concept & Rules](01-game-concept.md) - Core gameplay (draw losses, classify, estimate), 3-level scoring, 5-minute standard timer
2. [Architecture & Tech Stack](02-architecture.md) - Local-first standalone app, SQLite + Google Sheets sync, Infomaniak SMTP email, French UI
3. [Scenario Preparation](03-scenario-preparation.md) - How Bernard creates scenarios (CSV upload, loss marking, intro videos, maintenance events)
4. [Game Flow & UX](04-game-flow-ux.md) - Screen-by-screen walkthrough (START → video → GO → play → summary → email → results → classement), on-screen keyboard, signup page
5. [Registration, Scoreboard & Email](05-registration-scoreboard.md) - Post-game registration, Classement (leaderboard), results email with CTA, Naia signup page
6. [Technical Implementation](06-technical-implementation.md) - Data model, drawing layer, scoring algorithm, API, frontend components
7. [Conference Setup](07-conference-setup.md) - Hardware (single PC, no keyboard), local startup, staffing, fallback plans
8. [Hardware Build: Tabletop Arcade](08-hardware-build.md) - Poplar plywood 15mm cabinet, lightbox logo panel, panel dimensions, transport crate

## Key Decisions

- **Standalone local-first app** — runs on the game PC without internet. The developer stays focused on the product. Google Sheets sync for cloud backup when WiFi available.
- **Draw-to-identify game** — players draw expected production lines on the chart to identify losses, then classify by category and subcategory. Loss size is scored by accuracy of the drawn area.
- **Gameplay screen = Naia dashboard** — the gameplay screen is 100% identical to the real Naia platform, doubling as a live product demo. Only a chronometer is added.
- **Register after play** — no friction before the game. Email capture happens after gameplay when the player wants detailed results.
- **3-level scoring** — category (+10/-5), subcategory (+5/-2), size estimation (0-10 based on accuracy 80-100%)
- **Single mode: 5 minutes** — one standard time for all players, fair leaderboard
- **French UI** — all screens in French including the Classement (leaderboard)
- **No keyboard** — all text input via on-screen virtual keyboard (AZERTY)
- **Infomaniak SMTP** — email results via naia.energy domain, no extra API service needed
- **CTA to naia.energy/signup** — results screen and email include a call-to-action linking to a signup page (part of this project)
- **Poplar plywood 15mm** — ~50% lighter than MDF 18mm, same structural strength
- **Illuminated logo panel** — lightbox with opal acrylic + LED strip for eye-catching branding
- **Multi-console support** — 2 arcade cabinets share a combined leaderboard via Google Sheets with write verification. Each console works offline, syncs when WiFi is available
- **Scoreboard on same PC** — second browser window on a connected TV via 5m HDMI cable
- **Built with Claude Code** — issues and test cases defined upfront, then worked through one by one
