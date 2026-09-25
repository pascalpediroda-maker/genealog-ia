#!/bin/sh
# BRANCHE LES HOOKS VERSIONNES DU DEPOT. A lancer une fois par machine :
#
#     sh scripts/hooks/installer.sh
#
# Il pose `core.hooksPath` sur ce dossier-ci. Les hooks vivent donc DANS le depot, sous git,
# relus et corriges comme le reste — au lieu de `.git/hooks/`, que git ne suit pas et qu'un
# clone perd en silence.
#
# ⚠️ `core.hooksPath` REMPLACE TOUT `.git/hooks/` : si un jour ce dossier porte autre chose,
# il faudra le reprendre ici.
set -e
racine=$(git rev-parse --show-toplevel)
cd "$racine"
git config core.hooksPath scripts/hooks
chmod +x scripts/hooks/pre-commit 2>/dev/null || true
echo "core.hooksPath = $(git config core.hooksPath)"
echo "hooks actifs :"
ls scripts/hooks | grep -v '\.sh$' | sed 's/^/  /'
