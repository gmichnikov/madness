"""
ESPN API integration for fetching teams and scoreboard data.
"""
import json
import urllib.request
from app import db
from app.models import EspnTeam

ESPN_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams?limit=400"


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
