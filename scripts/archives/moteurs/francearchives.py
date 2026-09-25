# -*- coding: utf-8 -*-
"""FRANCEARCHIVES — le portail national, et la porte de service des portails defendus.

CE MODULE EXISTE PARCE QUE LA RECETTE ETAIT ECRITE ET LE CODE NON. La fiche
`references/portails.md` decrit depuis le 18 septembre 2026 comment franchir le controle
anti-robot et quels parametres tuent silencieusement une requete — et chaque session le
refaisait a la main, en urllib, dans un one-liner. C'est exactement la recette dupliquee
que `scripts/archives/` existe pour empecher.

CE QU'ON Y CHERCHE :

    - L'INDEX NOMINATIF DES DECRETS DE NATURALISATION des Archives nationales. Une notice
      porte date et lieu de naissance, profession, residence, epouse, enfants, et LE NUMERO
      DE DOSSIER (« 4092 X 29 ») qui ouvre le carton a Pierrefitte.
      ⚠️ IL N'INDEXE QUE 1883-1898, 1913-1927 ET 1929-1930. Un zero sur 1931-1948 ne veut
      rien dire du tout : ces annees sont numerisees et n'ont jamais ete indexees.
    - Les inventaires de presque toutes les AD, y compris ceux qu'un WAF cache.
    - Le Fichier central de la Surete nationale (19940469/...), nominatif sur des etrangers
      surveilles dans les annees 1930.
    - La base Leonore, les dossiers AC 21 P de Caen.

LES TROIS PIEGES, ET LE DEUXIEME REND UN FAUX ZERO PARFAITEMENT CREDIBLE :

    1. LA PREMIERE REPONSE N'EST PAS LA PAGE. C'est 242 octets de controle anti-robot,
       ecrits en clair : `window.location.href='/redirect_<jeton>/fr/search?q=...'`. On lit
       le jeton, on redemande cette URL-la sur le MEME opener, et la page vient. La fiche du
       SHD en avait conclu « vrai Chrome obligatoire » — sur la taille de la reponse, sans
       l'avoir lue.
    2. N'AJOUTER AUCUN PARAMETRE « RAISONNABLE ». `sort=`, `per_page=50`, `es_cw_etypes=`
       vides font repondre « Les parametres de la requete ne donnent aucun resultat » sur
       une requete qui rend 21 documents sans eux. Et `es_publisher=...` rend « Aucun
       resultat » alors que la facette de la meme page en annonce deux. UNIQUEMENT `q` et
       `page`, on trie a l'oeil.
    3. ⛔ → ✅ CE MODULE A DESACTIVE LA VERIFICATION TLS PENDANT UNE JOURNEE, ET C'ETAIT UN
       FAUX DIAGNOSTIC. Il portait ici « le magasin de certificats de la machine refuse
       francearchives.gouv.fr — lecture seule sur un portail public, contexte non verifie,
       assume ». Le site n'y etait pour rien : c'est le magasin de racines de Windows servi
       a Python qui porte une racine perimee, et il refusait aussi wikipedia, data.gouv.fr
       et culture.gouv.fr — tous chez Let's Encrypt. **Un certificat qui ne se verifie pas
       est un probleme a corriger, pas a contourner** : `scripts/archives/tls.py` le repare
       pour tout le processus, et la verification est retablie ici.

ET LA REGLE QUI DECIDE DE CE QU'UN ZERO VAUT : un moteur d'inventaire lit des DESCRIPTIONS,
pas des dossiers. Une serie decrite « dossiers individuels classes par ordre alphabetique »
ne rendra jamais un patronyme. Regarder a quelle maille l'inventaire descend avant de
conclure.

Ligne de commande :

    python francearchives.py cherche "Peresson"
    python francearchives.py cherche "Migot" --pages 3
    python francearchives.py naturalises "Pediroda"      # ne garde que les decrets
    python francearchives.py notice /fr/facomponent/xxxx # le detail d'une notice
"""
import sys, io, os, re, ssl, json, time
import urllib.request, urllib.parse, urllib.error
import http.cookiejar

# La verification TLS de cette machine est reparee par `scripts/archives/tls.py` :
# le magasin de racines de Windows porte une racine perimee, et tous ces portails sont
# chez Let's Encrypt. Un import suffit, il agit sur tout le processus.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tls  # noqa: F401,E402

BASE = "https://francearchives.gouv.fr"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}
CADENCE = 0.5

_opener = None


def _ouvre():
    """Un opener a cookies, AVEC verification TLS — voir le piege 3 de l'en-tete.

    Le contexte par defaut suffit parce que `tls.py`, importe plus haut, l'a repare pour tout
    le processus. Si un CERTIFICATE_VERIFY_FAILED revient un jour, la reponse n'est pas de
    remettre CERT_NONE : c'est `python scripts/archives/tls.py reparer`.
    """
    global _opener
    if _opener is None:
        _opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    return _opener


def _get(url, essais=4, timeout=60):
    """Un GET qui suit le controle anti-robot ecrit en clair dans la reponse."""
    op = _ouvre()
    for essai in range(essais):
        try:
            b = op.open(urllib.request.Request(url, headers=UA), timeout=timeout).read()
            t = b.decode("utf-8", "replace")
            m = re.search(r"window\.location\.href\s*=\s*'([^']+)'", t)
            if m and len(t) < 4000:
                url2 = urllib.parse.urljoin(BASE, m.group(1))
                time.sleep(0.3)
                b = op.open(urllib.request.Request(url2, headers=UA), timeout=timeout).read()
                t = b.decode("utf-8", "replace")
            return t
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500 and e.code != 429:
                raise
            if essai == essais - 1:
                raise
        except Exception:
            if essai == essais - 1:
                raise
        time.sleep(2 ** essai)


def _detague(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
          .replace("&eacute;", "é").replace("&egrave;", "è").replace("&agrave;", "à")
          .replace("&ccedil;", "ç").replace("&ocirc;", "ô").replace("&ecirc;", "ê"))
    return re.sub(r"\s+", " ", s).strip()


def _total(t):
    """Le nombre de resultats annonce.

    ⚠️ LE MOT « resultats » FIGURE DANS L'AIDE DE LA PAGE, ET IL Y PORTE UN NOMBRE. Un
    `re.search` sur « N resultats » rend **10 000** sur une page qui n'a rien trouve, parce
    que l'aide dit « Il est possible d'exporter jusqu'a 10 000 resultats ». On a lu « 10000
    lignes annoncees, 0 lues » pour PEDIRODA avant de s'en apercevoir. Donc : le zero se
    reconnait a SA phrase, et le compte se lit dans le `<span>` du titre, nulle part
    ailleurs.

    ET LE SEUL CONTROLE QUI NE MENT PAS : comparer le total a celui d'une requete SANS
    filtre. La base de noms sans filtre annonce 430 992 353 — si une requete filtree rend
    ce nombre-la, le filtre n'a pas filtre.
    """
    m = re.search(r"<span>\s*([\d \xa0 ]*\d)\s*r[ée]sultats?\s*</span>", t)
    if m:
        return int(re.sub(r"\D", "", m.group(1)))
    # ET LA PHRASE DU ZERO FIGURE AUSSI DANS L'AIDE DE LA PAGE : on ne la lit qu'apres
    # avoir cherche le compte, sinon une requete a 157 reponses est declaree vide.
    return 0 if re.search(r"Aucun r(?:&eacute;|é)sultat", t) else None


CARTE = re.compile(r'<div class="fr-card [^"]*fa-sr-card">(.*?)(?=<div class="fr-card '
                   r'|<footer|\Z)', re.S)
TITRE = re.compile(r'<h3 class="fr-card__title">\s*<a href="([^"]+)"[^>]*>(.*?)</a>', re.S)
PROP = re.compile(r'props--label">(.*?)</span>.*?props--value[^"]*">(.*?)</span>', re.S)
BADGE = re.compile(r'<p class="fr-badge">(.*?)</p>', re.S)


def _cartes(t):
    """Les fiches d'une page de resultats — meme gabarit pour la recherche generale et
    pour la base de noms."""
    out = []
    for m in CARTE.finditer(t):
        bloc = m.group(1)
        mt = TITRE.search(bloc)
        if not mt:
            continue
        d = {"titre": _detague(mt.group(2)), "url": mt.group(1)}
        for lab, val in PROP.findall(bloc):
            d[_detague(lab)] = _detague(val)
        b = BADGE.search(bloc)
        if b:
            d["type"] = _detague(b.group(1))
        d["texte"] = _detague(bloc)[:900]
        out.append(d)
    return out


def _pages(url, pages):
    total, out = None, []
    for p in range(1, pages + 1):
        t = _get(url + ("&page=%d" % p if p > 1 else ""))
        if total is None:
            total = _total(t)
        lot = _cartes(t)
        if not lot:
            break
        out += lot
        time.sleep(CADENCE)
    vus, net = set(), []
    for d in out:
        if d["url"] in vus:
            continue
        vus.add(d["url"])
        net.append(d)
    return total, net


def cherche(termes, pages=1):
    """Cherche dans les INVENTAIRES. Rend (total, [notices]).

    Une notice porte titre, url, et les proprietes affichees par la fiche — Cote, Periode,
    Fonds, Lieu de conservation. C'est la que se lisent la date d'un decret et le numero de
    dossier BB/11.
    """
    if not isinstance(termes, str):
        termes = " ".join(termes)
    return _pages("%s/fr/search?q=%s" % (BASE, urllib.parse.quote(termes)), pages)


def noms(nom, prenom=None, lieu=None, an_min=None, an_max=None, pages=1):
    """⭐ LA BASE DE NOMS — 430 992 353 lignes nominatives versees par les AD.

    C'EST UN AUTRE MOTEUR QUE `cherche()`, SUR UNE AUTRE URL, AVEC D'AUTRES CHAMPS, et il
    ne se devine pas : `?q=Peresson` sur `/fr/basedenoms` rend LES 430 MILLIONS DE LIGNES —
    le parametre est ignore en silence et la page ressemble parfaitement a un resultat.
    Les champs sont `es_names`, `es_forenames`, `es_locations`, `es_date_min`,
    `es_date_max`, et ils se lisent sur le formulaire.

    Chaque fiche porte un type dans un badge : « Recensement de la population », « Registre
    matricule », « Etat civil », « Naturalisation »... C'est un INDEX, pas un fonds : ce que
    des AD ont verse, jamais la totalite des registres. Un zero n'y prouve rien.
    """
    p = []
    if nom:
        p.append(("es_names", nom))
    if prenom:
        p.append(("es_forenames", prenom))
    if lieu:
        p.append(("es_locations", lieu))
    if an_min:
        p.append(("es_date_min", str(an_min)))
    if an_max:
        p.append(("es_date_max", str(an_max)))
    return _pages("%s/fr/basedenoms?%s" % (BASE, urllib.parse.urlencode(p)), pages)


def noms_csv(nom, prenom=None, lieu=None, an_min=None, an_max=None):
    """⭐⭐ LE MEME FONDS, MAIS PAR SON EXPORT — et c'est par la qu'il faut passer.

    La page de resultats est paginee par vingt et ne montre pas tout ; la base sert le
    MEME filtre en CSV, dix colonnes, jusqu'a 10 000 lignes, en une requete :

        URL de FranceArchives, Nom, Prenoms, PROFESSION, Type de document, Date du
        document, Lieu du document, Cote, LIEN VERS LE DOCUMENT NUMERISE, Lieu de
        conservation

    La profession et le lien vers l'image ne sont NULLE PART sur la page de resultats.
    Rend une liste de dict, entetes en clef.
    """
    import csv
    p = [(k, v) for k, v in (("es_names", nom), ("es_forenames", prenom),
                             ("es_locations", lieu),
                             ("es_date_min", an_min and str(an_min)),
                             ("es_date_max", an_max and str(an_max))) if v]
    t = _get("%s/fr/basedenomsexport/export.csv?%s" % (BASE, urllib.parse.urlencode(p)))
    return list(csv.DictReader(io.StringIO(t)))


DECRET = re.compile(r"d[ée]cret du (\d{1,2}[^,;.]{2,20}\d{4})", re.I)
DOSSIER = re.compile(r"\b(\d{3,6})\s*[Xx]\s*(\d{2})\b")


def naturalises(nom, pages=2):
    """Ne garde des resultats que ce qui ressemble a un decret de naturalisation.

    ⚠️ RAPPEL QUI DECIDE DE TOUT : l'index ne couvre que 1883-1898, 1913-1927 et 1929-1930.
    Un zero ne dit RIEN sur 1899-1912, 1928 et 1931-1948.
    """
    total, res = cherche(nom, pages=pages)
    gardes = []
    for d in res:
        t = (d.get("texte") or "") + " " + d["titre"]
        if "naturalisation" in t.lower() or DECRET.search(t) or DOSSIER.search(t):
            d["decret"] = (DECRET.search(t).group(1) if DECRET.search(t) else None)
            d["dossier"] = ("%s X %s" % DOSSIER.search(t).groups()
                            if DOSSIER.search(t) else None)
            gardes.append(d)
    return total, gardes


def notice(chemin):
    """Le detail d'une notice, en texte. `chemin` : l'URL rendue par cherche()."""
    url = chemin if chemin.startswith("http") else urllib.parse.urljoin(BASE, chemin)
    t = _get(url)
    m = re.search(r"<main.*?</main>", t, re.S) or re.search(r"<body.*?</body>", t, re.S)
    return _detague(m.group(0) if m else t)


# ------------------------------------------------------------------ ligne de commande
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    a = sys.argv[1:]
    if not a:
        print(__doc__.split("Ligne de commande :")[1].strip())
        sys.exit(0)
    cmd = a[0]
    pages = 1
    if "--pages" in a:
        pages = int(a[a.index("--pages") + 1])
    mots = [x for x in a[1:] if not x.startswith("--") and not x.isdigit()]

    if cmd == "cherche":
        total, res = cherche(mots, pages=pages)
        print("%s résultat(s) annoncé(s), %d notice(s) lue(s)\n"
              % (total if total is not None else "?", len(res)))
        for d in res:
            print("• %s\n  %s\n  %s\n"
                  % (d["titre"], d["url"],
                     " · ".join("%s : %s" % (k, v) for k, v in d.items()
                                if k not in ("titre", "url", "texte"))))

    elif cmd == "noms":
        prenom = a[a.index("--prenom") + 1] if "--prenom" in a else None
        lieu = a[a.index("--lieu") + 1] if "--lieu" in a else None
        mots = [x for x in mots if x not in (prenom, lieu)]
        total, res = noms(" ".join(mots), prenom=prenom, lieu=lieu, pages=max(pages, 1))
        print("%s ligne(s) annoncée(s), %d lue(s)  "
              "— sans filtre la base en annonce 430 992 353\n"
              % (total if total is not None else "?", len(res)))
        for d in res:
            print("• %-34s %-26s %-34s %s"
                  % (d["titre"][:34], d.get("type", "")[:26],
                     d.get("Lieu du document", "")[:34], d.get("Date du document", "")))

    elif cmd == "naturalises":
        total, res = naturalises(" ".join(mots), pages=max(pages, 2))
        print("%s résultat(s) annoncé(s), %d ressemblent à un décret\n"
              % (total if total is not None else "?", len(res)))
        for d in res:
            print("• %s\n  décret : %s | dossier : %s\n  %s\n  %s\n"
                  % (d["titre"], d.get("decret"), d.get("dossier"), d["url"],
                     (d.get("texte") or "")[:400]))
        print("⚠️ L'index ne couvre que 1883-1898, 1913-1927 et 1929-1930 — "
              "un zéro ne dit rien sur 1899-1912, 1928 et 1931-1948.")

    elif cmd == "notice":
        print(notice(a[1])[:6000])

    else:
        print(__doc__.split("Ligne de commande :")[1].strip())
