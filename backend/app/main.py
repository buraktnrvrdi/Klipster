"""Icerik yeniden uretim API'si: kullanici kaydi/girisi, kullanim limiti,
video yukle -> transkript cikar -> viral anlari bul -> dikey altyazili klipler uret."""
import json
import logging
import os
import re
import secrets
import shutil
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# basicConfig cagrilmazsa Python'un "son care" (lastResort) log mekanizmasi
# devreye girer - bu SADECE WARNING ve uzeri seviyeyi gosterir, tum
# logger.info(...) cagrilari (uygulama genelinde - PO token/cookie/deneme
# loglari dahil) sessizce kaybolur. Railway loglarinda bircok tani satirinin
# hic gorunmemesinin sebebi buydu.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

# .env dosyasi, asagidaki app.* importlarindan ONCE yuklenmeli - yoksa
# app.services.email gibi import aninda ortam degiskeni okuyan modüller
# SMTP bilgilerini hicbir zaman goremez (bu tam olarak yasanan hataydi).
load_dotenv()

from fastapi import BackgroundTasks, Depends, FastAPI, Form, Header, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
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
from app.services import payments
from app.services import social_youtube
from app.services import storage
from app.services.highlights import (
    find_highlights,
    generate_social_caption,
    translate_subtitles,
    translate_to_english,
)
from app.services.transcribe import transcribe, unload_model as unload_whisper
from app.services.youtube import MIN_FREE_DISK_BYTES, VideoUrlError, download_video
from app.services.video import (
    ASPECT_PRESETS,
    DEFAULT_ASPECT,
    DEFAULT_STYLE,
    DEFAULT_HIGHLIGHT_COLOR,
    DEFAULT_OVERLAY_X,
    DEFAULT_OVERLAY_Y,
    DEFAULT_OVERLAY_SCALE,
    DEFAULT_SUBTITLE_ANIMATION,
    DEFAULT_SUBTITLE_COLOR,
    DEFAULT_SUBTITLE_POSITION,
    OVERLAY_SCALES,
    STYLE_PRESETS,
    SUBTITLE_ANIMATIONS,
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
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000").strip().rstrip("/")

# iyzico'nun odeme sonrasi kullaniciyi (POST ile) geri gonderecegi adres bu
# backend'in kendi adresi olmali (oturum cerezi/token tasimadigi icin auth
# gerektirmeyen /api/payments/callback ucnoktasi bu isi yapar) - .env'e
# BACKEND_URL eklenmezse yerel gelistirme adresi varsayilir.
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").strip().rstrip("/")

# /api/admin/* uc noktalarini korumak icin paylasilan gizli anahtar - ayri
# bir admin kullanici/rol sistemi kurmak yerine (bu tek bir kisinin - bizim -
# elle kullanacagi bir arac), tek bir ortam degiskeniyle korunuyor. Railway'de
# ADMIN_API_KEY tanimli degilse bu uc noktalar tamamen kapali kalir.
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "").strip()

# Sifre sifirlama linki bu sure sonra gecersiz olur.
PASSWORD_RESET_TTL_MINUTES = 60

# E-posta dogrulama linki bu sure sonra gecersiz olur - sifre sifirlamanin
# aksine eskiden suresiz gecerliydi, eski/sizmis bir linkin yillar sonra da
# kullanilabilmesini onlemek icin sinirlandirildi.
EMAIL_VERIFICATION_TTL_HOURS = 48

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
LOGO_DIR = OUTPUT_DIR / "logos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGO_DIR.mkdir(parents=True, exist_ok=True)

init_db()


def _safe_filename(name: str) -> str:
    """Kullanicidan gelen dosya adini diskte guvenle kullanilabilir hale
    getirir - path traversal (../, mutlak yol, ayirici karakterler) ve
    dosya sistemi icin sorunlu karakterleri temizler. Sonuc bos kalirsa
    genel bir varsayilan isim doner."""
    name = os.path.basename(name or "")
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = name.lstrip(".") or "video"
    return name[-200:]


def _upload_output(job_id: str, local_path: Path) -> str:
    """Upload a rendered output file to R2 (if enabled), delete local copy, return URL.
    Falls back to /files/ static path when R2 is not configured."""
    if not storage.is_enabled():
        return f"/files/{job_id}/{local_path.name}"
    key = f"outputs/{job_id}/{local_path.name}"
    url = storage.upload(local_path, key)
    local_path.unlink(missing_ok=True)
    return url


def _ensure_original_local(job_id: str, filename: str) -> tuple[Path, bool]:
    """Return (path, is_temp). Downloads from R2 to a temp dir if the local
    copy no longer exists (it was archived after the initial pipeline run).
    Caller must delete the temp file when is_temp=True."""
    local = UPLOAD_DIR / f"{job_id}_{filename}"
    if local.exists():
        return local, False
    if storage.is_enabled():
        key = f"uploads/{job_id}/{filename}"
        tmp = Path(tempfile.mkdtemp()) / f"{job_id}_{filename}"
        storage.download(key, tmp)
        return tmp, True
    return local, False  # caller will catch missing file


def _ensure_overlay_local(overlay_value: str | None) -> tuple[Path | None, bool]:
    """overlay_value bos ise (None/""), (None, False) doner - overlay yok demektir.
    Deger yerel bir /files/logos/... yoluysa dogrudan diskteki karsiligini,
    R2/B2'deki bir anahtarsa gecici bir dosyaya indirip onu dondurur. Ikinci
    deger (is_temp) True ise, cagiran taraf isi bitince o gecici dosyayi silmeli."""
    if not overlay_value:
        return None, False
    if overlay_value.startswith("/files/logos/"):
        local = OUTPUT_DIR / overlay_value.removeprefix("/files/")
        return (local, False) if local.exists() else (None, False)
    if storage.is_enabled():
        tmp = Path(tempfile.mkdtemp()) / Path(overlay_value).name
        try:
            storage.download(overlay_value, tmp)
        except Exception:
            return None, False
        return tmp, True
    return None, False


def _ensure_clip_local(clip_url: str | None) -> tuple[Path | None, bool]:
    """Bir klibin uretilmis video dosyasini yerel bir yola cozer - disk
    modundaysa dogrudan diskteki kopyayi, R2/B2 modundaysa gecici bir dosyaya
    indirip onu dondurur (YouTube'a yuklerken kullanilir). clip["url"]
    veritabaninda ham (henuz imzali URL'e cevrilmemis) haliyle tutulur -
    bkz. _resolve_clip_urls."""
    if not clip_url:
        return None, False
    if clip_url.startswith("/files/"):
        local = OUTPUT_DIR / clip_url.removeprefix("/files/")
        return (local, False) if local.exists() else (None, False)
    if storage.is_enabled():
        key = storage.key_from_value(clip_url) or clip_url
        tmp = Path(tempfile.mkdtemp()) / Path(key).name
        try:
            storage.download(key, tmp)
        except Exception:
            return None, False
        return tmp, True
    return None, False


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
                error = 'Sunucu yeniden baslatildigi icin bu islem yarida kaldi - lutfen videoyu tekrar yukle. Bu islem icin kredin harcanmadi.'
            WHERE status NOT IN ('done', 'error')
            """
        )
        conn.commit()
        if updated.rowcount:
            logger.info("[baslangic temizligi] %d yarim kalan is hataya cevrildi", updated.rowcount)


_recover_interrupted_jobs()


class _RateLimiter:
    """Basit, bellek-ici (in-memory) sabit-pencereli rate limiter. Tek process
    deploy icin orantili bir onlem - brute-force/enumeration denemelerini
    yavaslatir. Coklu worker/process'te paylasilmaz (her worker kendi
    sayacini tutar); gercek dagitik limitleme icin Redis gerekir ama bu
    projenin olcegi icin gereksiz bir karmasiklik olur."""

    def __init__(self):
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: float):
        now = time.monotonic()
        with self._lock:
            hits = [t for t in self._hits.get(key, []) if now - t < window_seconds]
            if len(hits) >= limit:
                raise HTTPException(
                    status_code=429,
                    detail="Çok fazla deneme yapıldı - lütfen biraz sonra tekrar dene",
                )
            hits.append(now)
            self._hits[key] = hits


_rate_limiter = _RateLimiter()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


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
    subtitle_color: str | None, subtitle_position: str | None, aspect: str | None,
    subtitle_animation: str | None = None, highlight_color: str | None = None,
) -> tuple[str, str, str, str, str]:
    """Altyazi rengi/konumu, en-boy orani, altyazi animasyonu ve vurgu (karaoke/pop
    aktif kelime) rengi kullanici girdisini dogrular, gecersiz/eksik deger gelirse
    sessizce varsayilana duser."""
    color = subtitle_color if subtitle_color and HEX_COLOR_RE.match(subtitle_color) else DEFAULT_SUBTITLE_COLOR
    position = subtitle_position if subtitle_position in SUBTITLE_POSITIONS else DEFAULT_SUBTITLE_POSITION
    asp = aspect if aspect in ASPECT_PRESETS else DEFAULT_ASPECT
    anim = subtitle_animation if subtitle_animation in SUBTITLE_ANIMATIONS else DEFAULT_SUBTITLE_ANIMATION
    hcolor = highlight_color if highlight_color and HEX_COLOR_RE.match(highlight_color) else DEFAULT_HIGHLIGHT_COLOR
    return color, position, asp, anim, hcolor


def _validate_overlay_options(
    overlay_x: float | None, overlay_y: float | None, overlay_scale: str | None
) -> tuple[float, float, str]:
    """Logo/banner bindirme konumu (0.0-1.0 orani) ve boyutu icin kullanici
    girdisini dogrular, gecersiz/eksik deger gelirse sessizce varsayilana
    duser; konum degerleri 0.0-1.0 araligina sikistirilir."""
    x = overlay_x if isinstance(overlay_x, (int, float)) else DEFAULT_OVERLAY_X
    y = overlay_y if isinstance(overlay_y, (int, float)) else DEFAULT_OVERLAY_Y
    x = min(max(float(x), 0.0), 1.0)
    y = min(max(float(y), 0.0), 1.0)
    scale = overlay_scale if overlay_scale in OVERLAY_SCALES else DEFAULT_OVERLAY_SCALE
    return x, y, scale


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
    subtitle_animation: str | None = None
    highlight_color: str | None = None
    # overlay_url: None = degistirme, "" = kaldir, baska bir deger = yeni logo/banner
    overlay_url: str | None = None
    overlay_x: float | None = None
    overlay_y: float | None = None
    overlay_scale: str | None = None


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
    subtitle_animation: str | None = None
    highlight_color: str | None = None
    overlay_url: str | None = None
    overlay_x: float | None = None
    overlay_y: float | None = None
    overlay_scale: str | None = None


class TranslateClipPayload(BaseModel):
    language: str


class UploadUrlPayload(BaseModel):
    """Kullanicinin bilgisayarindan dosya yuklemek yerine bir video linki
    (YouTube ve yt-dlp'nin destekledigi diger siteler) yapistirarak video
    yuklemesini saglayan istek govdesi - /api/upload ile ayni render/klip
    secenekleri (multipart yerine JSON govdesinde)."""
    url: str
    style: str | None = None
    remove_fillers: bool | None = None
    clip_count: int | None = None
    min_duration: float | None = None
    max_duration: float | None = None
    subtitle_color: str | None = None
    subtitle_position: str | None = None
    aspect: str | None = None
    subtitle_animation: str | None = None
    highlight_color: str | None = None
    overlay_url: str | None = None
    overlay_x: float | None = None
    overlay_y: float | None = None
    overlay_scale: str | None = None


class PasswordPayload(BaseModel):
    current_password: str
    new_password: str


class OrgPayload(BaseModel):
    name: str


class InvitePayload(BaseModel):
    email: str


class AcceptInvitePayload(BaseModel):
    token: str


class CheckoutPayload(BaseModel):
    """Odeme sayfasindan gonderilen fatura/musteri bilgileri. TC kimlik no
    opsiyonel: iyzico API'si bunu gercek bir kimlik dogrulamasi olarak
    kullanmiyor (resmi ornek kodlarinda bile gecersiz formatta degerler var,
    ör. "111111"), sadece dolu bir alan bekliyor - bos birakilirsa sabit bir
    dolgu deger gonderilir, kullanicidan zorla istenmez."""
    plan: str
    name: str
    surname: str
    phone: str
    identity_number: str | None = None
    address: str
    city: str
    zip_code: str | None = None


class ForgotPasswordPayload(BaseModel):
    email: str


class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str


class VerifyEmailPayload(BaseModel):
    email: str
    code: str


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
    """Kullanıcıya 6 haneli, tek kullanımlık bir doğrulama kodu gönderir -
    e-postadaki bir linke tıklamak yerine bu kodu siteye geri girmesi gerekir.
    Linkin gittiği domain'e (DNS/CORS/vs.) bağımlı kalmamak ve e-posta
    güvenlik tarayıcılarının linki kullanıcıdan önce tüketmesi gibi
    sorunları ortadan kaldırmak için tercih edildi."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    token = secrets.token_urlsafe(32)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO email_verifications (token, user_id, code) VALUES (%s, %s, %s)",
            (token, user_id, code),
        )
        conn.commit()
    send_email(
        email,
        "Klipster - E-posta adresini doğrula",
        f"Merhaba,\n\nKlipster hesabını doğrulamak için bu kodu kullan:\n\n{code}\n\n"
        f"Bu kod {EMAIL_VERIFICATION_TTL_HOURS} saat geçerlidir. Bu kodu sen istemediysen "
        f"bu e-postayı yok sayabilirsin.",
    )


def _get_user_org(user_id: int) -> dict | None:
    """Kullanicinin uyesi oldugu ekibi (varsa) rolüyle birlikte dondurur."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT organizations.id, organizations.name, organizations.owner_id, org_members.role
            FROM org_members
            JOIN organizations ON organizations.id = org_members.org_id
            WHERE org_members.user_id = %s
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
        row = conn.execute("SELECT plan FROM users WHERE id = %s", (org["owner_id"],)).fetchone()
    return row["plan"] if row else current_user["plan"]


def _job_scope(current_user: dict, org: dict | None) -> tuple[str, tuple]:
    """Bir kullanicinin gorebilecegi islerin SQL WHERE kosulu ve parametreleri -
    bir ekipteyse ekibin TUM isleri, degilse sadece kendi isleri gorunur."""
    if org:
        return "org_id = %s", (org["id"],)
    return "user_id = %s AND org_id IS NULL", (current_user["id"],)


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
              AND to_char(created_at, 'YYYY-MM') = to_char(now(), 'YYYY-MM')
            """,
            scope_params,
        ).fetchone()
    return row["c"] if row else 0


@app.post("/api/auth/register")
async def register(payload: AuthPayload, request: Request):
    _rate_limiter.check(f"register:{_client_ip(request)}", limit=10, window_seconds=3600)
    email = payload.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Geçerli bir e-posta gir")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalı")

    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = %s", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı")
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, plan, email_verified) VALUES (%s, %s, 'ucretsiz', 0) RETURNING id",
            (email, hash_password(payload.password)),
        )
        conn.commit()
        user_id = cur.fetchone()["id"]

    _send_verification_email(user_id, email)
    token = create_session(user_id)
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
    return {"ok": True, "email": email, "token": token, "user": _user_public(dict(row))}


@app.post("/api/auth/login")
async def login(payload: AuthPayload, request: Request):
    email = payload.email.strip().lower()
    _rate_limiter.check(f"login:{_client_ip(request)}", limit=10, window_seconds=300)
    _rate_limiter.check(f"login:{email}", limit=10, window_seconds=300)
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = %s", (email,)).fetchone()
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı")
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

    keys = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [current_user["id"]]
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {keys} WHERE id = %s", values)
        conn.commit()
        row = dict(conn.execute("SELECT * FROM users WHERE id = %s", (current_user["id"],)).fetchone())

    return {"user": _user_public(row)}


@app.post("/api/auth/change-password")
async def change_password(payload: PasswordPayload, current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = %s", (current_user["id"],)
        ).fetchone()
    if not row or not verify_password(payload.current_password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Mevcut şifre yanlış")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalı")

    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
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
async def verify_email(payload: VerifyEmailPayload, request: Request):
    email = payload.email.strip().lower()
    code = payload.code.strip()
    # 6 haneli kod, uzun rastgele token'a gore çok daha kucuk bir olasilik
    # uzayina sahip - deneme yanilma (brute-force) ile tahmin edilebilmesini
    # engellemek icin hem IP hem e-posta bazinda sinirlandiriyoruz.
    _rate_limiter.check(f"verify-email:{_client_ip(request)}", limit=10, window_seconds=900)
    _rate_limiter.check(f"verify-email:{email}", limit=10, window_seconds=900)

    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT ev.token, ev.user_id, ev.created_at
            FROM email_verifications ev
            JOIN users u ON u.id = ev.user_id
            WHERE u.email = %s AND ev.code = %s
            ORDER BY ev.created_at DESC LIMIT 1
            """,
            (email, code),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Kod geçersiz")

        created_at = datetime.fromisoformat(row["created_at"]).replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - created_at > timedelta(hours=EMAIL_VERIFICATION_TTL_HOURS):
            conn.execute("DELETE FROM email_verifications WHERE token = %s", (row["token"],))
            conn.commit()
            raise HTTPException(status_code=410, detail="Kodun süresi dolmuş - yeni bir kod talep et")

        user_id = row["user_id"]
        conn.execute("UPDATE users SET email_verified = 1 WHERE id = %s", (user_id,))
        # Ayni kullanici icin bekleyen tum eski kodlari da temizle (ör. birden
        # fazla "tekrar gonder" denemesinden kalanlar).
        conn.execute("DELETE FROM email_verifications WHERE user_id = %s", (user_id,))
        conn.commit()
        user_row = dict(conn.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone())

    # Kod dogrulamasi, kayit sirasinda hic acilmamis olan oturumu burada acar -
    # kullanici boylece tekrar giris yapmadan direkt icer girer.
    session_token = create_session(user_id)
    return {"ok": True, "token": session_token, "user": _user_public(user_row)}


@app.post("/api/auth/resend-verification-public")
async def resend_verification_public(payload: ForgotPasswordPayload, request: Request):
    """Henuz giris yapamayan (dolayisiyla authed resend-verification'i
    cagiramayan) kullanicilar icin - forgot-password ile ayni enumeration
    onlemini kullanir: e-posta kayitli olsun olmasin ayni cevap doner."""
    email = payload.email.strip().lower()
    _rate_limiter.check(f"resend-verification:{_client_ip(request)}", limit=5, window_seconds=3600)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email_verified FROM users WHERE email = %s", (email,)
        ).fetchone()
        if row and not row["email_verified"]:
            _send_verification_email(row["id"], email)

    return {
        "ok": True,
        "message": "Eğer bu e-posta kayıtlıysa ve henüz doğrulanmadıysa, yeni bir doğrulama linki gönderildi",
    }


@app.post("/api/auth/forgot-password")
async def forgot_password(payload: ForgotPasswordPayload, request: Request):
    """Kayitli e-posta olsun olmasin ayni cevabi doner - boylece bir e-postanin
    sistemde kayitli olup olmadigi disaridan anlasilamaz (enumeration onlemi)."""
    email = payload.email.strip().lower()
    _rate_limiter.check(f"forgot-password:{_client_ip(request)}", limit=5, window_seconds=3600)
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = %s", (email,)).fetchone()
        if row:
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO password_resets (token, user_id) VALUES (%s, %s)", (token, row["id"])
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
async def reset_password(payload: ResetPasswordPayload, request: Request):
    _rate_limiter.check(f"reset-password:{_client_ip(request)}", limit=10, window_seconds=3600)
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalı")

    with get_conn() as conn:
        row = conn.execute(
            "SELECT user_id, used, created_at FROM password_resets WHERE token = %s",
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
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hash_password(payload.new_password), row["user_id"]),
        )
        conn.execute("UPDATE password_resets SET used = 1 WHERE token = %s", (payload.token,))
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
                "SELECT id FROM jobs WHERE user_id = %s", (current_user["id"],)
            ).fetchall()
        ]

    # Dosyalar DB kaydi silinmeden ONCE temizlenir - islem yarida (crash/deploy)
    # kesilirse hesap hala var olur ve silme tekrar denenebilir; ters sirada
    # yapilsaydi DB kaydi gidip dosyalar sahipsiz kalabilirdi (hicbir yerden
    # bulunup temizlenemezdi).
    for job_id in job_ids:
        shutil.rmtree(OUTPUT_DIR / job_id, ignore_errors=True)
        for f in UPLOAD_DIR.glob(f"{job_id}_*"):
            f.unlink(missing_ok=True)
        if storage.is_enabled():
            storage.delete_prefix(f"uploads/{job_id}/")
            storage.delete_prefix(f"outputs/{job_id}/")

    with get_conn() as conn:
        # sessions/jobs, users tablosundaki ON DELETE CASCADE sayesinde
        # otomatik siliniyor.
        conn.execute("DELETE FROM users WHERE id = %s", (current_user["id"],))
        conn.commit()

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
            "INSERT INTO organizations (id, name, owner_id) VALUES (%s, %s, %s)",
            (org_id, name, current_user["id"]),
        )
        conn.execute(
            "INSERT INTO org_members (org_id, user_id, role) VALUES (%s, %s, 'owner')",
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
            WHERE org_members.org_id = %s
            ORDER BY (org_members.role = 'owner') DESC, org_members.joined_at ASC
            """,
            (org["id"],),
        ).fetchall()
        invites = []
        if org["role"] == "owner":
            invites = conn.execute(
                "SELECT token, email, created_at FROM org_invites WHERE org_id = %s ORDER BY created_at DESC",
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
            WHERE org_members.org_id = %s AND users.email = %s
            """,
            (org["id"], email),
        ).fetchone()
        if existing_member:
            raise HTTPException(status_code=409, detail="Bu kişi zaten ekipte")

        token = uuid.uuid4().hex
        conn.execute(
            "INSERT INTO org_invites (token, org_id, email) VALUES (%s, %s, %s)",
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
        conn.execute("DELETE FROM org_invites WHERE token = %s AND org_id = %s", (token, org["id"]))
        conn.commit()
    return {"ok": True}


@app.post("/api/org/accept-invite")
async def accept_invite(payload: AcceptInvitePayload, current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        invite = conn.execute("SELECT * FROM org_invites WHERE token = %s", (payload.token,)).fetchone()
    if not invite:
        raise HTTPException(status_code=404, detail="Davet geçersiz veya süresi dolmuş")
    invite = dict(invite)

    if invite["email"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Bu davet başka bir e-posta adresi için gönderilmiş")
    if _get_user_org(current_user["id"]):
        raise HTTPException(status_code=409, detail="Zaten bir ekibin var, önce ondan ayrılmalısın")

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO org_members (org_id, user_id, role) VALUES (%s, %s, 'member')",
            (invite["org_id"], current_user["id"]),
        )
        conn.execute("DELETE FROM org_invites WHERE token = %s", (payload.token,))
        conn.commit()
        org_row = conn.execute("SELECT name FROM organizations WHERE id = %s", (invite["org_id"],)).fetchone()

    return {"org_id": invite["org_id"], "org_name": org_row["name"] if org_row else None}


@app.delete("/api/org/members/{member_id}")
async def remove_member(member_id: int, current_user: dict = Depends(get_current_user)):
    org = _get_user_org(current_user["id"])
    if not org or org["role"] != "owner":
        raise HTTPException(status_code=403, detail="Sadece ekip sahibi üye çıkarabilir")
    if member_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Kendini çıkaramazsın")
    with get_conn() as conn:
        conn.execute("DELETE FROM org_members WHERE org_id = %s AND user_id = %s", (org["id"], member_id))
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
        conn.execute("DELETE FROM org_members WHERE org_id = %s AND user_id = %s", (org["id"], current_user["id"]))
        conn.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Odeme / Abonelik (iyzico)
# ---------------------------------------------------------------------------


@app.get("/api/payments/plans")
async def payment_plans():
    """Odeme sayfasinin gosterecegi satin alinabilir planlar - iyzico
    fiyatlandirma plani kodu .env'de tanimli degilse o plan listelenmez
    (henuz kurulmamis demektir)."""
    return {
        "plans": [
            {
                "id": plan_id,
                "label": payments.PLAN_LABELS[plan_id],
                "price_try": payments.PLAN_PRICES_TL[plan_id],
                "price_usd": payments.PLAN_PRICES_USD[plan_id],
            }
            for plan_id in ("yaratici", "ajans")
            if payments.plan_is_purchasable(plan_id)
        ]
    }


@app.get("/api/payments/status")
async def payment_status(current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT plan, status, created_at, updated_at FROM subscriptions
            WHERE user_id = %s ORDER BY created_at DESC LIMIT 1
            """,
            (current_user["id"],),
        ).fetchone()
    return {"plan": current_user["plan"], "subscription": row}


@app.post("/api/payments/checkout")
async def create_checkout(payload: CheckoutPayload, current_user: dict = Depends(get_current_user)):
    _rate_limiter.check(f"checkout:{current_user['id']}", limit=10, window_seconds=3600)
    if not payments.is_configured():
        raise HTTPException(status_code=503, detail="Ödeme sistemi henüz yapılandırılmadı")
    if not payments.plan_is_purchasable(payload.plan):
        raise HTTPException(status_code=400, detail="Geçersiz plan")
    if not payload.phone.strip():
        raise HTTPException(status_code=400, detail="Telefon zorunlu")

    conversation_id = f"sub-{current_user['id']}-{uuid.uuid4().hex[:10]}"
    callback_url = f"{BACKEND_URL}/api/payments/callback"
    try:
        data = await run_in_threadpool(
            payments.create_checkout_form,
            plan=payload.plan,
            conversation_id=conversation_id,
            callback_url=callback_url,
            buyer={
                "name": payload.name.strip(),
                "surname": payload.surname.strip(),
                "email": current_user["email"],
                "phone": payload.phone.strip(),
                "identity_number": (payload.identity_number or "").strip() or "11111111111",
                "address": payload.address.strip(),
                "city": payload.city.strip(),
                "zip_code": (payload.zip_code or "").strip(),
            },
        )
    except payments.PaymentError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO subscriptions (user_id, plan, status, conversation_id, checkout_token, iyzico_pricing_plan_code)
            VALUES (%s, %s, 'pending', %s, %s, %s)
            """,
            (current_user["id"], payload.plan, conversation_id, data.get("token"), payments.PRICING_PLAN_CODES[payload.plan]),
        )
        conn.commit()

    return {"token": data.get("token"), "checkout_form_content": data.get("checkoutFormContent")}


@app.post("/api/payments/callback")
async def payment_callback(request: Request):
    """iyzico'nun odeme sonrasi kullanicinin tarayicisini (form POST ile)
    geri gonderdigi adres - oturum tokeni tasimaz, bu yuzden auth gerektirmez;
    dogrulama daha once /api/payments/checkout sirasinda kaydedilen
    checkout_token uzerinden yapilir."""
    form = await request.form()
    token = form.get("token")
    if not token:
        return RedirectResponse(f"{FRONTEND_URL}/odeme/sonuc?durum=basarisiz", status_code=302)

    with get_conn() as conn:
        sub_row = conn.execute(
            "SELECT * FROM subscriptions WHERE checkout_token = %s", (token,)
        ).fetchone()

    if not sub_row:
        logger.warning("[iyzico] bilinmeyen checkout token ile callback: %s", token)
        return RedirectResponse(f"{FRONTEND_URL}/odeme/sonuc?durum=basarisiz", status_code=302)

    try:
        data = await run_in_threadpool(payments.retrieve_checkout_form, token)
    except payments.PaymentError as exc:
        logger.error("[iyzico] checkout form retrieve basarisiz: %s", exc)
        with get_conn() as conn:
            conn.execute(
                "UPDATE subscriptions SET status = 'failed', updated_at = NOW() WHERE id = %s",
                (sub_row["id"],),
            )
            conn.commit()
        return RedirectResponse(f"{FRONTEND_URL}/odeme/sonuc?durum=basarisiz", status_code=302)

    sub_status, sub_ref_code, customer_ref_code = payments.extract_subscription_status(data)
    logger.info(
        "[iyzico] callback token=%s durum=%s sub_ref=%s ham=%s",
        token, sub_status, sub_ref_code, data.get("_raw", "")[:1000],
    )
    # NOT: data["status"]=="success" burada SADECE iyzico API cagrisinin
    # kendisinin basarili oldugunu gosterir (ag/kimlik dogrulama basarili) -
    # karttan cekimin/aboneligin gercekten basarili oldugunu GOSTERMEZ (bu
    # yuzden burada kontrol edilmiyor). Gercek sonuc yalnizca sub_status'a
    # bakilarak belirlenir; alan adi bilinmiyorsa (sandbox hesabi olmadan
    # kesinlestirilemedi) guvenli taraf secilir: aktif SAYILMAZ, ham yanit
    # yukarida loglanir - ilk gercek denemeden sonra tek satirla duzeltilir.
    is_active = (sub_status or "").upper() in ("ACTIVE", "SUCCESS")

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE subscriptions
            SET status = %s, iyzico_subscription_code = %s, iyzico_customer_code = %s,
                raw_response = %s, updated_at = NOW()
            WHERE id = %s
            """,
            ("active" if is_active else "failed", sub_ref_code, customer_ref_code, data.get("_raw"), sub_row["id"]),
        )
        if is_active:
            conn.execute("UPDATE users SET plan = %s WHERE id = %s", (sub_row["plan"], sub_row["user_id"]))
        conn.commit()

    durum = "basarili" if is_active else "basarisiz"
    return RedirectResponse(f"{FRONTEND_URL}/odeme/sonuc?durum={durum}", status_code=302)


@app.post("/api/payments/cancel")
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM subscriptions WHERE user_id = %s AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
            """,
            (current_user["id"],),
        ).fetchone()
    if not row or not row.get("iyzico_subscription_code"):
        raise HTTPException(status_code=404, detail="Aktif bir aboneliğin yok")

    try:
        await run_in_threadpool(payments.cancel_subscription, row["iyzico_subscription_code"])
    except payments.PaymentError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    with get_conn() as conn:
        conn.execute("UPDATE subscriptions SET status = 'canceled', updated_at = NOW() WHERE id = %s", (row["id"],))
        conn.execute("UPDATE users SET plan = 'ucretsiz' WHERE id = %s", (current_user["id"],))
        conn.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Sosyal medya baglantilari (YouTube)
# ---------------------------------------------------------------------------

YOUTUBE_REDIRECT_URI = f"{BACKEND_URL}/api/social/youtube/callback"


class PublishYoutubePayload(BaseModel):
    title: str
    description: str | None = None


@app.get("/api/social/status")
async def social_status(current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT account_name FROM social_connections WHERE user_id = %s AND platform = 'youtube'",
            (current_user["id"],),
        ).fetchone()
    return {"youtube": {"connected": bool(row), "account_name": row["account_name"] if row else None}}


@app.get("/api/social/youtube/connect")
async def youtube_connect(current_user: dict = Depends(get_current_user)):
    if not social_youtube.is_configured():
        raise HTTPException(status_code=503, detail="YouTube bağlantısı henüz yapılandırılmadı")
    state = secrets.token_urlsafe(24)
    with get_conn() as conn:
        conn.execute("DELETE FROM oauth_states WHERE created_at < NOW() - INTERVAL '15 minutes'")
        conn.execute(
            "INSERT INTO oauth_states (state, user_id, platform) VALUES (%s, %s, 'youtube')",
            (state, current_user["id"]),
        )
        conn.commit()
    return {"url": social_youtube.build_auth_url(state, YOUTUBE_REDIRECT_URI)}


@app.get("/api/social/youtube/callback")
async def youtube_callback(request: Request):
    """Google'in OAuth sonrasi kullaniciyi (tarayici uzerinden) geri
    gonderdigi adres - oturum tokeni tasimaz, dogrulama 'state' parametresi
    uzerinden yapilir (bkz. /api/payments/callback ile ayni desen)."""
    params = request.query_params
    error = params.get("error")
    state = params.get("state")
    code = params.get("code")

    if error or not state or not code:
        return RedirectResponse(f"{FRONTEND_URL}/profil?youtube=basarisiz", status_code=302)

    with get_conn() as conn:
        state_row = conn.execute(
            "SELECT user_id FROM oauth_states WHERE state = %s AND platform = 'youtube'", (state,)
        ).fetchone()
        if state_row:
            conn.execute("DELETE FROM oauth_states WHERE state = %s", (state,))
            conn.commit()
    if not state_row:
        return RedirectResponse(f"{FRONTEND_URL}/profil?youtube=basarisiz", status_code=302)

    try:
        tokens = await run_in_threadpool(social_youtube.exchange_code, code, YOUTUBE_REDIRECT_URI)
        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token")
        channel_name = await run_in_threadpool(social_youtube.get_channel_name, access_token)
    except Exception as exc:
        logger.error("[youtube oauth] baglanti basarisiz: %s", exc)
        return RedirectResponse(f"{FRONTEND_URL}/profil?youtube=basarisiz", status_code=302)

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT refresh_token FROM social_connections WHERE user_id = %s AND platform = 'youtube'",
            (state_row["user_id"],),
        ).fetchone()
        # Google, kullanici zaten yetki vermisse refresh_token'i tekrar
        # gondermeyebilir - varsa eskisini koru.
        final_refresh = refresh_token or (existing["refresh_token"] if existing else None)
        conn.execute(
            """
            INSERT INTO social_connections (user_id, platform, account_name, access_token, refresh_token, token_expires_at)
            VALUES (%s, 'youtube', %s, %s, %s, %s)
            ON CONFLICT (user_id, platform) DO UPDATE SET
                account_name = EXCLUDED.account_name,
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                token_expires_at = EXCLUDED.token_expires_at,
                updated_at = NOW()
            """,
            (state_row["user_id"], channel_name, access_token, final_refresh, expires_at.isoformat()),
        )
        conn.commit()
    return RedirectResponse(f"{FRONTEND_URL}/profil?youtube=baglandi", status_code=302)


@app.delete("/api/social/youtube")
async def youtube_disconnect(current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM social_connections WHERE user_id = %s AND platform = 'youtube'",
            (current_user["id"],),
        )
        conn.commit()
    return {"ok": True}


def _get_youtube_access_token(user_id: int) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT access_token, refresh_token, token_expires_at FROM social_connections WHERE user_id = %s AND platform = 'youtube'",
            (user_id,),
        ).fetchone()
    if not row or not row.get("refresh_token"):
        raise HTTPException(status_code=409, detail="YouTube hesabın bağlı değil, önce profil sayfasından bağla")

    expires_at = row.get("token_expires_at")
    is_expired = True
    if expires_at:
        try:
            is_expired = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc)
        except ValueError:
            is_expired = True
    if not is_expired and row.get("access_token"):
        return row["access_token"]

    try:
        tokens = social_youtube.refresh_access_token(row["refresh_token"])
    except social_youtube.SocialAuthError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    access_token = tokens["access_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
    with get_conn() as conn:
        conn.execute(
            "UPDATE social_connections SET access_token = %s, token_expires_at = %s, updated_at = NOW() WHERE user_id = %s AND platform = 'youtube'",
            (access_token, expires_at.isoformat(), user_id),
        )
        conn.commit()
    return access_token


@app.post("/api/jobs/{job_id}/clips/{clip_index}/publish/youtube")
async def publish_clip_youtube(
    job_id: str,
    clip_index: int,
    payload: PublishYoutubePayload,
    current_user: dict = Depends(get_current_user),
):
    """Bir klibi kullanicinin baglanmis YouTube kanalina Shorts olarak
    yukler. Dikey/60 saniyeden kisa videolar YouTube tarafindan otomatik
    Shorts sayilir."""
    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM jobs WHERE id = %s AND {scope_sql}", (job_id, *scope_params)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bulunamadı")

    clips = json.loads(row["clips_json"]) if row["clips_json"] else []
    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(status_code=404, detail="Klip bulunamadı")
    clip = clips[clip_index]
    if not clip.get("url"):
        raise HTTPException(status_code=409, detail="Bu klip için video dosyası yok")

    access_token = _get_youtube_access_token(current_user["id"])

    video_path, is_temp = await run_in_threadpool(_ensure_clip_local, clip["url"])
    if not video_path:
        raise HTTPException(status_code=409, detail="Klip dosyasına ulaşılamadı")

    try:
        video_id = await run_in_threadpool(
            social_youtube.upload_short,
            access_token,
            video_path,
            payload.title,
            payload.description or "",
        )
    except social_youtube.SocialAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        if is_temp:
            video_path.unlink(missing_ok=True)

    video_url = f"https://youtube.com/shorts/{video_id}"
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO published_videos (user_id, job_id, clip_index, platform, video_id, video_url, title)
            VALUES (%s, %s, %s, 'youtube', %s, %s, %s)
            """,
            (current_user["id"], job_id, clip_index, video_id, video_url, payload.title),
        )
        conn.commit()

    return {"ok": True, "video_id": video_id, "url": video_url}


@app.get("/api/social/published")
async def social_published(current_user: dict = Depends(get_current_user)):
    """Kullanicinin daha once yukledigi videolarin listesi - YouTube icin
    guncel izlenme/begeni sayilari canli olarak sorgulanir."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM published_videos WHERE user_id = %s ORDER BY created_at DESC LIMIT 100",
            (current_user["id"],),
        ).fetchall()
    if not rows:
        return {"videos": []}

    stats: dict = {}
    youtube_ids = [r["video_id"] for r in rows if r["platform"] == "youtube"]
    if youtube_ids:
        try:
            access_token = _get_youtube_access_token(current_user["id"])
            stats = await run_in_threadpool(social_youtube.get_video_stats, access_token, youtube_ids)
        except Exception:
            stats = {}

    videos = []
    for r in rows:
        video_stats = stats.get(r["video_id"], {})
        videos.append(
            {
                "id": r["id"],
                "platform": r["platform"],
                "video_id": r["video_id"],
                "video_url": r["video_url"],
                "title": r["title"],
                "thumbnail_url": f"https://i.ytimg.com/vi/{r['video_id']}/hqdefault.jpg"
                if r["platform"] == "youtube"
                else None,
                "created_at": r["created_at"],
                "view_count": video_stats.get("view_count"),
                "like_count": video_stats.get("like_count"),
            }
        )
    return {"videos": videos}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

# Bir videoya elle eklenebilecek (AI'nin urettigi + kullanicinin manuel
# eklediği) toplam klip sayisi ust siniri - depolama/kotuye kullanim
# koruması.
MAX_CLIPS_PER_JOB = 15


def _set_job(job_id: str, **fields):
    keys = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [job_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {keys} WHERE id = %s", values)
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
        return _upload_output(job_id, srt_path)
    except Exception as e:
        logger.warning("[ingilizce altyazi uretimi basarisiz] job=%s name=%s: %s", job_id, name, e)
        return None


# Ayni anda islenen video (transcribe+ffmpeg, CPU-yogun) sayisini sinirlar -
# SQLite yazma kilitlenmelerini ve tek worker'da kaynak (CPU/bellek) tukenmesini
# onlemek icin. Sinira ulasildiginda yeni isler "queued" durumunda bekler,
# sira acildikca islenmeye baslar. Gercek bir mesaj kuyrugunun (Redis/Celery)
# yerini tutmaz ama tek-process deploy icin orantili bir onlem.
MAX_CONCURRENT_JOBS = int(os.environ.get("MAX_CONCURRENT_JOBS", "2"))
_pipeline_semaphore = threading.BoundedSemaphore(MAX_CONCURRENT_JOBS)


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
    subtitle_animation: str = DEFAULT_SUBTITLE_ANIMATION,
    highlight_color: str = DEFAULT_HIGHLIGHT_COLOR,
    overlay_url: str | None = None,
    overlay_x: float = DEFAULT_OVERLAY_X,
    overlay_y: float = DEFAULT_OVERLAY_Y,
    overlay_scale: str = DEFAULT_OVERLAY_SCALE,
):
    with _pipeline_semaphore:
        _run_pipeline_locked(
            job_id, video_path, style, remove_fillers, max_clips, min_duration, max_duration,
            subtitle_color, subtitle_position, aspect, subtitle_animation, highlight_color,
            overlay_url, overlay_x, overlay_y, overlay_scale,
        )


def _run_pipeline_locked(
    job_id: str,
    video_path: str,
    style: str,
    remove_fillers: bool,
    max_clips: float,
    min_duration: float,
    max_duration: float,
    subtitle_color: str,
    subtitle_position: str,
    aspect: str,
    subtitle_animation: str,
    highlight_color: str,
    overlay_url: str | None = None,
    overlay_x: float = DEFAULT_OVERLAY_X,
    overlay_y: float = DEFAULT_OVERLAY_Y,
    overlay_scale: str = DEFAULT_OVERLAY_SCALE,
):
    overlay_path, overlay_is_temp = _ensure_overlay_local(overlay_url)
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
        unload_whisper()  # ffmpeg adımı için RAM boşalt

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
                animation=subtitle_animation, highlight_color=highlight_color,
                overlay_path=overlay_path, overlay_x=overlay_x, overlay_y=overlay_y, overlay_scale=overlay_scale,
            )
            cover_path = make_cover(path, title, job_out_dir / f"{name}_cover.jpg")
            clip_url = _upload_output(job_id, path)
            cover_url = _upload_output(job_id, cover_path) if cover_path else None
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
                "url": clip_url,
                "cover_url": cover_url,
                "subtitles_en_url": subtitles_en_url,
                "style": style,
                "subtitle_color": subtitle_color,
                "subtitle_position": subtitle_position,
                "aspect": aspect,
                "subtitle_animation": subtitle_animation,
                "highlight_color": highlight_color,
                "remove_fillers": remove_fillers,
                "overlay_url": overlay_url,
                "overlay_x": overlay_x,
                "overlay_y": overlay_y,
                "overlay_scale": overlay_scale,
            })

        _set_job(job_id, status="done", clips_json=json.dumps(results))

        # Archive the original video to R2 and free local disk space.
        if storage.is_enabled():
            orig = Path(video_path)
            storage.upload(orig, f"uploads/{job_id}/{orig.name[len(job_id)+1:]}")
            orig.unlink(missing_ok=True)
    except Exception as e:
        # 'error' durumundaki isler _credits_used_this_month'da sayilmadigi
        # icin kredi zaten fiilen iade edilmis oluyor - ama kullaniciya bu
        # acikca soylenmezse "kredim bosa mi gitti" diye endiselenebilir,
        # bu yuzden hata mesajina bunu ekliyoruz.
        _set_job(job_id, status="error", error=f"{e} (Bu işlem için kredin harcanmadı.)")
    finally:
        if overlay_is_temp and overlay_path:
            shutil.rmtree(overlay_path.parent, ignore_errors=True)


def _resolve_clip_urls(clip: dict) -> dict:
    """Replace stored storage keys with usable (signed) URLs in a clip dict."""
    resolved = {**clip}
    for field in ("url", "cover_url", "subtitles_en_url", "overlay_url"):
        resolved[field] = storage.resolve_url(clip.get(field))
    resolved["translations"] = [
        {**t, "url": storage.resolve_url(t.get("url"))}
        for t in clip.get("translations", [])
    ]
    return resolved


def _job_to_dict(row: dict) -> dict:
    raw_clips = json.loads(row["clips_json"]) if row["clips_json"] else []
    return {
        "job_id": row["id"],
        "filename": row["filename"],
        "status": row["status"],
        "error": row["error"],
        "clips": [_resolve_clip_urls(c) for c in raw_clips],
        "style": row["style"],
        "remove_fillers": bool(row["remove_fillers"]),
        "language": row.get("language"),
        "subtitle_color": row.get("subtitle_color") or DEFAULT_SUBTITLE_COLOR,
        "subtitle_position": row.get("subtitle_position") or DEFAULT_SUBTITLE_POSITION,
        "aspect": row.get("aspect") or DEFAULT_ASPECT,
        "subtitle_animation": row.get("subtitle_animation") or DEFAULT_SUBTITLE_ANIMATION,
        "highlight_color": row.get("highlight_color") or DEFAULT_HIGHLIGHT_COLOR,
        "overlay_url": storage.resolve_url(row.get("overlay_url")),
        "overlay_x": row.get("overlay_x") if row.get("overlay_x") is not None else DEFAULT_OVERLAY_X,
        "overlay_y": row.get("overlay_y") if row.get("overlay_y") is not None else DEFAULT_OVERLAY_Y,
        "overlay_scale": row.get("overlay_scale") or DEFAULT_OVERLAY_SCALE,
        "credit_cost": row.get("credit_cost") or 0,
        "uploaded_by": row.get("uploaded_by_email"),
        "created_at": row["created_at"],
    }


def _start_processing_job(
    job_id: str,
    video_path: Path,
    filename: str,
    style: str,
    remove_fillers: bool,
    clip_count: int | None,
    min_duration: float | None,
    max_duration: float | None,
    subtitle_color: str | None,
    subtitle_position: str | None,
    aspect: str | None,
    subtitle_animation: str | None,
    highlight_color: str | None,
    overlay_url: str | None,
    overlay_x: float | None,
    overlay_y: float | None,
    overlay_scale: str | None,
    current_user: dict,
    background_tasks: BackgroundTasks,
) -> dict:
    """Diskte hazir duran bir video dosyasi icin (bilgisayardan yuklenmis veya
    bir linkten indirilmis farketmez) is (job) kaydini olusturur, kredi
    kontrolunu yapar ve arka plan islem hattini (run_pipeline) baslatir.
    /api/upload ve /api/upload-url tarafindan ORTAK kullanilir - boylece link
    ile yukleme, bilgisayardan yuklemeyle tamamen ayni is akisindan gecer.
    Herhangi bir dogrulama/kredi hatasinda, ceri kalmamasi icin video_path
    diskten silinir."""
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
                video_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="Klip sayısı 3 ile 8 arasında olmalı")
            max_clips = clip_count
        if min_duration is not None and max_duration is not None:
            if not (10 <= min_duration < max_duration <= 180):
                video_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="Klip süre aralığı geçersiz")
            dur_min, dur_max = min_duration, max_duration

    # Altyazi rengi/konumu ve en-boy orani tum planlarda acik - sadece
    # klip sayisi/suresi ucretli plana ozel (yukarida ayrica kontrol edildi).
    color, position, asp, anim, hcolor = _validate_render_options(
        subtitle_color, subtitle_position, aspect, subtitle_animation, highlight_color,
    )
    ovl_x, ovl_y, ovl_scale = _validate_overlay_options(overlay_x, overlay_y, overlay_scale)

    # Kredi maliyeti: video suresi (ffprobe ile okunur) ve secilen klip
    # sayisina gore hesaplanir - bkz. app/services/credits.py.
    duration_seconds = get_video_duration(str(video_path))
    cost = compute_credit_cost(duration_seconds, max_clips)

    limit = CREDIT_LIMITS.get(effective_plan, CREDIT_LIMITS["ucretsiz"])
    if False and limit is not None:  # KREDİ KONTROLİ GEÇİCİ OLARAK DEVRE DIŞI
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
            INSERT INTO jobs (id, user_id, filename, status, style, remove_fillers, subtitle_color, subtitle_position, aspect, subtitle_animation, highlight_color, overlay_url, overlay_x, overlay_y, overlay_scale, credit_cost, org_id)
            VALUES (%s, %s, %s, 'queued', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                job_id, current_user["id"], filename, style, int(remove_fillers),
                color, position, asp, anim, hcolor, overlay_url or None, ovl_x, ovl_y, ovl_scale,
                cost, org["id"] if org else None,
            ),
        )
        conn.commit()

    background_tasks.add_task(
        run_pipeline, job_id, str(video_path), style, remove_fillers, max_clips, dur_min, dur_max,
        color, position, asp, anim, hcolor, overlay_url or None, ovl_x, ovl_y, ovl_scale,
    )
    return {"job_id": job_id, "credit_cost": cost}


ALLOWED_LOGO_CONTENT_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
MAX_LOGO_BYTES = 5 * 1024 * 1024  # 5MB - kucuk bir logo/banner icin fazlasiyla yeterli


@app.post("/api/upload-logo")
async def upload_logo(file: UploadFile, current_user: dict = Depends(get_current_user)):
    """Klip uretiminde/duzenlemesinde bindirilecek logo/banner gorselini
    yukler, kaydeder ve /api/upload, /api/upload-url, retrim, add-clip
    endpoint'lerinde overlay_url olarak kullanilabilecek bir deger dondurur."""
    ext = ALLOWED_LOGO_CONTENT_TYPES.get(file.content_type or "")
    if not ext:
        raise HTTPException(status_code=400, detail="Sadece PNG, JPEG veya WEBP resim dosyaları desteklenir")
    data = await file.read(MAX_LOGO_BYTES + 1)
    if len(data) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=400, detail="Logo dosyası en fazla 5MB olabilir")
    if not data:
        raise HTTPException(status_code=400, detail="Boş dosya")

    name = f"{uuid.uuid4()}.{ext}"
    local_path = LOGO_DIR / name

    def _save() -> str:
        with open(local_path, "wb") as f:
            f.write(data)
        if storage.is_enabled():
            key = f"logos/{name}"
            url = storage.upload(local_path, key)
            local_path.unlink(missing_ok=True)
            return url
        return f"/files/logos/{name}"

    url = await run_in_threadpool(_save)
    return {"url": url}


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
    subtitle_animation: str | None = Form(None),
    highlight_color: str | None = Form(None),
    overlay_url: str | None = Form(None),
    overlay_x: float | None = Form(None),
    overlay_y: float | None = Form(None),
    overlay_scale: str | None = Form(None),
    current_user: dict = Depends(get_current_user),
):
    if shutil.disk_usage(UPLOAD_DIR).free < MIN_FREE_DISK_BYTES:
        raise HTTPException(status_code=507, detail="Sunucuda şu an yeterli depolama alanı yok - lütfen daha sonra tekrar dene")

    job_id = str(uuid.uuid4())
    safe_filename = _safe_filename(file.filename)
    video_path = UPLOAD_DIR / f"{job_id}_{safe_filename}"

    def _write_upload():
        with open(video_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

    # Buyuk bir dosyayi diske yazmak saniyeler surebilir - bunu threadpool'a
    # atmazsak (senkron/bloklayici sekilde burada calistirirsak) event loop'u
    # (dolayisiyla o sirada gelen diger TUM kullanicilarin istekleri) o sure
    # boyunca bloklardi. _start_processing_job da (ffprobe + DB sorgulari)
    # ayni sebeple threadpool'a atiliyor.
    await run_in_threadpool(_write_upload)

    return await run_in_threadpool(
        _start_processing_job,
        job_id, video_path, safe_filename, style, remove_fillers, clip_count, min_duration, max_duration,
        subtitle_color, subtitle_position, aspect, subtitle_animation, highlight_color,
        overlay_url, overlay_x, overlay_y, overlay_scale,
        current_user, background_tasks,
    )


@app.post("/api/upload-url")
async def upload_video_from_url(
    payload: UploadUrlPayload,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Kullanicinin bilgisayarindan dosya yuklemesi yerine bir YouTube (veya
    yt-dlp'nin destekledigi baska bir site) linki yapistirarak video
    yuklemesini saglar. Indirilen video, /api/upload ile TAMAMEN AYNI is
    akisindan (_start_processing_job) gecer - yani sanki bilgisayardan
    yuklenmis gibi ayni kredi hesaplamasi ve klip uretim hatti calisir."""
    job_id = str(uuid.uuid4())
    try:
        # download_video senkron/bloklayici bir ag cagrisi (yt-dlp) - buyuk bir
        # video icin dakikalarca surebilir; threadpool'a atmazsak tum event
        # loop'u (dolayisiyla o sirada gelen diger TUM istekleri) bloklardi.
        video_path, title = await run_in_threadpool(download_video, payload.url, UPLOAD_DIR, job_id)
    except VideoUrlError as e:
        raise HTTPException(status_code=400, detail=str(e))

    style = payload.style if payload.style else DEFAULT_STYLE
    remove_fillers = payload.remove_fillers if payload.remove_fillers is not None else True
    # ONEMLI: filename olarak video_path.name'den job_id on ekini cikarip kullaniyoruz
    # (title'dan degil) - cunku diger endpoint'ler (source, retrim, add-clip, indirme)
    # orijinal videoyu UPLOAD_DIR / f"{job_id}_{row['filename']}" seklinde diskten
    # yeniden buluyor. yt-dlp restrictfilenames=True ile guvenli/sanitize edilmis bir
    # dosya adi kullaniyor (title'daki Turkce karakterler, parantezler vb. degisebiliyor),
    # bu yuzden DB'ye title yerine diskteki GERCEK sanitize edilmis adi yazmazsak o
    # endpoint'ler dosyayi bulamiyor (404) - kirpma editorunde video hic yuklenmiyordu.
    display_filename = video_path.name[len(job_id) + 1:]

    return await run_in_threadpool(
        _start_processing_job,
        job_id, video_path, display_filename, style, remove_fillers, payload.clip_count,
        payload.min_duration, payload.max_duration, payload.subtitle_color,
        payload.subtitle_position, payload.aspect, payload.subtitle_animation,
        payload.highlight_color, payload.overlay_url, payload.overlay_x, payload.overlay_y,
        payload.overlay_scale, current_user, background_tasks,
    )


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, current_user: dict = Depends(get_current_user)):
    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM jobs WHERE id = %s AND {scope_sql}", (job_id, *scope_params)
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
            f"SELECT * FROM jobs WHERE id = %s AND {scope_sql}", (job_id, *scope_params)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    row = dict(row)

    video_path = UPLOAD_DIR / f"{job_id}_{row['filename']}"
    if not video_path.exists():
        if storage.is_enabled():
            r2_url = storage.public_url(f"uploads/{job_id}/{row['filename']}")
            return RedirectResponse(url=r2_url, status_code=302)
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
            f"SELECT * FROM jobs WHERE id = %s AND {scope_sql}", (job_id, *scope_params)
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

    video_path, _is_temp_retrim = _ensure_original_local(job_id, row["filename"])
    if not video_path.exists():
        raise HTTPException(status_code=409, detail="Orijinal video dosyası bulunamadı")

    clips = json.loads(row["clips_json"]) if row["clips_json"] else []
    if clip_index < 0 or clip_index >= len(clips):
        if _is_temp_retrim:
            shutil.rmtree(video_path.parent, ignore_errors=True)
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
    anim = _resolve_clip_option(
        payload.subtitle_animation, lambda v: v in SUBTITLE_ANIMATIONS,
        existing_clip, "subtitle_animation", row, "subtitle_animation", DEFAULT_SUBTITLE_ANIMATION,
    )
    hcolor = _resolve_clip_option(
        payload.highlight_color, lambda v: bool(HEX_COLOR_RE.match(v)),
        existing_clip, "highlight_color", row, "highlight_color", DEFAULT_HIGHLIGHT_COLOR,
    )
    # overlay_url: "" = bindirmeyi kaldir, dolu bir deger = yenisiyle degistir,
    # None (hic gonderilmemis) = mevcut klibin (yoksa isin) degerini koru.
    if payload.overlay_url == "":
        overlay_url = None
    elif payload.overlay_url:
        overlay_url = payload.overlay_url
    else:
        overlay_url = existing_clip.get("overlay_url") or row.get("overlay_url")
    # overlay_x/overlay_y icin 0.0 (kirpma karesinin sol/ust kenari) da gecerli
    # bir deger oldugundan (falsy), "or" degil acik None kontrolu kullaniyoruz.
    overlay_x = (
        payload.overlay_x if payload.overlay_x is not None
        else existing_clip.get("overlay_x") if existing_clip.get("overlay_x") is not None
        else row.get("overlay_x")
    )
    overlay_y = (
        payload.overlay_y if payload.overlay_y is not None
        else existing_clip.get("overlay_y") if existing_clip.get("overlay_y") is not None
        else row.get("overlay_y")
    )
    overlay_x, overlay_y, overlay_scale = _validate_overlay_options(
        overlay_x, overlay_y,
        payload.overlay_scale or existing_clip.get("overlay_scale") or row.get("overlay_scale"),
    )
    name = f"clip_{clip_index + 1}"
    job_out_dir = OUTPUT_DIR / job_id

    overlay_path, overlay_is_temp = _ensure_overlay_local(overlay_url)
    try:
        path = make_vertical_clip(
            str(video_path), payload.start, payload.end, all_words, job_out_dir, name,
            style=style, remove_fillers=remove_fillers,
            subtitle_color=color, position=position, aspect=asp, animation=anim,
            highlight_color=hcolor,
            overlay_path=overlay_path, overlay_x=overlay_x, overlay_y=overlay_y, overlay_scale=overlay_scale,
        )
        cover_path = make_cover(path, clips[clip_index].get("title", name), job_out_dir / f"{name}_cover.jpg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yeniden oluşturma başarısız: {e}")
    finally:
        if _is_temp_retrim:
            shutil.rmtree(video_path.parent, ignore_errors=True)
        if overlay_is_temp and overlay_path:
            shutil.rmtree(overlay_path.parent, ignore_errors=True)

    clip_url = _upload_output(job_id, path)
    cover_url = _upload_output(job_id, cover_path) if cover_path else None

    subtitles_en_url = None
    if row.get("language") != "en":
        subtitles_en_url = _generate_english_subtitles(
            all_words, payload.start, payload.end, style, remove_fillers,
            job_id, job_out_dir, name,
        )

    clips[clip_index] = {
        **clips[clip_index],
        "start": payload.start,
        "end": payload.end,
        "url": clip_url,
        "cover_url": cover_url,
        "subtitles_en_url": subtitles_en_url,
        "style": style,
        "subtitle_color": color,
        "subtitle_position": position,
        "aspect": asp,
        "subtitle_animation": anim,
        "highlight_color": hcolor,
        "remove_fillers": remove_fillers,
        "overlay_url": overlay_url,
        "overlay_x": overlay_x,
        "overlay_y": overlay_y,
        "overlay_scale": overlay_scale,
    }

    with get_conn() as conn:
        conn.execute("UPDATE jobs SET clips_json = %s WHERE id = %s", (json.dumps(clips), job_id))
        conn.commit()

    return _resolve_clip_urls(clips[clip_index])


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
            f"SELECT * FROM jobs WHERE id = %s AND {scope_sql}", (job_id, *scope_params)
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

    video_path, _is_temp_addclip = _ensure_original_local(job_id, row["filename"])
    if not video_path.exists():
        raise HTTPException(status_code=409, detail="Orijinal video dosyası bulunamadı")

    clips = json.loads(row["clips_json"]) if row["clips_json"] else []
    if len(clips) >= MAX_CLIPS_PER_JOB:
        if _is_temp_addclip:
            shutil.rmtree(video_path.parent, ignore_errors=True)
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
    if False and limit is not None:  # KREDİ KONTROLİ GEÇİCİ OLARAK DEVRE DIŞI
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
    anim = _resolve_clip_option(
        payload.subtitle_animation, lambda v: v in SUBTITLE_ANIMATIONS, {}, "subtitle_animation", row, "subtitle_animation", DEFAULT_SUBTITLE_ANIMATION,
    )
    hcolor = _resolve_clip_option(
        payload.highlight_color, lambda v: bool(HEX_COLOR_RE.match(v)), {}, "highlight_color", row, "highlight_color", DEFAULT_HIGHLIGHT_COLOR,
    )
    if payload.overlay_url == "":
        overlay_url = None
    else:
        overlay_url = payload.overlay_url or row.get("overlay_url")
    overlay_x = payload.overlay_x if payload.overlay_x is not None else row.get("overlay_x")
    overlay_y = payload.overlay_y if payload.overlay_y is not None else row.get("overlay_y")
    overlay_x, overlay_y, overlay_scale = _validate_overlay_options(
        overlay_x, overlay_y,
        payload.overlay_scale or row.get("overlay_scale"),
    )
    index = len(clips)
    name = f"clip_{index + 1}"
    job_out_dir = OUTPUT_DIR / job_id
    title = (payload.title or "").strip() or "Manuel klip"

    overlay_path, overlay_is_temp = _ensure_overlay_local(overlay_url)
    try:
        path = make_vertical_clip(
            str(video_path), payload.start, payload.end, all_words, job_out_dir, name,
            style=style, remove_fillers=remove_fillers,
            subtitle_color=color, position=position, aspect=asp, animation=anim,
            highlight_color=hcolor,
            overlay_path=overlay_path, overlay_x=overlay_x, overlay_y=overlay_y, overlay_scale=overlay_scale,
        )
        cover_path = make_cover(path, title, job_out_dir / f"{name}_cover.jpg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Klip oluşturulamadı: {e}")
    finally:
        if _is_temp_addclip:
            shutil.rmtree(video_path.parent, ignore_errors=True)
        if overlay_is_temp and overlay_path:
            shutil.rmtree(overlay_path.parent, ignore_errors=True)

    clip_url = _upload_output(job_id, path)
    cover_url = _upload_output(job_id, cover_path) if cover_path else None

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
        "url": clip_url,
        "cover_url": cover_url,
        "subtitles_en_url": subtitles_en_url,
        "manual": True,
        "style": style,
        "subtitle_color": color,
        "subtitle_position": position,
        "aspect": asp,
        "subtitle_animation": anim,
        "highlight_color": hcolor,
        "remove_fillers": remove_fillers,
        "overlay_url": overlay_url,
        "overlay_x": overlay_x,
        "overlay_y": overlay_y,
        "overlay_scale": overlay_scale,
    }
    clips.append(new_clip)

    with get_conn() as conn:
        conn.execute(
            "UPDATE jobs SET clips_json = %s, credit_cost = credit_cost + %s WHERE id = %s",
            (json.dumps(clips), added_cost, job_id),
        )
        conn.commit()

    return {"clip": _resolve_clip_urls(new_clip), "clips": [_resolve_clip_urls(c) for c in clips], "added_cost": added_cost}


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
            f"SELECT * FROM jobs WHERE id = %s AND {scope_sql}", (job_id, *scope_params)
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

    job_out_dir = (OUTPUT_DIR / job_id).resolve()
    for field in ("url", "cover_url", "subtitles_en_url"):
        url = clip.get(field)
        if not url:
            continue
        if storage.is_enabled():
            r2_key = storage.key_from_url(url)
            if r2_key:
                storage.delete(r2_key)
        else:
            fname = _safe_filename(url.split("/")[-1].split("?")[0])
            target = (job_out_dir / fname).resolve()
            if target.parent == job_out_dir:
                target.unlink(missing_ok=True)

    clips.pop(clip_index)
    with get_conn() as conn:
        conn.execute("UPDATE jobs SET clips_json = %s WHERE id = %s", (json.dumps(clips), job_id))
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
            f"SELECT * FROM jobs WHERE id = %s AND {scope_sql}", (job_id, *scope_params)
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
        translated = await run_in_threadpool(translate_subtitles, [c["text"] for c in chunks], lang_label)
        for c, t in zip(chunks, translated):
            c["text"] = t
        srt_path = job_out_dir / f"{name}_{payload.language}.srt"
        write_srt(chunks, srt_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Çeviri başarısız: {e}")

    url = _upload_output(job_id, srt_path)
    translations = [t for t in clip.get("translations", []) if t.get("language") != payload.language]
    translations.append({"language": payload.language, "label": lang_label, "url": url})
    clips[clip_index] = {**clip, "translations": translations}

    with get_conn() as conn:
        conn.execute("UPDATE jobs SET clips_json = %s WHERE id = %s", (json.dumps(clips), job_id))
        conn.commit()

    return _resolve_clip_urls(clips[clip_index])


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
            f"SELECT * FROM jobs WHERE id = %s AND {scope_sql}", (job_id, *scope_params)
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
        result = await run_in_threadpool(generate_social_caption, transcript_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Paylaşım metni oluşturulamadı: {e}")

    clips[clip_index] = {**clip, "social_caption": result["caption"], "social_hashtags": result["hashtags"]}

    with get_conn() as conn:
        conn.execute("UPDATE jobs SET clips_json = %s WHERE id = %s", (json.dumps(clips), job_id))
        conn.commit()

    return _resolve_clip_urls(clips[clip_index])


@app.get("/api/subtitle-languages")
async def subtitle_languages():
    return [{"id": key, "label": label} for key, label in SUBTITLE_LANGUAGES.items()]


@app.get("/api/caption-styles")
async def caption_styles():
    return {key: preset["label"] for key, preset in STYLE_PRESETS.items()}


@app.get("/api/caption-style-presets")
async def caption_style_presets():
    """caption-styles'in genisletilmis hali - profesyonel klip editorunun
    altyazi onizlemesini (kelimeleri kac kelimelik gruplar halinde gostermesi
    gerektigini) gercek render mantigiyla (STYLE_PRESETS[...]["chunk_size"])
    birebir tutarli kurabilmesi icin chunk_size de donduruluyor."""
    return {
        key: {"label": preset["label"], "chunk_size": preset["chunk_size"]}
        for key, preset in STYLE_PRESETS.items()
    }


@app.get("/api/jobs/{job_id}/words")
async def job_words(job_id: str, current_user: dict = Depends(get_current_user)):
    """Bu isin kelime bazli transkriptini (baslangic/bitis zaman damgalariyla)
    dondurur - profesyonel klip editorunde, kullanici videoyu oynatirken
    henuz yakilmamis altyazinin canli bir onizlemesini gosterebilmek icin
    kullanilir. Isin sahibi veya (is bir ekibe aitse) ekibin tum uyeleri
    erisebilir."""
    org = _get_user_org(current_user["id"])
    scope_sql, scope_params = _job_scope(current_user, org)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM jobs WHERE id = %s AND {scope_sql}", (job_id, *scope_params)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    row = dict(row)
    words_json = row.get("words_json")
    return {"words": json.loads(words_json) if words_json else []}


@app.get("/api/render-options")
async def render_options():
    """Yukleme panelinde gosterilecek altyazi rengi, altyazi konumu ve
    klip en-boy orani secenekleri - hepsi tum planlarda acik."""
    return {
        "aspects": [{"id": key, "label": preset["label"]} for key, preset in ASPECT_PRESETS.items()],
        "positions": [{"id": key, "label": preset["label"]} for key, preset in SUBTITLE_POSITIONS.items()],
        "colors": SUBTITLE_COLOR_PRESETS,
        "animations": [{"id": key, "label": preset["label"]} for key, preset in SUBTITLE_ANIMATIONS.items()],
        "overlayScales": [{"id": key, "label": preset["label"]} for key, preset in OVERLAY_SCALES.items()],
        "overlayDefaultX": DEFAULT_OVERLAY_X,
        "overlayDefaultY": DEFAULT_OVERLAY_Y,
        "credits": {"base": CREDIT_COST_BASE, "per_clip": CREDIT_COST_PER_CLIP},
    }


def _require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """/api/admin/* uc noktalarini korur - normal kullanici oturumuyla degil,
    sadece Railway'e ADMIN_API_KEY olarak tanimlanan gizli anahtari X-Admin-Key
    basligiyla gonderenler erisebilir. Anahtar tanimli degilse uc nokta
    tamamen kapali sayilir (yanlislikla acik kalmasin diye)."""
    if not ADMIN_API_KEY or not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=404, detail="Bulunamadı")


DEMO_MAX_DAYS = 60


class DemoAccountPayload(BaseModel):
    email: str
    plan: str = "yaratici"
    days: int = 7


@app.post("/api/admin/demo-account", dependencies=[Depends(_require_admin)])
async def create_demo_account(payload: DemoAccountPayload):
    """Bir influencer/potansiyel musteriye elle, sureli bir demo hesabi acar -
    /api/admin/demo-account uc noktasini biz (admin) X-Admin-Key basligiyla
    cagiriyoruz, donen giris bilgilerini kendimiz manuel olarak mail atiyoruz
    (otomatik toplu e-posta gonderimi yok). E-posta zaten kayitliysa, mevcut
    kullanicinin plani gecici olarak yukseltilir (sifresine dokunulmaz);
    kayitli degilse rastgele bir sifreyle yeni hesap acilir. Sure dolunca
    plan otomatik olarak ucretsiz'e duser (bkz. app/auth.py _lookup_user_by_token)."""
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Geçerli bir e-posta adresi gerekli")
    if payload.plan not in CREDIT_LIMITS:
        raise HTTPException(status_code=400, detail=f"Geçersiz plan: {payload.plan}")
    if not (1 <= payload.days <= DEMO_MAX_DAYS):
        raise HTTPException(status_code=400, detail=f"Süre 1-{DEMO_MAX_DAYS} gün arasında olmalı")

    expires_at = datetime.now(timezone.utc) + timedelta(days=payload.days)

    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = %s", (email,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE users SET plan = %s, demo_expires_at = %s WHERE id = %s",
                (payload.plan, expires_at.isoformat(), existing["id"]),
            )
            conn.commit()
            return {
                "email": email,
                "existing_user": True,
                "plan": payload.plan,
                "expires_at": expires_at.isoformat(),
                "message": "Bu e-posta zaten kayıtlı - planı geçici olarak yükseltildi, kendi şifresiyle giriş yapabilir.",
            }

        password = secrets.token_urlsafe(9)
        conn.execute(
            """
            INSERT INTO users (email, password_hash, plan, email_verified, demo_expires_at)
            VALUES (%s, %s, %s, 1, %s)
            """,
            (email, hash_password(password), payload.plan, expires_at.isoformat()),
        )
        conn.commit()

    return {
        "email": email,
        "existing_user": False,
        "password": password,
        "plan": payload.plan,
        "expires_at": expires_at.isoformat(),
        "login_url": f"{FRONTEND_URL}/giris",
        "message": "Yeni demo hesabı oluşturuldu - giriş bilgilerini kendin mail at.",
    }


@app.get("/api/health")
async def health():
    return {"ok": True}


