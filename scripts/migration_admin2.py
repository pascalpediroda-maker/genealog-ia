# -*- coding: utf-8 -*-
"""Renomme `dept` / `dept_name` en `admin2` / `admin2_name` dans un corpus.

    python scripts/migration_admin2.py                        # rapport, n'ecrit rien
    python scripts/migration_admin2.py --ecrire               # applique au corpus du depot
    GENEALOGIA_DATA="<archives>/…/DUPONT - Prenom/data" python scripts/migration_admin2.py --ecrire

UN CORPUS PAR APPEL, ET C'EST LA PORTE DOCUMENTEE : `corpus_io` resout `GENEALOGIA_DATA` a
l'import, donc un seul processus ne peut pas ecrire deux arbres. LES TROIS DOIVENT PASSER,
parce que les scripts sont partages -- laisser un corpus en arriere le rendrait muet sur ses
lieux du jour au lendemain.

POURQUOI. Un lieu s'affiche avec LE NIVEAU QUI LE SITUE : le departement en France, la
province en Italie, la wilaya en Algerie. C'est la meme idee partout, et le corpus la
portait sous un nom francais. Le 25 septembre 2026 la branche italienne a eu besoin de ses
provinces, et plutot que de forcer « Pordenone » dans un champ appele `dept_name` -- ce qui
aurait fait lire « Valvasone (Pordenone) » a un lecteur francais --, une PAIRE CONCURRENTE
a ete creee. Le généalogiste, en la voyant : *« les departements c'est tres francais, pourquoi ne pas
faire evoluer ? »*. Deux champs pour une seule idee est le probleme, pas la solution.

`region` n'etait pas la reponse : il existe deja, il est ecrit dans plus de cent lieux, il
n'est rendu par AUCUNE page, et c'est le niveau 1 -- « Prodolone (Frioul-Venetie Julienne) »
la ou l'utile est « Prodolone (Pordenone) ».

CE QUI CHANGE AUSSI, ET C'EST LE VRAI TRAVAIL. Jusqu'ici `lieu()` affichait le departement
AVANT le pays, et ca marchait PAR ACCIDENT : un lieu francais n'a pas de `country`, un lieu
etranger n'avait pas de `dept_name`. Le champ unifie casse cet accident -- Valvasone porte
desormais une subdivision ET un pays. La regle redevient donc explicite dans `lieu()`, et
c'est celle de CLAUDE.md : **subdivision pour un lieu francais, pays pour un lieu etranger.**

LE SEUL CONTROLE QUI COMPTE : LA PAGE DOIT RENDRE EXACTEMENT LA MEME CHOSE. Ce script
compare chaque libelle avant et apres, et REFUSE D'ECRIRE si un seul bouge.

⚠️ Le `dept` de `scripts/archives/` n'a RIEN A VOIR -- c'est le numero de departement d'un
portail d'archives. Ce script ne touche que `places.json`.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENOMME = {"dept": "admin2", "dept_name": "admin2_name",
           "dept_disputed": "admin2_disputed",
           "dept_name_disputed": "admin2_name_disputed"}


def apres_migration(p):
    """`lieu()` tel qu'il sera. Reimplemente ici pour comparer sans importer la page --
    un `import build_poc` reconstruit les 16 Mo de `index.html`, ce qui est arrive le
    18 septembre 2026 et de nouveau aujourd'hui."""
    n = p["name"]
    bouts = []
    if p.get("commune") and p["commune"] not in n:
        bouts.append(p["commune"])
    pays = p.get("country")
    if pays and pays != "France":
        bouts.append(pays)
    elif p.get("admin2_name"):
        bouts.append(p["admin2_name"])
    elif pays:
        bouts.append(pays)
    bouts = [b for b in bouts if b != n]
    if not bouts:
        return n
    ctx = ", ".join(bouts)
    return f"{n}, {ctx}" if "(" in n else f"{n} ({ctx})"


def migre(place):
    """Renomme EN PLACE dans l'ordre des cles, pour que le diff JSON reste lisible."""
    return {RENOMME.get(k, k): v for k, v in place.items()}


def main():
    ecrire = "--ecrire" in sys.argv
    print(f">> corpus : {corpus_io.DATA}")

    src = io.open(os.path.join(ROOT, "scripts", "build_poc.py"), encoding="utf-8").read()
    m = re.search(r"\ndef lieu\(.*?\n(?=def )", src, re.S)
    ancien = {}
    exec("import json\n" + m.group(0).replace("places.get(pid)", "PL.get(pid)"), ancien)

    d = corpus_io.charge("places.json")
    ancien["PL"] = {p["id"]: p for p in d["places"]}
    avant = {p["id"]: ancien["lieu"](p["id"]) for p in d["places"]}

    migres = [migre(p) for p in d["places"]]
    apres = {p["id"]: apres_migration(p) for p in migres}
    porteurs = sum(1 for p in migres if p.get("admin2_name") or p.get("admin2"))

    ecarts = [(i, avant[i], apres[i]) for i in avant if avant[i] != apres[i]]
    print(f"   {len(migres)} lieux · {porteurs} portent une subdivision · "
          f"{len(ecarts)} libelle(s) changent")

    if ecarts:
        print("\n⛔ UN RENOMMAGE NE DOIT RIEN CHANGER A L'ECRAN. Rien n'est ecrit.")
        for i, a, b in ecarts[:40]:
            print(f"   {i:<28} {a!r}\n   {'':<28} -> {b!r}")
        return 1

    print("   OK -- tous les libelles sont identiques avant et apres")
    if not ecrire:
        print("   (rien n'a ete ecrit -- relancer avec --ecrire)")
        return 0

    # RECHARGER JUSTE AVANT D'ECRIRE et rejouer le renommage sur la version fraiche :
    # plusieurs sessions travaillent en parallele sur les memes JSON.
    frais = corpus_io.charge("places.json")
    frais["places"] = [migre(p) for p in frais["places"]]
    corpus_io.sauve("places.json", frais)
    print(f"   ecrit : {len(frais['places'])} lieux")
    return 0


if __name__ == "__main__":
    sys.exit(main())
