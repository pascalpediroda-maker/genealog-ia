# genealog-ia

**Un assistant de recherche familiale qui trouve l'acte, écrit ce qu'il dit vraiment, et refuse d'inventer le reste.**

- **Pour qui remonte une famille**, d'un prénom au dos d'une photo jusqu'à un registre paroissial de 1643.
- **Couvre toute la chaîne**, pas seulement la recherche : trouver → lire → consigner avec sa source → demander l'acte manquant → publier une page que la famille lit.
- **64 fonds fichés**, 45 portails départementaux sur 15 moteurs, plus l'Italie, l'Algérie et 70 services sur 12 régions du monde.
- **Bâti sur un corpus réel** de 754 personnes et 350 sources. Chaque règle a coûté quelque chose avant d'être écrite.

---

## Installation

```bash
claude plugin marketplace add pascalpediroda-maker/genealog-ia-plugin
claude plugin install genealog-ia@genealog-ia
```

Trois questions à l'activation — où ranger les archives, où sont vos photographies, où écrire le corpus. Vous ne retapez plus jamais un chemin.

---

## Sommaire

- [Le problème](#le-problème)
- [Ce que ça couvre](#ce-que-ça-couvre)
- [Ce n'est pas qu'un outil de recherche](#ce-nest-pas-quun-outil-de-recherche)
- [Pourquoi les règles sont écrites comme ça](#pourquoi-les-règles-sont-écrites-comme-ça)
- [Ce qu'il faut avoir](#ce-quil-faut-avoir)
- [Avant d'écrire à une mairie](#avant-décrire-à-une-mairie)
- [État](#état)

---

## Le problème

Une IA qui déchiffre une écriture ancienne impressionne dix minutes et nuit pendant des années.

- Elle comble un blanc avec le nom vraisemblable, et l'ancêtre fabriqué se propage dans tous les arbres qui recopient le vôtre.
- Elle déclare un registre vide après un balayage qui ne montre qu'un acte sur trois.
- Elle conclut d'une lecture partielle, et la session suivante hérite d'un mur qui n'existait pas.

Les trois sont arrivés dans le corpus sur lequel ce plugin a été bâti. Le code sert surtout à ce qu'ils ne se reproduisent pas.

---

## Ce que ça couvre

| | |
|---|---|
| **France** | 45 portails d'archives départementales sur 15 moteurs. En ouvrir un de plus est le plus souvent de la configuration, pas du code |
| **Ailleurs** | l'état civil italien, celui d'Algérie, et un catalogue de 70 services sur 12 régions — archives nationales, bases paroissiales, morts des guerres, index de migration |
| **Hors registres** | fiches matricules, presse numérisée, fichier des décès de l'INSEE, bases de cimetières et de déportation |
| **Les images** | demi-page rendue à la taille lisible, recadrage sur l'encre, zoom sur un mot pâle, planches qui datent un registre sans le lire |

---

## Ce n'est pas qu'un outil de recherche

**Il écrit.** Cinq fichiers JSON lisibles — personnes, unions, moments, lieux, sources. Chaque valeur porte sa source et sa confiance. Un même événement se raconte différemment selon la fiche d'où on le lit.

**Il répare.** L'outillage GEDCOM a remis d'aplomb 3 arbres sortis d'un logiciel de Windows XP : 5 234 personnes, 1 268 dates qui dormaient dans le champ « lieu », 219 liens de famille rétablis — sans modifier un seul fichier d'origine.

**Il fait les démarches.** Rédige les demandes d'actes, nomme la bonne mairie, et sait qui a le droit de demander quoi.

**Il refuse de publier.** Des contrôles qui échouent au lieu d'avertir : une date qui contredit la fiche, un participant dont personne n'a vérifié le point de vue, un champ hors schéma qui ne s'afficherait nulle part, deux passages qui racontent deux fois la même chose.

---

## Pourquoi les règles sont écrites comme ça

Une « Clotilde » a vécu plusieurs jours dans le corpus d'origine — fiche, parents, événements — avant qu'on s'aperçoive qu'elle était née d'un prénom inventé par une transcription automatique.

Une paroisse a été déclarée vide sur douze années de registres ; le mariage y était, troisième acte de la page. Le balayage employé ne montre jamais que le premier acte de chaque page, et personne ne l'avait écrit.

Un balayage des marges a manqué une naissance parce qu'un timbre fiscal de 75 centimes couvrait la moitié de la mention.

Chacune est devenue une règle, et plusieurs sont des scripts qui échouent. Une règle nue se relit et s'oublie ; une règle attachée à son accident se retient.

---

## Ce qu'il faut avoir

| | |
|---|---|
| **Claude Code** | et un modèle capable de lire l'image d'un registre manuscrit |
| **Python 3.10+** | Pillow, numpy, certifi, truststore, PyMuPDF |
| **Node** | pour 13 départements français seulement |

Le plus simple pour Python est [`uv`](https://docs.astral.sh/uv/), un binaire unique qui installe l'interpréteur et les dépendances tout seul :

```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"       # Windows
curl -LsSf https://astral.sh/uv/install.sh | sh                  # macOS, Linux
```

**À propos de Node.** 13 portails départementaux se défendent — preuve de travail, blocage des clients qui ne sont pas un navigateur. Ceux-là demandent un Chrome piloté : Node et Playwright, environ 300 Mo. Les 32 autres départements, la lecture d'image, l'INSEE, les contrôles et l'export GEDCOM s'en passent, et le message vous le dit le jour où ça arrive.

---

## Avant d'écrire à une mairie

- **Un acte d'état civil est gratuit.** Les sites qui le facturent 35 € ne sont pas l'administration, et ils sortent avant la mairie sur un moteur de recherche.
- **Après 75 ans, c'est l'archive qui s'ouvre, pas le guichet.** Un tiers n'obtient jamais de copie intégrale en mairie, même sur un acte de 1904 — un descendant direct l'obtient en cinq minutes.

---

## État

Version 0.1.0, en usage quotidien sur trois corpus familiaux. Les skills sont en français ; le README principal et le manifeste sont en anglais.

MIT. Le catalogue des fonds hors de France reprend celui de [`sliday/genealogy-research`](https://github.com/sliday/genealogy-research), même licence.
