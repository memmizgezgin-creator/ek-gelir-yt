"""Upload to YouTube with the Data API v3 (free quota).

Needs repo secrets YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
(one-time OAuth consent, see docs/setup.md). Privacy comes from the repo
variable YT_PRIVACY: "private" until the API audit is approved, then "public".
Uploads the video, the thumbnail and the SRT captions.
Writes out/<id>/upload.json with the video id.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import requests

from common import OUT, find_script, load_json, log, parse_script, save_json, fail

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
THUMB_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
CAPTION_URL = "https://www.googleapis.com/upload/youtube/v3/captions"


def access_token() -> str:
    need = ["YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"]
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        fail(f"missing secrets: {', '.join(missing)} (one-time OAuth step in docs/setup.md)")
    r = requests.post(TOKEN_URL, data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=30)
    if r.status_code != 200:
        fail(f"token refresh failed: {r.status_code} {r.text[:300]}")
    return r.json()["access_token"]


def description(script, credits: list[dict]) -> str:
    srcs = [s.strip() for s in script.meta.get("sources", "").split("|") if s.strip()]
    lines = [script.meta.get("summary", "")]
    tl = load_json(OUT / script.vid / "timeline.json", {"sections": []})
    if tl["sections"]:
        lines += ["", "Chapters"]
    for i, s in enumerate(tl["sections"]):
        t = 0 if i == 0 else int(s["start"])
        lines.append(f"{t // 60:02d}:{t % 60:02d} {s['title']}")
    lines += ["", "Sources"] + [f"- {s}" for s in srcs]
    lines += ["", "Image credits (Wikimedia Commons)"]
    lines += [f"- {c['title'].removeprefix('File:')}: {c['artist']}, {c['license']}, {c['source']}" for c in credits]
    txt = OUT / script.vid / "credits.txt"
    if not credits and txt.exists():
        lines += [txt.read_text(encoding="utf-8").strip()]
    music = load_json(OUT / script.vid / "music.json", {})
    if music.get("credit"):
        lines += ["", music["credit"]]
    lines += ["", "Narration is synthetic (text-to-speech). Script researched and fact-checked by the channel."]
    text = "\n".join(x for x in lines if x is not None).strip()
    return text[:4900]


def resumable_upload(token: str, path, meta: dict) -> str:
    size = os.path.getsize(path)
    r = requests.post(f"{UPLOAD_URL}?uploadType=resumable&part=snippet,status",
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                               "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
                      data=json.dumps(meta), timeout=60)
    if r.status_code != 200:
        fail(f"upload init failed: {r.status_code} {r.text[:400]}")
    loc = r.headers["Location"]
    for attempt in range(5):
        with open(path, "rb") as f:
            r = requests.put(loc, headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"},
                             data=f, timeout=3600)
        if r.status_code in (200, 201):
            return r.json()["id"]
        log(f"upload attempt {attempt + 1} failed: {r.status_code}")
        time.sleep(10 * (attempt + 1))
    fail(f"upload failed: {r.status_code} {r.text[:400]}")
    return ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    args = ap.parse_args()
    script_path = find_script(args.vid)
    script = parse_script(script_path)
    gate = load_json(OUT / args.vid / "gate.json", {})
    if not gate.get("passed"):
        fail("quality gate not passed, refusing to upload")
    privacy = os.environ.get("YT_PRIVACY", "private")
    old = load_json(OUT / args.vid / "upload.json", {})
    credits = load_json(OUT / args.vid / "credits.json", [])
    token = access_token()
    meta = {
        "snippet": {"title": script.meta["title"][:100], "description": description(script, credits),
                    "tags": [t.strip() for t in script.meta.get("tags", "").split(",") if t.strip()],
                    "categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": True},
    }
    mp4 = OUT / f"{script_path.stem}.mp4"
    if not mp4.exists():
        mp4 = next(OUT.glob(f"{args.vid}-*.mp4"))
    vid_id = resumable_upload(token, mp4, meta)
    log(f"uploaded {vid_id} as {privacy}")
    auth = {"Authorization": f"Bearer {token}"}
    thumb = OUT / args.vid / "thumbnail.jpg"
    if thumb.exists():
        r = requests.post(f"{THUMB_URL}?videoId={vid_id}", headers={**auth, "Content-Type": "image/jpeg"},
                          data=thumb.read_bytes(), timeout=60)
        log(f"thumbnail: {r.status_code}" + ("" if r.ok else f" {r.text[:200]} (custom thumbnails need a verified channel)"))
    srt = OUT / args.vid / f"{args.vid}.srt"
    if srt.exists():
        boundary = "ekgeliryt"
        body = (f"--{boundary}\r\nContent-Type: application/json\r\n\r\n"
                + json.dumps({"snippet": {"videoId": vid_id, "language": "en", "name": "English"}})
                + f"\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n"
                + srt.read_text(encoding="utf-8") + f"\r\n--{boundary}--")
        r = requests.post(f"{CAPTION_URL}?uploadType=multipart&part=snippet",
                          headers={**auth, "Content-Type": f"multipart/related; boundary={boundary}"},
                          data=body.encode("utf-8"), timeout=60)
        log(f"captions: {r.status_code}")
    save_json(OUT / args.vid / "upload.json", {"video_id": vid_id, "privacy": privacy,
                                              "url": f"https://youtu.be/{vid_id}"})
    # replace mode: the new upload worked, now remove the older upload of the same episode
    if os.environ.get("REPLACE_OLD") == "1" and old.get("video_id") and old["video_id"] != vid_id:
        r = requests.delete("https://www.googleapis.com/youtube/v3/videos", params={"id": old["video_id"]},
                            headers=auth, timeout=60)
        log(f"replaced: deleted old upload {old['video_id']}: {r.status_code}")


if __name__ == "__main__":
    main()
