import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
import joblib
from sklearn.linear_model import LogisticRegression

# =========================
# 1. LOAD DATA FROM SHEET
# =========================
def load_data():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=scope
    )

    client = gspread.authorize(creds)

    sheet = client.open(
        "MASTER MODEL v1 - Football Prediction Engine"
    ).worksheet("API_MATCHES")

    data = pd.DataFrame(sheet.get_all_records())
    return data


df = load_data()

# =========================
# 2. CLEAN + FIX COLUMN NAMES
# =========================
df = df.fillna(0)

# 🔥 FIX: align sheet columns with model
df = df.rename(columns={
    "home_goals": "HomeGoals",
    "away_goals": "AwayGoals",
    "home_team": "HomeTeam",
    "away_team": "AwayTeam"
})

# 🔒 SAFETY: ensure columns exist
for col in ["HomeGoals", "AwayGoals", "HomeTeam", "AwayTeam"]:
    if col not in df.columns:
        df[col] = 0

# ensure numeric goals
df["HomeGoals"] = pd.to_numeric(df["HomeGoals"], errors="coerce").fillna(0)
df["AwayGoals"] = pd.to_numeric(df["AwayGoals"], errors="coerce").fillna(0)

# =========================
# 3. CREATE LABELS
# =========================
def result(row):
    if row["HomeGoals"] > row["AwayGoals"]:
        return 2   # Home Win
    elif row["HomeGoals"] < row["AwayGoals"]:
        return 0   # Away Win
    else:
        return 1   # Draw

df["target"] = df.apply(result, axis=1)

# =========================
# 4. VALIDATION
# =========================
print("CLASS DISTRIBUTION:")
print(df["target"].value_counts())

if df["target"].nunique() < 2:
    raise ValueError("❌ Not enough classes. Fix goals data first.")

# =========================
# 5. FEATURE ENGINEERING
# =========================

df["goal_diff"] = df["HomeGoals"] - df["AwayGoals"]

df["home_form"] = df.groupby("HomeTeam")["HomeGoals"].transform(
    lambda
