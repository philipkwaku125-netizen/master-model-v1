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

    # ✅ FIXED SHEET NAME (YOUR REAL NAME)
    sheet = client.open("MASTER MODEL v1 - Football Prediction Engine").worksheet("API_MATCHES")

    data = sheet.get_all_records()

    if not data:
        raise ValueError("Google Sheet is empty")

    return pd.DataFrame(data)

df = load_data()

# =========================
# 2. CLEAN DATA
# =========================
df = df.fillna(0)

for col in ['HomeGoals', 'AwayGoals']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# =========================
# 3. RESULT LABEL
# =========================
def get_result(row):
    if row.get("HomeGoals", 0) > row.get("AwayGoals", 0):
        return "H"
    elif row.get("HomeGoals", 0) < row.get("AwayGoals", 0):
        return "A"
    else:
        return "D"

df["result"] = df.apply(get_result, axis=1)

# =========================
# 4. BASIC FEATURES (TEMP)
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

print("MODEL TRAINED SUCCESSFULLY FROM GOOGLE SHEET") 
