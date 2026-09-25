# -*- coding: utf-8 -*-
"""LIRE N'IMPORTE QUEL REGISTRE DU NAS — le moteur, dont le departement n'est qu'un argument.

POURQUOI CE FICHIER EXISTE, ET C'ETAIT UNE FAUTE DE METHODE.
`page.py`, `zoomb.py`, `strip.py`, `tete.py` et `grille.py` ne savent parler qu'a l'AD42 :
leurs chemins passent par `actes.REGS`, une table des registres d'Usson-en-Forez codee en
dur. `sp.py` et `decouper.py` font la meme chose pour Saint-Pal (AD43). Chaque nouveau
departement repartait donc de zero : le 26 aout 2026, les neuf actes d'Indre-et-Loire ont
ete lus avec un script ecrit pour l'occasion dans le repertoire temporaire de la session,
et perdu avec elle. LA CONSIGNE ETAIT D'ENRICHIR L'OUTILLAGE A CHAQUE NOUVEAU DEPARTEMENT,
PAS DE LE DUPLIQUER. Ici la recette est ecrite une fois ; l'AD37, l'AD45, l'AD67 et le
centieme departement sont la meme commande.

ET IL N'Y A RIEN A DECLARER. Le NAS est deja range de facon reguliere --
`<archives>/\Archives genealogiques\\AD<NN> - <Commune>\\<Registre>\\vNNN.jpg` -- alors le registre
se DESIGNE au lieu de se configurer : « 37/luble/d 1837 » suffit, sans accent, sans casse,
sans nom exact. Aucun fichier de configuration a tenir a jour, donc aucun a oublier.

    python nas.py l                                    # lister les registres du NAS
    python nas.py l luble                              # ... ceux qui repondent au motif
    python nas.py "37/luble/D 1837" 124 127            # rendre les demi-pages
    python nas.py t "43/saint-pal/BMS 1737" 1 12 t.png # cadrer : 12 vues en UNE image
    python nas.py t "49/meon" 100 129 t.png 0.16 7     # ... en planches de 7 cellules
    python nas.py m "42/usson/BMS 1773" 80 92 marge    # balayer les marges (type, hameau)
    python nas.py z "37/villiers/D 1906" 26 G 0.30 0.40 z.png 0.28 1.0 1   # zoomer
    python nas.py d "17/les mathes/N 1883" 65 D 0.50 0.99 \
        "1891-10-10 naissance BARITEAU Germaine - Les Mathes 2 E 236-12 v065D.png"
                                                       # l'acte seul, range sur le NAS

Un chemin complet marche aussi : c'est un dossier de `vNNN.jpg`, d'ou qu'il vienne.

LES RECETTES, ET LEURS RAISONS -- elles sont celles du carnet `data/archives-fr.md` :
  * UNE DEMI-PAGE PAR IMAGE A 1990 px sur le grand cote. Au-dela, l'image est reduite avant
    lecture : rendre plus grand ne rend rien.
  * RECADRAGE SUR LA BOITE D'ENCRE : tout ce qui est gagne sur les blancs du papier est gagne
    sur l'ecriture. Le zoom utilise LES MEMES FRACTIONS que le rendu, on repere donc sur
    l'image qu'on vient de lire sans rien recalculer.
  * `div=True` divise par un fond floute : c'est ce qui tue l'ombre de pliure.
  * LA PLANCHE DE MARGES NE VOIT PAS LES MARIAGES : leur texte part du bord gauche, ils n'ont
    pas de mention de marge. Un balayage par les marges est donc negatif pour les baptemes et
    les sepultures, et MUET sur les mariages. Le noter en consignant le negatif.

TROIS PIEGES PAYES, ET ILS SONT DANS LE CODE.

1. SIMPLE OU DOUBLE PAGE : C'EST L'ORIENTATION QUI TRANCHE, PAS LA LARGEUR. `actes.py`
   testait « moins de 2600 px de large = page simple », ce qui est vrai a l'AD42 et FAUX a
   l'AD43, dont les doubles pages font 2500 px : elles y passaient pour des pages simples.
   `marges.py` avait meme le test a l'envers. Une double page est plus large que haute ; une
   page simple est plus haute que large -- couverture, feuillet de garde, feuillet de cloture.
   Vrai des trois portails a la fois, donc vrai du prochain.

2. LE NUMERO DE VUE EST DANS LE NOM DU FICHIER, PAS DANS LA POSITION. Un registre n'est
   presque jamais tire en entier : on prend la fenetre d'une annee, puis une autre dix ans
   plus loin. Le dossier de Luble portait `v025-v065` et `v169-v194`, et indexer la liste
   triee par `[n-1]` rendait la vue 60 quand on demandait la 36 -- erreur silencieuse, qui
   fait lire un acte pour un autre et conclure qu'une annee est vide.

3. CERTAINES VUES SONT PHOTOGRAPHIEES LA TETE EN BAS. Trois au moins dans E-depot 2/8 a
   l'AD43, restees illisibles plusieurs jours faute d'une rotation. `NAS_ROT=10,11,12`
   donne la liste des vues a retourner.

4. UNE IMAGE QUI NE VIENT PAS D'UN PORTAIL N'OBEIT A AUCUNE DES TROIS REGLES CI-DESSUS.
   Un document tenu a la main et photographie au telephone est souvent plus large que
   haut sans etre une double page, et rarement d'aplomb. Deux reglages, tous deux
   explicites parce qu'aucune detection ne tranchera :
     NAS_ENTIER=1     l'image est UN document — ne pas chercher de pliure
     NAS_TOURNER=-90  tourner de N degres avant le recadrage
"""
import glob
import os
import sys
import unicodedata

import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont

MAX = 1990
OUT = os.environ.get("NAS_OUT", "vues")

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  _os.pardir, _os.pardir))
import config

NAS = config.archives()


# --------------------------------------------------------------- designer un registre
def _plat(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def registres(motif=""):
    """[(etiquette, chemin)] de tous les registres ranges sur le NAS."""
    # `AD*` SEUL RENDAIT LES ARCHIVES ITALIENNES INVISIBLES. Le NAS range un registre
    # sous `<fonds> - <Commune>/<Registre>/vNNN.jpg`, et le fonds n'est un « AD<NN> »
    # que dans un departement francais : l'Archivio di Stato di Udine s'ecrit
    # `AS Udine - Valvasone`. Le 27 aout 2026, le registre des morts de 1813 a ete tire
    # sur X: et `nas.py l` ne le voyait pas — l'outil de lecture est cense ignorer d'ou
    # vient une image, et il trebuchait sur le nom du dossier parent.
    out = []
    dossiers = sorted(set(glob.glob(os.path.join(NAS, "AD*"))
                          + glob.glob(os.path.join(NAS, "AS*"))))
    for dep in dossiers:
        if not os.path.isdir(dep):
            continue
        for r in sorted(glob.glob(os.path.join(dep, "*"))):
            if os.path.isdir(r) and glob.glob(os.path.join(r, "v*.*")):
                out.append(("%s / %s" % (os.path.basename(dep), os.path.basename(r)), r))
    m = _plat(motif)
    if m.isdigit() and len(m) <= 3:          # « 67 » cherche l'AD67, pas l'annee 1667
        m = "ad" + m + " "
    return [x for x in out if m in _plat(x[0])] if m else out


def reg(spec):
    """Le dossier d'un registre, designe par un chemin complet OU par des bouts de son nom.

    « 37/luble/d 1837 » -> <archives>/AD37 - Luble/D 1837-1905.
    Chaque bout doit se retrouver, DANS L'ORDRE, dans l'etiquette du registre -- sans
    accent ni casse. Si plusieurs registres repondent, on refuse et on les liste : une
    commande qui ouvre le mauvais registre est pire qu'une commande qui echoue.
    """
    if os.path.isdir(spec):
        return spec
    # UNE IMAGE SEULE EST UN REGISTRE D'UNE VUE, ET L'OUTIL DOIT SAVOIR LA LIRE.
    # La skill le dit depuis le debut — « les outils de lecture ne dependent de rien,
    # ils travaillent sur des JPEG deja sur le disque et ignorent d'ou ils viennent,
    # c'est voulu : la moitie des images arrivent par un autre chemin » — mais le code
    # n'acceptait qu'un DOSSIER de `vNNN.jpg`. Le 27 aout 2026, il a fallu zoomer sur
    # l'affiche de cinema d'une photo de famille, `<photos>/Papa/.../Alfiero et Alida.jpg`,
    # et le moteur a repondu « aucun registre ne repond ». Une photo de livret, un envoi
    # de cousin, un cliche pris au telephone : rien de tout ca n'est range en vues
    # numerotees, et c'est precisement le cas que la regle annonçait.
    if os.path.isfile(spec):
        return spec
    bouts = [_plat(b) for b in spec.replace("\\", "/").split("/") if b.strip()]
    # UN NUMERO DE DEPARTEMENT S'ANCRE SUR LE PREFIXE « AD », sinon il attrape des annees :
    # « 67 » repondait pour onze registres de l'AD43, tous a cause de « BMS 1672-1687 ».
    if bouts and bouts[0].isdigit() and len(bouts[0]) <= 3:
        bouts[0] = "ad" + bouts[0] + " "
    cands = []
    for etiq, chemin in registres():
        reste, ok = _plat(etiq), True
        for b in bouts:
            i = reste.find(b)
            if i < 0:
                ok = False
                break
            reste = reste[i + len(b):]
        if ok:
            cands.append((etiq, chemin))
    if len(cands) == 1:
        return cands[0][1]
    if not cands:
        raise FileNotFoundError(
            "aucun registre ne repond a %r -- `python nas.py l` pour la liste" % spec)
    raise ValueError("%r designe %d registres :\n  %s"
                     % (spec, len(cands), "\n  ".join(e for e, _ in cands)))


# ------------------------------------------------------------------- les vues, les pages
def vues(dossier):
    if os.path.isfile(dossier):          # une image seule : un registre d'une vue
        return [dossier]
    return sorted(glob.glob(os.path.join(dossier, "v*.jpg"))
                  + glob.glob(os.path.join(dossier, "v*.png")))


def plage(spec):
    """Les numeros de vues d'un « 30-42 », d'un « 30,60,90 », ou des deux melanges.

    ECHANTILLONNER DES VUES DISPERSEES EST LE GESTE NORMAL SUR UN GROS REGISTRE, et il
    n'etait pas outillé : `tetes` et `marges` ne prenaient qu'une plage continue, si bien
    qu'un sondage tous les trente feuillets d'un recensement de 1 183 vues obligeait a
    ecrire un script a cote -- la faute meme que ce fichier existe pour empecher.
    """
    ns = []
    for m in str(spec).replace(";", ",").split(","):
        m = m.strip()
        if not m:
            continue
        if "-" in m.lstrip("-"):
            d, f = m.split("-", 1)
            ns += list(range(int(d), int(f) + 1))
        else:
            ns.append(int(m))
    return ns


def vue(dossier, n):
    """Le chemin de LA VUE N° n — par son NOM DE FICHIER, jamais par sa position."""
    if os.path.isfile(dossier):
        return dossier                   # quel que soit n : il n'y en a qu'une
    for ext in ("jpg", "png"):
        p = os.path.join(dossier, "v%03d.%s" % (n, ext))
        if os.path.exists(p):
            return p
    raise FileNotFoundError("vue %d absente de %s — la telecharger d'abord" % (n, dossier))


def papier(im):
    """Le rectangle du PAPIER, fond de scanner ote.

    QUATRIEME PIEGE, ET IL COUTE DE LA RESOLUTION DE LECTURE. Plusieurs portails
    photographient le registre au milieu d'un large fond noir : a Gougenheim il
    fait 19 % de la surface de la vue, a Clery 7 %. `boite()` cherche les pixels
    SOMBRES pour trouver l'encre — elle prend ce fond pour du texte, et comme il
    touche les bords, elle rend la page entiere. Le recadrage ne recadre alors
    rien, et les 1990 px du rendu sont depenses a photographier du noir.

    On cherche donc ici le contraire de l'encre : la zone CLAIRE. Sur un scan sans
    fond sombre — la Loire, la Haute-Loire — la fonction ne trouve rien a oter et
    rend l'image telle quelle, donc rien ne bouge pour les fractions de zoom deja
    notees dans le corpus.

    ATTENTION A NE PAS LIRE UNE BOITE A 100 % COMME UNE PANNE : les pages reglees
    de Touraine portent des lignes imprimees sur toute leur surface, et leur boite
    d'encre EST la page. Verifie le 26 aout 2026 sur les onze registres du NAS.
    """
    g = np.asarray(im)
    seuil = max(55.0, float(np.percentile(g, 65)) * 0.55)
    clair = g > seuil
    xs = np.nonzero(clair.mean(axis=0) > 0.35)[0]
    ys = np.nonzero(clair.mean(axis=1) > 0.35)[0]
    if len(xs) < 20 or len(ys) < 20:
        return im
    x0, y0, x1, y1 = int(xs[0]), int(ys[0]), int(xs[-1]) + 1, int(ys[-1]) + 1
    if (x1 - x0) * (y1 - y0) > 0.985 * im.width * im.height:
        return im                                # pas de fond a oter
    return im.crop((x0, y0, x1, y1))


def volume(im, marge=0.04, seuil=90, densite=0.05):
    """Le rectangle du VOLUME RELIE, quand le fond du scanner est CLAIR.

    CINQUIEME PIEGE, ET IL EST LE MIROIR DU QUATRIEME. `papier()` ci-dessus a ete
    ecrite pour les portails qui posent le registre sur du NOIR : elle cherche la
    zone claire. Le Maine-et-Loire le pose sur du BLANC, plus clair que le papier du
    registre lui-meme — la zone claire est alors le FOND, et rien n'est recadre. Le
    volume n'occupe que 29 % de la vue ; les trois quarts des 1990 px du rendu partent
    en papier blanc, sans que rien ne le signale puisque le texte reste lisible.

    ON CHERCHE DONC LA RELIURE, qui est sombre — mais EN IGNORANT D'ABORD UNE MARGE
    EXTERIEURE. C'est tout le secret, et c'est ce qui a manque a trois tentatives : le
    scan porte un LISERE NOIR sur son pourtour, si bien qu'une recherche de pixels
    sombres part du bord et rend la vue entiere. Quatre pour cent de marge suffisent.
    Mesure sur les 85 vues de Breil : x 0,233-0,799, y 0,230-0,758, STABLE A 1 % PRES.

    ELLE NE S'ALLUME QUE SUR DEMANDE — `NAS_CROP=auto`, ou des fractions explicites.
    Rien ne change pour les 111 registres deja sur le NAS, dont les fractions de zoom
    notees dans le corpus et les decoupes d'actes deja publiees dependent du cadrage
    actuel. Le jour ou l'on saura decider tout seul du sens du fond, cette fonction
    deviendra automatique ; en attendant, c'est au lecteur de le dire.
    """
    p = os.environ.get("NAS_CROP", "").strip()
    if not p:
        return im
    if p != "auto":
        x0, y0, x1, y1 = (float(v) for v in p.replace(";", ",").split(","))
        return im.crop((int(x0 * im.width), int(y0 * im.height),
                        int(x1 * im.width), int(y1 * im.height)))
    g = np.asarray(im.resize((max(1, im.width // 8), max(1, im.height // 8)),
                             Image.BILINEAR)).astype(np.float32)
    H, W = g.shape
    mx, my = int(W * marge), int(H * marge)
    if W - 2 * mx < 10 or H - 2 * my < 10:
        return im
    s = g[my:H - my, mx:W - mx] < seuil
    xs = np.nonzero(s.mean(axis=0) > densite)[0]
    ys = np.nonzero(s.mean(axis=1) > densite)[0]
    if len(xs) < 3 or len(ys) < 3:
        return im
    x0, x1 = (mx + int(xs[0])) / W, (mx + int(xs[-1]) + 1) / W
    y0, y1 = (my + int(ys[0])) / H, (my + int(ys[-1]) + 1) / H
    if (x1 - x0) * (y1 - y0) > 0.95:
        return im                                # rien a oter : fond deja absent
    return im.crop((int(x0 * im.width), int(y0 * im.height),
                    int(x1 * im.width), int(y1 * im.height)))


def pages(path, rot=()):
    """[(side, PIL.Image)] — 'S' pour une page simple, 'G' et 'D' pour une double.

    La pliure se cherche VUE PAR VUE : elle ne tombe jamais au meme x.

    DEUX REGLAGES POUR LES IMAGES QUI NE VIENNENT PAS D'UN PORTAIL, et ils existent
    parce que la regle « c'est l'orientation qui tranche » ne vaut que pour un
    REGISTRE POSE A PLAT SOUS UN SCANNER. Le 28 aout 2026, les clichés du Raduno
    PIEDIRODA de 2013 — des documents tenus a la main, photographies au telephone —
    ont ete rendus par cet outil : les cinq certificats isoles ont ete coupes en deux
    au milieu du texte, parce qu'ils sont plus larges que hauts ; et les onze pages de
    registre ont ete rendues intactes mais DE TRAVERS, le texte courant a la verticale.
    Aucune detection ne tranchera ces cas — c'est au lecteur de le dire :

      NAS_ENTIER=1        ne pas chercher de pliure : l'image est UN document
      NAS_TOURNER=-90     tourner de N degres avant tout le reste (sens trigonometrique)

    `NAS_TOURNER` s'applique AVANT `volume()` et `papier()`, sans quoi le recadrage
    travaillerait sur un rectangle qui n'est pas encore celui du papier.
    """
    im = Image.open(path).convert("L")
    if os.path.basename(path)[1:4] in {"%03d" % int(x) for x in rot}:
        im = im.rotate(180, expand=True)
    ang = os.environ.get("NAS_TOURNER", "").strip()
    if ang:
        im = im.rotate(float(ang), expand=True, resample=Image.BICUBIC, fillcolor=255)
    im = volume(im)                              # fond de scanner CLAIR : sur demande
    im = papier(im)                              # fond de scanner SOMBRE : toujours
    g = np.asarray(im)
    if os.environ.get("NAS_ENTIER", "").strip() not in ("", "0"):
        return [("S", im)]                       # un document, pas une double page
    if g.shape[0] >= g.shape[1]:                 # plus haute que large -> page simple
        return [("S", im)]
    col = g.mean(axis=0)
    a, b = int(len(col) * 0.40), int(len(col) * 0.60)
    gx = a + int(np.argmin(col[a:b]))
    return [("G", im.crop((0, 0, gx, g.shape[0]))),
            ("D", im.crop((gx, 0, g.shape[1], g.shape[0])))]


def boite(g, seuil=0.010):
    """Le rectangle qui porte l'encre, marges de papier otees.

    `seuil` reste reglable parce que les outils historiques ne s'accordaient pas :
    `page.py` mesurait a 0,010 et `sp.py` a 0,012. Les fractions de zoom deja notees
    dans le corpus sont relatives a l'une ou a l'autre -- changer la valeur les
    deplacerait toutes, et les decoupes d'actes deja publiees avec. Chaque appelant
    garde donc la sienne.
    """
    bg = np.percentile(g, 88)
    m = g < bg - 58
    col, row = m.mean(axis=0), m.mean(axis=1)
    xs = np.nonzero(col > seuil)[0]
    ys = np.nonzero(row > seuil)[0]
    if len(xs) < 10 or len(ys) < 10:
        return 0, 0, g.shape[1], g.shape[0]
    return int(xs[0]), int(ys[0]), int(xs[-1]) + 1, int(ys[-1]) + 1


def _page(dossier, n, side, rot=()):
    d = dict(pages(vue(dossier, n), rot))
    return d[side] if side in d else d["S"]


# ------------------------------------------------------------------------- rendre, zoomer
def rendre(dossier, n, side, pad=34, dest=None, out=OUT, rot=(), seuil=0.010, prefixe="v"):
    pim = _page(dossier, n, side, rot)
    x0, y0, x1, y1 = boite(np.asarray(pim), seuil)
    c = pim.crop((max(0, x0 - pad), max(0, y0 - pad),
                  min(pim.width, x1 + pad), min(pim.height, y1 + pad)))
    f = MAX / max(c.width, c.height)
    c = c.resize((int(c.width * f), int(c.height * f)), Image.LANCZOS)
    c = ImageOps.autocontrast(c, cutoff=1)
    c = ImageEnhance.Sharpness(c).enhance(2.3)
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, dest or "%s%03d%s.png" % (prefixe, n, side))
    c.save(p)
    return p, c.size


def zb(dossier, n, side, y0, y1, dest, x0=0.0, x1=1.0, div=False, up=1,
       out=OUT, rot=(), seuil=0.010):
    """Zoom aux FRACTIONS DE LA BOITE D'ENCRE — les memes que celles de rendre()."""
    pim = _page(dossier, n, side, rot)
    X0, Y0, X1, Y1 = boite(np.asarray(pim), seuil)
    W, H = X1 - X0, Y1 - Y0
    c = pim.crop((X0 + int(x0 * W), Y0 + int(y0 * H),
                  X0 + int(x1 * W), Y0 + int(y1 * H)))
    f = up if up > 1 else max(1.0, MAX / max(c.width, c.height))
    c = c.resize((int(c.width * f), int(c.height * f)), Image.LANCZOS)
    if div:
        a = np.asarray(c).astype(np.float32)
        bg = np.asarray(c.filter(ImageFilter.GaussianBlur(70))).astype(np.float32)
        c = Image.fromarray(np.clip(a / np.maximum(bg, 1) * 208, 0, 255).astype(np.uint8))
    c = ImageOps.autocontrast(c, cutoff=1)
    c = ImageEnhance.Sharpness(c).enhance(2.2)
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, dest)
    c.save(p)
    return p, c.size


DECOUPES = config.decoupes()
PAD = 0.030          # marge haut et bas, en fraction de la boite d'encre


def decoupe(dossier, n, side, y0, y1, nom, x0=0.0, x1=1.0, div=False, rot=(),
            dest=DECOUPES, pad=PAD):
    """L'ACTE SEUL, EN IMAGE DURABLE, RANGE SUR LE NAS — la piece qu'on attache a un moment.

    POURQUOI ELLE EXISTE ICI ET PLUS DANS `decouper.py` : celui-la portait, en dur, le
    chemin de quatre registres de Saint-Pal et la LISTE DES ACTES a decouper. Ouvrir un
    cinquieme registre demandait d'editer le script ; ouvrir un autre departement
    demandait de le reecrire. C'est exactement la faute que ce fichier existe pour
    empecher, et elle avait survecu dans le seul outil qui ecrit sur le NAS.

    POURQUOI DECOUPER PLUTOT QUE MONTRER LA VUE : une vue brute est une DOUBLE PAGE de
    2500 px ; reduite a la largeur d'un ecran, elle ne se lit plus. On decoupe l'acte aux
    memes fractions de boite d'encre que celles qui ont servi a le lire.

    ET ON DECOUPE LARGE. Le 24 aout 2026, le généalogiste a signale des decoupes « cropees trop
    court » : des fractions relevees a l'oeil rognaient la derniere ligne, donc la
    signature. UNE LIGNE DE VOISINAGE EN TROP NE COUTE RIEN ; une signature coupee coute
    la moitie de l'interet de l'image. D'ou `pad`, applique en haut et en bas.

    LE NOM SUIT LA CONVENTION DU NAS, ET ELLE N'EST PAS DECORATIVE :

        date type NOM - commune registre vNNNc.png
        1668-07-18 mariage PEYRET x MEY - Saint-Pal E-depot 2-5 v024G.png

    C'est ce nom qui se retrouve dans `source_file`, et c'est par lui qu'on relit une
    image trois mois plus tard sans rouvrir le portail.
    """
    p, taille = zb(dossier, n, side, max(0.0, y0 - pad), min(1.0, y1 + pad), nom,
                   x0=x0, x1=x1, div=div, out=dest, rot=rot)
    return p, taille


# ----------------------------------------------------------------------------- cadrer
def _planche(cells, dest, out=OUT, vertical=True, nettete=1.6):
    police = config.police_pil(20 if vertical else 30)
    if vertical:
        W = max(c.width for _, c in cells)
        sh = Image.new("L", (W, sum(c.height + 26 for _, c in cells)), 255)
        d, y = ImageDraw.Draw(sh), 0
        for lab, c in cells:
            d.line([(0, y), (W, y)], fill=120, width=2)
            d.text((4, y + 2), lab, fill=0, font=police)
            sh.paste(c, (0, y + 24))
            y += c.height + 26
    else:
        H = max(c.height for _, c in cells)
        sh = Image.new("L", (sum(c.width + 14 for _, c in cells) + 14, H + 40), 255)
        d, x = ImageDraw.Draw(sh), 14
        for lab, c in cells:
            d.line([(x - 7, 0), (x - 7, H + 40)], fill=110, width=2)
            d.text((x, 4), lab, fill=0, font=police)
            sh.paste(c, (x, 38))
            x += c.width + 14
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, dest)
    ImageEnhance.Sharpness(sh).enhance(nettete).save(p)
    return p, sh.size


def tetes(dossier, a, b, dest, part=0.14, echelle=0.62, out=OUT, rot=(), seuil=0.010,
          par=None):
    """Empile la bande HAUTE de chaque demi-page des vues [a, b] : cadrer sans lire.

    La premiere ligne d'un acte porte toujours sa date : quinze vues en une image
    trouvent l'annee dans un registre sans table, contre trente images a 3 100 jetons.

    RECADRE SUR LA BOITE D'ENCRE, ET C'EST TOUTE LA DIFFERENCE. Couper une fraction du
    HAUT DE LA PAGE ne rend que du papier sur les registres anciens, dont la marge haute
    fait le quart du feuillet. On prend donc le haut de l'ENCRE, quelle que soit la mise
    en page. `par` decoupe en plusieurs planches : au-dela de ~2000 px de haut, l'image
    est reduite avant lecture et le gain disparait.
    """
    cells = []
    for n in (plage(a) if b is None else range(int(a), int(b) + 1)):
        for side, pim in pages(vue(dossier, n), rot):
            x0, y0, x1, y1 = boite(np.asarray(pim), seuil)
            c = pim.crop((x0, y0, x1, y0 + int((y1 - y0) * part)))
            f = MAX / max(c.width, c.height) * echelle
            c = ImageOps.autocontrast(
                c.resize((int(c.width * f), int(c.height * f)), Image.LANCZOS), cutoff=1)
            cells.append(("v%03d%s" % (n, side), c))
    if not par:
        return _planche(cells, dest, out)
    base, ext = os.path.splitext(dest)
    return [_planche(cells[k:k + par], "%s%d%s" % (base, k // par, ext or ".png"), out)
            for k in range(0, len(cells), par)]


def marges(dossier, a, b, prefixe, frac=0.22, par=6, haut=1900, out=OUT, rot=(), seuil=0.010,
           pivot=0, x0=0.0):
    """Empile la BANDE DE GAUCHE de chaque demi-page, pleine hauteur : balayer un hameau.

    La marge porte le TYPE d'acte et le HAMEAU (« B. de brandy bas », « Ent. d'Usson »),
    et c'est un bon filtre POUR UNE CIBLE RARE -- un hameau qui revient deux fois par
    registre. Rendue a peu pres a sa taille native, donc lisible sans etre agrandie pour
    rien. 0,22 NE SUFFIT PAS SUR UNE PAGE DE GAUCHE, dont la boite d'encre commence au
    bord dechire : 0,34 avec quatre cellules par planche rend la marge lisible des deux
    cotes sans depasser les 2000 px au-dela desquels l'image est reduite.

    `pivot` FAIT TOURNER CHAQUE BANDE, ET C'EST UN RECENSEMENT QUI L'A DEMANDE. Sur une
    liste nominative, la colonne 2 « DES RUES dans les villes » porte le nom de la rue
    ECRIT VERTICALEMENT, une seule fois, en travers des trente lignes de la page : la
    bande de marge le contient donc toujours, mais couche. `pivot=-90` le redresse, et la
    planche s'empile alors verticalement -- une ligne par vue, le nom de rue en clair.
    Sans ca on lit une page entiere a 3 600 jetons pour un seul mot.

    `x0` DEPLACE LA BANDE, ET LA MARGE N'EST PLUS QU'UN CAS PARTICULIER. Sur un registre
    regle en colonnes -- une liste nominative, un tableau de matricules --, la colonne
    qu'on veut balayer n'est pas au bord : les PATRONYMES d'un recensement sont en 6e
    position, vers 0,30 de la boite d'encre. Sans ce decalage il fallait lire la page
    entiere, soit dix-sept pages a 3 600 jetons pour chercher un nom dans une rue.
    """
    cells = []
    for n in (plage(a) if b is None else range(int(a), int(b) + 1)):
        for side, pim in pages(vue(dossier, n), rot):
            bx, y0, x1, y1 = boite(np.asarray(pim), seuil)
            L = x1 - bx
            g = bx + int(L * x0)
            c = pim.crop((g, y0, min(x1, g + int(L * frac)), y1))
            if pivot:
                c = c.rotate(pivot, expand=True)
            f = haut / max(c.height, c.width) if pivot else haut / c.height
            c = c.resize((max(1, int(c.width * f)), max(1, int(c.height * f))),
                         Image.LANCZOS)
            cells.append(("v%03d%s" % (n, side),
                          ImageOps.autocontrast(c, cutoff=1)))
    faits = []
    for k in range(0, len(cells), par):
        faits.append(_planche(cells[k:k + par], "%s%d.png" % (prefixe, k // par),
                              out, vertical=bool(pivot), nettete=1.7))
    return faits


# ---------------------------------------------------------------------------------- CLI
def _rot():
    v = os.environ.get("NAS_ROT", "")
    return [x for x in v.replace(";", ",").split(",") if x.strip()]


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "l":
        for etiq, chemin in registres(a[1] if len(a) > 1 else ""):
            print("%-52s %s" % (etiq, chemin))
    elif a[0] in ("t", "m") and len(a) > 2 and ("," in a[2] or "-" in a[2].lstrip("-")):
        # UNE LISTE DE VUES A LA PLACE DE « debut fin » : « 30,60,90 » ou « 30-42,120 ».
        # Le `None` glisse a la place de la borne haute, et les arguments qui suivent
        # retrouvent leur rang -- meme ligne de commande, un argument de moins.
        b = a[:3] + [None] + a[3:]
        f = tetes if a[0] == "t" else marges
        kw = dict(rot=_rot())
        if a[0] == "t":
            kw["par"] = int(b[6]) if len(b) > 6 else None
        else:
            kw["par"] = int(b[6]) if len(b) > 6 else 6
            kw["pivot"] = int(b[7]) if len(b) > 7 else 0
            kw["x0"] = float(b[8]) if len(b) > 8 else 0.0
        r = f(reg(b[1]), b[2], None, b[4],
              float(b[5]) if len(b) > 5 else (0.14 if a[0] == "t" else 0.22), **kw)
        for p in (r if isinstance(r, list) else [r]):
            print(p, flush=True)
    elif a[0] == "t":
        # `par` MANQUAIT A LA LIGNE DE COMMANDE, ET SON ABSENCE POUSSAIT A ECRIRE UN SCRIPT
        # JETABLE — la faute meme que ce fichier existe pour empecher. `tetes()` sait
        # decouper depuis le debut ; seul le CLI l'ignorait, si bien qu'une planche de
        # trente vues rendait une image de 16 000 px de haut, reduite avant lecture donc
        # illisible. Sept cellules tiennent sous les 2000 px : c'est le defaut utile.
        r = tetes(reg(a[1]), int(a[2]), int(a[3]), a[4],
                  float(a[5]) if len(a) > 5 else 0.14, rot=_rot(),
                  par=int(a[6]) if len(a) > 6 else None)
        for p in (r if isinstance(r, list) else [r]):
            print(p, flush=True)
    elif a[0] == "m":
        for p in marges(reg(a[1]), int(a[2]), int(a[3]), a[4],
                        float(a[5]) if len(a) > 5 else 0.22,
                        int(a[6]) if len(a) > 6 else 6, rot=_rot(),
                        pivot=int(a[7]) if len(a) > 7 else 0,
                        x0=float(a[8]) if len(a) > 8 else 0.0):
            print(p, flush=True)
    elif a[0] == "z":
        kw = {"div": a[9] == "1"} if len(a) > 9 else {}
        print(zb(reg(a[1]), int(a[2]), a[3], float(a[4]), float(a[5]), a[6],
                 float(a[7]) if len(a) > 7 else 0.0,
                 float(a[8]) if len(a) > 8 else 1.0, rot=_rot(), **kw))
    elif a[0] == "d":
        kw = {"div": a[9] == "1"} if len(a) > 9 else {}
        print(decoupe(reg(a[1]), int(a[2]), a[3], float(a[4]), float(a[5]), a[6],
                      float(a[7]) if len(a) > 7 else 0.0,
                      float(a[8]) if len(a) > 8 else 1.0, rot=_rot(), **kw))
    else:
        d = reg(a[0])
        for n in range(int(a[1]), int(a[2]) + 1):
            for side, _ in pages(vue(d, n), _rot()):
                q, t = rendre(d, n, side, rot=_rot())
                print(q, t, round(t[0] * t[1] / 750), flush=True)
