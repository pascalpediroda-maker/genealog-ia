# -*- coding: utf-8 -*-
"""Demi-page d'un registre d'Usson-en-Forez (AD42) — FACADE SUR `nas.py`.

  python page.py <cle-de-actes.REGS> <vue_a> <vue_b>     ->  vues/<cle><nnn><G|D>.png

La recette et ses raisons sont dans `nas.rendre()` : une demi-page a 1990 px sur le grand
cote, recadree sur la boite d'encre. Ce fichier ne garde que la ligne de commande
historique et la table `actes.REGS`, qui nomme les registres d'Usson par une lettre --
« a » pour BMS 1773-1778, « n » pour EC 1793-1794.

CETTE TABLE EST LE DERNIER RESTE DE L'EPOQUE OU CHAQUE DEPARTEMENT AVAIT SON OUTIL. Elle
n'est plus necessaire : `nas.py` DESIGNE un registre par des bouts de son nom, sans rien
declarer. Les deux commandes ci-dessous font la meme chose, et la seconde marche dans les
cent departements :

  python page.py a 76 76
  python nas.py "42/usson/BMS 1773" 76 76
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nas
import actes

MAX = nas.MAX
OUT = "vues"


def boite(g):
    return nas.boite(g)


def dossier(reg):
    return os.path.join(actes.ROOT, actes.REGS[reg])


def rendre(reg, n, side, pad=34):
    return nas.rendre(dossier(reg), n, side, pad=pad, out=OUT, prefixe=reg)


if __name__ == "__main__":
    reg, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    d = dossier(reg)
    for n in range(a, b + 1):
        for side, _ in nas.pages(nas.vue(d, n)):
            p, s = rendre(reg, n, side)
            print(p, s, round(s[0] * s[1] / 750), flush=True)
