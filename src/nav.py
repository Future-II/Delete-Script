# nav.py
import asyncio
from .config import OFFICE_ID
from .browser import new_window
from .utils import log

async def open_report_by_id(report_id: str):
    report_id = report_id.strip()
    url = f"https://qima.taqeem.sa/report/{report_id}?office={OFFICE_ID}"
    log(f"Opening report: {url}", "STEP")
    page = await new_window(url)
    await asyncio.sleep(1.0)
    return page
