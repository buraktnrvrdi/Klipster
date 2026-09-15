"""YouTube (ve yt-dlp'nin destekledigi diger paylasim siteleri) linkinden
video indirme. Boylece kullanici bilgisayarindan dosya yuklemek yerine bir
video linki yapistirarak da ayni klip uretim hattini calistirabilir - sanki
bilgisayarindan yuklemis gibi (bkz. app/main.py _start_processing_job)."""
import re
from pathlib import Path

import yt_dlp

# Bariz bos/alakasiz girdileri erken elemek icin hizli bir on kontrol - yt-dlp
# zaten desteklemedigi bir url'de kendi (daha az anlasilir) hatasini firlatir.
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

# Cok uzun videolarin indirilip islenmesi hem depolama hem sure acisindan
# makul degil - bu esigin uzerindeki videolar indirilmeden reddedilir.
MAX_DURATION_SECONDS = 4 * 60 * 60  # 4 saat


class VideoUrlError(Exception):
    """Mesaji oldugu gibi kullaniciya gosterilebilecek, anlasilir bir hata."""


def download_video(url: str, out_dir: Path, job_id: str) -> tuple[Path, str]:
    """Verilen linkten videoyu indirir, (dosya_yolu, video_basligi) dondurur.
    Dosya, mevcut yukleme dosyalarinin isimlendirme deseniyle (job_id on eki)
    tutarli olacak sekilde out_dir icine yazilir. Hata durumunda kullaniciya
    gosterilebilir bir mesajla VideoUrlError firlatir."""
    if not url or not URL_RE.match(url.strip()):
        raise VideoUrlError("Geçerli bir video linki gir (http:// veya https:// ile başlamalı)")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(out_dir / f"{job_id}_%(title).100B.%(ext)s")

    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best",
        "merge_output_format": "mp4",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
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
    except yt_dlp.utils.DownloadError:
        raise VideoUrlError("Video indirilemedi - linkin geçerli ve herkese açık olduğundan emin ol")
    except Exception as e:
        raise VideoUrlError(f"Video indirilemedi: {e}")

    candidates = sorted(out_dir.glob(f"{job_id}_*"))
    if not candidates:
        raise VideoUrlError("Video indirildi ama dosya bulunamadı")
    return candidates[0], title
