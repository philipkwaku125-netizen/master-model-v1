import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
import joblib
from sklearn.linear_model import LogisticRegression

# =========================
# 1. LOAD FROM GOOGLE SHEET
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
    sheet = client.open("MASTER MODEL v1").worksheet("API_MATCHES")

    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = load_data()

# =========================
# 2. CLEAN DATA
# =========================
df = df.fillna(0)

# Convert goals if they exist later (safe)
for col in ['HomeGoals','AwayGoals']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# =========================
# 3. SIMPLE RESULT LABEL (TEMP MODEL BASE)
# =========================
def get_result(row):
    if row.get("HomeGoals", 0) > row.get("AwayGoals", 0):
        return "H"
    elif row.get("HomeGoals", 0) < row.get("AwayGoals", 0):
        return "A"
    else:
        return "D"

if "HomeGoals" in df.columns:
    df["result"] = df.apply(get_result, axis=1)
else:
    df["result"] = "D"  # fallback until full stats exist

# =========================
# 4. BASIC FEATURES (SAFE START)
# =========================
df["home_strength"] = 1
df["away_strength"] = 1
df["strength_diff"] = 0
df["elo_diff"] = 0
df["home_xg"] = 1
df["away_xg"] = 1

features = [
    "home_strength",
    "away_strength",
    "strength_diff",
    "elo_diff",
    "home_xg",
    "away_xg"
]

X = df[features]
y = df["result"]

# =========================
# 5. TRAIN MODEL
# =========================
model = LogisticRegression(max_iter=1000)
model.fit(X, y)

# =========================
# 6. SAVE MODEL
# =========================
joblib.dump(model, "model.pkl")

print("MODEL TRAINED FROM GOOGLE SHEET")
