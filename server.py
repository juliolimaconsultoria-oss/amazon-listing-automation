import json
import os
import sys
import threading
import glob
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from config import Config
from storage import init_db

# Carrega config sem validar LLM (o servidor não precisa do Ollama para iniciar)
config = Config()
init_db(config.DB_PATH)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def get_db_connection():
    import sqlite3
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_products():
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT name, category, price_usd, competitor_reviews, "
            "competitor_rating, demand_score, notes, url, curation_score, "
            "status, copy_data, created_at, updated_at "
            "FROM products ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stats():
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM products GROUP BY status"
        ).fetchall()
        stats = {r["status"]: r["count"] for r in rows}
        total = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        stats["total"] = total
        return stats
    finally:
        conn.close()


def get_latest_listings():
    pattern = os.path.join(config.OUTPUT_DIR, "listings_ready_*.json")
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        return []
    with open(files[0], "r", encoding="utf-8") as f:
        return json.load(f)


def _capture_logs(fn):
    log_lines = []

    class LogCapture:
        def __init__(self, original):
            self.original = original

        def write(self, text):
            if text.strip():
                log_lines.append(text.strip())
            self.original.write(text)

        def flush(self):
            self.original.flush()

    old_stdout = sys.stdout
    sys.stdout = LogCapture(old_stdout)
    try:
        fn()
    except SystemExit:
        log_lines.append("ERRO: Verifique a configuração no .env")
    except Exception as e:
        log_lines.append(f"ERRO: {e}")
    finally:
        sys.stdout = old_stdout
    return log_lines


def run_filter():
    import research
    import curation

    def _run():
        cfg = Config()
        init_db(cfg.DB_PATH)
        research.run(cfg, use_scraper=True)
        curation.run(cfg)

    return _capture_logs(_run)


def run_copy():
    import copy_generator
    import publish

    def _run():
        cfg = Config()
        cfg.validate()
        init_db(cfg.DB_PATH)
        copy_generator.run(cfg)
        publish.run(cfg)

    return _capture_logs(_run)


def run_pipeline():
    import research
    import curation
    import copy_generator
    import publish

    def _run():
        cfg = Config()
        cfg.validate()
        init_db(cfg.DB_PATH)
        for stage_fn in [research.run, curation.run, copy_generator.run, publish.run]:
            stage_fn(cfg)

    return _capture_logs(_run)


def run_refresh():
    import research
    import curation

    def _run():
        cfg = Config()
        init_db(cfg.DB_PATH)
        conn = get_db_connection()
        try:
            removed = conn.execute(
                "SELECT COUNT(*) FROM products WHERE status = 'curated_rejected'"
            ).fetchone()[0]
            conn.execute("DELETE FROM products WHERE status = 'curated_rejected'")
            conn.commit()
            print(f"[atualizar] {removed} produto(s) rejeitado(s) removido(s).")
        finally:
            conn.close()
        research.run(cfg, use_scraper=True)
        curation.run(cfg)

    return _capture_logs(_run)


def reset_product(name):
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE products SET status = 'researched', curation_score = NULL, "
            "copy_data = NULL, updated_at = CURRENT_TIMESTAMP WHERE name = ?",
            (name,),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def delete_product(name):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM products WHERE name = ?", (name,))
        conn.commit()
        return True
    finally:
        conn.close()


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/products":
            self._json_response(get_products())
        elif path == "/api/stats":
            self._json_response(get_stats())
        elif path == "/api/listings":
            self._json_response(get_latest_listings())
        elif path == "/" or path == "":
            self.path = "/index.html"
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""

        if path == "/api/run":
            log = run_pipeline()
            self._json_response({"status": "ok", "log": log})
        elif path == "/api/run-filter":
            log = run_filter()
            self._json_response({"status": "ok", "log": log})
        elif path == "/api/run-copy":
            log = run_copy()
            self._json_response({"status": "ok", "log": log})
        elif path == "/api/refresh":
            log = run_refresh()
            self._json_response({"status": "ok", "log": log})
        elif path == "/api/reset":
            data = json.loads(body) if body else {}
            name = data.get("name", "")
            if name and reset_product(name):
                self._json_response({"status": "ok"})
            else:
                self._json_response({"status": "error"}, 400)
        elif path == "/api/delete":
            data = json.loads(body) if body else {}
            name = data.get("name", "")
            if name and delete_product(name):
                self._json_response({"status": "ok"})
            else:
                self._json_response({"status": "error"}, 400)
        else:
            self._json_response({"error": "not found"}, 404)

    def _json_response(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def main():
    port = int(os.getenv("DASHBOARD_PORT", "8080"))
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"Dashboard rodando em http://localhost:{port}")
    print("Pressione Ctrl+C para parar.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        server.server_close()


if __name__ == "__main__":
    main()
