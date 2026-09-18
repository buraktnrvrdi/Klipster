"""YouTube (ve yt-dlp'nin destekledigi diger paylasim siteleri) linkinden
video indirme. Boylece kullanici bilgisayarindan dosya yuklemek yerine bir
video linki yapistirarak da ayni klip uretim hattini calistirabilir - sanki
bilgisayarindan yuklemis gibi (bkz. app/main.py _start_processing_job)."""
import ipaddress
import os
import re
import shutil
import socket
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp

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


def download_video(url: str, out_dir: Path, job_id: str) -> tuple[Path, str]:
    """Verilen linkten videoyu indirir, (dosya_yolu, video_basligi) dondurur.
    Dosya, mevcut yukleme dosyalarinin isimlendirme deseniyle (job_id on eki)
    tutarli olacak sekilde out_dir icine yazilir. Hata durumunda kullaniciya
    gosterilebilir bir mesajla VideoUrlError firlatir."""
    url = url.strip()
    if not url or not URL_RE.match(url):
        raise VideoUrlError("Geçerli bir video linki gir (http:// veya https:// ile başlamalı)")
    _assert_safe_url(url)

    out_dir.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(out_dir).free < MIN_FREE_DISK_BYTES:
        raise VideoUrlError("Sunucuda şu an yeterli depolama alanı yok - lütfen daha sonra tekrar dene")
    out_template = str(out_dir / f"{job_id}_%(title).100B.%(ext)s")

    ydl_opts = {
        "format": "best",
        "merge_output_format": "mp4",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "extractor_args": {"youtube": {"player_client": ["tv_embedded", "ios"]}},
    }

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
            ydl.download([url])
    except VideoUrlError:
        raise
    except yt_dlp.utils.DownloadError as e:
        print(f"[yt-dlp indirme hatasi] {url}: {e}")
        raise VideoUrlError("Video indirilemedi - linkin geçerli ve herkese açık olduğundan emin ol")
    except Exception as e:
        raise VideoUrlError(f"Video indirilemedi: {e}")

    candidates = sorted(p for p in out_dir.glob(f"{job_id}_*") if ".part" not in p.name)
    if not candidates:
        raise VideoUrlError("Video indirildi ama dosya bulunamadı")
    return candidates[0], title
