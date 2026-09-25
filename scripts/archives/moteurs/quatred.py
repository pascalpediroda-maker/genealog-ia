# -*- coding: utf-8 -*-
"""4D (4th Dimension) — le moteur des Archives MUNICIPALES de Toulouse.

    python quatred.py controle                      # ⚠️ A LANCER EN PREMIER, TOUJOURS
    python quatred.py cherche --nom PERESSON
    python quatred.py cherche --annee 1912 --type naissance

⛔ ET IL FAUT COMMENCER PAR LA : CE MODULE N'A JAMAIS TOURNE CONTRE LE PORTAIL.

Ecrit le 19 septembre 2026 a partir d'une fiche complete — le formulaire, son action, ses
quinze champs et sa phrase de vide avaient tous ete releves le 2 septembre. Mais ce
jour-la le portail a rendu, a TOUTES les adresses y compris sa racine :

    « Desole, vous n'etes pas autorise a acceder a ce site ! »        (HTTP 200)
    HTTP 401 sur /4DCGI/Web_VoirLesFonds

**Et un vrai Chrome fenetre recoit exactement le meme refus.** Ce n'est donc pas une
protection anti-robot, ni un jeton de session perime : le portail refuse la connexion, comme
Geneanet l'avait fait le 28 aout pour tout le monde depuis cette ligne. La regle du dossier
s'applique : quand un acces echoue, se demander d'abord si le probleme est bien la ou on le
croit — et ne pas s'acharner sur le pilotage quand c'est le site qui est ferme.

**Donc : lancer `controle` avant de croire quoi que ce soit de ce module.** Il refuse de
rendre un resultat tant que le portail n'a pas prouve qu'il repond.

────────────────────────────────────────────────────────────────────────────────────────
⚠️ CE N'EST PAS LE PORTAIL DES AD31. Toulouse tient ses propres Archives municipales,
2 rue des Archives, 31500 Toulouse, 05 36 25 23 80. Les Archives DEPARTEMENTALES de la
Haute-Garonne sont une autre maison, sur Boscop, et elles ont l'etat civil des AUTRES
communes du departement. Chercher un Toulousain aux AD31 — ou un habitant de Muret ici —
c'est chercher dans le mauvais fonds. La fiche a porte le numero « 31 » pendant cinq jours,
et c'etait un piege.

⚠️ L'INDEX NE COUVRE QUE LES NAISSANCES, ET SEULEMENT 1900-1925. Mesure le 2 septembre 2026,
79 359 notices pour tout Toulouse :

    1900, 1902, 1905, 1910, 1912, 1915, 1920, 1922, 1924, 1925  -> des resultats
    1926, 1927, 1930, 1939                                      -> RIEN
    1920 naissance -> oui ; 1920 mariage -> RIEN ; 1920 deces -> RIEN
    1750 mariage, 1850 mariage, 1875 -> RIEN

**Chercher un mariage ou un deces par nom sur ce portail rend TOUJOURS zero, quel que soit
le nom. Ce n'est pas un negatif, c'est un hors-perimetre.** La borne 1925 est la regle des
cent ans ; elle glissera sur 1926 en 2027.

Le moteur rend du HTML serveur : pas de JavaScript a executer, un POST suffit, `urllib`
passe. Mais le serveur est LENT — timeout genereux et un reessai.
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
import tls  # noqa: F401

CONF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "portails.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

FORMULAIRE = "/4DCGI/Web_ActesRechSimple/ILUMP25828"
ACTION = "/4DCGI/WEB_ActesResultRechSimple/ILUMP25828"
VIDE = "aucune notice ne correspond"
REFUS = "n'êtes pas autorisé à accéder"

CHAMPS = {
    "type": "T",            # indif | naissance | mariage | deces
    "nom": "wNom3",
    "prenom": "wPrenom",
    "nom_epouse": "wNomEP3",
    "prenom_epouse": "wPrenomEP",
    "lieu": "wLieuEP",
    "cote": "wcote",
    "num": "wnum",
    "annee": "wannee",
    "date": "wdate",        # jj/mm/aaaa
    "du": "wdatedeb",
    "au": "wdatefin",
}

_op = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def base():
    c = json.load(io.open(CONF, encoding="utf-8"))
    for p in c["portails"]:
        if p.get("moteur") == "4d":
            return p["base"].rstrip("/")
    raise SystemExit("aucun portail 4D dans portails.json")


def _ouvre(u, donnees=None, essais=2):
    d = urllib.parse.urlencode(donnees, encoding="utf-8").encode() if donnees else None
    for i in range(essais):
        try:
            r = _op.open(urllib.request.Request(u, data=d, headers=UA), timeout=120)
            return r.read().decode("utf-8", "replace")
        except Exception:
            # LE SERVEUR EST LENT ET REND DES READ TIMEOUT SOUS CHARGE : un reessai, pas
            # une conclusion.
            if i + 1 == essais:
                raise
            time.sleep(5)


def _txt(h):
    t = re.sub(r"(?s)<(script|style).*?</\1>", " ", h)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"(?s)<[^>]+>", " ", t)))


def controle():
    """LE CONTROLE POSITIF, ET IL N'EST PAS FACULTATIF.

    `wNom3=MARTIN` et `wannee=1900` doivent rendre des resultats. Tant que l'un des deux ne
    rend rien, AUCUN zero de ce portail ne veut dire « la personne n'y est pas » : il veut
    dire que le portail ne repond pas, ou que la requete est hors perimetre.

    Rend (ok, message).
    """
    try:
        h = _ouvre(base() + FORMULAIRE)
    except Exception as e:
        return False, "le formulaire ne repond pas : %s" % str(e)[:120]
    if REFUS in _txt(h):
        return False, ("LE PORTAIL REFUSE LA CONNEXION — « Desole, vous n'etes pas autorise "
                       "a acceder a ce site ! ». Un vrai Chrome recoit le meme refus : ce "
                       "n'est pas un blocage anti-robot, c'est le site qui est ferme a "
                       "cette ligne. Reessayer plus tard, et demander a le généalogiste si son "
                       "propre navigateur y entre.")
    for critere in ({"nom": "MARTIN"}, {"annee": "1900"}):
        r = _cherche_brut(**critere)
        if not r:
            return False, ("le controle positif %s ne rend RIEN — le portail repond mais "
                           "l'index ne se comporte pas comme mesure. Ne rien conclure d'un "
                           "zero." % critere)
    return True, "controle positif passe : MARTIN et 1900 rendent des resultats."


def _cherche_brut(**criteres):
    d = {v: "" for v in CHAMPS.values()}
    for k, v in criteres.items():
        if k not in CHAMPS:
            raise SystemExit("critere inconnu : %s — connus : %s"
                             % (k, ", ".join(sorted(CHAMPS))))
        d[CHAMPS[k]] = v
    d.setdefault("T", "indif")
    if not d.get("T"):
        d["T"] = "indif"
    d["warrobase"] = "1"
    d["btout"] = "Lancer la recherche"
    b = base()
    _ouvre(b + FORMULAIRE)                  # ouvre la session 4D
    h = _ouvre(b + ACTION, d)
    t = _txt(h)
    if REFUS in t:
        raise SystemExit("le portail refuse la connexion — lancer `controle`")
    if VIDE in t:
        return []
    return lit(h, b)


def lit(h, b):
    """Les notices du tableau de resultats."""
    out = []
    for tr in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", h):
        cel = [re.sub(r"\s+", " ", H.unescape(re.sub(r"(?s)<[^>]+>", " ", c))).strip()
               for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)]
        cel = [c for c in cel if c]
        if len(cel) < 2:
            continue
        lien = re.search(r'href="([^"]*4D(?:CGI|action)[^"]*)"', tr)
        out.append({"cellules": cel,
                    "lien": (b + lien.group(1)) if lien and lien.group(1).startswith("/")
                            else (lien.group(1) if lien else None)})
    return out


def cherche(**criteres):
    """⚠️ REFUSE DE CHERCHER TANT QUE LE CONTROLE POSITIF N'EST PAS PASSE. Un zero rendu par
    un portail qui ne repond pas ressemble exactement a un zero rendu par un portail qui
    repond, et ce dossier a deja paye cette confusion."""
    ok, msg = controle()
    if not ok:
        raise SystemExit("⛔ " + msg)
    t = criteres.get("type")
    if t in ("mariage", "deces"):
        print("⚠️ L'INDEX NE PORTE QUE LES NAISSANCES 1900-1925 : une recherche de %s y rend "
              "toujours zero, quel que soit le nom. Ce n'est pas un negatif." % t,
              file=sys.stderr)
    return _cherche_brut(**criteres)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    av = sys.argv[1:]
    if not av or av[0] not in ("controle", "cherche"):
        print(__doc__.split("\n\n")[1])
        sys.exit(1)
    if av[0] == "controle":
        ok, msg = controle()
        print(("✅ " if ok else "⛔ ") + msg)
        sys.exit(0 if ok else 1)
    crit = {av[i][2:]: av[i + 1] for i in range(1, len(av) - 1, 2)
            if av[i].startswith("--")}
    r = cherche(**crit)
    print("%d notice(s)\n" % len(r))
    for x in r:
        print(" · ".join(x["cellules"])[:140])
