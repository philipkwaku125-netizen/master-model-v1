import requests
import gspread
import os
from google.oauth2.service_account import Credentials

# =========================
# 1. CONFIG
# =========================
SPORTMONKS_TOKEN = os.getenv("SPORTMONKS_TOKEN")

BASE_URL = "https://api.sportmonks.com/v3/football/fixtures"

# 🔥 SIMPLE + RELIABLE (no broken filters)
URL = f"{BASE_URL}?api_token={SPORTMONKS_TOKEN}&include=scores,participants&per_page=100"


# =========================
# 2. FETCH DATA
# =========================
def fetch_data():
    print("Fetching from API...")

    res = requests.get(URL)

    print("STATUS:", res.status_code)

    if res.status_code != 200:
        print("API ERROR:", res.text[:300])
        return []

    try:
        data = res.json()
    except Exception as e:
        print("JSON ERROR:", e)
        return []

    return data.get("data", [])


# =========================
# 3. CONNECT GOOGLE SHEET
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

    # ⚠️ MUST MATCH EXACT NAME
    sheet = client.open(
        "MASTER MODEL v1 - Football Prediction Engine"
    ).worksheet("API_MATCHES")

    return sheet


# =========================
# 4. FINAL GOAL EXTRACTION (STABLE)
# =========================
def extract_goals(r):
    try:
        scores = r.get("scores", [])

        for s in scores:
            desc = str(s.get("description", "")).upper()

            # ONLY accept finished matches
            if desc in ["FT", "FINAL", "FULLTIME"]:
                score = s.get("score", {})

                home = score.get("goals")
                away = score.get("opponent_goals")

                if home is not None and away is not None:
                    return int(home), int(away)

        return None, None

    except:
        return None, None


# =========================
# 5. WRITE TO SHEET (FORCED RESET)
# =========================
def update_sheet(rows):
    sheet = connect_sheet()

    print("Clearing sheet...")
    sheet.batch_clear(["A:Z"])

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

            # 🔥 ONLY KEEP REAL RESULTS
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
        print("❌ No valid matches found — THIS IS YOUR PROBLEM")
        return

    sheet.update(clean_rows, value_input_option="RAW")

    print("✅ Sheet updated")


# =========================
# 6. RUN PIPELINE
# =========================
def run():
    data = fetch_data()

    print("TOTAL FROM API:", len(data))

    if not data:
        print("❌ API returned nothing")
        return

    update_sheet(data)


if __name__ == "__main__":
    run()
