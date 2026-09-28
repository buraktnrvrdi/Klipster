"""YouTube (Google) OAuth baglantisi ve klip yukleme servisi.

Kullanicinin kendi YouTube kanalina, Klipster'dan uzerinden dogrudan
"Short" olarak klip yukleyebilmesini saglar. Google'in resmi OAuth 2.0
"authorization code" akisini ve YouTube Data API v3'un resumable upload
protokolunu kullanir - ikisi de Google'in yillardir degismeyen, iyi
belgelenmis, stabil API'leri (iyzico/PayTR'nin aksine burada SDK ornegi
kazma ihtiyaci yok).
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"

# youtube.upload: video yukleme: youtube.readonly: kanal adini gosterebilmek icin.
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"


class SocialAuthError(Exception):
    """Kullaniciya gosterilebilecek Turkce bir mesaj tasiyan OAuth/yukleme hatasi."""


def is_configured() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def build_auth_url(state: str, redirect_uri: str) -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        # refresh_token her zaman donsun diye - onceden baglanmis bir
        # kullanici tekrar baglanirsa Google normalde refresh_token'i
        # sessizce atlar, bunu zorluyoruz.
        "prompt": "consent",
        "state": state,
    }
    query = "&".join(f"{k}={requests.utils.quote(str(v), safe='')}" for k, v in params.items())
    return f"{AUTH_URL}?{query}"


def exchange_code(code: str, redirect_uri: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
        timeout=15,
    )
    data = resp.json()
    if resp.status_code != 200:
        logger.error("[youtube oauth] kod degisimi basarisiz: %s", data)
        raise SocialAuthError(data.get("error_description") or "Google ile bağlantı kurulamadı")
    return data


def refresh_access_token(refresh_token: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    data = resp.json()
    if resp.status_code != 200:
        logger.error("[youtube oauth] token yenileme basarisiz: %s", data)
        raise SocialAuthError("YouTube bağlantısının süresi dolmuş, lütfen tekrar bağlan")
    return data


def get_channel_name(access_token: str) -> str | None:
    resp = requests.get(
        CHANNELS_URL,
        params={"part": "snippet", "mine": "true"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    items = resp.json().get("items") or []
    if not items:
        return None
    return items[0].get("snippet", {}).get("title")


def upload_short(access_token: str, video_path, title: str, description: str) -> str:
    """Video dosyasini YouTube'a yukler, olusan videonun ID'sini dondurur.
    Dikey/60 saniyeden kisa videolar YouTube tarafindan otomatik olarak
    Shorts sayilir - ayri bir 'shorts' parametresi yok."""
    size = video_path.stat().st_size
    init = requests.post(
        UPLOAD_URL,
        params={"uploadType": "resumable", "part": "snippet,status"},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size),
        },
        json={
            "snippet": {"title": title[:100], "description": description[:5000]},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
        },
        timeout=20,
    )
    if init.status_code != 200:
        logger.error("[youtube upload] baslatma basarisiz: %s", init.text[:500])
        raise SocialAuthError("YouTube yükleme başlatılamadı")

    upload_session_url = init.headers.get("Location")
    if not upload_session_url:
        raise SocialAuthError("YouTube yükleme adresi alınamadı")

    with open(video_path, "rb") as f:
        put_resp = requests.put(
            upload_session_url,
            headers={"Content-Type": "video/mp4", "Content-Length": str(size)},
            data=f,
            timeout=300,
        )
    if put_resp.status_code not in (200, 201):
        logger.error("[youtube upload] yukleme basarisiz: %s", put_resp.text[:500])
        raise SocialAuthError("Video YouTube'a yüklenemedi")

    video_id = put_resp.json().get("id")
    if not video_id:
        raise SocialAuthError("YouTube video kimliği alınamadı")
    return video_id
