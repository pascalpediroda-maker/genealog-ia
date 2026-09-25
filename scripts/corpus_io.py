"""
Lecture et ecriture des cinq JSON de data/ -- LE SEUL CHEMIN AUTORISE POUR ECRIRE.

CE MODULE EXISTE PARCE QUE LE 7 SEPTEMBRE 2026, UNE COMMANDE `python -c` BRICOLEE A VIDE
persons.json. La ligne fautive ouvrait le fichier en mode 'w' au milieu d'une condition
censee empecher l'ecriture -- mais `io.open(chemin, 'w')` tronque le fichier A L'OUVERTURE,
avant qu'aucune ligne suivante ne s'execute. Aucune prudence de redaction ne protege contre
ca : il faut que l'ecriture ne puisse jamais toucher le fichier reel avant d'avoir reussi.

LA REGLE, DESORMAIS : toute ecriture dans data/*.json passe par `sauve()` ci-dessous, jamais
par un `io.open(chemin, 'w')` ecrit a la main. `sauve()` ecrit dans un fichier temporaire
voisin puis le bascule sur l'original par `os.replace` -- une operation atomique du systeme
de fichiers. Si le processus meurt, plante, ou ecrit n'importe quoi avant la fin, LE FICHIER
D'ORIGINE N'EST JAMAIS TOUCHE : le pire cas est un `.tmp` orphelin a supprimer, jamais un
persons.json a zero octet.

`sauve()` refuse aussi de remplacer un gros fichier par un petit sans qu'on le lui demande
explicitement (`shrink=True`) -- un JSON valide mais anormalement court est le symptome d'un
bug de logique, pas d'une ecriture ratee, et l'ecriture atomique seule ne l'attrape pas.

Usage :
    import corpus_io as io_
    P = io_.charge("persons.json")
    ... modifier P ...
    io_.sauve("persons.json", P)

Pour une verification qui ne doit RIEN ecrire : `io_.charge(...)` seul, jamais un `open(...,
'w')` a cote, meme dans une branche qu'on croit inatteignable.
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("GENEALOGIA_DATA") or os.path.join(ROOT, "data")

# L'indentation differe par fichier -- mesuree sur le depot, pas devinee. Une ecriture qui
# change l'indentation produit un diff de plusieurs milliers de lignes pour une phrase.
INDENT = {"persons.json": 1, "events.json": 1, "sources.json": 1, "unions.json": 1,
          "places.json": 2}

# Chaque fichier doit porter cette cle a la racine : un JSON valide qui ne l'a pas n'est
# pas ce fichier, meme s'il s'appelle pareil.
CLE_RACINE = {"persons.json": "persons", "events.json": "events",
              "sources.json": "sources", "unions.json": "unions", "places.json": "places"}


def charge(nom):
    """Lit un JSON de data/. Aucune ouverture en ecriture n'a lieu ici, jamais."""
    with io.open(os.path.join(DATA, nom), encoding="utf-8") as f:
        return json.load(f)


def sauve(nom, contenu, shrink=False):
    """Ecrit `contenu` dans data/<nom>, de facon atomique.

    ECRIT D'ABORD DANS UN FICHIER TEMPORAIRE VOISIN, PUIS BASCULE PAR `os.replace`. C'est la
    seule facon d'empecher qu'une exception, un bug de logique ou un plantage au milieu de
    l'ecriture ne laisse le fichier reel tronque : tant que le `replace` final n'a pas eu
    lieu, l'original est intact.

    `shrink=False` (par defaut) refuse de remplacer un fichier par un contenu de moins de
    80% de sa taille actuelle -- lever `shrink=True` explicitement si on sait qu'on retire
    vraiment beaucoup (une fusion d'evenements en double, par exemple).
    """
    if CLE_RACINE.get(nom) and CLE_RACINE[nom] not in contenu:
        raise ValueError(
            f"{nom} : le contenu a sauver ne porte pas la cle « {CLE_RACINE[nom]} » -- "
            f"ce n'est probablement pas le bon objet, rien n'est ecrit")

    chemin = os.path.join(DATA, nom)
    indent = INDENT.get(nom, 1)
    tmp = chemin + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(contenu, f, ensure_ascii=False, indent=indent)
        f.write("\n")

    if not shrink and os.path.exists(chemin):
        avant = os.path.getsize(chemin)
        apres = os.path.getsize(tmp)
        if avant > 1000 and apres < avant * 0.8:
            os.remove(tmp)
            raise ValueError(
                f"{nom} : le nouveau contenu ({apres} octets) fait moins de 80% de "
                f"l'actuel ({avant} octets). Si c'est voulu, rappeler avec shrink=True. "
                f"Rien n'a ete ecrit -- le .tmp a ete efface.")

    os.replace(tmp, chemin)


# ─────────────────────────────────────────────────────────────────────────────
# L'ATTELAGE CROISE : LES DONNEES D'UN CORPUS DANS LA PAGE D'UN AUTRE
#
# CE DEPOT SERT TROIS FAMILLES, ET IL LES DISTINGUE PAR DES VARIABLES
# D'ENVIRONNEMENT INDEPENDANTES. `build_media.py` et `build_poc.py` resolvaient
# chacune la leur, separement :
#
#     D   = os.environ.get("GENEALOGIA_DATA")  or <depot>/data
#     OUT = os.environ.get("GENEALOGIA_OUT")   or <depot>/poc/index.html
#
# Deux `or` qui ne se parlent pas. Poser le premier sans le second attelle
# SILENCIEUSEMENT les donnees d'un corpus a la page d'un autre, et rien ne
# proteste : le script annonce le bon nombre de personnes, ecrit un fichier
# valide, et rend la main.
#
# LE 18 SEPTEMBRE 2026, C'EST ARRIVE. Un `from build_poc import famille`, lance
# pour tester une fonction avec GENEALOGIA_DATA pointe sur le corpus DUPONT
# mais sans GENEALOGIA_OUT, a reecrit `poc/index.html` -- LA PAGE DU CORPUS
# PAIRE -- avec les 105 personnes de cet ami sous le titre « La trame ». Git
# ignore ce fichier, donc rien n'est entre au depot ; mais une autre session qui
# aurait republie depuis lui aurait pose l'arbre d'un ami sur l'artefact de
# le généalogiste, et c'est exactement l'accident que trois annees de regles sur les URL
# cherchent a empecher.
#
# La lecon a d'abord ete ecrite dans un handoff. Le généalogiste : « plus qu'une lecon,
# il faut que ce soit MECANIQUEMENT INFAISABLE. » Il a raison, et ce module
# existe deja pour cette raison-la : une regle relue a chaque session est une
# regle oubliee a chaque session.
#
# LA REGLE, DONC, ET ELLE VAUT DANS LES DEUX SENS :
#
#   · GENEALOGIA_DATA pose (corpus tiers, sur le NAS) -> les sorties doivent
#     etre posees AUSSI, et vivre dans le dossier du corpus. Une sortie laissee
#     par defaut pointerait dans le depot.
#   · GENEALOGIA_DATA absent (corpus PAIRE du depot) -> les sorties ne doivent
#     PAS pointer hors du depot. C'est le meme accident, dans l'autre sens.
#
# Le cas `GENEALOGIA_OUT=poc/cousine.html` sans DATA reste permis : c'est une page
# derivee du corpus du depot, ecrite dans le depot.
# ─────────────────────────────────────────────────────────────────────────────

def sortie(var, defaut):
    """Resout une variable de sortie, ou refuse d'ecrire quoi que ce soit.

    Leve SystemExit avant tout travail si le corpus lu et le fichier ecrit
    n'appartiennent pas au meme monde. Ne rend jamais un chemin douteux.
    """
    valeur = os.environ.get(var)
    corpus = os.environ.get("GENEALOGIA_DATA")

    def dedans(chemin, dossier):
        c = os.path.realpath(chemin)
        d = os.path.realpath(dossier)
        return c == d or c.startswith(d + os.sep)

    if corpus:
        maison = os.path.dirname(os.path.abspath(corpus))
        if not valeur:
            raise SystemExit(
                f"\n  ATTELAGE CROISE -- RIEN N'A ETE ECRIT.\n"
                f"  GENEALOGIA_DATA est pose sur un corpus tiers :\n"
                f"      {corpus}\n"
                f"  mais {var} ne l'est pas, et vaudrait par defaut :\n"
                f"      {defaut}\n"
                f"  C'est un fichier du depot : on ecrirait les donnees d'une famille\n"
                f"  dans le fichier d'une autre. Poser {var} dans\n"
                f"      {maison}\n"
                f"  -- et les autres sorties avec, elles ont la meme regle.\n")
        if not dedans(valeur, maison):
            raise SystemExit(
                f"\n  ATTELAGE CROISE -- RIEN N'A ETE ECRIT.\n"
                f"  Le corpus lu est dans   {maison}\n"
                f"  mais {var} ecrirait dans {os.path.abspath(valeur)}\n"
                f"  Les deux doivent etre du meme cote.\n")
    elif valeur and not dedans(valeur, ROOT):
        raise SystemExit(
            f"\n  ATTELAGE CROISE -- RIEN N'A ETE ECRIT.\n"
            f"  GENEALOGIA_DATA n'est pas pose : le corpus lu est celui du depot,\n"
            f"      {DATA}\n"
            f"  mais {var} ecrirait hors du depot :\n"
            f"      {os.path.abspath(valeur)}\n"
            f"  On poserait l'arbre du généalogiste dans le dossier d'une autre famille.\n")

    return valeur or defaut


# ─────────────────────────────────────────────────────────────────────────────
# NOMMER L'ARBRE UNE FOIS, ET LES CHEMINS EN DECOULENT
#
# `sortie()` ci-dessus REFUSE l'attelage croise ; ceci le rend INEXPRIMABLE, ce
# qui vaut mieux. Cinq variables d'environnement a poser d'un coup, c'est cinq
# occasions d'en oublier une ; un argument, c'est zero. La table des arbres est
# dans `scripts/corpus.json`, ecrite en toutes lettres.
#
# Les GENEALOGIA_* restent acceptees, et `sortie()` reste en seconde ligne : on
# appelle encore `build_poc.py` seul, et deux autres sessions tournaient quand
# ceci a ete ecrit. Une interface qu'on remplace d'un coup casse le travail en
# cours de ceux qui ne lisent pas le commit.
# ─────────────────────────────────────────────────────────────────────────────

_TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus.json")


def arbres():
    """Les arbres connus, tels que `scripts/corpus.json` les declare."""
    with io.open(_TABLE, encoding="utf-8") as f:
        return json.load(f)["arbres"]


def arbre(nom):
    """Resout un nom d'arbre en chemins absolus, ou refuse avec la liste.

    UN NOM QUI NE DESIGNE RIEN EST REFUSE AVEC LES CANDIDATS -- jamais devine.
    C'est la regle des registres du NAS, appliquee ici : une commande qui ouvre
    le mauvais corpus est pire qu'une commande qui echoue.
    """
    table = arbres()
    if nom not in table:
        raise SystemExit(
            f"\n  « {nom} » n'est pas un arbre connu. Ceux qui le sont :\n"
            + "".join(f"      {k:<10} {v['nom']}\n" for k, v in table.items())
            + f"  La table est dans {_TABLE}\n")

    a = dict(table[nom])
    racine = os.path.abspath(os.path.join(ROOT, a["racine"]))
    chemins = {c: os.path.join(racine, a[c]) for c in ("data", "media", "page", "gedcom")}
    chemins.update(nom=nom, libelle=a["nom"], racine=racine, titre=a.get("titre"))

    # L'adresse de publication voyage avec les donnees, pas avec la table.
    try:
        with io.open(os.path.join(chemins["data"], "persons.json"), encoding="utf-8") as f:
            meta = json.load(f).get("_meta", {})
        chemins["artefact"] = (meta.get("artefact") or {}).get("url")
    except (OSError, ValueError):
        chemins["artefact"] = None
    return chemins


def environnement(a):
    """Les GENEALOGIA_* d'un arbre resolu, pour les passer aux scripts enfants."""
    env = {"GENEALOGIA_DATA": a["data"], "GENEALOGIA_MEDIA": a["media"],
           "GENEALOGIA_OUT": a["page"], "GENEALOGIA_GEDCOM": a["gedcom"]}
    if a.get("titre"):
        env["GENEALOGIA_TITRE"] = a["titre"]
    # Le corpus du depot est le defaut historique : ne rien poser, pour que le
    # comportement sans argument reste EXACTEMENT celui d'avant.
    return {} if a["nom"] == "paire" else env
