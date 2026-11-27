"""Update title and description of an already uploaded video from its script front matter."""
import argparse

import requests

from common import OUT, find_script, load_json, log, parse_script, fail
from upload import access_token, description

API = "https://www.googleapis.com/youtube/v3/videos"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    vid = ap.parse_args().vid
    up = load_json(OUT / vid / "upload.json")
    if not up:
        fail(f"video {vid} has no upload.json, nothing to update")
    script = parse_script(find_script(vid))
    h = {"Authorization": f"Bearer {access_token()}"}
    r = requests.get(API, params={"part": "snippet", "id": up["video_id"]}, headers=h, timeout=30)
    items = r.json().get("items", []) if r.ok else []
    if not items:
        fail(f"video {up['video_id']} not found ({r.status_code})")
    snip = items[0]["snippet"]
    credits = load_json(OUT / vid / "credits.json", [])
    snip["title"] = script.meta["title"][:100]
    if credits:
        snip["description"] = description(script, credits)
    body = {"id": up["video_id"], "snippet": {k: snip[k] for k in
            ("title", "description", "tags", "categoryId", "defaultLanguage", "defaultAudioLanguage") if k in snip}}
    r = requests.put(API, params={"part": "snippet"}, json=body, headers=h, timeout=30)
    if not r.ok:
        fail(f"title update failed {r.status_code}: {r.text[:300]}")
    log(f"title set on {up['url']}: {snip['title']}")


if __name__ == "__main__":
    main()
