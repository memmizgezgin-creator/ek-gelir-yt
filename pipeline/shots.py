"""Render v2: shot-based video. A new visual every 5 to 8 seconds, timed to the narration.

Shot types (from <script>.shots.json):
  illus    DeepInfra FLUX illustration (prepaid credit), one consistent style per episode
  photo    licensed Wikimedia Commons image by key (assets/<id>/<key>-n.*), optional lower-third label
  words    big keyword lines that appear one by one
  compare  two-column comparison card
  title    illustration background with a big title
Motion: Ken Burns on every still, 0.5 s cross-dissolves, burned-in captions.

Usage: shots.py <id> <shots.json> [--out file.mp4] [--height 1080]
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


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"{' '.join(cmd[:6])}...: {r.stderr[-1200:]}")


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
    centered(d, H // 2 - 80, text, ImageFont.truetype(SERIF_BOLD, 110), (255, 255, 255))
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    ap.add_argument("shots")
    ap.add_argument("--out", default="")
    ap.add_argument("--height", type=int, default=1080)
    args = ap.parse_args()
    vid = args.vid
    spec = load_json(Path(args.shots))
    tl = load_json(OUT / vid / "timeline.json")
    sents = tl.get("sentences") or fail("timeline has no sentence timings (rerun tts.py)")
    duration = tl["duration"]
    work = OUT / vid / "shots"
    work.mkdir(parents=True, exist_ok=True)
    costs_file = OUT / vid / "costs.json"
    costs = load_json(costs_file, {"items": []})

    # 1. time every shot from the sentence it starts on
    starts, si = [], 0
    for i, s in enumerate(spec["shots"]):
        while si < len(sents) and not sents[si]["text"].startswith(s["at"]):
            si += 1
        if si == len(sents):
            fail(f"shot {i + 1}: no sentence starts with '{s['at']}'")
        starts.append(0.0 if i == 0 else sents[si]["start"])
    ends = starts[1:] + [duration]

    # 2. one still per shot (or several for 'words'), then a moving clip
    used: dict[str, int] = {}
    clips: list[Path] = []
    sheet: list[Path] = []
    for i, (s, a, b) in enumerate(zip(spec["shots"], starts, ends)):
        length = b - a + (XF if i < len(starts) - 1 else 0)
        t = s["type"]
        frames: list[Image.Image]
        if t == "illus":
            frames = [cover(illustration(s["prompt"], spec["style"], ASSETS / vid / f"illus-{i + 1:02d}.jpg", 2000 + i, costs["items"]))]
        elif t == "title":
            frames = [title_frame(illustration(s["prompt"], spec["style"], ASSETS / vid / f"illus-{i + 1:02d}.jpg", 2000 + i, costs["items"]), s["text"])]
        elif t == "photo":
            files = sorted((ASSETS / vid).glob(f"{s['key']}-*"))
            if not files:
                fail(f"shot {i + 1}: no images for key {s['key']}")
            k = used.get(s["key"], 0)
            used[s["key"]] = k + 1
            frames = [photo_frame(files[k % len(files)])]
        elif t == "words":
            frames = words_frames(s["lines"])
        elif t == "compare":
            frames = [compare_frame(s["title"], s["left"], s["right"])]
        else:
            fail(f"unknown shot type {t}")
        if s.get("label"):
            frames = [label(f, s["label"]) for f in frames]
        parts = []
        for j, fr in enumerate(frames):
            p = work / f"f{i + 1:02d}-{j}.jpg"
            fr.save(p, quality=92)
            sheet.append(p)
            seg = length / len(frames)
            c = work / f"c{i + 1:02d}-{j}.mp4"
            clip(p, seg, "still" if t in ("words", "compare") else s.get("move", "in"), c)
            parts.append(c)
        if len(parts) > 1:
            lst = work / f"c{i + 1:02d}.txt"
            lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
            c = work / f"c{i + 1:02d}.mp4"
            run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(c)])
            parts = [c]
        clips.append(parts[0])
        log(f"shot {i + 1:02d} {t:8s} {a:6.1f}s-{b:6.1f}s ({b - a:.1f}s)")

    # 3. cross-dissolve chain, narration, burned captions
    inputs, filt, last = [], [], "0:v"
    for c in clips:
        inputs += ["-i", str(c)]
    for k in range(1, len(clips)):
        out = f"v{k}"
        filt.append(f"[{last}][{k}:v]xfade=transition=fade:duration={XF}:offset={starts[k]:.3f}[{out}]")
        last = out
    srt = OUT / vid / f"{vid}.srt"
    style = ("FontName=DejaVu Sans,Bold=1,FontSize=17,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             "BackColour=&H80000000,BorderStyle=4,Outline=1,Shadow=0,MarginV=38")
    filt.append(f"[{last}]subtitles={srt}:force_style='{style}',scale=-2:{args.height}[vout]")
    out = Path(args.out) if args.out else OUT / f"{vid}-v2.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-i", str(OUT / vid / "narration.wav"),
         "-filter_complex", ";".join(filt), "-map", "[vout]", "-map", f"{len(clips)}:a",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "160k",
         "-shortest", "-movflags", "+faststart", str(out)])
    costs["total_usd_estimate"] = round(sum(c["usd_estimate"] for c in costs["items"]), 3)
    save_json(costs_file, costs)
    # contact sheet of the shots for review
    tw, th, cols = 320, 180, 6
    rows = (len(sheet) + cols - 1) // cols
    cs = Image.new("RGB", (cols * tw, rows * th))
    for i, p in enumerate(sheet):
        cs.paste(Image.open(p).resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    cs.save(OUT / vid / "shots-preview.jpg", quality=82)
    avg = duration / len(clips)
    log(f"v2 render {out.name}: {len(clips)} shots, average {avg:.1f}s per visual, "
        f"illustrations cost ${costs['total_usd_estimate']}")


if __name__ == "__main__":
    main()
