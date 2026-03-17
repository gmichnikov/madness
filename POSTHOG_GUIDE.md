# PostHog Integration Guide for Madness (March Madness Pool)

A step-by-step guide to setting up PostHog in both the PostHog dashboard and this codebase.

---

## Phase 1: Create Project & Get Keys (PostHog)

1. **Log into PostHog** at [app.posthog.com](https://app.posthog.com) (or your self-hosted URL).

2. **Create a new project** for Madness:
   - Click **Projects** in the left sidebar (or your org name).
   - Click **+ New project**.
   - Name it something like `Madness` or `March Madness Pool`.

3. **Get your keys**:
   - Go to **Project Settings** → **Project API Key**.
   - Copy the **Project API Key** (also called `api_key` or `project_api_key`).
   - Optionally copy the **Host** URL if not using `https://us.i.posthog.com` (or `https://eu.i.posthog.com` for EU).

4. **Add env vars locally** (or in production):
   ```
   POSTHOG_API_KEY=phc_your_key_here
   POSTHOG_HOST=https://us.i.posthog.com
   ```

---

## Phase 2: Basic Tracking (Frontend JS snippet)

### In PostHog
- No setup needed for basic pageviews; PostHog’s JS SDK auto-captures `$pageview` events.

### In this codebase
- Add the PostHog JS snippet to `base.html` (before `</head>`).
- Pass `POSTHOG_API_KEY` and `POSTHOG_HOST` from config into templates (e.g. via `inject_globals`).
- Result: every page load sends a `$pageview` with URL, referrer, etc.

---

## Phase 3: Identify Users & User Properties

### In PostHog
- **Product analytics** → events will show distinct users once we call `identify`.
- **Persons** → each identified user will appear.

### In this codebase
- Call `posthog.identify(distinct_id, { properties })` on login.
- `distinct_id`: use a stable ID (e.g. `user_${user.id}` or `user.email`).
- Properties: `email`, `full_name`, `time_zone`, `is_admin`, `is_super_admin`, `is_verified`, `pool_id`, etc.
- Call `identify` on every page load for authenticated users (e.g. in base template or a small script block).

---

## Phase 4: Custom Events (Frontend)

### In PostHog
- Define these as **Actions** or use them in **Insights** once they start flowing.
- **Data Management** → **Events** → you’ll see events as they arrive.

### Events to implement (frontend, via `posthog.capture`)

| Event name | When to fire | Properties |
|-----------|--------------|------------|
| `bracket_pick_made` | User selects a team in a game | `game_id`, `team_id`, `round_id` |
| `bracket_auto_fill_clicked` | User clicks “Auto fill” | — |
| `bracket_saved` | User saves bracket (validation success) | `is_valid`, `games_picked` |
| `standings_viewed` | User lands on standings page | `sort_by` (if applicable) |
| `standings_sorted` | User changes sort | `sort_by` |
| `predictions_viewed` | User lands on predictions | — |
| `simulate_standings_viewed` | User lands on scenarios | — |
| `simulate_standings_ran` | User runs simulation | `scenario_type` or similar |
| `compare_brackets_opened` | User opens compare view | `compared_user_ids` |
| `thread_created` | User creates a forum thread | `thread_id`, `title` |
| `post_created` | User creates a post | `thread_id`, `post_id` |
| `thread_viewed` | User opens a thread | `thread_id` |
| `pool_insights_viewed` | User lands on insights | — |
| `winners_viewed` | User lands on winners history | — |
| `venmo_clicked` | User clicks Venmo verify link | — |
| `profile_edited` | User saves profile | — |
| `password_reset_requested` | User requests reset | — |
| `login_failed` | Login failed | `reason` (e.g. invalid credentials) |

---

## Phase 5: Custom Events (Backend, server-side)

Use **PostHog Python SDK** for events that happen on the server (no JS).

### In PostHog
- Same events will appear in **Product** → **Events**.
- Use `posthog.capture()` with `distinct_id` set to the user (or anonymous ID for unauthenticated actions).

### In this codebase
- Add `posthog` to `requirements.txt`.
- Initialize the client once (e.g. in `app/__init__.py` or a `posthog_client.py` module).
- Call `posthog.capture(distinct_id, event_name, properties)` after important server actions.

### Events to implement (backend)

| Event name | When to fire | Properties |
|-----------|--------------|------------|
| `user_registered` | Registration success | `user_id`, `pool_id`, `time_zone` |
| `user_logged_in` | Login success | `user_id` |
| `user_logged_out` | Logout | `user_id` |
| `bracket_completed` | User has valid bracket | `user_id`, `games_picked`, `champion_team_id` |
| `user_verified` | Admin verifies user | `user_id`, `verified_by` |
| `admin_set_winners` | Admin sets game winners | `admin_id`, `games_updated` |
| `admin_verified_user` | Admin verifies a user | `admin_id`, `verified_user_id` |
| `thread_created` | Thread created (server confirms) | `thread_id`, `user_id`, `title` |
| `post_created` | Post created (server confirms) | `post_id`, `thread_id`, `user_id` |
| `password_reset_completed` | Password reset success | `user_id`, `method` (email / code) |
| `user_deleted` | Super admin deletes user | `deleted_user_id`, `deleted_by` |

---

## Phase 6: Session Recordings

### In PostHog
1. Go to **Session recordings** (or **Recordings**).
2. Enable **Record user sessions**.
3. Optional: adjust sampling rate, privacy (mask inputs, block URLs).
4. Optional: **Recording filters** to only record certain users, pages, or events.

### In this codebase
- Recordings work automatically once the JS snippet is loaded.
- Optionally add `posthog.startSessionRecording()` for finer control.
- Optional: add `$session_recording_url` or custom properties to help filter recordings.

---

## Phase 7: Feature Flags

### In PostHog
1. Go to **Feature flags**.
2. Create flags, e.g.:
   - `show-predictions-beta` – show predictions page to subset of users.
   - `new-bracket-ui` – A/B test a new bracket UI.
   - `enable-forum` – turn forum on/off.
   - `maintenance-mode` – show maintenance message.

3. Configure rollout: % of users, specific users (by `email` or `distinct_id`), or cohorts.

### In this codebase
- Call `posthog.isFeatureEnabled('flag-key')` (async) or `posthog.getFeatureFlag('flag-key')` in JS.
- In templates/views, gate features behind flag checks (e.g. show/hide nav items or sections).
- Server-side: use PostHog Python SDK’s `posthog.feature_enabled(distinct_id, 'flag-key')` in routes.

---

## Phase 8: Surveys & Feedback

### In PostHog
1. Go to **Surveys**.
2. Create a survey (e.g. “How’s the bracket experience?”).
3. Set trigger: after event (e.g. `bracket_saved`), after X pageviews, on specific URL, or % of sessions.
4. Configure question(s), style, and targeting.

### In this codebase
- No extra code needed; PostHog injects the survey widget based on your triggers.
- Ensure `posthog` is loaded on pages where you want surveys.
- Optional: add custom properties to `bracket_saved` so surveys can target “just completed bracket” users.

---

## Phase 9: Funnels & Insights

### In PostHog
1. Go to **Product analytics** → **New insight**.
2. Create **Funnels**, e.g.:
   - `Hero → Register → Make Picks → Bracket Saved`
   - `Login → Make Picks → Bracket Saved`
3. Create **Trends**: e.g. `bracket_pick_made` over time, `thread_created` by day.
4. Create **Retention**: e.g. users who registered vs. users who completed a bracket, by cohort.
5. Use **Breakdowns** by `$current_url`, `round_id`, etc.

### In this codebase
- Ensure all funnel steps send events (pageviews or custom events).
- Add any missing events from Phases 4–5 to make funnels accurate.

---

## Phase 10: Cohorts

### In PostHog
1. Go to **People** → **Cohorts**.
2. Create cohorts, e.g.:
   - **Completed Bracket** – performed `bracket_saved` (or `bracket_completed`).
   - **Active Forum Users** – performed `post_created` or `thread_created` in last 7 days.
   - **Admins** – property `is_admin` = true.
   - **Verified Users** – property `is_verified` = true.
   - **Drop-offs** – performed `$pageview` on `/make_picks` but never `bracket_saved`.

### In this codebase
- Ensure `identify` sets `is_admin`, `is_verified`, etc., so cohorts can filter by these.
- Ensure key actions send the events referenced in cohort definitions.

---

## Phase 11: Group Analytics (Pools)

### In PostHog
1. Go to **Data management** → **Groups**.
2. Add a group type: `pool` (or `organization`).
3. Set `group_type_index` (e.g. 0 for pool).

### In this codebase
- Call `posthog.group('pool', pool_id, { name: poolName, ... })` when user is in a pool.
- Call this after login or on pool-scoped pages.
- Use `posthog.capture(..., { $groups: { pool: pool_id } })` for pool-scoped events.
- Backend: use `group_analytics` in the Python SDK when capturing pool-level events.

---

## Phase 12: A/B Experiments (Optional)

### In PostHog
1. Go to **Experiments** (or **Feature flags** with experiments).
2. Create an experiment tied to a feature flag.
3. Define variants (e.g. control vs. treatment).
4. Set goal metric (e.g. `bracket_saved`, `post_created`).
5. Set exposure: which event means “user saw the variant” (e.g. `$pageview` on make_picks).

### In this codebase
- Use `posthog.getFeatureFlag('experiment-flag')` to get the variant.
- Render different UI based on variant.
- Ensure goal events are captured so PostHog can compute results.

---

## Phase 13: Data Management & Privacy

### In PostHog
1. **Data management** → **Event properties** – define important properties (e.g. `game_id`, `round_id`).
2. **Project settings** → **Data & Privacy** – enable/disable:
   - Session recordings
   - Autocapture
   - IP capture
   - Person profiles
3. Optionally set up **Data pipeline** destinations (webhooks, S3, etc.).

### In this codebase
- Avoid sending PII in event names or properties unless needed.
- Use hashed emails or user IDs instead of raw emails when possible.
- Respect PostHog’s opt-out: `posthog.opt_out_capturing()` if user opts out.

---

## Summary: What to do where

### In PostHog
1. Create Madness project, copy API key and host.
2. Enable Session recordings and tune sampling/privacy.
3. Create Feature flags for experiments and rollouts.
4. Create Surveys for feedback.
5. Build Funnels, Trends, Retention, and Cohorts.
6. Configure Groups for pool-level analytics.
7. Optionally create Experiments and Data pipeline destinations.

### In this codebase
1. Add `POSTHOG_API_KEY` and `POSTHOG_HOST` to config/env.
2. Add PostHog JS snippet to `base.html`.
3. Call `identify` and `group` on login / load.
4. Add `posthog.capture()` for frontend events (picks, UI actions).
5. Add PostHog Python SDK and `posthog.capture()` for backend events.
6. Use `posthog.isFeatureEnabled()` / `posthog.getFeatureFlag()` for flags.
7. Ensure all funnel and cohort steps emit the right events.

---

## Implementation order (recommended)

1. **Phase 1** – Create project, env vars.
2. **Phase 2** – JS snippet in base template.
3. **Phase 3** – Identify on login.
4. **Phase 4** – Key frontend events (`bracket_pick_made`, `bracket_saved`, `standings_viewed`, etc.).
5. **Phase 5** – Backend events (`user_registered`, `user_logged_in`, `bracket_completed`, etc.).
6. **Phase 6** – Enable session recordings in PostHog.
7. **Phase 7** – Add one feature flag and wire it in the app.
8. **Phase 8** – Create one survey.
9. **Phases 9–13** – Use PostHog UI to build dashboards, funnels, cohorts, and experiments.
