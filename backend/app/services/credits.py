"""Kredi sistemi: her video yuklemesi, secilen klip sayisi ve kaynak videonun
suresine gore bir miktar kredi tuketir. Boylece ayni "1 video hakki" kisa bir
klip icin de 1 saatlik bir podcast icin de esit sayilmaz - uzun video ve/veya
daha fazla klip secimi orantili olarak daha fazla kredi harcar.

Plan basina aylik kredi hakki sabittir (None = sinirsiz). Butun sabitler
buradan tek noktadan ayarlanabilir."""
import math

# Plan basina aylik kredi hakki.
CREDIT_LIMITS = {"ucretsiz": 30, "yaratici": 300, "ajans": None}

# Kredi maliyetinin sabit bilesenleri.
CREDIT_COST_BASE = 4       # video basina sabit maliyet (transkript + analiz)
CREDIT_COST_PER_CLIP = 2   # uretilecek her klip icin ek maliyet

# Kaynak video suresine gore carpan - daha uzun video daha fazla transkript/
# analiz islemi gerektirir, bu yuzden orantili olarak daha cok kredi tuketir.
# (esik_saniye, carpan) - suresi esik_saniye'yi asmayan ilk esik uygulanir.
DURATION_TIER_MULTIPLIERS = [
    (15 * 60, 1.0),        # 0-15 dk
    (45 * 60, 1.5),        # 15-45 dk
    (float("inf"), 2.0),   # 45 dk ve uzeri
]


def duration_multiplier(duration_seconds: float) -> float:
    for threshold, mult in DURATION_TIER_MULTIPLIERS:
        if duration_seconds <= threshold:
            return mult
    return DURATION_TIER_MULTIPLIERS[-1][1]


def compute_credit_cost(duration_seconds: float, clip_count: int) -> int:
    """Bir video yuklemesinin toplam kredi maliyetini hesaplar. Video suresi
    okunamadiysa (0 gelirse) en dusuk carpanla (1.0) devam edilir - kullaniciyi
    bilinmeyen bir hata yuzunden fazla ucretlendirmemek icin guvenli taraf."""
    base = CREDIT_COST_BASE + max(1, clip_count) * CREDIT_COST_PER_CLIP
    mult = duration_multiplier(max(0.0, duration_seconds))
    return max(1, math.ceil(base * mult))


def compute_added_clip_cost(duration_seconds: float) -> int:
    """Isi zaten tamamlanmis bir videoya, kullanicinin SONRADAN elle eklemek
    istedigi TEK bir klibin ek kredi maliyetini hesaplar - ayni sure
    carpani mantigi (uzun video = daha pahali) burada da gecerli."""
    mult = duration_multiplier(max(0.0, duration_seconds))
    return max(1, math.ceil(CREDIT_COST_PER_CLIP * mult))
