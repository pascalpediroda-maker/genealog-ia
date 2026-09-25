# -*- coding: utf-8 -*-
"""Zoom sur la BOITE D'ENCRE d'une demi-page d'Usson (AD42) — FACADE SUR `nas.py`.

  python zoomb.py <cle> <vue> <G|D> <y0> <y1> <dest> [x0] [x1] [div]

Memes fractions que le rendu de `page.py` : on repere sur l'image qu'on vient de lire et
on decoupe sans recalculer. `div=1` divise par un fond floute -- c'est ce qui a rendu
lisible « veuve de Jean PEYRET » sur l'acte de 1812.

La recette est dans `nas.zb()`, qui la sert a tous les departements. Meme commande sans
la table des cles d'Usson :

  python nas.py z "42/usson/BMS 1773" 76 G 0.30 0.40 z.png 0.0 1.0 1
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nas
import page


def zb(reg, n, side, y0, y1, dest, x0=0.0, x1=1.0, div=False, up=1):
    return nas.zb(page.dossier(reg), n, side, y0, y1, dest, x0, x1,
                  div=div, up=up, out="vues")


if __name__ == "__main__":
    a = sys.argv[1:]
    kw = {"div": a[8] == "1"} if len(a) > 8 else {}
    print(zb(a[0], int(a[1]), a[2], float(a[3]), float(a[4]), a[5],
             float(a[6]) if len(a) > 6 else 0.0,
             float(a[7]) if len(a) > 7 else 1.0, **kw))
