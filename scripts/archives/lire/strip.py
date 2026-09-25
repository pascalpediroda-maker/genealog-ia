# -*- coding: utf-8 -*-
"""OBSOLETE — utiliser `tete.py`, ou `python nas.py t`.

Ce module coupait une fraction du HAUT DE LA PAGE. Sur les registres anciens, dont la
marge haute fait le quart du feuillet, il ne rendait donc que du papier : c'est pour ca
que `tete.py` a ete ecrit, qui recadre sur la BOITE D'ENCRE. Les deux ont coexiste, et
la mauvaise version restait la plus facile a appeler.

Il redirige desormais vers la bonne, avec les memes arguments.
"""
import os
import runpy
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print("strip.py est obsolete : recadrage sur l'encre par tete.py", file=sys.stderr)
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tete.py"),
               run_name="__main__")
