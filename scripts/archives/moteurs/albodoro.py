# -*- coding: utf-8 -*-
"""ALBO D'ORO — les 530 000 militaires italiens morts en 1915-1918 · ASP.NET WebForms.

    python albodoro.py commune Valvasone
    python albodoro.py nom PEDEROD
    python albodoro.py mot ComuneNascita VALVASON      # le vocabulaire exact
    python albodoro.py fiche 123456

CE QUE C'EST, ET CE N'EST PAS UN INDEX DE BENEVOLES. L'Albo d'Oro est la liste OFFICIELLE
des militaires italiens morts pour la patrie, publiee en 28 volumes de 1924 a 1954 par le
Ministero della Difesa et mise en ligne en entier. Elle est exhaustive pour ceux que
l'armee a reconnus morts — donc un zero, ici, veut dire quelque chose, contrairement a
Geneanet ou a FamilySearch.

LE MOTEUR : de l'ASP.NET WebForms classique, reconnaissable a ses `.aspx` et a ses trois
champs caches `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, `__EVENTVALIDATION`. On fait un GET de
la page de recherche, on en extrait les trois, et on les REPOSTE avec le formulaire, en
gardant les cookies de session. Aucun WAF, aucun navigateur.
*(A ne pas confondre avec Arolsen, qui est de l'ASP.NET `.asmx` : la ce sont des services
web JSON, ici un POST de formulaire.)*

────────────────────────────────────────────────────────────────────────────────────────
LES DEUX PIEGES, PAYES LE 7 SEPTEMBRE 2026

⚠️ **LES DEUX SELECTS DE MOIS ONT « 0 » POUR VALEUR VIDE, PAS LA CHAINE VIDE.** Envoyer
`tMeseNasc=''` ou `tMeseMorte=''` rend un **HTTP 500 sec**, sans message. Les autres selects
(`tAlbo`, `tReg`, `tRegAtt`) acceptent bien la chaine vide. Une heure perdue si on l'ignore.

⚠️ **LA RECHERCHE PAR NOM EST UN PREFIXE, PAS UNE EGALITE.** « MIGOT » rend treize fiches,
toutes MIGOTTI ou MIGOTTO, **aucune MIGOT**. Donc **un zero strict se lit dans la LISTE, pas
dans le COMPTE** : le compte affiche « 13 nominativi » alors que la reponse a la question
posee est zero. `nom()` rend donc les fiches, et `exact=True` filtre.
Inversement c'est une chance sur un patronyme a graphies flottantes : « PEDEROD » attrape
PEDERODA et PEDERODI d'un coup.

⭐ **LE RACCOURCI QUI MARCHE : CHERCHER PAR COMMUNE DE NAISSANCE, ET LIRE TOUTE LA LISTE.**
Sur un village elle tient en une page — Valvasone rend 40 morts avec le patronyme du pere,
la classe, le grade, l'unite, l'annee, le lieu et la cause de la mort. C'est la facon de
repondre a « un tel du village est-il mort a la guerre ? » quand on n'a pas son nom, et ca
ne coute qu'une requete.

⚠️ ET LE LIBELLE SE LIT, IL NE SE TAPE PAS. `mots()` interroge le vocabulaire du portail :
« VALVASON » rend « Valvasone », « VITO » rend « Vito D'Asio » avec sa majuscule et son
apostrophe. A faire AVANT toute recherche par commune.
"""
import html as H
import http.cookiejar
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tls  # noqa: F401

BASE = "https://www.cadutigrandeguerra.it"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

# LES DEUX QUI VALENT « 0 » ET NON LA CHAINE VIDE. C'est tout le piege du HTTP 500.
MOIS = ("tMeseNasc", "tMeseMorte")

CHAMPS = ("tNome", "tNascita", "tNascitaTH", "tProv", "tReg", "tNascitaAtt", "tProvAtt",
          "tRegAtt", "tAnnoNasc", "tMeseNasc", "tggNasc", "tAnnoMorte", "tMeseMorte",
          "tGGMorte", "tGrado", "tReparto", "tDistretto", "tDecora", "tLuogoMorte",
          "tCausaMorte", "tAlbo")

_op = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def _ouvre(u, donnees=None):
    d = urllib.parse.urlencode(donnees, encoding="utf-8").encode() if donnees else None
    h = dict(UA)
    if d:
        h["Content-Type"] = "application/x-www-form-urlencoded"
    r = _op.open(urllib.request.Request(u, data=d, headers=h), timeout=120)
    return r.read().decode("utf-8", "replace")


def mots(champ, terme):
    """Le vocabulaire exact du portail pour un champ. A INTERROGER AVANT DE TAPER UN LIBELLE.

    `champ` : ComuneNascita, ProvNascitaOrig, ComuneNascitaAttuale, ProvNascitaAtt, Grado,
    GradoUniformato, Reparto, RepartoUniformato, Distretto, Decorazioni, LuogoMorte,
    CausaMorte, CausaMorteUniformato.
    """
    u = "%s/GetValoriCampo.ashx?%s" % (BASE, urllib.parse.urlencode(
        {"Campo": champ, "q": terme}))
    t = _ouvre(u).strip()
    try:
        d = json.loads(t)
    except ValueError:
        return [l.strip() for l in t.splitlines() if l.strip()]
    if isinstance(d, dict):
        d = d.get("suggestions") or d.get("d") or []
    # Le service rend des objets {"Key": ..., "Value": ...} : c'est la VALEUR qu'on
    # reposte, et la rendre telle quelle ferait taper un dict dans un formulaire.
    return [x.get("Value", x.get("Key")) if isinstance(x, dict) else x for x in d]


def _etat(h):
    """Les trois champs caches de WebForms."""
    e = {}
    for n in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
        m = re.search(r'id="%s"[^>]*value="([^"]*)"' % n, h) or \
            re.search(r'name="%s"[^>]*value="([^"]*)"' % n, h)
        if m:
            e[n] = H.unescape(m.group(1))
    return e


def cherche(**criteres):
    """Un POST du formulaire. Rend [fiches]. Les critere inconnus sont refuses tout de
    suite : un champ invente serait ignore en silence, et on lirait un resultat faux."""
    for k in criteres:
        if k not in CHAMPS:
            raise SystemExit("champ inconnu : %s — connus : %s" % (k, ", ".join(CHAMPS)))
    h = _ouvre(BASE + "/CercaNome.aspx")
    d = _etat(h)
    if "__VIEWSTATE" not in d:
        raise SystemExit("__VIEWSTATE introuvable — la page a change")
    for c in CHAMPS:
        # LES MOIS VALENT « 0 » A VIDE. Tout le reste prend la chaine vide.
        d[c] = criteres.get(c, "0" if c in MOIS else "")
    d["btCerca"] = "CERCA"
    return lit(_ouvre(BASE + "/CercaNome.aspx", d))


# Les en-tetes du tableau, relevees sur le portail le 19 septembre 2026.
COLONNES = ("nom", "classe", "commune_actuelle", "grade", "unite", "annee_mort",
            "lieu_mort", "cause_mort")


def lit(h):
    """Les lignes du tableau de resultats.

    ⚠️ L'IDENTIFIANT N'EST PAS UN NOMBRE : c'est un jeton chiffre deja encode pour l'URL
    (`id=6%2fKY2bjdbhPMNox...`). Une premiere version lisait `id=(\\d+)` et rendait « 6 »
    pour les quarante morts de Valvasone — quarante fiches pointant toutes sur la meme
    page. On garde le jeton TEL QUEL, sans le decoder : il se recolle dans l'URL.
    Et les deux liens ne portent pas le meme jeton — l'image et la fiche sont distinctes.
    """
    out = []
    for tr in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", h):
        img = re.search(r"""ShowImg\.aspx\?id=([^"'&\s]+)""", tr)
        det = re.search(r"""DettagliNominativi\.aspx\?id=([^"'&\s]+)""", tr)
        if not (img or det):
            continue
        cel = [re.sub(r"\s+", " ", H.unescape(re.sub(r"(?s)<[^>]+>", " ", c))).strip()
               for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)]
        cel = [c for c in cel if c and c not in ("Mostra Pagina", "Visualizza")]
        x = dict(zip(COLONNES, cel))
        x["cellules"] = cel
        x["id"] = det.group(1) if det else None
        x["fiche"] = ("%s/DettagliNominativi.aspx?id=%s" % (BASE, det.group(1))
                      if det else None)
        x["image"] = "%s/ShowImg.aspx?id=%s" % (BASE, img.group(1)) if img else None
        out.append(x)
    return out


def commune(nom_exact, **autres):
    """⭐ LE RACCOURCI : tous les morts nes dans une commune. `nom_exact` se prend par
    `mots('ComuneNascita', ...)`, jamais tape de memoire."""
    return cherche(tNascita=nom_exact, **autres)


def nom(prefixe, exact=False, **autres):
    """⚠️ C'EST UN PREFIXE. `exact=True` ne garde que les fiches dont le nom commence par un
    mot egal au prefixe — sans quoi « MIGOT » rend treize MIGOTTI."""
    r = cherche(tNome=prefixe, **autres)
    if not exact:
        return r
    p = prefixe.strip().upper()
    return [x for x in r
            if x["cellules"] and re.match(r"^%s\b" % re.escape(p),
                                          x["cellules"][0].upper())]


def fiche(ident):
    """La fiche complete : date de naissance AU JOUR, district de recrutement, date de mort
    au jour, page et sub de l'Albo. Le tableau de resultats, lui, ne donne que l'ANNEE.

    `ident` est le jeton rendu par `lit()`, DEJA ENCODE pour l'URL : on le recolle tel quel.
    Le decoder puis le reposter casse la signature et rend une page vide.

    La page est un tableau de lignes `<tr><td><span>Libelle:</span></td>
    <td><span id="lbl...">valeur</span></td></tr>` : c'est la deuxieme cellule qui porte la
    valeur, et un decoupage a plat du texte les perd toutes.
    """
    h = _ouvre("%s/DettagliNominativi.aspx?id=%s" % (BASE, ident))
    d = {}
    for tr in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", h):
        tds = re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)
        if len(tds) < 2:
            continue
        lib = re.sub(r"\s+", " ", H.unescape(
            re.sub(r"(?s)<[^>]+>", " ", tds[0]))).strip().rstrip(":").strip()
        val = re.sub(r"\s+", " ", H.unescape(
            re.sub(r"(?s)<[^>]+>", " ", tds[1]))).strip()
        if lib and val:
            d[lib] = val
    return d


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    av = sys.argv[1:]
    if not av:
        print(__doc__.split("\n\n")[1])
        sys.exit(1)
    if av[0] == "mot":
        for v in mots(av[1], av[2]):
            print(" ", v)
    elif av[0] == "commune":
        r = commune(av[1])
        print("%d morts nes a %s\n" % (len(r), av[1]))
        for x in r:
            print("%-8s %s" % (x["id"], " · ".join(x["cellules"])[:130]))
    elif av[0] == "nom":
        r = nom(av[1], exact="--exact" in av)
        print("%d fiches pour le prefixe « %s »%s\n"
              % (len(r), av[1], " (filtrees a l'exact)" if "--exact" in av else ""))
        for x in r:
            print("%-8s %s" % (x["id"], " · ".join(x["cellules"])[:130]))
        if r and "--exact" not in av:
            print("\n⚠️ LE NOM EST UN PREFIXE : ce compte n'est pas une reponse. "
                  "Relire la liste, ou `--exact`.")
    elif av[0] == "fiche":
        for k, v in fiche(av[1]).items():
            print("  %-28s %s" % (k, v))
    else:
        raise SystemExit("actions : commune | nom | mot | fiche")
