# -*- coding: utf-8 -*-
"""Pose les reponses de l'utilisateur la ou le code les cherche.

Lance par le hook `SessionStart` du plugin, en forme `command` + `args` — voir
`hooks/hooks.json` et le pourquoi ci-dessous.

⚠️ PIEGE PAYE LE 25 SEPTEMBRE 2026 : la documentation montre un exemple de forme exec
ecrit `"exec": [...]`, et `claude plugin validate` le REFUSE — « Invalid command hook
(command: Invalid input); entry ignored at runtime ». Le hook n'aurait rien fait, en
silence, et les chemins ne seraient jamais arrives jusqu'au code. La forme acceptee est
`"command": "python"` plus `"args": [...]`. Passer le manifeste au validateur ne se
discute pas : un hook invalide est ignore, pas signale.

CE QU'IL FAIT. Claude Code demande ses chemins a l'utilisateur au moment ou il active
le plugin (`userConfig` du manifeste), et range les reponses dans SON settings.json. Le
code Python, lui, ne les voit pas : `${user_config.*}` ne se substitue que dans les
skills, les serveurs MCP et les `args` d'un hook — pas dans l'environnement d'une
commande que Claude lance ensuite avec Bash.

Ce script fait le pont. Il recoit les valeurs en arguments et les ecrit dans
`${CLAUDE_PLUGIN_DATA}/config.json`, ou `scripts/config.py` va les lire.

⚠️ POURQUOI LA FORME EXEC, ET PAS UN `command` DE SHELL. Un hook en forme shell qui
porte `${user_config.*}` est REFUSE par Claude Code : la valeur passerait par un shell
qui la reinterpreterait. Un chemin Windows avec un espace — « D:/Mes archives »
— suffirait a le casser. La forme exec passe chaque valeur comme un argument, sans shell.

⚠️ ET IL N'ECRASE PAS UNE VALEUR PAR DU VIDE. `photos_root` et `artefact_url` sont
facultatifs ; si l'utilisateur les laisse vides, on ne remplace pas ce qui etait la.
Sinon une session qui ouvre le plugin sans reremplir le dialogue perdrait l'adresse de
la page publiee — et republierait a cote, ce que ce dossier a deja paye trois fois.
"""
import io
import json
import os
import sys

CLES = ("archives_root", "photos_root", "corpus_dir", "artefact_url")

# Le nom que `scripts/config.py` attend, pour chaque reponse du dialogue.
VERS = {"archives_root": "archives", "photos_root": "photos",
        "corpus_dir": "data", "artefact_url": "artefact"}


def main(argv):
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not base:
        return 0                       # hors plugin : rien a faire, et c'est normal
    os.makedirs(base, exist_ok=True)
    p = os.path.join(base, "config.json")

    try:
        courant = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        courant = {}

    neuf = dict(courant)
    for cle, valeur in zip(CLES, argv):
        valeur = (valeur or "").strip()
        if valeur:                     # jamais ecraser par du vide — voir l'en-tete
            neuf[VERS[cle]] = valeur

    if neuf != courant:
        tmp = p + ".tmp"
        io.open(tmp, "w", encoding="utf-8", newline="\n").write(
            json.dumps(neuf, ensure_ascii=False, indent=1) + "\n")
        os.replace(tmp, p)

    manquants = [c for c in ("archives", "data") if not neuf.get(c)]
    if manquants:
        # Un SessionStart peut parler a Claude : on le dit une fois, sans bloquer.
        print("genealogie : il manque %s — ouvrir /config pour les renseigner."
              % " et ".join(manquants))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
