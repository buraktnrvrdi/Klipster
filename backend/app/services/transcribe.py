"""Video/audio dosyasini metne cevirir, kelime bazli zaman damgalariyla.
Dil ZORLANMAZ - Whisper videonun konusma dilini kendisi tespit eder, boylece
altyazi videonun kendi dilinde cikar (sadece Turkce ile sinirli degil)."""
import os

from faster_whisper import WhisperModel

_model = None

# Model boyutu ve hassasiyeti .env uzerinden ayarlanabilir, boylece kod
# degistirmeden hiz/dogruluk dengesini test edebilirsin:
#   WHISPER_MODEL=medium       (varsayilan "small"dan daha dogru, daha yavas)
#   WHISPER_COMPUTE_TYPE=int8  (varsayilan; "float32" CPU'da daha yavas ama en dogru sonucu verir)
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE") or None  # None = otomatik tespit


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type=WHISPER_COMPUTE_TYPE)
    return _model


def _collect_segments(segments_iter) -> list:
    result = []
    for seg in segments_iter:
        result.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "words": [
                {"start": w.start, "end": w.end, "word": w.word}
                for w in (seg.words or [])
            ],
        })
    return result


def transcribe(video_path: str):
    """Donen deger: (segments, language_code)
    - segments: [{"start": float, "end": float, "text": str, "words": [...]}, ...]
    - language_code: Whisper'in tespit ettigi konusma dili (ör. "tr", "en", "de")
    """
    model = get_model()
    # language belirtilmezse Whisper ilk birkaç saniyeden dili otomatik tespit eder.
    #
    # vad_filter=True: sessiz/konusma-disi bolgeleri (muzik, arka plan gurultusu,
    # uzun sessizlik) modele hic vermeden atlar. Whisper'in en yaygin hata kaynagi
    # tam olarak bu bolgelerde "halusinasyon" yaparak olmayan kelimeler uretmesidir -
    # VAD bunu buyuk olcude onler ve genelde dogrulugu artirir.
    segments_iter, info = model.transcribe(
        video_path,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        language=WHISPER_LANGUAGE,
    )
    try:
        result = _collect_segments(segments_iter)
    except Exception:
        # VAD, HIC konusma/ses algilanamayan bir dosyada (ör. mikrofon izni
        # verilmeden alinmis sessiz bir ekran kaydi) icten "max() iterable
        # argument is empty" gibi bir hata firlatabiliyor - VAD'i kapatip
        # tekrar deniyoruz. Sesin gercekten hic olmadigi durumda bu ikinci
        # deneme de bos bir sonuc dondurur (hata degil) - bu, run_pipeline'in
        # kullaniciya anlasilir bir mesaj gostermesini sagliyor.
        segments_iter, info = model.transcribe(video_path, word_timestamps=True, vad_filter=False, language=WHISPER_LANGUAGE)
        result = _collect_segments(segments_iter)
    return result, info.language
