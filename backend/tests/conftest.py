"""Test suite genelinde paylasilan ayarlar. Gercek gelistirme veritabanina
(storage/klipster.db) hicbir testin dokunmamasi icin app.db import edilmeden
ONCE gecici bir DB dosyasina yonlendiriyoruz - bu dosya, module-level import
sirasinda calisir (pytest conftest.py'yi diger test modullerinden once yukler)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
import os  # noqa: E402

os.environ.setdefault("KLIPSTER_DB_PATH", _tmp_db.name)
