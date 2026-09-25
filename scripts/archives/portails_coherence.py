# -*- coding: utf-8 -*-
"""LE CONTROLE QUI EMPECHE LES TROIS FICHIERS DE DIVERGER.

    python scripts/archives/portails_coherence.py            # rapport, sort 1 si divergence
    python scripts/archives/portails_coherence.py --ecrire    # remet la table de README.md

POURQUOI IL EXISTE. Le savoir des portails vit a trois endroits, et rien ne les reliait :

    scripts/archives/portails.json                  LE REGISTRE — le factuel, et il fait foi
    .claude/skills/archives-fr/references/portails.md   LE CARNET — la methode et les pieges
    scripts/archives/README.md                      la table moteur -> departements

Le 18 septembre 2026, les trois disaient trois choses differentes. Le carnet portait
trente-quatre fiches, le registre trente et une, et douze n'etaient dans aucun des deux
sens : AD27 et AD66 reconnus au carnet sans jamais entrer au registre, douze departements
ouverts au registre sans fiche au carnet, et QUATORZE SOURCES — l'INSEE, Gallica, le CEMLA,
Arolsen, la Wayback — que le registre ignorait completement. README.md, lui, annoncait
encore « 7 moteurs, 16 portails » quand il y en avait dix pour trente et un.

Et ce n'etait pas faute d'outil : `moteurs_table.py` avait ete ecrit en septembre POUR
regenerer cette table, et il portait lui-meme deux tables en dur qui avaient derive. C'est
la lecon de fond — une copie non controlee ment tot ou tard, y compris dans l'outil ecrit
contre la derive. D'ou un controle qui ECHOUE, et pas une table de plus.

CE QU'IL VERIFIE
  1. tout moteur cite par une fiche est declare dans `_meta.moteurs` ;
  2. tout moteur declare a sa signature dans `moteurs/identifier.js` — ou un `signature:
     null` ASSUME, avec sa raison. C'est le controle qui a coute le plus cher : GAIA a ete
     reconnu le 12 septembre, sa fiche ecrite, `gaia.py` livre, et sa signature oubliee
     dans identifier.js — une session a refait tout le chemin le 18 ;
  3. tout module annonce est sur le disque, et tout fichier de `moteurs/` est reclame ;
  4. toute section `##` du carnet est reclamee par une fiche via son champ `carnet` ;
  5. tout `carnet` d'une fiche pointe sur une section qui existe ;
  6. la table de README.md est celle que `moteurs_table.py` regenere.
"""
import io
import json
import os
import re
import sys

import moteurs_table

D = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(D))
CONF = os.path.join(D, "portails.json")
IDENT = os.path.join(D, "moteurs", "identifier.js")
README = os.path.join(D, "README.md")
CARNET = os.path.join(RACINE, ".claude", "skills", "archives-fr", "references",
                      "portails.md")

# Les sections du carnet qui ne sont PAS des fiches de fonds. Liste explicite et courte :
# une section de methode qu'on oublierait d'inscrire ici ferait echouer le controle, ce qui
# est le bon sens de l'erreur — on prefere expliquer une section de plus que laisser passer
# une fiche orpheline.
METHODE = [
    "Les moteurs, et pourquoi il y en a moins qu'il n'y paraît",
    "Faire tourner les scripts Playwright — **la dépendance n'est pas dans le dépôt**",
    "OAI-PMH et EAD — la porte à côté du mur, et elle existe **six fois sur soixante-trois**",
]

# Les outils de `moteurs/` qui ne servent aucun moteur en particulier.
TRANSVERSES = ["identifier.js", "lire_page.js"]


def titres_du_carnet():
    if not os.path.exists(CARNET):
        return None
    return [l.rstrip("\n").rstrip()[3:]
            for l in io.open(CARNET, encoding="utf-8") if l.startswith("## ")]


def signatures():
    """Les cles de la table SIGNES d'identifier.js."""
    s = io.open(IDENT, encoding="utf-8").read()
    bloc = s[s.index("const SIGNES"):]
    bloc = bloc[:bloc.index("\n};")]
    return set(re.findall(r"^\s*'([^']+)'\s*:", bloc, re.M))


def controle():
    c = json.load(io.open(CONF, encoding="utf-8"))
    connus = c["_meta"]["moteurs"]
    fiches = c["portails"]
    maux = []

    def mal(titre, details):
        if details:
            maux.append((titre, details))

    # 1. un moteur cite mais pas declare
    mal("MOTEUR CITÉ PAR UNE FICHE ET ABSENT DE `_meta.moteurs`",
        sorted({"%s (fiche %s)" % (p["moteur"], p["id"]) for p in fiches
                if p.get("moteur") and p["moteur"] not in connus}))

    # 2. la signature dans identifier.js
    sig = signatures()
    sans_sig, sans_raison = [], []
    for nom, m in sorted(connus.items()):
        s = m.get("signature")
        if s is None:
            # `signature: null` est legitime — certains moteurs ne se signent nulle part
            # dans le HTML. Mais il faut alors DIRE POURQUOI, sinon « pas de signature » et
            # « signature oubliee » sont le meme JSON, et c'est l'oubli qu'on cherche.
            if not m.get("note_signature"):
                sans_raison.append(nom)
        elif s not in sig:
            sans_sig.append("%s → « %s » introuvable dans identifier.js" % (nom, s))
    mal("MOTEUR SANS SIGNATURE DANS `moteurs/identifier.js` — il sera redécouvert de zéro",
        sans_sig)
    mal("MOTEUR À `signature: null` SANS RAISON ÉCRITE (champ `note_signature`)",
        sans_raison)

    # 3. les modules
    dispo = {f for f in os.listdir(os.path.join(D, "moteurs"))
             if f.endswith((".js", ".py"))}
    annonces, absents = set(), []
    for nom, m in connus.items():
        for f in m.get("modules") or []:
            annonces.add(f)
            if f not in dispo:
                absents.append("%s → `moteurs/%s`" % (nom, f))
    for p in fiches:
        f = p.get("module")
        if not f:
            continue
        chemin = os.path.join(RACINE, f) if f.startswith("scripts/") \
            else os.path.join(D, f)
        if not os.path.exists(chemin):
            absents.append("fiche %s → `%s`" % (p["id"], f))
        elif f.startswith("moteurs/"):
            annonces.add(f[len("moteurs/"):])
    mal("MODULE ANNONCÉ ET ABSENT DU DISQUE", sorted(absents))
    mal("FICHIER DE `moteurs/` QUE PERSONNE NE RÉCLAME",
        sorted(dispo - annonces - set(TRANSVERSES)))

    # 3 bis. LA FICHE EST-ELLE COMPLETE ?
    #
    # ⛔ CE CONTROLE MANQUAIT, ET C'EST UN RECAPITULATIF QUI L'A FAIT VOIR. Le 19 septembre
    # 2026, le généalogiste a demande un tableau « departement, moteur, module » : VINGT-CINQ FICHES
    # portaient `module: null` alors que leur moteur etait connu et son module ecrit —
    # l'AD49 etait PROUVEE « sans navigateur » et sa fiche ne disait pas par quoi entrer.
    #
    # Aucune n'etait en contradiction avec quoi que ce soit : elles etaient parfaitement
    # COHERENTES, et vides. Ce fichier ne posait qu'une question — « les trois fichiers
    # disent-ils la meme chose ? » — et jamais la seconde : « cette fiche est-elle
    # COMPLETE ? » Une table est une projection, et une projection est un audit ; il ne
    # faut pas attendre qu'on la demande pour le faire.
    #
    # ⚠️ ET UN TROU SE DISTINGUE D'UN CHOIX PAR UN CHAMP QUI DIT POURQUOI. `module: null`
    # est legitime — l'AD35 n'a pas de module — a condition de porter `MODULE_ABSENT`.
    OBLIGATOIRES = [("base", None), ("type", None),
                    ("moteur", "MOTEUR_ABSENT"), ("module", "MODULE_ABSENT")]
    creux = []
    for p in sorted(fiches, key=lambda z: z["id"]):
        for champ, excuse in OBLIGATOIRES:
            if p.get(champ):
                continue
            if excuse and p.get(excuse):
                continue      # absence ASSUMEE, et la raison est ecrite
            creux.append("%-22s pas de `%s`%s"
                         % (p["id"], champ,
                            " ni de `%s` qui dise pourquoi" % excuse if excuse else ""))
    mal("FICHE INCOMPLETE — un champ vide sans rien qui dise que c'est un choix", creux)

    # 4 et 5. le carnet, dans les deux sens
    titres = titres_du_carnet()
    if titres is None:
        maux.append(("CARNET INTROUVABLE", [CARNET]))
    else:
        reclames = {t for p in fiches for t in (p.get("carnet") or [])}
        mal("SECTION DU CARNET QUE NUL NE RÉCLAME — fiche de fonds sans entrée au registre, "
            "ou section de méthode à inscrire dans METHODE",
            [t for t in titres if t not in reclames and t not in METHODE])
        mal("`carnet` D'UNE FICHE QUI NE POINTE SUR AUCUNE SECTION",
            sorted({"fiche %s → « %s »" % (p["id"], t) for p in fiches
                    for t in (p.get("carnet") or []) if t not in titres}))
        mal("SECTION INSCRITE DANS METHODE ET ABSENTE DU CARNET",
            [t for t in METHODE if t not in titres])

    # 6. la table de README.md
    attendu = moteurs_table.markdown(c)
    lu = io.open(README, encoding="utf-8").read()
    if attendu not in lu:
        mal("LA TABLE DE README.md N'EST PLUS CELLE QUE `moteurs_table.py` REND",
            ["`python scripts/archives/portails_coherence.py --ecrire` la remet"])
    return c, maux, attendu, lu


def ecrire_readme(attendu, lu):
    """Remplace le bloc de table de README.md par celui qu'on vient de rendre.

    Le bloc va de sa ligne d'en-tete a la fin de la phrase de generation, qui sert de
    borne basse parce qu'elle est la seule chose stable du bas de table.
    """
    debut = lu.index("| Moteur | Module |")
    fin = lu.index("\n", lu.index("`portails.json`.*", debut))
    io.open(README, "w", encoding="utf-8", newline="\n").write(
        lu[:debut] + attendu + lu[fin:])


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    c, maux, attendu, lu = controle()

    if "--ecrire" in sys.argv:
        ecrire_readme(attendu, lu)
        print("README.md : table réécrite.")
        c, maux, attendu, lu = controle()

    n = len(c["portails"])
    ad = [p for p in c["portails"] if p.get("dept")]
    print("registre : %d fiches — %d portails à département, %d sources sans"
          % (n, len(ad), n - len(ad)))
    print("moteurs   : %d déclarés, %d branchés"
          % (len(c["_meta"]["moteurs"]), moteurs_table.table(c)[2]))
    # L'ETAT SE DIT ICI, POUR QU'ON N'AIT PLUS A DEMANDER UN TABLEAU POUR LE VOIR.
    # `python scripts/archives/moteurs_essai.py` reste ce qui le MESURE ; cette ligne ne
    # fait que compter ce que les fiches declarent.
    print("portails  : %d avec module, %d vérifiés sur le portail, %d sans navigateur, "
          "%d avec un bloc `essai`"
          % (sum(1 for p in ad if p.get("module")),
             sum(1 for p in ad if p.get("VERIFIE_LE")),
             sum(1 for p in ad if p.get("http_simple")),
             sum(1 for p in ad if p.get("essai"))))
    print("            ⚠️ « avec module » n'est pas « vérifié » : un module écrit n'est "
          "pas un module essayé.\n")

    if not maux:
        print("✅ registre, carnet et README disent la même chose.")
        sys.exit(0)
    for titre, details in maux:
        print("⛔ %s" % titre)
        for x in details:
            print("     %s" % x)
        print("")
    print("%d divergence(s)." % len(maux))
    sys.exit(1)
