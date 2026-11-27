"""Render v2: shot-based video. A new visual every 5 to 8 seconds, timed to the narration.

Shot types (from <script>.shots.json):
  illus    DeepInfra FLUX illustration (prepaid credit), one consistent style per episode
  photo    licensed Wikimedia Commons image by key (assets/<id>/<key>-n.*), optional lower-third label
  words    big keyword lines that appear one by one
  compare  two-column comparison card
  title    illustration background with a big title
Motion: Ken Burns on every still, 0.5 s cross-dissolves, burned-in captions.

Usage:
  shots.py <id> sentences                 write out/<id>/sentences.txt for the shot director
  shots.py <id> frames  <shots.json>      stills + numbered review sheets in out/<id>/qa/ (no encoding)
  shots.py <id> render  <shots.json> [--out file.mp4] [--height 1080]
A shot starts on sentence index "s" (or the sentence starting with "at") and lasts until the next shot.
Photo shots name an exact asset "file" (or a "key", cycling its images).
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import subprocess
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from common import ASSETS, OUT, load_json, log, save_json, fail

W, H, FPS = 1920, 1080, 25
XF = 0.5
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
COST_PER_IMAGE = 0.009
# Audio standard (docs/audio.md). Every video uses these, nothing is set by hand:
VOICE_LUFS = -16          # narration normalised to -16 LUFS before mixing
MUSIC_UNDER_VOICE_DB = -10  # music bed sits 10 dB below the voice (same loudness scale)
DUCK_RATIO = 2.5          # gentle extra dip (about 3 to 4 dB) while the narrator speaks, back up in pauses
MASTER_LUFS = -14         # YouTube plays everything at about -14 LUFS, so we deliver there
MASTER_TP = -1.5          # true peak ceiling


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"{' '.join(cmd[:6])}...: {r.stderr[-1200:]}")


def illus_path(vid: str, prompt: str, seed: int) -> Path:
    import hashlib
    return ASSETS / vid / "illus" / f"{hashlib.sha1(f'{prompt}|{seed}'.encode()).hexdigest()[:12]}.jpg"


def illustration(prompt: str, style: str, path: Path, seed: int, costs: list) -> Image.Image:
    if path.exists():
        return Image.open(path).convert("RGB")
    key = os.environ.get("DEEPINFRA_API_KEY")
    if not key:
        fail("DEEPINFRA_API_KEY missing for illustration shots")
    r = requests.post("https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-1-dev",
                      headers={"Authorization": f"Bearer {key}"},
                      json={"prompt": f"{prompt}. {style}", "width": 1344, "height": 768,
                            "num_inference_steps": 28, "seed": seed}, timeout=180)
    if not r.ok:
        fail(f"deepinfra {r.status_code}: {r.text[:200]}")
    img = Image.open(io.BytesIO(base64.b64decode(r.json()["images"][0].split(",", 1)[-1]))).convert("RGB")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=93)
    costs.append({"what": f"illustration {path.name}", "service": "deepinfra", "usd_estimate": COST_PER_IMAGE})
    return img


def cover(img: Image.Image) -> Image.Image:
    return ImageOps.fit(img, (W, H), Image.LANCZOS)


def photo_frame(src: Path) -> Image.Image:
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(1.08)
    if abs(img.width / img.height - W / H) < 0.25:
        return cover(img)
    bg = cover(img).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H)), 0.5)
    fg = ImageOps.contain(img, (int(W * 0.96), int(H * 0.96)), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return bg


def vignette(img: Image.Image, strength: float = 0.55) -> Image.Image:
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([-W * 0.15, -H * 0.2, W * 1.15, H * 1.2], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(160))
    dark = Image.blend(img, Image.new("RGB", (W, H)), strength)
    return Image.composite(img, dark, mask)


def label(img: Image.Image, text: str) -> Image.Image:
    img = img.copy()
    d = ImageDraw.Draw(img, "RGBA")
    f = ImageFont.truetype(BOLD, 46)
    tw = d.textlength(text, font=f)
    d.rectangle([70, 90, 70 + tw + 60, 170], fill=(15, 12, 10, 200))
    d.rectangle([70, 90, 80, 170], fill=(255, 190, 40, 255))
    d.text((105, 104), text, font=f, fill=(255, 255, 255))
    return img


def card_bg() -> Image.Image:
    img = Image.new("RGB", (W, H), (20, 17, 15))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 3):
        d.line([(0, y), (W, y)], fill=(24 + (y % 9 == 0) * 4, 20, 17))
    return vignette(img, 0.6)


def centered(d: ImageDraw.ImageDraw, y: int, text: str, f, fill, x0: int = 0, x1: int = W) -> None:
    tw = d.textlength(text, font=f)
    d.text((x0 + (x1 - x0 - tw) / 2, y), text, font=f, fill=fill, stroke_width=4, stroke_fill=(0, 0, 0))


def words_frames(lines: list[str]) -> list[Image.Image]:
    f = ImageFont.truetype(BOLD, 120)
    out = []
    for k in range(1, len(lines) + 1):
        img = card_bg()
        d = ImageDraw.Draw(img)
        y = (H - len(lines) * 160) // 2
        for i, ln in enumerate(lines[:k]):
            centered(d, y, ln, f, (255, 200, 40) if i == k - 1 else (235, 230, 220))
            y += 160
        out.append(img)
    return out


def compare_frame(title: str, left: list[str], right: list[str]) -> Image.Image:
    img = card_bg()
    d = ImageDraw.Draw(img)
    centered(d, 150, title, ImageFont.truetype(BOLD, 84), (235, 230, 220))
    d.line([(W // 2, 330), (W // 2, 900)], fill=(90, 80, 70), width=4)
    fa = ImageFont.truetype(BOLD, 64)
    size = 150
    while size > 60 and max(d.textlength(x, font=ImageFont.truetype(BOLD, size)) for x in (left[1], right[1])) > W // 2 - 120:
        size -= 6
    fb = ImageFont.truetype(BOLD, size)
    centered(d, 400, left[0], fa, (200, 200, 200), 0, W // 2)
    centered(d, 560, left[1], fb, (230, 80, 50), 0, W // 2)
    centered(d, 400, right[0], fa, (200, 200, 200), W // 2, W)
    centered(d, 560, right[1], fb, (255, 200, 40), W // 2, W)
    return img


def title_frame(bg: Image.Image, text: str) -> Image.Image:
    img = vignette(ImageEnhance.Brightness(cover(bg)).enhance(0.6), 0.5)
    d = ImageDraw.Draw(img)
    size = 110
    while size > 50 and d.textlength(text, font=ImageFont.truetype(SERIF_BOLD, size)) > W - 160:
        size -= 6
    centered(d, H // 2 - size // 2, text, ImageFont.truetype(SERIF_BOLD, size), (255, 255, 255))
    return img


MOVES = {
    "in": ("1+0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "out": ("1.12-0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "right": ("1.10", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
    "left": ("1.10", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),
    "still": ("1.0", "0", "0"),
}


def clip(frame: Path, seconds: float, move: str, dst: Path) -> None:
    n = max(2, int(round(seconds * FPS)))
    z, x, y = (m.format(n=n) for m in MOVES.get(move, MOVES["in"]))
    vf = (f"scale={W * 2}:{H * 2},zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},format=yuv420p")
    run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(frame), "-vf", vf,
         "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS), str(dst)])


MAX_SHOT_SECONDS = 9.5      # pace rule: no visual stays longer (cards may hold up to 12 s)
MAX_CARD_SECONDS = 12.0
MAX_FILE_REUSE = 2
SEGMENT = 15                # clips cross-dissolved per segment, segments are joined with a cut


def timing(spec: dict, sents: list[dict], duration: float) -> tuple[list[float], list[float]]:
    starts, si = [], 0
    for i, s in enumerate(spec["shots"]):
        if "s" in s:
            si = int(s["s"])
            if si >= len(sents):
                fail(f"shot {i + 1}: sentence {si} does not exist")
        else:
            while si < len(sents) and not sents[si]["text"].startswith(s["at"]):
                si += 1
            if si == len(sents):
                fail(f"shot {i + 1}: no sentence starts with '{s['at']}'")
        starts.append(0.0 if i == 0 else sents[si]["start"])
    for k in range(1, len(starts)):
        if starts[k] <= starts[k - 1]:
            fail(f"shot {k + 1} does not start after shot {k} (check sentence order)")
    return starts, starts[1:] + [duration]


def frames_for(vid: str, i: int, s: dict, spec: dict, used: dict, costs: list) -> list[Image.Image]:
    t = s["type"]
    seed = int(s.get("seed", 2000 + i))
    if t in ("illus", "title"):
        img = illustration(s["prompt"], spec["style"], illus_path(vid, s["prompt"], seed), seed, costs)
        frames = [cover(img)] if t == "illus" else [title_frame(img, s["text"])]
    elif t == "photo":
        if s.get("file"):
            f = ASSETS / vid / s["file"]
            if not f.exists():
                fail(f"shot {i + 1}: asset {s['file']} missing")
        else:
            files = sorted((ASSETS / vid).glob(f"{s['key']}-*"))
            if not files:
                fail(f"shot {i + 1}: no images for key {s['key']}")
            f = files[used.get(s["key"], 0) % len(files)]
            used[s["key"]] = used.get(s["key"], 0) + 1
        frames = [photo_frame(f)]
        s["_file"] = f.name
    elif t == "words":
        frames = words_frames(s["lines"])
    elif t == "compare":
        frames = [compare_frame(s["title"], s["left"], s["right"])]
    else:
        fail(f"shot {i + 1}: unknown shot type {t}")
    if s.get("label"):
        frames = [label(f, s["label"]) for f in frames]
    return frames


def review_sheets(vid: str, items: list[tuple[int, Path, str, str]]) -> None:
    """Numbered tiles (shot number, type, narration) for the visual QA pass."""
    qa = OUT / vid / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    for old in qa.glob("sheet-*.jpg"):
        old.unlink()
    tw, th, cols, per = 480, 270, 3, 12
    f1, f2 = ImageFont.truetype(BOLD, 26), ImageFont.truetype(BOLD, 15)
    for n in range(0, len(items), per):
        chunk = items[n:n + per]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * (th + 70)), (12, 12, 12))
        d = ImageDraw.Draw(sheet)
        for k, (idx, path, typ, text) in enumerate(chunk):
            x, y = (k % cols) * tw, (k // cols) * (th + 70)
            sheet.paste(Image.open(path).resize((tw - 6, th - 6)), (x + 3, y + 3))
            d.rectangle([x + 3, y + 3, x + 110, y + 40], fill=(0, 0, 0))
            d.text((x + 10, y + 8), f"#{idx} {typ[:5]}", font=f1, fill=(255, 210, 60))
            words = text if len(text) < 120 else text[:117] + "..."
            d.text((x + 6, y + th + 2), "\n".join([words[j:j + 58] for j in range(0, len(words), 58)][:3]),
                   font=f2, fill=(220, 220, 220))
        sheet.save(qa / f"sheet-{n // per + 1:02d}.jpg", quality=80)


def report(vid: str, spec: dict, starts: list[float], ends: list[float]) -> dict:
    long_shots = [i + 1 for i, (s, a, b) in enumerate(zip(spec["shots"], starts, ends))
                  if b - a > (MAX_CARD_SECONDS if s["type"] in ("words", "compare", "title") else MAX_SHOT_SECONDS)]
    files: dict[str, int] = {}
    for s in spec["shots"]:
        if s.get("_file"):
            files[s["_file"]] = files.get(s["_file"], 0) + 1
    reused = {f: c for f, c in files.items() if c > MAX_FILE_REUSE}
    types: dict[str, int] = {}
    for s in spec["shots"]:
        types[s["type"]] = types.get(s["type"], 0) + 1
    rep = {"shots": len(starts), "average_seconds": round((ends[-1] - starts[0]) / len(starts), 2),
           "longest_seconds": round(max(b - a for a, b in zip(starts, ends)), 2),
           "too_long": long_shots, "reused_too_often": reused, "types": types}
    save_json(OUT / vid / "shots-report.json", rep)
    log(f"shots: {rep['shots']}, average {rep['average_seconds']}s, longest {rep['longest_seconds']}s, "
        f"too long {long_shots or 'none'}, overused {reused or 'none'}, types {types}")
    return rep


def write_sentences(vid: str) -> None:
    tl = load_json(OUT / vid / "timeline.json")
    lines = [f"{i}\t{s['start']:.1f}s\t{s['end'] - s['start']:.1f}s\tsection {s['section']}\t{s['text']}"
             for i, s in enumerate(tl["sentences"])]
    (OUT / vid / "sentences.txt").write_text("index\tstart\tlength\tsection\ttext\n" + "\n".join(lines) + "\n")
    log(f"{len(lines)} sentences, {tl['duration'] / 60:.1f} min -> out/{vid}/sentences.txt")


def build(vid: str, spec_path: Path, encode: bool, out: Path | None, height: int) -> None:
    spec = load_json(spec_path)
    tl = load_json(OUT / vid / "timeline.json")
    sents = tl.get("sentences") or fail("timeline has no sentence timings (rerun tts.py)")
    duration = tl["duration"]
    starts, ends = timing(spec, sents, duration)
    work = OUT / vid / "shots"
    work.mkdir(parents=True, exist_ok=True)
    costs_file = OUT / vid / "costs.json"
    costs = load_json(costs_file, {"items": []})
    used: dict[str, int] = {}
    review: list[tuple[int, Path, str, str]] = []
    sent_at = {round(x["start"], 3): x["text"] for x in sents}
    plan = []
    for i, (s, a, b) in enumerate(zip(spec["shots"], starts, ends)):
        frames = frames_for(vid, i, s, spec, used, costs["items"])
        paths = []
        for j, fr in enumerate(frames):
            p = work / f"f{i + 1:03d}-{j}.jpg"
            fr.save(p, quality=92)
            paths.append(p)
        review.append((i + 1, paths[-1], s["type"], sent_at.get(round(a, 3), sents[0]["text"] if i == 0 else "")))
        plan.append((s, a, b, paths))
    costs["total_usd_estimate"] = round(sum(c["usd_estimate"] for c in costs["items"]), 3)
    save_json(costs_file, costs)
    review_sheets(vid, review)
    report(vid, spec, starts, ends)
    tw, th, cols = 320, 180, 8
    rows = (len(review) + cols - 1) // cols
    cs = Image.new("RGB", (cols * tw, rows * th))
    for k, (_, p, _, _) in enumerate(review):
        cs.paste(Image.open(p).resize((tw, th)), ((k % cols) * tw, (k // cols) * th))
    cs.save(OUT / vid / "shots-preview.jpg", quality=80)
    if not encode:
        log(f"frames ready: {len(plan)} shots, review sheets in out/{vid}/qa/, illustrations ${costs['total_usd_estimate']}")
        return

    # clips: inside a segment each clip carries a 0.5 s tail for the cross-dissolve, the last one does not
    segs: list[Path] = []
    for g in range(0, len(plan), SEGMENT):
        group = plan[g:g + SEGMENT]
        clips, offs = [], []
        g0 = group[0][1]
        for k, (s, a, b, paths) in enumerate(group):
            tail = XF if k < len(group) - 1 else 0
            length = b - a + tail
            parts = []
            for j, p in enumerate(paths):
                c = work / f"c{g + k + 1:03d}-{j}.mp4"
                move = "still" if s["type"] in ("words", "compare") else s.get("move", ["in", "right", "out", "left"][(g + k) % 4])
                clip(p, length / len(paths), move, c)
                parts.append(c)
            if len(parts) > 1:
                lst = work / f"c{g + k + 1:03d}.txt"
                lst.write_text("".join(f"file '{x.name}'\n" for x in parts))
                c = work / f"c{g + k + 1:03d}.mp4"
                run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(c)])
                parts = [c]
            clips.append(parts[0])
            offs.append(a - g0)
        seg = work / f"seg{g // SEGMENT + 1:03d}.mp4"
        if len(clips) == 1:
            run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(clips[0]), "-c", "copy", str(seg)])
        else:
            inputs, filt, last = [], [], "0:v"
            for c in clips:
                inputs += ["-i", str(c)]
            for k in range(1, len(clips)):
                filt.append(f"[{last}][{k}:v]xfade=transition=fade:duration={XF}:offset={offs[k]:.3f}[x{k}]")
                last = f"x{k}"
            run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt),
                 "-map", f"[{last}]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(FPS), str(seg)])
        segs.append(seg)
        log(f"segment {g // SEGMENT + 1}: shots {g + 1}-{g + len(group)}")
    lst = work / "segments.txt"
    lst.write_text("".join(f"file '{x.name}'\n" for x in segs))
    joined = work / "joined.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])

    srt = OUT / vid / f"{vid}.srt"
    style = ("FontName=DejaVu Sans,Bold=1,FontSize=17,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             "BackColour=&H80000000,BorderStyle=4,Outline=1,Shadow=0,MarginV=38")
    filt = [f"[0:v]subtitles={srt}:force_style='{style}'" + (f",scale=-2:{height}" if height != H else "") + "[vout]"]
    audio_in = ["-i", str(OUT / vid / "narration.wav")]
    amap = "1:a"
    music = load_json(OUT / vid / "music.json", {})
    if music and Path(music["file"]).exists():
        audio_in += ["-stream_loop", "-1", "-i", music["file"]]
        filt.append(f"[2:a]atrim=0:{duration:.2f},afade=t=in:d=4,afade=t=out:st={max(0, duration - 6):.2f}:d=6,"
                    f"aresample=48000,aformat=channel_layouts=mono,loudnorm=I={VOICE_LUFS}:TP=-2:LRA=11,"
                    f"volume={MUSIC_UNDER_VOICE_DB}dB[m]")
        filt.append(f"[1:a]aresample=48000,aformat=channel_layouts=mono,loudnorm=I={VOICE_LUFS}:TP=-2:LRA=11,asplit[n1][n2]")
        filt.append(f"[m][n2]sidechaincompress=threshold=0.05:ratio={DUCK_RATIO}:attack=60:release=900[md]")
        filt.append(f"[n1][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I={MASTER_LUFS}:TP={MASTER_TP}:LRA=11,"
                    f"aresample=48000[aout]")
        amap = "[aout]"
        log(f"music bed: {music['title']}")
    else:
        filt.append(f"[1:a]loudnorm=I={MASTER_LUFS}:TP={MASTER_TP}:LRA=11,aresample=48000[aout]")
        amap = "[aout]"
    out = out or OUT / f"{vid}-v2.mp4"
    extra, smap = [], []
    if height == H and srt.exists():          # also keep soft subtitles (YouTube gets the .srt separately too)
        extra = ["-i", str(srt)]
        smap = ["-map", f"{1 + len(audio_in) // 2}:s", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(joined), *audio_in, *extra,
           "-filter_complex", ";".join(filt), "-map", "[vout]", "-map", amap, *smap,
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-c:a", "aac", "-b:a", "192k",
           "-t", f"{duration:.3f}", "-movflags", "+faststart", str(out)]
    run(cmd)
    log(f"v2 render {out.name}: {len(plan)} shots, illustrations ${costs['total_usd_estimate']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    ap.add_argument("mode", choices=["sentences", "frames", "render"])
    ap.add_argument("shots", nargs="?")
    ap.add_argument("--out", default="")
    ap.add_argument("--height", type=int, default=1080)
    a = ap.parse_args()
    if a.mode == "sentences":
        write_sentences(a.vid)
    else:
        if not a.shots:
            fail("shots file required")
        build(a.vid, Path(a.shots), a.mode == "render", Path(a.out) if a.out else None, a.height)


if __name__ == "__main__":
    main()
