# -*- coding: utf-8 -*-
"""Resout les coordonnees des LIEUX-DITS de places.json par la Base Adresse Nationale.

    python scripts/lieux_coords.py            # ce qui manque, sans rien ecrire
    python scripts/lieux_coords.py --ecrire   # ecrit les resultats retenus

POURQUOI UN SECOND SCRIPT A COTE DE `lieux_wikipedia.py`. Celui-la interroge Wikipedia et
n'accepte un article que s'il porte des coordonnees ; il sert les COMMUNES, qui ont un
article. UN HAMEAU N'EN A PAS -- « la Judie », « Montbeil », « la Pintiere » sont quelques
maisons chacun, et `lieux_wikipedia.py` ne les interroge meme pas, a dessein. Ils restaient
donc sans `coords`, et la vue Carte ne pourra pas les placer.

LA BAN LES CONNAIT, ELLE. C'est le referentiel de l'Etat, gratuit, sans cle, et elle indexe
les lieux-dits sous le type `locality`.

TROIS REGLES, ET CHACUNE EVITE UN FAUX POSITIF.

1. ON N'ACCEPTE QU'UN `type: locality` ou `street` -- une reponse `municipality` est la
   commune elle-meme, pas le hameau, et l'accepter placerait tous les villages d'une commune
   au meme point.
2. ON VERIFIE LA COMMUNE DE LA REPONSE. La BAN classe par ressemblance et rend toujours
   quelque chose : interrogee pour un hameau qui n'existe pas, elle propose le lieu-dit le
   plus proche phonetiquement, parfois a vingt kilometres. Si le `citycode` ne correspond
   pas, on refuse.
3. LES FUSIONS DE COMMUNES BROUILLENT LE TEST. Benassay, Lavausseau, Montreuil-Bonnin et La
   Chapelle-Montreuil sont depuis 2019 la seule commune de BOIVRE-LA-VALLEE, code 86123 : la
   BAN ne sait plus dire dans laquelle des quatre tombe un hameau. On accepte donc la commune
   nouvelle, et `commune_verifiee` note que le controle a porte sur elle et non sur l'ancienne.

ET LE SCORE NE SUFFIT PAS. Une reponse a 0,9 peut etre un homonyme : c'est la commune qui
tranche, pas la confiance du moteur.

4. ET LA COMMUNE NE SUFFIT PAS NON PLUS -- REGLE AJOUTEE LE 30 AOUT 2026, APRES COUP.
   Le premier jet s'arretait a la regle 3, et il a place « les Meilliers » sur une ALLEE DES
   MIMOSAS et « la Ville-Nouvelle » sur une IMPASSE DE LA VIEILLE CHAPELLE. Les deux etaient
   bien a Boivre-la-Vallee : le controle de commune passait, et il passait d'autant mieux que
   la fusion de 2019 met quatre communes sous un seul code. La BAN, interrogee pour un lieu
   qui n'existe pas, rend le plus proche phonetiquement -- et « Meilliers » attrape
   « Mimosas ».
   ON COMPARE DONC AUSSI LES NOMS, apres avoir ote les accents et les mots de voirie (rue,
   route, chemin, impasse, allee, lieu-dit, place) qui ne sont pas dans le nom du hameau.
   Seuil a 0,72, ou inclusion d'un nom dans l'autre. C'est ce qui laisse passer « la Pinelière »
   et « Montbeil », qui sont exacts, et « le Haut Radouere » pour « le Radoire », qui est la
   graphie moderne du meme lieu -- et ce qui arrete les mimosas.
   LES REFUS SE LISENT : ils disent ce que la BAN proposait, pour qu'on juge a l'oeil.
"""
import difflib
import io
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:                                    # meme lecon que lieux_wikipedia.py
    CTX = ssl.create_default_context()

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER = os.path.join(RACINE, "data", "places.json")
API = "https://api-adresse.data.gouv.fr/search/"

# Les communes nouvelles, et ce qu'elles ont absorbe. Sans cette table, le controle de la
# regle 3 refuserait tous les hameaux de Benassay, dont le code INSEE n'existe plus.
FUSIONS = {
    "Boivre-la-Vallée": {"Benassay", "Lavausseau", "Montreuil-Bonnin", "La Chapelle-Montreuil"},
}


def interroge(nom, commune):
    q = urllib.parse.urlencode({"q": f"{nom} {commune}", "limit": 5})
    req = urllib.request.Request(API + "?" + q, headers={"User-Agent": "genealog.ia"})
    with urllib.request.urlopen(req, context=CTX, timeout=20) as r:
        return json.load(r)


VOIRIE = ("lieu dit", "lieu-dit", "rue de la", "rue des", "rue du", "rue", "route de la",
          "route des", "route du", "route", "chemin de la", "chemin des", "chemin du",
          "chemin", "impasse de la", "impasse des", "impasse du", "impasse", "allee de la",
          "allee des", "allee du", "allee", "place de la", "place", "passage", "le", "la",
          "les", "l ", "du", "de", "des")


def sans_code(label):
    """Ote « 86470 Boivre-la-Vallée » de la fin d'un libelle BAN.

    LE DECOUPAGE NAIF SUR « 8 » NE MARCHAIT QUE POUR LA VIENNE : « Le Pot 79340 Vasles »
    en sortait entier, et le lieu se retrouvait marque approximatif alors que le nom est
    exact. Un code postal, c'est cinq chiffres, dans n'importe quel departement.
    """
    return re.sub(r"\s*\d{5}.*$", "", label or "").strip()


def nu(s):
    """Nom reduit a ce qui le distingue : sans accents, sans voirie, sans article."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    change = True
    while change:                                  # « rue de la Sablière » -> « sabliere »
        change = False
        for mot in VOIRIE:
            if s.startswith(mot + " "):
                s, change = s[len(mot) + 1:].strip(), True
                break
    return s


def meme_nom(demande, propose):
    a, b = nu(demande), nu(sans_code(propose))
    if not a or not b:
        return False
    return a in b or b in a or difflib.SequenceMatcher(None, a, b).ratio() >= 0.72


def accepte(rep, commune, nom):
    """Retient la premiere reponse qui est un lieu-dit, dans la bonne commune, ET du bon nom."""
    for f in rep.get("features", []):
        p = f["properties"]
        if p.get("type") not in ("locality", "street"):
            continue
        ville = p.get("city", "")
        ok = ville.lower() == commune.lower() or commune in FUSIONS.get(ville, set())
        if not ok:
            continue
        if not meme_nom(nom, p.get("name") or p.get("label") or ""):
            continue
        lon, lat = f["geometry"]["coordinates"]
        return {"coords": [round(lat, 5), round(lon, 5)],
                "ban": p.get("label"), "ban_commune": ville, "ban_type": p.get("type")}
    return None


def main():
    ecrire = "--ecrire" in sys.argv
    d = json.loads(io.open(FICHIER, encoding="utf-8").read())
    resolus = refuses = ignores = 0
    for lieu in d["places"]:
        commune = lieu.get("commune")
        if not commune or lieu.get("coords"):
            ignores += 1
            continue
        try:
            rep = interroge(lieu["name"], commune)
        except Exception as ex:                        # une erreur reseau n'est pas un negatif
            print(f"  [reporte] {lieu['id']:<32} {ex}")
            continue
        trouve = accepte(rep, commune, lieu["name"])
        if trouve:
            resolus += 1
            print(f"  [ok] {lieu['id']:<32} {trouve['coords']}  « {trouve['ban']} »")
            if ecrire:
                lieu["coords"] = trouve["coords"]
                lieu["coords_source"] = ("Base Adresse Nationale, "
                                         f"{trouve['ban_type']} « {trouve['ban']} »")
                # LE NOM RETENU N'EST PAS TOUJOURS LE NOTRE, et il faut que ca se voie sans
                # relire le script : « la Judie » est rendue par « La Juzie », « le Radoire »
                # par « La Radouere ». Ce sont vraisemblablement les graphies modernes des
                # memes lieux, mais vraisemblablement n'est pas etabli -- le drapeau dit ou
                # regarder si un point de la carte tombe a cote.
                if nu(lieu["name"]) != nu(sans_code(trouve["ban"] or "")):
                    lieu["coords_approx"] = True
                else:
                    lieu.pop("coords_approx", None)
        else:
            refuses += 1
            prop = [f["properties"].get("label") for f in rep.get("features", [])[:2]]
            print(f"  [refuse] {lieu['id']:<30} rien dans {commune} — proposait {prop}")
        time.sleep(0.2)

    print(f"\n{resolus} resolus, {refuses} refuses, {ignores} ignores "
          f"(communes, ou coordonnees deja la)")
    if ecrire and resolus:
        io.open(FICHIER, "w", encoding="utf-8", newline="").write(
            json.dumps(d, ensure_ascii=False, indent=2) + "\n")
        print("places.json ecrit")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
