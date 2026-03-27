# Jetayu Gadgets — Competitor Price Monitor

Automated daily price scraper for 21 DJI products across 6 competitors.  
Runs via **GitHub Actions** every morning. No server needed. Completely free.

---

## How it works

```
GitHub Actions (cron: daily 6:30 AM IST)
  └── scraper/scrape.py   ← visits each competitor URL, extracts price
        └── data/prices.json  ← saved back to repo
              └── docs/index.html  ← SPA reads this file from same origin (no CORS!)
```

---

## Setup (one-time, ~10 minutes)

### 1. Fork / clone this repo to your GitHub account

### 2. Enable GitHub Pages
- Go to **Settings → Pages**
- Source: **Deploy from branch → `main` → `/docs` folder**
- Your dashboard will be at: `https://YOUR-USERNAME.github.io/jetayu-price-monitor/`

### 3. That's it. 
GitHub Actions will run the scraper daily at 6:30 AM IST and commit fresh prices.  
You can also trigger it manually: **Actions → Scrape Competitor Prices → Run workflow**

---

## Project structure

```
jetayu-price-monitor/
├── .github/
│   └── workflows/
│       └── scrape.yml       ← GitHub Actions cron job
├── scraper/
│   ├── scrape.py            ← Main scraper (all 21 products × 6 sites)
│   └── requirements.txt     ← requests, beautifulsoup4, lxml
├── data/
│   └── prices.json          ← Auto-updated by scraper (committed by bot)
└── docs/
    └── index.html           ← The dashboard SPA (served by GitHub Pages)
```

---

## Adding new products

Edit `PRODUCTS` list in `scraper/scrape.py`:

```python
{
    "id": 22,
    "name": "Your Product Name",
    "urls": {
        "Jetayu":   "https://jetayugadgets.com/products/...",
        "Xboom":    "https://www.xboom.in/shop/...",
        # Add only the sites that carry this product
    }
},
```

---

## Fixing a broken extractor

If a site redesigns and prices stop showing, find the right CSS selector:

1. Open the product page in Chrome
2. Right-click the price → **Inspect**
3. Find the element's class (e.g. `.product-price`)
4. Update the relevant `_sitename()` function in `scrape.py`

---

## Competitors tracked

| Competitor  | Platform         | Notes                        |
|-------------|------------------|------------------------------|
| Jetayu      | Shopify          | Your own store               |
| Xboom       | WooCommerce      | xboom.in                     |
| Everse      | Custom           | everse.in                    |
| Airytek     | WooCommerce      | airytek.com                  |
| Hobitech    | WooCommerce      | hobitech.in                  |
| Designinfo  | Custom           | designinfo.in                |
