"""Scraper para Amazon Best Sellers e New Releases."""

import re
import time
import urllib.request
import urllib.error


CATEGORIES = {
    "Kitchen": {
        "bs_path": "Best-Sellers-Kitchen-Dining/zgbs/kitchen",
        "nr_path": "gp/new-releases/kitchen",
        "commission": 4.5,
    },
    "Home": {
        "bs_path": "Best-Sellers-Home-Kitchen/zgbs/home-garden",
        "nr_path": "gp/new-releases/home-garden",
        "commission": 3.0,
    },
    "Beauty": {
        "bs_path": "Best-Sellers-Beauty-Personal-Care/zgbs/beauty",
        "nr_path": "gp/new-releases/beauty",
        "commission": 3.0,
    },
    "Sports": {
        "bs_path": "Best-Sellers-Sports-Outdoors/zgbs/sporting-goods",
        "nr_path": "gp/new-releases/sporting-goods",
        "commission": 3.0,
    },
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
}


def _fetch(url):
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"[scraper] ERRO ao acessar {url}: {e}")
        return ""


def _parse_products(html, category, source, commission):
    products = []
    chunks = re.split(r'id="gridItemRoot"', html)
    for rank, chunk in enumerate(chunks[1:], 1):
        asin_m = re.search(r'/dp/([A-Z0-9]{10})', chunk)
        if not asin_m:
            continue
        asin = asin_m.group(1)

        name = ""
        for pattern in [
            r'class="[^"]*(?:truncate|line-clamp)[^"]*"[^>]*>([^<]{5,})',
            r'title="([^"]{5,})"',
        ]:
            m = re.search(pattern, chunk)
            if m:
                name = m.group(1).strip()
                break
        if not name:
            continue

        price_m = re.search(r'\$(\d+\.?\d*)', chunk)
        price = float(price_m.group(1)) if price_m else 0.0

        rating_m = re.search(r'([\d.]+) out of 5 stars', chunk)
        rating = float(rating_m.group(1)) if rating_m else 0.0

        reviews = 0
        rev_m = re.search(r'>(\d[\d,]*)</(?:span|a)>', chunk)
        if rev_m:
            reviews = int(rev_m.group(1).replace(",", ""))

        if source == "Best Seller":
            demand = 10 if rank <= 5 else 9 if rank <= 15 else 8
        else:
            demand = 9 if rank <= 3 else 8 if rank <= 10 else 7

        name = re.sub(r'\s+', ' ', name)[:80]

        products.append({
            "name": name,
            "category": category,
            "price_usd": price,
            "competitor_reviews": reviews,
            "competitor_rating": rating,
            "demand_score": demand,
            "url": f"https://www.amazon.com/dp/{asin}",
            "notes": f"{source} #{rank}; comissao {commission}%",
        })

    return products


def scrape_category(category_name):
    cat = CATEGORIES.get(category_name)
    if not cat:
        return []

    products = []
    commission = cat["commission"]

    bs_url = f"https://www.amazon.com/{cat['bs_path']}"
    print(f"[scraper] Buscando Best Sellers: {category_name}...")
    html = _fetch(bs_url)
    if html:
        found = _parse_products(html, category_name, "Best Seller", commission)
        products.extend(found[:10])
        print(f"[scraper] OK: {len(found)} produto(s) em Best Sellers {category_name}.")
    else:
        print(f"[scraper] AVISO: Não foi possível acessar Best Sellers {category_name}.")

    time.sleep(1.5)

    nr_url = f"https://www.amazon.com/{cat['nr_path']}"
    print(f"[scraper] Buscando New Releases: {category_name}...")
    html = _fetch(nr_url)
    if html:
        found = _parse_products(html, category_name, "New Release", commission)
        products.extend(found[:10])
        print(f"[scraper] OK: {len(found)} produto(s) em New Releases {category_name}.")
    else:
        print(f"[scraper] AVISO: Não foi possível acessar New Releases {category_name}.")

    time.sleep(1.5)
    return products


def run(config=None):
    """Busca produtos em todas as categorias configuradas."""
    print("[scraper] Iniciando busca na Amazon (Best Sellers + New Releases)...")
    all_products = []

    for cat_name in CATEGORIES:
        try:
            products = scrape_category(cat_name)
            all_products.extend(products)
        except Exception as e:
            print(f"[scraper] ERRO na categoria {cat_name}: {e}")

    seen_urls = set()
    unique = []
    for p in all_products:
        if p["url"] not in seen_urls and p["price_usd"] > 0:
            seen_urls.add(p["url"])
            unique.append(p)

    print(f"[scraper] Concluído: {len(unique)} produto(s) único(s) encontrado(s).")
    return unique
