import pandas as pd
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

    data = pd.DataFrame(sheet.get_all_records())

    print("ROWS LOADED:", len(data))
    print("COLUMNS:", data.columns.tolist())

    return data


df = load_data()

# =========================
# 2. NORMALIZE COLUMN NAMES
# =========================
df.columns = [c.strip().lower() for c in df.columns]

# map possible variations
col_map = {
    "home_goals": "home_goals",
    "away_goals": "away_goals",
    "homegoals": "home_goals",
    "awaygoals": "away_goals"
}

df = df.rename(columns=col_map)

# =========================
# 3. VALIDATE DATA
# =========================
if "home_goals" not in df.columns or "away_goals" not in df.columns:
    raise ValueError("❌ Goals columns missing from sheet")

df["home_goals"] = pd.to_numeric(df["home_goals"], errors="coerce").fillna(0)
df["away_goals"] = pd.to_numeric(df["away_goals"], errors="coerce").fillna(0)

print("\nSAMPLE GOALS:")
print(df[["home_goals", "away_goals"]].head(10))

# =========================
# 4. CREATE TARGET
# =========================
def get_target(row):
    if row["home_goals"] > row["away_goals"]:
        return 2
    elif row["home_goals"] < row["away_goals"]:
        return 0
    else:
        return 1

df["target"] = df.apply(get_target, axis=1)

print("\nCLASS DISTRIBUTION:")
print(df["target"].value_counts())

# =========================
# 5. HARD STOP IF BAD DATA
# =========================
if df["target"].nunique() < 2:
    print("\n❌ DATA PROBLEM DETECTED")
    print("Your dataset has only ONE outcome (likely all draws).")
    print("Fix fetch.py — training skipped.")

    # Save empty model to avoid pipeline crash
    joblib.dump(None, "model.pkl")
    exit()

# =========================
# 6. FEATURES
# =========================
df["goal_diff"] = df["home_goals"] - df["away_goals"]

X = df[["home_goals", "away_goals", "goal_diff"]]
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

print("\n✅ MODEL TRAINED SUCCESSFULLY") 
