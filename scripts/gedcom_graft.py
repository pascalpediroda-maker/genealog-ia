# -*- coding: utf-8 -*-
"""
Où souder deux arbres GEDCOM.

Cherche, parmi les ancêtres d'une personne dont l'arbre s'arrête (« la
frontière »), ceux qui existent aussi dans un second fichier — et dont ce
second fichier connaît les parents. Chaque correspondance est un point de
soudure possible, et le « gain » est le nombre d'ancêtres qu'elle apporterait.

    python scripts/gedcom_graft.py

Rien n'est écrit : ce script propose, il ne greffe pas. Une soudure se décide
sur pièces, pas sur un score — le score sert à savoir par où commencer.

Prudence héritée du corpus : on ne fusionne jamais sur une ressemblance. Un
homonyme de la même époque est le mode de défaillance le plus courant en
généalogie, et ce fichier en est plein — vingt FRANCOIS HUME, dont neuf nés
« avant » une date. Le score ci-dessous exige donc un faisceau : patronyme,
prénom, dates compatibles, ET un témoin de parenté (conjoint ou enfants).
"""

import os
import sys
import argparse
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gedcom_lib import Gedcom, compatible, sans_accents  # noqa: E402

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "stengel-hume", "corrige")


def prenoms(p):
    """Les tokens du prénom, sans accents. « DIT-gnégné HILAIRE » → deux jetons."""
    return [t for t in sans_accents(p.prenom).replace("-", " ").split() if len(t) > 1]


def patronymes(p):
    return {sans_accents(s) for s in p.patronymes if s and s != "?"}


def score(a, ga, b, gb):
    """
    Faisceau d'indices entre la personne a (arbre de base) et b (arbre source).

    Rend (score, raisons) ou (None, motif de rejet).
    """
    pa, pb = patronymes(a), patronymes(b)
    if not pa or not pb or not (pa & pb):
        return None, "patronyme"
    if a.sexe and b.sexe and a.sexe != b.sexe:
        return None, "sexe"
    if not compatible(a.naissance, b.naissance):
        return None, "naissances incompatibles"
    if not compatible(a.deces, b.deces):
        return None, "deces incompatibles"

    s, raisons = 0, []
    na, nb = prenoms(a), prenoms(b)
    if not na or not nb:
        # Un « ? » ne confirme rien : il s'apparie avec tout le monde. C'est
        # ainsi qu'un « ? HUME né avant 1560 » s'est retrouvé apparié à un
        # AUGUSTIN né avant 1740. Sans prénom des deux côtés, on ne conclut pas.
        return None, "prenom inconnu"
    if na[0] == nb[0]:
        s += 3
        raisons.append("meme prenom")
        if len(na) > 1 and len(nb) > 1 and set(na[1:]) & set(nb[1:]):
            s += 2
            raisons.append("prenoms secondaires communs")
    elif set(na) & set(nb):
        s += 2
        raisons.append("un prenom commun")
    else:
        return None, "prenom"

    for champ, lib in (("naissance", "naissance"), ("deces", "deces")):
        da, db = getattr(a, champ), getattr(b, champ)
        if da and db:
            if da.ferme and db.ferme and da.jour and db.jour \
                    and (da.annee, da.mois, da.jour) == (db.annee, db.mois, db.jour):
                s += 5
                raisons.append(f"{lib} au jour près ({da})")
            elif da.ferme and db.ferme and da.annee == db.annee:
                s += 3
                raisons.append(f"{lib} même année ({da} / {db})")
            else:
                s += 1
                raisons.append(f"{lib} compatible ({da} / {db})")

    # temoins de parente : conjoint et enfants
    cja = {n for c in ga.conjoints(a.id) if c in ga.personnes
           for n in patronymes(ga.personnes[c])}
    cjb = {n for c in gb.conjoints(b.id) if c in gb.personnes
           for n in patronymes(gb.personnes[c])}
    if cja & cjb:
        s += 4
        raisons.append(f"conjoint {sorted(cja & cjb)[0]}")

    ea = {t for e in ga.enfants(a.id) if e in ga.personnes
          for t in prenoms(ga.personnes[e])[:1]}
    eb = {t for e in gb.enfants(b.id) if e in gb.personnes
          for t in prenoms(gb.personnes[e])[:1]}
    communs = ea & eb
    if communs:
        s += 2 * min(len(communs), 4)
        raisons.append(f"{len(communs)} enfant(s) de meme prenom : "
                       + ", ".join(sorted(communs)[:4]))
    return s, raisons


def gain(g, pid):
    """Combien d'ancetres ce fichier connait-il au-dessus de cette personne ?"""
    gens = g.ascendance(pid)
    return sum(len(v) for k, v in gens.items() if k > 0), max(gens) if gens else 0


def chercher(base, racine, sources, seuil=8):
    frontiere = base.frontiere(racine)
    print(f"Arbre de base   : {os.path.basename(base.chemin)}")
    print(f"Racine          : {base.personnes[racine]}")
    print(f"Ancetres connus : {sum(len(v) for v in base.ascendance(racine).values()) - 1}")
    print(f"Points d'arret  : {len(frontiere)}")
    print()

    resultats = []
    for nom_src, src in sources:
        index = collections.defaultdict(list)
        for p in src.personnes.values():
            for n in patronymes(p):
                index[n].append(p)
        rejets = collections.Counter()
        for gen, pid in frontiere:
            a = base.personnes[pid]
            candidats = {}
            for n in patronymes(a):
                for b in index.get(n, ()):
                    candidats[b.id] = b
            for b in candidats.values():
                s, raisons = score(a, base, b, src)
                if s is None:
                    rejets[raisons] += 1
                    continue
                if s < seuil:
                    continue
                n_anc, prof = gain(src, b.id)
                if n_anc == 0:
                    continue
                resultats.append((n_anc, s, gen, pid, a, nom_src, b, prof, raisons))
        print(f"[{nom_src}] rejets : {dict(rejets)}")
    print()
    return sorted(resultats, key=lambda r: (-r[0], -r[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--racine", default="001159", help="id de la personne de depart")
    ap.add_argument("--seuil", type=int, default=8)
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    base = Gedcom(os.path.join(BASE, "LEO-colin - corrige.ged"))
    sources = [(n, Gedcom(os.path.join(BASE, f))) for n, f in
               [("HUME", "HUME 2026 - corrige.ged"),
                ("STENGEL", "STENGEL 2026 - corrige.ged")]]

    res = chercher(base, args.racine, sources, args.seuil)
    print("=" * 78)
    print(f"POINTS DE SOUDURE POSSIBLES : {len(res)}")
    print("=" * 78)
    vus = set()
    montre = 0
    for n_anc, s, gen, pid, a, nom_src, b, prof, raisons in res:
        if pid in vus:
            continue
        vus.add(pid)
        montre += 1
        if montre > args.top:
            continue
        print(f"+{n_anc:4d} ancetres ({prof} gen.)  score {s:2d}   "
              f"gen{gen} de l'arbre de base")
        print(f"      base    @{pid}@  {a}")
        print(f"      {nom_src:7s} @{b.id}@  {b}")
        print(f"      indices : {'; '.join(raisons)}")
        print()
    if montre > args.top:
        print(f"... et {montre - args.top} autres points d'arret avec correspondance.")


if __name__ == "__main__":
    main()
