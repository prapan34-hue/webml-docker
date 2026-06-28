"""
โมดูลฐานข้อมูล PostgreSQL
- เชื่อมต่อด้วยข้อมูลจาก environment variables (ไม่ hardcode รหัสลับ)
- อ้างถึงฐานข้อมูลด้วย "ชื่อ service" (DB_HOST=db) ผ่าน Docker network
- บันทึกประวัติการทำนาย และดึงประวัติล่าสุดออกมาแสดง
"""
import os
import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),          # ชื่อ service ของ PostgreSQL ใน compose
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "mlpredictions"),
    "user": os.getenv("DB_USER", "mluser"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def wait_for_db(retries: int = 30, delay: float = 2.0) -> None:
    """รอจน PostgreSQL พร้อมรับการเชื่อมต่อ (กันกรณี start ไม่ทันกัน)"""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            conn = get_connection()
            conn.close()
            print(f"[db] connected on attempt {attempt}", flush=True)
            return
        except Exception as err:  # noqa: BLE001
            last_err = err
            print(f"[db] not ready ({attempt}/{retries}): {err}", flush=True)
            time.sleep(delay)
    raise RuntimeError(f"Cannot connect to database: {last_err}")


def init_db() -> None:
    """สร้างตารางเก็บประวัติการทำนายถ้ายังไม่มี"""
    ddl = """
    CREATE TABLE IF NOT EXISTS predictions (
        id            SERIAL PRIMARY KEY,
        features      JSONB        NOT NULL,
        species       VARCHAR(50)  NOT NULL,
        probability   REAL         NOT NULL,
        created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
    );
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()


def save_prediction(features: dict, species: str, probability: float) -> None:
    """บันทึกผลการทำนาย 1 รายการ"""
    sql = (
        "INSERT INTO predictions (features, species, probability) "
        "VALUES (%s, %s, %s);"
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (json.dumps(features), species, probability))
        conn.commit()


def fetch_history(limit: int = 10) -> list:
    """ดึงประวัติการทำนายล่าสุด"""
    sql = (
        "SELECT id, features, species, probability, "
        "to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') AS created_at "
        "FROM predictions ORDER BY id DESC LIMIT %s;"
    )
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (limit,))
            return [dict(row) for row in cur.fetchall()]
