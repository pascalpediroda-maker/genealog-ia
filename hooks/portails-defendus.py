# -*- coding: utf-8 -*-
"""Interdit tout acces BRUT aux portails qui bannissent.

POURQUOI CE FICHIER EXISTE. Le 27 aout 2026, le Portale Antenati a banni l'IP de la
maison TROIS FOIS dans la meme journee — son proprietaire ne pouvait plus l'ouvrir
lui-meme. A chaque fois la meme cause : des requetes HTTP brutes envoyees en rafale.

Un garde-fou avait ete ecrit DANS le module — cadence, budget horaire, quarantaine sur
403. Il a ete contourne dans l'heure par un client brut tape a la main : un compteur ne
protege que ce qui passe par lui.

Une regle ecrite ne suffit pas quand on peut passer a cote. Celle-ci est un HOOK :
c'est le harnais qui refuse, pas la memoire de la session.

⛔ ET IL A FALLU UN SECOND FILET, LE 25 SEPTEMBRE 2026. La premiere version ne lisait
que la LIGNE DE COMMANDE. Un client brut tape a la main s'y voit ; une requete ecrite
DANS un script ne s'y voit pas — la commande dit seulement « python mon_script.py ».

Or c'est le script qui bannit : une commande tapee a la main envoie UNE requete, une
boucle en envoie mille. Le garde-fou arretait donc le geste qui bannit le moins et
laissait passer celui qui bannit le plus. On regarde desormais AUSSI ce qui s'ecrit
dans un fichier, et on refuse avant que le fichier existe.

⚠️ CE QUE CA NE COUVRE PAS : une adresse construite par concatenation, ou un script
deja sur le disque. Le seul verrou etanche serait dans le runtime. Ces deux filets
ferment les deux endroits ou ca a reellement echoue, pas tous ceux qu'on peut imaginer.

⚠️ ET CE FICHIER EST DANS SA PROPRE LISTE D'EXEMPTIONS, forcement : il cite les motifs
qu'il detecte. Sans l'exemption, le garde-fou interdit de lire et d'ecrire son propre
code — et on est tente de le rediger en concatenant des morceaux pour passer, ce qui
demontre la faille en meme temps que ca rend la source illisible. Essaye le
25 septembre 2026, puis defait.
"""
import json
import re
import sys

# Les clients HTTP bruts, sous toutes leurs formes utiles ici.
BRUT = re.compile(
    r"""(?xi)
    \bcurl\b | \bwget\b
  | \bInvoke-WebRequest\b | \bInvoke-RestMethod\b | \biwr\b | \birm\b
  | Net\.WebClient | System\.Net\.Http
  | \burllib\b | \bhttpx\b | \brequests\.(get|post|head|request)\b
  | \bhttp\.client\b | \bpycurl\b | \baiohttp\b
    """
)

# UN PORTAIL DEFENDU = ce qui le nomme, le seul chemin autorise, et ce qu'on dit.
# Pour en ajouter un : une entree de plus, et rien d'autre a toucher.
DEFENDUS = [
    {
        "nom": "Antenati",
        "nomme": re.compile(r"antenati", re.I),
        "autorise": re.compile(r"moteurs[/\\]antenati\.js|portails-defendus\.py", re.I),
        "message": (
            "Ce portail ne se requete QUE par scripts/archives/moteurs/antenati.js "
            "(cadence + budget + quarantaine). Un acces brut a fait bannir l'IP "
            "trois fois dans la meme journee.\n\n"
            "  node scripts/archives/moteurs/antenati.js etat       # sans rien demander au site\n"
            "  node scripts/archives/moteurs/antenati.js chercher '\"Valvasone Arzene\"'\n"
            "  node scripts/archives/moteurs/antenati.js registre <ark>\n\n"
            "Et si c'est ferme : ON ATTEND. Chaque tentative rallonge le bannissement."
        ),
    },
]

CONTENUS = ("content", "new_string", "file_text", "text")


def refuse(message):
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }))
    return 0


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    ti = data.get("tool_input") or {}
    if not isinstance(ti, dict):
        return 0

    cmd = ti.get("command") or ""
    cible = str(ti.get("file_path") or "")
    ecrits = [v for c in CONTENUS for v in (ti.get(c),) if isinstance(v, str) and v]

    for p in DEFENDUS:
        # 1. la ligne de commande
        if isinstance(cmd, str) and cmd and p["nomme"].search(cmd) \
                and not p["autorise"].search(cmd) and BRUT.search(cmd):
            return refuse(p["message"])
        # 2. ce qu'on s'apprete a ecrire dans un fichier
        if p["autorise"].search(cible):
            continue
        for v in ecrits:
            if p["nomme"].search(v) and BRUT.search(v):
                return refuse(p["message"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
