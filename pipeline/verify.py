"""Quality gate. Upload runs only if every check passes. Never loosen thresholds.

1. out/<id>-<slug>.mp4 exists and is longer than MIN_MINUTES.
2. Audio and video streams end within 1.5 s of each other (sync).
3. At least MIN_IMAGES real images, each with a license record in credits.json.
4. scripts/<id>-check.md has a claims table; every status is VERIFIED, SOFTENED or REMOVED.
5. Pace: no visual longer than 9.5 s (cards 12 s), average under 8 s, no image used more than twice.
6. Visual QA (Claude reviewed every frame) scored at least MIN_VISUAL_SCORE out of 10.
Writes out/<id>/gate.json.
"""
from __future__ import annotations

import argparse
import json
import subprocess

from common import ASSETS, OUT, SCRIPTS, find_script, load_json, log, save_json

MIN_MINUTES = 12.0
MIN_IMAGES = 10
MAX_AVERAGE_SECONDS = 8.0
MIN_VISUAL_SCORE = 7
MAX_ILLUSTRATIONS = 60      # credit guard, about 55 cents per episode
MAX_CARD_SHARE = 0.25       # text cards are a spice, not the meal


def probe(path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=codec_type,duration,width,height",
                        "-of", "json", str(path)], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    args = ap.parse_args()
    script_path = find_script(args.vid)
    video = OUT / f"{script_path.stem}.mp4"
    results: dict[str, dict] = {}

    if video.exists():
        info = probe(video)
        dur = float(info.get("format", {}).get("duration", 0))
        streams = {s["codec_type"]: s for s in info.get("streams", [])}
        v = float(streams.get("video", {}).get("duration", 0))
        a = float(streams.get("audio", {}).get("duration", 0))
        results["duration"] = {"ok": dur > MIN_MINUTES * 60, "detail": f"{dur / 60:.2f} min"}
        results["sync"] = {"ok": abs(v - a) <= 1.5 and v > 0 and a > 0, "detail": f"video {v:.2f}s, audio {a:.2f}s"}
        results["resolution"] = {"ok": streams.get("video", {}).get("width") == 1920,
                                 "detail": f"{streams.get('video', {}).get('width')}x{streams.get('video', {}).get('height')}"}
    else:
        results["duration"] = {"ok": False, "detail": f"{video.name} missing"}

    credits = load_json(OUT / args.vid / "credits.json", [])
    recorded = {c["file"] for c in credits if c.get("license") and c.get("source")}
    files = sorted(p.name for p in (ASSETS / args.vid).glob("*") if p.is_file()) if (ASSETS / args.vid).exists() else []
    missing = [f for f in files if f not in recorded]
    results["images"] = {"ok": len(files) >= MIN_IMAGES,
                         "detail": f"{len(files)} licensed images (minimum {MIN_IMAGES}, text cards alone do not pass)"}
    results["licenses"] = {"ok": not missing, "detail": f"{len(files)} images, missing records: {missing or 'none'}"}

    check = SCRIPTS / f"{script_path.stem}-check.md"
    if not check.exists():
        alt = SCRIPTS / f"{args.vid}-check.md"
        check = alt if alt.exists() else check
    if check.exists():
        text = check.read_text(encoding="utf-8")
        rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in text.splitlines()
                if ln.lstrip().startswith("|") and not set(ln.strip()) <= set("|- ")]
        statuses = [r[2].upper() for r in rows[1:] if len(r) >= 3]
        bad = [s for s in statuses if s not in ("VERIFIED", "SOFTENED", "REMOVED")]
        if not statuses:
            bad = ["no claims table"]
        results["fact_check"] = {"ok": not bad, "detail": f"{len(bad)} unverified claims"}
    else:
        results["fact_check"] = {"ok": False, "detail": "check report missing"}

    rep = load_json(OUT / args.vid / "shots-report.json", {})
    if rep:
        ok = (not rep["too_long"] and not rep["reused_too_often"] and rep["average_seconds"] <= MAX_AVERAGE_SECONDS
              and rep.get("card_share", 0) <= MAX_CARD_SHARE)
        results["pace"] = {"ok": ok, "detail": f"{rep['shots']} shots, average {rep['average_seconds']}s, "
                                               f"too long {rep['too_long'] or 'none'}, overused {rep['reused_too_often'] or 'none'}, "
                                               f"cards {rep.get('card_share', 0):.0%} (max {MAX_CARD_SHARE:.0%})"}
        n_ill = rep["types"].get("illus", 0) + rep["types"].get("title", 0)
        results["illustrations"] = {"ok": n_ill <= MAX_ILLUSTRATIONS, "detail": f"{n_ill} (max {MAX_ILLUSTRATIONS})"}
        qa = load_json(OUT / args.vid / "qa.json", {})
        score = float(qa.get("score", 0))
        results["visual_qa"] = {"ok": score >= MIN_VISUAL_SCORE, "detail": f"score {score} (minimum {MIN_VISUAL_SCORE})"}
    else:
        results["pace"] = {"ok": False, "detail": "shots-report.json missing (render v2 did not run)"}

    passed = all(r["ok"] for r in results.values())
    save_json(OUT / args.vid / "gate.json", {"passed": passed, "checks": results})
    for k, r in results.items():
        log(f"gate {k}: {'PASS' if r['ok'] else 'FAIL'} ({r['detail']})")
    if not passed:
        raise SystemExit(1)
    log("gate passed")


if __name__ == "__main__":
    main()
