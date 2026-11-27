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
UA = "ek-gelir-yt/1.0 (archive documentary pipeline; python-requests)"
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
        "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 1920,
    }
    for attempt in range(4):
        try:
            r = session.get(API, params=params, timeout=30)
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            return sorted(pages.values(), key=lambda p: p.get("index", 99))
        except requests.RequestException as e:
            log(f"commons search retry {attempt + 1}: {e}")
            time.sleep(2 ** attempt)
    fail(f"Wikimedia Commons unreachable for query '{query}'")
    return []


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
                url = info.get("thumburl") or info.get("url")
                try:
                    r = session.get(url, timeout=60)
                    r.raise_for_status()
                except requests.RequestException as e:
                    log(f"download failed {title}: {e}")
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
                time.sleep(0.5)
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
