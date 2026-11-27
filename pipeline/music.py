"""Background music bed: calm CC BY tracks from incompetech.com (Kevin MacLeod).

music.py fetch        download every track in music/tracks.json to assets/music/ (skips missing ones)
music.py pick <id>    choose a track for the episode, write out/<id>/music.json with the credit line
The mix itself happens in shots.py: low volume, ducked under the voice, fade in and out.
"""
from __future__ import annotations

import sys
import time
import zlib
from urllib.parse import quote

import requests

from common import ASSETS, OUT, ROOT, load_json, log, save_json, fail

BASE = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/"
DIR = ASSETS / "music"


def fetch() -> None:
    spec = load_json(ROOT / "music" / "tracks.json")
    DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for t in spec["tracks"]:
        dst = DIR / f"{t['title']}.mp3"
        if dst.exists() and dst.stat().st_size > 100_000:
            ok += 1
            continue
        for attempt in range(3):
            try:
                r = requests.get(BASE + quote(t["title"]) + ".mp3", timeout=60,
                                 headers={"User-Agent": "ek-gelir-yt (github.com/memmizgezgin-creator/ek-gelir-yt)"})
                if r.ok and len(r.content) > 100_000 and (r.content[:3] == b"ID3" or r.content[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
                    dst.write_bytes(r.content)
                    ok += 1
                    break
                log(f"music {t['title']}: {r.status_code} {r.headers.get('content-type')}")
                break
            except requests.RequestException as e:
                log(f"music {t['title']}: {e}")
                time.sleep(5 * (attempt + 1))
    log(f"music: {ok} tracks ready")


def pick(vid: str) -> None:
    spec = load_json(ROOT / "music" / "tracks.json")
    have = [t for t in spec["tracks"] if (DIR / f"{t['title']}.mp3").exists()]
    if not have:
        fail("no music tracks downloaded (run music.py fetch)")
    t = have[zlib.crc32(vid.encode()) % len(have)]
    credit = f'Music: "{t["title"]}" Kevin MacLeod (incompetech.com), licensed under {spec["license"]}'
    save_json(OUT / vid / "music.json", {"title": t["title"], "file": str(DIR / f"{t['title']}.mp3"), "credit": credit})
    log(f"music for {vid}: {t['title']}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        fetch()
    elif len(sys.argv) > 2 and sys.argv[1] == "pick":
        pick(sys.argv[2])
    else:
        fail("usage: music.py fetch | pick <id>")
