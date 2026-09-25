# -*- coding: utf-8 -*-
"""EST-CE QUE LES MOTEURS MARCHENT ENCORE, PORTAIL PAR PORTAIL ?

    python scripts/archives/moteurs_essai.py              # tous
    python scripts/archives/moteurs_essai.py 52 58 68     # quelques-uns
    python scripts/archives/moteurs_essai.py --joignable  # l'etage 1 seulement, rapide

POURQUOI. `portails_coherence.py` verifie que le registre, le carnet et le README disent la
MEME chose. Il ne verifie pas qu'ils disent VRAI. Deux pannes l'ont montre le 19 septembre
2026, et aucune n'aurait ete vue par un controle de coherence :

  * l'AD67 portait `archives.bas-rhin.fr`, qui redirige depuis vers `archives67.alsace.eu`.
    La redirection marchait, donc AUCUN script n'echouait — une fiche peut se perimer sans
    que rien ne le signale.
  * Toulouse rendait « Desole, vous n'etes pas autorise a acceder a ce site » a toutes ses
    adresses, racine comprise, et un vrai Chrome recevait le meme refus.

DEUX ETAGES, ET ILS NE DISENT PAS LA MEME CHOSE :

  ETAGE 1 — L'ADRESSE DE LA FICHE EST-ELLE ENCORE JUSTE ? Une requete par portail, en
  `urllib`. Quatre etats, et **DEUX D'ENTRE EUX VEULENT DIRE « LE PORTAIL VA BIEN »** :
  `ok` et `mur`.

  ⚠️ UN MUR N'EST PAS UNE PANNE, ET LE COMPTE RENDU A DEJA MENTI LA-DESSUS. Le 19 septembre
  2026, la premiere version rendait « 23 ok · 29 mur · 3 injoignables » et ca se lisait
  comme un bilan d'echec — alors que les vingt-neuf portails derriere Anubis, Cloudflare ou
  F5 fonctionnent parfaitement et qu'on les ouvre avec Chrome depuis des semaines.
  L'etage 1 les sonde en `urllib`, qui prend le mur PAR CONSTRUCTION : il mesure la
  presence du mur, jamais la sante du portail. Le rapport groupe donc **vivant** (ok +
  mur) contre **a regarder** (refus + injoignable), et c'est l'etage 2 — avec Chrome quand
  il faut — qui dit si le moteur marche.

  ETAGE 2 — LE MODULE PASSE. On appelle le module avec de vrais parametres et on regarde
  s'il rend quelque chose. C'est le seul etage qui prouve quelque chose, et il ne tourne
  que sur les fiches qui portent un bloc `essai`.

⚠️ UN PORTAIL SANS BLOC `essai` N'EST PAS UN PORTAIL QUI MARCHE : c'est un portail qu'on
n'a pas essaye. Le compte rendu les separe, et il ne faut pas lire l'un pour l'autre —
c'est la regle « ne jamais affirmer au-dela du travail fait », appliquee aux outils.

LE BLOC `essai` D'UNE FICHE :

    "essai": {"fonds": "etat_civil", "commune": "ANLEZY", "minimum": 5}

`fonds` designe une entree de `recherche.formulaires` quand le moteur en a ; `commune` est
le libelle EXACT, qui se lit sur le formulaire et ne se reconstruit jamais ; `minimum` est
le nombre de notices en dessous duquel on considere que le moteur a change de comportement.
"""
import io
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "moteurs"))
import tls  # noqa: F401

CONF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portails.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

MURS = [("Anubis", r"within\.website|anubis|not a bot"),
        ("Cloudflare", r"cloudflare|attack detected"),
        ("F5/Shape", r"/TSPD/|your support id is"),
        ("renvoi JS", r"window\.location\.href='/redirect_|requires JS enabled")]
REFUS = r"n'êtes pas autoris|not authorized|accès refus|403 forbidden"


def joignable(url):
    """Une requete. Rend (etat, detail) — ok / mur / refus / injoignable."""
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60)
        h = r.read().decode("utf-8", "replace")
    except Exception as e:
        return "injoignable", str(e)[:70]
    for nom, motif in MURS:
        if re.search(motif, h, re.I):
            return "mur", "%s (%d o)" % (nom, len(h))
    if re.search(REFUS, h, re.I):
        return "refus", "le portail ferme la porte (%d o)" % len(h)
    detail = "%d o" % len(h)
    if r.url.rstrip("/") != url.rstrip("/"):
        # UNE REDIRECTION N'EST PAS UNE PANNE, MAIS ELLE PERIME UNE FICHE EN SILENCE.
        detail += "  ⚠️ redirige vers %s" % r.url
    return "ok", detail


def module_passe(p):
    """Appelle le module avec le bloc `essai` de la fiche. Rend (etat, detail)."""
    e = p.get("essai")
    if not e:
        return "non essaye", "pas de bloc `essai` dans la fiche"
    m = p.get("moteur")
    try:
        if m == "naoned":
            import naoned
            f = (p.get("recherche", {}).get("formulaires") or {}).get(
                e.get("fonds", "etat_civil"))
            if not f:
                return "impossible", "formulaire « %s » absent de la fiche" % e.get("fonds")
            commune = e.get("commune")
            if not commune:
                # UN LIBELLE SE LIT, IL NE SE RECONSTRUIT PAS — et les trois portails
                # Naoned du dossier ont trois conventions differentes : « Épernay (Marne,
                # France) », « Illfurth » nu, « ANLEZY » en capitales. Quand la fiche ne
                # donne qu'un motif, on demande au portail sa forme exacte : ca teste du
                # meme coup le chemin qui fait rendre zero en silence quand on l'invente.
                libs = naoned.libelles(p["base"], f, e["motif"])
                if not libs:
                    return "KO", "aucun libelle pour le motif « %s »" % e["motif"]
                # ⚠️ PRENDRE LE PREMIER LIBELLE EST UN PIEGE, mesure sur l'AD19 : le motif
                # « Brive » y rend d'abord « Brive sont consultables sur le site des
                # Archives municipales », une PHRASE du site attrapee par la recherche
                # plein texte, avant les trois vrais libelles. On retient donc le plus
                # court de ceux qui COMMENCENT par le motif — un libelle de commune est
                # court et commence par son nom, une phrase ne fait ni l'un ni l'autre.
                bons = [x for x in libs
                        if x.lower().startswith(e["motif"].lower()) and len(x) < 60]
                candidats = sorted(bons, key=len) or libs[:3]
            else:
                candidats = [commune]
            # ⚠️ ET PLUSIEURS LIBELLES PEUVENT COEXISTER SANS QUE TOUS FILTRENT. A l'AD19,
            # le vocabulaire porte « Brive-la-Gaillarde », « Brive-la-Gaillarde (Corrèze,
            # France) » ET « Brive-la-Gaillarde, Corrèze, France ; paroisse) » — le
            # premier rend ZERO, le deuxieme rend les registres. On les essaie donc dans
            # l'ordre au lieu de parier, et le compte rendu dit lequel a marche.
            r = []
            for commune in candidats:
                r = naoned.recherche(p["base"], f, commune, champs=naoned.noms(p))
                if r:
                    break
            e = dict(e, commune=commune)          # pour le compte rendu
        elif m == "anaphore":
            import anaphore
            r = anaphore.Portail(p["dept"]).facettes(e.get("q", ""), "lieu")
        elif m == "arkotheque" and p.get("http_simple"):
            import arkotheque
            r = arkotheque.communes(p["dept"]) if hasattr(arkotheque, "communes") else None
            if r is None:
                return "impossible", "arkotheque.py n'expose pas `communes`"
        elif m == "aspnet-webforms":
            import albodoro
            r = albodoro.commune(e["commune"])
        elif m == "4d":
            import quatred
            ok, msg = quatred.controle()
            return ("ok" if ok else "KO"), msg[:90]
        else:
            return "non essaye", "aucun essai automatique pour le moteur « %s »" % m
    except Exception as ex:
        return "KO", "%s : %s" % (type(ex).__name__, str(ex)[:70])
    n = len(r or [])
    mini = e.get("minimum", 1)
    ou = (" sur « %s »" % e["commune"]) if e.get("commune") else ""
    if n < mini:
        return "KO", "%d reponse(s)%s, moins que le minimum attendu (%d)" % (n, ou, mini)
    return "ok", "%d reponse(s)%s" % (n, ou)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    av = [a for a in sys.argv[1:] if not a.startswith("--")]
    etage1 = "--joignable" in sys.argv
    c = json.load(io.open(CONF, encoding="utf-8"))
    fiches = [p for p in c["portails"] if p.get("base")
              and (not av or p.get("dept") in av or p.get("id") in av)]

    print("%d fiche(s) a essayer\n" % len(fiches))
    print("%-16s %-22s %-13s %-34s %s"
          % ("dept", "moteur", "joignable", "detail", "module"))
    print("-" * 118)
    compte = {}
    for p in sorted(fiches, key=lambda z: (z.get("dept") or "zz", z["id"])):
        # `sonde` quand la racine ne se laisse pas sonder — l'AD84 rend un 302 que
        # `urlopen` ne suit pas, alors que son moteur repond parfaitement. On ne change
        # pas `base` pour autant : le module en a besoin telle quelle.
        etat, detail = joignable(p.get("sonde") or p["base"])
        compte[etat] = compte.get(etat, 0) + 1
        mod = ""
        if not etage1 and etat in ("ok", "mur"):
            e2, d2 = module_passe(p)
            compte["module:" + e2] = compte.get("module:" + e2, 0) + 1
            mod = "%s — %s" % (e2, d2)
        print("%-16s %-22s %-13s %-34s %s"
              % (p.get("dept") or p["id"], p.get("moteur") or "—", etat, detail[:34], mod))

    # UN MUR VEUT DIRE « VIVANT », ET LE GROUPEMENT LE DIT AU LIEU DE LAISSER LIRE UN
    # BILAN D'ECHEC LA OU IL N'Y EN A PAS.
    vivant = compte.get("ok", 0) + compte.get("mur", 0)
    souci = compte.get("refus", 0) + compte.get("injoignable", 0)
    print("\nVIVANT     : %d  (%d en clair, %d derriere un mur — Anubis, Cloudflare ou F5, "
          "que Chrome franchit)" % (vivant, compte.get("ok", 0), compte.get("mur", 0)))
    print("A REGARDER : %d  (%d refus, %d injoignables)"
          % (souci, compte.get("refus", 0), compte.get("injoignable", 0)))
    if not etage1:
        print("MODULE    : " + " · ".join("%s %d" % (k[7:], v)
                                          for k, v in sorted(compte.items())
                                          if k.startswith("module:")))
        print("\n⚠️ « non essaye » N'EST PAS « marche » : c'est une fiche sans bloc `essai`.")
