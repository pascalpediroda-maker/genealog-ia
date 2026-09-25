# -*- coding: utf-8 -*-
"""Repointe les `source_file` dont le fichier a BOUGE, sans jamais en inventer un.

POURQUOI. La photothèque du généalogiste sur S: est la sienne, anterieure au corpus, et elle
VIT : il y range, il cree des sous-dossiers, il deplace. Le 28 aout 2026 au matin, sept
references sont tombees d'un coup parce que `Images Alfiero/` avait gagne un sous-dossier
`Genealogy/`. Le corpus ne range pas cette photothèque — il la cite ; c'est donc a lui de
se reaccorder, pas a elle de rester figee.

CE QUE CE SCRIPT NE FAIT PAS. Il ne devine pas, il ne rapproche pas par ressemblance, il
ne touche a rien de ce qui repond deja. Il cherche le MEME NOM DE FICHIER ailleurs sous
la meme racine, et ne repointe que s'il en trouve EXACTEMENT UN. Deux candidats, zero
candidat : il le dit et il laisse. Une image mal rattachee est pire qu'une image absente,
parce que l'absence, elle, se voit.

    python scripts/media_repointer.py           # rapport, n'ecrit rien
    python scripts/media_repointer.py --write   # applique
"""
import json, io, os, sys, collections

import config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = config.data()
# RACINES SANS RECOUVREMENT : « <photos>/Papa » est DANS « <photos>/ », et l'inclure deux fois faisait
# compter chaque fichier deux fois — d'ou sept « 2 candidats » qui etaient sept fois le meme
# chemin, et un refus de trancher parfaitement absurde.
RACINES = (config.photos(), config.archives())
WRITE = "--write" in sys.argv


def index_des_fichiers():
    """{nom en minuscules: [chemins DISTINCTS]}."""
    idx = collections.defaultdict(list)
    for racine in RACINES:
        if not os.path.isdir(racine):
            print("  [!] %s n'est pas monte — il ne sera pas fouille" % racine)
            continue
        for dossier, _, fichiers in os.walk(racine):
            for f in fichiers:
                chemin = os.path.join(dossier, f).replace("\\", "/")
                if chemin not in idx[f.lower()]:
                    idx[f.lower()].append(chemin)
    return idx


def meme_racine(candidats, avant):
    """DEUX COPIES D'UNE IMAGE NE SE VALENT PAS. Une meme photographie existe souvent sur
    S: (la phototheque du généalogiste) ET dans `le généalogiste.hmw/Media` (celle qu'Heredis s'est
    copiee). Quand le chemin casse etait sur S:, c'est sur S: qu'il faut le rattacher :
    la copie d'Heredis est un doublon technique, pas la piece de reference."""
    tete = avant.split("/")[0].lower()
    memes = [c for c in candidats if c.split("/")[0].lower() == tete]
    return memes[0] if len(memes) == 1 else None


def main():
    idx = index_des_fichiers()
    print("%d noms de fichiers indexes" % len(idx))
    repares, ambigus, perdus = [], [], []

    def traiter(porteur, m):
        sf = m.get("source_file")
        if not sf or os.path.exists(sf):
            return
        cands = idx.get(os.path.basename(sf).lower(), [])
        choix = cands[0] if len(cands) == 1 else (meme_racine(cands, sf) if cands else None)
        if choix:
            repares.append((porteur, sf, choix))
            m["source_file"] = choix
        elif cands:
            ambigus.append((porteur, sf, cands))
        else:
            perdus.append((porteur, sf))

    docs = {}
    for nom, cle in (("persons.json", "persons"), ("events.json", "events"),
                     ("sources.json", "sources")):
        p = os.path.join(DATA, nom)
        d = json.load(io.open(p, encoding="utf-8"))
        docs[nom] = (p, d)
        for x in d[cle]:
            for m in (x.get("media") or []):
                traiter(x["id"], m)
            if x.get("source_file"):
                traiter(x["id"], x)

    for qui, avant, apres in repares:
        print("  OK   %-30s %s" % (qui, apres.split("/")[-1]))
        print("       %s" % avant)
        print("    -> %s" % apres)
    for qui, sf, cands in ambigus:
        print("  ??   %-30s %s : %d candidats, ON NE TRANCHE PAS"
              % (qui, os.path.basename(sf), len(cands)))
        for c in cands:
            print("       - %s" % c)
    for qui, sf in perdus:
        print("  --   %-30s introuvable : %s" % (qui, sf))

    print("\n%d repare(s), %d ambigu(s), %d perdu(s)" % (len(repares), len(ambigus), len(perdus)))
    if WRITE and repares:
        for nom, (p, d) in docs.items():
            json.dump(d, io.open(p, "w", encoding="utf-8", newline="\n"),
                      ensure_ascii=False, indent=2)
        print("Ecrit.")
    elif repares:
        print("(--write pour appliquer)")


if __name__ == "__main__":
    main()
