# -*- coding: utf-8 -*-
"""LA SEULE PLACE QUI SAIT OU SONT LES CHOSES.

    from config import archives, photos, data, decoupes, police

POURQUOI CE FICHIER EXISTE. Les chemins du généalogiste sont ecrits en dur dans une
quinzaine de scripts : `<archives>/` dans `actes.py`, `decouper.py`,
`build_media.py`, quatre moteurs ; `<photos>/` dans `media_repointer.py` ; et
`C:\\Windows\\Fonts\\arialbd.ttf` dans les deux outils qui dessinent une planche.
Tant qu'ils y sont, RIEN NE TOURNE AILLEURS QUE SUR CETTE MACHINE — ni chez un
ami, ni dans un plugin distribue, ni sur un autre systeme.

Ce module ne change aucun comportement chez le généalogiste : les valeurs par defaut sont
exactement celles qui etaient en dur, et les variables d'environnement deja en
service sont honorees les premieres.

L'ORDRE DE RESOLUTION, ET IL EST VOULU DANS CET ORDRE

    1. la variable d'environnement historique   NAS_ROOT, GENEALOGIA_DATA, ...
       -> c'est ce qui marche aujourd'hui, et c'est ce qui marchera hors de Claude :
          une ligne de commande, un cron, Cursor, un script d'un tiers.
    2. le fichier du plugin Claude Code          ${CLAUDE_PLUGIN_DATA}/config.json
       -> ecrit par le hook SessionStart a partir des reponses que l'utilisateur
          a donnees dans la boite de dialogue `userConfig`. Il ne voit jamais un
          chemin passer.
    3. `genealogia.toml` dans le dossier courant, puis en remontant
       -> le cas d'un depot de travail qui porte sa propre configuration.
    4. le defaut historique du généalogiste
       -> pour que rien ne casse ici tant que tout n'est pas cable.

Une valeur trouvee plus haut gagne. Le defaut est le dernier recours, JAMAIS
le premier : c'est ce qui permettra, le jour ou tout sera cable, de le remplacer
par une erreur explicite au lieu d'un chemin qui n'existe pas chez l'autre.
"""
import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.dirname(_ICI)

# Les defauts d'aujourd'hui, repris tels quels des scripts ou ils etaient en dur.
_DEFAUTS = {
    "archives": r"<archives>/",
    "photos": r"<photos>/",
    "data": os.path.join(DEPOT, "data"),
}

# ⛔ CE QUI SE DERIVE NE SE FIGE PAS, ET CA A FAILLI PARTIR AVEC LE PLUGIN. `decoupes` et
# `planches` etaient dans la table ci-dessus, avec le X: du généalogiste en dur. Chez quelqu'un
# d'autre, qui aurait pourtant repondu au dialogue d'installation, les demi-pages
# decoupees seraient allees se ranger sur un lecteur qui n'existe pas — ou, pire, sur le
# sien s'il porte la meme lettre. Vu le 25 septembre 2026 en essayant le pont pour de vrai.
_DERIVES = {
    "decoupes": ("archives", "actes-decoupes"),
    "planches": ("archives", "_planches"),
}

# Le nom historique de chaque cle, pour ne casser aucun usage en cours.
_VARIABLES = {
    "archives": ("NAS_ROOT", "GENEALOGIA_ARCHIVES"),
    "photos": ("GENEALOGIA_PHOTOS",),
    "data": ("GENEALOGIA_DATA",),
    "decoupes": ("NAS_DECOUPES",),
    "planches": ("NAS_PLANCHES",),
}

_cache = {}


def _du_plugin():
    """Les reponses de la boite de dialogue du plugin, si on tourne dedans."""
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not base:
        return {}
    p = os.path.join(base, "config.json")
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except Exception:
        # Un fichier absent est le cas nominal hors plugin ; un fichier illisible
        # ne doit pas empecher les autres sources de repondre.
        return {}


def _du_toml():
    """`genealogia.toml` dans le dossier courant, puis en remontant."""
    try:
        import tomllib
    except ImportError:
        return {}
    d = os.path.abspath(os.getcwd())
    while True:
        p = os.path.join(d, "genealogia.toml")
        if os.path.exists(p):
            try:
                with io.open(p, "rb") as f:
                    return tomllib.load(f).get("chemins", {})
            except Exception:
                return {}
        parent = os.path.dirname(d)
        if parent == d:
            return {}
        d = parent


def chemin(cle):
    """Rend le chemin configure pour `cle`, en suivant l'ordre de resolution."""
    if cle in _cache:
        return _cache[cle]
    for var in _VARIABLES.get(cle, ()):
        v = os.environ.get(var)
        if v:
            return _cache.setdefault(cle, v)
    v = _du_plugin().get(cle) or _du_toml().get(cle)
    if v:
        return _cache.setdefault(cle, v)
    if cle in _DERIVES:
        parent, sous = _DERIVES[cle]
        return _cache.setdefault(cle, os.path.join(chemin(parent), sous))
    return _cache.setdefault(cle, _DEFAUTS[cle])


def archives():
    """Ou vivent les actes, matricules et documents telecharges. Le `X:` du généalogiste."""
    return chemin("archives")


def photos():
    """La photothegue familiale. Le `S:` du généalogiste — le corpus la cite, il ne la range pas."""
    return chemin("photos")


def data():
    """Le dossier des cinq JSON du corpus."""
    return chemin("data")


def decoupes():
    """Ou se posent les demi-pages decoupees."""
    return chemin("decoupes")


def planches():
    """Ou se posent les planches de balayage."""
    return chemin("planches")


# --------------------------------------------------------------- la police
#
# ⚠️ `C:\\Windows\\Fonts\\arialbd.ttf` etait ecrit en dur dans `nas.py` et
# `actes.py`. Sur un autre systeme, PIL leve `OSError` au moment de dessiner
# l'etiquette d'une planche — donc TRES loin du vrai probleme, et apres avoir
# deja telecharge les vues. On cherche la premiere police grasse qui existe.
_POLICES = [
    r"C:\Windows\Fonts\arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def police():
    """Le chemin d'une police grasse, ou None — a passer tel quel a PIL.

    `None` est une reponse valide : `ImageFont.load_default()` dessine encore,
    en moins beau. Une planche moche vaut mieux qu'un balayage qui s'arrete.
    """
    v = os.environ.get("GENEALOGIA_POLICE")
    if v and os.path.exists(v):
        return v
    for p in _POLICES:
        if os.path.exists(p):
            return p
    return None


def police_pil(taille):
    """La police prete a dessiner, quoi qu'il arrive.

    `ImageFont.truetype(None, 24)` leve : les appelants ne doivent donc PAS
    recevoir le chemin brut, sinon chacun doit se garder lui-meme et l'un
    d'eux oubliera.
    """
    from PIL import ImageFont
    p = police()
    if p:
        try:
            return ImageFont.truetype(p, taille)
        except OSError:
            pass
    return ImageFont.load_default()


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("dépôt      %s" % DEPOT)
    for c in ("archives", "photos", "data", "decoupes", "planches"):
        v = chemin(c)
        print("%-10s %-52s %s" % (c, v, "✅" if os.path.isdir(v) else "⛔ introuvable"))
    p = police()
    print("%-10s %s" % ("police", p or "aucune — PIL dessinera par défaut"))
