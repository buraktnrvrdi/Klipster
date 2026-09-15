"""ffmpeg ile klip kesme, dolgu kelime/sessizlik temizligi, dikey (9:16) kirpma,
altyazi yakma ve kapak (thumbnail) uretimi."""
import subprocess
import textwrap
from pathlib import Path


def get_video_duration(path: str) -> float:
    """ffprobe ile bir video dosyasinin suresini (saniye) okur - kredi
    maliyeti hesaplamasi icin kullanilir. Okunamazsa 0.0 doner, boylece
    kredi hesabi en dusuk (guvenli) carpanla devam eder."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", path,
        ],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return 0.0

# Altyazidan cikartilacak/atlanacak saf dolgu kelimeleri (Turkce).
# Bilerek dar tutuldu: "yani", "işte" gibi bazen anlam tasiyan kelimeler
# YOK, sadece gercekten "duraksama sesi" olanlar var.
FILLER_WORDS = {
    "ıı", "ııı", "eee", "ee", "aa", "aaa", "hmm", "mmm", "ıh", "öhm",
    "şey", "hı", "hıhı",
}

STYLE_PRESETS = {
    "klasik": {
        "label": "Klasik",
        "chunk_size": 4,
        "style_line": (
            "Style: Default,Arial,64,&H00FFFFFF,&H00000000,&H00000000,"
            "-1,0,3,4,0,2,60,60,140,1"
        ),
    },
    "vurgu": {
        "label": "Vurgulu (enerjik)",
        "chunk_size": 2,
        # turuncu, daha kalin, biraz daha buyuk
        "style_line": (
            "Style: Default,Arial,78,&H0026B4F9,&H00000000,&H00000000,"
            "-1,0,3,5,0,2,50,50,150,1"
        ),
    },
    "minimal": {
        "label": "Minimal",
        "chunk_size": 5,
        "style_line": (
            "Style: Default,Arial,52,&H00FFFFFF,&H00202020,&H00000000,"
            "0,0,1,2,1,2,80,80,110,1"
        ),
    },
    "kalin": {
        "label": "Kalın (TikTok tarzı)",
        "chunk_size": 2,
        # buyuk, kalin, sari metin + kalin siyah kontur/golge - test sirasinda
        # BorderStyle=3 (opak kutu) bu ffmpeg/libass kurulumunda hic
        # render olmadigi (altyazi tamamen görünmez kaldigi) icin bilerek
        # BorderStyle=1 (kontur+golge) ile yapildi - kanitlanmis calisan yontem.
        "style_line": (
            "Style: Default,Arial,88,&H0000FFFF,&H00000000,&H00000000,"
            "-1,0,1,5,2,2,40,40,150,1"
        ),
    },
    "editorial": {
        "label": "Editöryel (dergi tarzı)",
        "chunk_size": 6,
        # ince serif font, dusuk profilli, zarif bir dergi alt yazisi hissi
        "style_line": (
            "Style: Default,DejaVu Serif,50,&H00FFFFFF,&H00000000,&H00000000,"
            "0,0,1,1,0,2,100,100,130,1"
        ),
    },
    "vintage": {
        "label": "Vintage (retro)",
        "chunk_size": 3,
        # krem/sepya renkli serif metin, koyu kahverengi kontur - eski film hissi
        "style_line": (
            "Style: Default,DejaVu Serif,58,&H00B3DEF5,&H000F213B,&H00000000,"
            "0,0,1,3,2,2,70,70,130,1"
        ),
    },
}
DEFAULT_STYLE = "klasik"

# Altyazi rengi - kullanicinin secebilecegi hazir renk paleti (frontend'de
# renk daireleri olarak gosterilir, hex kodu backend'e oldugu gibi gonderilir).
SUBTITLE_COLOR_PRESETS = [
    {"id": "beyaz", "label": "Beyaz", "hex": "#FFFFFF"},
    {"id": "turuncu", "label": "Turuncu", "hex": "#F97316"},
    {"id": "sari", "label": "Sarı", "hex": "#FACC15"},
    {"id": "yesil", "label": "Yeşil", "hex": "#22C55E"},
    {"id": "mavi", "label": "Mavi", "hex": "#3B82F6"},
    {"id": "pembe", "label": "Pembe", "hex": "#EC4899"},
]
DEFAULT_SUBTITLE_COLOR = "#FFFFFF"

# Altyazi konumu - dikey kadrajda altyazinin nerede gorunecegini belirler.
SUBTITLE_POSITIONS = {
    "alt": {"label": "Alt (varsayılan)", "alignment": 2},
    "orta": {"label": "Orta", "alignment": 5},
    "ust": {"label": "Üst", "alignment": 8},
}
DEFAULT_SUBTITLE_POSITION = "alt"

# Klip en-boy orani - farkli platform/format hedeflerine gore kirpma+olcekleme.
ASPECT_PRESETS = {
    "9:16": {"label": "Dikey (9:16) — TikTok / Reels / Shorts", "ratio_w": 9, "ratio_h": 16, "res_x": 1080, "res_y": 1920},
    "4:5": {"label": "Dikey (4:5) — Instagram gönderisi", "ratio_w": 4, "ratio_h": 5, "res_x": 1080, "res_y": 1350},
    "1:1": {"label": "Kare (1:1) — Instagram akışı", "ratio_w": 1, "ratio_h": 1, "res_x": 1080, "res_y": 1080},
}
DEFAULT_ASPECT = "9:16"


def _hex_to_ass_color(hex_color: str) -> str:
    """'#RRGGBB' formatindaki bir rengi ASS altyazi formatinin bekledigi
    '&H00BBGGRR' (alfa + mavi-yesil-kirmizi ters sirali) formatina cevirir.
    Gecersiz girdi gelirse varsayilan beyaza duser."""
    h = (hex_color or "").lstrip("#")
    if len(h) != 6 or not all(c in "0123456789abcdefABCDEF" for c in h):
        h = DEFAULT_SUBTITLE_COLOR.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}".upper()


def _build_style_line(style: str, subtitle_color: str | None, position: str) -> str:
    """Secilen stil satirini, kullanicinin altyazi rengi/konumu tercihiyle
    ustune yazarak (override) doner. Renk verilmezse stilin kendi varsayilan
    rengi kullanilir."""
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS[DEFAULT_STYLE])
    fields = preset["style_line"].split(",")
    if subtitle_color:
        fields[3] = _hex_to_ass_color(subtitle_color)  # PrimaryColour
    pos_preset = SUBTITLE_POSITIONS.get(position, SUBTITLE_POSITIONS[DEFAULT_SUBTITLE_POSITION])
    fields[11] = str(pos_preset["alignment"])  # Alignment
    return ",".join(fields)


def _ass_header(
    style: str,
    subtitle_color: str | None = None,
    position: str = DEFAULT_SUBTITLE_POSITION,
    aspect: str = DEFAULT_ASPECT,
) -> str:
    aspect_preset = ASPECT_PRESETS.get(aspect, ASPECT_PRESETS[DEFAULT_ASPECT])
    style_line = _build_style_line(style, subtitle_color, position)
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {aspect_preset['res_x']}\n"
        f"PlayResY: {aspect_preset['res_y']}\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, "
        "Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"{style_line}\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def _format_ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    cs = int(round((seconds - int(seconds)) * 100))
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _clean_token(word: str) -> str:
    return word.strip().lower().strip(".,!?;:،-")


def build_keep_intervals(
    words: list,
    clip_start: float,
    clip_end: float,
    remove_fillers: bool = True,
    max_silence: float = 0.6,
    keep_silence: float = 0.12,
    word_pad: float = 0.03,
) -> list[tuple[float, float]]:
    """Klip araligi icinde 'atlanacak' (dolgu kelime / uzun sessizlik) bolgeleri
    bulup, geriye KALACAK araliklarin listesini dondurur (orijinal video zaman eksininde)."""
    clip_words = sorted(
        [w for w in words if clip_start <= w["start"] < clip_end],
        key=lambda w: w["start"],
    )

    cuts: list[list[float]] = []

    if remove_fillers:
        for w in clip_words:
            if _clean_token(w["word"]) in FILLER_WORDS:
                s = w["start"] + word_pad
                e = w["end"] - word_pad
                if e > s:
                    cuts.append([s, e])

    prev_end = clip_start
    for w in clip_words:
        gap = w["start"] - prev_end
        if gap > max_silence:
            cuts.append([prev_end + keep_silence, w["start"]])
        prev_end = max(prev_end, w["end"])
    tail_gap = clip_end - prev_end
    if tail_gap > max_silence:
        cuts.append([prev_end + keep_silence, clip_end])

    if not cuts:
        return [(clip_start, clip_end)]

    cuts.sort()
    merged: list[list[float]] = []
    for c in cuts:
        if merged and c[0] <= merged[-1][1] + 0.01:
            merged[-1][1] = max(merged[-1][1], c[1])
        else:
            merged.append(c)

    keep: list[tuple[float, float]] = []
    cursor = clip_start
    for c_start, c_end in merged:
        if c_start > cursor:
            keep.append((cursor, min(c_start, clip_end)))
        cursor = max(cursor, c_end)
    if cursor < clip_end:
        keep.append((cursor, clip_end))

    keep = [(s, e) for s, e in keep if e - s > 0.08]
    return keep or [(clip_start, clip_end)]


def _remap_time(t: float, keep_intervals: list[tuple[float, float]]) -> float:
    acc = 0.0
    for s, e in keep_intervals:
        if t < s:
            return acc
        if t <= e:
            return acc + (t - s)
        acc += (e - s)
    return acc


def remap_words(words: list, clip_start: float, clip_end: float, keep_intervals: list[tuple[float, float]]) -> list:
    """Kelimeleri, kesilen bolgeler cikarilmis YENI (kisalmis) zaman eksenine tasir.
    Kesilen bolgelere denk gelen kelimeler (ör. dolgu kelimeler) elenir."""
    out = []
    for w in words:
        if not (clip_start <= w["start"] < clip_end):
            continue
        mid = (w["start"] + w["end"]) / 2
        in_keep = any(s <= mid <= e for s, e in keep_intervals)
        if not in_keep:
            continue
        out.append({
            "start": _remap_time(w["start"], keep_intervals),
            "end": _remap_time(w["end"], keep_intervals),
            "word": w["word"],
        })
    return out


def generate_ass(
    words: list,
    ass_path: Path,
    style: str = DEFAULT_STYLE,
    subtitle_color: str | None = None,
    position: str = DEFAULT_SUBTITLE_POSITION,
    aspect: str = DEFAULT_ASPECT,
):
    """Zaten YENI zaman eksenine gore (0'dan baslayan) remap edilmis kelimelerden
    stili gomulu bir .ass altyazi dosyasi uretir."""
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS[DEFAULT_STYLE])
    chunk_size = preset["chunk_size"]
    lines = []
    for i in range(0, len(words), chunk_size):
        group = words[i:i + chunk_size]
        if not group:
            continue
        start = group[0]["start"]
        end = group[-1]["end"]
        text = "".join(w["word"] for w in group).strip().replace("\n", " ")
        if not text:
            continue
        lines.append(f"Dialogue: 0,{_format_ass_time(start)},{_format_ass_time(end)},Default,,0,0,0,,{text}")
    header = _ass_header(style, subtitle_color=subtitle_color, position=position, aspect=aspect)
    ass_path.write_text(header + "\n".join(lines), encoding="utf-8")


def chunk_words(words: list, style: str = DEFAULT_STYLE) -> list[dict]:
    """generate_ass ile ayni gruplama mantigini kullanarak (start, end, text)
    parcalari uretir - Ingilizce altyazi cevirisi icin zaman pencerelerini
    yeniden kullanmak amaciyla ayri bir fonksiyon olarak tutuluyor."""
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS[DEFAULT_STYLE])
    chunk_size = preset["chunk_size"]
    chunks = []
    for i in range(0, len(words), chunk_size):
        group = words[i:i + chunk_size]
        if not group:
            continue
        text = "".join(w["word"] for w in group).strip().replace("\n", " ")
        if not text:
            continue
        chunks.append({"start": group[0]["start"], "end": group[-1]["end"], "text": text})
    return chunks


def _format_srt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(chunks: list[dict], srt_path: Path):
    """(start, end, text) parcalarindan standart bir .srt altyazi dosyasi yazar."""
    lines = []
    for i, c in enumerate(chunks, start=1):
        lines.append(str(i))
        lines.append(f"{_format_srt_time(c['start'])} --> {_format_srt_time(c['end'])}")
        lines.append(c["text"])
        lines.append("")
    srt_path.write_text("\n".join(lines), encoding="utf-8")


def _extract_segments(input_path: str, keep_intervals: list[tuple[float, float]], out_dir: Path, name: str) -> Path:
    """Keep araliklarini ayri ayri kesip concat eder; tek aralik varsa direkt tek kesim yapar."""
    raw_path = out_dir / f"{name}_raw.mp4"

    if len(keep_intervals) == 1:
        s, e = keep_intervals[0]
        result = subprocess.run([
            "ffmpeg", "-y", "-ss", str(s), "-i", input_path, "-t", str(e - s),
            "-c:v", "libx264", "-c:a", "aac", "-preset", "fast",
            str(raw_path),
        ], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("ffmpeg kesme adiminda hata verdi:\n" + result.stderr[-2000:])
        return raw_path

    seg_paths = []
    for i, (s, e) in enumerate(keep_intervals):
        seg_path = out_dir / f"{name}_seg{i}.mp4"
        result = subprocess.run([
            "ffmpeg", "-y", "-ss", str(s), "-i", input_path, "-t", str(e - s),
            "-c:v", "libx264", "-c:a", "aac", "-preset", "fast",
            str(seg_path),
        ], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("ffmpeg segment kesme adiminda hata verdi:\n" + result.stderr[-2000:])
        seg_paths.append(seg_path)

    list_path = out_dir / f"{name}_concat.txt"
    list_path.write_text("\n".join(f"file '{p.name}'" for p in seg_paths), encoding="utf-8")

    result = subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path.name,
        "-c", "copy", raw_path.name,
    ], capture_output=True, text=True, cwd=str(out_dir))
    if result.returncode != 0:
        raise RuntimeError("ffmpeg birlestirme (concat) adiminda hata verdi:\n" + result.stderr[-2000:])

    for p in seg_paths:
        p.unlink(missing_ok=True)
    list_path.unlink(missing_ok=True)
    return raw_path


def make_vertical_clip(
    input_path: str,
    start: float,
    end: float,
    words: list,
    out_dir: Path,
    name: str,
    style: str = DEFAULT_STYLE,
    remove_fillers: bool = True,
    subtitle_color: str | None = None,
    position: str = DEFAULT_SUBTITLE_POSITION,
    aspect: str = DEFAULT_ASPECT,
) -> Path:
    """Videodan bir klip keser (dolgu kelime/uzun sessizlik varsa temizler),
    secilen en-boy oranina kirpar ve altyazi ekler."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ass_path = out_dir / f"{name}.ass"
    final_path = out_dir / f"{name}.mp4"

    keep_intervals = build_keep_intervals(words, start, end, remove_fillers=remove_fillers)
    raw_path = _extract_segments(input_path, keep_intervals, out_dir, name)

    remapped_words = remap_words(words, start, end, keep_intervals)
    generate_ass(
        remapped_words, ass_path, style=style,
        subtitle_color=subtitle_color, position=position, aspect=aspect,
    )

    aspect_preset = ASPECT_PRESETS.get(aspect, ASPECT_PRESETS[DEFAULT_ASPECT])
    vf = (
        f"crop=ih*{aspect_preset['ratio_w']}/{aspect_preset['ratio_h']}:ih,"
        f"scale={aspect_preset['res_x']}:{aspect_preset['res_y']},"
        f"subtitles=filename={ass_path.name}"
    )
    result = subprocess.run([
        "ffmpeg", "-y", "-i", raw_path.name, "-vf", vf,
        "-c:v", "libx264", "-c:a", "copy", "-preset", "fast",
        final_path.name,
    ], capture_output=True, text=True, cwd=str(out_dir))
    if result.returncode != 0:
        raise RuntimeError("ffmpeg altyazi adiminda hata verdi:\n" + result.stderr[-2000:])

    raw_path.unlink(missing_ok=True)
    return final_path


_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    # Linux/Railway konteynerinde macOS fontlari bulunmuyor - Dockerfile'da
    # kurulan fonts-liberation/fonts-dejavu-core paketlerinden gelen yollar.
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def make_cover(video_path: Path, title: str, out_path: Path, capture_time: float = 1.0):
    """Klipten bir kare alip uzerine baslik metni bindirilmis bir kapak (kapak.jpg) uretir."""
    from PIL import Image, ImageDraw, ImageFont

    tmp_frame = out_path.with_suffix(".raw.jpg")
    result = subprocess.run([
        "ffmpeg", "-y", "-ss", str(capture_time), "-i", str(video_path),
        "-frames:v", "1", "-q:v", "2", str(tmp_frame),
    ], capture_output=True, text=True)
    if result.returncode != 0 or not tmp_frame.exists():
        # kare cikaramadiysak sessizce vazgec, kapak olmadan devam
        return None

    img = Image.open(tmp_frame).convert("RGBA")
    w, h = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    grad_h = int(h * 0.42)
    for i in range(grad_h):
        alpha = int(210 * (i / grad_h))
        y = h - grad_h + i
        odraw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    font = None
    for path in _FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(path, size=int(w * 0.075))
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    wrapped = textwrap.fill(title or "Klip", width=16)
    draw.multiline_text(
        (w * 0.07, h * 0.76), wrapped, font=font, fill=(255, 255, 255),
        spacing=10, stroke_width=4, stroke_fill=(0, 0, 0),
    )

    img.save(out_path, quality=90)
    tmp_frame.unlink(missing_ok=True)
    return out_path
