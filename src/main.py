# main.py

import asyncio
import getpass
import json
import os

from src.auth import login_flow
from src.nav import open_report_by_id
from src.utils import log
from src.browser import stop_browser, new_window
from src.report_actions import try_delete_report, delete_incomplete_assets_across_pages
from src.asset_edit import edit_macro_and_save
from src.config import OFFICE_ID

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "asset_template.json")


def _load_template():
    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Could not load template {TEMPLATE_PATH}: {e}", "ERR")
        return {}


async def handle_reports_input():
    """
    Prompt the user to enter one or more report IDs (paste supported).
    The user may input a single ID or multiple IDs separated by commas, spaces,
    semicolons or newlines. Enter Q to quit.
    Processes each report ID sequentially.
    Returns False if the user chose to quit or cancelled input, True otherwise.
    """
    try:
        raw = input(
            "Enter one or more Report ID(s) (separate with spaces/commas or paste multiple lines), or Q to quit: "
        )
    except (EOFError, KeyboardInterrupt):
        log("Input cancelled. Quitting.", "INFO")
        return False

    if not raw:
        return True  # allow another loop iteration

    import re as _re
    parts = [p.strip() for p in _re.split(r"[\s,;]+", raw) if p.strip()]
    if any(p.lower() in ("q", "quit", "exit") for p in parts):
        return False

    for report_id in parts:
        log(f"Processing report {report_id}", "STEP")
        try:
            page = await open_report_by_id(report_id)

            # 1) Try full report delete first (if button appears)
            if await try_delete_report(page):
                log(f"Report {report_id}: deletion attempted.", "OK")
                continue

            # 2) Otherwise prune incomplete assets across ALL main pages & subpages
            summary = await delete_incomplete_assets_across_pages(page)
            log(f"Report {report_id}: pagination summary -> {summary}", "OK")

            total_deleted = int(summary.get("total_deleted") or 0)
            kept_nested = summary.get("kept_by_main_page") or []
            kept_flat = [kid for sub in kept_nested for kid in (sub or []) if kid]
            kept_first = kept_flat[0] if kept_flat else None

            if total_deleted == 0 and kept_first:
                # Heuristic: no deletions anywhere and we kept at least one -> likely all-incomplete case.
                log(f"Report {report_id}: no deletions; completing kept macro {kept_first}…", "INFO")
                values = _load_template()
                ok = await edit_macro_and_save(kept_first, values)
                log(f"Edited macro {kept_first} save ok={ok}", "INFO")

                # Re-open the report and try Delete again
                url = f"https://qima.taqeem.sa/report/{report_id}?office={OFFICE_ID}"
                log(f"Re-opening report to check Delete button: {url}", "STEP")
                page2 = await new_window(url)
                await asyncio.sleep(1.0)
                did_delete2 = await try_delete_report(page2)
                if did_delete2:
                    log(f"Report {report_id}: deletion attempted after completing one asset.", "OK")
                else:
                    log(f"Report {report_id}: Delete Report button still not present after completing one asset.", "INFO")
            else:
                # Partial cleanup (some complete assets exist or we deleted some incompletes)
                log(f"Report {report_id}: Deleted {total_deleted} incomplete asset(s). Checking for Delete Report button…", "INFO")
                url = f"https://qima.taqeem.sa/report/{report_id}?office={OFFICE_ID}"
                page2 = await new_window(url)
                await asyncio.sleep(1.0)
                if await try_delete_report(page2):
                    log(f"Report {report_id}: deletion attempted after partial cleanup.", "OK")
                else:
                    log(f"Report {report_id}: Delete Report button still not present after partial cleanup.", "INFO")

        except Exception as e:
            log(f"Error while processing report {report_id}: {e}", "ERR")

    return True


async def run():
    log("=== Taqeem: Login + OTP + Prune + Complete + Delete (Nodriver) ===")

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
    asyncio.run(run())
