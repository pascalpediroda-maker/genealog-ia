# -*- coding: utf-8 -*-
"""Zoom natif sur une bande d'une demi-page.

  python zoom.py <reg> <vue> <side> <y0> <y1> <dest.png> [x0 x1]

y0/y1 et x0/x1 sont des FRACTIONS de la demi-page (0..1), reperees sur le
rendu de page.py. La bande sort a 1990 px de grand cote maximum, donc plus
la bande est courte, plus l'ecriture est grande — c'est tout l'interet.
"""
import sys, os
from PIL import Image, ImageOps, ImageEnhance
import actes

MAX = 1990
OUT = "vues"


def zoom(reg, n, side, y0, y1, dest, x0=0.0, x1=1.0):
    pim = dict(actes.pages(actes.vues(reg)[n - 1]))[side]
    W, H = pim.size
    c = pim.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    f = MAX / max(c.width, c.height)
    if f > 1:
        f = min(f, 3.0)
    c = c.resize((max(1, int(c.width * f)), max(1, int(c.height * f))), Image.LANCZOS)
    c = ImageOps.autocontrast(c, cutoff=1)
    c = ImageEnhance.Sharpness(c).enhance(2.3)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, dest)
    c.save(p)
    return p, c.size


if __name__ == "__main__":
    a = sys.argv[1:]
    reg, n, side, y0, y1, dest = a[0], int(a[1]), a[2], float(a[3]), float(a[4]), a[5]
    x0 = float(a[6]) if len(a) > 6 else 0.0
    x1 = float(a[7]) if len(a) > 7 else 1.0
    print(zoom(reg, n, side, y0, y1, dest, x0, x1))
