import requests
import gspread
import os
from google.oauth2.service_account import Credentials

# =========================
# 1. API TOKEN
# =========================
SPORTMONKS_TOKEN = os.getenv("SPORTMONKS_TOKEN")

BASE_URL = "https://api.sportmonks.com/v3/football/fixtures"

# ✅ FIX: remove broken date filters + force only finished matches
URL = f"{BASE_URL}?api_token={SPORTMONKS_TOKEN}&include=scores,participants&per_page=100&filters=fixture:finished"


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
# 3. SHEET CONNECTION
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
# 4. SAFE GOALS EXTRACTION
# =========================
def extract_goals(r):
    try:
        participants = r.get("participants", [])

        if len(participants) < 2:
            return None, None

        home = participants[0]
        away = participants[1]

        home_goals = (
            home.get("meta", {}).get("goals")
            or home.get("result", {}).get("goals")
        )

        away_goals = (
            away.get("meta", {}).get("goals")
            or away.get("result", {}).get("goals")
        )

        if home_goals is None or away_goals is None:
            return None, None

        return int(home_goals), int(away_goals)

    except:
        return None, None


# =========================
# 5. UPDATE SHEET (FULL RESET FIX)
# =========================
def update_sheet(rows):
    sheet = connect_sheet()

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

    # 🔥 FULL RESET (IMPORTANT FIX)
    sheet.batch_clear(["A:Z"])
    sheet.update(clean_rows, value_input_option="RAW")


# =========================
# 6. RUN
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
