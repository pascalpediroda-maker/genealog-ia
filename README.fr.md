# genealog-ia

Un plugin Claude Code pour la recherche généalogique : il trouve les actes, déchiffre l'écriture, et écrit ce qu'ils disent dans une histoire de famille documentée.

Claude lit déjà un document et en fait un résumé correct. Deux choses qu'il ne fait pas bien seul : **chercher dans les archives** — une centaine de portails départementaux, chacun se défendant à sa façon — et **s'arrêter à ce qu'il a réellement lu**. Laissé à lui-même, il comble un blanc avec le nom vraisemblable, et un ancêtre fabriqué se propage dans tous les arbres qui recopient le vôtre.

Ce plugin ajoute la moitié qui manque : l'outillage de recherche sur **plus de 130 fonds en ligne**, la méthode de lecture, et les règles de fiabilité — chacune écrite après qu'elle a coûté quelque chose sur un arbre réel.

---

## Les skills

| Skill | Ce qu'elle fait | Exemples de demandes |
| --- | --- | --- |
| **archives-fr** | Ouvrir un portail d'archives, retrouver un registre, en tirer les vues, lire un acte au bon grossissement, et consigner ce qu'on a trouvé — comme ce qu'on n'a pas trouvé. | « trouve le mariage de 1858 de mon arrière-grand-père, il était de Haute-Loire », « liste les registres de cette commune », « lis les vues 120 à 128 », « est-elle morte là après 1870 ? » |
| **trame-fr** | Verser un témoignage ou un acte dans le corpus : personnes, unions, moments, sources. Rédiger le narratif, décider ce qui reste privé, relire une fiche avant publication. | « ajoute cet acte au corpus », « écris sa vie à partir de ces trois sources », « est-ce que ça doit rester privé ? », « relis sa fiche avant que je publie » |
| **nouveau-corpus** | Ouvrir un corpus à partir de ce qu'on a — un arbre manuscrit, un PDF, un GEDCOM, une base Hérédis, ou ce qu'un aîné raconte. Le sien, ou celui d'un ami, ou d'un adhérent du club. | « ouvre mon arbre de famille », « voici un arbre manuscrit scanné », « importe ce GEDCOM », « qu'est-ce que je dois demander à ma grand-mère ensuite ? » |

---

## Éprouvé à l'usage

Trois corpus familiaux tournent dessus tous les jours. Le premier a été bâti en **six semaines, sans aucune connaissance préalable en généalogie** : 754 personnes, 482 moments de vie, 350 sources, 258 photographies.

| | |
|---|---|
| **11 générations** | en moins de 4 heures, de rien jusqu'à une souche née en 1632 |
| **≈ 400 vues / heure** | en balayage de registres anciens, même sans table décennale |
| **31 356 377 lignes** | 6,27 Go parcourus en 6 minutes pour retrouver une aïeule dont on n'avait que la date de naissance |
| **3 GEDCOM réparés** | sortis d'un programme de Windows XP qui écrivait dans le champ *lieu* toute date qu'il ne savait pas lire — 5 234 personnes, 1 268 dates et 219 liens de famille remis, sans toucher un fichier d'origine |
| **22 demandes d'actes** | rédigées, adressées, et suivies |

Et trois photographies sans légende : un bout d'affiche de cinéma qui en date une à l'automne 1958, par la circulation du film en salle. Un numéro de prisonnier et un nom de camp au dos d'une autre — Stalag II B, en Poméranie. Un tampon de photographe sur la troisième — *E. Bernauer, Troisdorf* — qui l'a placée en Allemagne occupée et a ouvert une recherche de registre matricule.

**Aucun de ces trois faits n'était connu de la famille.**

---

## Installation

```bash
claude plugin marketplace add pascalpediroda-maker/genealog-ia
claude plugin install genealog-ia@genealog-ia
```

Trois questions à l'activation — où ranger les archives, où sont déjà vos photographies, où écrire le corpus. Vous ne retapez plus jamais un chemin.

| Ce qu'il faut | |
|---|---|
| **Claude Code** | et un modèle capable de lire l'image d'un registre manuscrit |
| **Python 3.10+** | installé pour vous par [`uv`](https://docs.astral.sh/uv/) si vous ne l'avez pas |
| **Node** | pour une douzaine de départements dont les portails bloquent les clients qui ne sont pas un navigateur. On vous le dit le jour où ça arrive |

---

## Jusqu'où ça va

| | |
|---|---|
| **France** | près de la moitié des départements, sur la douzaine de plateformes qui font tourner leurs portails. En ouvrir un de plus est le plus souvent de la configuration, pas du code |
| **Ailleurs** | l'état civil italien, celui d'Algérie, et un catalogue qui va de la Pologne à l'Argentine |
| **Hors registres** | fiches matricules, presse numérisée, fichier des décès, bases de cimetières et de déportation |
| **Les images** | demi-page rendue à la taille lisible, recadrage sur l'encre, zoom sur un mot pâle, planches qui datent un registre sans le lire |

---

## Les règles de fiabilité

Ce ne sont pas des conseils dans un document. Plusieurs sont des scripts qui échouent au lieu d'avertir.

- **`[non lu]` à la place du nom vraisemblable**, partout où un mot n'a pas été lu au grossissement.
- **Un négatif dit par quelle méthode il a été obtenu.** « Balayé aux marges » et « lu en pleine page » ne sont pas la même affirmation — un balayage de marges ne montre jamais un mariage.
- **Personne n'est créé sur une ressemblance.** Nommé par un acte ou par un témoin → créé. Déduit d'un homonyme ou d'un âge plausible → la question vous revient.
- **Chaque valeur porte sa source et sa confiance**, et la lecture écartée est conservée à côté de celle qu'on retient, avec la raison.
- **La publication est refusée** quand un contrôle échoue : une date qui contredit la fiche, un moment sans date qui tomberait après le décès, deux passages qui racontent deux fois la même chose.

Chacune vient d'un accident. Une « Clotilde » a vécu plusieurs jours dans le corpus d'origine — fiche, parents, événements — avant qu'on s'aperçoive qu'elle était née d'un prénom inventé par une transcription automatique.

---

MIT. Le catalogue des fonds hors de France reprend celui de [`sliday/genealogy-research`](https://github.com/sliday/genealogy-research), même licence.
