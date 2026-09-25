# -*- coding: utf-8 -*-
"""GAIA 9 — le moteur des Archives des Pyrenees-Orientales (AD66), et de qui l'emploie.

HUITIEME MOTEUR DU DOSSIER. Il ne ressemble a aucun autre : ni Boscop, ni Arkotheque, ni
Naoned, ni Anaphore, ni Archinoe, ni 4D, ni Prismia. Il se nomme dans son <title> :
« GAIA 9 : moteur de recherche - 9.4.8 ».

    LA FICHE DISAIT « LA VISIONNEUSE N'A PAS ETE OUVERTE », ET C'ETAIT UNE URL DEVINEE
    --------------------------------------------------------------------------------
    Le 12 septembre 2026, une session a passe l'argument de `detailNotice(0,0,'360573:...')`
    en segments d'URL, recu une erreur SQL brute, et conclu qu'il fallait un vrai navigateur.
    C'etait tirer une conclusion d'une URL inventee. L'ADRESSE DE LA VISIONNEUSE ETAIT DANS
    LA MEME PAGE, en clair, dans le `onClick` de la vignette :

        /mdr/index.php/docnumViewer/calculHierarchieDocNum/<idUd>/<cheminHierarchie>/<h>/<w>

    et cette page-la porte, dans son appel a `main({...})`, LA LISTE COMPLETE DES VUES du
    registre, avec pour chacune son `chemin`. Six jours perdus pour n'avoir pas lu la
    reponse en entier -- la regle est dans la skill depuis le debut.

    LE SERVEUR D'IMAGES N'A NI JETON NI COOKIE. Ses gabarits sont ecrits en clair dans
    `/mdr/assets/visualiseur/js/contentManager.js` :

        {HOST}/mdr/index.php/docnumserv/getImageVisualiseur/{RCODE}/{RVCODE}/{FILE}/{CACHE}/{TAILLE}/{COMPR}/{CRC}

    RCODE/RVCODE viennent de la fiche de la vue (« TSAI »/« TSAV » pour les tables de
    successions), FILE est le `chemin`, CACHE='N', COMPR=100, CRC=200.

    ⭐ LA TAILLE EST UN CODE, ET LE DEFAUT DU VISUALISEUR EST LE PETIT. `T17` est ce que la
    page demande ; **T20 est le maximum**, 2400 px sur le grand cote. Au-dela -- T21, T25,
    ORI -- le serveur rend 1 286 octets qui ne sont pas une image. Mesure : T15 = 800 px,
    T18 = 1600, T20 = 2400. Meme lecon qu'a l'AD17 : un plafond peut n'etre qu'un defaut.

    ⭐⭐ ET LE `chemin` D'UNE VUE PORTE SA LETTRE ALPHABETIQUE :

        PERPIGNAN@PERPIGNAN_VILLE@1304W553@P@FRAD066_1304W0553_095.JPG
                                            ^

    Sur une table des successions -- rangee par lettre, puis CHRONOLOGIQUEMENT par date de
    deces dans la lettre --, ca evite de feuilleter 144 vues : la lettre P du registre de
    1965 tient aux vues 95 a 107, et un mort du 14 juillet est au milieu. `sections()` rend
    la table des lettres sans tirer une seule image.

LE PARCOURS EST UNE SESSION A COOKIES, ET L'ORDRE COMPTE. GAIA garde la requete en session :
une etape appelee seule rend `Invalid argument supplied for foreach()`, qui ressemble a une
panne et n'est qu'un oubli de contexte.

⚠️ DEUX PIEGES D'ENCODAGE. La page se declare **iso-8859-1** -- la lire en UTF-8 rend
« requ?te ». Et **le libelle d'un critere fait partie de l'URL**, virgules et espaces
compris : il se COPIE depuis le HTML et s'encode, il ne se reconstruit pas.

Les dix themes, a `/mdr/index.php/rechercheTheme/requeteConstructor/<theme>/1/R/0/0` :

     1 Etat civil                                     6 Tables des deces, successions, absences
     2 Preparation militaire et recrutement           7 Fonds Francois Bernadi
     3 Recensement, liste nominative                  8 Iconographie de la Retirada
     4 Registres hypothecaires (1799-1955)           10 Controle des actes (1693-1791)
     5 Plans cadastraux                              13 Refugies et camps d'internement

Ligne de commande :

    python gaia.py themes
    python gaia.py --dept 09 themes            # un autre portail GAIA
    python gaia.py criteres 6                       # les bureaux du theme 6
    python gaia.py criteres 6 361650                # ... au second rang
    python gaia.py cherche 6 361650 361652 1965     # -> idUd + chemin de hierarchie
    python gaia.py vues 361490 360573:361650:361652:361490
    python gaia.py tirer 361490 360573:361650:361652:361490 "AD66 - Perpignan/TSA 1965" 95 107
"""
import io
import os
import re
import sys
import time
import http.cookiejar
import urllib.error
import urllib.parse
import urllib.request

# La verification TLS de cette machine est reparee par `scripts/archives/tls.py` :
# le magasin de racines de Windows porte une racine perimee, et tous ces portails sont
# chez Let's Encrypt. Un import suffit, il agit sur tout le processus.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tls  # noqa: F401,E402

# ⛔ LE DOMAINE A ETE ECRIT EN DUR ICI PENDANT UNE JOURNEE, ET C'EST LA FAUTE QUE LE DEPOT
# INTERDIT EN PREMIERE LIGNE : « le code vit par MOTEUR, pas par DEPARTEMENT ». Le 19 septembre
# 2026, l'AD09 s'est revelee tourner sur GAIA elle aussi -- meme chemin
# `/mdr/index.php/rechercheTheme/requeteConstructor/<theme>/1/R/0/0` -- et il n'y avait rien a
# ecrire, seulement une fiche a ajouter. Le domaine vient donc de `portails.json`, comme pour
# boscop.js, et `base(dept)` le resout.
import json as _json

_RACINE = _os_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PORTAILS = _json.load(io.open(os.path.join(_RACINE, "portails.json"), encoding="utf-8"))
DEFAUT = "66"


def base(dept=DEFAUT):
    """L'URL de base d'un portail GAIA, lue dans le registre des fonds."""
    for p in _PORTAILS["portails"]:
        if p.get("dept") == str(dept) and p.get("moteur") == "gaia":
            return p["base"].rstrip("/") + "/mdr/index.php"
    connus = [p.get("dept") for p in _PORTAILS["portails"] if p.get("moteur") == "gaia"]
    raise SystemExit("departement %r inconnu du moteur GAIA -- connus : %s"
                     % (dept, ", ".join(x for x in connus if x)))


BASE = base()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 os.pardir, os.pardir))
import config

NAS = config.archives()
CADENCE = 0.4
TAILLE_MAX = "T20"          # 2400 px ; au-dela le serveur ne rend pas une image

_op = None


def _ouvre():
    """UNE SESSION A COOKIES, TOUJOURS : GAIA garde la requete en session."""
    global _op
    if _op is None:
        _op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    return _op


def _get(url, essais=4, timeout=120, binaire=False):
    for essai in range(essais):
        try:
            b = _ouvre().open(urllib.request.Request(url, headers=UA), timeout=timeout).read()
            return b if binaire else b.decode("iso-8859-1")
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500 and e.code != 429:
                raise
            if essai == essais - 1:
                raise
        except Exception:
            if essai == essais - 1:
                raise
        time.sleep(2 ** essai)


def _post(url, champs, timeout=120):
    d = urllib.parse.urlencode(champs).encode("iso-8859-1")
    return _ouvre().open(urllib.request.Request(url, data=d, headers=UA),
                         timeout=timeout).read().decode("iso-8859-1")


def _q(s):
    """Le libelle voyage DANS le chemin de l'URL : espaces et virgules encodes."""
    return urllib.parse.quote(s, safe="")


# ------------------------------------------------------------------- le formulaire
def themes():
    """Les themes servis par le portail : [(id, libelle)]."""
    t = _get(BASE + "/rechercheTheme")
    vus, out = set(), []
    for m in re.finditer(r'requeteConstructor/(\d+)/1/R/0/0[^>]*>\s*([^<]{3,80})', t):
        if m.group(1) not in vus:
            vus.add(m.group(1))
            out.append((m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()))
    return out


def _abecedaire(theme, t):
    """La page d'un rang, PLUS ses pages d'abecedaire quand il y en a un.

    ⛔ IGNORER L'ABECEDAIRE RENDAIT UNE LISTE TRONQUEE SANS LE DIRE. Mesure sur l'AD09 le
    19 septembre 2026 : la page d'entree rend **32 communes** et s'arrete a AXIAT, sans le
    moindre lien de pagination — le departement en a **346**. VEBRE, qu'on cherchait, en
    etait donc « absente », ce qui se serait lu « la commune n'est pas sur ce portail ».
    C'est le pire genre de defaut : pas une erreur, un silence.

    ⚠️ ET LES LETTRES NE SE DEVINENT PAS NON PLUS. Balayer A-Z donne 506 entrees pour
    346 communes, parce que les lettres SANS commune — K, W, X, Y, Z en Ariege —
    **retombent sur A** au lieu de rendre du vide. On suit donc les lettres OFFERTES par
    la page, et on dedoublonne sur l'identifiant.
    """
    pages = [t]
    lettres = sorted(set(re.findall(
        r'requeteConstructor/%s/(\d+)/R/([A-Z])/0' % theme, t)))
    for rang, L in lettres:
        pages.append(_get("%s/rechercheTheme/requeteConstructor/%s/%s/R/%s/0"
                          % (BASE, theme, rang, L)))
    return pages


def _offerts(theme, pages):
    """Tous les criteres offerts par ces pages, groupes par rang : {rang: [(id, lib)]}."""
    par = {}
    vus = set()
    for p in pages:
        for m in re.finditer(
                r'requeteConstructor/%s/(\d+)/A/([^/"]+)/([^"]*)"' % theme, p):
            r, ident = int(m.group(1)), m.group(2)
            if (r, ident) in vus:
                continue
            vus.add((r, ident))
            par.setdefault(r, []).append((ident, urllib.parse.unquote(m.group(3))))
    return par


def criteres(theme, *choisis):
    """Les valeurs offertes au rang suivant, apres avoir pose `choisis`.

    Rend [(id, libelle)] — et LE LIBELLE SE COPIE, il ne se reconstruit pas.

    ⛔ LE RANG NE SE COMPTE PAS, IL SE LIT. Cette fonction incrementait le rang d'un par
    critere pose ; l'AD61 saute du rang 1 au rang **3**, et la recherche au rang 2 ne
    trouvait alors rien — la fonction levait « le critere n'est pas offert » sur un portail
    qui repondait parfaitement. Le rang vit dans l'URL des liens offerts : on l'y prend.
    """
    _get(BASE + "/rechercheTheme")
    t = _get("%s/rechercheTheme/requeteConstructor/%s/1/R/0/0" % (BASE, theme))
    for ident in choisis:
        pages = _abecedaire(theme, t)
        trouve = None
        for p in pages:
            m = re.search(r'requeteConstructor/%s/(\d+)/A/%s/([^"]*)"' % (theme, ident), p)
            if m:
                trouve = (int(m.group(1)), m.group(2))
                break
        if not trouve:
            raise ValueError("le critere %s n'est offert a aucun rang de cette etape"
                             % ident)
        rang, lib = trouve
        t = _get("%s/rechercheTheme/requeteConstructor/%s/%d/A/%s/%s"
                 % (BASE, theme, rang, ident, _q(urllib.parse.unquote(lib))))
    par = _offerts(theme, _abecedaire(theme, t))
    # Le rang le plus haut est celui qu'on nous offre MAINTENANT ; les rangs inferieurs
    # sont le fil d'Ariane des choix deja poses.
    return par[max(par)] if par else []


def cherche(theme, *choisis, annee=None):
    """Pose les criteres, la date, et rend les reponses.

    Une reponse : {titre, cote, date, idUd, hierarchie} — `idUd` et `hierarchie` sont ce
    qu'il faut pour ouvrir la visionneuse.
    """
    _get(BASE + "/rechercheTheme")
    t = _get("%s/rechercheTheme/requeteConstructor/%s/1/R/0/0" % (BASE, theme))
    rang = 1
    for ident in choisis:
        # ⛔ LE RANG NE SE COMPTE PAS, IL SE LIT. Le module incrementait `rang` d'un par
        # critere pose ; l'AD61 saute du rang 1 au rang **3**, et la recherche du lien au
        # rang 2 ne trouvait alors rien — donc `criteres()` rendait une liste vide et
        # `cherche()` levait « le critere n'est pas offert », sur un portail qui repondait
        # parfaitement. Mesure le 19 septembre 2026.
        # ⛔ ET IL FAUT CHERCHER DANS L'ABECEDAIRE, PAS DANS LA SEULE PAGE D'ENTREE.
        # `criteres()` le faisait, `cherche()` non : la page d'entree de l'AD09 s'arrete a
        # AXIAT, donc TOUTE COMMUNE APRES LES PREMIERES LETTRES etait injoignable par
        # `cherche`. Le message d'erreur disait « le critere n'est offert a aucun rang »,
        # ce qui se lit « ce portail ne connait pas cette commune » — alors qu'on venait
        # de la lister avec `criteres`. Vu le 20 septembre 2026 sur VEBRE, que `criteres 1`
        # rendait et que `cherche 1 272123 ...` refusait.
        m = None
        for p in _abecedaire(theme, t):
            m = re.search(r'requeteConstructor/%s/(\d+)/A/%s/([^"]*)"' % (theme, ident), p)
            if m:
                break
        if not m:
            raise ValueError("le critere %s n'est offert a aucun rang de cette page"
                             % ident)
        rang = int(m.group(1))
        t = _get("%s/rechercheTheme/requeteConstructor/%s/%d/A/%s/%s"
                 % (BASE, theme, rang, ident, _q(urllib.parse.unquote(m.group(2)))))
        rang += 1
    if annee:
        t = _post("%s/rechercheTheme/requeteConstructor/%s/%d/A/0/0" % (BASE, theme, rang),
                  {"typeDate": "simple", "dateSimple": str(annee)})
        rang += 1
    t = _post("%s/rechercheTheme/requeteConstructor/%s/%d/T/0/0" % (BASE, theme, rang), {})

    # ⛔ ET GAIA PAGINE PAR VINGT. Le module ne lisait que la premiere page : Alencon
    # annonce **402 reponses** et il en rendait **20**, sans un mot. C'est exactement le
    # defaut qui a fait rendre 20 registres de Royan sur 85 a Archinoe pendant deux
    # semaines, refait a l'identique sur un autre moteur — d'ou la regle du carnet : un
    # client d'archives lit les pages JUSQU'A CE QU'UNE PAGE N'APPORTE PLUS RIEN DE NEUF,
    # et recompte contre le total annonce.
    annonce = None
    m = re.search(r"(\d+)\s*r[ée]ponses", t)
    if m:
        annonce = int(m.group(1))
    out, vus, offset = [], set(), 0
    while True:
        neuf = 0
        for m in re.finditer(r"calculHierarchieDocNum/(\d+)/([\d:]+)/", t):
            if m.group(1) in vus:
                continue
            vus.add(m.group(1))
            out.append({"idUd": m.group(1), "hierarchie": m.group(2)})
            neuf += 1
        # La cote et la date vivent dans deux <span> voisins. LE MOTIF CHERCHAIT « 11NUM »
        # EN DUR, ce qui ne vaut que pour un portail : les cotes de l'AD09 commencent par
        # `1NUM`, celles de l'AD61 par `3NUMEC`. On prend donc n'importe quelle cote.
        lignes = list(re.finditer(r"<span>([^<]{3,40})</span>\s*"
                                  r"<span[^>]*>((?:\d{4}|An [IVX]+)[^<]{0,24})</span>", t))
        for i, m in enumerate(lignes):
            j = len(out) - neuf + i
            if 0 <= j < len(out) and "cote" not in out[j]:
                out[j]["cote"], out[j]["date"] = m.group(1).strip(), m.group(2).strip()
        if not neuf or (annonce and len(out) >= annonce):
            break
        offset += 20
        try:
            t = _get("%s/rechercheTheme/paginer/%d" % (BASE, offset))
        except Exception:
            break
    if annonce and len(out) < annonce:
        # ON NE TAIT PAS UNE LECTURE PARTIELLE : un appelant qui croit avoir tout et n'a
        # qu'un tiers ecrit un negatif faux, et c'est la faute la plus chere du dossier.
        # La cause la plus frequente n'est pas la pagination : TOUTES LES LIGNES N'ONT PAS
        # DE VISIONNEUSE. On ne compte ici que celles qui en ont une — l'AD66 rend
        # 10 reponses pour 9 vignettes, l'AD61 402 pour 387. L'ecart se dit, il ne se tait
        # pas, et il ne se maquille pas non plus en « pagination cassee ».
        print("[gaia] ⚠️ %d reponses annoncees, %d avec visionneuse — l'ecart est "
              "normalement le nombre de lignes NON NUMERISEES ; le verifier avant de "
              "conclure a une pagination incomplete" % (annonce, len(out)),
              file=sys.stderr)
    return out


# ----------------------------------------------------------------- la visionneuse
def vues(id_ud, hierarchie):
    """LA LISTE COMPLETE DES VUES D'UN REGISTRE, en une requete.

    Elle est dans la page de la visionneuse, dans l'appel a `main({docs:[...]})`. Rend
    [{n, chemin, lettre, rcode, rvcode, cote}] — `n` etant le rang, 1 pour la premiere vue.
    """
    t = _get("%s/docnumViewer/calculHierarchieDocNum/%s/%s/1080/1920"
             % (BASE, id_ud, hierarchie))
    # ⚠️ CERTAINS REGISTRES REPETENT LEURS VUES, ET ON COMPTAIT LES DOUBLONS. Mesure sur
    # l'AD09 le 19 septembre 2026 : `1NUM/4E4665` rend **660 chemins pour 165 vues
    # uniques**, `1NUM/4E6140` 652 pour 163 — un facteur QUATRE exactement. Les vingt-neuf
    # autres registres de la meme commune sont propres, donc ca ne se voit pas tant qu'on
    # ne tombe pas dessus. Un registre de 165 vues annonce 660 : on en tire quatre fois
    # trop, et un « nombre de vues » ecrit dans une source devient faux.
    out, vus = [], set()
    for m in re.finditer(
            r'"chemin":"([^"]+)"[^{}]*?"ressourceCode":"([^"]*)"'
            r'[^{}]*?"ressourceVignette":"([^"]*)"', t):
        ch = m.group(1)
        if ch in vus:
            continue
        vus.add(ch)
        bouts = ch.split("@")
        out.append({"n": len(out) + 1, "chemin": ch,
                    "lettre": bouts[3] if len(bouts) > 4 else None,
                    "rcode": m.group(2), "rvcode": m.group(3)})
    return out


def sections(id_ud, hierarchie):
    """⭐ LES LETTRES D'UN REGISTRE ALPHABETIQUE, SANS TIRER UNE IMAGE.

    Rend {lettre: (premiere vue, derniere vue)}. Sur une table des successions, dont chaque
    lettre est ensuite CHRONOLOGIQUE par date de deces, ca reduit 144 vues a une dizaine.
    """
    d = {}
    for v in vues(id_ud, hierarchie):
        if not v["lettre"]:
            continue
        a, b = d.get(v["lettre"], (v["n"], v["n"]))
        d[v["lettre"]] = (min(a, v["n"]), max(b, v["n"]))
    return d


def image(vue, dest, taille=TAILLE_MAX, compr=100):
    """Tire une vue. `vue` est un element rendu par vues()."""
    # ⚠️ LE CHEMIN SE QUOTE : les cotes ne sont pas toutes sans espace. Celles de l'AD09
    # en portent — « 10 M 4_6@FRAD09_10M0004_0288.jpg » — et l'URL brute leve alors
    # `InvalidURL: URL can't contain control characters`, ce qui ressemble a un bug du
    # module et non a une cote. Le `@` separe les segments du chemin : il reste litteral.
    url = "%s/docnumserv/getImageVisualiseur/%s/%s/%s/N/%s/%s/200" % (
        BASE, vue["rcode"], vue["rvcode"],
        urllib.parse.quote(vue["chemin"], safe="@"), taille, compr)
    b = _get(url, timeout=240, binaire=True)
    if len(b) < 5000:
        raise ValueError("la taille %r ne rend pas une image (%d octets) -- T20 est le "
                         "maximum de ce serveur" % (taille, len(b)))
    os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
    io.open(dest, "wb").write(b)
    return dest, len(b)


def tirer(id_ud, hierarchie, registre, a, b, racine=NAS):
    """Tire les vues [a, b] DANS LE RANGEMENT DU NAS, pour que `nas.py` les lise ensuite.

    `registre` : « AD66 - Perpignan/TSA 1965 - 11NUM1304W553 ».
    """
    liste = {v["n"]: v for v in vues(id_ud, hierarchie)}
    dossier = os.path.join(racine, registre)
    faits = []
    for n in range(int(a), int(b) + 1):
        if n not in liste:
            continue
        p, taille = image(liste[n], os.path.join(dossier, "v%03d.jpg" % n))
        faits.append((n, p, taille))
        time.sleep(CADENCE)
    return faits


# --------------------------------------------------------------- ligne de commande
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    a = sys.argv[1:]
    # `--dept NN` REBRANCHE LE MODULE SUR UN AUTRE PORTAIL GAIA. Sans lui on reste sur le 66,
    # qui est le portail par lequel le moteur a ete ouvert -- mais rien ici ne lui appartient.
    if "--dept" in a:
        i = a.index("--dept")
        globals()["BASE"] = base(a[i + 1])
        del a[i:i + 2]
    if not a:
        print(__doc__.split("Ligne de commande :")[1].strip())
        sys.exit(0)

    if a[0] == "themes":
        for i, lib in themes():
            print("%4s  %s" % (i, lib))

    elif a[0] == "criteres":
        for i, lib in criteres(a[1], *a[2:]):
            print("%9s  %s" % (i, lib))

    elif a[0] == "cherche":
        an = a[-1] if a[-1].isdigit() and len(a[-1]) == 4 else None
        crit = a[2:-1] if an else a[2:]
        for r in cherche(a[1], *crit, annee=an):
            print("  %s  %s  idUd=%s  hierarchie=%s"
                  % (r.get("cote", "?"), r.get("date", "?"), r["idUd"], r["hierarchie"]))

    elif a[0] == "vues":
        v = vues(a[1], a[2])
        print("%d vues" % len(v))
        for lettre, (d, f) in sorted(sections(a[1], a[2]).items()):
            print("  %-3s vues %3d a %3d" % (lettre, d, f))

    elif a[0] == "tirer":
        for n, p, t in tirer(a[1], a[2], a[3], a[4], a[5]):
            print("v%03d  %8d octets  %s" % (n, t, p))

    else:
        print(__doc__.split("Ligne de commande :")[1].strip())
