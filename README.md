# MALICE — Westerlands Progression Tracking

Independent password-protected Streamlit dashboard, based on the Fire Gremlins layout.

## Deploy
1. Upload the contents of this folder to a GitHub repository, preserving `.streamlit/`.
2. Deploy `app.py` using Streamlit Community Cloud.
3. In Streamlit app Settings → Secrets, enter:
   `WAR_COUNCIL_PASSWORD = "choose-a-private-password"`
4. Do not upload a real `secrets.toml` file to GitHub.

## Data
`progress.xlsx` has the 50-member November 23, 2026 snapshot on **Day 5**.
Days 1–4 are intentionally blank. Add Day 6 and later reports to `Player Progress`.
Replace `progress.xlsx` in GitHub to update the deployed app. Sidebar uploads are session-only.

Screenshots show the in-game label *HR Department*, while the dashboard is branded MALICE as requested. Please verify unusual characters in player names.
