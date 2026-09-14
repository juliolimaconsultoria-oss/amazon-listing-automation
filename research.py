import csv
import sys

from config import Config, load_config
from storage import init_db, insert_product, product_exists


def load_candidates(csv_path: str) -> list:
    """Lê candidatos do CSV (fallback)."""
    candidates = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candidates.append(row)
    return candidates


def load_from_scraper() -> list:
    """Busca candidatos via scraper da Amazon."""
    import scraper
    return scraper.run()


def run(config: Config, use_scraper: bool = False) -> None:
    print("[pesquisa] Iniciando etapa de pesquisa...")
    init_db(config.DB_PATH)

    candidates = []

    if use_scraper:
        try:
            candidates = load_from_scraper()
        except Exception as e:
            print(f"[pesquisa] ERRO no scraper: {e}")

        if not candidates:
            print("[pesquisa] Scraper não retornou produtos. Usando CSV como fallback...")
            candidates = load_candidates(config.CANDIDATES_CSV)
    else:
        candidates = load_candidates(config.CANDIDATES_CSV)

    print(f"[pesquisa] {len(candidates)} candidato(s) encontrado(s).")

    new_count = 0
    skip_count = 0
    for candidate in candidates:
        name = candidate.get("name", "").strip()
        if not name:
            print("[pesquisa] AVISO: linha sem nome ignorada.")
            continue

        if product_exists(config.DB_PATH, name):
            skip_count += 1
            continue

        try:
            insert_product(config.DB_PATH, candidate)
            new_count += 1
        except Exception as e:
            print(f"[pesquisa] ERRO ao inserir '{name}': {e}")

    print(
        f"[pesquisa] Concluído: {new_count} novo(s), {skip_count} já existente(s)."
    )


if __name__ == "__main__":
    try:
        config = load_config()
    except SystemExit:
        config = Config()
        config.ANTHROPIC_API_KEY = "not-needed-for-research"
    init_db(config.DB_PATH)
    run(config)
