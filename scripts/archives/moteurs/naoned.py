# -*- coding: utf-8 -*-
"""Moteur NAONED — AD37 (Touraine) et AD19 (Correze), et tout portail qui tourne dessus.

CE QU'IL FAUT SAVOIR AVANT DE LIRE LE CODE : ce moteur ne demande AUCUN navigateur.
Les autres modules de ce repertoire pilotent un Chrome parce que leur portail rend
tout en JavaScript ; ici, la recherche est rendue cote serveur et les images sortent
d'une URL directe. Trois requetes HTTP ordinaires suffisent a depouiller un registre.

    recherche(...)  -> les registres d'une commune (ark, cote, titre, nombre de vues)
    vues(...)       -> les N vues d'un registre, dans l'ordre, avec leur uuid
    telecharge(...) -> les images sur le disque, v001.jpg, v002.jpg, ...

LA LISTE DES VUES A MANQUE UNE SEMAINE, ET LA REPONSE ETAIT SOUS LES YEUX. La fiche du
portail 37 a porte du 18 au 25 aout 2026 la mention « l'endpoint qui rend la liste n'est
pas trouve », apres huit chemins essayes a la main. Il y en avait deux :

  1. /visualizer/api?naan=&arkName=&uuid=  — JSON : le nombre total de vues, et une
     fenetre de quinze vues autour de la position courante. Les trois parametres sont
     obligatoires ; sans uuid, 400.
  2. /iiif/ark:/{naan}/{arkName}/manifest.json — LE MANIFESTE IIIF, qui rend TOUT le
     registre en une requete et ne demande pas d'uuid. C'est celui-la qu'on utilise.

Et le premier appel contenait, dans media[].location.iiif, l'adresse du second. La lecon
tient en une ligne : LIRE LA REPONSE EN ENTIER AVANT DE DEVINER UNE URL.
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request
import sys

# La verification TLS de cette machine est reparee par `scripts/archives/tls.py` :
# le magasin de racines de Windows porte une racine perimee, et tous ces portails sont
# chez Let's Encrypt. Un import suffit, il agit sur tout le processus.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tls  # noqa: F401,E402

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
CADENCE = 1.0          # secondes entre deux images ; le portail ne s'en plaint pas
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def _get(url, timeout=90):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


# --------------------------------------------------------------- la recherche
# LES NOMS DES CHAMPS CHANGENT D'UN PORTAIL NAONED A L'AUTRE, ET UN NOM FAUX EST IGNORE EN
# SILENCE. Ce module a pose jusqu'au 25 septembre 2026 les noms de la Touraine partout.
# Au Calvados, qui les veut SANS prefixe et appelle ses dates `period_begin`, la commune
# comme la date tombaient dans le vide : Mondeville rendait les 10 000 notices du
# departement, exactement comme une requete sans filtre — et le handoff du jour en avait
# conclu « le filtre de date ne filtre pas sur ce portail ». Il filtre : 68 notices pour
# Mondeville, 4 pour 1893. Les noms se lisent dans la fiche du portail, voir noms().
NOMS_AD37 = {"commune": "0-controlledAccessGeographicName[]",
             "type_acte": "2-controlledAccessPhysicalCharacteristic[]",
             "debut": "3-date_begin", "fin": "3-date_end"}


def noms(portail):
    """Les noms de champs d'un portail, lus dans `recherche.params` de sa fiche.

    La fiche les porte deja sous forme de gabarit (« {commune} ({nom_dept}, France) »,
    « {annee_debut} »...) : on les inverse. Une fiche sans `params` rend les noms de
    l'AD37 — c'est une supposition, et il faut la verifier en comparant le total obtenu
    a celui d'une requete sans filtre.
    """
    params = (portail.get("recherche") or {}).get("params") or {}
    role = {"{commune}": "commune", "{type_acte}": "type_acte",
            "{annee_debut}": "debut", "{annee_fin}": "fin"}
    lus = {r: champ for champ, gabarit in params.items()
           for motif, r in role.items() if gabarit.startswith(motif)}
    return {**NOMS_AD37, **lus}


def recherche(base, form_uuid, commune, type_acte=None, debut=None, fin=None, pages=10,
              champs=None):
    """[{ark, cote, titre, vues}] pour une commune.

    `commune` doit etre le LIBELLE COMPLET du vocabulaire, « Courcelles-de-Touraine
    (Indre-et-Loire, France) ». Il ne se reconstruit pas : la liste entiere est dans le
    HTML de {base}/search/form/{form_uuid}, en clair. Voir libelles().

    `type_acte` est une liste fermee (« Naissances », « Mariages », « Deces », « Table
    decennale »...) — MAIS ELLE N'EST PAS APPLIQUEE PARTOUT. A Courcelles-de-Touraine,
    les tables decennales portent un titre nu (« 1903-1912 ») et ne repondent a aucun
    type : les chercher en listant toute la commune, type_acte=None.

    `champs` : les noms de champs du portail, `noms(fiche)`. Absent, ceux de l'AD37.
    """
    n = champs or NOMS_AD37
    out, vus = [], set()
    for page in range(1, pages + 1):
        p = {"formUuid": form_uuid, "mode": "list", "sort": "date_asc",
             n["commune"]: commune, "page": str(page)}
        if type_acte:
            p[n["type_acte"]] = type_acte
        if debut:
            p[n["debut"]] = str(debut)
        if fin:
            p[n["fin"]] = str(fin)
        html = _get(base + "/search/results?" + urllib.parse.urlencode(p)).decode("utf-8", "replace")
        # COMMENT CE PORTAIL DIT « RIEN » : la chaine « Aucun resultat ». NE PAS tester
        # « Aucun » tout court -- le panneau de facettes affiche « Aucune valeur
        # disponible » sur presque toutes les pages, y compris quand il y a des
        # resultats. Le 25 aout 2026, ce raccourci a fait declarer Villiers-au-Bouin
        # vide alors que la commune a 158 documents.
        if re.search(r"Aucun r.sultat", html):
            break
        notices = _notices(html)
        if not notices:
            break
        neuf = False
        for b in notices:
            if b["ark"] in vus:
                continue
            vus.add(b["ark"])
            neuf = True
            out.append(b)
        if not neuf:
            break
        time.sleep(0.4)
    return out


def _notices(html):
    """Une entree par notice, lue DANS SON BLOC <li class="element-list">.

    La version precedente relevait les arks suivis d'un uuid de vue, puis leur attribuait
    titre et nombre de vues PAR POSITION dans la page. Deux fautes en une, payees au
    Calvados le 25 septembre 2026 : une notice CATALOGUEE SANS IMAGE n'a pas de lien de
    vue, donc elle disparaissait (36 notices rendues sur 68 a Mondeville) — et en
    disparaissant elle decalait d'un cran le titre de toutes les suivantes. On rendait
    alors « 1879-1892, 729 vues » sur un registre qui n'etait pas celui-la.

    Une notice sans image est GARDEE, avec vues=0 et uuid_premiere_vue=None : « le
    registre existe » et « on peut le lire » ne sont pas la meme reponse, et la
    difference se dit.
    `contexte` porte ce que la page affiche sous le titre — la commune, et surtout le
    TYPE D'ACTE (« Naissances », « Baptemes, Mariages, Sepultures »), qui n'est pas
    dans le titre.
    """
    import html as _h
    out = []
    for bloc in re.split(r'<li class="element-list"', html)[1:]:
        ark = re.search(r'ark:/(\d+)/([0-9a-zA-Z]+)', bloc)
        if not ark:
            continue
        uuid = re.search(r"ark:/\d+/[0-9a-zA-Z]+/(" + UUID + ")", bloc)
        med = re.search(r"(\d+)\s*m.dias?\b", bloc)
        titre = re.search(r'title="Voir la notice compl[^:"]*:\s*([^"]*)"', bloc)
        cote = re.search(r"Cote\s*</h3>\s*<p>(.*?)</p>", bloc, flags=re.S)
        ctx = re.search(r'<ul class="context[^"]*">(.*?)</ul>', bloc, flags=re.S)
        net = lambda s: re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
        out.append({
            "naan": ark.group(1), "ark": ark.group(2),
            "uuid_premiere_vue": uuid.group(1) if uuid else None,
            "vues": int(med.group(1)) if med else 0,
            "titre": _h.unescape(titre.group(1)).strip() if titre else None,
            "cote": net(cote.group(1)) if cote else None,
            "contexte": [net(li) for li in re.findall(r"<li>(.*?)</li>", ctx.group(1), flags=re.S)]
                        if ctx else [],
        })
    return out or _par_position(html)


def _par_position(html):
    """L'ancienne lecture, pour une page qui n'aurait pas de blocs element-list."""
    arks = list(dict.fromkeys(re.findall(r"ark:/(\d+)/([0-9a-zA-Z]+)/(" + UUID + ")", html)))
    blocs = _blocs(html)
    return [{"naan": naan, "ark": ark, "uuid_premiere_vue": uuid,
             "vues": (blocs[i] if i < len(blocs) else {}).get("vues"),
             "titre": (blocs[i] if i < len(blocs) else {}).get("titre"),
             "cote": (blocs[i] if i < len(blocs) else {}).get("cote"), "contexte": []}
            for i, (naan, ark, uuid) in enumerate(arks)]


def _blocs(html):
    """Titre, cote et nombre de vues de chaque resultat, dans l'ordre de la page."""
    import html as _h
    t = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    t = _h.unescape(re.sub(r"<[^>]+>", "\n", t))
    lignes = [x.strip() for x in t.split("\n") if x.strip()]
    out = []
    for k, x in enumerate(lignes):
        if "sultat n" not in x:                       # « Resultat n° » sans l'accent
            continue
        b = lignes[k:k + 10]
        med = next((y for y in b if "medias" in y), "")
        out.append({
            "vues": int(re.match(r"(\d+)", med).group(1)) if med else None,
            "titre": next((y for y in b if re.search(r"\d{4}", y)
                           and "medias" not in y and "sultat" not in y), None),
            "cote": next((y for y in b if "Cote" in y), None),
        })
    return out


def libelles(base, form_uuid, motif):
    """Les libelles de commune du vocabulaire qui contiennent `motif`.

    Le libelle exact est un piege paye deux fois (AD42 puis AD37) : il ne se devine pas,
    il se lit. Le formulaire porte la liste entiere -- mais DEUX FOIS ENCODEE : entites
    HTML par-dessus des echappements JSON, si bien que « Rille » y dort sous la forme
    « Rill\\u00e9 » et qu'une recherche du nom accentue ne rend rien. On decode les deux
    couches avant de chercher, sinon on croit la commune absente.
    """
    import html as _h
    page = _h.unescape(_get(base + "/search/form/" + form_uuid).decode("utf-8", "replace"))
    page = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), page)
    return sorted(set(re.findall(re.escape(motif) + r"[^\"<>]{0,60}", page)))


# ----------------------------------------------------------- les vues, par IIIF
def vues(base, naan, ark_name):
    """[{n, lot, uuid, w, h}] pour TOUT le registre, dans l'ordre.

    UN REGISTRE PEUT ETRE DECOUPE EN LOTS, et le manifeste est alors une COLLECTION :
    ses `items` ne sont plus des Canvas mais des sous-manifestes
    `/iiif/ark:/{naan}/{ark}/group/{i}/manifest.json`. La visionneuse l'affiche
    « Lot 1/2 ». Le 26 aout 2026 ce module a plante dessus, sur le repertoire de la
    classe 1929 : il cherchait un `/canvas/N` dans l'id d'un sous-manifeste. On
    descend donc d'un cran quand c'est le cas, et on concatene les lots dans l'ordre.
    """
    j = json.loads(_get(f"{base}/iiif/ark:/{naan}/{ark_name}/manifest.json").decode("utf-8"))
    lots = ([f"{base}/iiif/ark:/{naan}/{ark_name}/group/{i}/manifest.json"
             for i, _ in enumerate(j["items"])]
            if j["items"] and "/group/" in j["items"][0]["id"] else [None])
    out = []
    for lot, url in enumerate(lots, 1):
        k = json.loads(_get(url).decode("utf-8")) if url else j
        for c in k["items"]:
            m = re.search(r"/(" + UUID + r")/canvas/(\d+)", c["id"])
            out.append({"n": len(out) + 1, "lot": lot, "vue_du_lot": int(m.group(2)) + 1,
                        "uuid": m.group(1), "w": c.get("width"), "h": c.get("height")})
    return out


def vues_api(base, naan, ark_name, cadence=0.4):
    """Comme vues(), mais par /visualizer/api — POUR LES PORTAILS SANS IIIF.

    L'AD19 (Correze) tourne sur le meme moteur que l'AD37 et sert les memes URLs de
    recherche, MAIS SON /iiif/.../manifest.json REND 404. La fiche annoncait « IIIF est
    une norme, la meme adresse a toutes les chances de servir sur les autres portails
    Naoned » : elle sert sur l'un et pas sur l'autre, et c'est verifie le 1er septembre 2026.

    L'autre porte demande ses TROIS parametres, dont un uuid de depart — qu'on lit dans le
    HTML de la page {base}/ark:/{naan}/{ark_name}. Elle ne rend qu'une FENETRE de quinze
    vues autour de la position courante : on avance de fenetre en fenetre jusqu'a en avoir
    counts.media, en repartant du dernier uuid vu.
    """
    page = _get(f"{base}/ark:/{naan}/{ark_name}").decode("utf-8", "replace")
    depart = re.search(UUID, page)
    if not depart:
        raise RuntimeError(f"aucun uuid dans la page ark de {ark_name}")

    connus, ordre, pivot, total = {}, [], depart.group(0), None
    while True:
        j = json.loads(_get(f"{base}/visualizer/api?naan={naan}"
                            f"&arkName={ark_name}&uuid={pivot}").decode("utf-8"))
        total = j["counts"]["media"]
        # `media` EST UNE LISTE AU PREMIER APPEL ET UN DICT AUX SUIVANTS, indexe par la
        # position dans le registre. Itere tel quel, le dict rend ses CLES — des chaines —
        # et le `m["uuid"]` casse sur un TypeError qui ne dit rien de la cause.
        brut = j["media"]
        fenetre = ([brut[k] for k in sorted(brut, key=lambda s: int(s))]
                   if isinstance(brut, dict) else brut)
        neuf = 0
        for m in fenetre:
            u = m["uuid"]
            if u not in connus:
                connus[u] = m
                ordre.append(u)
                neuf += 1
        if len(connus) >= total or neuf == 0:
            break
        pivot = ordre[-1]
        time.sleep(cadence)

    if len(connus) != total:
        raise RuntimeError(f"{ark_name} : {len(connus)} vues sur {total} annoncees")
    return [{"n": i, "lot": 1, "vue_du_lot": i, "uuid": u,
             "w": None, "h": None} for i, u in enumerate(ordre, 1)]


def telecharge(base, vues_, dossier, debut=1, fin=None, cadence=CADENCE):
    """Ecrit v###.jpg pour les vues [debut, fin]. Ne retelecharge jamais un fichier deja la.

    L'URL de l'image est {base}/images/{uuid}.jpg — pas de cookie, pas de referer, pas de
    compte. NE PAS passer par /visualizer/api/record/.../media/... : 404 depuis l'exterieur,
    quelle que soit la forme de l'ark. Et le bouton de telechargement du site produit un
    blob, donc il n'a pas d'URL : inutile de la chercher.
    """
    os.makedirs(dossier, exist_ok=True)
    fin = fin or max(v["n"] for v in vues_)
    faits = []
    for v in vues_:
        if not (debut <= v["n"] <= fin):
            continue
        chemin = os.path.join(dossier, "v%03d.jpg" % v["n"])
        faits.append(chemin)
        if os.path.exists(chemin) and os.path.getsize(chemin) > 50_000:
            continue
        open(chemin, "wb").write(_get(f"{base}/images/{v['uuid']}.jpg"))
        time.sleep(cadence)
    return faits


if __name__ == "__main__":
    import sys
    # python naoned.py <base> <naan> <arkName> <dossier> [debut] [fin]
    a = sys.argv[1:]
    vs = vues(a[0], a[1], a[2])
    print(f"{len(vs)} vues")
    if len(a) > 3:
        d = int(a[4]) if len(a) > 4 else 1
        f = int(a[5]) if len(a) > 5 else None
        print(len(telecharge(a[0], vs, a[3], d, f)), "images")
