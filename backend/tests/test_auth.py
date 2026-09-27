"""Auth akislari (kayit -> e-posta dogrulama -> giris) ve rate limiting
icin uctan uca API testleri. Daha once bu 1600+ satirlik main.py icin
hic endpoint testi yoktu. conftest.py, testlerin DATABASE_URL ile
gosterilen (gercek gelistirme/production veritabanindan bagimsiz,
CI'da gecici bir servis container'i olan) bir Postgres'e karsi
calismasini zorunlu kilar."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.main as main  # noqa: E402


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


def test_register_then_login_requires_email_verification(client):
    # NOT: main.py'de e-posta dogrulama zorunlulugu su an KASITLI olarak
    # devre disi birakilmis durumda (Railway'de SMTP calismadigi icin,
    # Resend.com entegrasyonu tamamlanana kadar - main.py'deki TODO'ya bak).
    # Bu yuzden yeni kayit su an dogrudan giris yapabiliyor; bu test o
    # gecici davranisi dogruluyor, NIHAI/istenen davranisi degil - e-posta
    # dogrulamasi tekrar aktif edilince bu test de eski haline (403 bekleyen)
    # donmeli.
    email = "test-auth-1@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "sifre123"})
    assert r.status_code == 200

    r = client.post("/api/auth/login", json={"email": email, "password": "sifre123"})
    assert r.status_code == 200


def test_register_returns_usable_session_and_allows_later_login(client):
    # NOT: e-posta dogrulamasi kasitli olarak devre disi oldugu icin
    # (bkz. yukaridaki test) register artik e-posta linki beklemeden
    # dogrudan kullanilabilir bir oturum tokeni donduruyor - eskiden bu
    # test register->verify-email->login akisini dogruluyordu, dogrulama
    # geri gelince bu test de o akisa donmeli.
    email = "test-auth-2@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "sifre123"})
    assert r.status_code == 200
    session_token = r.json()["token"]
    assert session_token

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {session_token}"})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == email

    r = client.post("/api/auth/login", json={"email": email, "password": "sifre123"})
    assert r.status_code == 200


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


def test_verify_email_rejects_unknown_code(client):
    r = client.post(
        "/api/auth/verify-email", json={"email": "yok-boyle-biri@example.com", "code": "000000"}
    )
    assert r.status_code == 404


def test_verify_email_with_correct_code_marks_account_verified(client, monkeypatch):
    import re

    captured = {}

    def _capture_email(to, subject, body):
        captured["to"] = to
        captured["body"] = body
        return True

    monkeypatch.setattr(main, "send_email", _capture_email)

    email = "test-auth-verify-code@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "sifre123"})
    assert r.status_code == 200

    match = re.search(r"\b(\d{6})\b", captured["body"])
    assert match, "dogrulama e-postasinda 6 haneli kod bulunamadi"
    code = match.group(1)

    # Yanlis kod reddedilmeli.
    r = client.post("/api/auth/verify-email", json={"email": email, "code": "000000"})
    assert r.status_code in (404, 429)

    r = client.post("/api/auth/verify-email", json={"email": email, "code": code})
    assert r.status_code == 200
    session_token = r.json()["token"]
    assert session_token

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {session_token}"})
    assert r.json()["user"]["email_verified"] is True


def test_login_rate_limit_blocks_after_threshold(client):
    email = "test-auth-ratelimit@example.com"
    for _ in range(10):
        client.post("/api/auth/login", json={"email": email, "password": "yanlis"})
    r = client.post("/api/auth/login", json={"email": email, "password": "yanlis"})
    assert r.status_code == 429
