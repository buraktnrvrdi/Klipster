"""E-posta gonderme yardimcisi. Resend HTTP API kullanir (SMTP yerine) -
Railway SMTP portlarini bloke ettigi icin HTTP API tek calisma yontemi.

RESEND_API_KEY env var'i tanimli degilse e-postayi gercekten gondermez,
icerigi loglara yazar - gelistirme sirasinda linkler terminalden okunabilir.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")

EMAIL_CONFIGURED = bool(RESEND_API_KEY)


def send_email(to: str, subject: str, body: str) -> bool:
    if not EMAIL_CONFIGURED:
        print(f"[e-posta devre disi - RESEND_API_KEY tanimli degil] Kime: {to}\nKonu: {subject}\n{body}\n")
        return False

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": FROM_EMAIL, "to": [to], "subject": subject, "text": body},
            timeout=10,
        )
        if resp.status_code >= 400:
            print(f"[e-posta gonderim hatasi] {to}: {resp.status_code} {resp.text}")
            return False
        return True
    except Exception as e:
        print(f"[e-posta gonderim hatasi] {to}: {e}")
        return False
