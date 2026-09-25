# -*- coding: utf-8 -*-
"""CE QUE LE LECTEUR VOIT : du texte brut, en francais, qui parle des GENS.

    python scripts/corpus_affiche.py        # rapport, sort 1 si quelque chose passe

POURQUOI IL EXISTE. Trois regles du dossier ne portent QUE sur les champs affiches --
`summary`, `narrative`, `narrative_for` -- et les trois sont purement mecaniques : il n'y a
rien a juger, une chaine est la ou elle n'y est pas. Elles vivaient pourtant dans une
checklist, c'est-a-dire nulle part :

  1. LA PAGE N'AFFICHE PAS LE MARKDOWN, elle imprime les asterisques. Vu par le généalogiste le
     24 aout 2026 sur la fiche de Jean PEYRET : cinq narratifs portaient du `**gras**`.
     L'emphase se met en CAPITALES.
  2. UN NARRATIF RACONTE UNE VIE, PAS UN DEPOUILLEMENT. « le corpus tenait pour », « deux
     siecles plus tard », « on croyait » racontent le travail, pas la personne -- et ca
     perime au premier acte suivant. Le généalogiste, le 27 aout : « c'est de la toutouille interne,
     ca interesse qui ? ». Le 20 septembre 2026, deux phrases de ce genre sont passees dans
     des narratifs neufs et n'ont ete attrapees qu'en relancant la checklist a la main.
  3. LE TEXTE AFFICHE S'ECRIT EN FRANCAIS ACCENTUE. Des scripts de versement ont deja ecrit
     « Meigne », « etait », « generation » -- de l'ASCII pose par prudence d'encodage dans un
     shell -- au milieu d'un corpus accentue partout.

CE QU'IL NE FAIT PAS. Il ne juge rien. `relire.py` montre et laisse trancher ; celui-ci
REFUSE, et il ne refuse que ce qui n'a pas de cas legitime. Les `notes`, les sources et les
`.md` sont hors de son champ : rien ne les affiche, le markdown y est chez lui.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("GENEALOGIA_DATA") or os.path.join(ROOT, "data")

CHAMPS = {"persons.json": ("persons", ["summary"]),
          "events.json": ("events", ["narrative", "narrative_for"])}

# Chaque motif a coute une relecture du généalogiste sur la page publiee.
INTERDITS = [
    (re.compile(r"\*\*|(?<!\w)`(?!\w*\s*»)"), "markdown : la page imprime les caractères"),
    (re.compile(r"\ble corpus\b", re.I), "raconte la recherche, pas la personne"),
    (re.compile(r"\bdeux siècles\b", re.I), "raconte la recherche, pas la personne"),
    # ⛔ « on croyait » A ETE RETIRE LE JOUR MEME DE SON ECRITURE, et c'est la limite de ce
    # fichier. Il attrapait « un chien qu'ON CROYAIT enrage » : ce sont les gens de 1892 qui
    # le croyaient, pas nous. La formule peut dire la recherche OU raconter les faits, et seul
    # un lecteur tranche. Elle reste dans la checklist de `trame-fr`, ou elle est a sa place ;
    # un controle qui BLOQUE ne prend que ce qui n'a aucun cas legitime.
    (re.compile(r"\btenait pour\b", re.I), "raconte la recherche, pas la personne"),
]

# Les mots qu'un corpus francais n'ecrit jamais sans accent.
#
# ⚠️ CHAQUE ENTREE DOIT PORTER UN ACCENT DANS SA FORME CORRECTE, SINON C'EST UN FAUX POSITIF.
# Premiere version de ce fichier, 20 septembre 2026 : « naissance de » y figurait -- un mot
# qui n'a aucun accent a perdre. Trente-trois signalements, tous faux, sur un controle cense
# REFUSER un commit. Un controle qui crie a tort est desarme le jour meme.
# On ne cherche pas non plus « a » ni « ou », legitimes sans accent.
# ⚠️ ET CHAQUE ENTREE DOIT ETRE UN NON-MOT SANS SON ACCENT. Deuxieme faux positif du meme
# jour : « ne le » attrapait la negation (« la guerre NE LE prit pas »), et « cure » attrape
# une cure thermale. Le test avant d'ajouter un mot : la forme sans accent existe-t-elle en
# francais ? Si oui, elle ne peut pas entrer ici.
SANS_ACCENT = re.compile(
    r"\b(etait|etaient|epouse|epousa|epoux|decede|decedee|deces|"
    r"generation|annee|annees|apres|pere|mere|frere|premiere|derniere|"
    r"eglise|meme|tres|deja|voila|nee|ainee|bapteme|deces|veuve de la)\b")


def textes(nom):
    """Rend (identifiant, champ, texte) pour tout champ AFFICHE du fichier."""
    cle, champs = CHAMPS[nom]
    d = json.load(io.open(os.path.join(DATA, nom), encoding="utf-8"))
    for o in d[cle]:
        for c in champs:
            v = o.get(c)
            if isinstance(v, str):
                yield o["id"], c, v
            elif isinstance(v, dict):
                for qui, t in v.items():
                    if isinstance(t, str):
                        yield o["id"], "%s/%s" % (c, qui), t


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    fautes = []
    for nom in CHAMPS:
        for ident, champ, t in textes(nom):
            for motif, raison in INTERDITS:
                m = motif.search(t)
                if m:
                    fautes.append((nom, ident, champ, raison, m.group(0), t[max(0, m.start() - 40):m.end() + 40]))
            m = SANS_ACCENT.search(t)
            if m:
                fautes.append((nom, ident, champ, "français non accentué", m.group(0),
                               t[max(0, m.start() - 40):m.end() + 40]))

    if not fautes:
        print("✅ champs affichés : ni markdown, ni jargon de recherche, ni ASCII.")
        return 0

    print("⛔ %d champ(s) affiché(s) que le lecteur ne doit pas voir ainsi\n" % len(fautes))
    for nom, ident, champ, raison, quoi, ctx in fautes:
        print("  %-14s %-34s %s" % (nom.replace(".json", ""), ident[:34], champ))
        print("       %s — « %s »" % (raison, quoi))
        print("       …%s…" % re.sub(r"\s+", " ", ctx))
    print("\nLes `notes`, les sources et les .md ne sont PAS concernés : rien ne les affiche.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
