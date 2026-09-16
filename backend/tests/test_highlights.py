"""app/services/highlights.py icindeki saf (AI cagrisi gerektirmeyen) yardimci
fonksiyonlar icin birim testleri - AI saglayicisindan donen JSON cevabinin
(bazen kod bloguna sarilmis olabiliyor) temizlenip parse edilmesi.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.highlights import _clean_json, _strip_code_fence  # noqa: E402


def test_strip_code_fence_removes_markdown_json_fence():
    raw = '```json\n{"clips": []}\n```'
    assert _strip_code_fence(raw) == '\n{"clips": []}\n'


def test_strip_code_fence_removes_plain_fence():
    raw = '```\n{"clips": []}\n```'
    assert _strip_code_fence(raw) == '\n{"clips": []}\n'


def test_strip_code_fence_leaves_plain_json_untouched():
    raw = '{"clips": []}'
    assert _strip_code_fence(raw) == '{"clips": []}'


def test_clean_json_parses_fenced_response():
    raw = '```json\n{"clips": [{"start": 1.0, "end": 5.0, "score": 80}]}\n```'
    data = _clean_json(raw)
    assert data["clips"][0]["score"] == 80


def test_clean_json_parses_plain_response():
    raw = '{"clips": []}'
    assert _clean_json(raw) == {"clips": []}
