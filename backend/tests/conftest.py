"""Test suite genelinde paylaşılan ayarlar. DATABASE_URL env var'ı
test çalıştırmadan önce ayarlanmış olmalı (bir test PostgreSQL DB'si işaret etmeli)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os  # noqa: E402

if not os.environ.get("DATABASE_URL"):
    raise RuntimeError(
        "Testler için DATABASE_URL env var'ı gerekli. "
        "Örnek: DATABASE_URL=postgresql://user:pass@localhost/klipster_test pytest tests/"
    )
