import json
import re
import urllib.request
import urllib.error

from config import Config, load_config
from storage import get_products_by_status, init_db, save_copy

COPY_PROMPT = """You are an expert Amazon listing copywriter. Generate a product listing in English for the US market.

Product: {name}
Category: {category}
Price: ${price_usd}

Return ONLY valid JSON (no markdown fences, no preamble, no thinking) with this exact schema:
{{
  "title": "SEO-optimized title, under 200 characters",
  "bullets": ["benefit 1", "benefit 2", "benefit 3", "benefit 4", "benefit 5"],
  "description": "Persuasive description, 3-4 sentences",
  "backend_keywords": "comma-separated search terms, under 250 bytes"
}}

IMPORTANT: Output ONLY the JSON object. No extra text before or after."""


def sanitize_response(text: str) -> str:
    text = text.strip()
    # Remove thinking blocks from models that use them
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    # Remove markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def generate_copy_ollama(model: str, base_url: str, product: dict) -> dict | None:
    prompt = COPY_PROMPT.format(
        name=product["name"],
        category=product.get("category", "General"),
        price_usd=product.get("price_usd", "N/A"),
    )

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.7},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"[copy] ERRO de conexão com Ollama: {e}")
        print("[copy] Verifique se o Ollama está rodando (ollama serve).")
        return None

    raw = data.get("message", {}).get("content", "")
    sanitized = sanitize_response(raw)

    try:
        return json.loads(sanitized)
    except json.JSONDecodeError as e:
        print(f"[copy] ERRO: JSON inválido para '{product['name']}': {e}")
        print(f"[copy] Resposta bruta (primeiros 300 chars): {raw[:300]}")
        return None


def generate_copy_anthropic(api_key: str, product: dict) -> dict | None:
    import anthropic

    prompt = COPY_PROMPT.format(
        name=product["name"],
        category=product.get("category", "General"),
        price_usd=product.get("price_usd", "N/A"),
    )

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text
    sanitized = sanitize_response(raw)

    try:
        return json.loads(sanitized)
    except json.JSONDecodeError as e:
        print(f"[copy] ERRO: JSON inválido para '{product['name']}': {e}")
        print(f"[copy] Resposta bruta (primeiros 300 chars): {raw[:300]}")
        return None


def run(config: Config) -> None:
    print("[copy] Iniciando etapa de geração de copy...")
    products = get_products_by_status(config.DB_PATH, "curated_approved")

    if not products:
        print("[copy] Nenhum produto aprovado para gerar copy.")
        return

    products = products[: config.MAX_PRODUCTS_PER_RUN]
    print(f"[copy] {len(products)} produto(s) para processar.")
    print(f"[copy] Provider: {config.LLM_PROVIDER}")

    success = 0
    fail = 0

    for product in products:
        name = product["name"]
        try:
            print(f"[copy] Gerando copy para '{name}'...")

            if config.LLM_PROVIDER == "ollama":
                copy_data = generate_copy_ollama(
                    config.OLLAMA_MODEL, config.OLLAMA_BASE_URL, product
                )
            else:
                copy_data = generate_copy_anthropic(
                    config.ANTHROPIC_API_KEY, product
                )

            if copy_data:
                save_copy(config.DB_PATH, name, copy_data)
                print(f"[copy] OK: '{name}'")
                success += 1
            else:
                fail += 1
        except Exception as e:
            print(f"[copy] ERRO ao gerar copy para '{name}': {e}")
            fail += 1

    print(f"[copy] Concluído: {success} sucesso(s), {fail} falha(s).")


if __name__ == "__main__":
    config = load_config()
    init_db(config.DB_PATH)
    run(config)
