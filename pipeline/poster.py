"""Patent drawing posters for print on demand (public domain only).

Reads posters/list.json: [{"file": "File:....jpg", "title": "...", "subtitle": "US Patent 123,456 · 1864"}]
Downloads the original from Wikimedia Commons, refuses anything that is not public domain,
cleans the scan (grey, levels, trim) and sets it on a warm paper background with a title block.
Writes posters/out/<slug>-18x24.png (5400x7200, 300 dpi) and a small preview.
"""
from __future__ import annotations

import io
import json
import re
from pathlib import Path

import requests
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

from common import ROOT, log
from images import API, UA, polite_get

W, H = 5400, 7200
PAPER = (241, 233, 216)
INK = (38, 33, 28)
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def info(session, title):
    r = polite_get(session, API, params={"action": "query", "titles": title, "prop": "imageinfo", "format": "json",
                                          "iiprop": "url|extmetadata|size"}, timeout=30).json()
    page = next(iter(r["query"]["pages"].values()))
    return (page.get("imageinfo") or [{}])[0]


def public_domain(meta: dict) -> bool:
    blob = " ".join((meta.get(k, {}).get("value") or "").lower() for k in ("License", "LicenseShortName", "UsageTerms"))
    return ("public domain" in blob or blob.strip().startswith("pd") or " pd" in blob or "cc0" in blob) and "cc-by" not in blob


def clean(img: Image.Image) -> Image.Image:
    g = ImageOps.grayscale(img)
    g = ImageOps.autocontrast(g, cutoff=1)
    bg = Image.new("L", g.size, 255)
    box = ImageChops.difference(g, bg).point(lambda p: 255 if p > 40 else 0).getbbox()
    if box:
        pad = 40
        g = g.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(g.width, box[2] + pad), min(g.height, box[3] + pad)))
    # ink on paper: dark lines become INK, white becomes transparent so the paper shows through
    alpha = ImageOps.invert(g)
    layer = Image.new("RGBA", g.size, INK + (0,))
    layer.putalpha(alpha)
    return layer


def render(item: dict, session) -> Path | None:
    ii = info(session, item["file"])
    if not ii.get("url"):
        log(f"poster: {item['file']} not found")
        return None
    if not public_domain(ii.get("extmetadata", {})):
        log(f"poster: {item['file']} is not public domain, skipped")
        return None
    raw = Image.open(io.BytesIO(polite_get(session, ii["url"], timeout=120).content)).convert("RGB")
    art = clean(raw)
    canvas = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(canvas)
    margin, text_h = 420, 1050
    box_w, box_h = W - 2 * margin, H - 2 * margin - text_h
    scale = min(box_w / art.width, box_h / art.height)
    art = art.resize((int(art.width * scale), int(art.height * scale)), Image.LANCZOS)
    canvas.paste(art, (margin + (box_w - art.width) // 2, margin + (box_h - art.height) // 2), art)
    d.rectangle([margin - 120, margin - 120, W - margin + 120, H - margin + 120], outline=INK, width=10)
    y = H - margin - text_h + 260
    d.line([margin + 600, y - 120, W - margin - 600, y - 120], fill=INK, width=6)
    for text, font, gap in ((item["title"].upper(), ImageFont.truetype(SERIF_B, 230), 330),
                            (item.get("subtitle", ""), ImageFont.truetype(SERIF, 130), 200)):
        tw = d.textlength(text, font=font)
        while tw > W - 2 * margin and font.size > 60:
            font = ImageFont.truetype(font.path, font.size - 10)
            tw = d.textlength(text, font=font)
        d.text(((W - tw) / 2, y), text, font=font, fill=INK)
        y += gap
    out = ROOT / "posters" / "out"
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{slug(item['title'])}-18x24.png"
    canvas.save(p, dpi=(300, 300), optimize=True)
    canvas.resize((600, 800)).save(out / f"{slug(item['title'])}-preview.jpg", quality=85)
    log(f"poster: {p.name} from {item['file']} ({raw.width}x{raw.height})")
    return p


def main() -> None:
    items = json.loads((ROOT / "posters" / "list.json").read_text())
    s = requests.Session()
    s.headers["User-Agent"] = UA
    made = [p for it in items if (p := render(it, s))]
    log(f"posters: {len(made)} of {len(items)}")


if __name__ == "__main__":
    main()
