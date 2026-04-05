import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_probable_pitchers():
    today = datetime.now()
    month = today.strftime("%B").lower()
    day = today.day
    year = today.year
    url = f"https://dknetwork.draftkings.com/{year}/{today.strftime('%m')}/mlb-probable-pitchers-{month}-{day}-{year}/"
    
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        pitchers = {}
        headings = soup.find_all("h2")
        for h in headings:
            text = h.get_text()
            if "Probable Pitchers" in text and "vs." in text:
                ul = h.find_next("ul")
                if ul:
                    items = ul.find_all("li")
                    for item in items:
                        line = item.get_text()
                        if ":" in line:
                            parts = line.split(":")
                            team = parts[0].strip()
                            pitcher = parts[1].strip().split("\n")[0].strip()
                            pitchers[team] = pitcher
        return pitchers
    except Exception as e:
        print(f"Scraper error: {e}")
        return {}

def get_standings():
    url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        standings = {}
        LEAGUE_AVG_RPG = 4.5
        for record in data.get("records", []):
            for team in record.get("teamRecords", []):
               abbr = team["team"].get("abbreviation") or team["team"].get("teamCode", "").upper()
if not abbr:
    continue
                wins = team["wins"]
                losses = team["losses"]
                games_played = wins + losses
                runs_scored = team.get("runsScored", 0)
                runs_allowed = team.get("runsAllowed", 0)
                if games_played == 0 or runs_scored == 0:
                    rpg_scored = LEAGUE_AVG_RPG
                    rpg_allowed = LEAGUE_AVG_RPG
                else:
                    rpg_scored = runs_scored / games_played
                    rpg_allowed = runs_allowed / games_played
                standings[abbr] = {
                    "w": wins,
                    "l": losses,
                    "runsScored": runs_scored,
                    "runsAllowed": runs_allowed,
                    "rpgScored": rpg_scored,
                    "rpgAllowed": rpg_allowed,
                    "gamesPlayed": games_played,
                    "divisionRank": team.get("divisionRank", ""),
                    "division": record["division"]["name"]
                }
        return standings
    except Exception as e:
        print(f"Standings error: {e}")
        return {}

def get_todays_games():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher,team"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        games = []
        for date in data.get("dates", []):
            for game in date.get("games", []):
                home = game["teams"]["home"]
                away = game["teams"]["away"]
                games.append({
                    "home": home["team"]["abbreviation"],
                    "away": away["team"]["abbreviation"],
                    "time": game.get("gameDate", ""),
                    "homePitcher": home.get("probablePitcher", {}).get("fullName", "TBD"),
                    "awayPitcher": away.get("probablePitcher", {}).get("fullName", "TBD"),
                })
        return games
    except Exception as e:
        print(f"Games error: {e}")
        return []
