# -*- coding: utf-8 -*-
"""Moteur ARCHINOE — AD17 (Charente-Maritime), et tout portail qui tourne dessus.

SEPTIEME MOTEUR DU DOSSIER. Il ne demande AUCUN navigateur : quelques requetes HTTP
ordinaires suffisent, du referentiel des communes au JPEG.

    communes(...)   -> les 552 communes du departement, avec leur identifiant
    registres(...)  -> les registres d'une commune : periode, type d'acte, lacunes, id
    cadastres(...)  -> les plans cadastraux d'une commune : cote, section, date, type
    vues(...)       -> les chemins des vues d'un registre ou d'un plan, dans l'ordre
    tirer(...)      -> les images sur le disque, v001.jpg, v002.jpg, ...

    python archinoe.py 17 communes mathes
    python archinoe.py 17 registres 170000379
    python archinoe.py 17 tirer 170030582 "<archives>/AD17 - Les Mathes/N 1870-1880"
    python archinoe.py 17 cadastre 170000390
    python archinoe.py 17 tirer-plan 170080750 "<archives>/AD17 - Royan/Cadastre TA 1985"

LE FORMULAIRE EST LISIBLE DANS LE HTML, ET C'EST UNE PREMIERE. L'AD43 et l'AD49 servent
des pages sans un seul <input> — il y fallait gratter une API. Ici les champs sont en
clair, et LE REFERENTIEL DES 552 COMMUNES TIENT DANS LA PAGE DU FORMULAIRE : une requete,
aucune pagination, aucune facette a deplier. « Un libelle de commune se lit, il ne se
reconstruit pas » — ici il se lit vraiment.

LES SELECTEURS SONT EN CASCADE, ET LEUR RECETTE EST DANS /v2/console/js/script.js :

    {page}.html?{champ}={valeur}&type={champ_suivant}&id_lieu_ref=

et la reponse est une liste d'<option>. D'ou l'enchainement :

    registre.html                                          -> les communes
    registre.html?commune=<id>&type=collection             -> communale / greffe
    registre.html?commune=<id>&collection=<id>&type=registre -> etat civil / paroissial
    registre_liste.html?commune=&collection=&registre=&acte=&annee=  -> les registres
    visualiseur/registre.html?id=<id>                      -> les vues du registre

LE CADASTRE SUIT LA MEME MECANIQUE (11 septembre 2026), avec d'autres noms :

    cadastre_liste.html?commune=<id>&canton=&cadastre=&plan=   -> les plans
    visualiseur/cadastre.html?id=<id>                          -> les vues du plan

Cinq types de cadastre (napoleonien, remanie, remembre, renove, renove « derniere mise a
jour avant informatisation ») et trois types de plan (tableau d'assemblage, feuille de
section, neant). CE SONT DES PLANS, PAS DES MATRICES : ils montrent les parcelles et leurs
numeros, jamais les proprietaires. Et ils ont des trous : a Royan, rien entre 1838 et 1964.

TROIS PIEGES PAYES, ET LE TROISIEME FAISAIT MENTIR CE MODULE SANS BRUIT.

1. `recherche_data.php` N'EST PAS LA BONNE PORTE, et elle repond quand meme. Interrogee
   avec ?type=commune elle rend `{"query":"Marennes","suggestions":[]}` — elle echoit la
   question et rend une liste vide. Ce n'est pas une session qui manque : cette route sert
   l'AUTOCOMPLETION DE L'INDEXATION COLLABORATIVE, pas les selecteurs du formulaire. Un
   endpoint qui repond poliment a cote n'est pas un endpoint casse ; c'est le mauvais.

2. `data-original` EST LE CHEMIN DISQUE DU SERVEUR, PAS UNE URL. Le HTML du visualiseur
   porte data-original="/mnt/lustre/ad17/etatcivil/…jpg" et lazyload le copie tel quel :
   les trois formes evidentes rendent 404. LA VRAIE ROUTE EST UN PROXY, et le visualiseur
   s'en sert a chaque vue :

       /v2/images/genereImage.html?o=IMG&image=<chemin disque>&l=<largeur>&h=<hauteur>&r=0&n=0&b=0&c=0

   Elle rend une ligne de sept champs separes par des TABULATIONS, dont

       [1] le chemin du JPEG dans /cache/    [2],[3] la taille servie
       [4],[5] LA TAILLE DU MASTER           [6] l'identifiant de la vue

   LE 1er SEPTEMBRE 2026, UNE SESSION A CONCLU « image : trouvee, et elle echoue cote
   serveur — ne pas repartir de la », apres neuf tentatives sur trois sessions. Elle
   passait par `telechargement.html`, LE BOUTON DE TELECHARGEMENT du site, qui demande un
   hash puis genere l'image a la demande et expire a vingt secondes. Le visualiseur, lui,
   ne demande jamais ca : il appelle genereImage.html et recoit son JPEG tout de suite.
   LA LECON N'EST PAS « LE PORTAIL EST CASSE » MAIS « J'AI PRIS LA PORTE DE L'UTILISATEUR
   AU LIEU DE CELLE DE LA PAGE ». Quand un chemin echoue, regarder ce que le site fait
   pour AFFICHER, pas ce qu'il propose pour telecharger.

3. LES LISTES SONT PAGINEES PAR VINGT, ET LA PAGE SUIVANTE TIENT A UN COOKIE. Jusqu'au
   11 septembre 2026, `registres()` ne lisait que la premiere page et ne le disait pas :
   Royan a plus de vingt registres, le module en rendait vingt. Le cadastre de Royan
   annonce 167 plans ; `cadastre_liste.html?page=2` SANS COOKIE rend une page vide, AVEC le
   cookie PHPSESSID de la recherche il rend les vingt suivants. D'ou une session a
   cookies pour tout le module, et une boucle de pages qui s'arrete quand une page
   n'apporte plus rien de neuf. RECOMPTER CONTRE LE TOTAL ANNONCE : c'est la regle de la
   skill, et elle s'appliquait ici aussi.

`l` ET `h` SONT LA LARGEUR ET LA HAUTEUR MAXIMALES, ET LE PLAFOND DE 1800 PX N'EN ETAIT QUE
LA VALEUR PAR DEFAUT. Ce module a longtemps affirme « c'est la hauteur qui plafonne a 1800,
demander plus ne rend pas plus » : c'etait vrai sans `h`. Avec `l=12359&h=8880`, le plan de
Royan sort a 12359 x 8880, son master entier. `image()` fait donc deux appels : le premier
lit la taille du master, le second la demande. Pour un registre, 2472 px suffisaient a la
recette de lecture ; pour un plan au 1/10 000, les numeros de parcelle n'existent qu'a
pleine resolution.
"""
import http.cookiejar
import io
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

import certifi

# La verification TLS de cette machine est reparee par `scripts/archives/tls.py` :
# le magasin de racines de Windows porte une racine perimee, et tous ces portails sont
# chez Let's Encrypt. Un import suffit, il agit sur tout le processus.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tls  # noqa: F401,E402

# LE MAGASIN TLS DE WINDOWS FAIT ECHOUER PYTHON SUR CERTAINS PORTAILS, et le site n'y est
# pour rien : c'est la lecon du certificat de l'AD49. On passe certifi, on ne desactive pas.
CTX = ssl.create_default_context(cafile=certifi.where())
CADENCE = 0.35
CONF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "portails.json")

# Une seule session pour tout le module : la pagination en depend (piege 3).
_OPENER = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
    urllib.request.HTTPSHandler(context=CTX))


def _conf(dept):
    with io.open(CONF, encoding="utf-8") as f:
        for p in json.load(f)["portails"]:
            if str(p.get("dept")) == str(dept):
                return p
    raise SystemExit("departement %s absent de portails.json" % dept)


def _get(url, referer=None, brut=False, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                               "Referer": referer or url})
    d = _OPENER.open(req, timeout=timeout).read()
    return d if brut else d.decode("utf-8", "replace")


def _options(html, select_id=None):
    """[(valeur, libelle)] d'une liste d'<option> — la reponse des selecteurs en cascade."""
    if select_id:
        m = re.search(r'<select[^>]*id="%s".*?</select>' % select_id, html, re.S)
        html = m.group(0) if m else ""
    out = []
    for v, t in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', html, re.S):
        lib = re.sub(r"<[^>]+>", "", t)
        lib = " ".join(_dehtml(lib).split())
        if v and lib and not lib.startswith("--"):
            out.append((v, lib))
    return out


def _dehtml(s):
    try:
        import html as _h
        return _h.unescape(s)
    except Exception:
        return s


def _lignes(h, page):
    """Les lignes d'un tableau de resultats : [(id, [colonnes])]."""
    out = []
    for bloc in re.split(r'(?=visualiseur/%s\.html\?id=)' % page, h)[1:]:
        ident = re.match(r"visualiseur/%s\.html\?id=(\d+)" % page, bloc).group(1)
        cells = [" ".join(_dehtml(re.sub(r"<[^>]+>", " ", c)).split())
                 for c in re.findall(r"<span class=[\"']Cell[\"']>(.*?)</span>\s*</span>",
                                     bloc[:4000], re.S)]
        if not cells:
            cells = [" ".join(_dehtml(re.sub(r"<[^>]+>", " ", c)).split())
                     for c in re.findall(r"<td[^>]*>(.*?)</td>", bloc[:4000], re.S)]
        out.append((ident, [c for c in cells if c]))
    return out


def _toutes_les_pages(base, liste, requete, page, referer):
    """Premiere page par la requete, les suivantes par ?page=N dans la meme session.

    On s'arrete quand une page n'apporte plus aucun identifiant neuf : le portail rend la
    derniere page, ou une page vide, au-dela du total — les deux cas se traitent pareil.
    """
    h = _get(base + "/" + liste + "?" + requete, base + "/" + referer)
    total = re.search(r"(\d+)\s*r[ée]sultat", h)
    out, vus, n = [], set(), 1
    while True:
        neuves = [(i, c) for i, c in _lignes(h, page) if i not in vus]
        if not neuves:
            break
        out += neuves
        vus |= {i for i, _ in neuves}
        n += 1
        time.sleep(CADENCE)
        h = _get(base + "/%s?page=%d" % (liste, n), base + "/" + liste)
    if total and int(total.group(1)) != len(out):
        print("  ATTENTION : %s resultats annonces, %d lus" % (total.group(1), len(out)),
              file=sys.stderr)
    return out


# ------------------------------------------------------------------ le referentiel
def communes(base, motif=""):
    """Les communes du departement, avec leur identifiant. UNE SEULE REQUETE."""
    h = _get(base + "/registre.html")
    m = motif.lower()
    return [(v, t) for v, t in _options(h, "inputcommune")
            if not m or m in t.lower()]


def collections(base, id_commune):
    return _options(_get(base + "/registre.html?commune=%s&type=collection&id_lieu_ref="
                         % id_commune, base + "/registre.html"))


def types_registre(base, id_commune, id_collection):
    return _options(_get(base + "/registre.html?commune=%s&collection=%s&type=registre"
                         "&id_lieu_ref=" % (id_commune, id_collection),
                         base + "/registre.html"))


def registres(base, id_commune, id_collection="", id_type=""):
    """Les registres d'une commune : (id, [colonnes du tableau]), TOUTES PAGES LUES.

    Chaque ligne du tableau porte cote, commune, collection, type de registre, actes,
    table, LACUNES et periode — et les lacunes valent autant qu'une trouvaille : c'est
    ce qui evite de conclure « l'acte n'existe pas » sur un trou de collection.
    """
    q = "commune=%s&collection=%s&registre=%s&acte=&annee=" % (
        id_commune, id_collection, id_type)
    return _toutes_les_pages(base, "registre_liste.html", q, "registre", "registre.html")


def cadastres(base, id_commune, id_type="", id_plan=""):
    """Les plans cadastraux d'une commune : (id, [cote, commune, commune, section, date,
    type]), TOUTES PAGES LUES. Des plans, pas des matrices : aucun proprietaire."""
    q = "canton=&commune=%s&cadastre=%s&plan=%s" % (id_commune, id_type, id_plan)
    return _toutes_les_pages(base, "cadastre_liste.html", q, "cadastre", "cadastre.html")


# ------------------------------------------------------------------------ les images
def vues(base, ident, page="registre"):
    """Les chemins disque des vues d'un registre (ou d'un plan, page="cadastre"), DANS
    L'ORDRE. Une seule requete : la page du visualiseur les porte toutes."""
    h = _get(base + "/visualiseur/%s.html?id=%s" % (page, ident),
             base + "/%s_liste.html" % page)
    vus, out = set(), []
    for p in re.findall(r'data-original="([^"]+\.jpg)"', h):
        if p not in vus:
            vus.add(p)
            out.append(p)
    return out


def _genere(base, chemin, largeur, hauteur):
    q = {"o": "IMG", "image": chemin, "l": largeur, "r": 0, "n": 0, "b": 0, "c": 0,
         "id": "v"}
    if hauteur:
        q["h"] = hauteur
    t = _get(base.split("/v2/")[0] + "/v2/images/genereImage.html?" + urllib.parse.urlencode(q),
             base + "/visualiseur/registre.html").split("\t")
    if len(t) < 6 or not t[1].endswith(".jpg"):
        raise RuntimeError("genereImage n'a pas rendu de chemin : %r" % t[:2])
    return t


def image(base, chemin, pleine=True):
    """Le JPEG d'une vue. Rend (octets, largeur, hauteur, largeur_master, hauteur_master).

    pleine=True : le master entier, en deux appels (le premier lit sa taille). Sans `h`,
    le serveur plafonne a 1800 px de haut — voir l'en-tete.
    """
    t = _genere(base, chemin, 4264, None)
    if pleine and (int(t[2]), int(t[3])) != (int(t[4]), int(t[5])):
        t = _genere(base, chemin, int(t[4]), int(t[5]))
    jpg = _get(base.split("/v2/")[0] + t[1], base + "/visualiseur/registre.html", brut=True)
    if jpg[:3] != b"\xff\xd8\xff":
        raise RuntimeError("ce n'est pas un JPEG : %r" % jpg[:40])
    return jpg, int(t[2]), int(t[3]), int(t[4]), int(t[5])


def tirer(base, ident, dossier, debut=1, fin=None, cadence=CADENCE, page="registre",
          pleine=False):
    """Les vues d'un registre ou d'un plan sur le disque, vNNN.jpg — la convention du NAS.

    Un registre se tire a la taille par defaut (2472 px, au-dessus de la recette de
    lecture) ; un plan se tire en pleine resolution, sinon ses numeros ne se lisent pas.
    """
    liste = vues(base, ident, page)
    fin = min(fin or len(liste), len(liste))
    os.makedirs(dossier, exist_ok=True)
    print("%s %s : %d vues listees" % (page, ident, len(liste)), flush=True)
    for n in range(debut, fin + 1):
        cible = os.path.join(dossier, "v%03d.jpg" % n)
        if os.path.exists(cible) and os.path.getsize(cible) > 20000:
            continue
        jpg, w, h, mw, mh = image(base, liste[n - 1], pleine)
        with open(cible, "wb") as f:
            f.write(jpg)
        print("  v%03d  %dx%d  (master %dx%d)  %d Ko" % (n, w, h, mw, mh, len(jpg) // 1024),
              flush=True)
        time.sleep(cadence)
    return fin - debut + 1


# ------------------------------------------------------------------------------- CLI
if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    base = _conf(a[0])["base"].rstrip("/")
    cmd = a[1] if len(a) > 1 else "communes"
    if cmd == "communes":
        for v, t in communes(base, a[2] if len(a) > 2 else ""):
            print("%-12s %s" % (v, t))
    elif cmd == "collections":
        for v, t in collections(base, a[2]):
            print("%-12s %s" % (v, t))
    elif cmd == "registres":
        coll = a[3] if len(a) > 3 else ""
        typ = a[4] if len(a) > 4 else ""
        lignes = registres(base, a[2], coll, typ)
        for ident, cells in lignes:
            print("%-10s %s" % (ident, " | ".join(cells)))
        print("%d registres" % len(lignes))
    elif cmd == "cadastre":
        lignes = cadastres(base, a[2])
        for ident, cells in lignes:
            print("%-10s %s" % (ident, " | ".join(cells)))
        print("%d plans" % len(lignes))
    elif cmd == "vues":
        for i, p in enumerate(vues(base, a[2]), 1):
            print("%4d %s" % (i, p))
    elif cmd in ("tirer", "tirer-plan"):
        plan = cmd == "tirer-plan"
        tirer(base, a[2], a[3],
              int(a[4]) if len(a) > 4 else 1,
              int(a[5]) if len(a) > 5 else None,
              page="cadastre" if plan else "registre", pleine=plan)
    else:
        raise SystemExit(__doc__)
