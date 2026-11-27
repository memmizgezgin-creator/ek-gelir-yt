"""Replace the thumbnail of an already uploaded video (id from out/<id>/upload.json)."""
import argparse

import requests

from common import OUT, load_json, log, fail
from upload import THUMB_URL, access_token


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    vid = ap.parse_args().vid
    up = load_json(OUT / vid / "upload.json")
    if not up:
        fail(f"video {vid} has no upload.json, nothing to update")
    r = requests.post(f"{THUMB_URL}?videoId={up['video_id']}",
                      headers={"Authorization": f"Bearer {access_token()}", "Content-Type": "image/jpeg"},
                      data=(OUT / vid / "thumbnail.jpg").read_bytes(), timeout=60)
    if not r.ok:
        fail(f"thumbnail set failed {r.status_code}: {r.text[:300]} (custom thumbnails need a phone-verified channel)")
    log(f"thumbnail set on {up['url']}")


if __name__ == "__main__":
    main()
