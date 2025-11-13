# src/report_macro.py
import asyncio
from .utils import log, wait_for_element
from .browser import new_window
from .report_info import extract_report_info
from .pagination import go_to_last_asset_page
from .config import OFFICE_ID  # if you need it elsewhere
from .asset_delete import delete_latest_asset


MACROS_INPUT_SEL = "#macros"
SAVE_BTN_SEL = "input.btn.btn-primary.btn-lg.mt-2[type='submit'][value='Save']"

CANCELLED_VALUES = {"ملغى", "ملغي", "Canceled", "Cancelled"}

async def _set_macros_to_one(page) -> bool:
    try:
        ok = await page.evaluate("""
            (() => {
              const el = document.querySelector('#macros');
              if (!el) return false;
              el.removeAttribute('readonly');
              el.removeAttribute('disabled');
              el.value = 1;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
              return true;
            })()
        """)
        return bool(ok)
    except Exception as e:
        log(f"Failed to set macros via JS: {e}", "WARN")
        return False

async def _click_save(page) -> bool:
    # Try the standard English button first
    btn = await wait_for_element(page, SAVE_BTN_SEL, timeout=12)
    if btn:
        try:
            await btn.click()
            return True
        except Exception as e:
            log(f"Primary Save click failed: {e}", "WARN")

    # ✅ Fallbacks: support both English and Arabic save buttons
    try:
        ok = await page.evaluate("""
            (() => {
              const texts = ["Save", "حفظ"];
              // Match <input type=submit value=...> or <button>text</button>
              const candidates = Array.from(
                document.querySelectorAll('input[type=submit], button')
              );
              for (const el of candidates) {
                const v = (el.value || el.textContent || '').trim();
                if (texts.some(t => v.includes(t))) {
                  el.click();
                  return true;
                }
              }
              return false;
            })()
        """)
        if ok:
            log("Clicked Arabic/English Save button successfully.", "OK")
            return True
    except Exception as e:
        log(f"Fallback Arabic/English Save click failed: {e}", "ERR")
        return False

    log("No Save button found (English or Arabic).", "ERR")
    return False



async def _create_single_macro(report_id: str) -> bool:
    """
    Create exactly 1 macro for the given report, click Save (English/Arabic),
    then navigate to the last page (and last DataTable subpage, if any)
    so the newly created asset is visible for follow-up actions.
    """
    create_url = f"https://qima.taqeem.sa/report/asset/create/{report_id}"
    log(f"Navigating to asset-create page: {create_url}", "STEP")
    page = await new_window(create_url)
    await asyncio.sleep(1.5)

    # Wait for the "Number of Macros" input
    macros_input = await wait_for_element(page, MACROS_INPUT_SEL, timeout=25)
    if not macros_input:
        log("Could not find Number of Macros input (#macros).", "ERR")
        return False

    # Set macros=1
    if not await _set_macros_to_one(page):
        log("Failed to set Number of Macros to 1.", "ERR")
        return False

    # Click Save (supports English 'Save' and Arabic 'حفظ')
    if not await _click_save(page):
        log("Save button not found/click failed on asset-create page.", "ERR")
        return False

    log("Clicked Save to create 1 macro.", "OK")
    await asyncio.sleep(1.0)

    # After save, move to the last available page(s) where the new asset appears
    try:
        # requires: from .pagination import go_to_last_asset_page
        await go_to_last_asset_page(report_id, page)
    except Exception as e:
        log(f"Pagination to last asset page failed: {e}", "WARN")

   # 🔥 NEW: delete the last (newest) asset
    try:
        ok_del = await delete_latest_asset(report_id, page)
        if ok_del:
            log("Newest asset deleted successfully.", "OK")
        else:
            log("Failed to delete newest asset.", "ERR")
    except Exception as e:
        log(f"Delete latest asset errored: {e}", "ERR")

    return True


async def check_status_and_create_macro_if_cancelled(report_id: str, report_page) -> bool:
    await asyncio.sleep(1.2)  # let DOM render

    info = await extract_report_info(report_page)
    if not info.get("found"):
        log(f"Report {report_id}: report details not found.", "ERR")
        return False

    alias = info.get("alias") or {}
    status_val = (alias.get("status") or {}).get("value") or ""
    log(f"Report {report_id} status = {status_val!r}", "INFO")

    if status_val in CANCELLED_VALUES:
        log(f"Report {report_id} is cancelled ({status_val}) → creating 1 macro.", "STEP")
        ok = await _create_single_macro(report_id)
        if ok:
            log(f"Report {report_id}: macro creation flow finished.", "OK")
        else:
            log(f"Report {report_id}: macro creation flow failed.", "ERR")
        return ok

    log(f"Report {report_id} is not cancelled — no macro creation.", "INFO")
    return False
