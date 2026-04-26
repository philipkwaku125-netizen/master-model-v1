def extract_goals(r):
    home_goals = 0
    away_goals = 0

    try:
        scores = r.get("scores", [])

        for s in scores:
            if s.get("description") == "CURRENT":
                home_goals = s.get("score", {}).get("goals", 0)
                away_goals = s.get("score", {}).get("opponent_goals", 0)
                return home_goals, away_goals
    except:
        pass

    return None, None
