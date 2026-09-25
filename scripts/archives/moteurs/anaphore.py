# -*- coding: utf-8 -*-
"""ANAPHORE — produit « Bach », et c'est le moteur de l'AD52 (Haute-Marne).

    python anaphore.py 52 cherche "Saint-Dizier naissances"
    python anaphore.py 52 cherche "" --lieu "Saint-Dizier (Haute-Marne, France)" \
                                    --type "baptême ou naissance"
    python anaphore.py 52 facettes --lieu "Saint-Dizier (Haute-Marne, France)"
    python anaphore.py 52 vues  E/1E/AD52_1E0448_104_001
    python anaphore.py 52 tirer E/1E/AD52_1E0448_104_001 1 30 "<archives>/.../AD52 - Saint-Dizier/N 1912"

NEUVIEME MOTEUR DU DOSSIER, ET LE DERNIER DES TROIS QUI N'AVAIENT QUE LEUR RECONNAISSANCE.
Il se signe par sa feuille de style `/assetic/css/compiled/bach.css` — le
`<meta name="generator">` ne dit que le nom du service. C'est un Symfony ; la table de
routage `/js/routing` n'est PAS publiee ici, contrairement a l'AD49.

────────────────────────────────────────────────────────────────────────────────────────
CE QUE LA FICHE DISAIT, ET CE QUE LE CODE A CORRIGE LE 19 SEPTEMBRE 2026

1. ⛔ « LE CERTIFICAT EST EXPIRE, il faut ssl.CERT_NONE ». **FAUX, et c'etait la cinquieme
   fois.** `import tls` suffit : le probleme n'a jamais ete chez l'AD52, c'est le magasin de
   racines que Windows sert a Python. `tls.py` porte la liste des quatre autres sites
   accuses a tort. On ne desactive pas la verification d'un certificat.

2. ⛔ « LA PARTIE {q} DU CHEMIN N'A PAS FILTRE : /archives/search/default/1 E 448/1 rend
   327 867 reponses, c'est-a-dire le fonds entier. Le plein texte se passe autrement — non
   elucide. » **Elucide : LA RECHERCHE EST UN POST, avec un jeton CSRF.**

       GET  /archives/search/default          ouvre la session, porte searchQuery[_token]
       POST /archives/do-search/default       searchQuery[query] + le jeton
            -> redirige vers /archives/search/default/<q>?view=list

   Le chemin n'est donc pas une API : c'est l'URL ou le POST vous depose. L'appeler a froid
   rend le fonds entier parce que la session ne porte aucune requete — exactement ce que la
   fiche avait mesure sans pouvoir l'expliquer.

3. ⚠️ « DEUX PAIRES filter_field/filter_value DANS LA MEME URL NE SE SONT PAS COMBINEES.
   Le filtre s'empile probablement DANS LA SESSION, un a la fois. A verifier. » **Verifie,
   et c'est bien ca** : chaque facette se pose par une requete, sur la session, et le
   bandeau « Filtres selectionnes » les accumule. Une URL qui en porte deux n'en applique
   qu'une. `facettes=` de ce module les pose l'une apres l'autre.

⚠️ ET BACH CLASSE AU LIEU DE FILTRER, comme FamilySearch. « Saint-Dizier naissances » rend
**36 068 reponses** triees par pertinence — ce n'est pas un filtre, c'est un classement. Ce
qui filtre vraiment, ce sont les FACETTES. Ne jamais lire un total de recherche libre comme
un nombre d'actes trouves.

────────────────────────────────────────────────────────────────────────────────────────
LES IMAGES SONT LE POINT FACILE, ET IL N'Y A AUCUNE API A CHERCHER

La visionneuse est une application separee et moderne, sans rapport avec Bach. Sa page fait
~134 Ko et EMBARQUE LA LISTE COMPLETE DES VUES en clair, sous forme de noms de fichiers.
On lit la page et on compte — 322 vues pour 1 E 448/104. Aucun IIIF, aucun manifeste.

Et le chemin de la visionneuse est donne par chaque resultat de recherche, dans l'attribut
`alt` de sa vignette : `E/1E/AD52_1E0448_101_001/`. Il ne se reconstruit pas depuis la cote.
"""
import html as H
import http.cookiejar
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tls  # noqa: F401  — repare la verification TLS pour tout le processus

CONF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "portails.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

# Les champs de facette, lus sur le portail. Les libelles, eux, se LISENT dans les liens de
# facette d'une page de resultats : « Saint-Dizier (Haute-Marne, France) » ne se reconstruit
# pas depuis « Saint-Dizier ».
CHAMPS = {
    "lieu": "cGeogname",
    "personne": "cPersname",
    "titre": "archDescUnitTitle",
    "type": "dyndescr_cGenreform_none",
    "niveau": "dyndescr_cGenreform_liste-niveau",
    "domaine": "dyndescr_cSubject_liste-grandDomaine",
    "sousdomaine": "dyndescr_cSubject_liste-sousDomaine",
    "numerise": "dao",            # Oui / Non
    "statut": "cLegalstatus",
}


def base(dept):
    c = json.load(io.open(CONF, encoding="utf-8"))
    for p in c["portails"]:
        if p.get("dept") == str(dept) and p.get("moteur") == "anaphore":
            return p["base"].rstrip("/")
    raise SystemExit("aucun portail Anaphore pour le departement %s dans portails.json"
                     % dept)


def _txt(h):
    t = re.sub(r"(?s)<(script|style).*?</\1>", " ", h)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"(?s)<[^>]+>", " ", t)))


class Portail(object):
    """UNE SESSION A COOKIES, TOUJOURS. Sans elle le moteur rend le fonds entier sans le
    dire, et les facettes ne s'empilent pas."""

    def __init__(self, dept):
        self.base = base(dept)
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.derniere = None

    def _ouvre(self, u, donnees=None, essais=2):
        d = urllib.parse.urlencode(donnees).encode() if donnees is not None else None
        for i in range(essais):
            try:
                r = self.op.open(urllib.request.Request(u, data=d, headers=UA), timeout=120)
                return r.url, r.read().decode("utf-8", "replace")
            except Exception:
                if i + 1 == essais:
                    raise
                time.sleep(3)

    # ------------------------------------------------------------------ la recherche
    def pose(self, q="", facettes=None, portee="default"):
        """Pose la requete par POST, puis empile les facettes une a une. Rend le HTML de la
        premiere page.

        ⚠️ SEPARE DE `cherche` A DESSEIN. La premiere version reposait la requete ET toutes
        ses facettes A CHAQUE PAGE : quatre requetes par page, trente-six pages, et le
        balayage de Saint-Dizier ne finissait pas en deux minutes. La requete vit dans la
        SESSION — on la pose une fois, puis on tourne les pages.
        """
        u, h = self._ouvre("%s/archives/search/%s" % (self.base, portee))
        m = re.search(r'name="searchQuery\[_token\]"[^>]*value="([^"]+)"', h)
        if not m:
            raise SystemExit("jeton CSRF introuvable — le formulaire a change")
        u, h = self._ouvre("%s/archives/do-search/%s" % (self.base, portee),
                           {"searchQuery[query]": q,
                            "searchQuery[_token]": m.group(1),
                            "searchQuery[keep_filters]": "1",
                            "searchQuery[perform_search]": ""})
        # UNE FACETTE PAR REQUETE : deux paires dans la meme URL n'en appliquent qu'une.
        # Elles se CUMULENT bien, mesure le 19 septembre 2026 sur Saint-Dizier :
        # 17 813 sans facette -> 1 264 avec le lieu -> 355 en ajoutant la typologie.
        for nom, valeur in (facettes or {}).items():
            champ = CHAMPS.get(nom, nom)
            u, h = self._ouvre("%s?%s" % (u.split("?")[0], urllib.parse.urlencode(
                {"filter_field": champ, "filter_value": valeur})))
        self.derniere = u
        return h

    def cherche(self, q="", facettes=None, page=1, portee="default"):
        """Une page de resultats. Rend (total, [resultats])."""
        h = self.pose(q, facettes, portee)
        if page > 1:
            _, h = self._ouvre("%s/%d?view=list"
                               % (self.derniere.split("?")[0].rstrip("/"), page))
        return self.lit(h)

    def parcours(self, q="", facettes=None, pages_max=60, portee="default"):
        """TOUTES les fiches, la requete posee UNE fois.

        S'arrete quand une page n'apporte plus rien de neuf — jamais sur un compte annonce,
        qui ment des qu'un doublon s'y glisse.
        """
        h = self.pose(q, facettes, portee)
        racine = self.derniere.split("?")[0].rstrip("/")
        total, r = self.lit(h)
        vus, tout = set(), []
        for page in range(1, pages_max + 1):
            if page > 1:
                _, h = self._ouvre("%s/%d?view=list" % (racine, page))
                _, r = self.lit(h)
            neuf = [x for x in r if x["id"] and x["id"] not in vus]
            if not neuf:
                break
            vus.update(x["id"] for x in neuf)
            tout += neuf
        return total, tout

    def lit(self, h):
        t = _txt(h)
        if "Aucun résultat" in t:
            return 0, []
        m = re.search(r"Résultats\s+\d+\s+à\s+\d+\s+sur\s+([\d\s\u00a0]+)", t)
        total = int(re.sub(r"\D", "", m.group(1))) if m else None
        out = []
        for a in re.findall(r"(?s)<article id=\"result_.*?</article>", h):
            ident = re.search(r'<article id="result_([^"]+)"', a)
            vis = re.search(r'alt="([^"]*/)"', a)
            titre = re.search(r'(?s)<h\d[^>]*>\s*<a[^>]*>(.*?)</a>', a)
            champs = dict(re.findall(
                r"\|([^|]{3,30}) :\| \|([^|]{1,90}?)\|",
                re.sub(r"\s+", " ", H.unescape(re.sub(r"(?s)<[^>]+>", "|", a)))))
            brut = re.sub(r"\s+", " ", H.unescape(re.sub(r"(?s)<[^>]+>", " ", a))).strip()
            cote = re.search(r"\b(\d+\s*[A-Z]+\s*\d+(?:/\d+)?)\b", brut)
            out.append({
                "id": ident.group(1) if ident else None,
                "titre": re.sub(r"\s+", " ", H.unescape(
                    re.sub(r"(?s)<[^>]+>", " ", titre.group(1)))).strip() if titre else "",
                "cote": cote.group(1) if cote else "",
                "visionneuse": vis.group(1).rstrip("/") if vis else None,
                "lieu": champs.get("Lieu", ""),
                "notice": "%s/archives/show/%s" % (self.base, ident.group(1))
                          if ident else None})
        return total, out

    def facettes(self, q="", champ="lieu", facettes=None, combien=40):
        """Les valeurs proposees pour un champ, AVEC LEUR LIBELLE EXACT — c'est la seule
        facon correcte de remplir `facettes=` : un libelle ne se reconstruit pas."""
        self.cherche(q, facettes)
        u, h = self._ouvre(self.derniere)
        ch = CHAMPS.get(champ, champ)
        vus = []
        for m in re.finditer(
                r'filter_field=%s&(?:amp;)?filter_value=([^"&]+)[^>]*>(.*?)</a>'
                % re.escape(ch), h, re.S):
            lib = urllib.parse.unquote_plus(m.group(1))
            if lib not in vus:
                vus.append(lib)
        return vus[:combien]

    # ------------------------------------------------------------------ les images
    def vues(self, chemin):
        """Les noms de fichiers d'un registre. `chemin` = « E/1E/AD52_1E0448_104_001 »,
        tel que l'attribut `alt` d'un resultat le donne."""
        u, h = self._ouvre("%s/viewer/series/%s/" % (self.base, chemin.strip("/")))
        cote = chemin.strip("/").split("/")[-1]
        noms = sorted(set(re.findall(re.escape(cote) + r"_\d{3,5}\.jpg", h)))
        return noms

    def tire(self, chemin, a, b, dossier, cadence=1.0):
        """Ecrit les vues a..b dans `dossier`, nommees vNNN.jpg — la convention du NAS."""
        noms = self.vues(chemin)
        if not noms:
            raise SystemExit("aucune vue lue sur la page de la visionneuse : %s" % chemin)
        os.makedirs(dossier, exist_ok=True)
        serie = "/".join(chemin.strip("/").split("/")[:-1])
        cote = chemin.strip("/").split("/")[-1]
        ecrits = []
        for n in range(a, min(b, len(noms)) + 1):
            nom = noms[n - 1]
            dest = os.path.join(dossier, "v%03d.jpg" % n)
            if os.path.exists(dest) and os.path.getsize(dest) > 20000:
                ecrits.append(dest)
                continue
            u = ("%s/viewer/show/full/%s/%s/%s?isMobOrTab=false"
                 % (self.base, serie, cote, nom))
            r = self.op.open(urllib.request.Request(u, headers=UA), timeout=180)
            d = r.read()
            if len(d) < 20000:
                raise SystemExit("vue %d trop legere (%d octets) — %s" % (n, len(d), u))
            io.open(dest, "wb").write(d)
            ecrits.append(dest)
            print("  v%03d  %6.1f Ko" % (n, len(d) / 1024.0))
            time.sleep(cadence)
        return ecrits


# ------------------------------------------------------------------------ ligne de commande
def _arg(av, nom, defaut=None):
    return av[av.index(nom) + 1] if nom in av else defaut


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    av = sys.argv[1:]
    if len(av) < 2:
        print(__doc__.split("\n\n")[1])
        sys.exit(1)
    dept, action = av[0], av[1]
    p = Portail(dept)
    fac = {n: _arg(av, "--" + n) for n in CHAMPS if "--" + n in av}

    if action == "cherche":
        q = av[2] if len(av) > 2 and not av[2].startswith("--") else ""
        total, r = p.cherche(q, fac, page=int(_arg(av, "--page", 1)))
        print("total annonce : %s   (rendus : %d)\n" % (total, len(r)))
        for x in r:
            print("%-12s %-30s %-26s %s" % (x["cote"], x["titre"][:30], x["lieu"][:26],
                                            x["visionneuse"] or ""))
        if total and total > 500 and not fac:
            print("\n⚠️ Bach CLASSE par pertinence, il ne filtre pas : un gros total sur une "
                  "recherche libre n'est pas un nombre d'actes. Poser des facettes "
                  "(--lieu, --type), dont les libelles se lisent par `facettes`.")
    elif action == "facettes":
        champ = _arg(av, "--champ", "lieu")
        q = av[2] if len(av) > 2 and not av[2].startswith("--") else ""
        for v in p.facettes(q, champ, fac):
            print(" ", v)
    elif action == "vues":
        n = p.vues(av[2])
        print("%d vues   %s ... %s" % (len(n), n[0] if n else "-", n[-1] if n else "-"))
    elif action == "tirer":
        f = p.tire(av[2], int(av[3]), int(av[4]), av[5])
        print("%d vues dans %s" % (len(f), av[5]))
    else:
        raise SystemExit("actions : cherche | facettes | vues | tirer")
