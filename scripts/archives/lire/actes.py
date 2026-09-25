# -*- coding: utf-8 -*-
"""Decoupe un registre en ACTES, reperes par leur mention de marge.

La marge porte, pour chaque acte, son type et son hameau ("Ent. d'Usson",
"Bapt. de la Grange neuve"). Ces mentions sont separees par du blanc : un
profil d'encre par ligne sur la bande de marge donne les debuts d'acte.

Garde-fou repris de symb.py : une vue de moins de 2600 px est une PAGE
SIMPLE, pas une double page. Y chercher une pliure coupe le texte en deux.
"""
import os, glob
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  _os.pardir, _os.pardir))
import config
ROOT = _os.path.join(config.archives(), "AD42 - Usson-en-Forez")
REGS = {"a": "BMS 1773-1778", "b": "BMS 1779-1783",
        "c": "BMS 1784-1788", "d": "BMS 1789-1792",
        "e": "BMS 1744-1750", "f": "BMS 1751-1755", "g": "BMS 1756-1761",
        "t": "TD deces 1802-1812", "u": "TD deces 1813-1822",
        "x": "EC deces 1812", "y": "EC 1793-1802", "z": "EC divers",
        # L'etat civil republicain, ou se trouve la mort de Jean PEYRET pere
        # (entre mars 1793 et mars 1794). PAGES SIMPLES : 1848 x 3000, donc
        # sous le seuil de 2600 px et jamais coupees en deux -- c'est correct.
        "n": "EC 1793-1794", "o": "EC 1794-1796",
        # ET USSON TIENT UN REGISTRE PAR TYPE D'ACTE, ce que trois agents ont
        # etabli le 17 aout 2026 : "EC 1793-1794" est un SUPPLEMENT AUX
        # NAISSANCES, clos "contenant cent vingt-cinq naissances", suivi d'un
        # volume MARIAGES. Les deces sont ailleurs -- ici.
        "p": "EC D 1794", "q": "EC N 1794"}
MARGE = 340          # largeur de la bande de marge
MINRUN = 26          # hauteur mini d'une mention de marge
GAP = 40             # blanc mini entre deux mentions


def vues(reg):
    return sorted(glob.glob(os.path.join(ROOT, REGS[reg], "v*.jpg")))


def pages(path):
    """rend [(side, PIL.Image)] — jamais de pliure sur une page simple."""
    im = Image.open(path).convert("L")
    g = np.asarray(im)
    if g.shape[1] < 2600:
        return [("S", im)]
    col = g.mean(axis=0)
    w = len(col)
    a, b = int(w * 0.40), int(w * 0.60)
    gx = a + int(np.argmin(col[a:b]))
    return [("G", im.crop((0, 0, gx, g.shape[0]))),
            ("D", im.crop((gx, 0, g.shape[1], g.shape[0])))]


def bord(g, side):
    """premiere colonne de papier : liesere noir du scan a gauche, ombre de
    pliure a droite. Les deux sont sombres sur toute la hauteur, donc on
    avance tant que la colonne est majoritairement sombre."""
    prof = (g < 90).mean(axis=0)
    s = 0
    while s < g.shape[1] - MARGE and prof[s] > 0.45:
        s += 1
    if side == "D":
        s += 30                       # marge de securite sur l'ombre de pliure
        while s < g.shape[1] - MARGE and prof[s] > 0.45:
            s += 1
    return s


def colonne_texte(g, x0):
    """x ou commence le bloc de texte : la marge s'arrete la.

    Le bloc de texte est la seule zone dont presque toutes les lignes sont
    encrees sur toute la hauteur ; la marge, elle, est trouee de blanc. Sans
    ce calcul la bande de marge mord sur le texte des pages ou le bloc
    commence tot, et toutes les mentions fusionnent en une seule.
    """
    bg = np.percentile(g, 85)
    dark = (g < bg - 55)
    col = dark.mean(axis=0)
    lim = min(g.shape[1], x0 + 700)
    run = 0
    for x in range(x0 + 110, lim):
        run = run + 1 if col[x] > 0.22 else 0
        if run >= 55:
            return max(x0 + 110, x - run - 18)
    return x0 + MARGE


def mentions(im, side="G"):
    """y de debut de chaque mention de marge, du haut vers le bas."""
    g = np.asarray(im).astype(np.int16)
    x0 = bord(g, side)
    band = g[:, x0:colonne_texte(g, x0)]
    # seuil adaptatif : le papier n'a pas la meme clarte d'un bord a l'autre
    bg = np.percentile(band, 85, axis=0)
    ink = (band < (bg - 55)).mean(axis=1)
    on = ink > 0.012
    runs, i, n = [], 0, len(on)
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    # fusionne ce qui est separe par moins de GAP
    out = []
    for r in runs:
        if out and r[0] - out[-1][1] < GAP:
            out[-1][1] = r[1]
        else:
            out.append(r)
    return x0, [r for r in out if r[1] - r[0] >= MINRUN]


def decoupe(reg, a, b):
    """rend la liste des actes : (label, page_img, y_debut, y_fin)."""
    out = []
    for p in vues(reg)[a - 1:b]:
        n = os.path.basename(p)[1:4]
        for side, im in pages(p):
            x0, ms = mentions(im, side)
            for k, (y0, y1) in enumerate(ms):
                yn = ms[k + 1][0] if k + 1 < len(ms) else im.height
                out.append((f"{reg}{n}{side}.{k+1}", im, x0, max(0, y0 - 24), yn))
    return out


def planche(actes, dest, lignes=3, par=6, hmax=430, scale=1.0):
    """empile les premieres lignes de chaque acte, marge comprise."""
    cells = []
    for lab, im, x0, y0, y1 in actes:
        h = min(hmax, max(150, y1 - y0))
        c = im.crop((x0, y0, im.width, min(im.height, y0 + h)))
        if scale != 1.0:
            c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
        c = ImageOps.autocontrast(c, cutoff=1)
        cells.append((lab, c))
    W = max(c.width for _, c in cells)
    H = sum(c.height for _, c in cells) + 30 * len(cells)
    sh = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(sh)
    f = config.police_pil(24)
    y = 0
    for lab, c in cells:
        d.line([(0, y), (W, y)], fill=120, width=3)
        d.text((6, y + 3), lab, fill=0, font=f)
        sh.paste(c, (0, y + 28))
        y += c.height + 30
    sh = ImageEnhance.Sharpness(sh).enhance(1.7)
    sh.save(dest)
    return sh.size


if __name__ == "__main__":
    import sys
    reg, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    ac = decoupe(reg, a, b)
    print(len(ac), "actes")
    for lab, im, x0, y0, y1 in ac:
        print(lab, y0, y1, y1 - y0)
