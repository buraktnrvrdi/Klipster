"""Sifre hash'leme, oturum (bearer token) olusturma ve dogrulama."""
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Header, HTTPException, Query

from app.db import get_conn

# Oturum token'lari bu sureden sonra gecersiz sayilir - "birisi linki ele
# gecirirse sonsuza kadar erisir" riskini sinirlar. Kullanici bu sure
# icinde tekrar giris yapmazsa yeniden sifresiyle giris yapmasi gerekir.
SESSION_TTL_DAYS = 30


def _lookup_user_by_token(token: str | None) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="Giris yapman gerekiyor")
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT users.id, users.email, users.plan, users.display_name, users.avatar,
                   users.email_verified, users.created_at, sessions.expires_at
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Oturum gecersiz, tekrar giris yap")
    row = dict(row)

    expires_at = row.pop("expires_at", None)
    if expires_at:
        try:
            expiry = datetime.fromisoformat(expires_at)
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
        except ValueError:
            expiry = None
        if expiry and datetime.now(timezone.utc) > expiry:
            with get_conn() as conn:
                conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
            raise HTTPException(status_code=401, detail="Oturum suresi doldu, tekrar giris yap")

    return row


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )
        conn.commit()
    return token


def invalidate_all_sessions(user_id: int) -> None:
    """Kullanicinin TUM oturumlarini iptal eder - sifre sifirlama sonrasi
    guvenlik icin: eger sifre calinmis ve baskasi oturum acmissa, sifre
    degistirilince o oturum da dusmeli."""
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.commit()


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Giris yapman gerekiyor")
    token = authorization.split(" ", 1)[1].strip()
    return _lookup_user_by_token(token)


def get_current_user_flexible(
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> dict:
    """get_current_user ile ayni, ama token'i Authorization basligi yaninda
    URL query parametresinden de kabul eder. Sadece <video>/<img> gibi
    ozel header ekleyemeyen taglerin src'sine token gecirebilmek icin
    (ör. orijinal videoyu kirpma editorunde onizlerken) kullanilir."""
    if authorization and authorization.lower().startswith("bearer "):
        return _lookup_user_by_token(authorization.split(" ", 1)[1].strip())
    return _lookup_user_by_token(token)
