# -*- coding: utf-8 -*-
"""Planche des MARGES d'une plage de vues — FACADE SUR `nas.py`.

  python marges.py <dossier-ou-designation> <a> <b> <prefixe> [largeur=0.22] [par=6]
  python marges.py "42/usson/BMS 1773" 80 92 marge 0.34 4

La recette et ses raisons sont dans `nas.marges()`. Ce fichier ne garde que la ligne de
commande historique.

ET IL PORTAIT UNE INVERSION QUI L'A RENDU FAUX HORS DE L'AD43. Il testait
« largeur < 2600 px -> double page », c'est-a-dire le contraire d'`actes.py`. Ca tombait
juste a Saint-Pal, dont les doubles font 2500 px, et faux partout ailleurs : une double
page de 3511 px y passait pour une page simple, et la planche empilait la marge de gauche
d'une vue entiere au lieu de celle de chaque page. Le moteur tranche desormais par
L'ORIENTATION, qui est vraie des trois portails a la fois.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nas

if __name__ == "__main__":
    d = nas.reg(sys.argv[1])
    a, b, pref = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    frac = float(sys.argv[5]) if len(sys.argv) > 5 else 0.22
    par = int(sys.argv[6]) if len(sys.argv) > 6 else 6
    rot = [x for x in os.environ.get("NAS_ROT", "").split(",") if x.strip()]
    for p, taille in nas.marges(d, a, b, pref, frac, par, rot=rot):
        print(p, taille, flush=True)
