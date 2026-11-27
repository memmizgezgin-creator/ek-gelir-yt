"""Thumbnail 1280x720: bold illustrated scene + 2 to 4 huge words.

The click decides everything, so the thumbnail is the one place we spend credit:
1. DeepInfra FLUX-1-dev (prepaid credit, DEEPINFRA_API_KEY), about 1 cent an image
2. fal.ai FLUX dev (remaining prepaid credit, FAL_KEY) if DeepInfra fails
3. Free fallback: Pillow over a licensed Commons image
The model draws the picture only. Text is set by Pillow so it is always sharp
and spelled right. Front matter: thumb_prompt (scene), thumb_text (2-4 words).
Writes out/<id>/thumbnail.jpg and out/<id>/thumb-variants/*.jpg, logs cost to
out/<id>/costs.json.
"""
from __future__ import annotations

import argparse
import base64
import io
import os
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from common import ASSETS, OUT, find_script, load_json, log, parse_script, save_json

TW, TH = 1280, 720
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
STYLE = ("Bold clean cartoon illustration, thick black outlines, flat warm saturated colors, "
         "exaggerated facial expression with huge eyes and open mouth, storybook editorial style, "
         "strong contrast, dramatic warm lighting, simple dark uncluttered background, square "
         "composition with the character and the object both large and centered. "
         "Absolutely no text, letters, numbers or logos.")
VARIANTS = 3
COST_PER_IMAGE = {"deepinfra": 0.009, "fal": 0.025}   # USD, approximate list prices


def gen_deepinfra(prompt: str, seed: int) -> Image.Image | None:
    key = os.environ.get("DEEPINFRA_API_KEY")
    if not key:
        return None
    r = requests.post("https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-1-dev",
                      headers={"Authorization": f"Bearer {key}"},
                      json={"prompt": prompt, "width": 1024, "height": 1024, "num_inference_steps": 28,
                            "seed": seed}, timeout=180)
    if not r.ok:
        log(f"deepinfra {r.status_code}: {r.text[:200]}")
        return None
    img = (r.json().get("images") or [None])[0]
    if not img:
        return None
    return Image.open(io.BytesIO(base64.b64decode(img.split(",", 1)[-1]))).convert("RGB")


def gen_fal(prompt: str, seed: int) -> Image.Image | None:
    key = os.environ.get("FAL_KEY")
    if not key:
        return None
    r = requests.post("https://fal.run/fal-ai/flux/dev", headers={"Authorization": f"Key {key}"},
                      json={"prompt": prompt, "image_size": "square_hd", "seed": seed,
                            "num_images": 1}, timeout=180)
    if not r.ok:
        log(f"fal {r.status_code}: {r.text[:200]}")
        return None
    url = r.json()["images"][0]["url"]
    return Image.open(io.BytesIO(requests.get(url, timeout=60).content)).convert("RGB")


def archive_base(vid: str, script) -> Image.Image:
    credits = load_json(OUT / vid / "credits.json", [])
    key = script.meta.get("thumb_key", "")
    pick = next((c for c in credits if c["key"] == key), credits[0] if credits else None)
    canvas = Image.new("RGB", (TW, TH), (24, 21, 18))
    if pick:
        img = ImageOps.exif_transpose(Image.open(ASSETS / vid / pick["file"])).convert("RGB")
        img = ImageEnhance.Contrast(img).enhance(1.15)
        obj = ImageOps.contain(img, (int(TW * 0.55), int(TH * 0.92)), Image.LANCZOS)
        glow = Image.new("RGB", (TW, TH), (24, 21, 18))
        glow.paste(obj, (TW - obj.width - 30, (TH - obj.height) // 2))
        canvas = Image.blend(canvas, glow.filter(ImageFilter.GaussianBlur(30)), 0.5)
        canvas.paste(obj, (TW - obj.width - 30, (TH - obj.height) // 2))
    return canvas


def overlay_text(base: Image.Image, words: str) -> Image.Image:
    """Scene on the right, solid title panel on the left: text never covers the picture."""
    img = Image.new("RGB", (TW, TH), (16, 12, 10))
    if base.width / base.height > 1.4:      # archive fallback is already a 16:9 layout
        img = ImageOps.fit(base, (TW, TH), Image.LANCZOS)
        scene_x = int(TW * 0.4)
    else:
        scene = ImageOps.fit(base, (TH, TH), Image.LANCZOS)
        scene_x = TW - TH
        img.paste(scene, (scene_x, 0))
        # soft blend of the scene's left edge into the panel
        fade = Image.new("L", (TW, TH), 0)
        df = ImageDraw.Draw(fade)
        for x in range(160):
            df.line([(scene_x + x, 0), (scene_x + x, TH)], fill=int(255 * (1 - x / 160)))
        img = Image.composite(Image.new("RGB", (TW, TH), (16, 12, 10)), img, fade)
    d = ImageDraw.Draw(img)
    lines = words.upper().split("|") if "|" in words else _split(words.upper())
    colors = [(255, 255, 255), (255, 200, 40), (255, 255, 255), (255, 200, 40)]
    max_w = scene_x + 60 - 70
    size = 170
    while size > 50 and (max(d.textlength(l, font=ImageFont.truetype(BOLD, size)) for l in lines) > max_w
                         or len(lines) * size * 1.08 > TH * 0.86):
        size -= 6
    f = ImageFont.truetype(BOLD, size)
    total = len(lines) * int(size * 1.08)
    y = (TH - total) // 2
    for i, ln in enumerate(lines):
        d.text((44, y), ln, font=f, fill=colors[i % 4], stroke_width=max(6, size // 14), stroke_fill=(0, 0, 0))
        y += int(size * 1.08)
    return img


def _split(text: str) -> list[str]:
    w = text.split()
    if len(w) <= 2:
        return w
    half = (len(w) + 1) // 2
    return [" ".join(w[:half]), " ".join(w[half:])]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    args = ap.parse_args()
    script = parse_script(find_script(args.vid))
    out = OUT / args.vid
    var_dir = out / "thumb-variants"
    var_dir.mkdir(parents=True, exist_ok=True)
    words = script.meta.get("thumb_text") or script.meta.get("slug", "").replace("-", " ")
    scene = script.meta.get("thumb_prompt", "")
    costs = load_json(out / "costs.json", {"items": []})
    made: list[Path] = []
    if scene:
        for i in range(VARIANTS):
            prompt = f"{scene} {STYLE}"
            img, src = gen_deepinfra(prompt, 1000 + i), "deepinfra"
            if img is None:
                img, src = gen_fal(prompt, 1000 + i), "fal"
            if img is None:
                break
            costs["items"].append({"what": f"thumbnail variant {i + 1}", "service": src,
                                   "usd_estimate": COST_PER_IMAGE[src]})
            p = var_dir / f"v{i + 1}.jpg"
            overlay_text(img, words).save(p, quality=90)
            made.append(p)
            log(f"thumbnail variant {i + 1} from {src}")
    if not made:
        p = var_dir / "archive.jpg"
        overlay_text(archive_base(args.vid, script), words).save(p, quality=90)
        made.append(p)
        log("thumbnail: free archive fallback (no image credit key or generation failed)")
    choice = int(script.meta.get("thumb_pick", "1")) - 1
    Image.open(made[min(choice, len(made) - 1)]).save(out / "thumbnail.jpg", quality=90)
    costs["total_usd_estimate"] = round(sum(c["usd_estimate"] for c in costs["items"]), 3)
    save_json(out / "costs.json", costs)


if __name__ == "__main__":
    main()
