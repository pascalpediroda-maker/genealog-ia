# -*- coding: utf-8 -*-
"""Saint-Pal-de-Chalencon (AD43) — FACADE SUR `nas.py`, plus un outil separe.

Ce module rendait les demi-pages et les zooms du registre de Saint-Pal avec sa propre
copie de la recette : sa pliure, sa boite d'encre, son plafond de 1990 px. `page.py` et
`zoomb.py` en avaient une autre pour l'AD42, et l'Indre-et-Loire n'en avait aucune. Trois
copies d'un meme savoir-faire, dont deux departements seulement profitaient.

DEPUIS LE 26 AOUT 2026 IL N'Y A QU'UN MOTEUR, `nas.py`, ET LE DEPARTEMENT EST UN ARGUMENT.
Ce fichier ne garde que ce qui est propre a Saint-Pal : le dossier par defaut, les vues
photographiees a l'envers, et le seuil de boite d'encre de 0,012 -- car les fractions de
zoom deja notees dans le corpus, et les decoupes d'actes deja publiees, sont relatives a
CE seuil-la. Le changer les deplacerait toutes.

  SP_DIR="<archives>/.../BMS 1687-1737" python sp.py 1 12
  python sp.py z <vue> <G|D> <y0> <y1> <dest> [x0] [x1] [div]

Meme commande, en passant par le moteur et sans variable d'environnement :
  python nas.py "43/saint-pal/BMS 1687-1737" 1 12
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nas

D = os.environ.get(
    "SP_DIR",
    r"<archives>/AD43 - Saint-Pal-de-Chalencon/BMS 1737-1771")
OUT = os.environ.get("SP_OUT", "vues")
# LES VUES 010, 011 ET 012 D'E-DEPOT 2/8 SONT PHOTOGRAPHIEES LA TETE EN BAS, signalees
# le 17 aout 2026 et restees illisibles faute d'une rotation.
ROT = [x for x in os.environ.get("SP_ROT", "").split(",") if x.strip()]
SEUIL = 0.012                       # celui d'origine : ne pas y toucher, voir l'en-tete


def demipage(n, side):
    return nas._page(D, n, side, ROT)


def boite(g):
    return nas.boite(g, SEUIL)


def rendre(n, side, pad=26):
    return nas.rendre(D, n, side, pad=pad, out=OUT, rot=ROT, seuil=SEUIL, prefixe="sp")


def zoom(n, side, y0, y1, dest, x0=0.0, x1=1.0, div=False):
    return nas.zb(D, n, side, y0, y1, dest, x0, x1, div=div,
                  out=OUT, rot=ROT, seuil=SEUIL)


if __name__ == "__main__":
    if sys.argv[1] == "z":
        a = sys.argv[2:]
        print(zoom(int(a[0]), a[1], float(a[2]), float(a[3]), a[4],
                   float(a[5]) if len(a) > 5 else 0.0,
                   float(a[6]) if len(a) > 6 else 1.0,
                   div=len(a) > 7 and a[7] == "1"))
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        for n in range(a, b + 1):
            for side, _ in nas.pages(nas.vue(D, n), ROT):
                print(*rendre(n, side), flush=True)
