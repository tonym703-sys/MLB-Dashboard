import json
import os
from datetime import datetime
from scraper import get_standings, get_todays_games, get_probable_pitchers

PITCHER_STATS = {
    "Max Fried":           {"era": 0.00, "xfip": 2.10, "kbb": 28, "whip": 0.75, "hh": 22, "hand": "L"},
    "Edward Cabrera":      {"era": 0.00, "xfip": 2.80, "kbb": 22, "whip": 0.83, "hh": 24, "hand": "R"},
    "Luis Castillo":       {"era": 0.00, "xfip": 2.60, "kbb": 20, "whip": 0.80, "hh": 20, "hand": "R"},
    "Lance McCullers Jr":  {"era": 1.29, "xfip": 2.70, "kbb": 19, "whip": 0.86, "hh": 22, "hand": "R"},
    "Chase Burns":         {"era": 1.80, "xfip": 2.90, "kbb": 20, "whip": 0.90, "hh": 26, "hand": "R"},
    "Kodai Senga":         {"era": 3.00, "xfip": 3.00, "kbb": 18, "whip": 0.94, "hh": 24, "hand": "R"},
    "Jack Leiter":         {"era": 1.50, "xfip": 3.10, "kbb": 18, "whip": 0.88, "hh": 25, "hand": "R"},
    "Roki Sasaki":         {"era": 2.25, "xfip": 3.20, "kbb": 16, "whip": 1.00, "hh": 22, "hand": "R"},
    "Kyle Harrison":       {"era": 1.60, "xfip": 3.30, "kbb": 15, "whip": 0.88, "hh": 26, "hand": "L"},
    "Simeon Woods Richardson": {"era": 2.20, "xfip": 3.50, "kbb": 14, "whip": 0.96, "hh": 28, "hand": "R"},
    "Eric Lauer":          {"era": 1.69, "xfip": 3.60, "kbb": 14, "whip": 0.94, "hh": 27, "hand": "L"},
    "Nick Martinez":       {"era": 3.00, "xfip": 3.80, "kbb": 10, "whip": 1.10, "hh": 30, "hand": "R"},
    "Foster Griffin":      {"era": 2.50, "xfip": 3.90, "kbb": 12, "whip": 1.10, "hh": 28, "hand": "L"},
    "Kris Bubic":          {"era": 1.50, "xfip": 4.65, "kbb":  9, "whip": 1.00, "hh": 32, "hand": "L"},
    "Keider Montero":      {"era": 0.00, "xfip": 4.20, "kbb": 10, "whip": 1.10, "hh": 30, "hand": "R"},
    "Brandon Pfaadt":      {"era": 5.00, "xfip": 4.50, "kbb":  9, "whip": 1.40, "hh": 36, "hand": "R"},
    "Kyle Leahy":          {"era": 7.20, "xfip": 5.00, "kbb":  6, "whip": 1.80, "hh": 38, "hand": "R"},
    "Chris Bassitt":       {"era": 7.00, "xfip": 4.90, "kbb":  6, "whip": 1.80, "hh": 38, "hand": "R"},
    "Davis Martin":        {"era": 5.40, "xfip": 5.00, "kbb":  7, "whip": 1.50, "hh": 36, "hand": "R"},
    "Braxton Ashcraft":    {"era": 4.50, "xfip": 4.70, "kbb":  8, "whip": 1.30, "hh": 34, "hand": "R"},
    "Taijuan Walker":      {"era": 8.00, "xfip": 5.20, "kbb":  5, "whip": 1.90, "hh": 42, "hand": "R"},
    "Walker Buehler":      {"era": 5.40, "xfip": 5.10, "kbb":  5, "whip": 1.50, "hh": 36, "hand": "R"},
    "Ranger Suarez":       {"era": 5.50, "xfip": 4.80, "kbb":  7, "whip": 1.62, "hh": 35, "hand": "L"},
    "Tomoyuki Sugano":     {"era": 2.00, "xfip": 4.30, "kbb":  8, "whip": 0.93, "hh": 30, "hand": "R"},
    "Logan Webb":          {"era": 8.18, "xfip": 5.30, "kbb":  6, "whip": 1.82, "hh": 40, "hand": "R"},
    "Ryan Johnson":        {"era": 9.00, "xfip": 5.50, "kbb":  5, "whip": 2.10, "hh": 44, "hand": "R"},
    "Jacob Lopez":         {"era": 9.00, "xfip": 5.60, "kbb":  4, "whip": 2.25, "hh": 45, "hand": "R"},
    "Chris Paddack":       {"era":12.00, "xfip": 5.40, "kbb":  5, "whip": 2.00, "hh": 42, "hand": "R"},
}

DEFAULT_PITCHER = {"era": 4.50, "xfip": 4.50, "kbb": 8, "whip": 1.35, "hh": 32, "hand": "R"}

def pyth(rs, ra, exp=1.83):
    if rs + ra == 0:
        return 0.5
    return rs ** exp / (rs ** exp + ra ** exp)

def pit_score(name):
    p = PITCHER_STATS.get(name, DEFAULT_PITCHER)
    x = max(0, 1 - p["xfip"] / 7)
    e = max(0, 1 - p["era"] / 7)
    k = min(1, p["kbb"] / 30)
    w = max(0, 1 - p["whip"] / 2.5)
    h = max(0, 1 - p["hh"] / 50)
    return 0.12*x + 0.10*(x*0.6 + e*0.4) + 0.06*k + 0.04*w + 0.03*h

def pit_grade(name):
    s = pit_score(name)
    if s >= 0.23: return "A"
    if s >= 0.18: return "B"
    if s >= 0.12: return "C"
    return "D"

def fair_ml(p):
    if p >= 0.5:
        return f"-{round(100 * p / (1 - p))}"
    return f"+{round(100 * (1 - p) / p)}"

def run_model():
    standings = get_standings()
    games = get_todays_games()

    results = []
    for g in games:
        home = g["home"]
        away = g["away"]
        hp_name = g.get("homePitcher", "TBD")
        ap_name = g.get("awayPitcher", "TBD")

        hd = standings.get(home, {})
        ad = standings.get(away, {})

     LEAGUE_AVG = 4.5

        h_rpg = hd.get("rpgScored", LEAGUE_AVG)
        a_rpg = ad.get("rpgScored", LEAGUE_AVG)
        h_rapg = hd.get("rpgAllowed", LEAGUE_AVG)
        a_rapg = ad.get("rpgAllowed", LEAGUE_AVG)

        h_pyth = pyth(h_rpg, h_rapg)
        a_pyth = pyth(a_rpg, a_rapg)

        h_base = 0.20*h_pyth + 0.10*h_pyth + 0.05*0.6
        a_base = 0.20*a_pyth + 0.10*a_pyth + 0.05*0.5

        h_pit = pit_score(hp_name)
        a_pit = pit_score(ap_name)

        h_bull = max(0.08, min(0.20, 0.20 - (h_rapg - 3.5) * 0.015))
        a_bull = max(0.08, min(0.20, 0.20 - (a_rapg - 3.5) * 0.015))

        h_line = min(0.10, max(0.04, h_rpg / 60))
        a_line = min(0.10, max(0.04, a_rpg / 60))

        h_total = h_base + h_pit + h_bull + h_line + 0.035
        a_total = a_base + a_pit + a_bull + a_line

        prob = h_total / (h_total + a_total)
        winner = home if prob > 0.5 else away
        wp = prob if prob > 0.5 else 1 - prob

        h_pred = (h_rpg + a_rapg) / 2
        a_pred = (a_rpg + h_rapg) / 2
        if prob > 0.5:
            h_pred = max(h_pred, a_pred + 0.3)
        else:
            a_pred = max(a_pred, h_pred + 0.3)

        results.append({
            "home": home,
            "away": away,
            "time": g["time"],
            "homePitcher": hp_name,
            "awayPitcher": ap_name,
            "homePitcherGrade": pit_grade(hp_name),
            "awayPitcherGrade": pit_grade(ap_name),
            "homeWinProb": round(prob, 4),
            "awayWinProb": round(1 - prob, 4),
            "winner": winner,
            "winnerProb": round(wp, 4),
            "fairMLHome": fair_ml(prob),
            "fairMLAway": fair_ml(1 - prob),
            "homePredRuns": round(h_pred, 1),
            "awayPredRuns": round(a_pred, 1),
            "homePyth": round(h_pyth * 100, 1),
            "awayPyth": round(a_pyth * 100, 1),
            "homeRecord": f"{hd.get('w',0)}-{hd.get('l',0)}",
            "awayRecord": f"{ad.get('w',0)}-{ad.get('l',0)}",
            "homeRPG": round(h_rpg, 1),
            "awayRPG": round(a_rpg, 1),
            "edge": wp >= 0.60,
            "lean": 0.56 <= wp < 0.60,
        })

    os.makedirs("data", exist_ok=True)
    with open("data/predictions.json", "w") as f:
        json.dump({
            "generated": datetime.now().strftime("%Y-%m-%d %I:%M %p ET"),
            "games": results,
            "standings": standings
        }, f)

    print(f"Model run complete — {len(results)} games written")

if __name__ == "__main__":
    run_model()
