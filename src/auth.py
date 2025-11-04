
import asyncio
from .config import START_URL, LOGIN_TIMEOUT_SECONDS, OTP_TIMEOUT_SECONDS
from .utils import wait_for_element, log
from .browser import new_window

USERNAME = "input#username"
PASSWORD = "input#password"
LOGIN_BTN = "input#kc-login.login-btn"
OTP_INPUT = "input#emailCode"
OTP_SEND_BTN = "input[name='login'].login-btn"

async def login_flow(username: str, password: str) -> bool:
    target = (START_URL or "").strip().strip('"\\' + "'")
    log(f"Opening SSO login page (raw): {START_URL}", "INFO")
    log(f"Opening SSO login page (clean): {target}", "STEP")
    page = await new_window(target)

    # Fill username
    log("Waiting for username field...")
    user_el = await wait_for_element(page, USERNAME, timeout=LOGIN_TIMEOUT_SECONDS)
    if not user_el:
        log("Username field not found. If a security/MFA page is shown, complete it manually and retry.", "ERR")
        return False
    await user_el.send_keys(username)

    # Fill password
    pass_el = await wait_for_element(page, PASSWORD, timeout=10)
    if not pass_el:
        log("Password field not found.", "ERR")
        return False
    await pass_el.send_keys(password)

    # Click Sign In
    login_btn = await wait_for_element(page, LOGIN_BTN, timeout=10)
    if not login_btn:
        log("Sign In button not found.", "ERR")
        return False
    await login_btn.click()

    # OTP screen
    log("Waiting for OTP screen...")
    otp_el = await wait_for_element(page, OTP_INPUT, timeout=OTP_TIMEOUT_SECONDS)
    if not otp_el:
        log("OTP input not detected. If MFA/Cloudflare shows up, complete it manually, then re-run.", "ERR")
        return False

    otp = input("Enter the OTP (email code) shown on the page: ").strip()
    await otp_el.send_keys(otp)

    send_btn = await wait_for_element(page, OTP_SEND_BTN, timeout=10)
    if not send_btn:
        log("Send button not found on OTP screen.", "ERR")
        return False
    await send_btn.click()

    log("Submitted OTP. Waiting for redirect...", "OK")
    await asyncio.sleep(3)
    return True
