"""
Jetayu Gadgets — Competitor Price Monitor
Scrapes prices from competitor product pages and outputs data.json
"""

import json
import re
import time
import random
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ─── Product catalog from your Excel file ────────────────────────────────────
PRODUCTS = [
    {
        "id": 1, "name": "Neo Fly More Combo",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-neo-motion-fly-more-combo-rc-motion-3-fpv-goggles-extra-battery",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-consumer-drone/dji-neo-fly-more-combo/",
            "Everse":      "https://everse.in/product/dji-neo-fly-more-combo",
            "Airytek":     "https://airytek.com/dji-neo-drone-fly-more-combo/",
            "Hobitech":    "https://hobitech.in/product/dji-neo-motion-fly-more-combo/",
            "Designinfo":  "https://www.designinfo.in/p/dji-neo-fly-more-combo-3-batteries-remote-charging-hub/",
        }
    },
    {
        "id": 2, "name": "Neo Standard",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-neo-standard-drone-only",
        }
    },
    {
        "id": 3, "name": "Mini 2 SE Standard",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-mini-2-se-standard",
            "Xboom":       "https://www.xboom.in/shop/drone-guide/recreational/dji-mini-2-se-drone-camera/",
            "Everse":      "https://everse.in/product/dji-mini-2se-standard",
            "Airytek":     "https://airytek.com/dji-mini-2-se-drone/",
            "Hobitech":    "https://hobitech.in/product/dji-mini-2-se-standard-drone/",
            "Designinfo":  "https://www.designinfo.in/p/dji-mini-2-se-drone/",
        }
    },
    {
        "id": 4, "name": "Mini 4K Fly More Combo",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-mini-4k-fly-more-combo",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-drone/dji-mini-4k-fly-more-combo/",
            "Everse":      "https://everse.in/product/dji-mini-4k-fly-more-combo",
            "Airytek":     "https://airytek.com/dji-mini-4k-drone-fly-more-combo/",
            "Hobitech":    "https://hobitech.in/product/dji-mini-4k-fly-more-combo/",
            "Designinfo":  "https://www.designinfo.in/p/dji-mini-4k-drone-fly-more-combo-3-battery-charging-hub-kit/",
        }
    },
    {
        "id": 5, "name": "Mini 3 Fly More Combo with RC",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-mini-3-fly-more-combo-drone-camera-with-rc",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-consumer-drone/dji-mini-3-fly-more-combo-remote-controller-with-screen/",
            "Everse":      "https://everse.in/product/dji-mini-3-fly-more-combo-drone-camera-with-rc",
            "Hobitech":    "https://hobitech.in/product/dji-mini-3-fly-more-combo-dji-rc-51/",
            "Designinfo":  "https://www.designinfo.in/p/dji-mini-3-drone-with-dji-rc-remote-fly-more-combo/",
        }
    },
    {
        "id": 6, "name": "Flip Fly More Combo",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-flip-fly-more-combo-dji-rc-2",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-consumer-drone/dji-flip/dji-flip-flymore-combo-dji-rc-2/",
            "Everse":      "https://everse.in/product/dji-flip-fly-more-combo-dji-rc-2",
            "Airytek":     "https://airytek.com/dji-flip-fly-more-combo-dji-rc-2-3-batteries/",
            "Hobitech":    "https://hobitech.in/product/dji-flip-fly-more-combo-dji-rc-2/",
        }
    },
    {
        "id": 7, "name": "Mini 4 Pro Fly More Combo – 34 min",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-mini-4-pro-drone-camera-fly-more-combo-dji-rc-2-34-mins",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-consumer-drone/dji-mini-4-pro-fly-more-combo-37-min/",
            "Airytek":     "https://airytek.com/dji-mini-4-pro-drone-fly-more-combo-with-rc-2-controller/",
            "Hobitech":    "https://hobitech.in/product/dji-mini-4-pro-fly-more-combo-dji-rc-2/",
        }
    },
    {
        "id": 8, "name": "Mini 4 Pro Fly More Combo Plus – 45 min",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-mini-4-pro-drone-camera-fly-more-combo-plus-45-mins",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-consumer-drone/dji-mini-4-pro-drone-camera-fly-more-combo-plus/",
            "Everse":      "https://everse.in/product/dji-mini-4-pro-drone-camera-fly-more-combo-plus-45-mins",
            "Airytek":     "https://airytek.com/dji-mini-4-pro-drone-fly-more-combo-plus-with-rc-2-controller/",
            "Hobitech":    "https://hobitech.in/product/dji-mini-4-pro-fly-more-combo-plus-dji-rc-2/",
            "Designinfo":  "https://www.designinfo.in/p/dji-mini-4-pro-drone-plus-series-45-min-fly-more-combo-with-rc-2-controller/",
        }
    },
    {
        "id": 9, "name": "Mini 5 Pro Fly More Combo – 36 min",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-mini-5-pro-fly-more-combo-36-mins",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-drone/dji-mini-5-pro-fly-more-combo-dji-rc-2/",
            "Everse":      "https://everse.in/product/mini-5-pro-combo-36-min",
            "Designinfo":  "https://www.designinfo.in/p/dji-mini-5-pro-fly-more-combo-series-drone-36-min-battery/",
        }
    },
    {
        "id": 10, "name": "Mini 5 Pro Fly More Combo Plus – 52 min",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-mini-5-pro-flymore-combo-plus-52-mins",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-drone/dji-mini-5-pro/",
            "Everse":      "https://everse.in/product/dji-mini-5-pro",
            "Airytek":     "https://airytek.com/dji-mini-5-pro-combo-plus/",
            "Hobitech":    "https://hobitech.in/product/dji-mini-5-pro-fly-more-combo/",
        }
    },
    {
        "id": 11, "name": "Air 3S Fly More Combo RC2",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-air-3s-fly-more-combo-dji-rc-2",
            "Xboom":       "https://www.xboom.in/shop/drone-shop-by-price/rs-1-3l-rs-1-5l/dji-air-3s-fly-more-combo-dji-rc-2/",
            "Everse":      "https://everse.in/product/dji-air-3s-fly-more-combo-with-smart-controller",
            "Airytek":     "https://airytek.com/dji-air-3s-fly-more-combo-drone-with-3-batteries-rc2-remote/",
            "Hobitech":    "https://hobitech.in/product/dji-air-3s-fly-more-combo-2/",
        }
    },
    {
        "id": 12, "name": "Mavic 4 Pro Standard",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-mavic-4-pro-standard",
            "Everse":      "https://everse.in/product/dji-mavic-4-pro",
        }
    },
    {
        "id": 13, "name": "Mavic 4 Pro Fly More Combo",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-mavic-4-pro-fly-more-combo-dji-rc-2",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-consumer-drone/dji-mavic-4-pro-flymore-combo/",
            "Everse":      "https://everse.in/product/dji-mavic-4-pro-drone-fly-more-combo-with-rc-2-remote-controller",
            "Hobitech":    "https://hobitech.in/product/dji-mavic-4-pro-fly-more-combo/",
        }
    },
    {
        "id": 14, "name": "Mavic 4 Pro 512GB Creator Combo",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-mavic-4-pro-512gb-creator-combo-dji-rc-pro-2",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-consumer-drone/dji-mavic-4-pro-512gb-creator-combo-dji-rc-pro-2/",
            "Everse":      "https://everse.in/product/dji-mavic-4-pro-drone-creator-combo-with-rc-pro-2-remote-controller",
            "Hobitech":    "https://hobitech.in/product/dji-mavic-4-pro-512gb-creator-combo-dji-rc-pro-2/",
        }
    },
    {
        "id": 15, "name": "Neo 2 Combo",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-neo-2-fly-more-combo",
            "Xboom":       "https://www.xboom.in/shop/drones/selfie-drone/dji-neo/dji-neo-2-4k-smart-drone/",
            "Everse":      "https://everse.in/category/dji-neo-series",
            "Airytek":     "https://airytek.com/dji-neo-2-fly-more-combo/",
            "Hobitech":    "https://hobitech.in/product/dji-neo-2-drone-camera/",
            "Designinfo":  "https://www.designinfo.in/p/dji-neo-2-fly-more-combo/",
        }
    },
    {
        "id": 16, "name": "Neo 2 Motion Fly More Combo",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-neo-2-motion-fly-more-combo",
            "Xboom":       "https://www.xboom.in/shop/drones/selfie-drone/dji-neo/dji-neo-2-fly-motion-flymore-combo/",
            "Everse":      "https://everse.in/product/dji-neo-2-motion-fly-more-combo",
            "Airytek":     "https://airytek.com/dji-neo-2-motion-fly-more-combo/",
            "Hobitech":    "https://hobitech.in/product/dji-neo-2-motion-fly-more-combo/",
            "Designinfo":  "https://www.designinfo.in/p/dji-neo-motion-fly-more-combo-goggles-n3-rc-motion-3-controller-kit/",
        }
    },
    {
        "id": 17, "name": "Neo Motion Combo",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-neo-motion-fly-more-combo-rc-motion-3-fpv-goggles-extra-battery",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-consumer-drone/dji-neo-motion-fly-more-combo/",
            "Everse":      "https://everse.in/product/dji-neo-motion-fly-more-combo",
            "Airytek":     "https://airytek.com/dji-neo-motion-fly-more-combo-rc-motion-3-fpv-goggles-extra-battery/",
            "Hobitech":    "https://hobitech.in/product/dji-neo-motion-fly-more-combo/",
            "Designinfo":  "https://www.designinfo.in/p/dji-neo-motion-fly-more-combo-goggles-n3-rc-motion-3-controller-kit/",
        }
    },
    {
        "id": 18, "name": "DJI M4T (Mavic 4 Thermal)",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-matrice-4-thermal-m4t",
            "Xboom":       "https://www.xboom.in/shop/drones/drones-series/matrice-series/dji-matrice-4t/",
            "Everse":      "https://everse.in/product/dji-matrice-4t-worry-free-plus-combo",
            "Airytek":     "https://airytek.com/dji-matrice-4t-worry-free-plus-combo/",
            "Hobitech":    "https://hobitech.in/product/dji-matrice-4t-worry-free-plus-combo/",
        }
    },
    {
        "id": 19, "name": "DJI M4E (Mavic 4 Enterprise)",
        "urls": {
            "Everse":      "https://everse.in/product/dji-matrice-4e-worry-free-plus-combo",
            "Airytek":     "https://airytek.com/dji-matrice-4e/",
        }
    },
    {
        "id": 20, "name": "DJI Matrice 350 (M350)",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-matrice-350-rtk-m350-rtk",
            "Xboom":       "https://www.xboom.in/shop/drones/drones-series/matrice-series/dji-matrice-350-rtk-basic-combo-drone/",
            "Everse":      "https://everse.in/product/dji-matrice-350-rtk-m350-basic-combo-drone",
            "Airytek":     "https://airytek.com/dji-matrice-350-rtk-worry-free-basic-combo/",
            "Hobitech":    "https://hobitech.in/product/dji-matrice-350-rtk-drone/",
        }
    },
    {
        "id": 21, "name": "DJI Matrice 400 (M400)",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-matrice-400-m400",
            "Xboom":       "https://www.xboom.in/shop/drones/drones-series/matrice-series/dji-matrice-400/",
            "Everse":      "https://everse.in/product/dji-matrice-400",
            "Hobitech":    "https://hobitech.in/product/dji-matrice-400/",
        }
    },
]

# ─── Per-site price extraction strategies ────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def clean_price(text: str) -> Optional[int]:
    """Extract integer rupee amount from messy price strings."""
    if not text:
        return None
    text = text.replace(",", "").replace("\u20b9", "").replace("Rs.", "").replace("INR", "")
    m = re.search(r"(\d{4,7})", text)
    return int(m.group(1)) if m else None


def fetch(url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        log.warning(f"  ✗ fetch failed [{url[:60]}]: {e}")
        return None


def extract_price(soup: BeautifulSoup, competitor: str) -> Optional[int]:
    """Route to site-specific extractor."""
    extractors = {
        "Jetayu":     _jetayu,
        "Xboom":      _xboom,
        "Everse":     _everse,
        "Airytek":    _airytek,
        "Hobitech":   _hobitech,
        "Designinfo": _designinfo,
    }
    fn = extractors.get(competitor)
    return fn(soup) if fn else None


# ── Site extractors ──────────────────────────────────────────────────────────

def _shopify_generic(soup: BeautifulSoup) -> Optional[int]:
    """Generic Shopify price extractor — works for Jetayu, Airytek, Hobitech."""
    # 1. JSON-LD product schema
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            offers = data.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0]
            price = offers.get("price") or offers.get("lowPrice")
            if price:
                return int(float(price))
        except Exception:
            pass

    # 2. Shopify product JSON endpoint pattern
    for sel in [
        'span[class*="price"]',
        'div[class*="price"]',
        '[data-product-price]',
        '.price__current',
        '.product__price',
    ]:
        tag = soup.select_one(sel)
        if tag:
            p = clean_price(tag.get_text())
            if p:
                return p
    return None


def _jetayu(soup: BeautifulSoup) -> Optional[int]:
    return _shopify_generic(soup)


def _airytek(soup: BeautifulSoup) -> Optional[int]:
    # WooCommerce + Shopify hybrid
    for sel in ['.woocommerce-Price-amount', 'p.price .amount', '[class*="price"]']:
        tag = soup.select_one(sel)
        if tag:
            p = clean_price(tag.get_text())
            if p:
                return p
    return _shopify_generic(soup)


def _hobitech(soup: BeautifulSoup) -> Optional[int]:
    # WooCommerce
    for sel in [
        'p.price ins .woocommerce-Price-amount',
        'p.price .woocommerce-Price-amount',
        '.entry-summary .price .amount',
    ]:
        tag = soup.select_one(sel)
        if tag:
            p = clean_price(tag.get_text())
            if p:
                return p
    return _shopify_generic(soup)


def _xboom(soup: BeautifulSoup) -> Optional[int]:
    # WooCommerce
    for sel in [
        'p.price ins .woocommerce-Price-amount bdi',
        'p.price .woocommerce-Price-amount bdi',
        '.summary .price .amount',
        '.price bdi',
    ]:
        tag = soup.select_one(sel)
        if tag:
            p = clean_price(tag.get_text())
            if p:
                return p
    return None


def _everse(soup: BeautifulSoup) -> Optional[int]:
    for sel in [
        '.product-price',
        '.price',
        '[class*="price"]',
        'span[itemprop="price"]',
    ]:
        tag = soup.select_one(sel)
        if tag:
            attr_price = tag.get("content") or tag.get("data-price")
            if attr_price:
                p = clean_price(str(attr_price))
                if p:
                    return p
            p = clean_price(tag.get_text())
            if p:
                return p
    return _shopify_generic(soup)


def _designinfo(soup: BeautifulSoup) -> Optional[int]:
    for sel in [
        '.price-block .price',
        '.product-price',
        '[class*="price"]',
        'span[itemprop="price"]',
    ]:
        tag = soup.select_one(sel)
        if tag:
            attr = tag.get("content") or tag.get("data-price")
            if attr:
                p = clean_price(str(attr))
                if p:
                    return p
            p = clean_price(tag.get_text())
            if p:
                return p
    return _shopify_generic(soup)


# ─── Main scrape loop ─────────────────────────────────────────────────────────

def scrape_all() -> dict:
    results = []
    scraped_at = datetime.now(timezone.utc).isoformat()

    for product in PRODUCTS:
        log.info(f"── {product['name']}")
        row = {"id": product["id"], "name": product["name"], "prices": {}}

        for competitor, url in product["urls"].items():
            time.sleep(random.uniform(1.5, 3.5))   # polite delay
            log.info(f"   {competitor}: {url[:70]}")
            soup = fetch(url)
            if soup:
                price = extract_price(soup, competitor)
                row["prices"][competitor] = {
                    "price": price,
                    "url": url,
                    "scraped_ok": price is not None,
                }
                log.info(f"   → ₹{price}" if price else "   → price not found")
            else:
                row["prices"][competitor] = {"price": None, "url": url, "scraped_ok": False}

        results.append(row)

    return {"scraped_at": scraped_at, "products": results}


if __name__ == "__main__":
    import sys, pathlib
    data = scrape_all()
    out = pathlib.Path("docs/prices.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    log.info(f"Saved → {out}")
