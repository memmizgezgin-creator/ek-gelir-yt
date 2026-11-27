"""Weekly topic radar: outlier videos (views far above their channel's median).

Uses the free YouTube Data API quota (about 50 units a run). Writes docs/topic-radar.md and
radar/latest.json. The topic itself is what counts: a video at 5x its channel's median
shows the subject pulls viewers, independent of channel size.
"""
from __future__ import annotations

import re
import statistics
from datetime import datetime, timezone

import requests

from common import ROOT, load_json, log, save_json
from upload import access_token

API = "https://www.googleapis.com/youtube/v3"


def secs(iso: str) -> int:
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    d, h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0, 0)
    return d * 86400 + h * 3600 + mi * 60 + s


def videos(h, ids):
    out = []
    for i in range(0, len(ids), 50):
        r = requests.get(f"{API}/videos", params={"part": "snippet,statistics,contentDetails",
                         "id": ",".join(ids[i:i + 50])}, headers=h, timeout=30).json()
        out += r.get("items", [])
    return out


def main() -> None:
    cfg = load_json(ROOT / "radar" / "channels.json")
    h = {"Authorization": f"Bearer {access_token()}"}
    now = datetime.now(timezone.utc)
    rows, seen_ch = [], []
    for handle in cfg["handles"]:
        r = requests.get(f"{API}/channels", params={"part": "snippet,contentDetails,statistics", "forHandle": handle},
                         headers=h, timeout=30).json()
        if not r.get("items"):
            log(f"radar: {handle} not found")
            continue
        ch = r["items"][0]
        up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        pl = requests.get(f"{API}/playlistItems", params={"part": "contentDetails", "playlistId": up, "maxResults": 50},
                          headers=h, timeout=30).json()
        ids = [x["contentDetails"]["videoId"] for x in pl.get("items", [])]
        vs = [v for v in videos(h, ids) if secs(v["contentDetails"].get("duration")) > 180]
        views = [int(v["statistics"].get("viewCount", 0)) for v in vs]
        if len(views) < 5:
            continue
        med = statistics.median(views)
        seen_ch.append(f"{ch['snippet']['title']} (median {int(med):,} views over {len(views)} long videos)")
        for v, n in zip(vs, views):
            age = (now - datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))).days
            if med and n / med >= cfg["outlier_ratio"] and age >= cfg["min_age_days"]:
                rows.append({"channel": ch["snippet"]["title"], "title": v["snippet"]["title"], "views": n,
                             "ratio": round(n / med, 1), "age_days": age, "url": f"https://youtu.be/{v['id']}"})
    for q in cfg.get("searches", []):
        r = requests.get(f"{API}/search", params={"part": "snippet", "q": q, "type": "video", "order": "viewCount",
                         "videoDuration": "long", "maxResults": 10}, headers=h, timeout=30).json()
        for v in videos(h, [x["id"]["videoId"] for x in r.get("items", [])]):
            rows.append({"channel": v["snippet"]["channelTitle"], "title": v["snippet"]["title"],
                         "views": int(v["statistics"].get("viewCount", 0)), "ratio": None, "age_days": None,
                         "url": f"https://youtu.be/{v['id']}", "search": q})
    rows.sort(key=lambda x: (x["ratio"] is None, -(x["ratio"] or 0), -x["views"]))
    save_json(ROOT / "radar" / "latest.json", {"date": str(now.date()), "channels": seen_ch, "rows": rows})
    md = [f"# Topic radar, {now.date()}", "", "Outliers: long videos at {0}x or more of their channel's median views. "
          "Copy the topic type and title pattern, never the content.".format(cfg["outlier_ratio"]), "",
          "Channels checked: " + "; ".join(seen_ch), "", "| Ratio | Views | Channel | Title |", "|---|---|---|---|"]
    md += [f"| {r['ratio']}x | {r['views']:,} | {r['channel']} | [{r['title']}]({r['url']}) |" for r in rows if r["ratio"]]
    md += ["", "## Top search results (by views)", "", "| Views | Channel | Title | Search |", "|---|---|---|---|"]
    md += [f"| {r['views']:,} | {r['channel']} | [{r['title']}]({r['url']}) | {r['search']} |" for r in rows if not r["ratio"]]
    (ROOT / "docs" / "topic-radar.md").write_text("\n".join(md) + "\n")
    log(f"radar: {sum(1 for r in rows if r['ratio'])} outliers from {len(seen_ch)} channels")


if __name__ == "__main__":
    main()
