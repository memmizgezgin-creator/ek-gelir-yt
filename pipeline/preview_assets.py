"""Labeled contact sheet of downloaded images (assets/<id>) for a quick human check."""
import argparse

from PIL import Image, ImageDraw, ImageFont, ImageOps

from common import ASSETS, OUT, load_json

TW, TH, COLS = 400, 260, 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    vid = ap.parse_args().vid
    files = sorted(p for p in (ASSETS / vid).glob("*") if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png"))
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
    # pages of 20 for the shot director (readable tiles) and a text list with Commons titles
    pages = OUT / vid / "assets"
    pages.mkdir(parents=True, exist_ok=True)
    for old in pages.glob("page-*.jpg"):
        old.unlink()
    per = 20
    for n in range(0, len(files), per):
        chunk = files[n:n + per]
        rows = (len(chunk) + COLS - 1) // COLS
        pg = Image.new("RGB", (COLS * TW, rows * TH), (20, 20, 20))
        dp = ImageDraw.Draw(pg)
        for i, p in enumerate(chunk):
            im = ImageOps.contain(Image.open(p).convert("RGB"), (TW - 10, TH - 40))
            x, y = (i % COLS) * TW, (i // COLS) * TH
            pg.paste(im, (x + (TW - im.width) // 2, y + 5))
            dp.text((x + 8, y + TH - 30), p.name, font=f, fill=(255, 210, 80))
        pg.save(pages / f"page-{n // per + 1:02d}.jpg", quality=82)
    credits = {c["file"]: c["title"] for c in load_json(OUT / vid / "credits.json", [])}
    (OUT / vid / "assets.txt").write_text("".join(f"{p.name}\t{credits.get(p.name, '')}\n" for p in files))
    print(f"[ek-gelir-yt] {len(files)} images -> {out}, {pages}/page-*.jpg, assets.txt")


if __name__ == "__main__":
    main()
