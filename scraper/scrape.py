"""
Jetayu Gadgets — Competitor Price Monitor
Uses curl_cffi to impersonate Chrome TLS fingerprint — bypasses Cloudflare.
"""

import json
import re
import time
import random
import logging
import pathlib
from datetime import datetime, timezone
from typing import Optional

from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ─── Product catalog ──────────────────────────────────────────────────────────
PRODUCTS = [
    {
        "id": 1, "name": "Neo Fly More Combo",
        "urls": {
            # "Jetayu":      "https://jetayugadgets.com/products/dji-neo-motion-fly-more-combo-rc-motion-3-fpv-goggles-extra-battery",
            "Jetayu":      "https://jetayugadgets.com/products/dji-neo-fly-more-drone-combo-with-3-batteries-remote-charging-hub",
            "Xboom":       "https://www.xboom.in/shop/brands/dji/dji-consumer-drone/dji-neo-fly-more-combo/",
            "Everse":      "https://everse.in/product/dji-neo-fly-more-combo",
            "Airytek":     "https://airytek.com/dji-neo-drone-fly-more-combo/",
            # "Hobitech":    "https://hobitech.in/product/dji-neo-motion-fly-more-combo/",
            "Hobitech":    "https://hobitech.in/product/dji-neo-fly-more-drone-combo-with-3-batteries/",
            "Designinfo":  "https://www.designinfo.in/p/dji-neo-fly-more-combo-3-batteries-remote-charging-hub/",
        }
    },
    {
        "id": 2, "name": "Neo Standard",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-neo-standard-drone-only",
            "Everse": "https://everse.in/product/dji-neo-no-rc"
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
            "Everse":   "https://everse.in/product/dji-mini-4-pro-drone-camera-fly-more-combo-dji-rc-2-34-mins",
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
           "Airytek":    "https://airytek.com/dji-mavic-4-pro-drone-with-512gb-creator-combo/",
            "Hobitech":    "https://hobitech.in/product/dji-mavic-4-pro-512gb-creator-combo-dji-rc-pro-2/",
        }
    },
    {
        "id": 15, "name": "Neo 2 Combo",
        "urls": {
            "Jetayu":      "https://jetayugadgets.com/products/dji-neo-2-fly-more-combo",
            "Xboom":       "https://www.xboom.in/shop/drones/selfie-drone/dji-neo/dji-neo-2-4k-smart-drone/",
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
        "id": 19, "name": "DJI M4E (Matrice 4 Enterprise)",
        "urls": {
           "Jetayu":  "https://jetayugadgets.com/products/dji-matrice-4-enterprise-m4e",
            "Xboom":"https://www.xboom.in/shop/brands/dji/dji-enterprise-series/dji-matrice-4e/",
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

# ─── Helpers ─────────────────────────────────────────────────────────────────

def clean_price(text: str) -> Optional[int]:
    if not text:
        return None
    text = str(text).replace(",", "").replace("\u20b9", "").replace("Rs.", "").replace("INR", "").strip()
    m = re.search(r"(\d{4,7})", text)
    return int(m.group(1)) if m else None


def fetch(url: str, timeout: int = 20) -> Optional[BeautifulSoup]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://www.google.com/",
            "Accept": "text/html,application/xhtml+xml",
        }

        r = cffi_requests.get(
            url,
            impersonate="chrome124",
            headers=headers,
            timeout=timeout,
        )

        if r.status_code == 403:
            log.warning(f"  🚫 BLOCKED (403) → {url}")
            return None

        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")

    except Exception as e:
        log.warning(f"  ✗ [{url[:55]}]: {e}")
        return None


def extract_price_generic(soup: BeautifulSoup) -> Optional[int]:
    """Try every known price pattern — works across Shopify and WooCommerce."""

    # 1. JSON-LD Product schema (most reliable when present)
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            if not isinstance(data, dict):
                continue
            offers = data.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0]
            price = offers.get("price") or offers.get("lowPrice")
            if price:
                p = int(float(str(price).replace(",", "")))
                if 1000 < p < 10000000:
                    return p
        except Exception:
            pass

    # 2. Meta og:price or product:price
    for meta in soup.find_all("meta"):
        prop = meta.get("property", "") + meta.get("name", "")
        if "price" in prop.lower():
            val = meta.get("content", "")
            p = clean_price(val)
            if p and 1000 < p < 10000000:
                return p

    # 3. WooCommerce selectors
    for sel in [
        "p.price ins .woocommerce-Price-amount bdi",
        "p.price .woocommerce-Price-amount bdi",
        ".woocommerce-Price-amount bdi",
        ".entry-summary .price .amount",
    ]:
        tag = soup.select_one(sel)
        if tag:
            p = clean_price(tag.get_text())
            if p and 1000 < p < 10000000:
                return p

    # 4. Shopify selectors
    for sel in [
        '[class*="price__current"]',
        '[class*="price-item--sale"]',
        '[class*="price-item--regular"]',
        '.product__price',
        '[data-product-price]',
    ]:
        tag = soup.select_one(sel)
        if tag:
            val = tag.get("content") or tag.get("data-product-price") or tag.get_text()
            p = clean_price(str(val))
            if p and 1000 < p < 10000000:
                return p

    # 5. Shopify inline JSON (window.ShopifyAnalytics or __st)
    for script in soup.find_all("script"):
        txt = script.string or ""
        if '"price"' in txt and "Shopify" in txt:
            m = re.search(r'"price"\s*:\s*(\d+)', txt)
            if m:
                paise = int(m.group(1))
                # Shopify stores price in paise (×100)
                rupees = paise // 100
                if 1000 < rupees < 10000000:
                    return rupees

    # 6. Any span/div containing ₹ followed by digits
    for tag in soup.find_all(["span", "div", "p"], string=re.compile(r"[\u20b9Rs]\s*[\d,]{4,}")):
        p = clean_price(tag.get_text())
        if p and 1000 < p < 10000000:
            return p

    return None


# ─── Site extractors ─────────────────────────────────────────────────────────

def _jetayu(url: str) -> Optional[int]:
    soup = fetch(url)
    if not soup:
        return None
    # Shopify stores price as paise in inline JSON
    for script in soup.find_all("script"):
        txt = script.string or ""
        if "price" in txt and ("ShopifyAnalytics" in txt or "meta" in txt.lower()):
            # Pattern: "price":12990000 (in paise)
            m = re.search(r'"price"\s*:\s*(\d{6,9})', txt)
            if m:
                paise = int(m.group(1))
                rupees = paise // 100
                if 1000 < rupees < 10000000:
                    return rupees
            # Pattern: "price": "64999.00"
            m = re.search(r'"price"\s*:\s*"([\d.]+)"', txt)
            if m:
                p = int(float(m.group(1)))
                if 1000 < p < 10000000:
                    return p
    return extract_price_generic(soup)


def _xboom(url: str) -> Optional[int]:
    soup = fetch(url)
    return extract_price_generic(soup) if soup else None


def _everse(url: str) -> Optional[int]:
    soup = fetch(url)
    return extract_price_generic(soup) if soup else None


def _airytek(url: str) -> Optional[int]:
    soup = fetch(url)
    return extract_price_generic(soup) if soup else None


def _hobitech(url: str) -> Optional[int]:
    soup = fetch(url)
    return extract_price_generic(soup) if soup else None


def _designinfo(url: str) -> Optional[int]:
    soup = fetch(url)
    return extract_price_generic(soup) if soup else None


EXTRACTORS = {
    "Jetayu":     _jetayu,
    "Xboom":      _xboom,
    "Everse":     _everse,
    "Airytek":    _airytek,
    "Hobitech":   _hobitech,
    "Designinfo": _designinfo,
}

# ─── Main ────────────────────────────────────────────────────────────────────

def scrape_all() -> dict:
    results = []
    scraped_at = datetime.now(timezone.utc).isoformat()

    for product in PRODUCTS:
        log.info(f"── {product['name']}")
        row = {"id": product["id"], "name": product["name"], "prices": {}}

        for competitor, url in product["urls"].items():
            time.sleep(random.uniform(2, 4))
            log.info(f"   {competitor}: {url[:70]}")
            fn = EXTRACTORS.get(competitor)
            price = fn(url) if fn else None
            row["prices"][competitor] = {
                "price": price,
                "url": url,
                "scraped_ok": price is not None,
            }
            log.info(f"   → ₹{price:,}" if price else "   → not found")

        results.append(row)

    return {"scraped_at": scraped_at, "products": results}


if __name__ == "__main__":
    data = scrape_all()
    out = pathlib.Path("docs/prices.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    log.info(f"Saved → {out}")
