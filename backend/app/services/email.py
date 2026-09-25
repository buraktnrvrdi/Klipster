"""E-posta gonderme yardimcisi. Resend HTTP API kullanir (SMTP yerine) -
Railway SMTP portlarini bloke ettigi icin HTTP API tek calisma yontemi.

RESEND_API_KEY env var'i tanimli degilse e-postayi gercekten gondermez,
icerigi loglara yazar - gelistirme sirasinda linkler terminalden okunabilir.
"""
import logging
import os

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")

EMAIL_CONFIGURED = bool(RESEND_API_KEY)


def send_email(to: str, subject: str, body: str) -> bool:
    logger.info("[e-posta] API_KEY=%s FROM=%s TO=%s", bool(RESEND_API_KEY), FROM_EMAIL, to)
    if not EMAIL_CONFIGURED:
        logger.info("[e-posta devre disi] Kime: %s | Konu: %s\n%s", to, subject, body)
        return False

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": FROM_EMAIL, "to": [to], "subject": subject, "text": body},
            timeout=10,
        )
        logger.info("[e-posta sonuc] %s: %s %s", to, resp.status_code, resp.text[:200])
        if resp.status_code >= 400:
            logger.error("[e-posta gonderim hatasi] %s: %s %s", to, resp.status_code, resp.text)
            return False
        return True
    except Exception as e:
        logger.error("[e-posta gonderim hatasi] %s: %s", to, e)
        return False
