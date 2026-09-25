# généalogie — chercher dans les archives, et ne rien inventer

Un plugin Claude Code pour **dépouiller les archives d'état civil en ligne** et **verser ce
qu'on y lit** dans un corpus familial.

Il est né d'un arbre réel — 754 personnes, 350 sources, six semaines — et **chacune de ses
règles vient d'une erreur commise et payée**. Une « Clotilde » a vécu plusieurs jours dans ce
corpus avec sa fiche et ses événements : elle était née d'un prénom inventé par une
transcription automatique. C'est contre ça que le reste est écrit.

---

## Ce qu'il sait faire

**Chercher.** Soixante-trois fonds interrogeables : quarante-cinq portails d'archives
départementales sur quinze moteurs différents, les registres italiens, l'état civil d'Algérie,
les fiches matricules, la presse numérisée, le fichier des décès de l'INSEE.

**Lire un registre.** Une demi-page par image à la taille utile, le recadrage sur l'encre, le
zoom sur un mot pâle, les planches qui datent un registre sans le lire. Et les quatre méthodes
de balayage, avec **ce que chacune ne voit pas** — une marge ne montre jamais un mariage.

**Écrire.** Un corpus où chaque fait porte sa source et son degré de certitude, où un moment se
raconte différemment selon qui le lit, et où ce qui est sensible se masque **sans se masquer en
silence**.

**Refuser.** Des contrôles qui échouent : un événement dont la date contredit la fiche, un
participant dont personne n'a vérifié le point de vue, un champ hors schéma qui ne s'afficherait
nulle part, un moment sans date qui tomberait après le décès, deux passages qui racontent deux
fois la même chose.

---

## Ce qu'il ne fait pas

- **Il ne crée personne sur une déduction.** Nommé par un acte ou par un témoin → la personne
  entre. Déduite d'un homonyme, d'un âge plausible, d'une transcription → elle n'entre pas, la
  question se pose.
- **Il ne comble pas un blanc.** Un mot qu'il n'a pas lu au grossissement s'écrit « non lu ».
- **Il ne conclut pas d'un dépouillement partiel.** Un compte rendu dit *par quelle méthode* un
  négatif a été obtenu, parce que « balayé aux marges » et « lu en pleine page » ne sont pas la
  même affirmation.

---

## Installation

```bash
claude plugin marketplace add <dépôt>
claude plugin install genealogie
```

À l'activation, **trois questions** : où ranger les archives téléchargées, où sont vos
photographies de famille, et où écrire le corpus. Vous ne reverrez plus jamais un chemin — et
vous pouvez les changer plus tard dans `/config`.

### Ce qu'il faut avoir

| | |
|---|---|
| **Claude Code** | et un modèle capable de lire une image de registre manuscrit |
| **Python 3.10+** | cinq dépendances légères : Pillow, numpy, certifi, truststore, PyMuPDF |
| **Node** | **seulement pour treize départements** — voir ci-dessous |

**Le plus simple pour Python est [`uv`](https://docs.astral.sh/uv/)**, un binaire unique qui
installe l'interpréteur et les dépendances tout seul :

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"      # Windows
curl -LsSf https://astral.sh/uv/install.sh | sh                  # macOS, Linux
```

### La question de Node, en clair

Treize portails départementaux se défendent — preuve de travail, blocage des clients qui ne
sont pas un navigateur. Les atteindre demande un vrai Chrome piloté, donc **Node et Playwright,
environ 300 Mo**. Les trente-deux autres départements, la lecture d'image, l'INSEE, les
contrôles et l'export GEDCOM n'en ont pas besoin.

**Vous n'installez donc rien de tout ça tant que votre famille n'est pas dans un de ces treize
départements** — et le message vous le dira le jour où ça arrive.

---

## Ce que ça produit

Les données sont **cinq fichiers JSON lisibles**, chez vous. Pas de base, pas de compte, pas de
plateforme.

Et un **export GEDCOM 5.5.1** contrôlé, qui s'ouvre dans Hérédis, Gramps ou Geneanet. Le même
outil a réparé trois arbres sortis d'un logiciel de Windows XP : 5 234 personnes, 1 268 dates
qui dormaient dans le champ « lieu », 219 liens de famille rétablis — **sans jamais modifier
les fichiers d'origine**.

---

## Avant de demander un acte à une mairie

Deux choses que le plugin connaît et qui font gagner des semaines :

- **La délivrance d'un acte d'état civil est gratuite.** Les sites qui la facturent trente-cinq
  euros ne sont pas l'administration, et ils sortent avant la mairie sur un moteur de recherche.
- **Après soixante-quinze ans, c'est l'archive qui s'ouvre, pas le guichet.** Un tiers n'obtient
  jamais de copie intégrale en mairie, même sur un acte de 1904 — mais un descendant direct
  l'obtient en cinq minutes. Avant de monter un dossier, regarder qui, dans la famille, a le
  droit de le demander.

---

## Licence

MIT. Le catalogue mondial des fonds hors de France reprend celui de
[`sliday/genealogy-research`](https://github.com/sliday/genealogy-research), sous la même
licence.
