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
# 4. EXTRACT REAL SCORES
# =========================
def extract_goals(r):
    try:
        scores = r.get("scores", [])

        for s in scores:
            if s.get("description") == "CURRENT":
                home = s.get("score", {}).get("goals", None)
                away
