"""app/services/video.py icindeki saf (ffmpeg/network gerektirmeyen) fonksiyonlar icin
birim testleri: altyazi zaman/renk formatlama, dolgu kelime/sessizlik temizleme mantigi,
kelime zaman eksenini yeniden esleme ve chunk'lama.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.video import (  # noqa: E402
    _clean_token,
    _format_ass_time,
    _format_srt_time,
    _hex_to_ass_color,
    build_keep_intervals,
    chunk_words,
    remap_words,
)


def test_hex_to_ass_color_converts_rgb_order():
    # ASS renk formati BGR sirali (+ alfa) bekler, RGB degil.
    assert _hex_to_ass_color("#FF0000") == "&H000000FF"  # kirmizi
    assert _hex_to_ass_color("#00FF00") == "&H0000FF00"  # yesil
    assert _hex_to_ass_color("#0000FF") == "&H00FF0000"  # mavi


def test_hex_to_ass_color_falls_back_to_white_on_invalid_input():
    assert _hex_to_ass_color("gecersiz") == "&H00FFFFFF"
    assert _hex_to_ass_color("") == "&H00FFFFFF"
    assert _hex_to_ass_color(None) == "&H00FFFFFF"


def test_format_ass_time_matches_ass_h_mm_ss_cs_format():
    assert _format_ass_time(0) == "0:00:00.00"
    assert _format_ass_time(75.5) == "0:01:15.50"
    assert _format_ass_time(3661.25) == "1:01:01.25"


def test_format_ass_time_clamps_negative_to_zero():
    assert _format_ass_time(-5) == "0:00:00.00"


def test_format_srt_time_matches_srt_hh_mm_ss_ms_format():
    assert _format_srt_time(0) == "00:00:00,000"
    assert _format_srt_time(75.5) == "00:01:15,500"


def test_clean_token_strips_punctuation_and_lowercases():
    assert _clean_token(" Şey, ") == "şey"
    assert _clean_token("Hmm!") == "hmm"
    assert _clean_token("Merhaba.") == "merhaba"


def _w(word, start, end):
    return {"word": word, "start": start, "end": end}


def test_build_keep_intervals_removes_filler_words():
    # "sey" bir dolgu kelimesi (FILLER_WORDS icinde) - word_pad (0.03s) payla
    # aralarindan kesilmis olmali, once ve sonrasi ayri birer "keep" araligi olarak kalmali.
    words = [_w("Merhaba", 0.0, 0.5), _w("şey", 0.5, 0.8), _w("nasılsın", 0.8, 1.3)]
    keep = build_keep_intervals(words, clip_start=0.0, clip_end=1.3, remove_fillers=True)
    assert len(keep) == 2
    assert keep[0] == pytest.approx((0.0, 0.53))
    assert keep[1] == pytest.approx((0.77, 1.3))


def test_build_keep_intervals_keeps_whole_range_without_fillers_or_silence():
    words = [_w("Merhaba", 0.0, 0.5), _w("dunya", 0.5, 1.0)]
    keep = build_keep_intervals(words, clip_start=0.0, clip_end=1.0, remove_fillers=True)
    assert keep == [(0.0, 1.0)]


def test_build_keep_intervals_removes_long_silence_gaps():
    # 0.6 saniyeden (max_silence varsayilani) uzun bir sessizlik var (1.0 -> 3.0),
    # keep_silence (0.12s) payi sessizligin basinda birakiliyor.
    words = [_w("Merhaba", 0.0, 1.0), _w("dunya", 3.0, 3.5)]
    keep = build_keep_intervals(words, clip_start=0.0, clip_end=3.5, remove_fillers=False)
    assert len(keep) == 2
    assert keep[0] == pytest.approx((0.0, 1.12))
    assert keep[1] == pytest.approx((3.0, 3.5))


def test_remap_words_drops_words_outside_keep_intervals():
    words = [_w("Merhaba", 0.0, 0.5), _w("sey", 0.5, 0.8), _w("dunya", 0.8, 1.3)]
    keep_intervals = [(0.0, 0.5), (0.8, 1.3)]
    remapped = remap_words(words, clip_start=0.0, clip_end=1.3, keep_intervals=keep_intervals)
    # "sey" kesilen araliga (0.5-0.8) denk geldigi icin elenmis olmali.
    assert [w["word"] for w in remapped] == ["Merhaba", "dunya"]
    # Kesilen bolge cikarildigi icin "dunya" kelimesi artik 0.5'ten hemen sonra baslamali.
    assert remapped[1]["start"] == pytest.approx(0.5)


def test_chunk_words_groups_by_style_chunk_size():
    words = [_w(f"kelime{i}", i * 0.5, i * 0.5 + 0.4) for i in range(6)]
    chunks = chunk_words(words, style="klasik")  # klasik stilin chunk_size'i 4
    assert len(chunks) == 2
    assert chunks[0]["start"] == words[0]["start"]
    assert chunks[0]["end"] == words[3]["end"]
    assert chunks[1]["start"] == words[4]["start"]
