# -*- coding: utf-8 -*-
"""Resout l'article Wikipedia et les coordonnees des lieux de places.json.

    python scripts/lieux_wikipedia.py            # ce qui manque, sans rien ecrire
    python scripts/lieux_wikipedia.py --ecrire   # ecrit les resultats retenus

LA REGLE, ET ELLE EST DANS CLAUDE.md : un article n'est accepte QUE S'IL PORTE DES
COORDONNEES. Une page d'homonymie n'en a pas, et c'est ce test qui a evite d'envoyer
« Marennes » vers une page de desambiguisation. Les coordonnees viennent dans la meme
reponse : elles vont dans `coords`, et ce sont elles qui rendront la vue Carte possible.
LE CHAMP NE SE FABRIQUE JAMAIS A PARTIR DU NOM.

⚠️ MAIS LE TEST DES COORDONNEES NE PROUVE QUE LA MOITIE DE CE QU'ON CROIT, ET IL FAUT LE
SAVOIR : il dit qu'une page n'est PAS une homonymie. Il ne dit pas que c'est la BONNE
commune. Le 18 septembre 2026, un lieu « Rachecourt » cree pour la Haute-Marne -- ou le
registre ecrit le nom nu et ou le departement en compte DEUX, Rachecourt-sur-Marne et
Rachecourt-Suzemont -- a resolu vers l'article « Rachecourt » tout court, coordonnees
comprises : 49,59 / 5,73, c'est-a-dire la commune BELGE de la province de Luxembourg. Les
deux Rachecourt francaises sont a 48,5.

    RELIRE LES COORDONNEES CONTRE LE DEPARTEMENT DU LIEU avant d'accepter un titre nu.
    Un ecart de plus d'un degre entre l'article et la region attendue est un mauvais lien,
    et PAS DE LIEN VAUT MIEUX QU'UN MAUVAIS LIEN.

Le cas symetrique existe aussi, et il se resout : une commune DISPARUE peut garder son
article. « Saucourt », reunie a Doulaincourt en 1972, a toujours sa page
« Saucourt-sur-Rognon » avec ses coordonnees -- c'est celle-la qu'il faut, pas celle de la
commune qui lui a succede.

UN LIEU-DIT N'A PAS D'ARTICLE, ET CE N'EST PAS UN ECHEC. « Le Radoire », « La Grollerie »,
« Le Jardinet » : quelques maisons chacun, aucun n'aura jamais de page. Ils ne sont donc
meme pas interroges -- c'est leur COMMUNE DE RATTACHEMENT qui porte le lien, et
`build_poc.py` le leur prete a l'affichage.

TROIS CHOSES PAYEES LE 26 AOUT 2026 AU SOIR, ET ELLES SONT LA RAISON D'ETRE DU FICHIER.

1. LE CERTIFICAT. `urllib` echoue ici sur CERTIFICATE_VERIFY_FAILED avec le magasin du
   systeme (racine expiree sur cette machine), et la premiere conclusion a ete « l'API est
   injoignable » -- ce qui etait faux. `certifi` regle le probleme et est deja installe.
   NE PAS desactiver la verification : on lit une reponse dont on tire des donnees qu'on
   ecrit dans le corpus.

2. LE 429. Une requete par lieu, meme espacee, fait rendre a Wikipedia « You are making
   too many requests ». **L'API accepte JUSQU'A 50 TITRES PAR REQUETE**, separes par des
   barres verticales : trente lieux tiennent en une requete, et le probleme disparait au
   lieu d'etre ralenti. C'est ce que fait `lot()`.

3. ET SURTOUT : UNE ERREUR RESEAU N'EST PAS UN NEGATIF. La premiere version notait
   « aucun article » sur un 429 et l'ecrivait dans le lieu -- fabriquant exactement le
   faux negatif que ce corpus se refuse partout ailleurs. Un lieu dont la requete a echoue
   n'est PAS marque : il sera repris au prochain passage.
"""
import io
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_io as io_

# GENEALOGIA_DATA, COMME LES AUTRES SCRIPTS. Il manquait ici, et un second corpus se
# retrouvait donc a enrichir les lieux du premier. `corpus_io` porte deja la variable :
# on la lui reprend plutot que de la relire, pour qu'il n'y ait qu'un seul endroit ou
# elle se decide.
DATA = io_.DATA
API = "https://fr.wikipedia.org/w/api.php?"
UA = {"User-Agent": "genealogia/1.0 (corpus familial prive; +https://github.com/pascalpediroda-maker/genealog-ia)"}
PAR_LOT = 30

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:                                     # magasin du systeme
    CTX = None


def lot(titres):
    """{titre demande: (url, [lat, lon])} pour ceux qui portent des coordonnees.

    `normalized` et `redirects` sont relus : l'API rend le titre CANONIQUE dans
    `pages`, pas celui qu'on a demande. Sans ce remappage, « Meigne-le-Vicomte »
    ne se retrouve pas dans la reponse et le lieu passe pour introuvable.
    """
    params = {"action": "query", "prop": "coordinates|info", "inprop": "url",
              "titles": "|".join(titres), "format": "json", "redirects": 1}
    vers, coords, urls = {}, {}, {}                     # canonique -> [lat, lon] / url
    suite = {}
    # `prop=coordinates` EST PAGINE, ET C'EST LE PIEGE DU LOT. Sur trente titres,
    # l'API rend les coordonnees des premiers seulement et pose un `continue`
    # (`cocontinue`). Sans le suivre, Courcelles-de-Touraine, Saint-Pal et Tavant
    # passaient pour « sans article » alors qu'ils ont chacun le leur -- un faux
    # negatif fabrique par la pagination, pas par Wikipedia.
    #
    # ET IL FAUT COLLECTER LES DEUX CHAMPS SEPAREMENT. Sur la requete de
    # continuation, les pages reviennent avec leurs `coordinates` MAIS SANS
    # `fullurl` : `info` a deja ete servi au premier tour, l'API ne le repete pas.
    # Exiger les deux dans la meme reponse rejetait tout ce qui arrivait en second.
    while True:
        u = API + urllib.parse.urlencode(dict(params, **suite))
        for essai in range(5):
            try:
                r = json.load(urllib.request.urlopen(
                    urllib.request.Request(u, headers=UA), timeout=45, context=CTX))
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or essai == 4:
                    raise
                time.sleep(5 * (essai + 1))
        q = r["query"]
        for k in ("normalized", "redirects"):
            for m in q.get(k, []):
                vers[m["from"]] = m["to"]
        for p in q["pages"].values():
            c = (p.get("coordinates") or [None])[0]
            if c:
                coords[p["title"]] = [round(c["lat"], 5), round(c["lon"], 5)]
            if p.get("fullurl"):
                urls[p["title"]] = p["fullurl"]
        if "continue" not in r:
            break
        suite = r["continue"]
        time.sleep(0.4)
    def canon(t):
        vu = set()
        while t in vers and t not in vu:
            vu.add(t)
            t = vers[t]
        return t
    out = {}
    for t in titres:
        k = canon(t)
        out[t] = (urls[k], coords[k]) if k in coords and k in urls else None
    return out


def cle(s):
    """Forme comparable d'un nom de lieu : sans accents, sans ponctuation, en minuscules.

    Le qualificatif entre parentheses des titres homonymes -- « Gestel (Morbihan) » --
    est ote : c'est une desambiguisation de Wikipedia, pas une difference de nom.
    """
    import re
    import unicodedata
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def cherche(p):
    """Repli quand aucun titre direct n'existe -- ET IL NE SERT QU'A FRANCHIR UNE GRAPHIE.

    C'EST LA LECON DES PATRONYMES APPLIQUEE A L'ENCYCLOPEDIE. Le corpus ecrit
    « Saint-Pal-de-Chalençon », avec la cedille que portent les registres ; Wikipedia
    titre son article « Saint-Pal-de-Chalencon », sans. Une interrogation par titre exact
    rendait donc `missing` sur une commune qui a bel et bien sa page -- exactement comme
    chercher PAIRÉ quand l'acte ecrit PAYRÉ.

    MAIS LE MOTEUR DE RECHERCHE REND TOUJOURS QUELQUE CHOSE, ET C'EST LE PIEGE. Une
    premiere version acceptait le premier resultat portant des coordonnees : elle a
    propose « La Chainade → Marennes », « Le Lioran → Cantal (departement) », « Azzano →
    Castel d'Azzano », qui est a Verone. Le test des coordonnees ne protege que des pages
    d'homonymie ; il ne dit rien de la RESSEMBLANCE. Donc : ON N'ACCEPTE QU'UN TITRE QUI
    EST LE MEME NOM A LA GRAPHIE PRES. Pas de lien vaut mieux qu'un mauvais lien.
    """
    u = API + urllib.parse.urlencode({
        "action": "query", "list": "search", "srlimit": 8, "format": "json",
        # POUR CHERCHER, LE PLUS PRECIS GAGNE : « Valvasone Pordenone » cadre mieux que
        # « Valvasone Italie », et le test des coordonnees ecarte de toute facon un mauvais
        # article. C'est l'inverse de l'AFFICHAGE, ou le pays l'emporte pour l'etranger.
        "srsearch": "%s %s" % (p["name"],
                               p.get("admin2_name") or p.get("country") or "")})
    r = json.load(urllib.request.urlopen(
        urllib.request.Request(u, headers=UA), timeout=45, context=CTX))
    voulu = cle(p["name"])
    cands = [s["title"] for s in r["query"]["search"] if cle(s["title"]) == voulu]
    if not cands:
        return None
    time.sleep(0.4)
    for t in cands[:2]:
        hit = lot([t])[t]
        if hit:
            return hit
    return None


def titres(p):
    """Les formes a essayer, de la plus sure a la plus large.

    « Madic » seul est ambigu dans un pays qui compte des homonymes partout ; la forme
    « Nom (departement) » est celle que Wikipedia donne aux communes homonymes, et elle
    tombe juste quand elle existe. On essaie la desambiguisee d'abord.
    """
    n = p["name"]
    out = []
    # « Marennes (Charente-Maritime) » est la convention de desambiguisation de la Wikipedia
    # FRANCAISE, et elle ne vaut que pour les communes francaises : « Valvasone (Pordenone) »
    # n'est le titre d'aucun article chez elle. On ne propose donc ce gabarit que quand le
    # lieu est en France -- ailleurs, le nom nu, et le test des coordonnees tranche.
    pays = p.get("country")
    if p.get("admin2_name") and (not pays or pays == "France"):
        out.append("%s (%s)" % (n, p["admin2_name"]))
    out.append(n)
    return out


def main(ecrire=False):
    chemin = os.path.join(DATA, "places.json")
    d = json.load(io.open(chemin, encoding="utf-8"))     # recharge juste avant l'ecriture
    a_faire, ignores = [], 0
    for p in d["places"]:
        if p.get("wikipedia") and p.get("coords"):
            continue
        if p.get("commune") or p.get("wikipedia_cherche"):
            ignores += 1                                 # lieu-dit, ou deja cherche et refuse
            continue
        a_faire.append(p)

    demandes = []
    for p in a_faire:
        demandes += titres(p)
    demandes = list(dict.fromkeys(demandes))
    reponses, echecs = {}, 0
    for i in range(0, len(demandes), PAR_LOT):
        bloc = demandes[i:i + PAR_LOT]
        try:
            reponses.update(lot(bloc))
        except Exception as e:
            echecs += len(bloc)
            print("  [!] lot %d-%d : %s -- AUCUN NEGATIF NOTE, a reprendre"
                  % (i, i + len(bloc), type(e).__name__), flush=True)
        time.sleep(1.0)

    trouves, vides, reportes = [], [], []
    for p in a_faire:
        rep = [reponses.get(t) for t in titres(p)]
        hit = next((r for r in rep if r), None)
        if hit:
            p["wikipedia"], p["coords"] = hit
            trouves.append(p["id"])
            print("  [ok] %-28s %s" % (p["id"], hit[0]), flush=True)
        elif any(t not in reponses for t in titres(p)):
            reportes.append(p["id"])                     # la requete n'a pas abouti
            continue
        else:
            try:
                hit = cherche(p)                         # repli : le moteur de recherche
            except Exception as e:
                print("  [!] %-28s recherche : %s" % (p["id"], type(e).__name__), flush=True)
                reportes.append(p["id"])
                continue
            if hit:
                p["wikipedia"], p["coords"] = hit
                trouves.append(p["id"])
                print("  [ok] %-28s %s   (par recherche)" % (p["id"], hit[0]), flush=True)
                continue
            p["wikipedia_cherche"] = "2026-08-26 : aucun article portant des coordonnees, titre direct ni recherche"
            vides.append(p["id"])
            print("  [--] %-28s aucun article a coordonnees" % p["id"], flush=True)
        time.sleep(0.3)

    print("\n%d resolus, %d sans article, %d reportes (erreur reseau), %d ignores"
          % (len(trouves), len(vides), len(reportes), ignores))
    if reportes:
        print("   a reprendre : " + ", ".join(reportes))
    if ecrire and (trouves or vides):
        # PAR `corpus_io.sauve`, ET NON PAR UN `io.open(chemin, "w")`. C'est exactement le
        # geste qui a vide persons.json le 7 septembre 2026 : le mode 'w' tronque le fichier
        # A L'OUVERTURE, avant que la moindre ligne suivante ne s'execute. `sauve` ecrit dans
        # un temporaire voisin et bascule par `os.replace`.
        io_.sauve("places.json", d)
        print("places.json ecrit")
    elif not ecrire:
        print("(rien ecrit -- relancer avec --ecrire)")


if __name__ == "__main__":
    main("--ecrire" in sys.argv)
