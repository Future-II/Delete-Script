#config.py

import os
import re
from dotenv import load_dotenv

load_dotenv()

_ZW = ''.join(['\u200b','\u200c','\u200d','\ufeff'])
_ZW_RE = re.compile('[%s]' % re.escape(_ZW))

def _clean(v: str | None, default: str = "") -> str:
    if v is None:
        return default
    v = v.strip().strip('\"\'')
    v = _ZW_RE.sub('', v)
    return v

START_URL = _clean(os.getenv("START_URL"), "https://sso.taqeem.gov.sa/realms/REL_TAQEEM/protocol/openid-connect/auth?client_id=cli-qima-valuers&redirect_uri=https%3A%2F%2Fqima.taqeem.sa%2Fkeycloak%2Flogin%2Fcallback&scope=openid&response_type=code&state=yWlonMo3FYQUti6DhYz054gbf9AiVGWUIvv89Q7g")
PROFILE_DIR = _clean(os.getenv("PROFILE_DIR"), "./qima-profile")
OFFICE_ID = _clean(os.getenv("OFFICE_ID"), "487")
LOGIN_TIMEOUT_SECONDS = int(_clean(os.getenv("LOGIN_TIMEOUT_SECONDS"), "60") or "60")
OTP_TIMEOUT_SECONDS = int(_clean(os.getenv("OTP_TIMEOUT_SECONDS"), "120") or "120")
WINDOW_WIDTH = int(_clean(os.getenv("WINDOW_WIDTH"), "1200") or "1200")
WINDOW_HEIGHT = int(_clean(os.getenv("WINDOW_HEIGHT"), "850") or "850")
