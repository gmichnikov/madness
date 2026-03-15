"""
ESPN API integration for fetching teams and scoreboard data.
"""
import json
import urllib.request
from datetime import datetime
from app import db
from app.models import EspnTeam

ESPN_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams?limit=400"
ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?seasontype=3&group=100&limit=100"

# Placeholder espn_id range for manual teams (not in ESPN teams API). Scores won't sync until set-espn-id.
MANUAL_ESPN_ID_BASE = 900000


def fetch_espn_teams():
    """
    Fetch all NCAA men's basketball teams from ESPN API.
    Returns list of dicts with espn_id, display_name, short_display_name, abbreviation.
    """
    with urllib.request.urlopen(ESPN_TEAMS_URL) as response:
        data = json.loads(response.read().decode())

    teams = []
    try:
        raw_teams = data["sports"][0]["leagues"][0]["teams"]
    except (KeyError, IndexError):
        return teams

    for item in raw_teams:
        team = item.get("team", item)
        teams.append({
            "espn_id": int(team["id"]),
            "display_name": team.get("displayName", ""),
            "short_display_name": team.get("shortDisplayName", ""),
            "abbreviation": team.get("abbreviation", ""),
        })

    return teams


def refresh_espn_teams():
    """
    Fetch teams from ESPN and upsert into EspnTeam table.
    """
    teams = fetch_espn_teams()
    for t in teams:
        existing = EspnTeam.query.filter_by(espn_id=t["espn_id"]).first()
        if existing:
            existing.display_name = t["display_name"]
            existing.short_display_name = t["short_display_name"]
            existing.abbreviation = t["abbreviation"]
        else:
            db.session.add(EspnTeam(
                espn_id=t["espn_id"],
                display_name=t["display_name"],
                short_display_name=t["short_display_name"],
                abbreviation=t["abbreviation"],
            ))
    db.session.commit()
    return len(teams)


def fetch_espn_scoreboard():
    """Fetch NCAA tournament scoreboard. Returns raw JSON."""
    with urllib.request.urlopen(ESPN_SCOREBOARD_URL) as response:
        return json.loads(response.read().decode())


def _next_manual_espn_id():
    """Return next available placeholder espn_id for manual teams."""
    max_id = db.session.query(db.func.max(EspnTeam.espn_id)).filter(
        EspnTeam.espn_id >= MANUAL_ESPN_ID_BASE
    ).scalar()
    return (max_id or MANUAL_ESPN_ID_BASE) + 1


def add_manual_espn_team(short_name, display_name=None, abbreviation=None):
    """
    Add a manually-created EspnTeam for teams not in ESPN's API (e.g. first-year D1).
    Uses a placeholder espn_id so bracket works. Run set-espn-id with the real ID
    once discovered (from list-scoreboard-teams when games are listed).
    """
    display_name = display_name or short_name
    abbrev = (abbreviation or (short_name[:4] if len(short_name) >= 4 else short_name)).upper()
    espn_id = _next_manual_espn_id()
    et = EspnTeam(
        espn_id=espn_id,
        display_name=display_name,
        short_display_name=short_name,
        abbreviation=abbrev,
    )
    db.session.add(et)
    db.session.commit()
    return et


def set_espn_id(short_name_or_placeholder_id, real_espn_id):
    """
    Update a manual team's placeholder espn_id to the real ESPN ID.
    Also updates any Team (bracket slot) that references the placeholder.
    """
    from app.models import Team
    try:
        placeholder_int = int(short_name_or_placeholder_id)
    except (ValueError, TypeError):
        placeholder_int = None
    if placeholder_int is not None:
        et = EspnTeam.query.filter_by(espn_id=placeholder_int).first()
    else:
        et = EspnTeam.query.filter(
            EspnTeam.espn_id >= MANUAL_ESPN_ID_BASE,
            EspnTeam.short_display_name.ilike(short_name_or_placeholder_id)
        ).first()
    if not et:
        return None
    old_id = et.espn_id
    if old_id == real_espn_id:
        return et
    for slot in Team.query.filter(Team.espn_team_id == old_id).all():
        slot.espn_team_id = real_espn_id
    for slot in Team.query.filter(Team.espn_play_in_team_2_id == old_id).all():
        slot.espn_play_in_team_2_id = real_espn_id
    et.espn_id = real_espn_id
    db.session.commit()
    return et


def fetch_scoreboard_team_ids():
    """
    Fetch team IDs and names from tournament scoreboard (all events, not just completed).
    Use to discover real ESPN IDs for manual teams when bracket/games are listed.
    Returns list of {espn_id, display_name, short_display_name}.
    """
    data = fetch_espn_scoreboard()
    seen = set()
    result = []
    for ev in data.get("events", []):
        try:
            comps = ev.get("competitions", [{}])[0]
            for c in comps.get("competitors", []):
                team = c.get("team", c)
                tid = team.get("id") or c.get("id")
                if not tid:
                    continue
                tid_int = int(tid)
                if tid_int in seen:
                    continue
                seen.add(tid_int)
                result.append({
                    "espn_id": tid_int,
                    "display_name": team.get("displayName", c.get("displayName", "")),
                    "short_display_name": team.get("shortDisplayName", c.get("shortDisplayName", "")),
                })
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(result, key=lambda t: (t["short_display_name"] or "").lower())


fetch_scoreboard_teams = fetch_scoreboard_team_ids  # alias for CLI


def parse_completed_events(data):
    """
    Parse completed events from scoreboard response.
    Returns list of dicts: {team_ids: (id1, id2), winner_espn_id: int, event_date: datetime}
    """
    events = data.get("events", [])
    result = []
    for ev in events:
        status = ev.get("status", {}).get("type", {})
        if not status.get("completed"):
            continue
        try:
            comps = ev.get("competitions", [{}])[0]
            competitors = comps.get("competitors", [])
            if len(competitors) != 2:
                continue
            ids = []
            scores = {}
            winner_id = None
            for c in competitors:
                tid = c.get("id") or c.get("team", {}).get("id")
                if tid:
                    tid_int = int(tid)
                    ids.append(tid_int)
                    try:
                        scores[tid_int] = int(c.get("score", 0))
                    except (TypeError, ValueError):
                        scores[tid_int] = 0
                if c.get("winner"):
                    winner_id = int(tid) if tid else None
            if len(ids) != 2:
                continue
            if winner_id is None:
                winner_id = max(ids, key=lambda x: scores.get(x, 0))
            date_str = ev.get("date") or comps.get("date", "")
            event_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else None
            result.append({
                "team_ids": tuple(ids),
                "winner_espn_id": winner_id,
                "event_date": event_date,
            })
        except (KeyError, TypeError, ValueError):
            continue
    return result
