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

    const client = await auth.getClient();
    const sheets = google.sheets({ version: "v4", auth: client });

    // ====== 1. FETCH DATA ======
    console.log("📡 Fetching matches...");
    const response = await axios.get(
      `https://api.sportmonks.com/v3/football/fixtures?api_token=${API_KEY}`
    );

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
    console.error("🔥 ERROR:", error.message);
    process.exit(1);
  }
}

run();
