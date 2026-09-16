"""Basit SQLite katmani: kullanicilar, oturumlar (sessions) ve is (job) kayitlari.
Agir bir ORM yerine stdlib sqlite3 kullaniliyor - ekstra bagimlilik/kurulum riski yok."""
import os
import sqlite3
from pathlib import Path

# Testler KLIPSTER_DB_PATH ile ayri/gecici bir dosyaya yonlendirerek gercek
# gelistirme veritabanina (storage/klipster.db) dokunmadan calisabilir.
DB_PATH = Path(os.environ.get("KLIPSTER_DB_PATH") or Path(__file__).resolve().parent.parent / "storage" / "klipster.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                plan TEXT NOT NULL DEFAULT 'ucretsiz',
                display_name TEXT,
                avatar TEXT,
                email_verified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS email_verifications (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS password_resets (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                filename TEXT,
                status TEXT NOT NULL DEFAULT 'queued',
                error TEXT,
                clips_json TEXT,
                style TEXT,
                remove_fillers INTEGER DEFAULT 1,
                smart_crop INTEGER DEFAULT 1,
                words_json TEXT,
                language TEXT,
                subtitle_color TEXT,
                subtitle_position TEXT,
                aspect TEXT,
                credit_cost INTEGER DEFAULT 0,
                org_id TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS org_members (
                org_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                joined_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (org_id, user_id),
                FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS org_invites (
                token TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()

        # Var olan (eski) veritabanlarinda users/jobs tablolari bu kolonlar
        # olmadan olusturulmus olabilir - varsa sessizce atla, yoksa ekle.
        # words_json: klibi elle yeniden kirpabilmek (retrim) icin videonun
        # tum kelime-seviyesi transkriptini saklar, boylece yeniden transkript
        # cikarmaya gerek kalmaz.
        # subtitle_color/subtitle_position/aspect: kullanicinin altyazi rengi,
        # altyazi konumu ve klip en-boy orani tercihini saklar, boylece retrim
        # (yeniden kesim) sirasinda ayni gorunumle yeniden uretilebilir.
        # credit_cost: bu isin tukettigi kredi miktari (bkz. app/services/credits.py) -
        # aylik kredi kullanimini hesaplarken bu kolon toplanir.
        # org_id: is bir ekip/ajans calisma alanina aitse doldurulur - o zaman
        # isi sadece yukleyen degil, ekibin tum uyeleri gorebilir.
        # email_verified: kayit sirasinda 0 baslar, dogrulama linkine tiklaninca 1 olur.
        # sessions.expires_at: token'in ne zaman gecersiz olacagi - eski (bu kolon
        # eklenmeden once acilmis) oturumlarda NULL kalir ve suresiz kabul edilir,
        # ama yeni acilan TUM oturumlarda artik doldurulur (bkz. auth.create_session).
        for stmt in (
            "ALTER TABLE users ADD COLUMN display_name TEXT",
            "ALTER TABLE users ADD COLUMN avatar TEXT",
            "ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE sessions ADD COLUMN expires_at TEXT",
            "ALTER TABLE jobs ADD COLUMN words_json TEXT",
            "ALTER TABLE jobs ADD COLUMN language TEXT",
            "ALTER TABLE jobs ADD COLUMN subtitle_color TEXT",
            "ALTER TABLE jobs ADD COLUMN subtitle_position TEXT",
            "ALTER TABLE jobs ADD COLUMN aspect TEXT",
            "ALTER TABLE jobs ADD COLUMN credit_cost INTEGER DEFAULT 0",
            "ALTER TABLE jobs ADD COLUMN org_id TEXT",
            "ALTER TABLE jobs ADD COLUMN subtitle_animation TEXT",
            "ALTER TABLE jobs ADD COLUMN highlight_color TEXT",
            "ALTER TABLE jobs ADD COLUMN smart_crop INTEGER DEFAULT 1",
        ):
            try:
                conn.execute(stmt)
                conn.commit()
            except sqlite3.OperationalError:
                pass  # kolon zaten var


# Klip sayisi ve sure araligini elle ayarlayabilme - sadece bu planlarda acik.
CUSTOMIZABLE_CLIP_PLANS = {"yaratici", "ajans"}

# Profilde secilebilecek sabit avatar seti. Bunlar emoji DEGIL, sadece birer
# kimlik (id) - gorseli (ozel cizilmis SVG ikon) frontend'deki AvatarIcons.tsx
# tanimliyor. Sunucu sadece bu id listesine karsi dogrulama yapar.
AVATAR_OPTIONS = [
    "bolt", "flame", "spark", "comet", "clip", "wave",
    "gem", "crown", "rocket", "shield", "infinity", "moon",
    "sun", "target", "pulse", "orbit",
]
