# -*- coding: utf-8 -*-
"""Rend la table « moteur -> departements » a partir de portails.json.

CETTE TABLE ETAIT RECOPIEE A LA MAIN DANS README.md, ET ELLE A DERIVE. Le 5 septembre
2026 elle annoncait encore « trois moteurs couvrent les six portails ouverts ici » alors
qu'il y en avait sept pour seize, et l'AD46 — ouvert le matin meme — n'y figurait pas.
Le généalogiste l'a vu avant moi.

Une table recopiee est une table qui ment tot ou tard. Celle-ci se regenere :

    python scripts/archives/moteurs_table.py            # markdown, a coller dans README.md
    python scripts/archives/moteurs_table.py --court    # une ligne par moteur

⚠️ ET CE SCRIPT A REFAIT L'ERREUR QU'IL DEVAIT EMPECHER. Il a porte jusqu'au 18 septembre
2026 ses PROPRES tables en dur — `MODULES` et `EDITEUR`, sept moteurs chacune — pendant que
`portails.json` en comptait dix. Les trois qui manquaient (`gaia`, `anaphore`,
`aspnet-webforms`) sortaient en « — », c'est-a-dire « aucun module », c'est-a-dire le
contraire de la verite pour GAIA : `gaia.py` existe depuis le 12 septembre. Un outil ecrit
contre la derive n'y echappe pas tant qu'il porte lui-meme une copie.

Elles vivent desormais dans `_meta.moteurs` de `portails.json`, avec la signature attendue
dans `identifier.js` — et `portails_coherence.py` echoue si l'une des deux manque.

La source de verite reste `portails.json`, et elle seule.
"""
import io
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.join(D, "portails.json")


def charge():
    return json.load(io.open(CONF, encoding="utf-8"))


def _modules(m):
    """Le libelle de la colonne « Module » d'un moteur.

    ⚠️ LA DETTE S'AFFICHE MEME QUAND UN MODULE EXISTE. La premiere version ne la rendait
    qu'a defaut de module, si bien que l'avertissement le plus important de la table — le
    module 4D n'a jamais tourne contre son portail — disparaissait a la seconde ou le
    fichier etait cree. Un module ecrit n'est pas un module verifie.
    """
    mods = m.get("modules") or []
    dette = m.get("dette")
    if not mods:
        return "*" + (dette or "aucun module") + "*"
    txt = " + ".join("`%s`" % x for x in mods)
    if m.get("note"):
        txt += " — " + m["note"]
    if dette:
        txt += " — **" + dette + "**"
    return txt


def table(c=None):
    c = c or charge()
    connus = c["_meta"]["moteurs"]
    par = {}
    for p in c["portails"]:
        if p.get("moteur"):
            par.setdefault(p["moteur"], []).append(p)
    lignes = []
    for m in sorted(par, key=lambda k: (-len(par[k]), k)):
        ps = sorted(par[m], key=lambda z: z.get("dept") or z["id"])
        depts = " · ".join(("**%s** %s" % (z["dept"], z.get("nom", ""))).strip()
                           if z.get("dept") else z.get("nom", z["id"]) for z in ps)
        fiche = connus.get(m, {})
        lignes.append((fiche.get("editeur", m), _modules(fiche), depts, len(ps),
                       sum(1 for z in ps if z.get("http_simple"))))
    sans = [p for p in c["portails"] if not p.get("moteur")]
    return lignes, sum(len(v) for v in par.values()), len(par), sans


def markdown(c=None):
    lignes, n_portails, n_moteurs, sans = table(c)
    out = ["| Moteur | Module | Départements branchés |", "|---|---|---|"]
    for nom, mod, depts, _, _ in lignes:
        out.append("| **%s** | %s | %s |" % (nom, mod, depts))
    out.append("")
    out.append("*%d moteurs, %d portails à moteur, plus %d sources sans moteur "
               "(%d fiches en tout). Table générée par "
               "`python scripts/archives/moteurs_table.py` — la source de vérité est "
               "`portails.json`.*" % (n_moteurs, n_portails, len(sans),
                                      n_portails + len(sans)))
    return "\n".join(out)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if "--court" in sys.argv:
        lignes, n_portails, n_moteurs, sans = table()
        for nom, _, depts, n, s in lignes:
            print("%-34s %2d portail(s), %d sans navigateur" % (nom, n, s))
        print("\n%d moteurs, %d portails à moteur, %d sources sans moteur"
              % (n_moteurs, n_portails, len(sans)))
    else:
        print(markdown())
