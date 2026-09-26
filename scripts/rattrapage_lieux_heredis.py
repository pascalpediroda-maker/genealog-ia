# -*- coding: utf-8 -*-
"""Rattrape la GEOGRAPHIE des lieux, que `import_heredis.py` avait laissee tomber.

QUATRIEME PERTE DE CET IMPORT, TROUVEE LE 25 SEPTEMBRE 2026 -- les trois premieres sont
dans `rattrapage_heredis.py`. La table `Lieux` de la base d'Alfiero porte CINQ colonnes
que l'import n'a pas lues : `Departement`, `Region`, `Pays`, `Latitude`, `Longitude`.

ET IL A FAIT PIRE QUE DE LES IGNORER : il a ecrit `country: "France"` sur TOUT ce qu'il
creait. Quatre lieux du corpus se disaient donc en France sans y etre -- AZZANO DECIMO,
GONNOSFANADIGA, FRUINTZ et, dans l'autre sens, SALERNE, que la resolution Wikipedia avait
ensuite envoye a Salerno en Campanie alors qu'Alfiero avait ecrit « VAR ».

L'ERREUR ETAIT INVISIBLE, ET C'EST CE QUI LA REND INTERESSANTE. `lieu()` n'ecrit pas
« France » a un lecteur francais : un lieu italien marque France s'affichait donc NU --
« Fruintz », rien d'autre -- exactement ce que la regle « un lieu ne s'affiche jamais nu »
interdit. Aucun controle ne regardait la VALEUR d'un champ correctement nomme. C'est
`build.py --pays` qui l'attrape desormais, en opposant `country` aux coordonnees du meme
enregistrement.

    python scripts/rattrapage_lieux_heredis.py            # rapport, n'ecrit rien
    python scripts/rattrapage_lieux_heredis.py --ecrire   # applique

CE SCRIPT NE NORMALISE RIEN TOUT SEUL. Alfiero ecrit « pordenone », « PORDENONE », « PN »
et « friul », « FRIUL », « Frioul » pour les memes choses, et il range la PROVINCE italienne
dans la colonne `Departement`. Une normalisation par regle -- capitaliser, deviser -- aurait
ecrit « Sardaigne » comme une province alors que c'est une region, et fabrique un code pour
« Fruintz » qu'aucune source ne donne. La table ci-dessous est donc ecrite A LA MAIN, et
TOUT CE QUI N'Y EST PAS EST REFUSE : le script le signale au lieu de deviner.

CE QU'IL N'ECRIT PAS, ET POURQUOI. Une base Heredis est une COMPILATION, pas un acte : elle
donne une piste solide, jamais une preuve. Ces valeurs situent un lieu sur une carte et le
nomment pour un lecteur -- elles ne fondent aucune filiation. C'est la raison pour laquelle
on les accepte ici alors qu'on refuse d'y creer une personne.
"""
import io
import json
import os
import sqlite3
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
import corpus_io

HRD = os.path.join(config.archives(), "le généalogiste.hmw", "le généalogiste.heredis")

# --- ce qu'Alfiero ecrit -> ce que le corpus ecrit ---------------------------
# A GAUCHE LA CHAINE BRUTE, MISE EN MINUSCULES ET SANS ACCENTS. A droite, soit une
# subdivision de niveau 2 -- province, departement -- soit une region, soit rien.
# Un lieu dont la valeur n'est pas ici ressort dans « non normalise » et n'est pas ecrit.

PROVINCES = {          # brut -> (admin2_name, admin2, region)
    "pordenone": ("Pordenone", "PN", "Frioul-Vénétie Julienne"),
    "pn":        ("Pordenone", "PN", "Frioul-Vénétie Julienne"),
    "udine":     ("Udine", "UD", "Frioul-Vénétie Julienne"),
    "ud":        ("Udine", "UD", "Frioul-Vénétie Julienne"),
    "asti":      ("Asti", "AT", "Piémont"),
}

# DES REGIONS QU'ALFIERO RANGE DANS LA COLONNE DEPARTEMENT. « Sardaigne » n'est pas une
# province : l'ecrire en `admin2_name` ferait lire « Gonnosfanadiga (Sardaigne) » a un
# Italien la ou il attend « (Sud Sardegna) ». La region est vraie, la province est
# inconnue -- on ecrit la premiere et on laisse la seconde vide.
REGIONS_MAL_RANGEES = {
    "sardaigne": "Sardaigne",
}

# LES DEPARTEMENTS FRANCAIS, ecrits au long par Alfiero. Le code vient de l'INSEE, pas
# d'une deduction : ces quatre-la ont ete confirmes par la Base Adresse Nationale, qui
# rend le meme point que les coordonnees deja presentes dans le corpus.
DEPARTEMENTS = {       # brut -> (admin2_name, admin2)
    "val d'oise": ("Val-d'Oise", "95"),
    "isere":      ("Isère", "38"),
    "var":        ("Var", "83"),
    "haut-rhin":  ("Haut-Rhin", "68"),
}

REGIONS = {            # brut de la colonne Region -> region du corpus
    "friul":      "Frioul-Vénétie Julienne",
    "frioul":     "Frioul-Vénétie Julienne",
    "piemont":    "Piémont",
    "lazio":      "Latium",
    "lombardie":  "Lombardie",
    "alsace":     "Grand Est",
}

PAYS = {               # brut de la colonne Pays -> country du corpus
    "italie":    "Italie",
    "france":    "France",
    "algerie":   "Algérie",
    "argentine": "Argentine",
    "albanie":   "Albanie",
}

# --- les deux que la base ne rattrape pas ------------------------------------
# LA TABLE `Lieux` NE DIT RIEN SUR EUX, ET POURTANT LEUR ETAT EST FAUX. Ils sont traites
# nommement, avec leur raison, plutot que par une regle qui les depasserait.
#
# AZZANO DECIMO : sa ligne Heredis ne porte que des coordonnees -- 45,88 / 12,71, c'est-a-dire
# le Frioul, a douze kilometres de Valvasone. La Base Adresse Nationale ne connait AUCUNE
# commune francaise de ce nom, et la base porte une ligne voisine « Azzano » donnee en
# « friul / italie ». Le pays est donc etabli ; LA PROVINCE NE L'EST PAS, et on ne l'ecrit
# pas : personne n'a produit de source qui la nomme.
#
# SALERNE : le cas inverse, et le plus instructif. Alfiero ecrit « VAR » -- c'est la commune
# francaise. Mais `lieux_wikipedia.py`, interroge sur le nom nu, a rendu l'article de SALERNE
# EN CAMPANIE et ecrit ses coordonnees, 40,68 / 14,77. C'est le piege que son propre
# docstring decrit a propos de Rachecourt : le test des coordonnees prouve qu'une page n'est
# pas une homonymie, jamais que c'est la BONNE commune. Le lien et les coordonnees partent ;
# PAS DE LIEN VAUT MIEUX QU'UN MAUVAIS LIEN, et un point faux sur la carte est pire qu'un
# point manquant.
CAS_PARTICULIERS = {
    "azzanodecimo": {
        "pose":   {"country": "Italie", "region": "Frioul-Vénétie Julienne"},
        "retire": [],
        "note": "Importé de la base Hérédis d'Alfiero. Le pays est établi par les "
                "coordonnées (45,88 / 12,71, Frioul) et par la ligne voisine « Azzano », "
                "donnée « friul / italie » ; l'import avait écrit « France » sur tout ce "
                "qu'il créait. LA PROVINCE RESTE À ÉTABLIR : aucune source du corpus ne "
                "la nomme.",
    },
    "salerne": {
        "pose":   {"country": "France", "admin2_name": "Var", "admin2": "83"},
        "retire": ["wikipedia", "coords"],
        "note": "Importé de la base Hérédis d'Alfiero, qui écrit « VAR » : c'est la "
                "commune française, et c'est là que meurt Lidio MIGOT en 2003. "
                "L'article et les coordonnées qui figuraient ici renvoyaient à SALERNE "
                "EN CAMPANIE — résolus sur un nom nu, ils ont été retirés. Le nom de la "
                "commune du Var s'écrit SALERNES ; reste à vérifier laquelle des deux "
                "graphies est la bonne sur l'acte.",
    },
    # ET UN PAYS RANGE PARMI LES COMMUNES. « Checoslovaquie » est l'endroit ou meurent
    # Antonio et Filippo MIGOT, sans date : ce n'est pas un lieu, c'est tout ce qu'on
    # sait du lieu. L'import lui a mis « France », ce qui est faux deux fois. On ecrit
    # le pays -- la seule chose vraie -- et la commune reste a trouver.
    "checoslovaquie": {
        "pose":   {"country": "Tchécoslovaquie"},
        "retire": [],
        "note": "Importé de la base Hérédis d'Alfiero, où le nom du PAYS tient lieu de "
                "commune : c'est là que meurent Antonio et Filippo MIGOT, sans date. "
                "L'import avait écrit « France ». La commune reste à établir, et l'État "
                "lui-même a cessé d'exister le 31 décembre 1992 — le lieu est aujourd'hui "
                "en Tchéquie ou en Slovaquie.",
    },
    # DEUX QUE LA BASE LAISSE NUS ET QUE LA BAN TRANCHE. Alfiero n'a rempli que la
    # colonne `Region`, avec « PARIS » pour l'un et rien pour l'autre. La Base Adresse
    # Nationale rend une commune dont les coordonnees tombent a moins de deux centiemes
    # de degre de celles que le corpus porte deja : ce n'est pas une ressemblance de nom,
    # c'est le meme point.
    "creteil": {
        "pose":   {"admin2_name": "Val-de-Marne", "admin2": "94", "region": "Île-de-France"},
        "retire": [],
        "note": "Importé de la base Hérédis d'Alfiero, qui ne dit que « PARIS ». "
                "Département établi par la Base Adresse Nationale, code INSEE 94028, "
                "dont le point tombe à un centième de degré des coordonnées du corpus.",
    },
    "reims": {
        "pose":   {"admin2_name": "Marne", "admin2": "51", "region": "Grand Est"},
        "retire": [],
        "note": "Importé de la base Hérédis d'Alfiero, qui ne dit que le pays. "
                "Département établi par la Base Adresse Nationale, code INSEE 51454, "
                "dont le point tombe à deux centièmes de degré des coordonnées du corpus.",
    },
}


def nrm(s):
    s = unicodedata.normalize("NFKD", (s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def cle(s):
    return "".join(c for c in nrm(s) if c.isalnum())


def main():
    ecrire = "--ecrire" in sys.argv

    if not os.path.exists(HRD):
        print(f"Base introuvable : {HRD}\nLe NAS doit etre monte.")
        return 1

    cx = sqlite3.connect(f"file:{HRD}?mode=ro", uri=True)
    heredis = {}
    for v, dep, reg, pays, lat, lon in cx.execute(
        "SELECT Ville, Departement, Region, Pays, Latitude, Longitude FROM Lieux"
    ):
        if cle(v):
            heredis.setdefault(cle(v), []).append((v, dep, reg, pays, lat, lon))

    d = corpus_io.charge("places.json")
    touches, refuses, conflits = [], [], []

    for p in d["places"]:
        cas = CAS_PARTICULIERS.get(p["id"])
        if cas:
            ajouts = []
            for k, v in cas["pose"].items():
                if p.get(k) != v:
                    if p.get(k):
                        conflits.append((p["id"], k, p[k], v))
                    p[k] = v
                    ajouts.append(f"{k}={v}")
            for k in cas["retire"]:
                if k in p:
                    conflits.append((p["id"], k, p[k], None))
                    del p[k]
                    ajouts.append(f"-{k}")
            if ajouts:
                p["note"] = cas["note"]
                touches.append((p["id"], p.get("name"), ajouts, None))
            continue

        lignes = heredis.get(cle(p.get("name")))
        if not lignes:
            continue
        # Une ville peut figurer plusieurs fois dans la base : on prend la premiere
        # ligne qui dit quelque chose, les autres sont des doublons vides.
        v, dep, reg, pays, lat, lon = next(
            (l for l in lignes if l[1] or l[2] or l[3]), lignes[0]
        )

        avant = {k: p.get(k) for k in
                 ("country", "region", "admin2", "admin2_name", "admin2", "admin2_name")}
        ajouts = []

        # --- le pays ---------------------------------------------------------
        if pays:
            attendu = PAYS.get(nrm(pays))
            if not attendu:
                refuses.append((p["id"], "pays", pays))
            elif p.get("country") and p["country"] != attendu:
                conflits.append((p["id"], "country", p["country"], attendu))
            elif not p.get("country") and attendu != "France":
                p["country"] = attendu
                ajouts.append(f"country={attendu}")

        # --- la colonne Departement, qui porte trois choses differentes -------
        if dep:
            k = nrm(dep)
            if k in PROVINCES:
                nom, code, region = PROVINCES[k]
                if not p.get("admin2_name"):
                    p["admin2_name"], p["admin2"] = nom, code
                    ajouts.append(f"admin2={nom}")
                if not p.get("region"):
                    p["region"] = region
                    ajouts.append(f"region={region}")
                # Une province italienne implique le pays, meme quand la colonne
                # `Pays` de la base est vide -- c'est le cas de FRUINTZ, que
                # l'import avait marque France.
                if p.get("country") in (None, "France") and region != "Grand Est":
                    if p.get("country") == "France":
                        conflits.append((p["id"], "country", "France", "Italie"))
                    p["country"] = "Italie"
                    ajouts.append("country=Italie")
            elif k in REGIONS_MAL_RANGEES:
                if not p.get("region"):
                    p["region"] = REGIONS_MAL_RANGEES[k]
                    ajouts.append(f"region={p['region']}")
                if p.get("country") == "France":
                    conflits.append((p["id"], "country", "France", "Italie"))
                    p["country"] = "Italie"
                    ajouts.append("country=Italie")
            elif k in DEPARTEMENTS:
                nom, code = DEPARTEMENTS[k]
                if not p.get("admin2_name"):
                    p["admin2_name"], p["admin2"] = nom, code
                    ajouts.append(f"admin2={nom}")
            elif not (p.get("admin2_name") or p.get("admin2_name")):
                # On ne signale un refus que s'il MANQUE vraiment quelque chose : la
                # moitie des communes francaises de la base sont deja renseignees par
                # ailleurs, et les lister noierait le signal.
                refuses.append((p["id"], "departement", dep))

        # --- la region, quand la colonne Departement n'a rien appris ----------
        if reg and not p.get("region"):
            attendu = REGIONS.get(nrm(reg))
            if attendu:
                p["region"] = attendu
                ajouts.append(f"region={attendu}")
            else:
                refuses.append((p["id"], "region", reg))

        if ajouts:
            touches.append((p["id"], p.get("name"), ajouts, avant))

    print(f">> {len(touches)} lieux completes depuis la base d'Alfiero")
    for pid, nom, ajouts, _ in touches:
        print(f"  {pid:<26} {nom:<28} {' · '.join(ajouts)}")

    if conflits:
        print(f"\n>> {len(conflits)} valeurs CORRIGEES -- le corpus disait autre chose")
        for pid, champ, ancien, neuf in conflits:
            print(f"  {pid:<26} {champ} : {ancien!r} -> {neuf!r}")

    if refuses:
        print(f"\n>> {len(refuses)} valeurs NON NORMALISEES, laissees de cote")
        for pid, champ, brut in refuses:
            print(f"  {pid:<26} {champ:<12} {brut!r}")

    if not ecrire:
        print("\n(rien n'a ete ecrit -- relancer avec --ecrire)")
        return 0

    # RECHARGER JUSTE AVANT D'ECRIRE : plusieurs sessions travaillent en parallele, et
    # un script qui reecrit un JSON entier ecrase ce qui est arrive entre-temps. On
    # rejoue donc les ajouts sur la version la plus fraiche, par identifiant, et
    # CHAMP PAR CHAMP -- recopier la fiche entiere emporterait ce qu'un autre y a mis.
    GEO = ("country", "region", "admin2", "admin2_name", "admin2", "admin2_name")
    frais = corpus_io.charge("places.json")
    index = {p["id"]: p for p in frais["places"]}
    n = 0
    for pid, _, _, _ in touches:
        source = next(p for p in d["places"] if p["id"] == pid)
        cible = index.get(pid)
        if cible is None:
            continue
        for k in GEO:
            if source.get(k) is not None:
                cible[k] = source[k]
        cas = CAS_PARTICULIERS.get(pid)
        if cas:
            for k in cas["retire"]:
                cible.pop(k, None)
            cible["note"] = cas["note"]
        n += 1
    corpus_io.sauve("places.json", frais)
    print(f"\n{n} lieux ecrits dans places.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
