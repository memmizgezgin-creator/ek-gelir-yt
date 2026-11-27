"""Images from Wikimedia Commons with license records.

Reads scripts/<id>-<slug>.images.json: {"key": ["search query", ...], ...}
Only public domain, CC0, CC BY and CC BY-SA files are accepted. Anything
else (NC, ND, fair use, unknown) is skipped. If a key ends up empty, the
renderer falls back to a plain text card, never to an unlicensed image.

Writes assets/<id>/<key>-<n>.jpg and out/<id>/credits.json + credits.txt.
"""
from __future__ import annotations

import argparse
import html
import re
import time

import requests

from common import ASSETS, OUT, find_script, load_json, log, save_json, fail

API = "https://commons.wikimedia.org/w/api.php"
UA = "ek-gelir-yt/1.0 (https://github.com/memmizgezgin-creator/ek-gelir-yt; archive documentary pipeline) python-requests"
THUMB_WIDTH = 1280      # a standard Wikimedia thumbnail step; odd sizes and originals get rate limited
API_PAUSE = 1.5
DL_PAUSE = 2.0
PER_KEY = 3
MIN_WIDTH = 800
BAD_WORDS = ("logo", "icon", "map of", "flag of", "coat of arms", "signature")


def license_ok(meta: dict) -> str | None:
    lic = (meta.get("License", {}).get("value") or "").lower()
    short = (meta.get("LicenseShortName", {}).get("value") or "").lower()
    terms = (meta.get("UsageTerms", {}).get("value") or "").lower()
    blob = " ".join([lic, short, terms])
    if any(x in blob for x in ("-nc", " nc", "noncommercial", "-nd", "noderiv", "fair use", "non-free")):
        return None
    if lic.startswith("pd") or "public domain" in blob or short.startswith("pd"):
        return meta.get("LicenseShortName", {}).get("value") or "Public domain"
    if lic == "cc0" or "cc0" in short:
        return "CC0"
    if re.match(r"cc-by(-sa)?-\d", lic) or re.match(r"cc by(-sa)? \d", short):
        return meta.get("LicenseShortName", {}).get("value") or lic.upper()
    return None


def strip_html(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def search(session: requests.Session, query: str) -> list[dict]:
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrnamespace": 6, "gsrlimit": 20, "gsrsearch": f"{query} filetype:bitmap",
        "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": THUMB_WIDTH,
    }
    for attempt in range(6):
        r = polite_get(session, API, params=params, timeout=30)
        if r is not None and r.ok:
            time.sleep(API_PAUSE)
            pages = r.json().get("query", {}).get("pages", {})
            return sorted(pages.values(), key=lambda p: p.get("index", 99))
    log(f"commons search gave up for '{query}', key falls back to other queries")
    return []


def polite_get(session: requests.Session, url: str, **kw):
    """GET with Retry-After aware backoff for 429/5xx. Returns None after retries."""
    for attempt in range(6):
        try:
            r = session.get(url, **kw)
        except requests.RequestException as e:
            log(f"network retry {attempt + 1}: {e}")
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 429 or r.status_code >= 500:
            wait = int(r.headers.get("Retry-After", "0") or 0) or 10 * (attempt + 1)
            log(f"{r.status_code} from {url.split('?')[0][:80]}, waiting {wait}s")
            time.sleep(min(wait, 120))
            continue
        return r
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    args = ap.parse_args()
    script_path = find_script(args.vid)
    qfile = script_path.with_suffix(".images.json")
    queries = load_json(qfile)
    if not queries:
        fail(f"missing {qfile.name}")

    session = requests.Session()
    session.headers["User-Agent"] = UA
    dest = ASSETS / args.vid
    dest.mkdir(parents=True, exist_ok=True)
    credits: list[dict] = []
    used_titles: set[str] = set()

    for key, qs in queries.items():
        got = 0
        for q in qs:
            if got >= PER_KEY:
                break
            for page in search(session, q):
                if got >= PER_KEY:
                    break
                title = page.get("title", "")
                if title in used_titles or any(b in title.lower() for b in BAD_WORDS):
                    continue
                info = (page.get("imageinfo") or [{}])[0]
                if info.get("mime") not in ("image/jpeg", "image/png", "image/tiff"):
                    continue
                if info.get("width", 0) < MIN_WIDTH:
                    continue
                meta = info.get("extmetadata", {})
                lic = license_ok(meta)
                if not lic:
                    continue
                url = info.get("thumburl")
                if not url:
                    continue
                r = polite_get(session, url, timeout=60)
                time.sleep(DL_PAUSE)
                if r is None or not r.ok:
                    log(f"download failed {title}: {getattr(r, 'status_code', 'no response')}")
                    continue
                fname = f"{key}-{got + 1}.jpg" if "jpeg" in r.headers.get("content-type", "jpeg") else f"{key}-{got + 1}.png"
                (dest / fname).write_bytes(r.content)
                used_titles.add(title)
                credits.append({
                    "key": key, "file": fname, "title": title,
                    "license": lic,
                    "license_url": strip_html(meta.get("LicenseUrl", {}).get("value", "")),
                    "artist": strip_html(meta.get("Artist", {}).get("value", "")) or "Unknown author",
                    "credit": strip_html(meta.get("Credit", {}).get("value", "")),
                    "source": info.get("descriptionurl", ""),
                })
                got += 1
        log(f"images '{key}': {got}")

    save_json(OUT / args.vid / "credits.json", credits)
    lines = [f"Image credits for video {args.vid}", ""]
    for c in credits:
        lines.append(f"{c['file']}: {c['title'].removeprefix('File:')} | {c['artist']} | {c['license']} | {c['source']}")
    (OUT / args.vid / "credits.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    empty = [k for k in queries if not any(c["key"] == k for c in credits)]
    if empty:
        log(f"keys with no licensed image (text card fallback): {', '.join(empty)}")
    log(f"{len(credits)} images with license records")


if __name__ == "__main__":
    main()
