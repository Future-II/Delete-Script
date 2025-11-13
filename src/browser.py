#browser.py
import os
from urllib.parse import urlparse
import nodriver as uc
from .config import PROFILE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT
from .utils import log

_browser = None

def _is_valid_http_url(url: str) -> bool:
    try:
        parts = urlparse(url)
        return parts.scheme in ("http", "https") and bool(parts.netloc)
    except Exception:
        return False

async def get_browser():
    global _browser
    if _browser is None:
        os.makedirs(PROFILE_DIR, exist_ok=True)
        _browser = await uc.start(
            headless=False,
            window_size=(WINDOW_WIDTH, WINDOW_HEIGHT),
            startup_args=[
                f"--user-data-dir={os.path.abspath(PROFILE_DIR)}",
                "--disable-blink-features=AutomationControlled",
            ],
        )
    return _browser

async def navigate(url: str):
    def _sanitize(u: str) -> str:
        return (u or "").strip().strip('"\\' + "'")

    url = _sanitize(url)
    browser = await get_browser()

    if not _is_valid_http_url(url):
        log(f"Invalid URL -> '{url}'", "ERR")
        page = await browser.new_page()
        return page

    # Try once, then restart browser and retry once more if transport fails
    for attempt in range(2):
        try:
            return await browser.get(url)
        except Exception as e:
            log(f"browser.get() failed (try {attempt+1}/2): {e}", "WARN")
            try:
                page = await browser.new_page()
                await page.evaluate("url => { window.location.href = url; }", url)
                return page
            except Exception as e2:
                log(f"fallback window.location failed: {e2}", "WARN")
                if attempt == 0:
                    # restart browser and retry
                    try:
                        await stop_browser()
                    except Exception:
                        pass
                    # get_browser() will recreate
                    browser = await get_browser()
                else:
                    # give up with a blank page
                    try:
                        return await browser.new_page()
                    except Exception:
                        raise

async def new_window(url: str | None = None):
    if url:
        return await navigate(url)
    browser = await get_browser()
    return await browser.new_page()

# browser.py
async def stop_browser():
    global _browser
    # snapshot, then null-out to avoid races
    b = _browser
    _browser = None
    if b is not None:
        try:
            await b.stop()
        except Exception as e:
            log(f"Error stopping browser: {e}", "ERR")

