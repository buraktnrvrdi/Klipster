"""Auth akislari (kayit -> e-posta dogrulama -> giris) ve rate limiting
icin uctan uca API testleri. Daha once bu 1600+ satirlik main.py icin
hic endpoint testi yoktu. conftest.py, gercek gelistirme veritabanina
dokunulmamasi icin bagimsiz bir gecici SQLite dosyasi ayarliyor."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.main as main  # noqa: E402
from app.db import get_conn  # noqa: E402


@pytest.fixture(autouse=True)
def _no_real_email(monkeypatch):
    """Gercek SMTP'ye hicbir zaman dokunma - .env'de SMTP bilgisi tanimli
    olsa bile testler sirasinda e-posta gonderilmesini engeller."""
    monkeypatch.setattr(main, "send_email", lambda *a, **kw: True)


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Testler arasi rate limit sayaclarinin sizmasini (bir testin digerini
    429'a dusurmesini) onlemek icin her testten once temizle."""
    main._rate_limiter._hits.clear()


@pytest.fixture
def client():
    return TestClient(main.app)


def _latest_verification_token(email: str) -> str:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT ev.token FROM email_verifications ev
            JOIN users u ON u.id = ev.user_id
            WHERE u.email = ?
            ORDER BY ev.created_at DESC LIMIT 1
            """,
            (email,),
        ).fetchone()
    assert row is not None
    return row["token"]


def test_register_then_login_requires_email_verification(client):
    email = "test-auth-1@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "sifre123"})
    assert r.status_code == 200

    r = client.post("/api/auth/login", json={"email": email, "password": "sifre123"})
    assert r.status_code == 403


def test_register_verify_and_login_flow(client):
    email = "test-auth-2@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "sifre123"})
    assert r.status_code == 200

    token = _latest_verification_token(email)
    r = client.post("/api/auth/verify-email", json={"token": token})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    r = client.post("/api/auth/login", json={"email": email, "password": "sifre123"})
    assert r.status_code == 200
    session_token = r.json()["token"]

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {session_token}"})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == email


def test_register_rejects_invalid_email(client):
    r = client.post("/api/auth/register", json={"email": "not-an-email", "password": "sifre123"})
    assert r.status_code == 400


def test_register_rejects_short_password(client):
    r = client.post("/api/auth/register", json={"email": "test-auth-3@example.com", "password": "123"})
    assert r.status_code == 400


def test_register_rejects_duplicate_email(client):
    email = "test-auth-4@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "sifre123"})
    r = client.post("/api/auth/register", json={"email": email, "password": "baskasifre"})
    assert r.status_code == 409


def test_login_wrong_password_rejected(client):
    email = "test-auth-5@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "sifre123"})
    r = client.post("/api/auth/login", json={"email": email, "password": "yanlissifre"})
    assert r.status_code == 401


def test_forgot_password_does_not_leak_whether_email_exists(client):
    r1 = client.post("/api/auth/forgot-password", json={"email": "yok-boyle-biri@example.com"})
    r2 = client.post("/api/auth/forgot-password", json={"email": "test-auth-2@example.com"})
    assert r1.status_code == r2.status_code == 200
    assert r1.json()["message"] == r2.json()["message"]


def test_verify_email_rejects_unknown_token(client):
    r = client.post("/api/auth/verify-email", json={"token": "gecersiz-token"})
    assert r.status_code == 404


def test_login_rate_limit_blocks_after_threshold(client):
    email = "test-auth-ratelimit@example.com"
    for _ in range(10):
        client.post("/api/auth/login", json={"email": email, "password": "yanlis"})
    r = client.post("/api/auth/login", json={"email": email, "password": "yanlis"})
    assert r.status_code == 429
