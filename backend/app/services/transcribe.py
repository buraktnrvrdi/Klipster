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


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type=WHISPER_COMPUTE_TYPE)
    return _model


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
    segments, info = model.transcribe(
        video_path,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    result = []
    for seg in segments:
        result.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "words": [
                {"start": w.start, "end": w.end, "word": w.word}
                for w in (seg.words or [])
            ],
        })
    return result, info.language
