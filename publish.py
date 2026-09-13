import json
import os
from datetime import datetime

from config import Config, load_config
from storage import get_products_by_status, init_db, update_product_status


def export_listings(products: list, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"listings_ready_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    listings = []
    for p in products:
        copy_data = json.loads(p["copy_data"]) if p.get("copy_data") else {}
        listings.append(
            {
                "product_name": p["name"],
                "category": p.get("category", ""),
                "price_usd": p.get("price_usd"),
                "curation_score": p.get("curation_score"),
                "listing": copy_data,
            }
        )

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)

    return filepath


def publish_via_sp_api(product_name: str, copy_data: dict) -> None:
    # TODO: Integração com Amazon SP-API quando credenciais estiverem disponíveis.
    # Passos:
    # 1. Trocar refresh_token por access_token via OAuth (POST https://api.amazon.com/auth/o2/token)
    # 2. Montar payload no formato da Listings Items API
    # 3. PUT /listings/2021-08-01/items/{sellerId}/{sku}
    # 4. Tratar resposta e erros de validação da Amazon
    raise NotImplementedError(
        f"Publicação via SP-API não implementada. "
        f"Produto '{product_name}' deve ser enviado manualmente pelo Seller Central."
    )


def run(config: Config) -> None:
    print("[publicacao] Iniciando etapa de publicação...")
    products = get_products_by_status(config.DB_PATH, "copy_ready")

    if not products:
        print("[publicacao] Nenhum produto pronto para publicar.")
        return

    print(f"[publicacao] {len(products)} produto(s) com copy pronta.")
    filepath = export_listings(products, config.OUTPUT_DIR)
    print(f"[publicacao] Listagens exportadas para: {filepath}")

    for product in products:
        update_product_status(config.DB_PATH, product["name"], "published")

    print(
        f"[publicacao] {len(products)} produto(s) marcado(s) como publicado(s)."
    )
    print("[publicacao] ATENÇÃO: Faça upload manual no Seller Central.")


if __name__ == "__main__":
    try:
        config = load_config()
    except SystemExit:
        config = Config()
        config.ANTHROPIC_API_KEY = "not-needed-for-publish"
    init_db(config.DB_PATH)
    run(config)
