import requests
import gspread
import os
from google.oauth2.service_account import Credentials

SPORTMONKS_TOKEN = os.getenv("SPORTMONKS_TOKEN")

URL = f"https://api.sportmonks.com/v3/football/fixtures?api_token={SPORTMONKS_TOKEN}&from=2022-01-01&to=2026-12-31"

def fetch_data():
    res = requests.get(URL)
    data = res.json()
    return data.get("data", [])

def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        "service_account.json",
        scopes=scope
    )

    client = gspread.authorize(creds)
    sheet = client.open("MASTER MODEL v1").worksheet("API_MATCHES")
    return sheet

def update_sheet(rows):
    sheet = connect_sheet()
    sheet.clear()

    headers = ["MatchID", "League", "DateTime", "HomeTeam", "AwayTeam", "Status"]
    sheet.append_row(headers)

    for r in rows:
        try:
            sheet.append_row([
                r.get("id"),
                r.get("league_id"),
                r.get("starting_at"),
                r["participants"][0]["name"],
                r["participants"][1]["name"],
                r.get("state_id")
            ])
        except:
            continue

def run():
    try:
        print("Starting fetch...")
        data = fetch_data()
        print("Fetched:", len(data))

        update_sheet(data)
        print("Sheet updated successfully")

    except Exception as e:
        print("ERROR:", str(e))
        raise

run() 
