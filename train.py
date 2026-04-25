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
# 2. CLEAN DATA
# =========================
df = df.fillna(0)

# ensure numeric goals
df["HomeGoals"] = pd.to_numeric(df["HomeGoals"], errors="coerce").fillna(0)
df["AwayGoals"] = pd.to_numeric(df["AwayGoals"], errors="coerce").fillna(0)

# =========================
# 3. CREATE REAL LABELS
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
# 4. VALIDATION (FIX "1 CLASS" ERROR)
# =========================
print("CLASS DISTRIBUTION:")
print(df["target"].value_counts())

if df["target"].nunique() < 2:
    raise ValueError("❌ Not enough classes. Fix goals data first.")

# =========================
# 5. FEATURE ENGINEERING (REAL NOT FAKE)
# =========================

# Basic goal-based features
df["goal_diff"] = df["HomeGoals"] - df["AwayGoals"]

# Rolling form (important upgrade vs your old system)
df["home_form"] = df.groupby("HomeTeam")["HomeGoals"].transform(
    lambda x: x.rolling(5, min_periods=1).mean()
)

df["away_form"] = df.groupby("AwayTeam")["AwayGoals"].transform(
    lambda x: x.rolling(5, min_periods=1).mean()
)

df["form_diff"] = df["home_form"] - df["away_form"]

# =========================
# 6. FINAL FEATURES
# =========================
features = [
    "HomeGoals",
    "AwayGoals",
    "goal_diff",
    "home_form",
    "away_form",
    "form_diff"
]

X = df[features].fillna(0)
y = df["target"]

# =========================
# 7. TRAIN MODEL
# =========================
model = LogisticRegression(max_iter=1000)
model.fit(X, y)

# =========================
# 8. SAVE MODEL
# =========================
joblib.dump(model, "model.pkl")

print("✅ MODEL TRAINED SUCCESSFULLY") 
