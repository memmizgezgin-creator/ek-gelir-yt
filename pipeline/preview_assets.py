"""Labeled contact sheet of downloaded images (assets/<id>) for a quick human check."""
import argparse

from PIL import Image, ImageDraw, ImageFont, ImageOps

from common import ASSETS, OUT

TW, TH, COLS = 400, 260, 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    vid = ap.parse_args().vid
    files = sorted(p for p in (ASSETS / vid).glob("*") if p.is_file())
    rows = (len(files) + COLS - 1) // COLS or 1
    sheet = Image.new("RGB", (COLS * TW, rows * TH), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    for i, p in enumerate(files):
        im = ImageOps.contain(Image.open(p).convert("RGB"), (TW - 10, TH - 40))
        x, y = (i % COLS) * TW, (i // COLS) * TH
        sheet.paste(im, (x + (TW - im.width) // 2, y + 5))
        d.text((x + 8, y + TH - 30), p.stem, font=f, fill=(255, 210, 80))
    out = OUT / vid / "assets-preview.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=80)
    print(f"[ek-gelir-yt] {len(files)} images -> {out}")


if __name__ == "__main__":
    main()
