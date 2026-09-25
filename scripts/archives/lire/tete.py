# -*- coding: utf-8 -*-
"""Planche des premieres lignes de chaque demi-page, RECADREE SUR L'ENCRE
   — FACADE SUR `nas.py`.

  python tete.py <dossier-ou-designation> <a> <b> <nb_par_planche> <prefixe>
  python tete.py "43/saint-pal/BMS 1737" 90 105 6 t

`strip.py` coupait une fraction du HAUT DE LA PAGE : sur les registres anciens, dont la
marge haute fait le quart du feuillet, il ne rendait que du papier. Ici on prend le haut
de la BOITE D'ENCRE, donc la premiere ligne ecrite, quelle que soit la mise en page.

La recette est dans `nas.tetes()`, qui la sert a tous les departements — et c'est le
resultat de la consigne : un savoir-faire ecrit une fois, pas une copie par portail.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nas

if __name__ == "__main__":
    d = nas.reg(sys.argv[1])
    a, b = int(sys.argv[2]), int(sys.argv[3])
    par = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    pref = sys.argv[5] if len(sys.argv) > 5 else "tete"
    rot = [x for x in os.environ.get("NAS_ROT", "").split(",") if x.strip()]
    for p, taille in nas.tetes(d, a, b, pref + ".png", rot=rot, par=par):
        print(p, taille, flush=True)
