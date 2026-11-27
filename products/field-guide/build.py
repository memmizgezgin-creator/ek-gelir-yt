"""Build the field guide: full PDF (paid) and 2 page cheat sheet (free lead magnet).

python build.py  -> out/field-guide.pdf, out/cheat-sheet.pdf (needs node + playwright)
"""
import html
import subprocess
from pathlib import Path

import content as C

HERE = Path(__file__).parent
OUTDIR = HERE / "out"
e = html.escape


def head(title):
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{e(title)}</title><style>{(HERE / 'style.css').read_text()}</style></head><body>"


def compare_table():
    rows = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in C.COMPARE)
    return f"<table><tr>{''.join(f'<th>{e(h)}</th>' for h in C.COMPARE_HEAD)}</tr>{rows}</table>"


def timeline():
    return "<div class='timeline'>" + "".join(f"<b>{e(y)}</b><span>{e(t)}</span>" for y, t in C.TIMELINE) + "</div>"


def material(m):
    li = lambda xs: "<ul>" + "".join(f"<li>{e(x)}</li>" for x in xs) + "</ul>"
    return f"""<section style="page-break-inside: avoid; margin-bottom: 7mm">
<h2>{e(m['name'])}</h2>
<div class='facts'><div><span class='label'>Era</span><b>{e(m['era'])}</b></div>
<div><span class='label'>Made of</span><b>{e(m['comp'])}</b></div>
<div><span class='label'>Hot hardness</span><b>{e(m['hot'])}</b></div>
<div><span class='label'>Starting speed</span><b>{e(m['vc'])}</b></div></div>
<p>{e(m['story'])}</p>
<div class='two'><div><h3>Still the right choice for</h3>{li(m['today'])}</div><div><h3>Not for</h3>{li(m['not'])}</div></div>
</section>"""


def full():
    sel = "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in C.SELECTION)
    return head(C.TITLE) + f"""
<div class='page cover'><div><div class='kicker'>{e(C.BRAND)} field guide</div><h1 style='margin-top:10mm'>{e(C.TITLE)}</h1>
<div class='sub'>{e(C.SUBTITLE)}</div></div><div class='band'>{e(C.EDITION)} · Brand neutral · Metric units</div></div>
<div class='page'><h2>Why the history matters at the machine</h2>{''.join(f'<p>{e(p)}</p>' for p in C.INTRO)}
<h2 style='margin-top:8mm'>Timeline</h2>{timeline()}</div>
<div class='page'>{''.join(material(m) for m in C.MATERIALS)}</div>
<div><h2>Side by side</h2>{compare_table()}<p class='small'>{e(C.DISCLAIMER)}</p>
<h2 style='margin-top:8mm'>Choosing at the machine: five questions</h2>{sel}</div>
<div style='margin-top:8mm'><h2>About</h2><p>{e(C.ABOUT)}</p><p class='small'>© {e(C.BRAND)}. For personal use. Please do not redistribute.</p></div>
</body></html>"""


def cheat():
    return head(C.TITLE + " cheat sheet") + f"""
<div class='kicker' style='font-family:DejaVu Sans;letter-spacing:3px;color:#b8541c;font-size:9pt'>{e(C.BRAND)} · FREE CHEAT SHEET</div>
<h1 style='font-size:22pt;margin:3mm 0 4mm'>Cutting tool materials on one page</h1>
{compare_table()}<p class='small'>{e(C.DISCLAIMER)}</p>
<h2 style='margin-top:6mm'>Timeline</h2>{timeline()}
<div class='box'>The full guide, <b>{e(C.TITLE)}</b>, covers every material in depth: where it came from, what it is made of, where it still wins and where it fails, plus a five question selection routine.</div>
</body></html>"""


def pdf(html_text, name):
    OUTDIR.mkdir(exist_ok=True)
    src = OUTDIR / f"{name}.html"
    src.write_text(html_text)
    js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://{src.resolve()}');await p.pdf({{path:'{(OUTDIR / (name + '.pdf')).resolve()}',format:'A4',printBackground:true,
displayHeaderFooter:true,headerTemplate:'<span></span>',footerTemplate:'<div style="font-size:8px;width:100%;text-align:center;color:#888"><span class="pageNumber"></span></div>',
margin:{{top:'18mm',bottom:'18mm',left:'17mm',right:'17mm'}}}});await b.close();}})();"""
    subprocess.run(["node", "-e", js], check=True)
    print("wrote", OUTDIR / f"{name}.pdf")


if __name__ == "__main__":
    pdf(full(), "field-guide")
    pdf(cheat(), "cheat-sheet")
