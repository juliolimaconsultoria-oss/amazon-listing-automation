import json
import sqlite3


def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                name TEXT PRIMARY KEY,
                category TEXT,
                price_usd REAL,
                competitor_reviews INTEGER,
                competitor_rating REAL,
                demand_score REAL,
                notes TEXT,
                curation_score REAL,
                status TEXT NOT NULL DEFAULT 'researched',
                copy_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def product_exists(db_path: str, name: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM products WHERE name = ?", (name,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def insert_product(db_path: str, product: dict) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT INTO products
               (name, category, price_usd, competitor_reviews,
                competitor_rating, demand_score, notes, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'researched')""",
            (
                product["name"],
                product.get("category", ""),
                float(product.get("price_usd", 0)),
                int(product.get("competitor_reviews", 0)),
                float(product.get("competitor_rating", 0)),
                float(product.get("demand_score", 0)),
                product.get("notes", ""),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_products_by_status(db_path: str, status: str) -> list:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM products WHERE status = ?", (status,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_product_status(db_path: str, name: str, status: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE products SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE name = ?",
            (status, name),
        )
        conn.commit()
    finally:
        conn.close()


def save_curation_score(db_path: str, name: str, score: float) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE products SET curation_score = ? WHERE name = ?",
            (score, name),
        )
        conn.commit()
    finally:
        conn.close()


def save_copy(db_path: str, name: str, copy_data: dict) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """UPDATE products
               SET copy_data = ?, status = 'copy_ready', updated_at = CURRENT_TIMESTAMP
               WHERE name = ?""",
            (json.dumps(copy_data, ensure_ascii=False), name),
        )
        conn.commit()
    finally:
        conn.close()
