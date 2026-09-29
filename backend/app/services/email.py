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

# E-posta govdesindeki logo her zaman gercek siteden yuklenmeli - alicinin
# posta istemcisi resmi kendi cihazindan cekiyor, yerel/gelistirme adresi
# (localhost) orada calismaz.
LOGO_URL = "https://klipster.com.tr/logo-v2.png"


def send_email(to: str, subject: str, body: str, html: str | None = None) -> bool:
    logger.info("[e-posta] API_KEY=%s FROM=%s TO=%s", bool(RESEND_API_KEY), FROM_EMAIL, to)
    if not EMAIL_CONFIGURED:
        logger.info("[e-posta devre disi] Kime: %s | Konu: %s\n%s", to, subject, body)
        return False

    payload = {"from": FROM_EMAIL, "to": [to], "subject": subject, "text": body}
    if html:
        payload["html"] = html

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json=payload,
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


def _shell(content_html: str) -> str:
    """Klipster marka temasiyla (siyah zemin, kirmizi vurgu) uyumlu, e-posta
    istemcileri arasinda genis uyumluluk icin tablo tabanli/satir-ici (inline)
    CSS kullanan bir HTML e-posta kabugu. Ic icerik (content_html) bu kabugun
    ortasindaki beyaz karta yerlestirilir."""
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Klipster</title>
</head>
<body style="margin:0;padding:0;background-color:#000000;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#000000;padding:40px 16px;">
<tr>
<td align="center">
<table role="presentation" width="100%" style="max-width:480px;" cellpadding="0" cellspacing="0">
<tr>
<td align="center" style="padding-bottom:32px;">
<img src="{LOGO_URL}" alt="Klipster" height="40" style="display:block;">
</td>
</tr>
<tr>
<td style="background-color:#0a0a0a;border:1px solid #27272a;border-radius:16px;padding:40px 32px;">
{content_html}
</td>
</tr>
<tr>
<td align="center" style="padding-top:32px;">
<p style="margin:0;color:#71717a;font-size:12px;line-height:1.6;">
Klipster &middot; <a href="https://klipster.com.tr" style="color:#71717a;">klipster.com.tr</a>
</p>
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>"""


def _button(label: str, url: str) -> str:
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" style="margin:28px auto 0;">
<tr>
<td align="center" style="background-color:#ef4444;border-radius:9999px;">
<a href="{url}" style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:15px;
font-weight:600;text-decoration:none;">{label}</a>
</td>
</tr>
</table>"""


def verification_code_html(code: str, ttl_hours: int) -> str:
    content = f"""
<h1 style="margin:0 0 12px;color:#ffffff;font-size:22px;font-weight:700;text-align:center;">
E-posta adresini doğrula
</h1>
<p style="margin:0 0 28px;color:#a1a1aa;font-size:15px;line-height:1.6;text-align:center;">
Klipster hesabını doğrulamak için aşağıdaki kodu kullan:
</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;">
<tr>
<td style="background-color:#000000;border:1px solid #3f3f46;border-radius:12px;padding:18px 28px;">
<span style="color:#ffffff;font-size:32px;font-weight:700;letter-spacing:8px;font-family:'Courier New',monospace;">{code}</span>
</td>
</tr>
</table>
<p style="margin:28px 0 0;color:#71717a;font-size:13px;line-height:1.6;text-align:center;">
Bu kod {ttl_hours} saat geçerlidir. Bu kodu sen istemediysen bu e-postayı yok sayabilirsin.
</p>"""
    return _shell(content)


def password_reset_html(link: str, ttl_minutes: int) -> str:
    content = f"""
<h1 style="margin:0 0 12px;color:#ffffff;font-size:22px;font-weight:700;text-align:center;">
Şifreni sıfırla
</h1>
<p style="margin:0 0 4px;color:#a1a1aa;font-size:15px;line-height:1.6;text-align:center;">
Şifreni sıfırlamak için aşağıdaki butona tıkla.
</p>
<p style="margin:0;color:#71717a;font-size:13px;line-height:1.6;text-align:center;">
Bu link {ttl_minutes} dakika geçerlidir.
</p>
{_button("Şifreni Sıfırla", link)}
<p style="margin:28px 0 0;color:#71717a;font-size:13px;line-height:1.6;text-align:center;">
Bu talebi sen yapmadıysan bu e-postayı yok sayabilirsin, şifren değişmez.
</p>"""
    return _shell(content)
