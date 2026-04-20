import requests
import gspread
import os
import json
from google.oauth2.service_account import Credentials

# Get the token from GitHub Secrets
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

    # CHANGED: This must match the name in your daily.yml
    creds = Credentials.from_service_account_file(
        "credentials.json", 
        scopes=scope
    )

    client = gspread.authorize(creds)
    # Ensure your Google Sheet is shared with the client_email in your JSON
    sheet = client.open("MASTER MODEL v1").worksheet("API_MATCHES")
    return sheet

def update_sheet(rows):
    sheet = connect_sheet()
    sheet.clear()

    headers = ["MatchID", "League", "DateTime", "HomeTeam", "AwayTeam", "Status"]
    sheet.append_row(headers)

    for r in rows:
        try:
            # Check if participants exist to avoid index errors
            participants = r.get("participants", [])
            home = participants[0]["name"] if len(participants) > 0 else "Unknown"
            away = participants[1]["name"] if len(participants) > 1 else "Unknown"
            
            sheet.append_row([
                r.get("id"),
                r.get("league_id"),
                r.get("starting_at"),
                home,
                away,
                r.get("state_id")
            ])
        except Exception as e:
            print(f"Skipping row due to error: {e}")
            continue

def run():
    try:
        print("Starting fetch...")
        data = fetch_data()
        print(f"Fetched: {len(data)} matches")

        if not data:
            print("No data found from API.")
            return

        update_sheet(data)
        print("Sheet updated successfully!")

    except Exception as e:
        print("ERROR:", str(e))
        raise

if __name__ == "__main__":
    run()
