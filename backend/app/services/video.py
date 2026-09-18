"""ffmpeg ile klip kesme, dolgu kelime/sessizlik temizligi, dikey (9:16) kirpma,
altyazi yakma ve kapak (thumbnail) uretimi."""
import subprocess
import textwrap
from pathlib import Path

try:
    import cv2  # akilli kadraj (yuz takibi) icin - kurulu degilse sessizce devre disi kalir
except ImportError:
    cv2 = None


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
            "-1,0,1,4,0,2,60,60,140,1"
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
    {"id": "kirmizi", "label": "Kırmızı", "hex": "#EF4444"},
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

# Altyazi animasyonu - "statik" tum kelimeler ayni anda gorunur (klasik alt yazi),
# "karaoke" ise o an konusulan kelimeyi ayri bir vurgu rengiyle/hafif buyuterek
# one cikarir (TikTok/CapCut/Opus Clip'te populer olan "kelime vurgulu altyazi" formati).
SUBTITLE_ANIMATIONS = {
    "statik": {"label": "Statik (klasik)"},
    "karaoke": {"label": "Kelime vurgulu (karaoke)"},
    "pop": {"label": "Zıplayan (pop)"},
    "daktilo": {"label": "Daktilo (harf harf)"},
    "kayan": {"label": "Kayarak giren"},
}
DEFAULT_SUBTITLE_ANIMATION = "statik"

# Karaoke modunda aktif kelimeyi vurgulamak icin kullanilan sabit renk - kullanicinin
# sectigi subtitle_color hala TUM metnin temel (PrimaryColour) rengini belirler,
# bu sadece o an soylenen kelimeyi one cikaran AYRI bir vurgu rengidir.
KARAOKE_HIGHLIGHT_HEX = "#FFEB3B"

# Karaoke/pop vurgu renginin varsayilani - KARAOKE_HIGHLIGHT_HEX ile ayni,
# generate_ass/make_vertical_clip parametrelerinde DEFAULT_SUBTITLE_COLOR gibi
# isimlendirme tutarliligi icin ayri bir sabit olarak da tutuluyor.
DEFAULT_HIGHLIGHT_COLOR = KARAOKE_HIGHLIGHT_HEX

# Daktilo (typewriter) animasyonunda her karakter-adimi icin minimum sure (saniye) -
# cok uzun chunk'larda bile adimlar bu sureden kisa olmaz, boylece "strobe" etkisi
# (asiri hizli yanip-sonme) engellenir.
TYPEWRITER_MIN_STEP_SEC = 0.03

# Pop (ziplayan) animasyonunda buyutme-asiri gecis (overshoot) ve oturma sureleri (ms) -
# gercek bir ffmpeg/libass yakma testiyle dogrulanan degerler (bkz. generate_ass).
POP_OVERSHOOT_MS = 120
POP_SETTLE_MS = 200


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


def _slide_rest_position(style: str, position: str, aspect: str) -> tuple[int, int, int]:
    """\move ile kayarak-giren animasyonu icin metnin OTURACAGI (rest) nokta
    koordinatini hesaplar. \move, stilin otomatik hizalama/MarginV tabanli
    konumlandirmasini TAMAMEN GECERSIZ KILDIGI icin, o otomatik konumu burada
    elle yeniden uretiyoruz (Alignment 2=alt-orta, 5=orta-orta, 8=ust-orta;
    MarginV alt/ust hizalamada kenardan mesafe, ortada kullanilmaz)."""
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS[DEFAULT_STYLE])
    aspect_preset = ASPECT_PRESETS.get(aspect, ASPECT_PRESETS[DEFAULT_ASPECT])
    pos_preset = SUBTITLE_POSITIONS.get(position, SUBTITLE_POSITIONS[DEFAULT_SUBTITLE_POSITION])
    alignment = pos_preset["alignment"]
    fields = preset["style_line"].split(",")
    margin_v = int(fields[14])
    res_x, res_y = aspect_preset["res_x"], aspect_preset["res_y"]
    x = res_x // 2
    if alignment == 8:  # ust
        y = margin_v
    elif alignment == 5:  # orta
        y = res_y // 2
    else:  # 2, alt (varsayilan)
        y = res_y - margin_v
    return x, y, alignment


def generate_ass(
    words: list,
    ass_path: Path,
    style: str = DEFAULT_STYLE,
    subtitle_color: str | None = None,
    position: str = DEFAULT_SUBTITLE_POSITION,
    aspect: str = DEFAULT_ASPECT,
    animation: str = DEFAULT_SUBTITLE_ANIMATION,
    highlight_color: str = KARAOKE_HIGHLIGHT_HEX,
):
    """Zaten YENI zaman eksenine gore (0'dan baslayan) remap edilmis kelimelerden
    stili gomulu bir .ass altyazi dosyasi uretir.

    animation="statik" (varsayilan): her grup (chunk) tek bir Dialogue satiri -
    tum kelimeler ayni anda, ayni renkte gorunur (eski/klasik davranis, degismedi).

    animation="karaoke": her grup icin, grup icindeki HER kelime kadar ayri
    Dialogue satiri uretilir - o an "aktif" (konusulan) kelime vurgu rengiyle
    ve hafifce buyutulerek gosterilir, digerleri normal stil rengiyle kalir.
    Boylece video oynarken kelime kelime vurgu kayarak ilerler (karaoke hissi)."""
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS[DEFAULT_STYLE])
    chunk_size = preset["chunk_size"]
    highlight_color_ass = _hex_to_ass_color(highlight_color or KARAOKE_HIGHLIGHT_HEX)
    lines = []
    for i in range(0, len(words), chunk_size):
        group = words[i:i + chunk_size]
        if not group:
            continue
        if animation == "karaoke":
            chunk_end = group[-1]["end"]
            for j, active in enumerate(group):
                w_start = active["start"]
                w_end = group[j + 1]["start"] if j + 1 < len(group) else chunk_end
                if w_end <= w_start:
                    w_end = max(active["end"], w_start + 0.05)
                parts = []
                for k, w in enumerate(group):
                    if k == j:
                        parts.append(
                            f"{{\\c{highlight_color_ass}\\b1\\fscx112\\fscy112}}{w['word']}{{\\r}}"
                        )
                    else:
                        parts.append(w["word"])
                text = "".join(parts).strip().replace("\n", " ")
                if not text:
                    continue
                lines.append(
                    f"Dialogue: 0,{_format_ass_time(w_start)},{_format_ass_time(w_end)},Default,,0,0,0,,{text}"
                )
        elif animation == "pop":
            # Karaoke ile ayni yapi (chunk boyunca hepsi gorunur, aktif kelime
            # pencereleri sirayla ilerler) ama vurguyu RENK yerine bir "pop"
            # (kucuk baslayip hafifce asiri buyuyup 100%'e oturan) olcek
            # gecisiyle yapiyoruz - \t() transform + \fscx/\fscy, bu
            # ortamda dogrulanmis calisan tag'ler (karaoke'de de kullaniliyor).
            chunk_end = group[-1]["end"]
            for j, active in enumerate(group):
                w_start = active["start"]
                w_end = group[j + 1]["start"] if j + 1 < len(group) else chunk_end
                if w_end <= w_start:
                    w_end = max(active["end"], w_start + 0.05)
                parts = []
                for k, w in enumerate(group):
                    if k == j:
                        parts.append(
                            f"{{\\c{highlight_color_ass}\\fscx60\\fscy60\\b1"
                            f"\\t(0,{POP_OVERSHOOT_MS},\\fscx115\\fscy115)"
                            f"\\t({POP_OVERSHOOT_MS},{POP_SETTLE_MS},\\fscx100\\fscy100)}}"
                            f"{w['word']}{{\\r}}"
                        )
                    else:
                        parts.append(w["word"])
                text = "".join(parts).strip().replace("\n", " ")
                if not text:
                    continue
                lines.append(
                    f"Dialogue: 0,{_format_ass_time(w_start)},{_format_ass_time(w_end)},Default,,0,0,0,,{text}"
                )
        elif animation == "daktilo":
            # Karakter karakter yaziliyormus gibi gorunmesi icin chunk'in
            # toplam suresini kucuk adimlara bolup, her adimda bir onceki
            # metnin biraz daha uzun bir on-eki (prefix) gosteren AYRI
            # Dialogue satirlari uretiyoruz (ASS clip/tag hilesi degil, duz
            # coklu satir - en garanti calisan yontem).
            start = group[0]["start"]
            end = group[-1]["end"]
            full_text = "".join(w["word"] for w in group).strip()
            if not full_text:
                continue
            total_dur = max(end - start, 0.01)
            char_count = len(full_text)
            step_count = min(char_count, max(1, int(total_dur / TYPEWRITER_MIN_STEP_SEC)))
            step_dur = total_dur / step_count
            for step in range(step_count):
                chars_shown = max(1, round((step + 1) * char_count / step_count))
                step_text = full_text[:chars_shown].replace("\n", " ")
                step_start = start + step * step_dur
                step_end = end if step == step_count - 1 else start + (step + 1) * step_dur
                lines.append(
                    f"Dialogue: 0,{_format_ass_time(step_start)},{_format_ass_time(step_end)},"
                    f"Default,,0,0,0,,{step_text}"
                )
        elif animation == "kayan":
            # Chunk, dinlenme (rest) konumunun biraz altindan/ustunden baslayip
            # \move() ile kisa surede yerine kayarak oturuyor. \move, stilin
            # otomatik hizalamasini GECERSIZ KILDIGI icin dinlenme x/y'sini
            # _slide_rest_position ile stilin Alignment+MarginV degerlerinden
            # elle yeniden hesapliyoruz (aksi halde metin yanlis yere ziplar).
            rest_x, rest_y, alignment = _slide_rest_position(style, position, aspect)
            offset_y = 40
            slide_ms = 180
            if alignment == 8:  # ust: yukaridan asagi kayarak gelsin (ekran disina
                start_y = rest_y - offset_y  # tasmasin diye yukari degil asagi yonlu)
            else:  # alt / orta: alttan yukari kayarak gelsin (dogal TikTok hissi)
                start_y = rest_y + offset_y
            start = group[0]["start"]
            end = group[-1]["end"]
            text = "".join(w["word"] for w in group).strip().replace("\n", " ")
            if not text:
                continue
            move_tag = f"\\move({rest_x},{start_y},{rest_x},{rest_y},0,{slide_ms})"
            lines.append(
                f"Dialogue: 0,{_format_ass_time(start)},{_format_ass_time(end)},"
                f"Default,,0,0,0,,{{{move_tag}}}{text}"
            )
        else:
            start = group[0]["start"]
            end = group[-1]["end"]
            text = "".join(w["word"] for w in group).strip().replace("\n", " ")
            if not text:
                continue
            lines.append(f"Dialogue: 0,{_format_ass_time(start)},{_format_ass_time(end)},Default,,0,0,0,,{text}")
    # Kelimeler arası boşluk artır: her dialogue satırının text kısmına \fsp3 ekle
    spaced_lines = []
    for line in lines:
        if line.startswith("Dialogue:"):
            parts = line.split(",,", 1)
            if len(parts) == 2:
                text_part = parts[1]
                if text_part.startswith("{"):
                    # Mevcut override bloğuna fsp ekle
                    text_part = text_part.replace("{", "{\\fsp3", 1)
                else:
                    text_part = "{\\fsp3}" + text_part
                line = parts[0] + ",," + text_part
        spaced_lines.append(line)
    header = _ass_header(style, subtitle_color=subtitle_color, position=position, aspect=aspect)
    ass_path.write_text(header + "\n".join(spaced_lines), encoding="utf-8")


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

    _ENCODE_FLAGS = ["-c:v", "libx264", "-threads", "2", "-c:a", "aac", "-preset", "fast"]

    if len(keep_intervals) == 1:
        s, e = keep_intervals[0]
        result = subprocess.run([
            "ffmpeg", "-y", "-ss", str(s), "-i", input_path, "-t", str(e - s),
            *_ENCODE_FLAGS, str(raw_path),
        ], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("ffmpeg kesme adiminda hata verdi:\n" + result.stderr[-2000:])
        return raw_path

    seg_paths = []
    for i, (s, e) in enumerate(keep_intervals):
        seg_path = out_dir / f"{name}_seg{i}.mp4"
        result = subprocess.run([
            "ffmpeg", "-y", "-ss", str(s), "-i", input_path, "-t", str(e - s),
            *_ENCODE_FLAGS, str(seg_path),
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


# Akilli kadraj (smart crop) icin varsayilan ayarlar - yuz takibi baglamli/
# jitter'siz calissin diye ornekleme araligi ve maksimum kaydirma hizi.
SMART_CROP_SAMPLE_INTERVAL = 0.7  # saniye - her ornekte yuz tespiti calistirilir
SMART_CROP_DETECT_WIDTH = 480  # tespit oncesi karenin kucultulecegi genislik (px)
SMART_CROP_MIN_DETECTION_RATIO = 0.15  # orneklerin en az bu orani yuz icermeli, yoksa None donulur
SMART_CROP_MAX_PAN_PER_SEC = 0.15  # saniyede kirpma merkezinin genislik fraksiyonu cinsinden kayabilecegi en fazla mesafe
SMART_CROP_MIN_KEYFRAME_GAP = 1.5  # saniye - ffmpeg ifadesini makul uzunlukta tutmak icin key frame'leri seyreltme araligi


def detect_smart_crop_keyframes(
    input_path: str, start: float, end: float, target_aspect_ratio: float,
) -> list[tuple[float, float]] | None:
    """Klip araliginda (start-end, orijinal video zaman ekseninde) OpenCV'nin
    Haar cascade yuz dedektoruyle en belirgin (en buyuk) yuzu ornekleyerek,
    kirpma penceresinin yatay merkezinin zaman icindeki konumunu (0-1 araliginda
    fraksiyon) dondurur. Donen liste (klip basina gore saniye, x_fraction)
    ikililerinden olusur - 0 saniye klip basiangicina denk gelir.

    Yuz guvenilir sekilde tespit edilemezse (video ekran kaydi/slayt gibi
    yuzsuz icerikse ya da OpenCV kurulu degilse) None doner, boylece cagiran
    taraf eski sabit merkez-kirpma davranisina geri doner. target_aspect_ratio
    su an tespit mantigini etkilemiyor (gelecekte, ornegin yuz cok genis bir
    kirpma penceresine sigmiyorsa farkli bir strateji secmek icin saklaniyor)."""
    if cv2 is None:
        return None

    duration = end - start
    if duration <= 0.5:
        return None

    cap = cv2.VideoCapture(input_path)
    try:
        if not cap.isOpened():
            return None

        frame_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        frame_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if not frame_w or not frame_h:
            return None

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(cascade_path)
        if cascade.empty():
            return None

        # Uzun kliplerde ornek sayisini makul tutmak icin araligi genisletiyoruz
        # (cok fazla ornek hem yavaslatir hem de sonda uretilecek ffmpeg ifadesini
        # gereksiz uzatir - zaten sonda ayrica seyreltme de yapiliyor).
        sample_interval = max(SMART_CROP_SAMPLE_INTERVAL, duration / 140.0)

        samples: list[tuple[float, float | None]] = []
        t = 0.0
        while t < duration:
            cap.set(cv2.CAP_PROP_POS_MSEC, (start + t) * 1000.0)
            ok, frame = cap.read()
            if ok and frame is not None:
                h, w = frame.shape[:2]
                scale = SMART_CROP_DETECT_WIDTH / float(w) if w > SMART_CROP_DETECT_WIDTH else 1.0
                small = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale != 1.0 else frame
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)
                faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                if len(faces) > 0:
                    fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                    samples.append((t, (fx + fw / 2.0) / small.shape[1]))
                else:
                    samples.append((t, None))
            t += sample_interval

        if not samples:
            return None

        detected = [s for s in samples if s[1] is not None]
        if len(detected) / len(samples) < SMART_CROP_MIN_DETECTION_RATIO:
            return None

        # Yuz bulunamayan orneklerde son bilinen konumu koru (ani ziplamayi engeller).
        filled: list[tuple[float, float]] = []
        last_known = detected[0][1]
        for tt, x in samples:
            if x is not None:
                last_known = x
            filled.append((tt, last_known))

        # Maksimum kayma hizini sinirlayarak (clamped max-step) yumusat -
        # akilli kadraj yavas/kararli bir "pan" gibi hissettirsin, jitter olmasin.
        smoothed: list[tuple[float, float]] = [filled[0]]
        prev_t, prev_x = filled[0]
        for tt, x in filled[1:]:
            dt = max(tt - prev_t, 1e-6)
            max_delta = SMART_CROP_MAX_PAN_PER_SEC * dt
            delta = max(-max_delta, min(max_delta, x - prev_x))
            new_x = prev_x + delta
            smoothed.append((tt, new_x))
            prev_t, prev_x = tt, new_x

        # Ek olarak kucuk bir hareketli ortalama uygula (kalan yuksek frekansli
        # titremeyi de temizler).
        window = 2
        final: list[tuple[float, float]] = []
        for i in range(len(smoothed)):
            lo, hi = max(0, i - window), min(len(smoothed), i + window + 1)
            avg = sum(p[1] for p in smoothed[lo:hi]) / (hi - lo)
            final.append((smoothed[i][0], avg))

        # ffmpeg ifadesinin cok uzamamasi icin key frame'leri seyrelt.
        thinned: list[tuple[float, float]] = [final[0]]
        for tt, x in final[1:]:
            if tt - thinned[-1][0] >= SMART_CROP_MIN_KEYFRAME_GAP:
                thinned.append((tt, x))
        if thinned[-1][0] < final[-1][0] - 0.01:
            thinned.append(final[-1])

        if len(thinned) < 2:
            return None

        return thinned
    except Exception:
        return None
    finally:
        cap.release()


def _remap_smart_crop_keyframes(
    keyframes: list[tuple[float, float]], start: float, keep_intervals: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """Akilli kadraj key frame zamanlarini (klip basina gore, orijinal video
    zaman ekseninde) dolgu kelime/sessizlik temizligi sonrasi KISALMIS klip
    zaman eksenine tasir (bkz. remap_words/_remap_time ile ayni mantik -
    ffmpeg'e verilecek raw_path zaten bu kisalmis eksende, o yuzden akilli
    kadraj key frame'leri de ayni eksene tasinmali)."""
    remapped: list[tuple[float, float]] = []
    for t, x in keyframes:
        new_t = _remap_time(start + t, keep_intervals)
        if remapped and new_t <= remapped[-1][0]:
            # Bu key frame kesilen (silinen) bir bolgeye denk geliyor - ayni
            # zaman noktasina cakisan bir onceki key frame ile birlesir,
            # sifir-uzunluklu segment olusmasini (bolme hatasi) engelliyoruz.
            remapped[-1] = (remapped[-1][0], x)
        else:
            remapped.append((new_t, x))
    return remapped


def _build_smart_crop_x_expr(keyframes: list[tuple[float, float]]) -> str:
    """(zaman, x_fraction) key frame listesinden, ffmpeg crop filtresinin
    x parametresi icin kullanilacak parcali-dogrusal (piecewise-linear)
    interpolasyon ifadesini uretir. Sonuc, kirpma penceresinin kaynak
    karenin disina cikmamasi icin clip() ile sinirlanir."""
    def center_expr(x: float) -> str:
        return f"({x:.5f}*in_w)"

    # Son key frame'den sonraki t degerleri icin: son bilinen konumda sabit kal.
    expr = center_expr(keyframes[-1][1])
    for i in range(len(keyframes) - 2, -1, -1):
        t0, x0 = keyframes[i]
        t1, x1 = keyframes[i + 1]
        span = max(t1 - t0, 1e-6)
        seg = f"({center_expr(x0)}+({center_expr(x1)}-{center_expr(x0)})*(t-{t0:.3f})/{span:.3f})"
        expr = f"if(lt(t,{t1:.3f}),{seg},{expr})"
    # Ilk key frame'den onceki t degerleri icin: ilk bilinen konumda sabit kal.
    expr = f"if(lt(t,{keyframes[0][0]:.3f}),{center_expr(keyframes[0][1])},{expr})"

    return f"clip({expr}-out_w/2,0,in_w-out_w)"


# Otomatik yakinlastirma (auto-zoom / "punch-in") icin varsayilan ayarlar -
# altyazi grubu (chunk) degistikce kisa bir zoom-in "vurgu" yapip yumusakca
# eski olceğine geri doner (Submagic/CapCut gibi araclarda yaygin bir efekt).
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]

AUTO_ZOOM_AMOUNT = 0.14  # tepe noktasinda ekstra buyutme orani (%14)
AUTO_ZOOM_DECAY_SEC = 0.45  # tepeden 1.0 olceğine donme suresi (saniye)
AUTO_ZOOM_MIN_GAP_SEC = 1.3  # iki vurgu arasinda olmasi gereken en az sure - surekli/rahatsiz edici zoom'u onler
AUTO_ZOOM_MAX_PULSES = 40  # ffmpeg ifadesinin asiri uzamamasi icin ust sinir


def _get_video_fps(path: str) -> str:
    """ffprobe ile bir videonun kare hizini 'pay/payda' (ör. '30000/1001')
    formatinda okur - zoompan filtresine TAM olarak kaynagin kare hizini
    vermek icin (aksi halde zoompan'in kendi varsayilan fps'i kaynaktan
    farkli olursa kare kopyalanip/dusurulur, bu da video suresini degistirip
    sese (audio -c:a copy ile aynen korunuyor) gore kaymaya yol acar)."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path,
        ],
        capture_output=True, text=True,
    )
    fps = result.stdout.strip()
    return fps if fps and "/" in fps else "30"


def _compute_auto_zoom_pulses(remapped_words: list, style: str, clip_duration: float) -> list[float]:
    """Altyazi gruplarinin (chunk) baslangic zamanlarindan, aralarinda en az
    AUTO_ZOOM_MIN_GAP_SEC olacak sekilde seyreltilmis bir "zoom vurgusu"
    zaman listesi uretir - boylece her altyazi degisiminde degil, makul
    araliklarla zoom pulsu tetiklenir."""
    chunks = chunk_words(remapped_words, style=style)
    pulses: list[float] = []
    last = -1e9
    for c in chunks:
        t = c["start"]
        if t >= clip_duration - 0.2:
            break
        if t - last >= AUTO_ZOOM_MIN_GAP_SEC:
            pulses.append(t)
            last = t
        if len(pulses) >= AUTO_ZOOM_MAX_PULSES:
            break
    return pulses


def _build_auto_zoom_expr(pulses: list[float]) -> str:
    """(zoompan'in 'time' degiskenini kullanarak) her vurgu zamaninda 1'den
    (1+AUTO_ZOOM_AMOUNT)'a aniden ziplayip, sonrasinda AUTO_ZOOM_DECAY_SEC
    icinde dogrusal olarak 1'e geri donen bir zoom ifadesi uretir. Vurgular
    AUTO_ZOOM_MIN_GAP_SEC kadar arayla seyreltildigi icin pratikte ayni anda
    en fazla bir tanesi aktif olur, bu yuzden katkilari toplamak (yerine
    max almak) yeterli ve daha basit bir ifadeye karsilik gelir."""
    if not pulses:
        return "1"
    terms = "+".join(
        f"if(lt(time,{t:.3f}),0,max(0,{AUTO_ZOOM_AMOUNT}*(1-(time-{t:.3f})/{AUTO_ZOOM_DECAY_SEC})))"
        for t in pulses
    )
    return f"(1+{terms})"


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
    animation: str = DEFAULT_SUBTITLE_ANIMATION,
    highlight_color: str = KARAOKE_HIGHLIGHT_HEX,
    smart_crop: bool = True,
    auto_zoom: bool = True,
) -> Path:
    """Videodan bir klip keser (dolgu kelime/uzun sessizlik varsa temizler),
    secilen en-boy oranina kirpar ve altyazi ekler.

    smart_crop=True ise, kirpma penceresinin yatay konumu OpenCV yuz
    tespitiyle konusan kisiyi takip eder (yumusatilmis, yavas bir "pan" -
    bkz. detect_smart_crop_keyframes). Yuz guvenilir sekilde bulunamazsa ya da
    tespit/ifade uretimi herhangi bir sekilde hata verirse SESSIZCE eski sabit
    merkez-kirpma davranisina (crop=ih*ratio:ih, varsayilan x=(in_w-out_w)/2)
    geri doner - akilli kadraj hicbir zaman klip uretimini bozmamali.

    auto_zoom=True ise, altyazi gruplari degistikce kisa "punch-in" zoom
    vurgulari eklenir (bkz. _compute_auto_zoom_pulses/_build_auto_zoom_expr,
    zoompan filtresiyle uygulanir). Kelime/zaman verisi yetersizse ya da
    zoompan adimi herhangi bir sekilde hata verirse SESSIZCE zoomsuz devam
    edilir - ayni smart_crop gibi, bu efekt de asla klip uretimini bozmamali."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ass_path = out_dir / f"{name}.ass"
    final_path = out_dir / f"{name}.mp4"

    keep_intervals = build_keep_intervals(words, start, end, remove_fillers=remove_fillers)
    raw_path = _extract_segments(input_path, keep_intervals, out_dir, name)

    remapped_words = remap_words(words, start, end, keep_intervals)
    generate_ass(
        remapped_words, ass_path, style=style,
        subtitle_color=subtitle_color, position=position, aspect=aspect,
        animation=animation, highlight_color=highlight_color,
    )

    aspect_preset = ASPECT_PRESETS.get(aspect, ASPECT_PRESETS[DEFAULT_ASPECT])
    crop_dims = f"ih*{aspect_preset['ratio_w']}/{aspect_preset['ratio_h']}:ih"

    x_expr = None
    if smart_crop:
        try:
            keyframes = detect_smart_crop_keyframes(
                input_path, start, end, aspect_preset["ratio_w"] / aspect_preset["ratio_h"],
            )
            if keyframes:
                remapped_keyframes = _remap_smart_crop_keyframes(keyframes, start, keep_intervals)
                if len(remapped_keyframes) >= 2:
                    x_expr = _build_smart_crop_x_expr(remapped_keyframes)
        except Exception:
            # Yuz tespiti/ifade uretimi herhangi bir nedenle patlarsa (bozuk kare,
            # opencv hatasi vb.) sessizce sabit merkez-kirpmaya don - klip
            # uretiminin basarili olmasi akilli kadrajdan daha onemli.
            x_expr = None

    if x_expr:
        # NOT: ffmpeg -vf icinde virgul, filtre zincirindeki filtreleri ayirmak
        # icin kullanilir - x ifadesinin (if/clip) kendi virgulleri bu yuzden
        # kacis (escape) edilmeli, yoksa ffmpeg filtre grafigini yanlis boler.
        escaped_x_expr = x_expr.replace(",", "\\,")
        crop_step = f"crop={crop_dims}:x={escaped_x_expr}:y=0"
    else:
        crop_step = f"crop={crop_dims}"

    zoom_step = None
    if auto_zoom:
        try:
            pulses = _compute_auto_zoom_pulses(remapped_words, style, end - start)
            if pulses:
                zoom_expr = _build_auto_zoom_expr(pulses)
                fps = _get_video_fps(str(raw_path))
                # zoompan'in kendi 's' secenegi hem zoom/pan'i hem final
                # olcegi (scale) tek adimda uyguluyor - crop_step zaten
                # dogru en-boy oranina kirptigi icin burada sadece merkezden
                # simetrik yakinlastirma yeterli (x/y varsayilan merkez).
                # d=1 + kaynagin TAM fps'i: kare kopyalama/dusurme olmadan
                # 1:1 kare eslemesi, boylece video suresi (dolayisiyla ses
                # senkronu, ses ayrica -c:a copy ile degismiyor) korunur.
                # Zoompan yarı çözünürlükte çalışır (~4x daha hızlı, zoom
                # efekti için kalite farkı göze çarpmaz), sonra scale ile
                # hedef çözünürlüğe getirilir.
                half_w = aspect_preset['res_x'] // 2
                half_h = aspect_preset['res_y'] // 2
                zoom_step = (
                    f"scale={half_w}:{half_h},"
                    f"zoompan=z='{zoom_expr}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
                    f"s={half_w}x{half_h}:fps={fps}:d=1,"
                    f"scale={aspect_preset['res_x']}:{aspect_preset['res_y']}:flags=bilinear"
                )
        except Exception:
            # Zoom hesaplama/ifade uretimi herhangi bir nedenle patlarsa
            # sessizce zoomsuz devam et - smart_crop ile ayni felsefe.
            zoom_step = None

    scale_step = f"scale={aspect_preset['res_x']}:{aspect_preset['res_y']},setsar=1"
    if zoom_step:
        vf = f"{crop_step},{zoom_step},setsar=1,subtitles=filename={ass_path.name}"
    else:
        vf = f"{crop_step},{scale_step},subtitles=filename={ass_path.name}"

    vf_fallback = f"{crop_step},{scale_step},subtitles=filename={ass_path.name}"

    def _run_ffmpeg(vf_filter: str):
        try:
            return subprocess.run([
                "ffmpeg", "-y", "-i", raw_path.name, "-vf", vf_filter,
                "-c:v", "libx264", "-threads", "2",
                "-c:a", "copy", "-preset", "fast",
                final_path.name,
            ], capture_output=True, text=True, cwd=str(out_dir), timeout=600)
        except subprocess.TimeoutExpired:
            return None

    result = _run_ffmpeg(vf)
    if (result is None or result.returncode != 0) and zoom_step:
        # zoompan bazı kaynak videolarda (garip SAR, OOM, timeout) başarısız olur —
        # zoomsuz sürümle yeniden dene
        result = _run_ffmpeg(vf_fallback)
    if result is None:
        raise RuntimeError("ffmpeg altyazi adiminda zaman asimi (600s)")
    if result.returncode != 0:
        raise RuntimeError("ffmpeg altyazi adiminda hata verdi:\n" + result.stderr[-2000:])

    raw_path.unlink(missing_ok=True)
    return final_path

def make_cover(video_path: Path, title: str, out_path: Path, capture_time: float = 1.0):
    """Klipten bir kare alip uzerine baslik metni bindirilmis bir kapak (kapak.jpg) uretir."""
    from PIL import Image, ImageDraw, ImageFont

    tmp_frame = out_path.with_suffix(".raw.jpg")
    result = subprocess.run([
        "ffmpeg", "-y", "-ss", str(capture_time), "-i", str(video_path),
        "-frames:v", "1", "-q:v", "2", str(tmp_frame),
    ], capture_output=True, text=True)
    if result.returncode != 0 or not tmp_frame.exists():
        import logging
        logging.warning(f"make_cover: kare alinamadi ({video_path}): {result.stderr[-300:]}")
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
