# -*- coding: utf-8 -*-
"""MEMOIRE DES HOMMES — le portail du ministere des armees, moteur ARKOTHEQUE.

CE N'EST PAS UN PORTAIL D'ARCHIVES DEPARTEMENTALES — ni commune, ni registre d'etat civil —
mais il a sa fiche `memoire-des-hommes` dans `portails.json` depuis le 18 septembre 2026,
sous `dept: null`. C'est d'ailleurs CETTE PREMIERE LIGNE qui a rattrape la fiche : elle la
donnait sans moteur, faute de le lire dans le titre de sa section au carnet.
Il sert les JOURNAUX DES MARCHES
ET OPERATIONS de 14-18 (serie 26 N, 18 000 journaux, ~1,5 million de pages), les morts
pour la France, les fusilles, les historiques regimentaires, les sepultures de guerre.
C'est la ou se lit ce qu'une citation resume en trois lignes.

    LE PIEGE QUI COUTE UNE SEANCE ENTIERE : LE SITE A CHANGE DE DOMAINE
    -------------------------------------------------------------------
    L'ancienne adresse, `www.memoiredeshommes.SGA.defense.gouv.fr`, est encore celle que
    rendent les moteurs de recherche, tous les forums de genealogie et les liens de
    `data/ou-chercher.md`. ELLE NE REPOND PLUS :

        certificat TLS expire le 20 novembre 2025 (curl : SEC_E_CERT_EXPIRED)
        403 Forbidden sur TOUTE URL du domaine, racine comprise, meme avec un vrai Chrome

    Ce n'est pas une defense anti-robot : le site est mort a cette adresse. La Wayback
    Machine le confirme — dernier 200 le 1er octobre 2025, puis 403 a chaque passage
    jusqu'a aujourd'hui. LA BONNE ADRESSE N'A PLUS LE `sga` :

        https://www.memoiredeshommes.defense.gouv.fr

    Elle repond 200 a une requete Python ordinaire, sans WAF et sans jeton anti-robot.

    ET `/moteur` NE CHERCHE PAS — IL DECRIT
    ---------------------------------------
    `arkotheque.py` interroge `/_recherche-api/moteur` et lit les resultats dans
    `resultats.html` : c'est vrai a l'AD49, c'est FAUX ici. Le meme endpoint rend le
    bon `total` — donc les filtres marchent — mais `count` reste a 0 et `html` vide,
    ce qui donne l'impression d'un filtre qui echoue alors qu'il compte juste.

    C'est `/_recherche-api/SEARCH-SIMPLE/{id}` qui rend les fiches, et l'`{id}` est
    l'entier `id` du moteur, pas son `refUnique`. On ne le devine pas :

        LA TABLE DE ROUTAGE SYMFONY EST PUBLIQUE, `/js/routing` — 589 routes en JSON,
        chemins et parametres compris. Cinq minutes contre une soiree de tatonnement,
        et c'est la que se lisent `search-simple`, `visionneuse-infos`,
        `render-fiche` et `_recherche-images/show`.

    ET `?size=full`, SINON ON PERD L'IMAGE. Meme piege qu'en Haute-Loire et en
    Maine-et-Loire : sans lui l'endpoint plafonne a 2000 px sur le grand cote. Sur un
    JMO le master ne fait que 2282 x 1638 — la difference est mince, mais elle est
    gratuite. Une valeur inventee (`size=!4000,4000`) rend 3 ko de HTML d'erreur, pas
    une image : TOUJOURS verifier qu'on a bien recu un JPEG.

Les quatre commandes :

    python memoiredeshommes.py unite "55e regiment d'infanterie"   # les JMO d'une unite
    python memoiredeshommes.py fiche arko_fiche_669e823918807      # cote, dates, images
    python memoiredeshommes.py vues  arko_fiche_669e823918807      # nombre de vues
    python memoiredeshommes.py tire  arko_fiche_669e823918807 <dossier> [debut] [fin]
"""
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

# La verification TLS de cette machine est reparee par `scripts/archives/tls.py` :
# le magasin de racines de Windows porte une racine perimee, et tous ces portails sont
# chez Let's Encrypt. Un import suffit, il agit sur tout le processus.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tls  # noqa: F401,E402

# NE PAS REASSIGNER sys.stdout AU NIVEAU DU MODULE : ca ferme le flux de l'importateur.
BASE = "https://www.memoiredeshommes.defense.gouv.fr"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}
CADENCE = 0.6

# Les moteurs du portail, releves le 8 septembre 2026 sur les pages « faire une recherche ».
# `id` est l'entier qu'attend /search-simple/{id} ; `ref` le refUnique qu'attendent les
# parametres. Les deux sont necessaires, et ils ne se deduisent pas l'un de l'autre.
MOTEURS = {
    "jmo": {"ref": "arko_default_66b0ee3a6d947", "id": 13, "intitule": "JMO 1ere GM",
            "champ_unite": "arko_default_66b0f16c2c11a",     # « Armee ou unite »
            "champ_cote": "arko_default_66b0f1315be94",      # « Cote »
            "champ_libre": "arko_default_66b0f1314b47a",     # « Recherche libre »
            "champ_image": "arko_default_66b0f1f0a88b1"},    # le champ qui porte les vues
}


def _get(url, binaire=False, essais=7, timeout=120):
    """Un GET QUI INSISTE, et il le faut ici plus qu'ailleurs.

    LE 503 DE CE PORTAIL N'EST PAS UNE PANNE, C'EST UNE IMAGE QUI N'EST PAS ENCORE
    FABRIQUEE. La premiere demande d'une vue jamais servie rend 503 avec 115 ko de page
    d'erreur ; la meme URL, redemandee quelques secondes plus tard, rend le JPEG. Un
    tireur qui abandonne au premier 503 conclut que le journal n'est pas en ligne — et
    ces vues-la sont justement celles que personne n'a encore ouvertes, donc exactement
    celles qu'on vient chercher. Sept essais, attente doublee jusqu'a une demi-minute.
    """
    for essai in range(essais):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                       timeout=timeout).read()
            return b if binaire else b.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500 and e.code != 429:
                raise                     # une URL fausse ne devient pas vraie en 7 essais
            if essai == essais - 1:
                raise
        except Exception:
            if essai == essais - 1:
                raise
        time.sleep(min(2 ** essai, 30))


def _params(m, filtres, debut=0, taille=50):
    """La grammaire des parametres d'Arkotheque : tout est prefixe par le refUnique du
    moteur, et chaque filtre vit dans un groupe numerote. Identique a l'AD45."""
    ref = m["ref"]
    g = "%s--filtreGroupes[groupes][0]" % ref
    p = [("%s--ficheFocus" % ref, ""),
         ("%s--filtreGroupes[mode]" % ref, "simple"),
         ("%s--filtreGroupes[op]" % ref, "AND")]
    for champ, valeur in filtres:
        p += [("%s[%s][op]" % (g, champ), "AND"),
              ("%s[%s][q][]" % (g, champ), valeur)]
    p += [("%s--from" % ref, str(debut)), ("%s--resultSize" % ref, str(taille))]
    return "&".join(urllib.parse.quote(k, safe="") + "=" + urllib.parse.quote(v, safe="")
                    for k, v in p)


def cherche(moteur, filtres, debut=0, taille=50):
    """Rend (total, [fiches]). UNE FICHE N'EST PAS UN DOCUMENT : l'inventaire est un
    arbre, et une reponse melange les noeuds (« 55e regiment d'infanterie ») et les
    feuilles (« J.M.O. - 24 fevrier 1917-9 octobre 1918 - 26 N 644/16 »). Le drapeau
    `dernierNiveau` distingue les deux ; c'est lui qu'on regarde avant de tirer des vues.
    """
    m = MOTEURS[moteur]
    u = "%s/_recherche-api/search-simple/%d?%s" % (BASE, m["id"],
                                                   _params(m, filtres, debut, taille))
    d = json.loads(_get(u))
    return d["total"], d["results"]


def _detail(refuniq, moteur="jmo"):
    m = MOTEURS[moteur]
    return _get("%s/_recherche-api/render-fiche/%s/%s/%s/detail/html"
                % (BASE, m["ref"], refuniq, "arko_default_66b38461144b2"))


def fiche(refuniq, moteur="jmo"):
    """{cote, date, id_fiche, id_arkofile, arbre} — tout ce qu'il faut pour tirer les vues.

    L'IDENTIFIANT NUMERIQUE NE SE DEVINE PAS. L'URL d'une image est
    `/_recherche-images/show/{idFiche}/image/{idArkoFile}/{rang}` : deux entiers qui ne
    figurent ni dans le refUnique ni dans la cote. Ils sont dans le HTML du detail, dans
    l'attribut `data-visionneuse` du bouton de la visionneuse — on les LIT.
    """
    h = _detail(refuniq, moteur)
    out = {"refUnique": refuniq}
    for champ, clef in (("cote", "cote"), ("date", "date")):
        mm = re.search(r'data-type-champ="%s"[^>]*>(.*?)</' % champ, h, re.S)
        if mm:
            out[clef] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", mm.group(1))).strip()
    mm = re.search(r'data-term="([^"]+)"', h)
    if mm and "cote" not in out:
        out["cote"] = mm.group(1)
    mm = re.search(r'_recherche-images/show/(\d+)/image/(\d+)/', h)
    if mm:
        out["id_fiche"], out["id_arkofile"] = int(mm.group(1)), int(mm.group(2))
    mm = re.search(r'data-visionneuse-url="([^"]+)"', h)
    if mm:
        out["visionneuse"] = BASE + mm.group(1).replace("&amp;", "&")
    # L'arbre de classement, du fonds a la piece — c'est lui qui donne le contexte
    # archivistique qu'une cote seule ne dit pas.
    out["arbre"] = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).strip()
                    for x in re.findall(r'<li[^>]*class="[^"]*fil[^"]*"[^>]*>(.*?)</li>',
                                        h, re.S)]
    return out


def vues(refuniq, moteur="jmo"):
    """Le nombre de vues, LU dans la reponse de la visionneuse et non compte a la main.

    C'est l'application de « lire la reponse en entier avant de deviner une URL » : la
    liste `medias[0].sources` porte une entree par vue, avec son URL exacte ET les
    dimensions du master dans `infosImage`. Rien a paginer, rien a essayer.
    """
    f = fiche(refuniq, moteur)
    if "visionneuse" not in f:
        raise SystemExit("cette fiche ne porte pas d'images : %s" % refuniq)
    d = json.loads(_get(f["visionneuse"]))
    src = d["medias"][0]["sources"]
    taille = None
    for s in src:
        if s.get("infosImage"):
            taille = (s["infosImage"]["width"], s["infosImage"]["height"])
            break
    return len(src), taille, [s["src"] for s in src], f


def tire(refuniq, dossier, debut=1, fin=None, moteur="jmo", cadence=CADENCE):
    """Tire les vues en `vNNN.jpg` — la convention du NAS, donc `nas.py` les lit ensuite.

    `debut` et `fin` sont des NUMEROS DE VUE a partir de 1, comme partout ailleurs dans
    ce dossier ; le portail, lui, compte les rangs a partir de 0. La conversion est faite
    ici une fois pour toutes : ailleurs, ce decalage a fait lire un acte pour un autre.
    """
    n, taille, urls, f = vues(refuniq, moteur)
    fin = min(fin or n, n)
    os.makedirs(dossier, exist_ok=True)
    ecrits = []
    for v in range(debut, fin + 1):
        dest = os.path.join(dossier, "v%03d.jpg" % v)
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            ecrits.append(dest)
            continue
        b = _get(urls[v - 1] + "?size=full", binaire=True)
        # UNE VALEUR DE TAILLE INVENTEE REND DU HTML, PAS UNE IMAGE, ET SANS ERREUR HTTP.
        if not b.startswith(b"\xff\xd8"):
            raise SystemExit("la vue %d n'est pas un JPEG (%d octets) — verifier l'URL"
                             % (v, len(b)))
        io.open(dest, "wb").write(b)
        ecrits.append(dest)
        time.sleep(cadence)
    return ecrits, f, taille


# ------------------------------------------------------------------------ ligne de commande
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    a = sys.argv[1:]
    if not a:
        print(__doc__.split("Les quatre commandes :")[1].strip())
        sys.exit(0)

    if a[0] == "unite":
        total, res = cherche("jmo", [(MOTEURS["jmo"]["champ_unite"], a[1])], taille=100)
        print("%d fiche(s) pour « %s »\n" % (total, a[1]))
        for x in res:
            t = re.sub(r"<[^>]+>", "", x["intitule"])
            print("  %-26s %-3s %s" % (x["refUnique"],
                                       "piece" if x["dernierNiveau"] else "", t[:96]))

    elif a[0] == "fiche":
        f = fiche(a[1])
        for k in ("cote", "date", "id_fiche", "id_arkofile"):
            if k in f:
                print("  %-12s %s" % (k, f[k]))

    elif a[0] == "vues":
        n, taille, _, f = vues(a[1])
        print("  %s — %s" % (f.get("cote", "?"), f.get("date", "")))
        print("  %d vues, master %s" % (n, "x".join(map(str, taille)) if taille else "?"))

    elif a[0] == "tire":
        deb = int(a[3]) if len(a) > 3 else 1
        fin = int(a[4]) if len(a) > 4 else None
        ecrits, f, taille = tire(a[1], a[2], deb, fin)
        print("%d vue(s) dans %s — %s, master %s"
              % (len(ecrits), a[2], f.get("cote", "?"),
                 "x".join(map(str, taille)) if taille else "?"))

    else:
        print(__doc__.split("Les quatre commandes :")[1].strip())
