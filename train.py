import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
import joblib
from sklearn.linear_model import LogisticRegression

# =========================
# 1. LOAD DATA
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

    return pd.DataFrame(sheet.get_all_records())


df = load_data()

# =========================
# 2. CLEAN + FIX COLUMNS
# =========================
df = df.fillna(0)

df = df.rename(columns={
    "home_goals": "HomeGoals",
    "away_goals": "AwayGoals",
    "home_team": "HomeTeam",
    "away_team": "AwayTeam"
})

for col in ["HomeGoals", "AwayGoals", "HomeTeam", "AwayTeam"]:
    if col not in df.columns:
        df[col] = 0

df["HomeGoals"] = pd.to_numeric(df["HomeGoals"], errors="coerce").fillna(0)
df["AwayGoals"] = pd.to_numeric(df["AwayGoals"], errors="coerce").fillna(0)

# =========================
# 3. LABELS
# =========================
def result(row):
    if row["HomeGoals"] > row["AwayGoals"]:
        return 2
    elif row["HomeGoals"] < row["AwayGoals"]:
        return 0
    else:
        return 1

df["target"] = df.apply(result, axis=1)

print("CLASS DISTRIBUTION:")
print(df["target"].value_counts())

if df["target"].nunique() < 2:
    raise ValueError("❌ Not enough classes")

# =========================
# 4. FEATURES
# =========================
df["goal_diff"] = df["HomeGoals"] - df["AwayGoals"]

df["home_form"] = df.groupby("HomeTeam")["HomeGoals"].transform(
    lambda x: x.rolling(5, min_periods=1).mean()
)

df["away_form"] = df.groupby("AwayTeam")["AwayGoals"].transform(
    lambda x: x.rolling(5, min_periods=1).mean()
)

df["form_diff"] = df["home_form"] - df["away_form"]

# =========================
# 5. TRAIN
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

model = LogisticRegression(max_iter=1000)
model.fit(X, y)

joblib.dump(model, "model.pkl")

print("✅ MODEL TRAINED SUCCESSFULLY") 
