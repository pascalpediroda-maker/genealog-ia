# -*- coding: utf-8 -*-
"""LA SONDE OAI-PMH — « y a-t-il une porte a cote du mur qu'on crochete ? »

    python scripts/archives/oai.py              # sonde tous les fonds a `base`
    python scripts/archives/oai.py 43 49 17     # seulement ces departements
    python scripts/archives/oai.py --ecrire     # inscrit le resultat dans portails.json

POURQUOI ELLE EXISTE. Le dossier interroge les portails par la voie la plus chere et la
plus fragile : piloter un vrai Chrome sur du HTML. C'est justifie quand il n'y a rien
d'autre, et le dossier l'a paye assez souvent pour le savoir. Mais OAI-PMH est une NORME
d'archives, servie par beaucoup de portails, et personne ici ne l'avait jamais essayee.

CE QU'ELLE REND, ET POURQUOI C'EST DEUX REPONSES EN UNE REQUETE

  `?verb=Identify`            si ca repond, TOUT le catalogue est moissonnable : on
                              miroite l'inventaire une fois, en local, et on cherche
                              hors ligne au lieu d'interroger le portail a chaque fois.
  `?verb=ListMetadataFormats` dit si l'EAD est parmi les formats servis. L'EAD est le
                              format des instruments de recherche — fonds, serie, cote,
                              dates : exactement ce qu'on reconstitue a la main quand on
                              « liste les registres d'une commune ». Il ne se sonde pas
                              tout seul, il ARRIVE par OAI-PMH. D'ou une seule sonde.

⚠️ UN NEGATIF DE CETTE SONDE NE PROUVE PAS GRAND-CHOSE, ET IL FAUT L'ECRIRE. On essaie
une liste finie de chemins usuels ; un portail peut servir OAI-PMH ailleurs. Le resultat
se lit « aucun des chemins essayes ne repond », jamais « ce portail n'a pas d'OAI-PMH ».
La liste des chemins essayes est donc inscrite avec le resultat.
"""
import concurrent.futures as cf
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

try:
    import tls  # noqa: F401 — repare le magasin de certificats pour tout le processus
except Exception:
    pass

D = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.join(D, "portails.json")

# Les chemins usuels. Ordre : du plus frequent au plus rare.
#
# ⛔ CETTE LISTE A ETE ECRITE TROP COURTE, ET LE CONTROLE POSITIF L'A DIT TOUT DE SUITE.
# Premiere version : sept chemins sur l'hote du portail, et ZERO reponse sur 63 fonds.
# Avant d'ecrire ce negatif, trois depots OAI-PMH connus ont ete essayes — et LES TROIS
# auraient ete manques :
#
#     HAL               api.archives-ouvertes.fr/oai/hal/   autre hote, chemin profond
#     Internet Archive  archive.org/services/oai2.php       chemin absent de la liste
#     Persee            oai.persee.fr/oai                   SOUS-DOMAINE DEDIE
#
# Un depot OAI-PMH ne vit presque jamais a la racine du site qu'on regarde. D'ou, depuis
# le 20 septembre 2026 : plus de chemins, le sous-domaine `oai.<domaine>`, et surtout la
# PAGE D'ACCUEIL LUE pour y chercher un lien qui porte « oai » — c'est la regle du
# dossier, lire la reponse avant de deviner une URL.
CHEMINS = ["/oai", "/oai.php", "/oai2", "/oai-pmh", "/OAIHandler", "/oai/request",
           "/services/oai2.php", "/ws/oai", "/api/oai", "/cgi-bin/oai", "/oai/oai2.aspx",
           ""]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36"}
DELAI = 12


def demande(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=DELAI)
        return r.status, r.read(200000)
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return None, ("%r" % (e,)).encode("utf-8", "replace")


def texte(brut):
    for enc in ("utf-8", "iso-8859-1"):
        try:
            return brut.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def candidats(base):
    """Les URL a essayer : l'hote du portail, son sous-domaine `oai.`, et CE QUE LA PAGE
    D'ACCUEIL DESIGNE ELLE-MEME.

    Le dernier point est le seul qui ne devine rien, et c'est la regle du dossier : lire
    la reponse en entier avant d'inventer un chemin.
    """
    base = base.rstrip("/")
    m = re.match(r"(https?)://([^/]+)(.*)$", base)
    vus, sortie = set(), []

    def pose(u):
        if u not in vus:
            vus.add(u)
            sortie.append(u)

    for c in CHEMINS:
        pose(base + c)
    if m:
        schema, hote, _ = m.groups()
        nu = re.sub(r"^(www|archives|portail)\.", "", hote)
        for h in ("oai." + nu, "oai." + hote):
            for c in ("/oai", "/oai2/OAIHandler", "/oai/request", ""):
                pose("%s://%s%s" % (schema, h, c))

    # ce que la page d'accueil designe
    code, brut = demande(base + "/")
    if code == 200:
        s = texte(brut)
        for lien in re.findall(r'''["'\(]([^"'\(\)\s]*oai[^"'\(\)\s]*)["'\)]''', s, re.I):
            if lien.lower().startswith(("http://", "https://")):
                pose(lien.split("?")[0])
            elif lien.startswith("/"):
                pose(base + lien.split("?")[0])
    return sortie


def sonde(base):
    """Rend (url_oai, formats) ou (None, essayes)."""
    essayes = []
    for url in candidats(base):
        essayes.append(url)
        code, brut = demande(url + "?verb=Identify")
        if code != 200:
            continue
        s = texte(brut)
        # UNE REPONSE OAI-PMH SE RECONNAIT A SON ESPACE DE NOMS, PAS A SON CODE 200 :
        # beaucoup de portails rendent leur page d'accueil en 200 sur n'importe quel
        # chemin, et « 200 » pris pour « oui » est la famille de piege du parametre
        # invente qu'on ignore en silence.
        if "OAI-PMH" not in s or "<Identify" not in s:
            continue
        nom = re.search(r"<repositoryName>(.*?)</repositoryName>", s, re.S)
        code2, brut2 = demande(url + "?verb=ListMetadataFormats")
        formats = re.findall(r"<metadataPrefix>(.*?)</metadataPrefix>", texte(brut2))
        return url, {"repositoryName": (nom.group(1).strip() if nom else None),
                     "formats": formats,
                     "ead": any("ead" in f.lower() for f in formats)}
    return None, essayes


# LE CONTROLE POSITIF, ET IL N'EST PAS FACULTATIF. Une sonde qui ne rend que des « non »
# ne se distingue d'une sonde cassee que par la : trois depots dont on SAIT qu'ils
# repondent. C'est la regle du dossier — verifier comment l'outil dit « rien » avant de
# noter un negatif —, rendue executable.
TEMOINS = [
    ("HAL", "https://api.archives-ouvertes.fr/oai/hal/"),
    ("Internet Archive", "https://archive.org/services/oai2.php"),
    ("Persée", "http://oai.persee.fr/oai"),
]


def controle():
    print("CONTRÔLE POSITIF — trois dépôts dont on sait qu'ils répondent\n")
    bon = 0
    for nom, url in TEMOINS:
        code, brut = demande(url + "?verb=Identify")
        s = texte(brut)
        ok = code == 200 and "OAI-PMH" in s and "<Identify" in s
        bon += ok
        print("  %s %-18s %s" % ("✅" if ok else "⛔", nom, url))
    print("\n%d/%d témoins répondent.%s\n"
          % (bon, len(TEMOINS),
             "" if bon == len(TEMOINS) else "  ⛔ LA SONDE EST SUSPECTE : un négatif "
                                            "obtenu avec elle ne vaut rien."))
    return bon == len(TEMOINS)


def main():
    if "--controle" in sys.argv:
        sys.exit(0 if controle() else 1)
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    c = json.load(io.open(CONF, encoding="utf-8"))
    cibles = [p for p in c["portails"] if p.get("base")
              and (not args or str(p.get("dept")) in args or p.get("id") in args)]
    if not controle():
        print("On ne sonde pas avec un outil qui ne sait pas dire oui.")
        sys.exit(1)
    print("%d fonds à sonder — chemins usuels, sous-domaine `oai.`, "
          "et les liens de la page d'accueil\n" % len(cibles))

    trouves = {}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futurs = {ex.submit(sonde, p["base"]): p for p in cibles}
        for f in cf.as_completed(futurs):
            p = futurs[f]
            nom = "%s %s" % (p.get("dept") or "--", p.get("nom", p.get("id")))
            try:
                url, info = f.result()
            except Exception as e:
                print("   ?  %-52s %r" % (nom[:52], e))
                continue
            if url:
                trouves[p["id"]] = (url, info)
                print("✅ %-52s %s" % (nom[:52], url))
                print("      formats : %s%s" % (", ".join(info["formats"]) or "—",
                                                "   ⭐ EAD" if info["ead"] else ""))
            else:
                print("   ·  %-52s aucun des %d chemins" % (nom[:52], len(CHEMINS)))

    print("\n%d fonds sur %d répondent en OAI-PMH." % (len(trouves), len(cibles)))
    ead = [i for i, (_, v) in trouves.items() if v["ead"]]
    print("%d servent de l'EAD : %s" % (len(ead), ", ".join(ead) or "—"))

    if "--ecrire" in sys.argv:
        # ⛔ RECHARGER. La copie `c` date du DEBUT du sondage, qui dure plusieurs minutes,
        # et plusieurs sessions travaillent en parallele sur ce fichier : la reecrire
        # telle quelle emporterait tout ce qui est arrive entre-temps. On ne reporte que
        # les cles `oai`, par identifiant.
        c = json.load(io.open(CONF, encoding="utf-8"))
        for p in c["portails"]:
            if p["id"] in trouves:
                url, info = trouves[p["id"]]
                p["oai"] = {"url": url, "formats": info["formats"], "ead": info["ead"],
                            "repositoryName": info["repositoryName"],
                            "SONDE_LE": "2026-09-20"}
            elif p.get("base") and (not args or str(p.get("dept")) in args):
                p["oai"] = {"url": None, "SONDE_LE": "2026-09-20",
                            "NEGATIF_PARTIEL": "Aucun des chemins essayés ne répond en "
                                               "OAI-PMH : %s. Ça ne prouve pas que le "
                                               "portail n'en sert pas ailleurs."
                                               % ", ".join(CHEMINS)}
        tmp = CONF + ".tmp"
        io.open(tmp, "w", encoding="utf-8", newline="\n").write(
            json.dumps(c, ensure_ascii=False, indent=1) + "\n")
        os.replace(tmp, CONF)
        print("portails.json : résultats inscrits.")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
