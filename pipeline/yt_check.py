"""Check uploaded videos on YouTube: privacy, processing, duration, thumbnail, captions."""
import sys

import requests

from common import OUT, load_json, log
from upload import access_token

API = "https://www.googleapis.com/youtube/v3"


def main():
    h = {"Authorization": f"Bearer {access_token()}"}
    ch = requests.get(f"{API}/channels", params={"part": "snippet,status", "mine": "true"}, headers=h, timeout=30).json()
    for c in ch.get("items", []):
        log(f"channel {c['id']} {c['snippet']['title']} longUploads={c.get('status', {}).get('longUploadsStatus')}")
    sr = requests.get(f"{API}/search", params={"part": "snippet", "forMine": "true", "type": "video",
                                               "maxResults": 10}, headers=h, timeout=30).json()
    log(f"my videos: {[i.get('id') for i in sr.get('items', [])]} {sr.get('error', '')}")
    for vid in sys.argv[1:]:
        up = load_json(OUT / vid / "upload.json")
        if not up:
            log(f"{vid}: no upload.json")
            continue
        r = requests.get(f"{API}/videos", params={"part": "snippet,status,contentDetails,processingDetails",
                                                   "id": up["video_id"]}, headers=h, timeout=30).json()
        if not r.get("items"):
            log(f"{vid}: {up['video_id']} NOT FOUND on YouTube: {str(r)[:300]}")
            continue
        v = r["items"][0]
        thumbs = v["snippet"].get("thumbnails", {})
        caps = requests.get(f"{API}/captions", params={"part": "snippet", "videoId": up["video_id"]},
                            headers=h, timeout=30).json().get("items", [])
        log(f"{vid}: {up['url']} title='{v['snippet']['title'][:60]}' privacy={v['status']['privacyStatus']} "
            f"upload={v['status']['uploadStatus']} duration={v['contentDetails']['duration']} "
            f"processing={v.get('processingDetails', {}).get('processingStatus')} "
            f"thumb={'maxres' in thumbs and 'custom-ish' or 'auto'} captions={len(caps)}")


if __name__ == "__main__":
    main()
