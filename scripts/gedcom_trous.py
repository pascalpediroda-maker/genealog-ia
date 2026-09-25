# -*- coding: utf-8 -*-
"""
Où l'arbre s'arrête, et par quel bout le reprendre.

Liste les ascendants d'une personne dont il manque quelque chose — les parents,
une date, un lieu — puis les regroupe par commune et par époque. Le classement
ne cherche pas l'ancêtre le plus lointain mais **le trou le moins cher** : celui
dont on connaît la commune, dont la période est couverte par un fonds en ligne,
et qui est proche de la racine, donc rattaché à coup sûr.

    python scripts/gedcom_trous.py                    # les communes, par rendement
    python scripts/gedcom_trous.py --commune "Cléry"  # le détail d'une commune

Un ancêtre sans parents ET sans commune connue n'est pas une piste : c'est un nom.
Il figure au décompte, jamais en tête de liste.
"""

import os
import re
import sys
import argparse
import collections
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gedcom_lib import Gedcom, sans_accents  # noqa: E402

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "stengel-hume", "corrige")
DEFAUT = "LEO-colin - corrige.ged"
RACINE = "001159"          # Léo STENGEL, né en 2001


def normalise_lieu(v):
    """« Cléry-Saint-André (Paroisse Notre-Dame) » → « CLERY-SAINT-ANDRE »."""
    if not v:
        return ""
    v = re.sub(r"\(.*?\)", " ", v)
    v = re.sub(r"\b\d{4,5}\b", " ", v)          # codes postaux
    v = sans_accents(v).strip(" ,.-")
    v = re.sub(r"\s+", " ", v)
    return v.upper()


def epoque(p, g):
    """Année utile pour situer une recherche : naissance, sinon mariage, sinon décès."""
    for d in (p.naissance, p.deces):
        if d and d.annee:
            return d.annee
    for fid in p.fams:
        f = g.familles.get(fid)
        if f and f.mariage and f.mariage.annee:
            return f.mariage.annee
    return None


def lieu_utile(p, g):
    """La commune la mieux attestée pour cette personne, propre à guider une recherche."""
    for v in (p.lieu_naissance, p.lieu_deces):
        if normalise_lieu(v):
            return normalise_lieu(v)
    for fid in p.fams:
        f = g.familles.get(fid)
        if f and normalise_lieu(f.lieu_mariage):
            return normalise_lieu(f.lieu_mariage)
    # à défaut, le lieu de naissance d'un enfant : un couple baptise là où il vit
    for fid in p.fams:
        f = g.familles.get(fid)
        if not f:
            continue
        for cid in f.enfants:
            c = g.personnes.get(cid)
            if c and normalise_lieu(c.lieu_naissance):
                return normalise_lieu(c.lieu_naissance)
    return ""


def manques(p, g):
    """Ce qui manque à cette personne, en clair."""
    out = []
    if not any(pe or me for pe, me in g.parents(p.id)):
        out.append("parents")
    if not p.naissance:
        out.append("naissance")
    if not p.deces:
        out.append("deces")
    for fid in p.fams:
        f = g.familles.get(fid)
        if f and f.mari and f.femme and not f.mariage:
            out.append("mariage")
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fichier", default=DEFAUT)
    ap.add_argument("--racine", default=RACINE)
    ap.add_argument("--commune", default=None)
    ap.add_argument("--top", type=int, default=18)
    args = ap.parse_args()

    g = Gedcom(os.path.join(BASE, args.fichier))
    gens = g.ascendance(args.racine)
    gen_de = {i: gg for gg, ids in gens.items() for i in ids}

    lignes = []
    for pid, gg in gen_de.items():
        p = g.personnes.get(pid)
        if not p:
            continue
        m = manques(p, g)
        if not m:
            continue
        lignes.append({"id": pid, "gen": gg, "p": p, "manque": m,
                       "lieu": lieu_utile(p, g), "an": epoque(p, g)})

    if args.commune:
        c = sans_accents(args.commune).upper()
        sel = [l for l in lignes if c in l["lieu"]]
        sel.sort(key=lambda l: (l["an"] or 9999, l["gen"]))
        print(f"{len(sel)} ascendants incomplets rattachés à « {args.commune} »")
        print()
        print(f"{'gen':>3} {'année':>6}  {'manque':22} personne")
        print("-" * 96)
        for l in sel:
            p = l["p"]
            nom = f"{p.prenom} {'/'.join(p.patronymes)}"
            print(f"{l['gen']:>3} {str(l['an'] or '—'):>6}  "
                  f"{','.join(l['manque']):22} @{l['id']}@ {nom[:52]}")
        return

    # --- regroupement par commune ---------------------------------------
    par_lieu = collections.defaultdict(list)
    for l in lignes:
        par_lieu[l["lieu"] or "(lieu inconnu)"].append(l)

    print(f"Racine          : {g.personnes[args.racine]}")
    print(f"Ascendants      : {sum(len(v) for v in gens.values()) - 1}")
    print(f"Dont incomplets : {len(lignes)}")
    sans = len(par_lieu.get("(lieu inconnu)", []))
    print(f"Dont sans commune connue : {sans}  — ce ne sont pas des pistes, "
          f"seulement des noms")
    print()

    def score(items):
        """Rendement : beaucoup de trous, proches de la racine, et localisés."""
        if not items:
            return 0
        prox = sum(1 / (1 + l["gen"]) for l in items)
        return len(items) * 0.4 + prox * 12

    classe = sorted(((k, v) for k, v in par_lieu.items() if k != "(lieu inconnu)"),
                    key=lambda kv: -score(kv[1]))

    print(f"{'commune':34} {'trous':>5} {'gén.':>9} {'période':>13}  manques dominants")
    print("-" * 104)
    for lieu, items in classe[:args.top]:
        gmin = min(l["gen"] for l in items)
        gmax = max(l["gen"] for l in items)
        ans = sorted(l["an"] for l in items if l["an"])
        per = f"{ans[0]}-{ans[-1]}" if ans else "—"
        cpt = collections.Counter(m for l in items for m in l["manque"])
        dom = ", ".join(f"{k} ({n})" for k, n in cpt.most_common(3))
        print(f"{lieu[:34]:34} {len(items):>5} {gmin:>4}-{gmax:<4} {per:>13}  {dom}")


if __name__ == "__main__":
    main()
