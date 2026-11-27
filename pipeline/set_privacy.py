"""Change privacy of uploaded videos: set_privacy.py public 001 002"""
import sys

import requests

from common import OUT, load_json, log, fail, save_json
from upload import access_token

API = "https://www.googleapis.com/youtube/v3/videos"


def main():
    privacy, vids = sys.argv[1], sys.argv[2:]
    h = {"Authorization": f"Bearer {access_token()}"}
    bad = []
    for vid in vids:
        up = load_json(OUT / vid / "upload.json")
        r = requests.get(API, params={"part": "status", "id": up["video_id"]}, headers=h, timeout=30).json()
        st = r["items"][0]["status"]
        st["privacyStatus"] = privacy
        st.pop("publishAt", None)
        u = requests.put(API, params={"part": "status"}, json={"id": up["video_id"], "status": st}, headers=h, timeout=30)
        after = requests.get(API, params={"part": "status", "id": up["video_id"]}, headers=h, timeout=30).json()["items"][0]["status"]
        log(f"{vid} {up['url']}: update HTTP {u.status_code} {u.text[:200] if not u.ok else ''} -> privacy now {after['privacyStatus']} {after}")
        if after["privacyStatus"] != privacy:
            bad.append(vid)
        else:
            up["privacy"] = privacy
            save_json(OUT / vid / "upload.json", up)
    if bad:
        fail(f"privacy not changed for {bad} (unaudited API project uploads are locked private)")


if __name__ == "__main__":
    main()
