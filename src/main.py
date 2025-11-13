# src/main.py
import asyncio
import getpass

from src.auth import login_flow
from src.nav import open_report_by_id
from src.utils import log
from src.browser import stop_browser
from src.report_macro import check_status_and_create_macro_if_cancelled
from src.report_info import extract_report_info

print(">>> imported main.py", flush=True)

async def handle_reports_input():
    try:
        raw = input(
            "Enter one or more Report ID(s) (separate with spaces/commas or paste multiple lines), or Q to quit: "
        )
    except (EOFError, KeyboardInterrupt):
        log("Input cancelled. Quitting.", "INFO")
        return False

    if not raw:
        return True

    import re as _re
    parts = [p.strip() for p in _re.split(r"[\s,;]+", raw) if p.strip()]

    if any(p.lower() in ("q", "quit", "exit") for p in parts):
        return False

    for report_id in parts:
        log(f"Opening report {report_id}", "STEP")
        try:
            page = await open_report_by_id(report_id)
            await asyncio.sleep(2.0)

            info = await extract_report_info(page)
            if info.get("found"):
                alias = info.get("alias") or {}
                log(f"Issue Date: {(alias.get('issue_date') or {}).get('value')}", "INFO")
                log(f"Status: {(alias.get('status') or {}).get('value')}", "INFO")
                log(f"Purpose: {(alias.get('purpose') or {}).get('value')}", "INFO")
                log(f"Report Type: {(alias.get('report_type') or {}).get('value')}", "INFO")
                log(f"Valuation Date: {(alias.get('valuation_date') or {}).get('value')}", "INFO")
                fv = (alias.get('final_value') or {}).get('value')
                if fv:
                    log(f"Final Value: {fv}", "INFO")
                doc = alias.get("original_report_file") or {}
                if doc.get("href"):
                    log(f"Original File Link: {doc['href']}", "INFO")
            else:
                log("Report info not found; proceeding anyway.", "WARN")

            await check_status_and_create_macro_if_cancelled(report_id, page)
            await asyncio.sleep(0.5)

        except Exception as e:
            log(f"Error while opening/processing report {report_id}: {e}", "ERR")

    return True

async def run():
    log("=== Taqeem: Login + Report Info + Create Macro if Cancelled ===")

    try:
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ").strip()
    except (EOFError, KeyboardInterrupt):
        log("Input cancelled before login.", "INFO")
        return

    try:
        ok = await login_flow(username, password)
        if not ok:
            log("Login flow failed.", "ERR")
            return

        while True:
            cont = await handle_reports_input()
            if not cont:
                break

        log("Done. Exiting.", "OK")
    finally:
        await stop_browser()

if __name__ == "__main__":
    print(">>> __main__ guard executing", flush=True)
    asyncio.run(run())
