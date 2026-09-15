"""Icerik yeniden uretim API'si: kullanici kaydi/girisi, kullanim limiti,
video yukle -> transkript cikar -> viral anlari bul -> dikey altyazili klipler uret."""
import json
import os
import re
import secrets
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

# .env dosyasi, asagidaki app.* importlarindan ONCE yuklenmeli - yoksa
# app.services.email gibi import aninda ortam degiskeni okuyan modüller
# SMTP bilgilerini hicbir zaman goremez (bu tam olarak yasanan hataydi).
load_dotenv()

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.auth import (
    create_session,
    get_current_user,
    get_current_user_flexible,
    hash_password,
    invalidate_all_sessions,
    verify_password,
)
from app.db import AVATAR_OPTIONS, CUSTOMIZABLE_CLIP_PLANS, get_conn, init_db
from app.services.credits import (
    CREDIT_COST_BASE,
    CREDIT_COST_PER_CLIP,
    CREDIT_LIMITS,
    compute_added_clip_cost,
    compute_credit_cost,
)
from app.services.email import send_email
from app.services.highlights import (
    find_highlights,
    generate_social_caption,
    translate_subtitles,
    translate_to_english,
)
from app.services.transcribe import transcribe
from app.services.video import (
    ASPECT_PRESETS,
    DEFAULT_ASPECT,
    DEFAULT_STYLE,
    DEFAULT_SUBTITLE_COLOR,
    DEFAULT_SUBTITLE_POSITION,
    STYLE_PRESETS,
    SUBTITLE_COLOR_PRESETS,
    SUBTITLE_POSITIONS,
    build_keep_intervals,
    chunk_words,
    get_video_duration,
    make_cover,
    make_vertical_clip,
    remap_words,
    write_srt,
)

# E-postalardaki linklerin (dogrulama, sifre sifirlama, ekip daveti) hangi
# alan adina gidecegini belirler - .env dosyasina FRONTEND_URL eklenmezse
# yerel gelistirme adresi varsayilir.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")

# Sifre sifirlama linki bu sure sonra gecersiz olur.
PASSWORD_RESET_TTL_MINUTES = 60

# CORS: API'ye sadece bilinen frontend adreslerinden istek atilabilir - "*"
# (herkese acik) production'da guvenlik acigi olusturur, herhangi bir site
# kullanicinin tarayicisi uzerinden bu API'ye istek atabilirdi. Birden fazla
# adres gerekiyorsa (ör. www'li/www'siz veya bir staging adresi) .env'e
# ALLOWED_ORIGINS'e virgulle ayirarak ekle. Yerel gelistirme adresleri
# (localhost:3000, 127.0.0.1:3000) FRONTEND_URL farkli bir sey olsa bile
# gelistirme kolayligi icin her zaman listeye dahil edilir.
_extra_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
ALLOWED_ORIGINS = list(dict.fromkeys(
    [FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000", *_extra_origins]
))

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
OUTPUT_DIR = BASE_DIR / "storage" / "outputs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

init_db()


def _recover_interrupted_jobs():
    """Sunucu (deploy/yeniden baslatma/cokme yuzunden) bir video islenirken
    kapanirsa, o is veritabaninda sonsuza kadar 'queued'/'transcribing'/...
    durumunda takili kalirdi - kullanici sanki hala isleniyormus gibi
    gorurdu ve o isin kredisi de hicbir zaman "basarisiz" sayilip iade
    edilmezdi. Uygulama her acildiginda, bitmemis (done/error disi) tum
    isleri acikca hataya cevirerek bu durumu temizliyoruz."""
    with get_conn() as conn:
        updated = conn.execute(
            """
            UPDATE jobs SET status = 'error',
                error = 'Sunucu yeniden baslatildigi icin bu islem yarida kaldi - lutfen videoyu tekrar yukle'
            WHERE status NOT IN ('done', 'error')
            """
        )
        conn.commit()
        if updated.rowcount:
            print(f"[baslangic temizligi] {updated.rowcount} yarim kalan is hataya cevrildi")


_recover_interrupted_jobs()

app = FastAPI(title="Content Repurposer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.mount("/files", StaticFiles(directory=str(OUTPUT_DIR)), name="files")


@app.get("/healthz")
async def healthz():
    """Railway gibi platformlarin dagitim sonrasi 'uygulama gercekten ayakta
    mi' kontrolu icin kullandigi, kimlik dogrulama gerektirmeyen uc nokta."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Otomatik uretilen Ingilizce altyazinin (her klipte varsayilan olarak
# uretiliyor) disinda, kullanicinin talep uzerine ekstra olarak
# isteyebilecegi ceviri dilleri - /api/jobs/{id}/clips/{i}/translate.
SUBTITLE_LANGUAGES = {
    "en": "İngilizce",
    "es": "İspanyolca",
    "de": "Almanca",
    "fr": "Fransızca",
    "ar": "Arapça",
    "ru": "Rusça",
    "pt": "Portekizce",
    "it": "İtalyanca",
}


def _validate_render_options(
    subtitle_color: str | None, subtitle_position: str | None, aspect: str | None
) -> tuple[str, str, str]:
    """Altyazi rengi/konumu ve en-boy orani kullanici girdisini dogrular,
    gecersiz/eksik deger gelirse sessizce varsayilana duser."""
    color = subtitle_color if subtitle_color and HEX_COLOR_RE.match(subtitle_color) else DEFAULT_SUBTITLE_COLOR
    position = subtitle_position if subtitle_position in SUBTITLE_POSITIONS else DEFAULT_SUBTITLE_POSITION
    asp = aspect if aspect in ASPECT_PRESETS else DEFAULT_ASPECT
    return color, position, asp


def _resolve_clip_option(payload_value, is_valid, existing: dict, existing_key: str, row: dict, row_key: str, default):
    """Klip duzenleme/ekleme (mini editor) icin genel deger cozumleme sirasi:
    1) istekte gecerli bir deger gonderildiyse onu kullan,
    2) yoksa klibin kendi (daha once kaydedilmis) degerini kullan,
    3) o da yoksa isin (job) varsayilanini kullan,
    4) o da yoksa sabit varsayilana dus."""
    if payload_value is not None and is_valid(payload_value):
        return payload_value
    if existing.get(existing_key):
        return existing[existing_key]
    return row.get(row_key) or default


class AuthPayload(BaseModel):
    email: str
    password: str


class ProfilePayload(BaseModel):
    display_name: str | None = None
    avatar: str | None = None


class RetrimPayload(BaseModel):
    start: float
    end: float
    style: str | None = None
    remove_fillers: bool | None = None
    subtitle_color: str | None = None
    subtitle_position: str | None = None
    aspect: str | None = None


class AddClipPayload(BaseModel):
    """Kullanicinin orijinal video uzerinde elle sectigi bir araliktan
    yeni (AI'nin onermedigi) bir klip olusturmak icin gonderdigi veri."""
    start: float
    end: float
    title: str | None = None
    style: str | None = None
    remove_fillers: bool | None = None
    subtitle_color: str | None = None
    subtitle_position: str | None = None
    aspect: str | None = None


class TranslateClipPayload(BaseModel):
    language: str


class PasswordPayload(BaseModel):
    current_password: str
    new_password: str


class OrgPayload(BaseModel):
    name: str


class InvitePayload(BaseModel):
    email: str


class AcceptInvitePayload(BaseModel):
    token: str


class ForgotPasswordPayload(BaseModel):
    email: str


class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str


class VerifyEmailPayload(BaseModel):
    token: str


def _user_public(row: dict) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "plan": row["plan"],
        "display_name": row.get("display_name"),
        "avatar": row.get("avatar"),
        "email_verified": bool(row.get("email_verified")),
    }


def _send_verification_email(user_id: int, email: str) -> None:
    token = secrets.token_urlsafe(32)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO email_verifications (token, user_id) VALUES (?, ?)", (token, user_id)
        )
        conn.commit()
    link = f"{FRONTEND_URL}/email-dogrula?token={token}"
    send_email(
        email,
        "Klipster - E-posta adresini doğrula",
        f"Merhaba,\n\nKlipster hesabını doğrulamak için aşağıdaki linke tıkla:\n{link}\n\n"
        f"Bu linki sen istemediysen bu e-postayı yok sayabilirsin.",
    )


def _get_user_org(user_id: int) -> dict | None:
    """Kullanicinin uyesi oldugu ekibi (varsa) rolüyle birlikte dondurur."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT organizations.id, organizations.name, organizations.owner_id, org_members.role
            FROM org_members
            JOIN organizations ON organizations.id = org_members.org_id
            WHERE org_members.user_id = ?
            """,
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def _effective_plan(current_user: dict, org: dict | None) -> str:
    """Bir ekibe uyeyse, kredi/ozellik haklari ekip sahibinin planindan
    miras alinir (paylasilan havuz mantigi) - degilse kisinin kendi plani gecerlidir."""
    if not org:
        return current_user["plan"]
    with get_conn() as conn:
        row = conn.execute("SELECT plan FROM users WHERE id = ?", (org["owner_id"],)).fetchone()
    return row["plan"] if row else current_user["plan"]


def _job_scope(current_user: dict, org: dict | None) -> tuple[str, tuple]:
    """Bir kullanicinin gorebilecegi islerin SQL WHERE kosulu ve parametreleri -
    bir ekipteyse ekibin TUM isleri, degilse sadece kendi isleri gorunur."""
    if org:
        return "org_id = ?", (org["id"],)
    return "user_id = ? AND org_id IS NULL", (current_user["id"],)


def _credits_used_this_month(current_user: dict, org: dict | None) -> int:
    """Bu ay tuketilen toplam kredi (ekip halindeyse ekibin toplami). Hatali
    (status='error') isler dahil edilmez - basarisiz bir islem icin kredi
    'iade edilmis' olur."""
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"""
            SELECT COALESCE(SUM(credit_cost), 0) as c FROM jobs
            WHERE {scope_sql} AND status != 'error'
              AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            """,
            scope_params,
        ).fetchone()
    return row["c"] if row else 0


@app.post("/api/auth/register")
async def register(payload: AuthPayload):
    email = payload.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Geçerli bir e-posta gir")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalı")

    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı")
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, plan) VALUES (?, ?, 'ucretsiz')",
            (email, hash_password(payload.password)),
        )
        conn.commit()
        user_id = cur.lastrowid

    # Kayit olur olmaz oturum acilmiyor - hesap ancak e-posta dogrulandiktan
    # sonra kullanilabilir hale gelir (bkz. verify_email, orada oturum acilir).
    _send_verification_email(user_id, email)

    return {
        "ok": True,
        "email": email,
        "message": "Hesabını doğrulamak için e-postana gönderdiğimiz bağlantıya tıkla",
    }


@app.post("/api/auth/login")
async def login(payload: AuthPayload):
    email = payload.email.strip().lower()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı")
    if not row["email_verified"]:
        raise HTTPException(
            status_code=403,
            detail="Hesabını henüz doğrulamadın - e-postana gönderdiğimiz bağlantıya tıklaman gerekiyor",
        )

    token = create_session(row["id"])
    return {"token": token, "user": _user_public(dict(row))}


@app.get("/api/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    org = _get_user_org(current_user["id"])
    effective_plan = _effective_plan(current_user, org)
    used = _credits_used_this_month(current_user, org)
    limit = CREDIT_LIMITS.get(effective_plan, CREDIT_LIMITS["ucretsiz"])
    return {
        "user": _user_public(current_user),
        "usage": {"used": used, "limit": limit, "unit": "kredi"},
        "effective_plan": effective_plan,
        "org": {"id": org["id"], "name": org["name"], "role": org["role"]} if org else None,
    }


@app.get("/api/avatars")
async def avatars():
    return AVATAR_OPTIONS


@app.patch("/api/auth/profile")
async def update_profile(payload: ProfilePayload, current_user: dict = Depends(get_current_user)):
    fields = {}
    if payload.display_name is not None:
        name = payload.display_name.strip()
        if len(name) > 24:
            raise HTTPException(status_code=400, detail="İsim en fazla 24 karakter olabilir")
        fields["display_name"] = name or None
    if payload.avatar is not None:
        if payload.avatar not in AVATAR_OPTIONS:
            raise HTTPException(status_code=400, detail="Geçersiz avatar seçimi")
        fields["avatar"] = payload.avatar

    if not fields:
        raise HTTPException(status_code=400, detail="Güncellenecek bir alan yok")

    keys = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [current_user["id"]]
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {keys} WHERE id = ?", values)
        conn.commit()
        row = dict(conn.execute("SELECT * FROM users WHERE id = ?", (current_user["id"],)).fetchone())

    return {"user": _user_public(row)}


@app.post("/api/auth/change-password")
async def change_password(payload: PasswordPayload, current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (current_user["id"],)
        ).fetchone()
    if not row or not verify_password(payload.current_password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Mevcut şifre yanlış")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalı")

    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(payload.new_password), current_user["id"]),
        )
        conn.commit()

    return {"ok": True}


@app.post("/api/auth/resend-verification")
async def resend_verification(current_user: dict = Depends(get_current_user)):
    if current_user.get("email_verified"):
        return {"ok": True, "already_verified": True}
    _send_verification_email(current_user["id"], current_user["email"])
    return {"ok": True}


@app.post("/api/auth/verify-email")
async def verify_email(payload: VerifyEmailPayload):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT user_id FROM email_verifications WHERE token = ?", (payload.token,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Doğrulama linki geçersiz veya süresi dolmuş")
        user_id = row["user_id"]
        conn.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (user_id,))
        conn.execute("DELETE FROM email_verifications WHERE token = ?", (payload.token,))
        conn.commit()
        user_row = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

    # Dogrulama linkine tiklamak, kayit sirasinda hic acilmamis olan oturumu
    # burada acar - kullanici boylece tekrar giris yapmadan direkt icer girer.
    session_token = create_session(user_id)
    return {"ok": True, "token": session_token, "user": _user_public(user_row)}


@app.post("/api/auth/resend-verification-public")
async def resend_verification_public(payload: ForgotPasswordPayload):
    """Henuz giris yapamayan (dolayisiyla authed resend-verification'i
    cagiramayan) kullanicilar icin - forgot-password ile ayni enumeration
    onlemini kullanir: e-posta kayitli olsun olmasin ayni cevap doner."""
    email = payload.email.strip().lower()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email_verified FROM users WHERE email = ?", (email,)
        ).fetchone()
        if row and not row["email_verified"]:
            _send_verification_email(row["id"], email)

    return {
        "ok": True,
        "message": "Eğer bu e-posta kayıtlıysa ve henüz doğrulanmadıysa, yeni bir doğrulama linki gönderildi",
    }


@app.post("/api/auth/forgot-password")
async def forgot_password(payload: ForgotPasswordPayload):
    """Kayitli e-posta olsun olmasin ayni cevabi doner - boylece bir e-postanin
    sistemde kayitli olup olmadigi disaridan anlasilamaz (enumeration onlemi)."""
    email = payload.email.strip().lower()
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO password_resets (token, user_id) VALUES (?, ?)", (token, row["id"])
            )
            conn.commit()
            link = f"{FRONTEND_URL}/sifre-sifirla?token={token}"
            send_email(
                email,
                "Klipster - Şifreni sıfırla",
                f"Merhaba,\n\nŞifreni sıfırlamak için aşağıdaki linke tıkla (bu link "
                f"{PASSWORD_RESET_TTL_MINUTES} dakika geçerlidir):\n{link}\n\n"
                f"Bu talebi sen yapmadıysan bu e-postayı yok sayabilirsin, şifren değişmez.",
            )

    return {
        "ok": True,
        "message": "Eğer bu e-posta kayıtlıysa, şifre sıfırlama linki gönderildi",
    }


@app.post("/api/auth/reset-password")
async def reset_password(payload: ResetPasswordPayload):
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalı")

    with get_conn() as conn:
        row = conn.execute(
            "SELECT user_id, used, created_at FROM password_resets WHERE token = ?",
            (payload.token,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sıfırlama linki geçersiz")
    if row["used"]:
        raise HTTPException(status_code=409, detail="Bu sıfırlama linki zaten kullanılmış")

    created_at = datetime.fromisoformat(row["created_at"]).replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - created_at > timedelta(minutes=PASSWORD_RESET_TTL_MINUTES):
        raise HTTPException(status_code=410, detail="Sıfırlama linkinin süresi dolmuş, tekrar talep et")

    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(payload.new_password), row["user_id"]),
        )
        conn.execute("UPDATE password_resets SET used = 1 WHERE token = ?", (payload.token,))
        conn.commit()

    # Sifre sifirlandiginda guvenlik icin tum eski oturumlar (bu linki paylasan
    # baskasi dahil) sonlandirilir - kullanici yeni sifresiyle tekrar giris yapmali.
    invalidate_all_sessions(row["user_id"])

    return {"ok": True}


@app.delete("/api/auth/account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Hesabi ve tum verilerini (oturumlar, isler) kalici olarak siler.
    Kullaniciya ait video/klip dosyalari diskten de temizlenir."""
    with get_conn() as conn:
        job_ids = [
            r["id"] for r in conn.execute(
                "SELECT id FROM jobs WHERE user_id = ?", (current_user["id"],)
            ).fetchall()
        ]
        # sessions/jobs, users tablosundaki ON DELETE CASCADE sayesinde
        # otomatik siliniyor.
        conn.execute("DELETE FROM users WHERE id = ?", (current_user["id"],))
        conn.commit()

    for job_id in job_ids:
        shutil.rmtree(OUTPUT_DIR / job_id, ignore_errors=True)
        for f in UPLOAD_DIR.glob(f"{job_id}_*"):
            f.unlink(missing_ok=True)

    return {"ok": True}


# ---------------------------------------------------------------------------
# Ekip / Ajans isbirligi
# ---------------------------------------------------------------------------
# Sadece Ajans planindaki kullanicilar bir ekip olusturabilir (sahip olur).
# Sahip, e-posta ile davet linki uretir (e-posta GONDERILMEZ - linki kendisi
# paylasir); linkteki token'i kabul eden kisi ekibe uye olur ve o andan
# itibaren ekibin TUM video/klip gecmisini gorur, ekip sahibinin plan
# haklarindan (kredi, klip ozellestirme) faydalanir.

def _require_ajans(current_user: dict):
    if current_user["plan"] != "ajans":
        raise HTTPException(status_code=403, detail="Ekip özelliği sadece Ajans planında kullanılabilir")


@app.post("/api/org")
async def create_org(payload: OrgPayload, current_user: dict = Depends(get_current_user)):
    _require_ajans(current_user)
    if _get_user_org(current_user["id"]):
        raise HTTPException(status_code=409, detail="Zaten bir ekibin var")

    name = payload.name.strip() or f"{current_user['email'].split('@')[0]} Ekibi"
    if len(name) > 60:
        raise HTTPException(status_code=400, detail="Ekip adı en fazla 60 karakter olabilir")

    org_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO organizations (id, name, owner_id) VALUES (?, ?, ?)",
            (org_id, name, current_user["id"]),
        )
        conn.execute(
            "INSERT INTO org_members (org_id, user_id, role) VALUES (?, ?, 'owner')",
            (org_id, current_user["id"]),
        )
        conn.commit()

    return {"id": org_id, "name": name, "role": "owner"}


@app.get("/api/org")
async def get_org(current_user: dict = Depends(get_current_user)):
    org = _get_user_org(current_user["id"])
    if not org:
        return {"org": None}

    with get_conn() as conn:
        members = conn.execute(
            """
            SELECT users.id, users.email, users.display_name, users.avatar, org_members.role
            FROM org_members JOIN users ON users.id = org_members.user_id
            WHERE org_members.org_id = ?
            ORDER BY (org_members.role = 'owner') DESC, org_members.joined_at ASC
            """,
            (org["id"],),
        ).fetchall()
        invites = []
        if org["role"] == "owner":
            invites = conn.execute(
                "SELECT token, email, created_at FROM org_invites WHERE org_id = ? ORDER BY created_at DESC",
                (org["id"],),
            ).fetchall()

    return {
        "org": {
            "id": org["id"],
            "name": org["name"],
            "role": org["role"],
            "members": [dict(m) for m in members],
            "invites": [dict(i) for i in invites],
        }
    }


@app.post("/api/org/invite")
async def invite_to_org(payload: InvitePayload, current_user: dict = Depends(get_current_user)):
    org = _get_user_org(current_user["id"])
    if not org or org["role"] != "owner":
        raise HTTPException(status_code=403, detail="Sadece ekip sahibi davet gönderebilir")

    email = payload.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Geçerli bir e-posta gir")

    with get_conn() as conn:
        existing_member = conn.execute(
            """
            SELECT 1 FROM org_members JOIN users ON users.id = org_members.user_id
            WHERE org_members.org_id = ? AND users.email = ?
            """,
            (org["id"], email),
        ).fetchone()
        if existing_member:
            raise HTTPException(status_code=409, detail="Bu kişi zaten ekipte")

        token = uuid.uuid4().hex
        conn.execute(
            "INSERT INTO org_invites (token, org_id, email) VALUES (?, ?, ?)",
            (token, org["id"], email),
        )
        conn.commit()

    return {"token": token}


@app.delete("/api/org/invites/{token}")
async def cancel_invite(token: str, current_user: dict = Depends(get_current_user)):
    org = _get_user_org(current_user["id"])
    if not org or org["role"] != "owner":
        raise HTTPException(status_code=403, detail="Sadece ekip sahibi daveti iptal edebilir")
    with get_conn() as conn:
        conn.execute("DELETE FROM org_invites WHERE token = ? AND org_id = ?", (token, org["id"]))
        conn.commit()
    return {"ok": True}


@app.post("/api/org/accept-invite")
async def accept_invite(payload: AcceptInvitePayload, current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        invite = conn.execute("SELECT * FROM org_invites WHERE token = ?", (payload.token,)).fetchone()
    if not invite:
        raise HTTPException(status_code=404, detail="Davet geçersiz veya süresi dolmuş")
    invite = dict(invite)

    if invite["email"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Bu davet başka bir e-posta adresi için gönderilmiş")
    if _get_user_org(current_user["id"]):
        raise HTTPException(status_code=409, detail="Zaten bir ekibin var, önce ondan ayrılmalısın")

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO org_members (org_id, user_id, role) VALUES (?, ?, 'member')",
            (invite["org_id"], current_user["id"]),
        )
        conn.execute("DELETE FROM org_invites WHERE token = ?", (payload.token,))
        conn.commit()
        org_row = conn.execute("SELECT name FROM organizations WHERE id = ?", (invite["org_id"],)).fetchone()

    return {"org_id": invite["org_id"], "org_name": org_row["name"] if org_row else None}


@app.delete("/api/org/members/{member_id}")
async def remove_member(member_id: int, current_user: dict = Depends(get_current_user)):
    org = _get_user_org(current_user["id"])
    if not org or org["role"] != "owner":
        raise HTTPException(status_code=403, detail="Sadece ekip sahibi üye çıkarabilir")
    if member_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Kendini çıkaramazsın")
    with get_conn() as conn:
        conn.execute("DELETE FROM org_members WHERE org_id = ? AND user_id = ?", (org["id"], member_id))
        conn.commit()
    return {"ok": True}


@app.post("/api/org/leave")
async def leave_org(current_user: dict = Depends(get_current_user)):
    org = _get_user_org(current_user["id"])
    if not org:
        raise HTTPException(status_code=404, detail="Bir ekibin yok")
    if org["role"] == "owner":
        raise HTTPException(
            status_code=400,
            detail="Ekip sahibi ekipten ayrılamaz - ekibi tamamen silmek için hesap ayarlarını kullan",
        )
    with get_conn() as conn:
        conn.execute("DELETE FROM org_members WHERE org_id = ? AND user_id = ?", (org["id"], current_user["id"]))
        conn.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

# Bir videoya elle eklenebilecek (AI'nin urettigi + kullanicinin manuel
# eklediği) toplam klip sayisi ust siniri - depolama/kotuye kullanim
# koruması.
MAX_CLIPS_PER_JOB = 15


def _set_job(job_id: str, **fields):
    keys = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [job_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {keys} WHERE id = ?", values)
        conn.commit()


def _generate_english_subtitles(
    all_words: list, start: float, end: float, style: str, remove_fillers: bool,
    job_id: str, job_out_dir: Path, name: str,
) -> str | None:
    """Klibin altyazi metinlerini Ingilizce'ye cevirip ayri bir .srt dosyasi olarak
    kaydeder (videoya yakilmaz, indirilebilir bir ek dosya olarak sunulur).
    Ceviri basarisiz olursa ana islemi bozmadan sessizce None doner."""
    try:
        keep_intervals = build_keep_intervals(all_words, start, end, remove_fillers=remove_fillers)
        remapped = remap_words(all_words, start, end, keep_intervals)
        chunks = chunk_words(remapped, style=style)
        if not chunks:
            return None
        translated = translate_to_english([c["text"] for c in chunks])
        for c, t in zip(chunks, translated):
            c["text"] = t
        srt_path = job_out_dir / f"{name}_en.srt"
        write_srt(chunks, srt_path)
        return f"/files/{job_id}/{srt_path.name}"
    except Exception:
        return None


def run_pipeline(
    job_id: str,
    video_path: str,
    style: str,
    remove_fillers: bool,
    max_clips: int = 5,
    min_duration: float = 20.0,
    max_duration: float = 75.0,
    subtitle_color: str = DEFAULT_SUBTITLE_COLOR,
    subtitle_position: str = DEFAULT_SUBTITLE_POSITION,
    aspect: str = DEFAULT_ASPECT,
):
    try:
        _set_job(job_id, status="transcribing")
        segments, detected_language = transcribe(video_path)
        all_words = [w for s in segments for w in s["words"]]
        if not all_words:
            # Videoda/ses kaydinda hic konusma algilanamadi - en olasi sebep,
            # ekran kaydinda mikrofon/sistem sesi izni verilmemis olmasi (item 9,
            # ekran kaydi ozelligi). Bunu kullaniciya anlasilir bir mesajla
            # bildiriyoruz; aksi halde faster-whisper/VAD'in ic detaylarindan
            # kaynaklanan "max() iterable argument is empty" gibi anlasilmaz bir
            # hata gosterilirdi.
            raise RuntimeError(
                "Videoda konusma algilanamadi. Ekran kaydi aliyorsan mikrofon "
                "veya sistem sesi izni verildiginden emin ol ve tekrar dene."
            )
        _set_job(job_id, words_json=json.dumps(all_words), language=detected_language)

        _set_job(job_id, status="finding_highlights")
        clips = find_highlights(
            segments, max_clips=max_clips, min_duration=min_duration, max_duration=max_duration,
        )

        _set_job(job_id, status="rendering")
        job_out_dir = OUTPUT_DIR / job_id
        results = []
        for i, clip in enumerate(clips):
            name = f"clip_{i+1}"
            title = clip.get("title", name)
            path = make_vertical_clip(
                video_path, clip["start"], clip["end"], all_words, job_out_dir, name,
                style=style, remove_fillers=remove_fillers,
                subtitle_color=subtitle_color, position=subtitle_position, aspect=aspect,
            )
            cover_path = make_cover(path, title, job_out_dir / f"{name}_cover.jpg")
            subtitles_en_url = None
            if detected_language != "en":
                subtitles_en_url = _generate_english_subtitles(
                    all_words, clip["start"], clip["end"], style, remove_fillers,
                    job_id, job_out_dir, name,
                )
            results.append({
                "title": title,
                "reason": clip.get("reason", ""),
                "score": clip.get("score"),
                "start": clip["start"],
                "end": clip["end"],
                "url": f"/files/{job_id}/{path.name}",
                "cover_url": f"/files/{job_id}/{cover_path.name}" if cover_path else None,
                "subtitles_en_url": subtitles_en_url,
                "style": style,
                "subtitle_color": subtitle_color,
                "subtitle_position": subtitle_position,
                "aspect": aspect,
                "remove_fillers": remove_fillers,
            })

        _set_job(job_id, status="done", clips_json=json.dumps(results))
    except Exception as e:
        _set_job(job_id, status="error", error=str(e))


def _job_to_dict(row: dict) -> dict:
    return {
        "job_id": row["id"],
        "filename": row["filename"],
        "status": row["status"],
        "error": row["error"],
        "clips": json.loads(row["clips_json"]) if row["clips_json"] else [],
        "style": row["style"],
        "remove_fillers": bool(row["remove_fillers"]),
        "language": row.get("language"),
        "subtitle_color": row.get("subtitle_color") or DEFAULT_SUBTITLE_COLOR,
        "subtitle_position": row.get("subtitle_position") or DEFAULT_SUBTITLE_POSITION,
        "aspect": row.get("aspect") or DEFAULT_ASPECT,
        "credit_cost": row.get("credit_cost") or 0,
        "uploaded_by": row.get("uploaded_by_email"),
        "created_at": row["created_at"],
    }


@app.post("/api/upload")
async def upload_video(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    style: str = Form(DEFAULT_STYLE),
    remove_fillers: bool = Form(True),
    clip_count: int | None = Form(None),
    min_duration: float | None = Form(None),
    max_duration: float | None = Form(None),
    subtitle_color: str | None = Form(None),
    subtitle_position: str | None = Form(None),
    aspect: str | None = Form(None),
    current_user: dict = Depends(get_current_user),
):
    if style not in STYLE_PRESETS:
        style = DEFAULT_STYLE

    # Ekip calisma alanindaysa haklar (kredi limiti, klip ozellestirme) kullanicinin
    # kendi planindan degil, ekip sahibinin planindan miras alinir.
    org = _get_user_org(current_user["id"])
    effective_plan = _effective_plan(current_user, org)

    # Klip sayisi/sure araligi ozellestirmesi sadece ucretli planlarda acik -
    # ucretsiz plan istese bile (form alanini elle gonderse dahi) sunucu tarafinda
    # yoksayilir, sabit varsayilanlar kullanilir.
    can_customize = effective_plan in CUSTOMIZABLE_CLIP_PLANS
    max_clips = 5
    dur_min, dur_max = 20.0, 75.0
    if can_customize:
        if clip_count is not None:
            if not (3 <= clip_count <= 8):
                raise HTTPException(status_code=400, detail="Klip sayısı 3 ile 8 arasında olmalı")
            max_clips = clip_count
        if min_duration is not None and max_duration is not None:
            if not (10 <= min_duration < max_duration <= 180):
                raise HTTPException(status_code=400, detail="Klip süre aralığı geçersiz")
            dur_min, dur_max = min_duration, max_duration

    # Altyazi rengi/konumu ve en-boy orani tum planlarda acik - sadece
    # klip sayisi/suresi ucretli plana ozel (yukarida ayrica kontrol edildi).
    color, position, asp = _validate_render_options(subtitle_color, subtitle_position, aspect)

    job_id = str(uuid.uuid4())
    video_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Kredi maliyeti: video suresi (ffprobe ile okunur) ve secilen klip
    # sayisina gore hesaplanir - bkz. app/services/credits.py.
    duration_seconds = get_video_duration(str(video_path))
    cost = compute_credit_cost(duration_seconds, max_clips)

    limit = CREDIT_LIMITS.get(effective_plan, CREDIT_LIMITS["ucretsiz"])
    if limit is not None:
        used = _credits_used_this_month(current_user, org)
        if used + cost > limit:
            video_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=402,
                detail=(
                    f"Bu video {cost} kredi gerektiriyor ama bu ay {max(0, limit - used)} "
                    f"kredin kaldı ({used}/{limit}). Daha yüksek bir plana geçebilirsin."
                ),
            )

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, user_id, filename, status, style, remove_fillers, subtitle_color, subtitle_position, aspect, credit_cost, org_id)
            VALUES (?, ?, ?, 'queued', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id, current_user["id"], file.filename, style, int(remove_fillers),
                color, position, asp, cost, org["id"] if org else None,
            ),
        )
        conn.commit()

    background_tasks.add_task(
        run_pipeline, job_id, str(video_path), style, remove_fillers, max_clips, dur_min, dur_max,
        color, position, asp,
    )
    return {"job_id": job_id, "credit_cost": cost}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, current_user: dict = Depends(get_current_user)):
    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM jobs WHERE id = ? AND {scope_sql}", (job_id, *scope_params)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    return _job_to_dict(dict(row))


@app.get("/api/jobs")
async def list_jobs(current_user: dict = Depends(get_current_user)):
    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT jobs.*, users.email AS uploaded_by_email
            FROM jobs
            LEFT JOIN users ON users.id = jobs.user_id
            WHERE {scope_sql}
            ORDER BY jobs.created_at DESC LIMIT 50
            """,
            scope_params,
        ).fetchall()
    return [_job_to_dict(dict(r)) for r in rows]


@app.get("/api/jobs/{job_id}/source")
async def job_source(job_id: str, current_user: dict = Depends(get_current_user_flexible)):
    """Orijinal yuklenen videoyu (kirpilmemis) dondurur - kirpma editorunde
    kullanicinin baslangic/bitis noktasini videonun kendisi uzerinde
    surukleyerek secebilmesi icin. Isin sahibi veya (is bir ekibe aitse)
    ekibin tum uyeleri erisebilir."""
    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM jobs WHERE id = ? AND {scope_sql}", (job_id, *scope_params)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    row = dict(row)

    video_path = UPLOAD_DIR / f"{job_id}_{row['filename']}"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Orijinal video dosyası bulunamadı")

    return FileResponse(str(video_path), media_type="video/mp4")


@app.post("/api/jobs/{job_id}/clips/{clip_index}/retrim")
async def retrim_clip(
    job_id: str,
    clip_index: int,
    payload: RetrimPayload,
    current_user: dict = Depends(get_current_user),
):
    """Bir klibin baslangic/bitis noktasini elle degistirip videoyu (ve altyazilarini,
    kapak gorselini) o yeni araliktan yeniden uretir. Isin sahibi veya (is bir
    ekibe aitse) ekibin tum uyeleri erisebilir."""
    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM jobs WHERE id = ? AND {scope_sql}", (job_id, *scope_params)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    row = dict(row)

    if row["status"] != "done":
        raise HTTPException(status_code=409, detail="Bu iş henüz tamamlanmadı")
    if payload.end - payload.start < 3:
        raise HTTPException(status_code=400, detail="Klip en az 3 saniye olmalı")
    if payload.start < 0:
        raise HTTPException(status_code=400, detail="Başlangıç negatif olamaz")

    words_json = row.get("words_json")
    if not words_json:
        raise HTTPException(
            status_code=409,
            detail="Bu iş için transkript verisi saklanmamış, klip yeniden düzenlenemiyor",
        )
    all_words = json.loads(words_json)

    video_path = UPLOAD_DIR / f"{job_id}_{row['filename']}"
    if not video_path.exists():
        raise HTTPException(status_code=409, detail="Orijinal video dosyası bulunamadı")

    clips = json.loads(row["clips_json"]) if row["clips_json"] else []
    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(status_code=404, detail="Klip bulunamadı")

    existing_clip = clips[clip_index]
    style = _resolve_clip_option(
        payload.style, lambda v: v in STYLE_PRESETS, existing_clip, "style", row, "style", DEFAULT_STYLE,
    )
    remove_fillers = (
        payload.remove_fillers if payload.remove_fillers is not None
        else existing_clip["remove_fillers"] if "remove_fillers" in existing_clip
        else bool(row["remove_fillers"])
    )
    color = _resolve_clip_option(
        payload.subtitle_color, lambda v: bool(HEX_COLOR_RE.match(v)),
        existing_clip, "subtitle_color", row, "subtitle_color", DEFAULT_SUBTITLE_COLOR,
    )
    position = _resolve_clip_option(
        payload.subtitle_position, lambda v: v in SUBTITLE_POSITIONS,
        existing_clip, "subtitle_position", row, "subtitle_position", DEFAULT_SUBTITLE_POSITION,
    )
    asp = _resolve_clip_option(
        payload.aspect, lambda v: v in ASPECT_PRESETS, existing_clip, "aspect", row, "aspect", DEFAULT_ASPECT,
    )
    name = f"clip_{clip_index + 1}"
    job_out_dir = OUTPUT_DIR / job_id

    try:
        path = make_vertical_clip(
            str(video_path), payload.start, payload.end, all_words, job_out_dir, name,
            style=style, remove_fillers=remove_fillers,
            subtitle_color=color, position=position, aspect=asp,
        )
        cover_path = make_cover(path, clips[clip_index].get("title", name), job_out_dir / f"{name}_cover.jpg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yeniden oluşturma başarısız: {e}")

    subtitles_en_url = None
    if row.get("language") != "en":
        subtitles_en_url = _generate_english_subtitles(
            all_words, payload.start, payload.end, style, remove_fillers,
            job_id, job_out_dir, name,
        )

    cache_bust = uuid.uuid4().hex[:8]
    clips[clip_index] = {
        **clips[clip_index],
        "start": payload.start,
        "end": payload.end,
        "url": f"/files/{job_id}/{path.name}?v={cache_bust}",
        "cover_url": f"/files/{job_id}/{cover_path.name}?v={cache_bust}" if cover_path else None,
        "subtitles_en_url": subtitles_en_url,
        "style": style,
        "subtitle_color": color,
        "subtitle_position": position,
        "aspect": asp,
        "remove_fillers": remove_fillers,
    }

    with get_conn() as conn:
        conn.execute("UPDATE jobs SET clips_json = ? WHERE id = ?", (json.dumps(clips), job_id))
        conn.commit()

    return clips[clip_index]


@app.post("/api/jobs/{job_id}/clips/add")
async def add_clip(
    job_id: str,
    payload: AddClipPayload,
    current_user: dict = Depends(get_current_user),
):
    """Kullanicinin, orijinal video uzerinde AI'nin onerdigi kliplerle sinirli
    kalmadan kendi sectigi herhangi bir araliktan elle yeni bir klip
    olusturmasini saglar. Bu ek klip icin ayrica kredi harcanir (bkz.
    compute_added_clip_cost) ve isin toplam credit_cost'una eklenir. Isin
    sahibi veya (is bir ekibe aitse) ekibin tum uyeleri kullanabilir."""
    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM jobs WHERE id = ? AND {scope_sql}", (job_id, *scope_params)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    row = dict(row)

    if row["status"] != "done":
        raise HTTPException(status_code=409, detail="Bu iş henüz tamamlanmadı")
    if payload.end - payload.start < 3:
        raise HTTPException(status_code=400, detail="Klip en az 3 saniye olmalı")
    if payload.start < 0:
        raise HTTPException(status_code=400, detail="Başlangıç negatif olamaz")

    words_json = row.get("words_json")
    if not words_json:
        raise HTTPException(
            status_code=409,
            detail="Bu iş için transkript verisi saklanmamış, yeni klip oluşturulamıyor",
        )
    all_words = json.loads(words_json)

    video_path = UPLOAD_DIR / f"{job_id}_{row['filename']}"
    if not video_path.exists():
        raise HTTPException(status_code=409, detail="Orijinal video dosyası bulunamadı")

    clips = json.loads(row["clips_json"]) if row["clips_json"] else []
    if len(clips) >= MAX_CLIPS_PER_JOB:
        raise HTTPException(
            status_code=400,
            detail=f"Bir video için en fazla {MAX_CLIPS_PER_JOB} klip oluşturulabilir",
        )

    duration_seconds = get_video_duration(str(video_path))
    if duration_seconds and payload.end > duration_seconds + 0.5:
        raise HTTPException(status_code=400, detail="Bitiş noktası videonun süresini aşıyor")

    added_cost = compute_added_clip_cost(duration_seconds)
    effective_plan = _effective_plan(current_user, org)
    limit = CREDIT_LIMITS.get(effective_plan, CREDIT_LIMITS["ucretsiz"])
    if limit is not None:
        used = _credits_used_this_month(current_user, org)
        if used + added_cost > limit:
            raise HTTPException(
                status_code=402,
                detail=(
                    f"Yeni klip {added_cost} kredi gerektiriyor ama bu ay "
                    f"{max(0, limit - used)} kredin kaldı ({used}/{limit}). "
                    f"Daha yüksek bir plana geçebilirsin."
                ),
            )

    style = _resolve_clip_option(
        payload.style, lambda v: v in STYLE_PRESETS, {}, "style", row, "style", DEFAULT_STYLE,
    )
    remove_fillers = payload.remove_fillers if payload.remove_fillers is not None else bool(row["remove_fillers"])
    color = _resolve_clip_option(
        payload.subtitle_color, lambda v: bool(HEX_COLOR_RE.match(v)), {}, "subtitle_color", row, "subtitle_color", DEFAULT_SUBTITLE_COLOR,
    )
    position = _resolve_clip_option(
        payload.subtitle_position, lambda v: v in SUBTITLE_POSITIONS, {}, "subtitle_position", row, "subtitle_position", DEFAULT_SUBTITLE_POSITION,
    )
    asp = _resolve_clip_option(
        payload.aspect, lambda v: v in ASPECT_PRESETS, {}, "aspect", row, "aspect", DEFAULT_ASPECT,
    )
    index = len(clips)
    name = f"clip_{index + 1}"
    job_out_dir = OUTPUT_DIR / job_id
    title = (payload.title or "").strip() or "Manuel klip"

    try:
        path = make_vertical_clip(
            str(video_path), payload.start, payload.end, all_words, job_out_dir, name,
            style=style, remove_fillers=remove_fillers,
            subtitle_color=color, position=position, aspect=asp,
        )
        cover_path = make_cover(path, title, job_out_dir / f"{name}_cover.jpg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Klip oluşturulamadı: {e}")

    subtitles_en_url = None
    if row.get("language") != "en":
        subtitles_en_url = _generate_english_subtitles(
            all_words, payload.start, payload.end, style, remove_fillers,
            job_id, job_out_dir, name,
        )

    new_clip = {
        "title": title,
        "reason": "Elle seçildi",
        "score": None,
        "start": payload.start,
        "end": payload.end,
        "url": f"/files/{job_id}/{path.name}",
        "cover_url": f"/files/{job_id}/{cover_path.name}" if cover_path else None,
        "subtitles_en_url": subtitles_en_url,
        "manual": True,
        "style": style,
        "subtitle_color": color,
        "subtitle_position": position,
        "aspect": asp,
        "remove_fillers": remove_fillers,
    }
    clips.append(new_clip)

    with get_conn() as conn:
        conn.execute(
            "UPDATE jobs SET clips_json = ?, credit_cost = credit_cost + ? WHERE id = ?",
            (json.dumps(clips), added_cost, job_id),
        )
        conn.commit()

    return {"clip": new_clip, "clips": clips, "added_cost": added_cost}


@app.delete("/api/jobs/{job_id}/clips/{clip_index}")
async def delete_clip(
    job_id: str,
    clip_index: int,
    current_user: dict = Depends(get_current_user),
):
    """Elle eklenmis bir klibi siler - AI'nin ilk urettigi klipler silinemez,
    onlar yerine /retrim ile yeniden duzenlenebilir. Dosyalarini da diskten
    kaldirir."""
    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM jobs WHERE id = ? AND {scope_sql}", (job_id, *scope_params)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    row = dict(row)

    clips = json.loads(row["clips_json"]) if row["clips_json"] else []
    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(status_code=404, detail="Klip bulunamadı")
    clip = clips[clip_index]
    if not clip.get("manual"):
        raise HTTPException(status_code=400, detail="Sadece elle eklenen klipler silinebilir")

    job_out_dir = OUTPUT_DIR / job_id
    for key in ("url", "cover_url", "subtitles_en_url"):
        url = clip.get(key)
        if url:
            fname = url.split("/")[-1].split("?")[0]
            (job_out_dir / fname).unlink(missing_ok=True)

    clips.pop(clip_index)
    with get_conn() as conn:
        conn.execute("UPDATE jobs SET clips_json = ? WHERE id = ?", (json.dumps(clips), job_id))
        conn.commit()

    return {"ok": True, "clips": clips}


@app.post("/api/jobs/{job_id}/clips/{clip_index}/translate")
async def translate_clip(
    job_id: str,
    clip_index: int,
    payload: TranslateClipPayload,
    current_user: dict = Depends(get_current_user),
):
    """Bir klip icin Ingilizce disinda (o otomatik uretilir) baska bir dilde
    de altyazi (.srt) dosyasi uretir - SUBTITLE_LANGUAGES listesinden herhangi
    bir dil secilebilir. Uretilen dosyalar klibin 'translations' listesinde
    birikir (ayni dil tekrar istenirse ustune yazilir). Sadece metin cevirisi
    oldugu icin kredi harcamaz."""
    if payload.language not in SUBTITLE_LANGUAGES:
        raise HTTPException(status_code=400, detail="Desteklenmeyen dil")

    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM jobs WHERE id = ? AND {scope_sql}", (job_id, *scope_params)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    row = dict(row)

    words_json = row.get("words_json")
    if not words_json:
        raise HTTPException(status_code=409, detail="Bu iş için transkript verisi saklanmamış")
    all_words = json.loads(words_json)

    clips = json.loads(row["clips_json"]) if row["clips_json"] else []
    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(status_code=404, detail="Klip bulunamadı")
    clip = clips[clip_index]
    start, end = clip.get("start"), clip.get("end")
    if start is None or end is None:
        raise HTTPException(status_code=409, detail="Bu klip için zaman aralığı bilgisi yok")

    style = clip.get("style") or row["style"] or DEFAULT_STYLE
    remove_fillers = clip["remove_fillers"] if "remove_fillers" in clip else bool(row["remove_fillers"])
    job_out_dir = OUTPUT_DIR / job_id
    job_out_dir.mkdir(parents=True, exist_ok=True)
    name = f"clip_{clip_index + 1}"
    lang_label = SUBTITLE_LANGUAGES[payload.language]

    try:
        keep_intervals = build_keep_intervals(all_words, start, end, remove_fillers=remove_fillers)
        remapped = remap_words(all_words, start, end, keep_intervals)
        chunks = chunk_words(remapped, style=style)
        if not chunks:
            raise HTTPException(status_code=409, detail="Bu klip için altyazı metni bulunamadı")
        translated = translate_subtitles([c["text"] for c in chunks], lang_label)
        for c, t in zip(chunks, translated):
            c["text"] = t
        srt_path = job_out_dir / f"{name}_{payload.language}.srt"
        write_srt(chunks, srt_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Çeviri başarısız: {e}")

    cache_bust = uuid.uuid4().hex[:8]
    url = f"/files/{job_id}/{srt_path.name}?v={cache_bust}"
    translations = [t for t in clip.get("translations", []) if t.get("language") != payload.language]
    translations.append({"language": payload.language, "label": lang_label, "url": url})
    clips[clip_index] = {**clip, "translations": translations}

    with get_conn() as conn:
        conn.execute("UPDATE jobs SET clips_json = ? WHERE id = ?", (json.dumps(clips), job_id))
        conn.commit()

    return clips[clip_index]


@app.post("/api/jobs/{job_id}/clips/{clip_index}/caption")
async def generate_clip_caption(
    job_id: str,
    clip_index: int,
    current_user: dict = Depends(get_current_user),
):
    """Klibin transkript metninden sosyal medya paylasim metni (caption) ve
    hashtag onerileri uretip klibe kaydeder. Video islemenin aksine kisa bir
    metin uretimi oldugu icin kredi harcamaz."""
    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM jobs WHERE id = ? AND {scope_sql}", (job_id, *scope_params)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    row = dict(row)

    words_json = row.get("words_json")
    if not words_json:
        raise HTTPException(status_code=409, detail="Bu iş için transkript verisi saklanmamış")
    all_words = json.loads(words_json)

    clips = json.loads(row["clips_json"]) if row["clips_json"] else []
    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(status_code=404, detail="Klip bulunamadı")
    clip = clips[clip_index]
    start, end = clip.get("start"), clip.get("end")
    if start is None or end is None:
        raise HTTPException(status_code=409, detail="Bu klip için zaman aralığı bilgisi yok")

    clip_words = [w for w in all_words if start <= w["start"] < end]
    transcript_text = "".join(w["word"] for w in clip_words).strip()
    if not transcript_text:
        raise HTTPException(status_code=409, detail="Bu klip için transkript metni bulunamadı")

    try:
        result = generate_social_caption(transcript_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Paylaşım metni oluşturulamadı: {e}")

    clips[clip_index] = {**clip, "social_caption": result["caption"], "social_hashtags": result["hashtags"]}

    with get_conn() as conn:
        conn.execute("UPDATE jobs SET clips_json = ? WHERE id = ?", (json.dumps(clips), job_id))
        conn.commit()

    return clips[clip_index]


@app.get("/api/subtitle-languages")
async def subtitle_languages():
    return [{"id": key, "label": label} for key, label in SUBTITLE_LANGUAGES.items()]


@app.get("/api/caption-styles")
async def caption_styles():
    return {key: preset["label"] for key, preset in STYLE_PRESETS.items()}


@app.get("/api/render-options")
async def render_options():
    """Yukleme panelinde gosterilecek altyazi rengi, altyazi konumu ve
    klip en-boy orani secenekleri - hepsi tum planlarda acik."""
    return {
        "aspects": [{"id": key, "label": preset["label"]} for key, preset in ASPECT_PRESETS.items()],
        "positions": [{"id": key, "label": preset["label"]} for key, preset in SUBTITLE_POSITIONS.items()],
        "colors": SUBTITLE_COLOR_PRESETS,
        "credits": {"base": CREDIT_COST_BASE, "per_clip": CREDIT_COST_PER_CLIP},
    }


@app.get("/api/health")
async def health():
    return {"ok": True}
