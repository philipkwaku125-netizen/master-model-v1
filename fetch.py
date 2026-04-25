import requests
import gspread
import os
from google.oauth2.service_account import Credentials

# =========================
# 1. API TOKEN
# =========================
SPORTMONKS_TOKEN = os.getenv("SPORTMONKS_TOKEN")

# ✅ MUST include scores + participants
URL = f"https://api.sportmonks.com/v3/football/fixtures?api_token={SPORTMONKS_TOKEN}&include=scores,participants&from=2022-01-01&to=2026-12-31"


# =========================
# 2. FETCH DATA
# =========================
def fetch_data():
    res = requests.get(URL)

    if res.status_code != 200:
        print("API ERROR:", res.text)
        return []

    data = res.json()
    return data.get("data", [])


# =========================
# 3. GOOGLE SHEET CONNECT
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
            # SAFE GOALS EXTRACTION
            # =========================
            home_goals = 0
            away_goals = 0

            scores = r.get("scores", [])

            if scores and len(scores) >= 2:
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
            print(f"Skipping row: {e}")
            continue


# =========================
# 5. RUN PIPELINE
# =========================
def run():
    print("Starting fetch...")

    data = fetch_data()
    print(f"Fetched: {len(data)} matches")

    if not data:
        print("No data found.")
        return

    update_sheet(data)

    print("Sheet updated successfully!")


if __name__ == "__main__":
    run() 
