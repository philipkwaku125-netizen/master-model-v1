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
# 2. FETCH DATA (DEBUG SAFE)
# =========================
def fetch_data():
    res = requests.get(URL)

    print("STATUS:", res.status_code)

    if res.status_code != 200:
        print("API ERROR RESPONSE:")
        print(res.text[:500])
        return []

    try:
        data = res.json()
    except Exception as e:
        print("JSON ERROR:", e)
        print(res.text[:500])
        return []

    # 🔥 SAFETY: SportMonks sometimes returns different structure
    if "data" in data:
        return data["data"]

    print("NO 'data' KEY FOUND. FULL RESPONSE SAMPLE:")
    print(str(data)[:500])
    return []


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

    sheet = client.open("MASTER MODEL v1 - Football Prediction Engine").worksheet("API_MATCHES")
    return sheet


# =========================
# 4. UPDATE SHEET
# =========================
def update_sheet(rows):
    sheet = connect_sheet()
    sheet.clear()

    headers = [
        "MatchID", "League", "DateTime",
        "HomeTeam", "AwayTeam", "Status",
        "HomeGoals", "AwayGoals"
    ]

    sheet.append_row(headers)

    for r in rows:
        try:
            participants = r.get("participants", [])

            home = participants[0]["name"] if len(participants) > 0 else "Unknown"
            away = participants[1]["name"] if len(participants) > 1 else "Unknown"

            # =========================
            # GOALS EXTRACTION (SAFE)
            # =========================
            home_goals = 0
            away_goals = 0

            scores = r.get("scores")

            if isinstance(scores, list) and len(scores) >= 2:
                try:
                    home_goals = scores[0]["score"]["goals"]
                    away_goals = scores[1]["score"]["goals"]
                except:
                    pass

            sheet.append_row([
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


# =========================
# 5. RUN PIPELINE
# =========================
def run():
    print("Starting fetch...")

    data = fetch_data()

    print("Fetched matches:", len(data))

    if len(data) == 0:
        print("❌ NO DATA RETURNED — CHECK API PLAN OR FILTERS")
        return

    update_sheet(data)

    print("Sheet updated successfully!")


if __name__ == "__main__":
    run()
