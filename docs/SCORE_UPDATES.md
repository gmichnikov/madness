# Automatic Score Updates from ESPN

This document outlines how we plan to automatically sync NCAA tournament game results from ESPN's API into our bracket system.

---

## Overview

The goal is to fetch completed game scores from ESPN, match them to our bracket's `Game` records, and automatically set winners—reusing our existing `advance_team_to_next_game`, `recalculate_standings`, etc.

We will store ESPN teams in our DB and constrain the manage-teams UI so admins select from that list. This guarantees correct ESPN IDs for score matching and supports play-in slots (two teams shown until the First Four concludes).

---

## Workflow Summary

**1. What we build now (Phases 1–3):** EspnTeam table, refresh-espn-teams CLI, Team model changes, manage-teams UI with type-to-search inputs (HTML5 datalist), score sync logic, EspnSyncLog for caching, admin sync status UI.

**2. When the tournament starts (Selection Sunday):** Admin runs `flask refresh-espn-teams` to ensure the team list is current. Admin goes to Manage Teams and, for each of the 64 bracket slots, selects the team from the type-to-search input (or for the 4 play-in slots, checks the box and selects both teams). Admin updates `TOURNAMENT_ROUND_DATES` in config for the new season's dates. Cutoff time in `utils.py` is already set per REBOOT_GUIDE.

**3. During the tournament:** When anyone loads Standings or Admin → Set Game Winners, we check `EspnSyncLog`. If we synced within the last 3 minutes, skip. Otherwise, fetch ESPN scoreboard, match completed games to our bracket, set winners, advance teams, recalculate standings, and update `EspnSyncLog`. Scores stay up to date automatically. Admin can still manually set winners on the Set Game Winners page if needed (we never overwrite an already-set winner).

---

## ESPN API

**Scoreboard endpoint:**
```
https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard
```

**Parameters:** `seasontype=3` (postseason), `group=100` (NCAA tournament—verify during implementation), `limit=100`

**Teams endpoint** (for populating our team list):
```
https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams?limit=400
```

Returns ~350+ NCAA teams with `id`, `displayName`, `shortDisplayName`, `abbreviation`. No API key required.

---

## Data Model

### EspnTeam (new table)

Stores the list of teams we fetch from ESPN. Source of truth for display names.

| Column | Type |
|--------|------|
| id | PK |
| espn_id | Integer, unique (ESPN's team ID) |
| display_name | String (e.g. "UConn Huskies") |
| short_display_name | String (e.g. "UConn") |
| abbreviation | String (e.g. "CONN") |

### Team (changes)

| Column | Type | Notes |
|--------|------|-------|
| name | String | Kept for display fallback; synced from EspnTeam when selection is saved |
| espn_team_id | Integer, nullable | ESPN ID for primary team. Null until admin selects one. |
| espn_play_in_team_2_id | Integer, nullable | Second team for play-in slots only. Null for normal teams. |
| is_play_in_slot | Boolean, default False | Checkbox on manage-teams. When true, show second team input. |

**Display logic:** Implemented via `Team.get_display_name(short=True)`:
- If `espn_team_id` is set and `espn_play_in_team_2_id` is set: show `"{EspnTeam1.short_display_name} / {EspnTeam2.short_display_name}"` (e.g. "Grambling / Montana State")
- If `espn_team_id` is set: show `EspnTeam.short_display_name` (e.g. "UConn" not "UConn Huskies")
- If `espn_team_id` is null: show `Team.name` (placeholder like "Region 1: Seed 1")

Use `get_display_name(short=False)` for full names. We keep `Team.name` so existing code that references it still works. When the admin selects from the input, we save `espn_team_id` and update `name` from the selected EspnTeam's `display_name`. For play-in slots with both IDs, we compute the display string at render time.

### EspnSyncLog (new table)

Stores when we last ran the ESPN score sync. Used to avoid re-syncing on every page load.

| Column | Type |
|--------|------|
| id | PK |
| last_sync_at | DateTime, NOT NULL |
| games_updated | Integer, default 0 |

Single row, updated in place. Created on first sync.

---

## Getting the ESPN Teams List

**CLI:** `flask refresh-espn-teams`

1. Fetches from `https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams?limit=400`
2. Parses the response (teams live at `sports[0].leagues[0].teams[]`)
3. Upserts into `EspnTeam` (insert new, update existing by `espn_id`)

Run before Selection Sunday (or whenever you want to refresh). The manage-teams UI reads from this table—the team list will be empty until you run it.

---

## Manage Teams UI

**Implemented:** Table layout with type-to-search inputs (HTML5 datalist).

- **Table:** Columns: Slot (Region, Seed), Team, Play-in, Second Team
- **Team input:** `<input list="...">` with `<datalist>` populated from `EspnTeam` (ordered by `display_name`). User types to filter; selecting from suggestions sets `espn_team_id` via hidden input. Syncs `Team.name` from EspnTeam on save.
- **"Play-in slot" checkbox:** Default false. When checked:
  - Show a second input for the second team (same datalist pattern)
  - Sets `espn_play_in_team_2_id` when second team selected
- **Unset state:** User can clear the input; `espn_team_id` stays null and we show placeholder `Team.name`.
- **CSS:** All classes use `mm-manage-teams-*` prefix to avoid collisions.

---

## Play-in Slots

From Selection Sunday until the First Four concludes (Tue/Wed), 4 bracket slots show both possible teams (e.g. "Grambling / Montana State").

**When the bracket is announced (Selection Sunday):** For each of the 4 play-in slots (e.g. Region 1 Seed 16), admin checks "Play-in slot" and selects both teams from the type-to-search inputs—e.g. Grambling and Montana State. We store `espn_team_id` = first team, `espn_play_in_team_2_id` = second team. Display: `"Grambling / Montana State"`.

**When the First Four game completes (Tue/Wed):** The play-in game (Grambling vs Montana State) is not one of our 63 games. It only determines who fills the 16-seed slot. Our score sync matches the ESPN First Four event to the Round 1 Game that has that play-in slot. We update the slot: set `espn_team_id` = winner (e.g. Grambling), clear `espn_play_in_team_2_id`. Display becomes `"Grambling"`. We do **not** set `game.winning_team_id`—the Round 1 game (1 seed vs 16 seed) hasn't been played yet. We're just filling the slot.

**When the Round 1 game is played (Thu/Fri):** The actual Round 1 game (1 seed vs Grambling) completes. We match that ESPN event normally and set the winner. At that point we call `advance_team_to_next_game`.

---

## Score Sync (ESPN event → our Game)

### Process

1. **Fetch** the ESPN scoreboard (`seasontype=3`, `group=100`).
2. **Filter** to completed events (`status.type.completed == true`).
3. **For each completed event**, extract:
   - ESPN team IDs of the two competitors (from `competitions[0].competitors[]`)
   - Winner: the competitor with the higher `score` (or `winner: true` if present)
4. **Find our matching Game** among games that have `winning_team_id` NULL:
   - **Normal game:** Our `Game` has `team1_id`, `team2_id` → look up `team1.espn_team_id`, `team2.espn_team_id`. Match when `(team1.espn_team_id, team2.espn_team_id)` equals `(A, B)` or `(B, A)` for the ESPN event's two team IDs.
   - **Play-in game:** One of our slots has both `espn_team_id` and `espn_play_in_team_2_id`. Match when the ESPN event's two competitors are exactly that pair (either order). See Play-in slots below.
   - Skip games where either slot has `espn_team_id` NULL (unconfigured).
5. **When a match is found:** Check that the ESPN event's date falls within the expected round window (see Avoiding Wrong Games). If not, skip.
6. **Apply the update** (for normal games only; play-in has different handling—see Play-in slots below):
   - Resolve the winner's ESPN ID to our `Team` (look up `Team` where `espn_team_id` = winner's ESPN ID)
   - Set `game.winning_team_id` = that Team's id
   - Call `advance_team_to_next_game(game, winning_team_id)` to populate the next round
   - Log the update
7. **Process by round:** First Four (play-in) → Round 1 → … → Round 6. Sort ESPN events by date (or infer round from date) and process in that order. Play-in games must complete before Round 1 games have both teams; later rounds need `team1_id`/`team2_id` populated from earlier winners.
8. **After any game updates:** Run the same post-update steps used when admin manually sets winners:
   - `clear_potential_winners_cache()` — invalidate cached potential winners
   - `do_admin_update_potential_winners()` — recompute which teams can still win each game
   - `recalculate_standings()` — update all users' scores and max possible scores

   This keeps pool standings in sync with the new results.

### Play-in slots

Our 63 games don't include the First Four games. The First Four determines who fills 4 of our Round 1 slots. When an ESPN First Four event (A vs B) completes, we match it to a Round 1 Game where one of the two team slots has both `espn_team_id` and `espn_play_in_team_2_id` set to that pair.

When our `Game` has a team slot with both `espn_team_id` and `espn_play_in_team_2_id` set, that slot represents "Team A or Team B" (the play-in winner). The ESPN play-in event has those same two teams. We match when the ESPN event's two competitors are exactly `(espn_team_id, espn_play_in_team_2_id)` in either order. When we find that match:
- **Only** update the slot: set `espn_team_id` = winner's ESPN ID, clear `espn_play_in_team_2_id`
- **Do not** set `game.winning_team_id`—the Round 1 game (e.g. 1 seed vs 16 seed) hasn't been played yet; we're just filling the slot with the play-in winner
- **Do not** call `advance_team_to_next_game`—no game was decided
- **Do not** run standings steps—no picks were resolved
- **Do** update `EspnSyncLog` (with `games_updated=0`) so we don't re-fetch unnecessarily

The actual Round 1 game will be played later. When it completes, we'll match that ESPN event as a normal game and set the winner then.

---

## Avoiding Wrong Games

**Risk:** `seasontype=3` returns all postseason games. Without filtering, we could match:
- Conference tournament games (e.g. Duke vs UNC in ACC final)
- NIT or other non-NCAA games

**Mitigation:**
1. **API filter:** Use `group=100` to restrict to NCAA tournament. Verify during implementation that this returns only NCAA tournament games.
2. **Date validation:** Maintain a config of expected date ranges per round. Only process ESPN events whose date falls within the round's window. If we find a match but the event date is outside the expected window, skip it (or log a warning).

**Round date config** (in `app/utils.py`, update each season):

- ESPN returns event dates in **UTC**. We convert to **Eastern** before comparing.
- End date includes a **+1 day buffer** so games that run past midnight (e.g. 9pm start, ends 12:30am) still match.
- 2026 dates: First Four Mar 17–18, 1st Round Mar 19–20, 2nd Round Mar 21–22, Sweet 16 Mar 26–27, Elite 8 Mar 28–29, Final Four Apr 4, Championship Apr 6.

**When to check:** After finding a matching Game, verify the ESPN event's date (in Eastern) falls within the expected range. For play-in matches, use round 0; for normal matches, use `game.round_id`. If the date is outside the range, skip (or log a warning).

**Note:** Regular-season games use `seasontype=2` and won't appear in our fetch—we're safe from those. The risk is only other postseason games (conference tournaments, NIT) if filters fail.

**Benefits:** Extra safety if `group=100` is unreliable; clearer expectations; easier debugging.

---

## Trigger and Caching

**Trigger:** When someone loads `/standings` or `/admin/set_winners`, we attempt a sync (unless we synced recently).

**Caching approach:** Store last sync time in the DB (`EspnSyncLog` table). TTL = 3 minutes.

### When we read it

- **Where:** At the start of the sync flow, before fetching ESPN.
- **How:** `SELECT last_sync_at FROM espn_sync_log ORDER BY id DESC LIMIT 1` (or query the single row).
- **Decision:** If a row exists and `(now - last_sync_at).total_seconds() < 180` (3 minutes), skip the sync—don't fetch ESPN, don't process. Return immediately.
- **If no row exists:** Treat as "never synced"; run the sync.

### When we update it

- **Where:** After the sync completes (after we've updated games, run standings steps, etc.).
- **How:** Upsert the single row: `UPDATE espn_sync_log SET last_sync_at = now(), games_updated = N`. If no row exists, `INSERT` one.
- **When we update games:** Always update the row (even if `games_updated` is 0—we still ran the sync).
- **When we skip (cache hit):** Don't update—we didn't run the sync.

### Bypass

Admin "Refresh now" (Phase 3) bypasses the cache: run the sync regardless of `last_sync_at`.

### Effect

Works across all workers and instances. Survives deploys. With a 3-minute TTL, at most ~20 syncs per hour. Single DB query per page load to check.

---

## Edge Cases

1. **First Four:** Play-in games aren't in our 63-game bracket. Ignore ESPN events that don't match.
2. **Unset teams:** `espn_team_id` null → skip that game in sync. Admin can set manually.
3. **Already-set winners:** Only update games where `winning_team_id` is NULL.
4. **Event date outside all round windows:** Skip (e.g. config is wrong, or tournament delayed).

---

## Implementation Guide

A step-by-step guide for building the feature and operating it each season.

---

### Phase 1: Data Model and Manage Teams ✅ DONE

**1.1 Add EspnTeam model** ✅

- In `app/models.py`, add `EspnTeam` with columns: `id`, `espn_id` (Integer, unique), `display_name`, `short_display_name`, `abbreviation`
- Run `flask db migrate -m "Add EspnTeam table"` (you run this)
- Run `flask db upgrade` (you run this)

**1.2 Add Team columns** ✅

- In `app/models.py`, add to `Team`: `espn_team_id` (Integer, nullable), `espn_play_in_team_2_id` (Integer, nullable), `is_play_in_slot` (Boolean, default False, `server_default=sa.false()` in migration for existing rows)
- Run `flask db migrate` and `flask db upgrade` (you run this)

**1.3 Create `app/espn.py`** ✅

- Add `fetch_espn_teams()` — GET the teams endpoint, parse `sports[0].leagues[0].teams[]`, return list of dicts with `espn_id`, `display_name`, `short_display_name`, `abbreviation`
- Add `refresh_espn_teams()` — call fetch, upsert into `EspnTeam` by `espn_id`

**1.4 Add `flask refresh-espn-teams` CLI** ✅

- In `app/__init__.py`, add a click command that calls `refresh_espn_teams()`

**1.5 Update Manage Teams form and template** ✅

- Table layout with columns: Slot, Team, Play-in, Second Team
- HTML5 datalist: `<input list="...">` + `<datalist>` per team, populated from `EspnTeam` (ordered by `display_name`). User types to filter; hidden input stores `espn_id` for form submission.
- "Play-in slot" checkbox; when checked, show second input with same datalist pattern
- CSS class prefixes `mm-manage-teams-*`

**1.6 Update Manage Teams route** ✅

- Load `EspnTeam`, pass `selected_names` and `selected_names_2` for pre-populating inputs
- On POST: save `espn_team_id`, `espn_play_in_team_2_id`, `is_play_in_slot` from `request.form`
- When `espn_team_id` is set, sync `Team.name` from EspnTeam's `display_name`
- When `is_play_in_slot` unchecked, clear `espn_play_in_team_2_id`
- Call `clear_teams_cache()`

**1.7 Update display logic for Team names** ✅

- Added `Team.get_display_name(short=True)` — uses `short_display_name` by default (school name only, no mascot)
- Updated templates: `_shared_grid.html`, set_winners, view_picks, make_picks, simulate_standings, pool_insights
- Updated routes: standings (champion_picks), set_winners (log entries), show_potential_winners, pool_insights
- Updated forms: SortStandingsForm champion_teams

**1.8 Test Phase 1**

- Run `flask refresh-espn-teams`
- Go to Admin → Edit Teams. Verify type-to-search works. Select teams, check play-in slot, select both teams, save. Verify DB and display.

---

### Phase 2: Score Sync ✅ DONE

**2.1 Add EspnSyncLog model** ✅

- In `app/models.py`, add `EspnSyncLog` with `id`, `last_sync_at`, `games_updated`
- Run `flask db migrate -m "Add EspnSyncLog table"` (you run this)
- Run `flask db upgrade` (you run this)

**2.2 Add TOURNAMENT_ROUND_DATES config** ✅

- In `app/utils.py`, add `TOURNAMENT_ROUND_DATES` dict with round 0–6 and date ranges. 2026 dates; update each season.

**2.3 Add ESPN scoreboard fetch and parsing** ✅

- In `app/espn.py`, add `fetch_espn_scoreboard()` — GET scoreboard with `seasontype=3`, `group=100`, `limit=100`. Return raw JSON or parsed events. Verify during implementation that `group=100` returns only NCAA tournament games (see Avoiding Wrong Games).
- Add `parse_completed_events(data)` — filter to `status.type.completed == true`, extract team IDs, winner (from `winner` or higher `score`), event date.

**2.4 Add sync logic** ✅

- In `app/routes.py`, add `sync_espn_results_to_games(force=False)`:
  1. Unless `force=True`: Query `EspnSyncLog` for `last_sync_at`. If exists and `(now - last_sync_at).total_seconds() < 180`, return early (cache hit).
  2. Fetch scoreboard, parse completed events.
  3. Sort events by date (First Four first, then Round 1, etc.).
  4. For each event: find matching Game among games with `winning_team_id` NULL. Normal: both slots have single `espn_team_id`; play-in: one slot has both `espn_team_id` and `espn_play_in_team_2_id` matching the event's two teams. Skip if either slot has `espn_team_id` NULL (unconfigured). Check event date: for play-in match use round 0 range; for normal match use `game.round_id` range. If date outside range, skip (or log warning). If play-in match: update that slot only (`espn_team_id` = winner, clear `espn_play_in_team_2_id`). If normal match: resolve winner's ESPN ID to our `Team` (look up where `espn_team_id` = winner), set `game.winning_team_id`, call `advance_team_to_next_game`, increment games_updated count, log the update.
  5. If any normal games were updated: run `clear_potential_winners_cache()`, `do_admin_update_potential_winners()`, `recalculate_standings()`.
  6. Upsert `EspnSyncLog`: UPDATE if row exists, INSERT if not. Set `last_sync_at = now()`, `games_updated = N`. (Do this even for play-in-only syncs, with `games_updated=0`.)

**2.5 Wire sync into standings and set_winners** ✅

- At the start of `standings` and `admin_set_winners`, call `sync_espn_results_to_games()`.

**2.6 Test Phase 2**

- Before tournament: sync will run but find no completed NCAA games. Verify no errors, `EspnSyncLog` gets a row.
- During tournament (or with mocked ESPN response): verify matching and winner updates work.

---

### Phase 3: Admin Sync UI ✅ DONE

**3.1 Add sync status to Set Game Winners page** ✅

- Display "Last synced: X min ago" using `EspnSyncLog.last_sync_at`. "Refresh now" button triggers sync with cache bypass.

**3.2 Add refresh endpoint** ✅

- POST `/admin/refresh_espn_scores` calls `sync_espn_results_to_games(force=True)`. Redirects to set_winners. Admin-only.

**3.3 Add logging** ✅

- When sync updates games: `LogEntry` category "ESPN Sync", description "Auto-synced N games from ESPN". When play-in slot filled: "Filled play-in slot from ESPN".

---

### Seasonal Workflow (When to Do What)

| When | What |
|------|------|
| **Before season** | Phase 1–3 implemented and deployed. Run `flask refresh-espn-teams` so team list has data. |
| **Selection Sunday** | 1. Run `flask refresh-espn-teams` (optional, to refresh names). 2. Update `TOURNAMENT_ROUND_DATES` in config for new dates. 3. Update cutoff in `app/utils.py` per REBOOT_GUIDE. 4. Admin → Edit Teams: assign all 64 slots. For 4 play-in slots, check the box and select both teams. Save. |
| **Tue/Wed (First Four)** | Score sync runs when users load Standings or Set Winners. Play-in events fill the 4 slots. No manual action needed unless sync fails. |
| **Thu–Sun (Rounds 1–2)** | Sync continues automatically. Admin can manually set winners on Set Game Winners if needed. |
| **Subsequent weekends** | Same. Sync runs on page load (3-min cache). |
| **After tournament** | No action. Sync finds no new games. Next season: reset bracket per REBOOT_GUIDE, then repeat Selection Sunday steps. |
