import requests
import gspread
import os
from google.oauth2.service_account import Credentials

# =========================
# 1. API TOKEN
# =========================
SPORTMONKS_TOKEN = os.getenv("SPORTMONKS_TOKEN")

BASE_URL = "https://api.sportmonks.com/v3/football/fixtures"

URL = f"{BASE_URL}?api_token={SPORTMONKS_TOKEN}&include=scores,participants&filters=dates:2022-01-01,2026-12-31"


# =========================
# 2. FETCH DATA
# =========================
def fetch_data():
    res = requests.get(URL)

    print("STATUS:", res.status_code)

    if res.status_code != 200:
        print(res.text[:300])
        return []

    try:
        data = res.json()
    except Exception as e:
        print("JSON ERROR:", e)
        return []

    return data.get("data", [])


# =========================
# 3. CONNECT SHEET
# =========================
def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=scope
    )

    client = gspread.authorize(creds)

    return client.open(
        "MASTER MODEL v1 - Football Prediction Engine"
    ).worksheet("API_MATCHES")


# =========================
# 4. FIXED GOAL EXTRACTION (IMPORTANT)
# =========================
def extract_goals(r):
    scores = r.get("scores", [])

    for s in scores:
        desc = str(s.get("description", "")).upper()

        # accept all valid finished match types
        if desc in ["FT", "FINAL", "FULLTIME", "CURRENT"]:
            score = s.get("score", {})

            home = score.get("goals")
            away = score.get("opponent_goals")

            if home is not None and away is not None:
                try:
                    return int(home), int(away)
                except:
                    return None, None

    return None, None


# =========================
# 5. UPDATE SHEET
# =========================
def update_sheet(rows):
    sheet = connect_sheet()
    sheet.clear()

    headers = [
        "match_id", "league_id", "datetime",
        "home_team", "away_team", "status",
        "home_goals", "away_goals"
    ]

    clean_rows = [headers]

    for r in rows:
        try:
            participants = r.get("participants", [])

            home = participants[0]["name"] if len(participants) > 0 else "Unknown"
            away = participants[1]["name"] if len(participants) > 1 else "Unknown"

            home_goals, away_goals = extract_goals(r)

            # skip invalid matches (THIS IS CRITICAL)
            if home_goals is None or away_goals is None:
                continue

            clean_rows.append([
                r.get("id"),
                r.get("league_id"),
                r.get("starting_at"),
                home,
                away,
                r.get("state_id"),
                home_goals,
                away_goals
            ])

        except Exception as e:
            print("Skipping row:", e)
            continue

    print("VALID MATCHES:", len(clean_rows) - 1)

    if len(clean_rows) <= 1:
        print("❌ No valid matches found")
        return

    sheet.update(clean_rows)


# =========================
# 6. RUN PIPELINE
# =========================
def run():
    print("Starting fetch...")

    data = fetch_data()

    print("Fetched:", len(data))

    if not data:
        print("NO DATA RETURNED")
        return

    update_sheet(data)

    print("✅ Sheet updated successfully")


if __name__ == "__main__":
    run()
