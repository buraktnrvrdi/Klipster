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

def _extract_audio(video_path: str) -> str:
    """Video dosyasından ses çıkarır, Groq'un 25MB limitini aşmamak için."""
    import subprocess
    import tempfile
    audio_path = tempfile.mktemp(suffix=".mp3")
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ar", "16000", "-ac", "1", "-b:a", "32k",
        audio_path,
    ], capture_output=True, check=True)
    return audio_path


def _transcribe_groq(video_path: str):
    import tempfile
    from groq import Groq

    audio_path = _extract_audio(video_path)
    try:
        client = Groq(api_key=GROQ_API_KEY)
        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f),
                model="whisper-large-v3",
                language=WHISPER_LANGUAGE,
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"],
            )
    finally:
        try:
            os.remove(audio_path)
        except Exception:
            pass

    # Kelime listesini segment başlangıç/bitiş zamanlarına göre grupla
    raw_words = {w.start: {"start": w.start, "end": w.end, "word": w.word}
                 for w in (response.words or [])}
    all_words_list = sorted(raw_words.values(), key=lambda w: w["start"])

    segments = []
    for seg in (response.segments or []):
        seg_words = [w for w in all_words_list if w["start"] >= seg.start - 0.05 and w["end"] <= seg.end + 0.05]
        segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "words": seg_words,
        })

    # Groq bazen segment dönmeyebilir — fallback olarak tek segment
    if not segments and all_words_list:
        segments.append({
            "start": all_words_list[0]["start"],
            "end": all_words_list[-1]["end"],
            "text": response.text.strip(),
            "words": all_words_list,
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
