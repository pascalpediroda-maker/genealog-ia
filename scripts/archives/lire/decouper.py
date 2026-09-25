# -*- coding: utf-8 -*-
"""Decoupe les actes de Saint-Pal en images durables, pour les attacher aux
evenements du corpus.

  python decouper.py

POURQUOI DECOUPER PLUTOT QUE MONTRER LA VUE. Les vues brutes sont des DOUBLES
PAGES de 2500 px : reduite a la largeur d'un ecran, la page entiere ne se lit
plus. On decoupe donc l'acte seul, aux memes fractions de boite d'encre que
celles qui ont servi a le lire.

ET ON DECOUPE LARGE. Le 24 aout 2026, le généalogiste a signale que les decoupes etaient
"cropees trop court" : les fractions avaient ete relevees a l'oeil sur la
demi-page rendue, et elles rognaient la derniere ligne, la signature du cure,
parfois la premiere ligne. UNE LIGNE DE VOISINAGE EN TROP NE COUTE RIEN ; une
signature coupee coute la moitie de l'interet de l'image. D'ou PAD, applique
partout.

LE BORD DROIT D'UNE PAGE DE GAUCHE PLONGE DANS LA RELIURE, et aucun cadrage ne
le rattrapera : sur le mariage de 1668, "et de Louyse R..." disparait dans la
pliure. C'est pour cela que ce patronyme est [non lu] et le restera. On etend
tout de meme de MARGE_PLIURE pixels au-dela de la pliure detectee, qui tombe
une centaine de pixels trop tot.
"""
import sys, os
import numpy as np
from PIL import Image, ImageOps, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sp

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  _os.pardir, _os.pardir))
import config

DEST = config.decoupes()
R5 = r"<archives>/AD43 - Saint-Pal-de-Chalencon/M 1663-1673"
R6 = r"<archives>/AD43 - Saint-Pal-de-Chalencon/BMS 1672-1687"
R7 = r"<archives>/AD43 - Saint-Pal-de-Chalencon/BMS 1687-1737"
R8 = r"<archives>/AD43 - Saint-Pal-de-Chalencon/BMS 1737-1771"

PAD = 0.030          # marge haut/bas, en fraction de la hauteur de boite d'encre
MARGE_PLIURE = 190   # pixels rendus au-dela de la pliure, sur une page de gauche
MAX = 1990

# (registre, vue, cote, y0, y1, nom du fichier)
ACTES = [
 (R5,  24, 'G', 0.530, 0.975, "1668-07-18 mariage PEYRET x MEY - Saint-Pal E-depot 2-5 v024G.png"),
 (R6,  79, 'G', 0.055, 0.205, "1680-04-30 bapteme Irenee PEYRET - Saint-Pal E-depot 2-6 v079G.png"),
 (R6,  89, 'D', 0.745, 0.860, "1681-03-18 bapteme Marie THELEYRE - Saint-Pal E-depot 2-6 v089D.png"),
 (R6, 111, 'D', 0.830, 0.955, "1683-03-26 bapteme Marie PEYRET - Saint-Pal E-depot 2-6 v111D.png"),
 (R7, 207, 'D', 0.018, 0.132, "1707-07-24 sepulture Jean PEYRET - Saint-Pal E-depot 2-7 v207D.png"),
 (R7, 222, 'D', 0.042, 0.190, "1709-05-05 bapteme Marguerite PEYRET - Saint-Pal E-depot 2-7 v222D.png"),
 (R7, 225, 'G', 0.032, 0.180, "1709-11-02 sepulture Marguerite PEYRET - Saint-Pal E-depot 2-7 v225G.png"),
 (R7, 234, 'D', 0.172, 0.450, "1711-02-10 mariage PEYRET x THELEYRE - Saint-Pal E-depot 2-7 v234D.png"),
 (R7, 241, 'D', 0.612, 0.782, "1712-02-06 bapteme Mathieu PEYRET - Saint-Pal E-depot 2-7 v241D.png"),
 (R8,   8, 'D', 0.240, 0.500, "1737-09-17 mariage PEYRET x VALENTIN - Saint-Pal E-depot 2-8 v008D.png"),
 (R8,  35, 'G', 0.780, 1.000, "1740-04-20 sepulture Mathieu PEYRET - Saint-Pal E-depot 2-8 v035G.png"),
 (R8,  39, 'G', 0.198, 0.405, "1740-07-27 bapteme Catherine PEYRET - Saint-Pal E-depot 2-8 v039G.png"),
 (R8,  41, 'G', 0.040, 0.165, "1740-09 sepulture Benoit PEYRET - Saint-Pal E-depot 2-8 v041G.png"),
 (R8,  42, 'G', 0.070, 0.258, "1740-10-18 bapteme Jeanne-Marie PEYRET - Saint-Pal E-depot 2-8 v042G.png"),
 (R8,  58, 'G', 0.658, 0.832, "1742-01-21 bapteme Marie PEYRET - Saint-Pal E-depot 2-8 v058G.png"),
 (R8, 117, 'G', 0.285, 0.505, "1747-01-16 bapteme Jean PEYRET - Saint-Pal E-depot 2-8 v117G.png"),
 (R8, 126, 'D', 0.325, 0.425, "1747-11-16 sepulture Marie VIALAVON - Saint-Pal E-depot 2-8 v126D.png"),
]


def decoupe(reg, vue, side, y0, y1, nom):
    sp.D = reg
    pim = sp.demipage(vue, side)
    X0, Y0, X1, Y1 = sp.boite(np.asarray(pim))
    H = Y1 - Y0
    # marge verticale, bornee par la demi-page
    a = max(0, Y0 + int((y0 - PAD) * H))
    b = min(pim.height, Y0 + int((y1 + PAD) * H))
    # la pliure tombe trop tot : on rend ce qu'on peut au-dela, sans sortir de l'image
    droite = pim.width if side == "G" else X1
    droite = min(pim.width, droite + (MARGE_PLIURE if side == "D" else 0))
    c = pim.crop((max(0, X0 - 30), a, droite, b))
    f = max(1.0, MAX / max(c.width, c.height))
    c = c.resize((int(c.width * f), int(c.height * f)), Image.LANCZOS)
    c = ImageEnhance.Sharpness(ImageOps.autocontrast(c, cutoff=1)).enhance(2.2)
    os.makedirs(DEST, exist_ok=True)
    q = os.path.join(DEST, nom)
    c.save(q)
    return c.size


if __name__ == "__main__":
    for reg, vue, side, y0, y1, nom in ACTES:
        print("%-70s %s" % (nom[:70], decoupe(reg, vue, side, y0, y1, nom)))
