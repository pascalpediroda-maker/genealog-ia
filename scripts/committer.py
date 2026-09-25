# -*- coding: utf-8 -*-
"""COMMITTER SANS EMPORTER LE TRAVAIL D'UNE AUTRE SESSION.

    python scripts/committer.py -m "titre" chemin...
    python scripts/committer.py -F message.txt chemin...
    python scripts/committer.py -F - chemin...          # le message sur l'entree standard

POURQUOI CE FICHIER EXISTE, ET LA REGLE QU'IL REMPLACE NE SUFFISAIT PAS.

Le depot interdit `git add -A` depuis le 16 aout 2026, ou quatre commits d'une session sur
Usson ont emporte le travail d'une autre, en cours sur la branche PEDIRODA. La parade ecrite
etait : « stager les chemins qu'on a soi-meme touches, un par un ».

ELLE NE PROTEGE DE RIEN, ET C'EST CE QU'ON A APPRIS LE 25 SEPTEMBRE 2026. Une session a fait
exactement ce que la regle demande — `git add scripts/config.py scripts/archives/lire/nas.py
scripts/archives/lire/actes.py`, trois chemins, les siens — puis `git commit`. Le commit a
emporte ONZE fichiers : les huit autres etaient deja STAGES par une autre session, et
`git commit` valide L'INDEX ENTIER, pas ce qu'on vient d'ajouter.

`git status --short` le disait, avec un `M` en premiere colonne. Il a ete lu et pas vu.

⛔ LA LECON N'EST PAS « MIEUX LIRE `git status` ». C'est qu'il existe un geste — `git commit`
apres un `git add` — dont le resultat depend de ce qu'un AUTRE processus a fait entre-temps.
Aucune attention ne corrige ca. D'ou ce script, et le garde-fou de `pre-commit` qui refuse un
`git commit` direct : la seule facon de ne pas emporter l'index d'un autre est de ne pas
pouvoir le faire.

CE QU'IL FAIT, DANS CET ORDRE
  1. releve ce qui est deja stage — c'est le travail de l'autre session ;
  2. vide l'index (sans jamais toucher au repertoire de travail) ;
  3. stage UNIQUEMENT les chemins demandes ;
  4. commite ;
  5. REMET dans l'index ce qui y etait — l'autre session retrouve son etat exact.

L'etape 5 n'est pas une politesse : sans elle, la session d'a cote voit son `git add` disparaitre
sans explication, et refera le travail de staging en se demandant ce qui s'est passe.
"""
import io
import os
import subprocess
import sys


def git(*a, **kw):
    tolere = kw.pop("tolere", False)
    r = subprocess.run(("git",) + a, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", **kw)
    if r.returncode and not tolere:
        sys.stderr.write(r.stdout + r.stderr)
        sys.exit(r.returncode)
    return r


def stages():
    return [l for l in git("diff", "--cached", "--name-only").stdout.splitlines() if l]


def main(argv):
    message, fichier, chemins = None, None, []
    i = 0
    while i < len(argv):
        if argv[i] == "-m":
            i += 1
            message = argv[i]
        elif argv[i] == "-F":
            i += 1
            fichier = argv[i]
        else:
            chemins.append(argv[i])
        i += 1

    if not chemins or (message is None and fichier is None):
        sys.stderr.write(__doc__)
        return 2
    if fichier:
        # L'ENTREE STANDARD SE LIT EN OCTETS PUIS SE DECODE EN UTF-8. `sys.stdin.read()`
        # passe par l'encodage de la console — sous Windows il rend des surrogates sur le
        # moindre emoji, et `git commit` refuse ensuite de les ecrire. Vu le 25 sept. 2026
        # sur un message qui portait un « ⚠️ ».
        message = sys.stdin.buffer.read().decode("utf-8", "replace") if fichier == "-" \
            else io.open(fichier, encoding="utf-8").read()

    racine = git("rev-parse", "--show-toplevel").stdout.strip()
    os.chdir(racine)

    avant = set(stages())
    miens = set()
    for c in chemins:
        # On normalise par git lui-meme : un chemin donne en absolu, en Windows ou
        # avec un joker doit se comparer a ce que `diff --cached` rendra.
        r = git("ls-files", "--cached", "--others", "--exclude-standard", "--", c,
                tolere=True)
        miens.update(l for l in r.stdout.splitlines() if l)
    if not miens:
        sys.stderr.write("Aucun fichier suivi ne correspond a : %s\n" % " ".join(chemins))
        return 2

    autres = sorted(avant - miens)
    if autres:
        print("— index d'une autre session mis de cote (%d fichiers), il sera rendu :"
              % len(autres))
        for f in autres:
            print("    %s" % f)

    git("reset", "--quiet")                       # l'index seul ; rien ne bouge sur le disque
    for c in sorted(miens):
        git("add", "--", c)

    prets = stages()
    print("— ce commit porte %d fichier(s) :" % len(prets))
    for f in prets:
        print("    %s" % f)
    if not prets:
        sys.stderr.write("Rien a committer : ces chemins n'ont aucune modification.\n")
        for c in sorted(autres):
            git("add", "--", c)
        return 1

    # ⛔ `try/finally`, ET CE N'EST PAS DE LA PRUDENCE DE PRINCIPE. Le 25 septembre 2026, ce
    # script a leve une UnicodeEncodeError en passant le message a `git commit` : la levee
    # a saute l'etape qui rend son index a l'autre session. Un outil ecrit pour proteger
    # l'index d'autrui ne doit pas le perdre quand il tombe — surtout pas en tombant.
    env = dict(os.environ, GIA_COMMIT="1")        # ce que `pre-commit` exige
    try:
        r = subprocess.run(["git", "commit", "-F", "-"],
                           input=message.encode("utf-8"), env=env)
    finally:
        for c in autres:                          # on rend son index a l'autre session
            git("add", "--", c, tolere=True)

    if r.returncode:
        sys.stderr.write("\nLe commit a echoue — l'index a ete rendu tel qu'il etait.\n")
        return r.returncode
    print(git("log", "--oneline", "-1").stdout.strip())
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
