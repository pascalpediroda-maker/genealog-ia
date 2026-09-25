# -*- coding: utf-8 -*-
"""ANOM — l'etat civil des anciens territoires d'outre-mer (caomec2).

Developpement propre des Archives nationales d'outre-mer : il ne ressemble a aucun autre
moteur du dossier -- ni Boscop, ni Arkotheque, ni Naoned, ni Anaphore, ni Archinoe, ni 4D,
ni Prismia, ni Gaia. Recherche en GET sur `resultats.php`, visionneuse OpenSeadragon, images
en DeepZoom.

    ⛔ CE MODULE N'ANNONCE PAS SON RANG, ET C'EST VOULU. La premiere version s'ouvrait sur
    « NEUVIEME MOTEUR DU DOSSIER » -- faux : `anaphore.py` portait deja ce numero, et le
    dossier comptait deja DEUX « septiemes » (`archinoe.py` et `prismia.py`). Un rang ecrit
    a la main est un rang que la session suivante recompte de travers, parce que chacune
    incremente le dernier qu'elle a vu. **La source de verite est `_meta.moteurs` de
    `portails.json`**, et `moteurs_table.py` la rend -- c'est ce que ce meme fichier dit
    depuis le 5 septembre 2026 : « une table recopiee est une table qui ment tot ou tard ».

    python anom.py registres ALGERIE CONSTANTINE 1923        # les registres d'une annee
    python anom.py vues 40976                                # combien de vues, et lesquelles
    python anom.py tirer 40976 141 150                       # assembler les vues sur X:
    python anom.py tirer 40976 141 150 --niveau 12           # moitie de resolution, 4x moins cher
    python anom.py noms ALGERIE PAIR                         # le suggesteur de patronymes
    python anom.py chercher ALGERIE PAIRE                    # la recherche nominative

QUATRE PIEGES, TOUS PAYES LE 20 SEPTEMBRE 2026.

1. LE SERVEUR NE PARLE QUE `http`. Toute requete forcee en `https` echoue par
   UNSUPPORTED_PROTOCOL. **Ce n'est PAS un CERTIFICATE_VERIFY_FAILED** : le magasin de
   certificats est hors de cause, et `tls.py` n'y peut rien. C'est l'outil qui reecrit
   `http` en `https` qui se trompe de site. `urllib` en http simple suffit.

2. LES PAGES SE SERVENT EN ISO-8859-1, declaration comprise.

3. LES TUILES DEEPZOOM SONT EN `.jpeg`, PAS EN `.jpg`. Le manifeste le dit -- `Format="jpeg"`
   -- et une requete en `.jpg` rend 404. Trois niveaux ont ete essayes en `.jpg` avant de lire
   le manifeste : c'est exactement le faux negatif que la skill interdit.

4. LA RECHERCHE NOMINATIVE S'ARRETE VERS 1904, MAIS LE FONDS, NON. Chercher un nom apres
   cette date ne rend rien -- et ca ne prouve rien. Les registres posterieurs existent et se
   FEUILLETTENT : on interroge alors par commune + type d'acte + annee, sans nom, et on lit
   les vues. Constantine 1923 porte ainsi 419 vues de naissances.
"""
import io
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HOST = "http://anom.archivesnationales.culture.gouv.fr"
BASE = HOST + "/caomec2/"
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 os.pardir, os.pardir))
import config

NAS = config.archives()
UA = {"User-Agent": "Mozilla/5.0"}


def _get(url, brut=False, essais=3):
    if not url.startswith("http"):
        url = BASE + url
    for k in range(essais):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=45) as r:
                b = r.read()
            return b if brut else b.decode("iso-8859-1", "replace")
        except Exception:
            if k == essais - 1:
                raise
            time.sleep(1.5 * (k + 1))


def _q(chemin, **params):
    return _get(chemin + "?" + urllib.parse.urlencode(params, encoding="iso-8859-1"))


# ------------------------------------------------------------------- recherche
def noms(territoire, motif):
    """Les patronymes qui EXISTENT dans la base — evite d'essayer une graphie a l'aveugle."""
    h = _q("noms.php", territoire=territoire, commune="", nom=motif)
    out = []
    for bloc in h.split("::::"):
        m = re.match(r"\s*([A-ZÀ-Ü' -]+)\s*\((\d+)\)", bloc)
        if m:
            out.append((m.group(1).strip(), int(m.group(2))))
    return out


def _lignes(html):
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        reg = re.search(r"registre=(\d+)", tr)
        cells = [" ".join(re.sub(r"<[^>]+>", " ", c).split())
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
        cells = [c for c in cells if c and c not in ("&#160;", "\xa0")]
        if cells and cells[0].isdigit():
            out.append((reg.group(1) if reg else None, cells[1:]))
    return out


def chercher(territoire, nom="", commune="", typeacte="", annee=""):
    """Toutes les lignes, pagination comprise. Le parametre de page est `page`, LU dans le HTML."""
    tout, page = [], 1
    while True:
        h = _q("resultats.php", territoire=territoire, nom=nom, prenom="", commune=commune,
               typeacte=typeacte, annee=annee, debut="", fin="", page=str(page))
        lot = _lignes(h)
        if not lot or (tout and lot[0] == tout[0]):
            break
        tout += lot
        m = re.search(r"Page\s*\d+\s*de\s*(\d+)", re.sub(r"<[^>]+>", " ", h))
        if not m or page >= int(m.group(1)):
            break
        page += 1
    return tout


# ------------------------------------------------------------------- les vues
def vues(registre):
    """[(numero, chemin_dzi)] — lus dans osd.php, jamais fabriques."""
    h = _q("osd.php", territoire="ALGERIE", registre=str(registre))
    trouves = re.findall(r'"((?:\\/|/)caomec2[^"]+?_(\d{4})\.dzi)"', h)
    return [(int(n), c.replace("\\/", "/")) for c, n in trouves]


def _dzi(chemin):
    x = _get(HOST + chemin)
    return (int(re.search(r'Width="(\d+)"', x).group(1)),
            int(re.search(r'Height="(\d+)"', x).group(1)),
            int(re.search(r'TileSize="(\d+)"', x).group(1)),
            int(re.search(r'Overlap="(\d+)"', x).group(1)))


def assembler(chemin_dzi, niveau=None, cadence=0.05):
    """Recompose une vue a partir de ses tuiles DeepZoom. Rend une image PIL."""
    from PIL import Image
    W, H, TS, OV = _dzi(chemin_dzi)
    nmax = 0
    while (1 << nmax) < max(W, H):
        nmax += 1
    n = nmax if niveau is None else min(niveau, nmax)
    ech = 1 << (nmax - n)
    w, h = -(-W // ech), -(-H // ech)
    cols, lignes = -(-w // TS), -(-h // TS)
    base = chemin_dzi[:-4] + "_files/%d/" % n
    im = Image.new("RGB", (w, h), "white")
    for cx in range(cols):
        for cy in range(lignes):
            try:
                t = Image.open(io.BytesIO(
                    _get(HOST + base + "%d_%d.jpeg" % (cx, cy), brut=True)))
            except Exception:
                continue                      # une tuile manquante ne perd pas la vue
            im.paste(t, (cx * TS - (OV if cx else 0), cy * TS - (OV if cy else 0)))
            time.sleep(cadence)
    return im


def tirer(registre, debut, fin, dossier=None, niveau=None):
    """Assemble les vues [debut, fin] et les range SUR LE NAS, jamais dans un temporaire."""
    vs = dict(vues(registre))
    dest = dossier or os.path.join(NAS, "ANOM - registre %s" % registre)
    os.makedirs(dest, exist_ok=True)
    faits = []
    for n in range(int(debut), int(fin) + 1):
        if n not in vs:
            print("vue %d absente du registre" % n)
            continue
        p = os.path.join(dest, "v%03d.jpg" % n)
        if os.path.exists(p) and os.path.getsize(p) > 80000:
            faits.append(p)
            continue
        im = assembler(vs[n], niveau)
        im.save(p, quality=90)
        faits.append(p)
        print("v%03d  %dx%d  -> %s" % (n, im.width, im.height, p), flush=True)
    return faits


# ------------------------------------------------------------------------ CLI
if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
    elif a[0] == "noms":
        for nom, n in noms(a[1], a[2]):
            print("%6d  %s" % (n, nom))
    elif a[0] == "chercher":
        for reg, cells in chercher(a[1], nom=a[2] if len(a) > 2 else ""):
            print("%-8s %s" % (reg or "-", " | ".join(cells)))
    elif a[0] == "registres":
        for reg, cells in chercher(a[1], commune=a[2], annee=a[3] if len(a) > 3 else "",
                                   typeacte=a[4] if len(a) > 4 else ""):
            print("%-8s %s" % (reg or "-", " | ".join(cells)))
    elif a[0] == "vues":
        vs = vues(a[1])
        print("%d vues, de %d a %d" % (len(vs), vs[0][0], vs[-1][0]))
    elif a[0] == "tirer":
        niv = int(a[a.index("--niveau") + 1]) if "--niveau" in a else None
        tirer(a[1], a[2], a[3], niveau=niv)
    else:
        print(__doc__)
