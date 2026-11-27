"""Thumbnail 1280x720: one old object on a dark plain background + short text.

Free path only: Pillow over a licensed Commons image already downloaded for
the video. (fal.ai credit is optional and not required; see docs/abonelikler.md.)
"""
from __future__ import annotations

import argparse

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from common import ASSETS, OUT, find_script, load_json, log, parse_script

TW, TH = 1280, 720
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    args = ap.parse_args()
    script = parse_script(find_script(args.vid))
    credits = load_json(OUT / args.vid / "credits.json", [])
    key = script.meta.get("thumb_key", script.meta.get("slug", ""))
    pick = next((c for c in credits if c["key"] == key), credits[0] if credits else None)

    canvas = Image.new("RGB", (TW, TH), (24, 21, 18))
    if pick:
        img = ImageOps.exif_transpose(Image.open(ASSETS / args.vid / pick["file"])).convert("RGB")
        img = ImageEnhance.Contrast(img).enhance(1.15)
        obj = ImageOps.contain(img, (int(TW * 0.55), int(TH * 0.92)), Image.LANCZOS)
        glow = Image.new("RGB", (TW, TH), (24, 21, 18))
        glow.paste(obj, (TW - obj.width - 30, (TH - obj.height) // 2))
        canvas = Image.blend(canvas, glow.filter(ImageFilter.GaussianBlur(30)), 0.5)
        canvas.paste(obj, (TW - obj.width - 30, (TH - obj.height) // 2))

    d = ImageDraw.Draw(canvas)
    name = script.meta.get("thumb_text") or script.meta.get("slug", "").replace("-", " ").upper()
    f_small = ImageFont.truetype(BOLD, 54)
    size = 130
    while size > 60 and d.textlength(name, font=ImageFont.truetype(BOLD, size)) > TW * 0.5:
        size -= 6
    f_big = ImageFont.truetype(BOLD, size)
    d.text((48, 210), "WHAT HAPPENED TO", font=f_small, fill=(235, 222, 196), stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((44, 280), name + "?", font=f_big, fill=(255, 196, 64), stroke_width=5, stroke_fill=(0, 0, 0))
    out = OUT / args.vid / "thumbnail.jpg"
    canvas.save(out, quality=90)
    log(f"thumbnail {out.name} ({'image ' + pick['file'] if pick else 'text only'})")


if __name__ == "__main__":
    main()
