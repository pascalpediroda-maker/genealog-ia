# -*- coding: utf-8 -*-
"""LE FICHIER DES PERSONNES DECEDEES DE L'INSEE, EN FICHIERS BRUTS.

POURQUOI CE MODULE EXISTE. La methode qui suit avait ete refaite TROIS FOIS a la main —
Simonne COULBEAU le 18 septembre 2026, puis Pierrette, puis sa mere — et elle n'etait
ecrite nulle part en code : seulement en prose dans la fiche INSEE du carnet. Une recette
qu'on retape est une recette qui derive.

CE QU'IL SAIT FAIRE, ET C'EST TOUT L'INTERET :

    CHERCHER SANS CONNAITRE LE NOM.

L'API de matchID exige un patronyme et refuse `deathDate` par un 422. Or le mur le plus
frequent du metier est une femme connue sous son nom d'EPOUSE, que le fichier n'indexe
jamais — il n'indexe que le nom de NAISSANCE. Son nom est donc la question, pas la cle.

Les fichiers bruts, eux, se lisent EN ENTIER et se filtrent sur n'importe quelle colonne :
une date de deces, une annee de naissance, un departement, un prenom. Le nom devient le
RESULTAT. C'est ainsi que Simonne COULBEAU a ete nommee, a partir de « morte le 10 novembre
2018 du cote de Tours » et de rien d'autre.

    python insee.py liste
    python insee.py tirer 2000
    python insee.py chercher 2000 --sexe F --ne-dept 03,15,43,63 --ne-entre 1895 1917
    python insee.py chercher 2018 --mort-le 20181110 --mort-dept 37
    python insee.py chercher 2000 --prenom PIERRETTE --ne-en 1932

TROIS PIEGES PAYES, tous notes dans la fiche du carnet :

  * PYTHON REFUSE LE CERTIFICAT DE static.data.gouv.fr QUE CURL ACCEPTE. On passe donc par
    curl pour le telechargement, et on VERIFIE LE NOMBRE D'OCTETS RECUS : un curl dans une
    boucle du shell a deja rendu zero octet sans le dire, et le script avait conclu a un
    negatif.
  * LE FICHIER N'EST PAS TRIE PAR NOM, mais par ordre d'acte. Aucune dichotomie possible :
    on lit tout, et c'est rapide — ~500 000 lignes par an, quelques secondes.
  * LE LIEU DE DECES EST SOUVENT LA COMMUNE DE L'HOPITAL. Filtrer par DEPARTEMENT, jamais
    par la seule commune que dit la famille : Simonne est morte a Chambray-les-Tours quand
    la famille disait Tours.
"""
import io
import json
import os
import re
import subprocess
import sys
import urllib.request

CACHE = os.environ.get("INSEE_CACHE") or os.path.join(
    os.environ.get("TEMP", "/tmp"), "insee-deces")
API = "https://www.data.gouv.fr/api/1/datasets/fichier-des-personnes-decedees/"

# Largeurs fixes du fichier. `nom*PRENOMS/` sur 80, sexe 1=H 2=F, dates AAAAMMJJ,
# codes commune INSEE sur 5.
def champs(l):
    return dict(nom=l[0:80].strip(), sexe=l[80:81], naiss=l[81:89],
                cnaiss=l[89:94], vnaiss=l[94:124].strip(), pays=l[124:154].strip(),
                deces=l[154:162], cdeces=l[162:167], acte=l[167:176].strip())


def nom_prenoms(champ_nom):
    """« MARTIN*JEAN PIERRE/ » -> ('MARTIN', 'JEAN PIERRE')."""
    m = re.match(r"^(.*?)\*(.*?)/?$", champ_nom)
    return (m.group(1), m.group(2)) if m else (champ_nom, "")


def ressources():
    """{'2000': url, ...} — les fichiers annuels et mensuels du jeu de donnees.

    PASSE PAR CURL, COMME LE TELECHARGEMENT ET POUR LA MEME RAISON : Python refuse les
    certificats de data.gouv.fr que curl accepte. Le faire en urllib « parce que c'est
    du JSON » fait echouer l'outil avant meme qu'il ait lu une ligne.
    """
    brut = subprocess.run(["curl", "-sS", "-L", API],
                          check=True, capture_output=True).stdout
    d = json.loads(brut)
    out = {}
    for r in d.get("resources", []):
        m = re.match(r"deces-(\d{4}(?:-m\d{2})?)\.txt$", r.get("title", ""))
        if m:
            out[m.group(1)] = r["url"]
    return out


def tirer(annee):
    """Telecharge le fichier d'une annee dans le cache et rend son chemin.

    PASSE PAR CURL, ET COMPTE LES OCTETS. Python refuse le certificat de
    static.data.gouv.fr ; curl l'accepte. Et un telechargement qui rend zero octet sans
    le dire fabrique un negatif parfaitement credible.
    """
    os.makedirs(CACHE, exist_ok=True)
    chemin = os.path.join(CACHE, "deces-%s.txt" % annee)
    if os.path.exists(chemin) and os.path.getsize(chemin) > 1_000_000:
        return chemin
    url = ressources().get(str(annee))
    if not url:
        raise SystemExit("aucun fichier pour %s" % annee)
    subprocess.run(["curl", "-sS", "-L", "-o", chemin, url], check=True)
    n = os.path.getsize(chemin) if os.path.exists(chemin) else 0
    print("%s : %d octets" % (os.path.basename(chemin), n), file=sys.stderr)
    if n < 1_000_000:
        raise SystemExit("telechargement vide ou tronque — ne rien conclure de ce fichier")
    return chemin


def balaye(annee, garde, jeter=False):
    """Rend les enregistrements de l'annee pour lesquels `garde(rec)` est vrai.

    `jeter` SUPPRIME LE FICHIER APRES LECTURE, et c'est ce qui rend le fonds entier
    lisible sur un disque plein : 86 fichiers font 6,27 Go cumules, mais un seul a la
    fois n'en fait que 110 Mo. Le 18 septembre 2026, C: n'avait plus que 4,5 Go libres —
    et le CLAUDE.md du depot garde le souvenir d'une session ou il est tombe a zero.
    """
    chemin = tirer(annee)
    out, lus = [], 0
    with io.open(chemin, encoding="latin-1") as f:
        for l in f:
            if len(l) < 170:
                continue
            lus += 1
            r = champs(l)
            if garde(r):
                r["patronyme"], r["prenoms"] = nom_prenoms(r["nom"])
                r["fichier"] = annee
                out.append(r)
    print("%s : %d lignes lues, %d retenues" % (annee, lus, len(out)), file=sys.stderr)
    if jeter:
        os.remove(chemin)
    return out


def balaye_tout(garde, depuis=1970, jusqu=2099, jeter=True):
    """Le fonds ENTIER, fichier par fichier, sans jamais en garder deux sur le disque."""
    out = []
    for an in sorted(ressources()):
        if not (str(depuis) <= an[:4] <= str(jusqu)):
            continue
        out += balaye(an, garde, jeter=jeter)
    return out


# ------------------------------------------------------------------------------ CLI
def _cli():
    a = sys.argv[1:]
    if not a or a[0] == "liste":
        r = ressources()
        print(" ".join(sorted(r)))
        return
    if a[0] == "tirer":
        print(tirer(a[1]))
        return
    if a[0] != "chercher":
        raise SystemExit(__doc__)

    annee = a[1]
    opt = lambda n: (a[a.index("--" + n) + 1] if "--" + n in a else None)
    sexe = {"H": "1", "F": "2", None: None}.get(opt("sexe"), opt("sexe"))
    ne_dept = (opt("ne-dept") or "").split(",") if opt("ne-dept") else None
    mort_dept = (opt("mort-dept") or "").split(",") if opt("mort-dept") else None
    mort_le = opt("mort-le")
    ne_en = opt("ne-en")
    prenom = (opt("prenom") or "").upper() or None
    i = a.index("--ne-entre") if "--ne-entre" in a else -1
    borne = (a[i + 1], a[i + 2]) if i > 0 else None

    def garde(r):
        if sexe and r["sexe"] != sexe:
            return False
        if mort_le and r["deces"] != mort_le:
            return False
        if ne_en and not r["naiss"].startswith(ne_en):
            return False
        if borne and not (borne[0] <= r["naiss"][:4] <= borne[1]):
            return False
        if ne_dept and not any(r["cnaiss"].startswith(d) for d in ne_dept):
            return False
        if mort_dept and not any(r["cdeces"].startswith(d) for d in mort_dept):
            return False
        if prenom and prenom not in r["nom"].upper():
            return False
        return True

    for r in balaye(annee, garde):
        print("%-26s %-28s %s %-8s %-5s %-24s + %-8s %-5s acte %s" % (
            r["patronyme"][:26], r["prenoms"][:28], r["sexe"], r["naiss"],
            r["cnaiss"], r["vnaiss"][:24], r["deces"], r["cdeces"], r["acte"]))


if __name__ == "__main__":
    _cli()
