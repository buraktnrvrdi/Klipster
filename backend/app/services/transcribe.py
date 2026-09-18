"""Video/audio dosyasini metne cevirir, kelime bazli zaman damgalariyla.
GROQ_API_KEY varsa Groq Whisper API kullanilir (large-v3, ucretsiz, RAM sorunu yok).
Yoksa yerel faster-whisper modeli kullanilir (fallback).
"""
import gc
import os

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE") or None  # None = otomatik tespit
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# --- Groq API ---

def _transcribe_groq(video_path: str):
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    with open(video_path, "rb") as f:
        response = client.audio.transcriptions.create(
            file=(os.path.basename(video_path), f),
            model="whisper-large-v3",
            language=WHISPER_LANGUAGE,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )
    segments = []
    # Groq verbose_json: response.words listesi var, segment yok — tek segment olarak wrap et
    words = []
    for w in (response.words or []):
        words.append({"start": w.start, "end": w.end, "word": w.word})
    if words:
        segments.append({
            "start": words[0]["start"],
            "end": words[-1]["end"],
            "text": response.text.strip(),
            "words": words,
        })
    language = getattr(response, "language", None) or WHISPER_LANGUAGE or "tr"
    return segments, language


# --- Yerel faster-whisper ---

_model = None


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type=WHISPER_COMPUTE_TYPE)
    return _model


def unload_model():
    """Transkripsiyon bittikten sonra modeli bellekten boşalt — ffmpeg adımı için RAM açar."""
    global _model
    _model = None
    gc.collect()


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


def _transcribe_local(video_path: str):
    model = get_model()
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
        segments_iter, info = model.transcribe(
            video_path, word_timestamps=True, vad_filter=False, language=WHISPER_LANGUAGE
        )
        result = _collect_segments(segments_iter)
    unload_model()
    return result, info.language


# --- Ana fonksiyon ---

def transcribe(video_path: str):
    """Donen deger: (segments, language_code)
    - segments: [{"start": float, "end": float, "text": str, "words": [...]}, ...]
    - language_code: tespit edilen konusma dili (ör. "tr", "en")
    """
    if GROQ_API_KEY:
        return _transcribe_groq(video_path)
    return _transcribe_local(video_path)
