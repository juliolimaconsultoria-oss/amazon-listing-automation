from config import Config, load_config
from storage import (
    get_products_by_status,
    init_db,
    save_curation_score,
    update_product_status,
)

WEIGHTS = {
    "demand": 0.40,
    "competition": 0.30,
    "price": 0.15,
    "rating_gap": 0.15,
}


def calculate_score(product: dict) -> float:
    demand = float(product.get("demand_score", 0))
    demand_normalized = (demand / 10.0) * 100

    reviews = int(product.get("competitor_reviews", 0))
    if reviews <= 50:
        competition_score = 100
    elif reviews >= 5000:
        competition_score = 0
    else:
        competition_score = max(0, 100 - (reviews / 5000) * 100)

    price = float(product.get("price_usd", 0))
    if 10 <= price <= 50:
        price_score = 100
    elif price < 10:
        price_score = max(0, price * 10)
    else:
        price_score = max(0, 100 - (price - 50) * 2)

    rating = float(product.get("competitor_rating", 5.0))
    rating_gap_score = max(0, (5.0 - rating) / 5.0 * 100)

    score = (
        demand_normalized * WEIGHTS["demand"]
        + competition_score * WEIGHTS["competition"]
        + price_score * WEIGHTS["price"]
        + rating_gap_score * WEIGHTS["rating_gap"]
    )

    return round(score, 2)


def run(config: Config) -> None:
    print("[curadoria] Iniciando etapa de curadoria...")
    products = get_products_by_status(config.DB_PATH, "researched")
    print(f"[curadoria] {len(products)} produto(s) para avaliar.")

    approved = 0
    rejected = 0
    for product in products:
        name = product["name"]
        try:
            score = calculate_score(product)
            save_curation_score(config.DB_PATH, name, score)

            if score >= config.MIN_CURATION_SCORE:
                update_product_status(config.DB_PATH, name, "curated_approved")
                print(f"[curadoria] APROVADO: '{name}' (score: {score})")
                approved += 1
            else:
                update_product_status(config.DB_PATH, name, "curated_rejected")
                print(f"[curadoria] REJEITADO: '{name}' (score: {score})")
                rejected += 1
        except Exception as e:
            print(f"[curadoria] ERRO ao avaliar '{name}': {e}")

    print(
        f"[curadoria] Concluído: {approved} aprovado(s), {rejected} rejeitado(s)."
    )


if __name__ == "__main__":
    try:
        config = load_config()
    except SystemExit:
        config = Config()
        config.ANTHROPIC_API_KEY = "not-needed-for-curation"
    init_db(config.DB_PATH)
    run(config)
