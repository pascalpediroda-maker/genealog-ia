# -*- coding: utf-8 -*-
"""Planches de mentions de marge, packees sans blanc.

Les planches de bandes de symb.py gardent toute la hauteur de la page, donc
surtout du papier vide, et il faut les reduire a 62 % pour en tenir douze.
Ici on ne decoupe que le rectangle de la mention, repere par index.json, et on
les empile a leur taille native : meme cout d'image, ecriture deux fois plus
grande. Indispensable sur le registre de 1773, dont le cure abrege tout.

  python grille.py <reg> <vue_a> <vue_b> <dest.png>
"""
import sys, os, json
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import actes

IXF = os.environ.get("IX", "index.json")
IX = json.load(open(IXF)) if os.path.exists(IXF) else {}
FONT = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 22)
CELLW = 330
HCOL = 1840
NCOL = 7
PAD = 6


def cellules(reg, a, b):
    out = []
    for p in actes.vues(reg)[a - 1:b]:
        n = os.path.basename(p)[1:4]
        rec = IX[f"{reg}{n}"]
        im = Image.open(p).convert("L")
        for side, pg in rec["pages"].items():
            if side == "G":
                sub = im.crop((0, 0, rec["gutter"], rec["h"]))
            elif side == "D":
                sub = im.crop((rec["gutter"], 0, rec["w"], rec["h"]))
            else:
                sub = im
            for k, (y0, y1) in enumerate(pg["m"]):
                x1 = min(pg["xt"] + 24, pg["x0"] + CELLW)
                c = sub.crop((pg["x0"], max(0, y0 - 10), x1, min(rec["h"], y1 + 10)))
                c = ImageOps.autocontrast(c, cutoff=1)
                out.append((f"{reg}{n}{side}.{k+1}", c))
    return out


def planche(cells, dest):
    cols, cur, hcur = [], [], 0
    for lab, c in cells:
        h = c.height + 26 + PAD
        if hcur + h > HCOL and cur:
            cols.append(cur)
            cur, hcur = [], 0
        cur.append((lab, c))
        hcur += h
    if cur:
        cols.append(cur)
    W = NCOL * (CELLW + 10)
    H = max(sum(c.height + 26 + PAD for _, c in col) for col in cols) + 10
    sh = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(sh)
    for i, col in enumerate(cols[:NCOL]):
        x = i * (CELLW + 10)
        y = 4
        for lab, c in col:
            d.text((x + 2, y), lab, fill=0, font=FONT)
            sh.paste(c, (x, y + 24))
            d.line([(x, y + 22), (x + CELLW, y + 22)], fill=170, width=1)
            y += c.height + 26 + PAD
        d.line([(x + CELLW + 4, 0), (x + CELLW + 4, H)], fill=110, width=3)
    sh = ImageEnhance.Sharpness(sh).enhance(1.6)
    sh.save(dest)
    return sh.size, len(cells), len(cols)


if __name__ == "__main__":
    reg, a, b, dest = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    cs = cellules(reg, a, b)
    print(planche(cs, dest), [l for l, _ in cs][:4], "...")
