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
