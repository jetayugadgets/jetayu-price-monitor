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

# ─── Persistent session (Chrome TLS impersonation + realistic headers) ─────────
session = cffi_requests.Session(impersonate="chrome124")
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Accept": "text/html,application/xhtml+xml",
})

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
    # --- V2 Products Below ---
    {"id": 22, "name": "DJI Lito 1", "group": "v2", "urls": {"Amazon": "https://www.designinfo.in/p/dji-lito-1-drone-with-rc-n3-remote/"} },
    {"id": 23, "name": "LITO X1", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-lito-x1-fly-more-combo-dji-rc-2", "Amazon": "https://www.designinfo.in/p/dji-lito-x1-fly-more-combo-dji-rc-2-3-standard-batteries-combo-kit/"} },
    {"id": 24, "name": "DJI Avata 2 Fly More Combo (Three Batteries)", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-avata-2-fly-more-combo-three-batteries", "Amazon": "https://www.amazon.in/DJI-Batteries-MicroSD-Landing-Bundle/dp/B0D5J3FHCM", "Designinfo": "https://www.designinfo.in/p/dji-avata-2-fpv-drone-with-3-battery-fly-more-combo/"} },
    {"id": 25, "name": "AVATA 360 Standalone", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-avata-360-standalone-dji-rc-2", "Designinfo": "https://www.designinfo.in/p/dji-avata-360-with-rc-2/"} },
    {"id": 26, "name": "AVATA 360 RC2", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-avata-360-standalone-dji-rc-2", "Designinfo": "https://www.designinfo.in/p/dji-avata-360-with-rc-2/"} },
    {"id": 27, "name": "AVATA 360 MOTION", "group": "v2", "urls": {"Jetayu": "https://www.jetayugadgets.com/products/dji-avata-360-motion-fly-more-combo", "Designinfo": "https://www.designinfo.in/p/dji-avata-360-motion-fly-more-combo-rc-motion-3-goggle-n3-3-batteries-kit/"} },
    {"id": 28, "name": "ACTION 4 ADVENTURE", "group": "v2", "urls": {"Amazon": "https://www.amazon.in/DJI-Osmo-Action-Adventure-Combo/dp/B0C783J9WC", "Designinfo": "https://www.designinfo.in/p/dji-osmo-action-4-camera-adventure-combo/"} },
    {"id": 29, "name": "ACTION 5 ADVENTURE", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-action-5-pro-adventure-combo-1", "Amazon": "https://www.amazon.in/DJI-Adventure-Batteries-Stabilization-Touchscreens/dp/B07FW4CZZL", "Designinfo": "https://www.designinfo.in/p/dji-osmo-action-5-pro-adventure-combo/"} },
    {"id": 30, "name": "DJI Osmo Action 6 Adventure Combo", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-action-6-adventure-combo", "Amazon": "https://www.amazon.in/DJI-Adventure-Variable-Aperture-Cold-Resistant/dp/B0FM3YTRGD", "Designinfo": "https://www.designinfo.in/p/dji-osmo-action-6-adventure-combo/"} },
    {"id": 31, "name": "OSMO NANO 64", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-nano-64-gb", "Amazon": "https://www.amazon.in/DJI-Osmo-Action-2-64G/dp/B0FBFZM45S", "Designinfo": "https://www.designinfo.in/p/dji-osmo-nano-standard-combo-64gb/"} },
    {"id": 32, "name": "OSMO NANO 128", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-nano-128gb", "Amazon": "https://www.amazon.in/Osmo-Nano-Standard-Combo-128GB/dp/B0G21XS8JX", "Designinfo": "https://www.designinfo.in/p/dji-osmo-nano-standard-combo-128gb/"} },
    {"id": 33, "name": "POCKET 3 Standard", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-pocket-3", "Amazon": "https://www.amazon.in/DJI-Stabilization-Rotatable-Touchscreen-Photography/dp/B0CG19QXWD", "Designinfo": "https://www.designinfo.in/p/dji-osmo-pocket-3-new-2023-gst-billing/"} },
    {"id": 34, "name": "POCKET 3 Creator Combo", "group": "v2", "urls": {"Jetayu": "https://www.jetayugadgets.com/products/dji-osmo-pocket-3-creator-combo", "Amazon": "https://www.amazon.in/DJI-Vlogging-Stabilization-Tracking-Photography/dp/B0CG19FGQ5", "Designinfo": "https://www.designinfo.in/p/dji-osmo-pocket-3-creator-combo-new-2023-gst-billing/"} },
    {"id": 35, "name": "POCKET 4 Standard", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-pocket-4-standard-combo", "Amazon": "https://www.amazon.in/DJI-Standard-Tracking-Touchscreen-Stabilized/dp/B0FKTBGNR8", "Designinfo": "https://www.designinfo.in/p/dji-osmo-pocket-4-standard-combo/"} },
    {"id": 36, "name": "POCKET 4 Creator Combo", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-pocket-4-creator-combo", "Amazon": "https://www.amazon.in/DJI-Tracking-Wireless-Touchscreen-Stabilized/dp/B0FKT9K6CB", "Designinfo": "https://www.designinfo.in/p/dji-osmo-pocket-4-creator-combo/"} },
    {"id": 37, "name": "POCKET 4P Standard", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-pocket-4p-standard-combo", "Amazon": "https://www.amazon.in/DJI-Dual-Lens-Wide-Angle-Stabilization-ActiveTrack/dp/B0H2MRDB2C", "Designinfo": "https://www.designinfo.in/p/dji-osmo-pocket-4p-standard-combo-black/"} },
    {"id": 38, "name": "POCKET 4P VLOG COMBO", "group": "v2", "urls": {"Jetayu": "https://www.jetayugadgets.com/products/dji-osmo-pocket-4p-vlog-combo-creator-combo", "Amazon": "https://www.amazon.in/DJI-Osmo-Pocket-4P-Wide-Angle/dp/B0H8K1VM1Q", "Designinfo": "https://www.designinfo.in/p/dji-osmo-pocket-4p-vlog-combo/"} },
    {"id": 39, "name": "MIC 2 (2TX + 1RX + Charger)", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-mic-2-2-tx-1-rx-charging-case", "Amazon": "https://www.amazon.in/Wireless-Microphone-Recording-Cancelling-Smartphone/dp/B0H7JNZ8RL", "Designinfo": "https://www.designinfo.in/p/dji-mic-2-2tx-1rx_-new-2024/"} },
    {"id": 40, "name": "DJI MIC 3 (2TX + 1RX + Charging Case)", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-mic-3-2-tx-1-rx-charging-case", "Amazon": "https://www.amazon.in/DJI-Charging-Microphone-Recording-Anti-Interference/dp/B0FPG2MQSR"} },
    {"id": 41, "name": "MIC MINI 2 (2TX + 1RX + Charger)", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-mic-mini-2-2-tx-1-rx-charging-case", "Amazon": "https://www.amazon.in/DJI-Mic-Mini-Charging-Case/dp/B0H8HTSNC1", "Designinfo": "https://www.designinfo.in/p/dji-mic-mini-2-2-tx-1-rx-charging-case-combo-kit/"} },
    {"id": 42, "name": "MIC MINI 2 (2TX + Mobile Rx + Charger)", "group": "v2", "urls": {"Amazon": "https://www.amazon.in/Mic-Mini-Microphone-Bluetooth-Cancelling/dp/B0H164H3T7", "Designinfo": "https://www.designinfo.in/p/dji-mic-mini-2-2-tx-1-mobile-rx-charging-case/"} },
    {"id": 43, "name": "MIC MINI 2S (2TX + 1RX + Charger)", "group": "v2", "urls": {"Amazon": "https://www.amazon.in/Mic-Mini-Wireless-Microphone-Charging/dp/B0HGD1GY67"} },
    {"id": 44, "name": "OSMO Mobile 7", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-mobile-7", "Amazon": "https://www.amazon.in/dp/B07FSS4R16", "Designinfo": "https://www.designinfo.in/p/dji-osmo-mobile-7-smartphone-gimbal-stabilizer-dji-om7/"} },
    {"id": 45, "name": "OSMO Mobile 7P", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-mobile-7p-series", "Amazon": "https://www.amazon.in/DJI-Stabilizer-Tracking-Lighting-Extension/dp/B07FTG84SW", "Designinfo": "https://www.designinfo.in/p/dji-om-7p-osmo-mobile-7p-smartphone-mobile-gimbal/"} },
    {"id": 46, "name": "OSMO Mobile 8", "group": "v2", "urls": {"Amazon": "https://www.amazon.in/dp/B0FJ2L67HJ", "Designinfo": "https://www.designinfo.in/p/dji-osmo-mobile-8-smartphone-gimbal/"} },
    {"id": 47, "name": "OSMO Mobile 8P", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-osmo-mobile-8p-advanced-tracking-combo", "Amazon": "https://www.amazon.in/DJI-Smartphone-Stabilizer-Multifunctional-ActiveTrack/dp/B0G39B4DNL", "Designinfo": "https://www.designinfo.in/p/dji-osmo-mobile-8p-advanced-tracking-combo/"} },
    {"id": 48, "name": "DJI RS 4", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-rs4", "Amazon": "https://www.amazon.in/dp/B0CS6LC1ZQ", "Designinfo": "https://www.designinfo.in/p/dji-rs-4-gimbal-stabilizer/"} },
    {"id": 49, "name": "DJI RS 4 Pro", "group": "v2", "urls": {"Jetayu": "https://www.jetayugadgets.com/products/dji-rs4-pro", "Amazon": "https://www.amazon.in/dp/B0CS6J2648", "Designinfo": "https://www.designinfo.in/p/dji-rs-4-pro-gimbal-stabilizer/"} },
    {"id": 50, "name": "DJI RS 5", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/dji-rs-5", "Amazon": "https://www.amazon.in/DJI-RS-Camera-Stabiliser-Gimbal/dp/B0FLKBCT26", "Designinfo": "https://www.designinfo.in/p/dji-rs-5-gimbal-stabilizer/"} },
    {"id": 51, "name": "INSTA 360 X5", "group": "v2", "urls": {"Jetayu": "https://jetayugadgets.com/products/insta360-x5", "Amazon": "https://www.amazon.in/Insta360-Waterproof-Replaceable-Built-Stabilization/dp/B0F3P4G8SY", "Designinfo": "https://www.designinfo.in/p/insta360-x5-360-8k-camera/"} },
    {"id": 52, "name": "INSTA 360 X6 Essentials Bundle Black", "group": "v2", "urls": {"Amazon": "https://www.amazon.in/Insta360-Essentials-Bundle-Black-Replaceable/dp/B0H8SQKQKP", "Designinfo": "https://www.designinfo.in/p/insta360-x6-essentials-bundle-black/"} },
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def clean_price(text: str) -> Optional[int]:
    if not text:
        return None
    text = str(text).replace(",", "").replace("\u20b9", "").replace("Rs.", "").replace("INR", "").strip()
    m = re.search(r"(\d{4,7})", text)
    return int(m.group(1)) if m else None


def fetch(url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
    try:
        r = session.get(url, timeout=timeout)

        if r.status_code == 403:
            log.warning(f"  🚫 BLOCKED (403) → {url}")
            return None

        if r.status_code != 200:
            log.warning(f"  ✗ [{url[:55]}]: HTTP {r.status_code}")
            return None

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


def _amazon(url: str) -> Optional[int]:
    soup = fetch(url)
    if not soup:
        return None
    tag = soup.select_one('span.a-price-whole')
    if tag:
        p = clean_price(tag.get_text())
        if p and 1000 < p < 10000000:
            return p
    return extract_price_generic(soup)

EXTRACTORS = {
    "Jetayu":     _jetayu,
    "Xboom":      _xboom,
    "Everse":     _everse,
    "Airytek":    _airytek,
    "Hobitech":   _hobitech,
    "Designinfo": _designinfo,
    "Amazon":     _amazon,
}

# ─── Main ────────────────────────────────────────────────────────────────────

def scrape_all() -> dict:
    results = []
    scraped_at = datetime.now(timezone.utc).isoformat()

    for product in PRODUCTS:
        log.info(f"── {product['name']}")
        row = {"id": product["id"], "name": product["name"], "group": product.get("group", "v1"), "prices": {}}

        for competitor, url in product["urls"].items():
            time.sleep(random.uniform(1, 2))  # anti-bot delay between requests
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
