"""YouTube (ve yt-dlp'nin destekledigi diger paylasim siteleri) linkinden
video indirme. Boylece kullanici bilgisayarindan dosya yuklemek yerine bir
video linki yapistirarak da ayni klip uretim hattini calistirabilir - sanki
bilgisayarindan yuklemis gibi (bkz. app/main.py _start_processing_job)."""
import base64
import ipaddress
import logging
import os
import re
import shutil
import socket
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp

logger = logging.getLogger(__name__)

# Bariz bos/alakasiz girdileri erken elemek icin hizli bir on kontrol - yt-dlp
# zaten desteklemedigi bir url'de kendi (daha az anlasilir) hatasini firlatir.
URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _is_public_host(hostname: str) -> bool:
    """Hostname'in cozumlendigi TUM IP'lerin genel (public) internet
    adresi oldugunu dogrular - SSRF'e karsi (sunucunun iç agina,
    localhost'a veya bulut metadata endpoint'lerine (169.254.169.254 gibi)
    istek atilmasini engellemek icin). Herhangi bir adres private/loopback/
    link-local/reserved ise False doner."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False
    if not infos:
        return False
    for family, _, _, _, sockaddr in infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (
            ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified
        ):
            return False
    return True


def _assert_safe_url(url: str) -> None:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname or not _is_public_host(hostname):
        raise VideoUrlError("Geçerli bir video linki gir (http:// veya https:// ile başlamalı)")

# Cok uzun videolarin indirilip islenmesi hem depolama hem sure acisindan
# makul degil - bu esigin uzerindeki videolar indirilmeden reddedilir.
MAX_DURATION_SECONDS = 4 * 60 * 60  # 4 saat

# Diskte bu kadar bostan az yer varsa yeni indirmeyi baslatmadan reddet -
# kotu niyetli/coklu buyuk indirmelerin diski tamamen doldurup sunucuyu
# (SQLite yazmalari dahil) calismaz hale getirmesini onlemek icin.
MIN_FREE_DISK_BYTES = int(os.environ.get("MIN_FREE_DISK_GB", "2")) * 1024 * 1024 * 1024


class VideoUrlError(Exception):
    """Mesaji oldugu gibi kullaniciya gosterilebilecek, anlasilir bir hata."""


_cookie_file_path: str | None = None


def _get_cookie_file() -> str | None:
    """YOUTUBE_COOKIES_B64 env var'indan cookie dosyasini olusturur (tek seferlik)."""
    global _cookie_file_path
    if _cookie_file_path and os.path.exists(_cookie_file_path):
        return _cookie_file_path
    b64 = os.environ.get("YOUTUBE_COOKIES_B64", "").strip()
    if not b64:
        return None
    try:
        data = base64.b64decode(b64)
    except Exception:
        logger.warning("YOUTUBE_COOKIES_B64 gecersiz base64 iceriyor, cookie kullanilmayacak")
        return None
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="yt_cookies_")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(data)
    _cookie_file_path = path
    logger.info("YouTube cookie dosyasi olusturuldu: %s", path)
    return path


def download_video(url: str, out_dir: Path, job_id: str) -> tuple[Path, str]:
    """Verilen linkten videoyu indirir, (dosya_yolu, video_basligi) dondurur.
    Dosya, mevcut yukleme dosyalarinin isimlendirme deseniyle (job_id on eki)
    tutarli olacak sekilde out_dir icine yazilir. Hata durumunda kullaniciya
    gosterilebilir bir mesajla VideoUrlError firlatir."""
    url = url.strip()
    if not url or not URL_RE.match(url):
        raise VideoUrlError("Geçerli bir video linki gir (http:// veya https:// ile başlamalı)")
    _assert_safe_url(url)

    # Playlist/mix parametrelerini temizle - sadece video ID'si kalsın.
    # list= ve start_radio= parametreleri bazen format secimini bozuyor.
    parsed = urlparse(url)
    if parsed.hostname and "youtube" in parsed.hostname:
        from urllib.parse import parse_qs, urlencode
        qs = parse_qs(parsed.query, keep_blank_values=True)
        clean_qs = {k: v for k, v in qs.items() if k in ("v",)}
        if clean_qs:
            url = parsed._replace(query=urlencode(clean_qs, doseq=True)).geturl()

    out_dir.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(out_dir).free < MIN_FREE_DISK_BYTES:
        raise VideoUrlError("Sunucuda şu an yeterli depolama alanı yok - lütfen daha sonra tekrar dene")
    out_template = str(out_dir / f"{job_id}_%(title).100B.%(ext)s")

    _BASE_OPTS: dict = {
        "merge_output_format": "mp4",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }
    cookie_file = _get_cookie_file()
    if cookie_file:
        _BASE_OPTS["cookiefile"] = cookie_file

    # Deneme sirasi: once cookie+web clientlar, sonra cookie gerektirmeyen mobile.
    # player_skip=["webpage"] => web sayfasini cekmeyi atlar, "page needs to be reloaded"
    # bot-detection hatasini engeller. _no_cookie=True olan denemelerden cookiefile kaldirilir.
    _FMT = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
    _ATTEMPTS = [
        # mweb + cookie + missing_pot: SABR formatlarini da listele ve indirmeyi dene
        {"format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
         "extractor_args": {"youtube": {"player_client": ["mweb"],
                                        "formats": ["missing_pot"]}}},
        {"format": "best",
         "extractor_args": {"youtube": {"player_client": ["mweb"],
                                        "formats": ["missing_pot"]}}},
        # mweb cookie ile player_skip
        {"format": "best",
         "extractor_args": {"youtube": {"player_client": ["mweb"],
                                        "player_skip": ["webpage"]}}},
        # Diger web clientlar
        {"format": _FMT},
        {"format": _FMT,
         "extractor_args": {"youtube": {"player_client": ["web_creator"]}}},
        {"format": _FMT,
         "extractor_args": {"youtube": {"player_client": ["tv_embedded"]}}},
        # Android/iOS no-cookie + player_skip
        {"format": _FMT,
         "_no_cookie": True,
         "extractor_args": {"youtube": {"player_client": ["android"],
                                        "player_skip": ["webpage"]}}},
        {"format": _FMT,
         "_no_cookie": True,
         "extractor_args": {"youtube": {"player_client": ["ios"],
                                        "player_skip": ["webpage"]}}},
        # Son care
        {"format": "best",
         "_no_cookie": True,
         "extractor_args": {"youtube": {"player_client": ["android"],
                                        "player_skip": ["webpage"]}}},
    ]

    title = "video"
    last_error = None

    for extra in _ATTEMPTS:
        extra = dict(extra)
        no_cookie = extra.pop("_no_cookie", False)
        ydl_opts = {**_BASE_OPTS, **extra}
        if no_cookie:
            ydl_opts.pop("cookiefile", None)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                duration = info.get("duration") or 0
                if duration and duration > MAX_DURATION_SECONDS:
                    raise VideoUrlError(
                        f"Bu video çok uzun ({int(duration // 60)} dakika). "
                        f"En fazla {MAX_DURATION_SECONDS // 3600} saatlik videolar desteklenir."
                    )
                title = info.get("title") or "video"
                height = info.get("height") or "?"
                fmt = info.get("format") or "?"
                logger.info("[yt-dlp indirme] %s | cozunurluk=%s | format=%s", url, height, fmt)
                ydl.download([url])
            last_error = None
            break
        except VideoUrlError:
            raise
        except yt_dlp.utils.DownloadError as e:
            err = str(e)
            logger.warning("[yt-dlp deneme hatasi] %s: %s", url, err[:200])
            last_error = err
            continue
        except Exception as e:
            last_error = str(e)
            continue

    if last_error is not None:
        raise VideoUrlError("Video indirilemedi - linkin geçerli ve herkese açık olduğundan emin ol")

    candidates = sorted(p for p in out_dir.glob(f"{job_id}_*") if ".part" not in p.name)
    if not candidates:
        raise VideoUrlError("Video indirildi ama dosya bulunamadı")
    return candidates[0], title
