# -*- coding: utf-8 -*-
"""CHAQUE MEDIA DU CORPUS EST-IL DU BON COTE ? — et répond-il ?

    python scripts/media_sur_x.py

LA REGLE, ET C'EST CELLE DE PASCAL, LE 27 AOUT 2026 :

  * une PHOTOGRAPHIE DE FAMILLE vit sur `S:`, dans son dossier de date. C'est la
    photothèque du généalogiste, antérieure au corpus : celui-ci la cite, il ne la range pas.
  * TOUT LE RESTE vit sur `<archives>/\Archives genealogiques\\` — actes, matricules, documents
    de famille, poster, et la base Hérédis `le généalogiste.hmw\\`, regroupée là ce jour-là.

CE FICHIER A DEJA EU TORT UNE FOIS, ET C'EST POUR CA QU'IL EXISTE. Ecrit le 26 août au soir
sous le titre « tout média du corpus vit sur X: », il a tiré 121 photographies de famille
sur X: avant que le généalogiste ne corrige : « je veux bien garder les photos de famille dans S:
rangées par date ». La migration a été défaite, les copies effacées, et la règle réécrite
ici. **Une convention de rangement se demande à celui dont c'est le disque.**

CE QU'IL FAIT MAINTENANT : il rapporte, il ne déplace plus rien. Deux questions, et il ne
répond qu'à elles — un média est-il du bon côté, et le fichier répond-il ? Le déplacement,
lui, se fait à la main, une fois, en sachant ce qu'on fait.
"""
import collections
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
X = "x:/archives genealogiques"
S = "s:/"
# Sur X:, ce qui n'est PAS un fonds d'archives et qui n'a rien a y faire : rien pour
# l'instant. Sur S:, ce qui devrait etre sur X: -- la base Heredis, qui en est partie.
HORS_S = ("pascal.hmw",)


def medias():
    for nom, cle in (("events", "events"), ("persons", "persons")):
        d = json.load(io.open(os.path.join(DATA, nom + ".json"), encoding="utf-8"))
        for o in d[cle]:
            for m in (o.get("media") or []):
                if m.get("source_file"):
                    yield nom, o["id"], m["source_file"]


def main():
    tout = list(medias())
    par_disque = collections.Counter()
    absents, mauvais_cote = [], []
    for nom, oid, f in tout:
        p = f.replace("\\", "/").lower()
        if p.startswith(X):
            par_disque["X: (archives)" if "pascal.hmw" not in p else "X: (Hérédis)"] += 1
        elif p.startswith(S):
            par_disque["S: (photos de famille)"] += 1
            if any(h in p for h in HORS_S):
                mauvais_cote.append((oid, f))
        else:
            par_disque["ailleurs"] += 1
            mauvais_cote.append((oid, f))
        if not os.path.exists(f):
            absents.append((oid, f))

    print("%d médias référencés" % len(tout))
    for k, n in sorted(par_disque.items()):
        print("   %-26s %3d" % (k, n))

    if mauvais_cote:
        print("\n[!] %d médias du mauvais côté :" % len(mauvais_cote))
        for oid, f in mauvais_cote[:8]:
            print("      %-32s %s" % (oid, f))
    if absents:
        racines = collections.Counter(f[:2].upper() for _, f in absents)
        print("\n[!] %d médias INTROUVABLES : %s"
              % (len(absents), ", ".join("%d sur %s" % (n, r) for r, n in racines.most_common())))
        for oid, f in absents[:8]:
            print("      %-32s %s" % (oid, f))
        print("\n    Un disque n'est probablement pas monté. Le build refusera d'écrire")
        print("    media.json au-delà de 5 %% de manquants — c'est voulu.")
    if not mauvais_cote and not absents:
        print("\nTout est du bon côté, et tout répond.")
    return 1 if (mauvais_cote or absents) else 0


if __name__ == "__main__":
    sys.exit(main())
