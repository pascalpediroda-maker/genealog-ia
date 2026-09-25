# -*- coding: utf-8 -*-
"""Moteur ARCHINOE O2 / OXYGENE — AD62 (Pas-de-Calais), et tout portail qui tourne dessus.

    fonds(base)                  -> les douze fonds interrogeables du portail
    champs(base, fonds)          -> le FORMULAIRE de ce fonds, lu et non devine
    lieux(base, fonds, motif)    -> les libelles EXACTS des lieux
    registres(base, fonds, lieu) -> la liste, TOUTES PAGES LUES, plafond de 100 franchi
    vues(base, fonds, ident)     -> les chemins des vues d'un registre, dans l'ordre
    tirer(base, fonds, ident, d) -> les images sur le disque, v001.jpg, v002.jpg, ...

    python archinoe_o2.py 62 fonds
    python archinoe_o2.py 62 champs etat_civil
    python archinoe_o2.py 62 lieux etat_civil bours
    python archinoe_o2.py 62 registres etat_civil "Bours (Pas-de-Calais, France)"
    python archinoe_o2.py 62 registres etat_civil "Calais (Pas-de-Calais, France)"
    python archinoe_o2.py 62 vues etat_civil 393535994
    python archinoe_o2.py 62 tirer etat_civil 393535994 "<archives>/AD62 - Bours/BMS 1693-1751" 1 5

CE N'EST PAS L'ARCHINOE DE L'AD17, ET `archinoe.py` NE SERT AUCUNE DE CES ROUTES. Le
module de l'AD17 parle a la generation `/v2/<code>/` : `registre.html`, ses selecteurs en
cascade, `registre_liste.html`. Ici `/v2/ad62/registre.html` n'existe pas — la recherche
est une application ExtJS servie sous `/console/`, en PHP, dont les formulaires sont
decrits un par un cote serveur.

MAIS LA VISIONNEUSE, ELLE, EST BIEN L'ANCIENNE. C'est la trouvaille qui a fait ce module en
une soiree plutot qu'en trois : le bouton « Consulter » de la grille de resultats appelle
`afficheImage(id)`, et cette fonction-la fait

    window.open('/v2/ad62/visualiseur/' + fonds + '.html?id=' + id);

c'est-a-dire EXACTEMENT la page que `archinoe.py` sait lire, avec ses `data-original` et
son proxy `/v2/images/genereImage.html`. Le portail est donc un O2 pose sur un v2 :
recherche neuve, images anciennes. LE PREFIXE `/v2/<code>/` SE LIT DANS CETTE FONCTION, il
ne se reconstruit pas depuis le numero du departement — un portail qui en sert deux (des
fonds sur `ad62`, d'autres ailleurs) casserait la convention sans prevenir.

--------------------------------------------------------------------- LES PIEGES PAYES

1. LE MUR F5 / SHAPE SECURITY, ET IL NE COUVRE PAS TOUT LE SITE — C'EST CE QUI TROMPE.
   `/`, `/console/` et `/v2/images/genereImage.html` repondent a une requete Python
   ordinaire ; `/console/ir_seriel*.php` et `/v2/ad62/visualiseur/*.html` rendent 5 700
   octets de defi JavaScript (scripts en `/TSPD/`, ligne « Your support ID is »). Une
   session qui commence par la racine croit donc etre passee, et se prend le defi trois
   requetes plus loin. UN VRAI CHROME LE FRANCHIT EN 2 SECONDES ; ce module l'ouvre tout
   seul, ramasse les cookies et les verse dans son pot Python.

2. LES COOKIES DE CE MUR SE PERIMENT EN QUELQUES MINUTES, ET EN SILENCE. Un jeu amorce a
   17 h 21 rendait le defi a 17 h 31 — sans erreur HTTP, sans 403 : un HTTP 200 de
   5 752 octets, que du code qui cherche une grille de resultats lirait comme « zero
   registre ». C'est la faute que ce module refuse par construction : `_get()` RECONNAIT
   le defi dans la reponse, reamorce et rejoue une fois. Un negatif ne doit jamais pouvoir
   sortir d'une page de pare-feu.

3. LE NOM D'UN CHAMP NE SE TRANSPOSE PAS D'UN FONDS A L'AUTRE, ET LA PREUVE EST DANS LE
   PORTAIL. Le lieu de l'etat civil est `f_0_0` ; sur le CADASTRE, `f_0_0` est « Fonds ou
   collection » et le lieu est `f_0_1`. Poster un nom de commune dans `f_0_0` du cadastre
   ne leve aucune erreur : ca rend les plans du departement entier, triés, avec une
   colonne « Lieu » pleine de noms plausibles. C'est le piege `REch_commune` de l'AD16,
   dans un autre portail. DONC : `champs()` LIT le formulaire — `<label for='f_0_N'>` —
   et `registres()` choisit le champ dont le libelle est « Lieu » ou « Commune ».

4. « TROP DE RESULTATS TROUVES - (100 RESULTATS AFFICHES) » EST UN PLAFOND, PAS UN TOTAL.
   Calais l'atteint ; la pagination s'arrete a la page 3 et la page 4 rend zero ligne en
   continuant d'afficher le meme message. LE PLAFOND SE FRANCHIT PAR FENETRES D'ANNEES :
   le formulaire filtre « Entre a et b » en CHEVAUCHEMENT (un registre 1693-1751 sort pour
   « entre 1694 et 1695 »), donc on decoupe l'intervalle en deux tant qu'une moitie
   plafonne, et on reunit les lignes en dedoublonnant sur (cote, dates, id). Verifie : le
   filtre filtre vraiment — Calais rend 14 registres sur 1793-1802 contre le plafond sans
   bornes, et Bours 5 sur les seules naissances contre 22 en tout.

5. LES RESULTATS ONT DEUX ONGLETS, ET CELUI QUI PORTE LA GRILLE CHANGE AVEC LE FONDS.
   `&r=0` est « Details », `&r=1` est « Liste ». A l'ETAT CIVIL, la grille est en `r=1` :
   22 lignes sur Bours contre 3 en `r=0`, qui pagine ses fiches par trois. Au RECENSEMENT
   et aux TABLES, `r=1` rend TRENTE-DEUX OCTETS ET AUCUNE LIGNE — la grille est en `r=0`,
   et une commune qui a 28 recensements serait rendue « 0 registre » sans un mot. Le
   module DEMANDE LES DEUX a la page 0 et garde celui qui rend le plus de lignes.
   La pagination se compte a partir de zero, et on lit jusqu'a ce qu'une page n'apporte
   plus rien de neuf, en RECOMPTANT CONTRE LE TOTAL ANNONCE — la lecon des 20 registres
   de Royan sur 85.

6. LE TOTAL N'EST PAS TOUJOURS UN NOMBRE : a un seul resultat, le portail ecrit « Un
   resultat trouve », sans chiffre. Une expression qui cherche `(\\d+) resultat` rend alors
   None, et un controle « annonce == lu » passe a la trappe sans bruit.

7. UNE LIGNE SANS `afficheImage` N'EST PAS UNE LIGNE RATEE : c'est un registre « Non
   numerise ». Bours en annonce 22 et n'en donne que 21 a lire, et l'ecart est un fait du
   fonds, pas un bug de lecture. Le module rend les 22 lignes, `id` a None pour celle-la,
   et le dit.

8. LE `sid` DES AUTOCOMPLETIONS EST LE PHPSESSID, RIEN D'AUTRE. La fiche du portail disait
   « il se lit dans les appels autocomplete({serviceUrl:...}) du HTML » — c'est vrai, et
   c'est la meme valeur que le cookie. Un `sid` invente ne rend pas une liste vide : il
   leve un HTTP 500, ce qui est une bonne nouvelle (un endpoint qui se tait serait pire).

9. L'AUTOCOMPLETION REMBOURRE SA REPONSE. `query=Calais` rend six libelles qui contiennent
   « Calais »… puis « Ablain-Saint-Nazaire », « Ablainzevelle », « Acheville » — le debut
   du referentiel, jusqu'a une centaine d'entrees. Filtrer sur le motif est donc
   obligatoire, sinon on retient un lieu qu'on n'a pas cherche. ET IL EXISTE MIEUX : le
   bouton « Liste » du formulaire ouvre `ir_ead_liste_seriel_action.php?…&v=<lettre>`, qui
   rend LE VOCABULAIRE COMPLET de la lettre, libelles exacts. `lieux()` lit les deux et
   les reunit.

10. DEUX ENCODAGES SUR LE MEME SERVEUR. `ir_seriel.php` (le formulaire) est servi en
    `iso-8859-1` ; `ir_seriel_action.php` (les resultats) et l'autocompletion sont en
    UTF-8. Decoder le formulaire en UTF-8 rend « D\\ufffdpartement » et fait rater les
    libelles accentues — donc les champs « Annee » et « Recherche par cote ».

11. `l` ET `h` SONT LA LARGEUR ET LA HAUTEUR MAXIMALES, ET 1800 PX N'EST QUE LE DEFAUT.
    Sans `h`, `genereImage.html` rend 2520 x 1800 la ou le master fait 2912 x 2080 — et le
    nom du fichier servi le dit, `…_4264_1800_…_img.jpg`. Meme piege qu'a l'AD17, meme
    parade : un premier appel lit la taille du master, le second la demande.

12. LE PROXY D'IMAGES, LUI, N'EST PAS DERRIERE LE MUR. `/v2/images/genereImage.html` et
    `/cache/…jpg` repondent a une session nue. Ca ne sert a rien de s'en priver, mais ca
    explique pourquoi une session peut tirer des JPEG apres avoir perdu le droit de lire
    la page qui les liste : les images arrivent, la liste est une page de defi.

13. CE PORTAIL SE FERME, ET IL NE LE DIT PAS EN HTTP. Apres quelques centaines de POST a
    0,35 s d'intervalle — quatre balayages complets de Calais dans la meme heure —
    `archivesenligne.pasdecalais.fr` a cesse de repondre A LA POIGNEE DE MAIN TLS : pas de
    429, pas de 403, un `handshake operation timed out` sur trois essais d'affilee, alors
    que la vitrine `www.archivespasdecalais.fr` et les autres portails du dossier
    repondaient normalement depuis la meme machine. Ce n'est donc ni le reseau, ni le
    magasin de certificats (voir `tls.py`), ni une panne du site : c'est un seuil de debit
    sur cet hote-la. D'ou CADENCE a 1,0 s. Et si un balayage s'arrete ainsi : ce n'est pas
    une raison de relancer en boucle, c'est une raison d'attendre.

--------------------------------------------------------- CE QUI A ETE MESURE, ET COMMENT

Le 19 septembre 2026, sur l'AD62 :

  * BOURS — 22 registres annonces a l'etat civil, 22 lus, dont 21 numerises (le 3 E 166/17,
    naissances-mariages-deces 1923-1932, est marque « Non numerise »). Le compte tombe
    juste aussi sur les trois autres fonds essayes : 28 recensements, 15 tables, 32 plans
    cadastraux, annonces et lus.
  * CALAIS — la recherche sans borne plafonne a 100. Le decoupage par annees rend
    318 registres uniques, dont 297 numerises, en sept fenetres qui tombent toutes juste
    (1500-1730 : 16 · 1731-1845 : 55 · 1846-1874 : 36 · 1875-1903 : 83 · 1904-1918 : 74 ·
    1919-1932 : 58 · 1933-1960 : 42). CONTRE-EPREUVE : le meme balayage refait avec un
    decoupage different — quarante-six tranches de dix ans au lieu de la dichotomie —
    rend EXACTEMENT LE MEME ENSEMBLE, sans une ligne d'ecart. Deux decoupages qui
    tombent sur le meme ensemble, c'est la seule preuve qu'on n'a rien perdu en route.
  * IMAGES — 5 MIR 166/1 (Bours, microfilm BMS 1693-1751) : 609 vues listees, les vues 5
    a 7 tirees a 1440 x 2256 px, qui est leur master. 3 E 166/18 (Bours, mariages 1923) :
    la vue 2 sort a 4410 x 3305 px, 1,5 Mo — SANS le parametre `h` elle sortait a
    2401 x 1800 (piege 11).
"""
import http.cookiejar
import io
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

import certifi

# La verification TLS de cette machine est reparee par `scripts/archives/tls.py` :
# le magasin de racines de Windows porte une racine perimee, et tous ces portails sont
# chez Let's Encrypt. Un import suffit, il agit sur tout le processus.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tls  # noqa: F401,E402

CTX = ssl.create_default_context(cafile=certifi.where())
# UNE SECONDE, ET C'EST MESURE (piege 13) : a 0,35 s, une soiree de balayage de Calais a
# fini par un refus de poignee de main TLS de la part de ce seul hote.
CADENCE = 1.0
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))          # le depot, pour `require`
CONF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "portails.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

# Une seule session pour tout le module : le PHPSESSID sert de `sid` aux autocompletions,
# et les cookies du mur F5 tournent d'une reponse a l'autre (piege 2).
_CJ = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_CJ),
                                      urllib.request.HTTPSHandler(context=CTX))
_AMORCE = set()          # les hotes dont le mur a deja ete franchi dans ce processus

# Les signatures du defi F5 / Shape. Voir `lire_page.js`, qui porte la meme liste pour
# les autres murs rencontres par le dossier.
_DEFI = re.compile(r"/TSPD/|[Yy]our support ID is", re.I)

# Le script d'amorce : un vrai Chrome, une page, et on ramasse les cookies. Il est ecrit
# dans un repertoire temporaire a chaque appel plutot que garde a cote du module — un
# profil Chrome persistant pese 500 Mo au bout d'une semaine (la lecon du 12 septembre
# 2026), et le defi ne coute que deux secondes : il n'y a rien a mettre en cache.
_JS = """
const { chromium } = require('playwright');
const fs = require('fs');
const [URL, OUT] = process.argv.slice(2);
const defi = h => /\\/TSPD\\/|your support ID is/i.test(h) || h.length < 6000;
(async () => {
  const nav = await chromium.launch({ channel: 'chrome', headless: false });
  const ctx = await nav.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
  let h = await page.content(), t = 0;
  while (defi(h) && t < 60000) { await page.waitForTimeout(2000); t += 2000; h = await page.content(); }
  if (defi(h)) { process.stderr.write('defi NON franchi apres 60 s\\n'); process.exitCode = 2; }
  else process.stderr.write('mur F5 franchi en ' + (t / 1000) + ' s\\n');
  fs.writeFileSync(OUT, JSON.stringify(await ctx.cookies()), 'utf8');
  await nav.close();
})();
"""


# ------------------------------------------------------------------ la fiche du portail
def _conf(dept):
    with io.open(CONF, encoding="utf-8") as f:
        for p in json.load(f)["portails"]:
            if str(p.get("dept")) == str(dept):
                return p
    raise SystemExit("departement %s absent de portails.json" % dept)


def _id_appli(p):
    """L'identifiant d'application (`id=56` a l'AD62), LU dans la fiche du portail."""
    m = re.search(r"[?&]id=(\d+)", (p.get("recherche") or {}).get("chemin", ""))
    return m.group(1) if m else "56"


# ------------------------------------------------------------------------- le mur F5
def amorce(base, url=None):
    """Franchir le mur avec un vrai Chrome et verser ses cookies dans le pot Python.

    Le defi F5 est une preuve par JavaScript : aucune suite de requetes HTTP ne le passe,
    et le dossier a verifie qu'un rejeu simple ne suffit pas (quatre requetes d'affilee,
    quatre pages de defi). Un Chrome fenetre le franchit en deux secondes.

    ⛔ L'AMORCE DOIT VISER UNE PAGE QUI EST DERRIERE LE MUR. Amorcer sur `/console/`, qui
    passe en clair, rend « mur franchi en 0 s » et un pot de cookies SANS `TSPD_101` — la
    requete suivante se reprend le defi, et l'amorce a l'air d'avoir marche. D'ou l'URL
    passee par `_get()` : celle qu'on allait justement demander.
    """
    url = url or (base + "/console/")
    hote = urllib.parse.urlparse(base).hostname
    tmp = tempfile.mkdtemp(prefix="archinoe_o2-")
    js, jar = os.path.join(tmp, "amorce.js"), os.path.join(tmp, "cookies.json")
    try:
        with io.open(js, "w", encoding="utf-8") as f:
            f.write(_JS)
        env = dict(os.environ)
        env.setdefault("NODE_PATH", os.path.join(RACINE, "node_modules"))
        r = subprocess.run(["node", js, url, jar], cwd=RACINE, env=env,
                           capture_output=True, timeout=180)
        if r.stderr:
            sys.stderr.write(r.stderr.decode("utf-8", "replace"))
        if not os.path.exists(jar):
            raise RuntimeError("l'amorce n'a rendu aucun cookie — playwright est-il la ?\n"
                               + r.stdout.decode("utf-8", "replace")[:500])
        with io.open(jar, encoding="utf-8") as f:
            biscuits = json.load(f)
        for c in biscuits:
            dom = c.get("domain") or hote
            _CJ.set_cookie(http.cookiejar.Cookie(
                0, c["name"], c["value"], None, False, dom, False, dom.startswith("."),
                c.get("path", "/"), True, bool(c.get("secure")), None, False,
                None, None, {}))
        _AMORCE.add(hote)
        return len(biscuits)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _get(chemin, base, data=None, ref=None, brut=False, encodage="utf-8", rejoue=True):
    """Une requete, et LE DEFI RECONNU COMME TEL.

    Le pare-feu rend un HTTP 200 : sans ce controle, une page de defi se lirait comme un
    resultat vide, et un « aucun registre » sortirait d'une session perimee (piege 2).
    """
    hote = urllib.parse.urlparse(base).hostname
    if hote not in _AMORCE:
        amorce(base, base + chemin)
    h = dict(UA)
    h["Referer"] = ref or (base + "/console/")
    corps = None
    if data is not None:
        h["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        h["X-Requested-With"] = "XMLHttpRequest"
        corps = data.encode("utf-8")
    d = _OPENER.open(urllib.request.Request(base + chemin, data=corps, headers=h),
                     timeout=120).read()
    if _DEFI.search(d[:4000].decode("latin-1", "replace")):
        if not rejoue:
            raise RuntimeError("mur F5 non franchi sur %s" % chemin)
        sys.stderr.write("  mur F5 retombe — on reamorce\n")
        _AMORCE.discard(hote)
        amorce(base, base + chemin)
        return _get(chemin, base, data, ref, brut, encodage, rejoue=False)
    return d if brut else d.decode(encodage, "replace")


def _sid():
    """Le `sid` des autocompletions EST le PHPSESSID (piege 8)."""
    for c in _CJ:
        if c.name == "PHPSESSID":
            return c.value
    return ""


def _txt(s):
    import html as _h
    return " ".join(_h.unescape(re.sub(r"<[^>]+>", " ", s)).split())


# --------------------------------------------------------------------------- les fonds
def fonds(base, dept=None):
    """Les fonds interrogeables. La fiche du portail les porte ; a defaut on les lit dans
    les liens `ir_seriel.php?…&p=formulaire_<fonds>` de la page d'accueil du moteur."""
    if dept is not None:
        f = (_conf(dept).get("recherche") or {}).get("fonds")
        if f:
            return list(f)
    h = _get("/console/", base, encodage="iso-8859-1")
    return sorted(set(re.findall(r"p=formulaire_([a-z0-9_\-]+)", h)))


# ---------------------------------------------------------------- le formulaire, LU
def champs(base, fonds_, id_appli="56"):
    """Le formulaire d'un fonds, lu dans son HTML — jamais transpose (piege 3).

    Rend un dictionnaire :
        action   le chemin du POST
        libelles {id_champ: libelle affiche}
        tous     les ids de tous les champs a poster (les vides comptent)
        lieu     l'id du champ « Lieu » / « Commune », ou None
        annee    (id_select, id_debut, id_fin) du groupe « Entre … et … », ou None
        actes    les ids des cases a cocher de type d'acte
        visu     le prefixe de la visionneuse, p. ex. /v2/ad62/visualiseur/
    """
    h = _get("/console/ir_seriel.php?id=%s&p=formulaire_%s" % (id_appli, fonds_), base,
             encodage="iso-8859-1")
    m = re.search(r"<form id='form_0'[^>]*action='([^']+)'", h)
    if not m:
        raise RuntimeError("pas de formulaire pour le fonds %r "
                           "(fonds inconnu, ou mur non franchi)" % fonds_)
    action = _txt(m.group(1)).replace("&amp;", "&")
    libelles = {i: _txt(l) for i, l in re.findall(r"<label for='([^']+)'>(.*?)</label>",
                                                  h, re.S)}
    tous = sorted(set(re.findall(r"(?:id|name)='(f_0_[0-9_]+)'", h)))
    coches = sorted(set(re.findall(r"<input type='checkbox' id='(f_0_[0-9_]+)'", h)))

    # Le lieu : le champ dont le libelle dit Lieu ou Commune. A l'etat civil c'est f_0_0,
    # au cadastre f_0_1 — et f_0_0 y est « Fonds ou collection » (piege 3).
    lieu = None
    for i, lab in sorted(libelles.items()):
        if re.match(r"(lieu|commune)\b", lab, re.I):
            lieu = i
            break

    # L'annee : un <select id='c_0_N'> pilote deux champs f_0_N_0 / f_0_N_1.
    annee = None
    for n in re.findall(r"<select id='c_0_(\d+)'", h):
        annee = ("c_0_%s" % n, "f_0_%s_0" % n, "f_0_%s_1" % n)
        break

    # Les cases d'acte : celles du groupe qui n'est pas le groupe d'annee.
    actes = [c for c in coches if not (annee and c.startswith(annee[1][:-2]))]
    visu = re.search(r"window\.open\('(/v2/[^/]+/visualiseur/)'", h)
    return {"action": action, "libelles": libelles, "tous": tous, "lieu": lieu,
            "annee": annee, "actes": actes, "onglet": 1,
            "visu": visu.group(1) if visu else None, "sid": _sid()}


# --------------------------------------------------------------------------- les lieux
def lieux(base, fonds_, motif, id_appli="56", qualificatif=None):
    """Les libelles EXACTS des lieux — « Calais (Pas-de-Calais, France) », jamais « Calais ».

    Deux sources reunies (piege 9) : le vocabulaire complet de la lettre initiale, qui est
    exhaustif, et l'autocompletion, qui voit les entrees dont le motif n'est pas au debut
    (« Labourse » et « Sailly-Labourse » sortent sur « bours », et ils sont ranges au L).
    Les deux sont FILTREES sur le motif : l'autocompletion rembourre sa reponse avec le
    debut du referentiel, et rien dans le JSON ne separe les vraies reponses du bourrage.

    ⛔ ET LE FILTRE SE FAIT SUR LE NOM, PAS SUR LE LIBELLE ENTIER — SINON IL NE FILTRE
    RIEN ICI. Chaque libelle du Pas-de-Calais porte « (Pas-de-Calais, France) » : chercher
    « calais » dans le libelle entier retient les 895 communes du departement, et la
    reponse a l'air d'un referentiel complet plutot que d'un filtre casse. On retire donc
    le qualificatif geographique (le nom du departement, lu dans `portails.json`) avant de
    comparer. C'est la meme famille de piege que le champ `REch_commune` de l'AD16 : un
    filtre qui ne filtre pas rend TOUJOURS quelque chose de plausible.
    """
    f = champs(base, fonds_, id_appli)
    if not f["lieu"]:
        raise SystemExit("le fonds %r n'a pas de champ de lieu ; champs lus : %s"
                         % (fonds_, ", ".join("%s=%s" % kv for kv in
                                              sorted(f["libelles"].items()))))
    n = f["lieu"].rsplit("_", 1)[1]
    m = motif.lower()
    out = []

    # 1. le vocabulaire complet de la lettre — le bouton « Liste » du formulaire
    if motif:
        u = ("/console/ir_ead_liste_seriel_action.php?cli=%s&cle=formulaire_%s&f=0&id=%s"
             "&v=%s&PHPSID=%s" % (id_appli, fonds_, n,
                                  urllib.parse.quote(motif[0].upper()), _sid()))
        try:
            h = _get(u, base)
            out += [_txt(x) for x in
                    re.findall(r'selFichier\((?:&quot;|")(.*?)(?:&quot;|")\)', h)]
        except Exception as e:                       # une lettre absente n'est pas un bug
            sys.stderr.write("  liste par lettre indisponible : %s\n" % e)

    # 2. l'autocompletion — trois lettres minimum, et elle voit les motifs internes
    if len(motif) >= 3:
        u = ("/console/ir_seriel_data.php?f=0&c=%s&cle=formulaire_%s&id=%s&sid=%s&query=%s"
             % (n, fonds_, id_appli, _sid(), urllib.parse.quote(motif)))
        out += json.loads(_get(u, base)).get("suggestions", [])

    vus, res = set(), []
    for lib in out:
        nom = lib.lower()
        if qualificatif:
            nom = nom.replace(qualificatif.lower(), " ")
        if m in nom and lib not in vus:
            vus.add(lib)
            res.append(lib)
    return sorted(res)


# ----------------------------------------------------------------------- les registres
_CAP = "Trop de r"


def _total(h):
    """Le total annonce. « Un resultat trouve » n'a pas de chiffre (piege 6)."""
    m = re.search(r"<div\s+class='cnres'\s*>([^<]*)", h)
    if not m:
        return None, ""
    t = _txt(m.group(1))
    if t.startswith(_CAP):
        return None, t                               # plafond : ce n'est pas un total
    if t.lower().startswith("un r"):
        return 1, t
    n = re.match(r"(\d+)", t)
    return (int(n.group(1)) if n else None), t


def _grille(h):
    """Les lignes de l'onglet « Liste » : [(id_ou_None, [cellules])]."""
    entetes = [_txt(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", h, re.S)]
    lignes = {}
    for r, c, cell in re.findall(r'<td id="td_(\d+)_(\d+)"[^>]*>(.*?)</td>', h, re.S):
        lignes.setdefault(int(r), {})[int(c)] = cell
    out = []
    for r in sorted(lignes):
        cells = [lignes[r].get(c, "") for c in sorted(lignes[r])]
        brut = "".join(cells)
        m = re.search(r"afficheImage\((\d+)", brut)
        cellules = [_txt(c) for c in cells]
        # UNE LIGNE ENTIEREMENT VIDE N'EST PAS UN REGISTRE. Les pages plafonnees en
        # rendent une de temps en temps ; conservee, elle ajoutait un 319e registre
        # fantome a Calais et faisait diverger deux balayages par ailleurs identiques.
        if any(cellules):
            out.append((m.group(1) if m else None, cellules))
    return entetes, out


def _requete(f, lieu, a1="", a2=""):
    """Le corps du POST : TOUS les champs du formulaire, le lieu rempli, les annees si on
    en donne, et toutes les cases d'acte cochees — c'est ce que fait `doSubmit0()`."""
    vals = []
    for i in f["tous"]:
        if i == f["lieu"]:
            vals.append((i, lieu))
        elif f["annee"] and i == f["annee"][1]:
            vals.append((i, a1))
        elif f["annee"] and i == f["annee"][2]:
            vals.append((i, a2))
        elif i in f["actes"]:
            vals.append((i, "on"))
        else:
            vals.append((i, ""))
    if f["annee"]:
        vals.append((f["annee"][0], "2"))            # 2 = « Entre … et … »
    return urllib.parse.urlencode(vals)


def _page(base, f, q, page, id_appli, r=None):
    u = f["action"] + "&r=%d" % (f["onglet"] if r is None else r)
    if page:
        u += "&page=%d" % page
    return _get("/console/" + u + "&" + q, base, data=q,
                ref=base + "/console/ir_seriel.php?id=%s" % id_appli)


def _onglet(base, f, q, id_appli, bruit=True):
    """QUEL ONGLET PORTE LA GRILLE ? ON LE MESURE, ON NE LE SUPPOSE PAS (piege 5).

    `&r=N` designe un onglet de resultats, et CE N'EST PAS LE MEME SELON LE FONDS. A
    l'etat civil, `r=0` est l'onglet « Details » — trois registres par page, en fiches —
    et `r=1` la grille complete : 3 lignes contre 22 sur Bours. Au RECENSEMENT et aux
    TABLES, `r=1` rend 32 octets et AUCUNE ligne : la grille est en `r=0`. Au CADASTRE,
    les deux repondent, et c'est `r=0` qui porte les colonnes.

    Choisir 1 partout aurait donc rendu « 0 registre » sur le recensement d'une commune
    qui en a 28, sans erreur ni message — le faux negatif le plus cher de ce carnet. On
    demande donc les deux onglets a la page 0 et on garde celui qui rend le plus de lignes.
    """
    mieux, combien, entetes = 0, -1, []
    for r in (0, 1):
        e, lignes = _grille(_page(base, f, q, 0, id_appli, r))
        if len(lignes) > combien:
            mieux, combien, entetes = r, len(lignes), e
    if bruit:
        sys.stderr.write("  onglet r=%d (%d lignes en page 0)\n" % (mieux, combien))
    return mieux, entetes


def _fenetre(base, f, lieu, a1, a2, id_appli, vus, bruit):
    """Une fenetre d'annees, TOUTES SES PAGES. Rend (lignes_neuves, plafonne, annonce).

    ⛔ DEUX COMPTES, ET LES CONFONDRE CASSE A LA FOIS LA PAGINATION ET LE CONTROLE. Les
    fenetres d'annees se chevauchent, donc la plupart des lignes d'une fenetre ont deja
    ete vues dans une autre. Si l'arret de la pagination et la comparaison au total
    annonce portent sur les lignes NEUVES, une fenetre entierement deja connue s'arrete a
    la page 0 et hurle « 58 annonces, 0 lus ». On compte donc separement :
      * `lues`   toutes les lignes de CETTE fenetre — c'est ce qui se compare a l'annonce
                 et ce qui decide s'il reste une page a lire ;
      * `neuves` celles qu'aucune fenetre n'avait rendues — c'est ce qu'on retourne.
    """
    q = _requete(f, lieu, a1, a2)
    h = _page(base, f, q, 0, id_appli)
    annonce, libelle = _total(h)
    plafond = libelle.startswith(_CAP)
    neuves, ici, page = [], set(), 0
    while True:
        _, lignes = _grille(h)
        fraiches = [(i, c) for i, c in lignes if (i, tuple(c)) not in ici]
        if not fraiches:                             # cette page n'apporte plus rien
            break
        for i, c in fraiches:
            cle = (i, tuple(c))
            ici.add(cle)
            if cle not in vus:
                vus.add(cle)
                neuves.append((i, c))
        page += 1
        time.sleep(CADENCE)
        h = _page(base, f, q, page, id_appli)
    borne = "%s-%s" % (a1, a2) if a1 or a2 else "sans borne"
    if bruit:
        sys.stderr.write("  %-11s %-48s %3d lues, %3d neuves\n"
                         % (borne, libelle, len(ici), len(neuves)))
    if annonce is not None and annonce != len(ici) and not plafond:
        sys.stderr.write("  ATTENTION : %s — %d annonces, %d lus\n"
                         % (borne, annonce, len(ici)))
    return neuves, plafond, annonce


def registres(base, fonds_, lieu, id_appli="56", annees=(1500, 1960), bruit=True):
    """Les registres d'un lieu, TOUTES PAGES LUES ET PLAFOND FRANCHI.

    Rend (entetes, lignes, annonce) ou lignes = [(id_ou_None, [cellules])]. `id` a None
    signale un registre non numerise (piege 7) — la ligne reste, c'est un fait du fonds.

    Le plafond de 100 se franchit en coupant l'intervalle d'annees en deux tant qu'une
    moitie plafonne (piege 4). Les bornes sont larges par defaut : un registre paroissial
    du Pas-de-Calais commence en 1553, l'etat civil en ligne s'arrete en 1947.
    """
    f = champs(base, fonds_, id_appli)
    if not f["lieu"]:
        raise SystemExit("le fonds %r n'a pas de champ de lieu" % fonds_)
    vus, out = set(), []
    f["onglet"], entetes = _onglet(base, f, _requete(f, lieu), id_appli, bruit)

    lignes, plafond, annonce = _fenetre(base, f, lieu, "", "", id_appli, vus, bruit)
    out += lignes
    if plafond and f["annee"]:
        if bruit:
            sys.stderr.write("  plafond atteint — decoupage par fenetres d'annees\n")
        pile = [annees]
        while pile:
            a, b = pile.pop()
            l2, p2, _ = _fenetre(base, f, lieu, str(a), str(b), id_appli, vus, bruit)
            out += l2
            if p2:
                if b - a < 2:
                    sys.stderr.write("  ATTENTION : %s-%s plafonne encore sur une fenetre "
                                     "d'un an — affiner par type d'acte\n" % (a, b))
                else:
                    m = (a + b) // 2
                    pile += [(a, m), (m + 1, b)]
    elif plafond:
        sys.stderr.write("  ATTENTION : plafond atteint et ce fonds n'a pas de champ "
                         "d'annee — la liste est tronquee a 100\n")
    return entetes, out, annonce


# ------------------------------------------------------------------------- les images
def vues(base, fonds_, ident, visu=None):
    """Les chemins disque des vues d'un registre, DANS L'ORDRE. Une seule requete.

    C'est l'ancienne visionneuse Archinoe v2, celle de l'AD17 : la page porte toutes ses
    vues en `data-original`, qui est un chemin sur le serveur de fichiers et non une URL.
    """
    if visu is None:
        visu = champs(base, fonds_)["visu"]
    h = _get("%s%s.html?id=%s" % (visu, fonds_, ident), base,
             ref=base + "/console/")
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
    t = _get("/v2/images/genereImage.html?" + urllib.parse.urlencode(q), base).split("\t")
    if len(t) < 6 or not t[1].endswith(".jpg"):
        raise RuntimeError("genereImage n'a pas rendu de chemin : %r" % t[:2])
    return t


def image(base, chemin, pleine=True):
    """Le JPEG d'une vue. Rend (octets, largeur, hauteur, largeur_master, hauteur_master).

    Sans `h`, le serveur plafonne a 1800 px de haut : c'est une valeur par defaut, pas une
    limite (piege 11). Le premier appel lit la taille du master, le second la demande.
    """
    t = _genere(base, chemin, 4264, None)
    if pleine and (int(t[2]), int(t[3])) != (int(t[4]), int(t[5])):
        t = _genere(base, chemin, int(t[4]), int(t[5]))
    jpg = _get(t[1], base, brut=True)
    if jpg[:3] != b"\xff\xd8\xff":
        raise RuntimeError("ce n'est pas un JPEG : %r" % jpg[:40])
    return jpg, int(t[2]), int(t[3]), int(t[4]), int(t[5])


def tirer(base, fonds_, ident, dossier, debut=1, fin=None, cadence=CADENCE, pleine=True):
    """Les vues d'un registre sur le disque, vNNN.jpg — la convention du NAS.

    LE NUMERO EST CELUI DU PORTAIL, pas la position dans le dossier : un registre se tire
    par fenetres, et indexer la liste triee ferait lire un acte pour un autre.
    """
    liste = vues(base, fonds_, ident)
    fin = min(fin or len(liste), len(liste))
    os.makedirs(dossier, exist_ok=True)
    print("%s %s : %d vues listees" % (fonds_, ident, len(liste)), flush=True)
    for n in range(debut, fin + 1):
        cible = os.path.join(dossier, "v%03d.jpg" % n)
        if os.path.exists(cible) and os.path.getsize(cible) > 20000:
            continue
        jpg, w, h, mw, mh = image(base, liste[n - 1], pleine)
        with open(cible, "wb") as fic:
            fic.write(jpg)
        print("  v%03d  %dx%d  (master %dx%d)  %d Ko"
              % (n, w, h, mw, mh, len(jpg) // 1024), flush=True)
        time.sleep(cadence)
    return fin - debut + 1


# ------------------------------------------------------------------------------- CLI
if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    p = _conf(a[0])
    base = p["base"].rstrip("/")
    ida = _id_appli(p)
    cmd = a[1] if len(a) > 1 else "fonds"

    if cmd == "fonds":
        for f in fonds(base, a[0]):
            print(f)
    elif cmd == "champs":
        f = champs(base, a[2], ida)
        print("action : %s" % f["action"])
        print("visu   : %s" % f["visu"])
        print("lieu   : %s" % f["lieu"])
        print("annee  : %s" % (f["annee"],))
        print("actes  : %s" % ", ".join(f["actes"]))
        for i in f["tous"]:
            print("  %-10s %s" % (i, f["libelles"].get(i, "")))
    elif cmd == "lieux":
        for lib in lieux(base, a[2], a[3] if len(a) > 3 else "", ida, p.get("nom")):
            print(lib)
    elif cmd == "registres":
        entetes, lignes, annonce = registres(base, a[2], a[3], ida)
        if entetes:
            print(" | ".join(entetes))
        for ident, cells in lignes:
            print("%-10s %s" % (ident or "-", " | ".join(cells)))
        num = sum(1 for i, _ in lignes if i)
        print("%d registres lus, dont %d numerises%s"
              % (len(lignes), num, ("  (annonce : %d)" % annonce) if annonce else ""))
    elif cmd == "vues":
        for i, chemin in enumerate(vues(base, a[2], a[3]), 1):
            print("%4d %s" % (i, chemin))
    elif cmd == "tirer":
        tirer(base, a[2], a[3], a[4],
              int(a[5]) if len(a) > 5 else 1,
              int(a[6]) if len(a) > 6 else None)
    else:
        raise SystemExit(__doc__)
