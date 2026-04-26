import requests
import gspread
import os
from google.oauth2.service_account import Credentials

SPORTMONKS_TOKEN = os.getenv("SPORTMONKS_TOKEN")

BASE_URL = "https://api.sportmonks.com/v3/football/fixtures"

URL = f"{BASE_URL}?api_token={SPORTMONKS_TOKEN}&include=scores,participants&per_page=20"


# =========================
# FETCH
# =========================
def fetch_data():
    res = requests.get(URL)

    print("STATUS:", res.status_code)

    if res.status_code != 200:
        print("API ERROR:", res.text[:300])
        return []

    data = res.json()

    print("RAW KEYS:", data.keys())

    return data.get("data", [])


# =========================
# SHEET CONNECT
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

    # ⚠️ IMPORTANT: this MUST match your real sheet title exactly
    sheet = client.open_by_url(os.getenv("SHEET_URL")).worksheet("API_MATCHES")

    return sheet


# =========================
# SIMPLE GOALS (NO FILTERS YET)
# =========================
def extract_goals(r):
    try:
        scores = r.get("scores", [])

        for s in scores:
            score = s.get("score", {})

            home = score.get("goals")
            away = score.get("opponent_goals")

            if home is not None and away is not None:
                return int(home), int(away)

        return None, None
    except:
        return None, None


# =========================
# WRITE TO SHEET (DEBUG SAFE)
# =========================
def update_sheet(rows):
    sheet = connect_sheet()

    print("➡ Clearing sheet...")
    sheet.clear()

    headers = ["match_id", "home", "away", "hg", "ag"]

    clean = [headers]

    for r in rows:
        participants = r.get("participants", [])

        home = participants[0]["name"] if len(participants) > 0 else "N/A"
        away = participants[1]["name"] if len(participants) > 1 else "N/A"

        hg, ag = extract_goals(r)

        print("MATCH:", home, away, hg, ag)

        if hg is None or ag is None:
            continue

        clean.append([r.get("id"), home, away, hg, ag])

    print("FINAL ROWS:", len(clean))

    sheet.update(clean)


# =========================
# RUN
# =========================
def run():
    print("STARTING PIPELINE")

    data = fetch_data()

    print("MATCHES RECEIVED:", len(data))

    if not data:
        print("NO DATA FROM API")
        return

    update_sheet(data)

    print("DONE")


if __name__ == "__main__":
    run() 
