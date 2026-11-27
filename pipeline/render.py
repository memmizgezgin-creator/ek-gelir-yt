"""Render: archive slideshow, 1920x1080, slow zoom/pan, blurred fill, captions.

Inputs: out/<id>/timeline.json, narration.wav, <id>.srt, credits.json, assets/<id>/
Output: out/<id>-<slug>.mp4 (soft subtitles embedded) and out/<id>/<id>.srt
"""
from __future__ import annotations

import argparse
import itertools
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from common import ASSETS, OUT, find_script, load_json, log, parse_script, fail

W, H, FPS = 1920, 1080, 25
SLIDE_SECONDS = 22.0
END_CARD_SECONDS = 20.0
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
PAPER = (28, 24, 20)
INK = (226, 214, 190)


def font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def compose_frame(src: Path, dst: Path) -> None:
    """Fit the image inside the frame over a blurred, darkened copy of itself."""
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    bg = ImageOps.fit(img, (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(38))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.45)
    fg = ImageOps.contain(img, (int(W * 0.94), int(H * 0.94)), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    bg.save(dst, quality=92)


def text_card(title: str, subtitle: str, dst: Path) -> None:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    for i in range(0, H, 4):
        shade = 6 if (i // 4) % 2 else 0
        d.line([(0, i), (W, i)], fill=(PAPER[0] + shade, PAPER[1] + shade, PAPER[2] + shade))
    d.rectangle([80, 80, W - 80, H - 80], outline=(120, 104, 80), width=3)
    f1, f2 = font(SERIF_BOLD, 76), font(SERIF, 40)
    lines = textwrap.wrap(title, 32)
    y = H // 2 - 60 * len(lines)
    for ln in lines:
        tw = d.textlength(ln, font=f1)
        d.text(((W - tw) / 2, y), ln, font=f1, fill=INK)
        y += 100
    if subtitle:
        tw = d.textlength(subtitle, font=f2)
        d.text(((W - tw) / 2, y + 30), subtitle, font=f2, fill=(170, 150, 120))
    img.save(dst, quality=92)


def end_card(credits: list[dict], sources: list[str], dst: Path) -> None:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    f1, f2 = font(SERIF_BOLD, 44), font(SERIF, 22)
    d.text((100, 70), "Sources and image credits", font=f1, fill=INK)
    y = 150
    rows = [f"Source: {s}" for s in sources] + [
        f"{c['title'].removeprefix('File:')} | {c['artist']} | {c['license']}" for c in credits
    ]
    if not credits:
        rows.append("Illustrations: title cards made for this video.")
    col_x = [100, W // 2 + 20]
    col = 0
    for r in rows:
        for ln in textwrap.wrap(r, 78)[:2]:
            d.text((col_x[col], y), ln, font=f2, fill=(200, 188, 164))
            y += 30
        y += 6
        if y > H - 120:
            if col == 1:
                d.text((100, H - 90), "Full list in the video description.", font=f2, fill=INK)
                break
            col, y = 1, 150
    img.save(dst, quality=92)


def ken_burns_clip(frame: Path, seconds: float, variant: int, dst: Path) -> None:
    n = max(1, int(round(seconds * FPS)))
    moves = [
        ("1+0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),            # slow zoom in
        ("1.10-0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),         # slow zoom out
        ("1.08", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),                  # pan right
        ("1.08", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),              # pan left
    ]
    z, x, y = (m.format(n=n) for m in moves[variant % len(moves)])
    vf = (f"scale={W * 2}:{H * 2},zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},"
          f"fade=t=in:st=0:d=0.6,fade=t=out:st={max(0.0, n / FPS - 0.6):.2f}:d=0.6,format=yuv420p")
    run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(frame), "-vf", vf,
         "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-r", str(FPS), str(dst)])


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"{' '.join(cmd[:6])}...: {r.stderr[-800:]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    args = ap.parse_args()
    script_path = find_script(args.vid)
    script = parse_script(script_path)
    work = OUT / args.vid
    tl = load_json(work / "timeline.json")
    if not tl:
        fail("timeline.json missing, run tts first")
    credits = load_json(work / "credits.json", [])
    by_key: dict[str, list[Path]] = {}
    for c in credits:
        p = ASSETS / args.vid / c["file"]
        if p.exists():
            by_key.setdefault(c["key"], []).append(p)

    frames = work / "frames"
    clips = work / "clips"
    frames.mkdir(exist_ok=True)
    clips.mkdir(exist_ok=True)
    clip_list: list[Path] = []
    variant = 0
    used_once: set[Path] = set()
    frame_cursor = 0  # absolute frame position, avoids rounding drift

    for si, sec in enumerate(tl["sections"]):
        start = 0.0 if si == 0 else sec["start"]
        dur = sec["end"] - start
        pool = [p for k in sec["images"] for p in by_key.get(k, [])]
        # prefer images not shown yet, keep order
        pool = [p for p in pool if p not in used_once] + [p for p in pool if p in used_once]
        n_slides = max(1, round(dur / SLIDE_SECONDS))
        slide_frames: list[Path] = []
        if pool:
            for i, src in zip(range(n_slides), itertools.cycle(pool)):
                f = frames / f"s{sec['index']:02d}-{i:02d}.jpg"
                compose_frame(src, f)
                slide_frames.append(f)
                used_once.add(src)
        else:
            f = frames / f"s{sec['index']:02d}-card.jpg"
            text_card(sec["title"], script.meta.get("title", "").split("?")[0] + "?", f)
            slide_frames = [f]
        each = dur / len(slide_frames)
        for i, f in enumerate(slide_frames):
            c = clips / f"c{sec['index']:02d}-{i:02d}.mp4"
            end_frame = round((start + each * (i + 1)) * FPS)
            ken_burns_clip(f, (end_frame - frame_cursor) / FPS, variant, c)
            frame_cursor = end_frame
            variant += 1
            clip_list.append(c)
        log(f"render section {sec['index']}: {len(slide_frames)} slides, {dur:.1f}s")

    sources = [s.strip() for s in script.meta.get("sources", "").split("|") if s.strip()]
    ec = frames / "end-card.jpg"
    end_card(credits, sources, ec)
    ecc = clips / "zz-end.mp4"
    ken_burns_clip(ec, END_CARD_SECONDS, 0, ecc)
    clip_list.append(ecc)

    concat = work / "concat.txt"
    concat.write_text("".join(f"file '{c.resolve()}'\n" for c in clip_list))
    slug = script_path.stem
    final = OUT / f"{slug}.mp4"
    srt = work / f"{args.vid}.srt"
    total = sum(1 for _ in clip_list)
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-i", str(work / "narration.wav"), "-i", str(srt),
         "-map", "0:v", "-map", "1:a", "-map", "2:s",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-af", f"apad=pad_dur={END_CARD_SECONDS}",
         "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
         "-shortest", "-movflags", "+faststart", str(final)])
    log(f"wrote {final.relative_to(OUT.parent)} from {total} clips")


if __name__ == "__main__":
    main()
