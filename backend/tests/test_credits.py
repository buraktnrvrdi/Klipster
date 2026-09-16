"""app/services/credits.py icindeki saf kredi hesaplama fonksiyonlari icin
birim testleri - bu mantik daha once hic test edilmiyordu, ancak dogrudan
kullanicidan para/kredi tahsilatini belirledigi icin regresyonlara karsi
en kritik yerlerden biri."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.credits import (  # noqa: E402
    CREDIT_COST_BASE,
    CREDIT_COST_PER_CLIP,
    compute_added_clip_cost,
    compute_credit_cost,
    duration_multiplier,
)


def test_duration_multiplier_short_video():
    assert duration_multiplier(5 * 60) == 1.0


def test_duration_multiplier_medium_video():
    assert duration_multiplier(30 * 60) == 1.5


def test_duration_multiplier_long_video():
    assert duration_multiplier(60 * 60) == 2.0


def test_duration_multiplier_boundary_is_inclusive():
    assert duration_multiplier(15 * 60) == 1.0
    assert duration_multiplier(45 * 60) == 1.5


def test_compute_credit_cost_matches_base_formula_for_short_video():
    clip_count = 3
    expected = CREDIT_COST_BASE + clip_count * CREDIT_COST_PER_CLIP
    assert compute_credit_cost(5 * 60, clip_count) == expected


def test_compute_credit_cost_scales_with_duration_multiplier():
    short = compute_credit_cost(5 * 60, 5)
    long = compute_credit_cost(60 * 60, 5)
    assert long > short


def test_compute_credit_cost_treats_zero_clip_count_as_one():
    assert compute_credit_cost(5 * 60, 0) == compute_credit_cost(5 * 60, 1)


def test_compute_credit_cost_never_below_one():
    assert compute_credit_cost(0, 0) >= 1


def test_compute_credit_cost_unknown_duration_uses_lowest_multiplier():
    # duration_seconds=0 (sure okunamadi) en dusuk carpanla (1.0) hesaplanmali -
    # kullaniciyi bilinmeyen bir hatadan dolayi fazla ucretlendirmemek icin.
    assert compute_credit_cost(0, 5) == compute_credit_cost(5 * 60, 5)


def test_compute_added_clip_cost_scales_with_duration():
    short = compute_added_clip_cost(5 * 60)
    long = compute_added_clip_cost(60 * 60)
    assert long >= short
    assert short >= 1
