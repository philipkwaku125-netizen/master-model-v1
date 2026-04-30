const axios = require("axios");
const { google } = require("googleapis");

// ====== CONFIG ======
const SHEET_NAME = "API_MATCHES";
const SPREADSHEET_ID = process.env.SPREADSHEET_ID;
const API_KEY = process.env.SPORTMONKS_API_KEY;

// ====== AUTH ======
const auth = new google.auth.GoogleAuth({
  credentials: JSON.parse(process.env.GOOGLE_CREDENTIALS),
  scopes: ["https://www.googleapis.com/auth/spreadsheets"],
});

async function run() {
  try {
    console.log("🚀 Starting pipeline...");

    // ====== DEBUG ENV ======
    console.log("🔍 Checking environment variables...");

    if (!API_KEY) {
      throw new Error("❌ SPORTMONKS_API_KEY is MISSING");
    }

    console.log("✅ API KEY LENGTH:", API_KEY.length);

    if (!SPREADSHEET_ID) {
      throw new Error("❌ SPREADSHEET_ID is MISSING");
    }

    console.log("✅ Spreadsheet ID loaded");

    if (!process.env.GOOGLE_CREDENTIALS) {
      throw new Error("❌ GOOGLE_CREDENTIALS is MISSING");
    }

    console.log("✅ Google credentials loaded");

    const client = await auth.getClient();
    const sheets = google.sheets({ version: "v4", auth: client });

    // ====== 1. FETCH DATA ======
    console.log("📡 Fetching matches from Sportmonks...");

    const url = `https://api.sportmonks.com/v3/football/fixtures?api_token=${API_KEY}`;
    console.log("🌐 URL:", url.replace(API_KEY, "HIDDEN"));

    const response = await axios.get(url);

    const matches = response.data.data;

    if (!matches || matches.length === 0) {
      throw new Error("❌ No matches returned from API");
    }

    console.log(`✅ Fetched ${matches.length} matches`);

    // ====== 2. CLEAR SHEET ======
    console.log("🧹 Clearing old data...");
    await sheets.spreadsheets.values.clear({
      spreadsheetId: SPREADSHEET_ID,
      range: `${SHEET_NAME}!A2:Z`,
    });

    // ====== 3. FORMAT DATA ======
    const rows = matches.map(match => [
      match.id,
      match.league_id,
      match.starting_at,
      match.home_team_id,
      match.away_team_id,
      match.state?.name || "",
      match.scores?.home_score || "",
      match.scores?.away_score || "",
    ]);

    console.log(`📊 Prepared ${rows.length} rows`);

    // ====== 4. WRITE DATA ======
    console.log("✍️ Writing new data...");
    await sheets.spreadsheets.values.update({
      spreadsheetId: SPREADSHEET_ID,
      range: `${SHEET_NAME}!A2`,
      valueInputOption: "RAW",
      requestBody: {
        values: rows,
      },
    });

    console.log("🎉 SUCCESS: Sheet updated!");

  } catch (error) {
    console.error("🔥 ERROR MESSAGE:", error.message);

    if (error.response) {
      console.error("📡 API RESPONSE STATUS:", error.response.status);
      console.error("📡 API RESPONSE DATA:", error.response.data);
    }

    process.exit(1);
  }
}

run(); 
