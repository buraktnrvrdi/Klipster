"""Basit e-posta gonderme yardimcisi. SMTP bilgileri (.env dosyasinda) tanimli
degilse e-postayi gerceten gondermez, bunun yerine icerigi konsola/loglara
yazar - boylece SMTP_HOST/SMTP_USER/SMTP_PASS eklenene kadar da gelistirme
sirasinda linkler terminalden okunup test edilebilir.

Gercek e-posta gondermek icin backend/.env dosyasina sunlari ekle:
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=seninadresin@gmail.com
  SMTP_PASS=uygulama-sifresi   (Gmail icin normal sifre degil, "uygulama sifresi")
  FROM_EMAIL=seninadresin@gmail.com
Gmail disinda Resend, SendGrid gibi servislerin de SMTP arayuzu var, ayni
degiskenlerle calisir.
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText

from dotenv import load_dotenv

# Bu modul main.py'daki load_dotenv() cagrisindan ONCE import edilebiliyor
# (import sirasi degisirse tekrar bozulmasin diye), o yuzden .env'i burada
# da kendi basina yukluyoruz - zaten yuklenmisse bu ikinci cagri zararsiz.
load_dotenv()

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
FROM_EMAIL = os.environ.get("FROM_EMAIL") or SMTP_USER or "noreply@klipster.app"

EMAIL_CONFIGURED = bool(SMTP_HOST and SMTP_USER and SMTP_PASS)


def send_email(to: str, subject: str, body: str) -> bool:
    """E-postayi gondermeyi dener. Basarili olursa True, SMTP tanimli degilse
    veya gonderim basarisiz olursa False dondurur (cagiran taraf bu durumda
    kullaniciyi engellememeli - ör. kayit islemi e-posta gonderilemese bile
    tamamlanmali)."""
    if not EMAIL_CONFIGURED:
        print(f"[e-posta devre disi - SMTP tanimli degil] Kime: {to}\nKonu: {subject}\n{body}\n")
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, [to], msg.as_string())
        return True
    except Exception as e:
        print(f"[e-posta gonderim hatasi] {to}: {e}")
        return False
