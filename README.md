# Taqeem SSO + OTP + Report Delete / Asset Cleanup (Nodriver)

Flow:
1) Login at SSO (username + password) and OTP.
2) Prompt for a **Report ID** (loop until you type Q to quit).
   - Open the report page.
   - If **Delete Report** button exists → auto-confirm and delete the report.
   - Else → look for the asset table. For rows whose status is **غير مكتملة**:
     - Delete each via `https://qima.taqeem.sa/report/macro/<ID>/delete`.
     - If **all** assets are غير مكتملة, delete **all except the first**, then open the first one's **Edit** page.
3) Use persistent profile; zip it at the end.

## Setup
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# edit .env if needed
python -m src.main
```
