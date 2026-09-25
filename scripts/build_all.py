"""
Enchaine toute la chaine : validation, medias, page.

  python scripts/build_all.py                    l'arbre du généalogiste, par defaut
  python scripts/build_all.py esperet            l'arbre d'une autre famille
  python scripts/build_all.py esperet --gedcom   + export GEDCOM
  python scripts/build_all.py --rapide           saute les medias (long) quand
                                                 seules les donnees ont change

L'ARBRE SE NOMME UNE FOIS, ET LES CINQ CHEMINS EN DECOULENT. Avant le 18 septembre
2026 il fallait poser cinq GENEALOGIA_* d'un coup, sans que rien ne verifie qu'elles
parlent du meme arbre : en oublier une attelait les donnees d'une famille au fichier
d'une autre, en silence. Une garde a ete posee ce jour-la (corpus_io.sortie), puis
Le généalogiste a demande mieux -- « plus qu'une lecon, il faut que ce soit mecaniquement
infaisable ». Un argument rend la faute inexprimable la ou une garde la rend
detectable. La table des arbres est dans `scripts/corpus.json`.

Les GENEALOGIA_* restent acceptees pour qui appelle les scripts un par un.

S'arrete a la PREMIERE etape qui echoue : une page construite sur des donnees
fausses est pire qu'une page pas construite.

ET CA VAUT AUSSI POUR LES DEUX ETAPES D'APRES, ce qui n'etait pas le cas jusqu'au
25 aout 2026 : seule la validation etait verifiee, et les codes de retour de
`build_media.py` et de `build_poc.py` etaient jetes. Ce soir-la, `build_poc.py` a
plante sur un champ `occupations` mal forme -- une liste de chaines au lieu d'une
liste de claims -- et ce script a quand meme affiche « Fait. Republier
poc/index.html ». La page publiee etait celle du build precedent, sans les huit
personnes qui venaient d'entrer au corpus, et rien ne le disait. UNE ETAPE QUI
ECHOUE EN SILENCE EST PIRE QU'UNE ETAPE QUI MANQUE : elle laisse en place un
fichier d'apparence normale, et la derniere ligne invite a le publier.
"""
import subprocess, sys, os

# La console Windows est en cp1252 par defaut : sans ca, une fleche ou un accent
# fait planter le script avant meme qu'il ait rien fait.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import corpus_io as _c

# Le premier argument qui n'est pas un drapeau nomme l'arbre. Sans lui, celui du
# depot -- le comportement d'avant, a l'octet pres.
_noms = [a for a in sys.argv[1:] if not a.startswith("-")]
if len(_noms) > 1:
    sys.exit(f"\n  Un seul arbre a la fois. Recu : {', '.join(_noms)}\n")
ARBRE = _c.arbre(_noms[0] if _noms else "paire")
ENV = {**os.environ, **_c.environnement(ARBRE), "PYTHONIOENCODING": "utf-8"}

print(f"\n\033[1m{ARBRE['libelle']}\033[0m")
print(f"   donnees  {ARBRE['data']}")
print(f"   page     {ARBRE['page']}")


def etape(titre, script, args=()):
    print(f"\n\033[1m>> {titre}\033[0m")
    r = subprocess.run([PY, os.path.join(ROOT, "scripts", script), *args],
                       cwd=ROOT, env=ENV)
    return r.returncode


if etape("validation du corpus", "build.py",
         ["--gedcom"] if "--gedcom" in sys.argv else []):
    sys.exit("\nLa validation a échoué : rien n'a été régénéré. Corrige les erreurs d'abord.")

if "--rapide" not in sys.argv:
    if etape("portraits et photos", "build_media.py"):
        sys.exit("\nLes médias n'ont pas été régénérés : `poc/media.json` est resté celui du "
                 "build précédent.\nNE PAS PUBLIER — corrige l'erreur ci-dessus, puis relance.")

if etape("page de démonstration", "build_poc.py"):
    sys.exit("\nLa page n'a pas été régénérée : `poc/index.html` est resté celui du build "
             "précédent.\nIL A L'AIR NORMAL ET IL EST PÉRIMÉ — ne le publie pas. Corrige "
             "l'erreur ci-dessus, puis relance.")

# L'ADRESSE DE PUBLICATION SE DIT ICI, ET ELLE VIENT DES DONNEES. Elle etait en prose
# dans CLAUDE.md, et elle s'est perdue trois fois -- deux artefacts abandonnes, et un
# soir de lecture d'une page vieille de plusieurs heures pendant qu'une autre etait a
# jour ailleurs. Republier SANS `url` cree un doublon : c'est l'attelage croise, version
# publication, et le seul qui ait vraiment coute.
print("\n\033[1mFait.\033[0m Republier avec l'outil Artifact :")
print(f"   fichier   {ARBRE['page']}")
if ARBRE["artefact"]:
    print(f"   url       {ARBRE['artefact']}")
    print("   \033[1mPasser cette url en parametre `url`\033[0m — sans elle, on cree un doublon.")
else:
    print(f"   url       — ABSENTE de _meta.artefact dans {ARBRE['data']}\\persons.json.")
    print("   La demander a le généalogiste et l'y ecrire : une adresse qui n'est nulle part se perd.")
