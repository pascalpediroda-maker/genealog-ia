# -*- coding: utf-8 -*-
"""Moteur PRISMIA ViSiON — AD47 (Lot-et-Garonne), et tout portail qui tourne dessus.

SEPTIEME MOTEUR DU DOSSIER, ouvert le 4 septembre 2026 pour la famille DUPONT de
Villeneuve-sur-Lot. Il ne demande AUCUN navigateur : trois requetes HTTP ordinaires
suffisent, de la configuration du backend au JPEG.

    instruments(...)  -> les formulaires du portail (etat civil, matricules, notaires...)
    facette(...)      -> les valeurs d'une facette (communes, types d'acte)
    registres(...)    -> les registres d'une commune, avec leur guid et leur nombre de vues
    manifeste(...)    -> le manifeste IIIF d'un registre
    tirer(...)        -> les images sur le disque, v001.jpg, v002.jpg, ...

LA VITRINE N'EST PAS LE MOTEUR, ET C'EST LE PREMIER PIEGE. archivesdepartementales.
lotetgaronne.fr est un TYPO3 qui ne porte pas un seul registre ; le moteur vit sur
lotetgaronne.archives.prismia.fr. Et celui-la est une application React d'UNE SEULE PAGE :
toutes ses routes rendent la meme coquille de 1375 octets, /js/routing comprise. Il n'y a
rien a gratter dans le HTML, et une heure passee a essayer des chemins ne rend rien.

TOUT EST PUBLIE PAR LE FRONT, EN CLAIR, DANS DEUX FICHIERS :
  /runtimeConfig.js          window.prismConfig -> serverUrl ET apiKey
  /static/js/main.<hash>.js  les 39 points d'entree, dont /presentation/v1/Query

C'est la regle « lire la reponse en entier avant de deviner une URL », appliquee a un
bundle JavaScript : la configuration du backend est servie par le front. On la LIT.
"""
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
CADENCE = 0.8
CONF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "portails.json")


def _ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def fiche(dept):
    c = json.load(open(CONF, encoding="utf-8"))
    p = next((x for x in c["portails"]
              if x["dept"] == str(dept) and x["moteur"] == "prismia"), None)
    if p is None:
        raise SystemExit(f"pas de portail prismia pour le departement {dept}")
    return p


def config(vitrine):
    """(serverUrl, apiKey) — LUS dans /runtimeConfig.js, jamais devines ni codes en dur.

    Les mettre dans portails.json serait une faute : le portail peut tourner sa cle, et
    une cle perimee rend 401 sur tout, ce qui ressemble a une panne du site.
    """
    t = urllib.request.urlopen(
        urllib.request.Request(vitrine.rstrip("/") + "/runtimeConfig.js", headers=UA),
        timeout=60, context=_ctx()).read().decode("utf-8")
    return (re.search(r"serverUrl:\s*'([^']+)'", t).group(1),
            re.search(r"apiKey:\s*'([^']+)'", t).group(1))


def _post(srv, key, chemin, corps, timeout=120):
    r = urllib.request.Request(
        srv.rstrip("/") + "/" + chemin.lstrip("/"),
        data=json.dumps(corps).encode("utf-8"),
        headers={**UA, "Content-Type": "application/json", "ApiKey": key,
                 "Accept": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=timeout, context=_ctx()).read())


def _get(srv, key, chemin, params=None, timeout=120, brut=False):
    url = srv.rstrip("/") + "/" + chemin.lstrip("/")
    if params:
        url += "?" + urllib.parse.urlencode(params)
    r = urllib.request.Request(url, headers={**UA, "ApiKey": key, "Accept": "*/*"})
    b = urllib.request.urlopen(r, timeout=timeout, context=_ctx()).read()
    return b if brut else json.loads(b)


# ------------------------------------------------------------------ les formulaires
def instruments(srv, key):
    """[{id, label, prismPathOrId, listInstrumentMeta}] — les formulaires du portail.

    LE MOTEUR SE DECRIT : chaque instrument porte ses facettes dans listInstrumentMeta,
    avec leur aggregateTag et la cle exacte a passer dans tagSelectedFilters. Rien a
    deviner, rien a scraper — meme recette qu'a l'AD49 en Arkotheque.
    """
    return _get(srv, key, "/presentation/v1/instrument/list")


def facette(srv, key, chemins, aggregate_tag, cles, texte="", taille=50):
    """Les valeurs d'une facette. UN LIBELLE DE COMMUNE SE LIT, IL NE SE RECONSTRUIT PAS."""
    d = _post(srv, key, "/presentation/v1/facet/getFacetValues", {
        "prismPathOrId": chemins, "tagSelectedFilters": [], "text": texte,
        "size": taille, "sortAlpha": True, "aggregateTag": aggregate_tag,
        "aggregateValue": cles, "excludeInheritedValues": False,
        "searchParameters": None})
    return [(x["label"], x["docCount"]) for x in d.get("searchAggsMetaTag", [])]


# --------------------------------------------------------------------- la recherche
def query(srv, key, chemins, filtres=None, texte="", deb=None, fin=None,
          debut=0, taille=100):
    corps = {"text": texte, "phrase": False, "images": False,
             "coteDeb": "", "coteFin": "",
             "periodeDeb": f"{deb}-01-01" if deb else "",
             "periodeFin": f"{fin}-12-31" if fin else "",
             "periodeRange": "between" if deb else "",
             "periodeFieldType": "year" if deb else "",
             "prismPathOrId": chemins, "tagSelectedFilters": filtres or [],
             "from": debut, "size": taille, "responseBy": "Pertinence",
             "onlyRestricted": False}
    return _post(srv, key, "/presentation/v1/Query", corps)


def lignes(d):
    out = []
    for o in d.get("listResponseObject", []):
        out.append({"titre": " / ".join(o.get("label", {}).get("fr", [""])),
                    "cote": o.get("prismCoteId"),
                    "vues": o.get("prismNbMedias"),
                    "guid": o.get("prismGuid")})
    return out


def registres(dept, commune, actes=None, deb=None, fin=None, pas=100):
    """(total, [ligne]) pour une commune, dans l'instrument etat civil du portail.

    ON PAGINE, ET ON RECOMPTE CONTRE LE TOTAL ANNONCE. Le 4 septembre 2026, cette
    fonction demandait 200 reponses d'un coup : Villeneuve-sur-Lot en a 224 pour les seuls
    mariages, et LES 24 DERNIERES TOMBAIENT SANS UN MOT. La liste avait l'air complete et
    montrait des trous de 1878-1880 et 1888-1892 dans le fonds — trous qui n'existent pas.
    C'est la regle « un parametre invente est ignore en silence », payee une fois de plus.
    """
    p = fiche(dept)
    srv, key = config(p["vitrine"])
    R = p["recherche"]
    filtres = [{"keys": [R["cle_commune"]], "values": [commune]}]
    if actes:
        # UN LIBELLE SEUL EST UNE CHAINE, ET L'API VEUT UNE LISTE. Passer
        # actes="Baptêmes ou Naissances" rendait un 400 sec, sans message utile : le
        # serveur lisait la chaine caractere par caractere.
        filtres.append({"keys": [R["cle_actes"]],
                        "values": [actes] if isinstance(actes, str) else list(actes)})
    tout, debut, total = [], 0, None
    while total is None or debut < total:
        d = query(srv, key, R["chemins_etat_civil"], filtres, "", deb, fin, debut, pas)
        total = d["total"] if total is None else total
        lot = lignes(d)
        if not lot:
            break
        tout += lot
        debut += len(lot)
    if len(tout) != total:
        print(f"  [alerte] {len(tout)} lignes pour {total} annoncees — liste tronquee",
              file=sys.stderr)
    return total, tout


# ------------------------------------------------------------------ les images, IIIF
def manifeste(srv, key, guid):
    return _get(srv, key, f"/iiif/presentation/v3/{guid}/manifest", timeout=240)


def urls(m):
    """[(n, url)] — LUES dans items[].items[0].items[0].body.id, jamais reconstruites."""
    out = []
    for i, c in enumerate(m.get("items", []), 1):
        try:
            out.append((i, c["items"][0]["items"][0]["body"]["id"]))
        except (KeyError, IndexError):
            out.append((i, None))
    return out


def tirer(dept, guid, dossier, debut=1, fin=None, cadence=CADENCE):
    """Ecrit v001.jpg ... pour les vues [debut, fin], NUMEROTEES A PARTIR DE 1.

    ATTENTION : LE NUMERO DE VUE N'EST PAS LE NUMERO DE PAGE DU REGISTRE. A
    Villeneuve-sur-Lot, les vues 64 et 65 du registre des naissances 1878-1882 portent
    LES MEMES ACTES — la meme double page photographiee deux fois, avec le volet de la
    mention marginale replie autrement. Estimer une date en divisant le nombre de vues
    par le nombre d'annees se trompe donc toujours dans le meme sens : trop loin.
    """
    p = fiche(dept)
    srv, key = config(p["vitrine"])
    us = urls(manifeste(srv, key, guid))
    fin = fin or len(us)
    os.makedirs(dossier, exist_ok=True)
    faits = []
    for n, u in us:
        if not (debut <= n <= fin) or u is None:
            continue
        chemin = os.path.join(dossier, "v%03d.jpg" % n)
        faits.append(chemin)
        if os.path.exists(chemin) and os.path.getsize(chemin) > 50_000:
            continue
        r = urllib.request.Request(u, headers={**UA, "ApiKey": key})
        open(chemin, "wb").write(
            urllib.request.urlopen(r, timeout=240, context=_ctx()).read())
        time.sleep(cadence)
    return faits


def _usage():
    print(__doc__)
    print("  python prismia.py <dept> instruments")
    print("  python prismia.py <dept> communes [motif]")
    print("  python prismia.py <dept> actes")
    print("  python prismia.py <dept> registres <Commune> [type d'acte] [debut] [fin]")
    print("  python prismia.py <dept> tirer <guid> <dossier> [debut] [fin]")
    raise SystemExit(1)


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    a = sys.argv[1:]
    if len(a) < 2:
        _usage()
    dept, cmd = a[0], a[1]
    p = fiche(dept)
    srv, key = config(p["vitrine"])
    R = p["recherche"]
    if cmd == "instruments":
        for x in instruments(srv, key):
            print("%-3s %-36s %s" % (x.get("id"), x.get("label"),
                                     (x.get("prismPathOrId") or [""])[0][:90]))
    elif cmd == "communes":
        for lab, n in facette(srv, key, R["chemins_etat_civil"], "Lieux",
                              [R["cle_commune"]], a[2] if len(a) > 2 else "", 200):
            print("%-44s %s" % (lab, n))
    elif cmd == "actes":
        for lab, n in facette(srv, key, R["chemins_etat_civil"], "ExtraField",
                              [R["cle_actes"]], "", 50):
            print("%-44s %s" % (lab, n))
    elif cmd == "registres":
        actes = [a[3]] if len(a) > 3 and a[3] else None
        deb = int(a[4]) if len(a) > 4 else None
        fin = int(a[5]) if len(a) > 5 else deb
        tot, ls = registres(dept, a[2], actes, deb, fin)
        print(f"{tot} registres")
        for r in ls:
            print("  %-56s cote=%-18s vues=%-5s guid=%s"
                  % (r["titre"][:56], r["cote"], r["vues"], r["guid"]))
    elif cmd == "tirer":
        d = int(a[4]) if len(a) > 4 else 1
        f = int(a[5]) if len(a) > 5 else None
        print(len(tirer(dept, a[2], a[3], d, f)), "vues ->", a[3])
    else:
        _usage()
