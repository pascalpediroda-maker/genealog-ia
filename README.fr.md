# genealog-ia

## Onze générations en une après-midi. Pas un ancêtre inventé.

**Donnez-lui un nom et un village. Il ouvre les portails d'archives, retrouve les registres, déchiffre l'écriture, et écrit ce que l'acte dit vraiment dans votre histoire de famille — chaque fait avec sa source, et une page que vos proches lisent sans avoir à déchiffrer un arbre.**

L'après-midi est mesurée : une branche est passée de rien à une souche née en 1632, entre 15 h et 19 h un samedi. C'est la seconde moitié du titre qui est difficile, et c'est à elle que sert l'essentiel du code.

```bash
claude plugin marketplace add pascalpediroda-maker/genealog-ia-plugin
claude plugin install genealog-ia@genealog-ia
```

---

## Vous savez déjà ce qui cloche

Vous demandez à une IA de lire un registre paroissial. Elle impressionne dix minutes.

Puis elle comble un blanc avec le nom qui *va bien*. Elle vous annonce qu'un registre ne contient rien, après un balayage qui ne montre qu'un acte sur trois. Elle conclut d'une demi-lecture — et six mois plus tard vous contournez encore un mur qui n'existait pas.

Un ancêtre fabriqué ne reste pas chez vous. Il se propage dans tous les arbres qui recopient le vôtre.

**Les trois sont arrivés sur l'arbre qui a servi à bâtir ce plugin.** C'est pour ça qu'il existe.

---

## Ce qu'il fait à la place

**Il écrit `[non lu]`** là où il n'a pas su lire le mot, au lieu du nom vraisemblable.

**Il dit comment il a cherché.** « Balayé aux marges » et « lu en pleine page » ne sont pas la même affirmation, et le compte rendu précise laquelle — parce qu'un balayage de marges ne montre jamais un mariage, et que personne ne l'avait écrit avant que ça coûte un mariage.

**Il ne crée personne sur une ressemblance.** Nommé par un acte ou par un témoin → créé. Déduit d'un homonyme ou d'un âge plausible → la question vous revient.

**Et il refuse de publier** quand un contrôle échoue : une date qui contredit la fiche, un moment sans date qui tomberait après le décès, deux passages qui racontent deux fois la même chose.

---

## Ce que vous y gagnez

**Les murs tombent par le côté.** Une aïeule que personne ne trouvait depuis des années : les fichiers de décès n'indexent que les noms de naissance, les recensements inscrivent les épouses sous le nom du mari. Elle était invisible des deux côtés. C'est la ligne de sa belle-mère, deux rangs plus bas dans le même ménage, qui l'a rendue.

**Les photographies se datent seules.** Un tampon de photographe lu au grossissement a placé un portrait de famille en Allemagne occupée. Un bout d'affiche de cinéma derrière deux enfants a resserré un cliché sur un automne, par la circulation du film en salle.

**Une page que la famille ouvre vraiment.** Pas un schéma d'arbre — une vie racontée moment par moment, avec l'image de l'acte sous le texte, et chaque fait portant d'où il vient et à quel point on en est sûr.

**Les démarches, rédigées.** Les demandes d'actes écrites, la bonne mairie nommée, et qui a le droit de demander quoi — ce qui, en France, sépare cinq minutes de jamais.

---

## Jusqu'où ça va

| | |
|---|---|
| **France** | près de la moitié des départements, sur la douzaine de plateformes qui font tourner leurs portails. En ouvrir un de plus est le plus souvent de la configuration, pas du code |
| **Ailleurs** | l'état civil italien, celui d'Algérie, et un catalogue qui va de la Pologne à l'Argentine |
| **Hors registres** | fiches matricules, presse numérisée, fichier des décès, bases de cimetières et de déportation |
| **Les images** | demi-page rendue à la taille lisible, recadrage sur l'encre, zoom sur un mot pâle, planches qui datent un registre sans le lire |

Il répare aussi ce que d'autres logiciels ont cassé : trois arbres sortis d'un programme de Windows XP, où chaque date qu'il ne savait pas lire avait été écrite dans le champ *lieu*. Des milliers de personnes remises d'aplomb, sans qu'un seul fichier d'origine soit touché.

---

## Installation

```bash
claude plugin marketplace add pascalpediroda-maker/genealog-ia-plugin
claude plugin install genealog-ia@genealog-ia
```

Trois questions à l'activation — où ranger les archives, où sont déjà vos photographies, où écrire le corpus. Vous ne retapez plus jamais un chemin.

| | |
|---|---|
| **Claude Code** | et un modèle capable de lire l'image d'un registre manuscrit |
| **Python 3.10+** | installé pour vous par [`uv`](https://docs.astral.sh/uv/) si vous ne l'avez pas |
| **Node** | pour une douzaine de départements dont les portails bloquent les clients qui ne sont pas un navigateur. On vous le dira le jour où ça arrive |

---

## D'où viennent les règles

Une « Clotilde » a vécu plusieurs jours dans le corpus d'origine — fiche, parents, événements — avant qu'on s'aperçoive qu'elle était née d'un prénom inventé par une transcription automatique.

Une paroisse a été déclarée vide sur douze années de registres. Le mariage y était, troisième acte de la page.

Un balayage des marges a manqué une naissance parce qu'un timbre fiscal de 75 centimes couvrait la moitié de la mention.

Chacune est devenue une règle, et plusieurs sont des scripts qui échouent au lieu d'avertir. Une règle nue se relit et s'oublie ; une règle attachée à son accident se retient.

---

MIT. Le catalogue des fonds hors de France reprend celui de [`sliday/genealogy-research`](https://github.com/sliday/genealogy-research), même licence.
