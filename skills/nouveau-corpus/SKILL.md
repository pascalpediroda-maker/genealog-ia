---
name: nouveau-corpus
description: Ouvrir un corpus familial à partir de ce qu'on a — une feuille manuscrite, un PDF, un GEDCOM, une base Hérédis, ou ce qu'un aîné raconte. Le sien, ou celui d'un proche, d'un ami, d'un adhérent de club. Couvre le rangement des pièces, les cinq fichiers du corpus, le bandeau de la page et sa publication. À charger dès qu'un arbre COMMENCE, avant d'écrire la première ligne. `archives-fr` sert à TROUVER, `trame-fr` à VERSER, celle-ci à OUVRIR.
---

# Ouvrir un corpus pour quelqu'un d'autre

Le dépôt sert **trois familles** et en servira d'autres. Celle du généalogiste vit dans `data/` ;
les autres vivent sur le NAS, chacune dans son dossier, et se construisent avec **le même
code, le même gabarit, les mêmes skills**. Rien n'est à dupliquer — seulement à paramétrer.

| | corpus | données | page |
|---|---|---|---|
| **PAIRÉ / PEDIRODA** | le généalogiste | `data/` | `poc/index.html` |
| **DUPONT** | un ami | `<archives>/\DUPONT - Prenom\data\` | son artefact |
| **MARTIN** | une amie | `<archives>/\MARTIN - Prenom\data\` | son artefact |

**Cette skill existe parce que le savoir-faire n'était nulle part.** Ouvrir le corpus
de cette amie le 17 septembre 2026 a demandé de retrouver, un par un : où les DUPONT rangent
leurs JSON (le généalogiste a dû le dire), quelles variables d'environnement existent (lues dans les
commentaires de `build_poc.py`), quelle forme a `_meta.entete` (lue dans le corpus DUPONT),
et **l'URL de l'artefact, qui n'était écrite nulle part** — il a fallu la demander.

---

## 1. Où ça se range, et ça ne se discute pas

```
<archives>/\<NOM> - <Prénom>\
    data\               les cinq JSON — persons, unions, events, places, sources
    media.json          généré, ou `{"portraits":{},"evenements":{}}` s'il n'y a pas de photo
    index.html          généré
    demandes-actes.md   ce qu'il faut demander, et à qui
    <les pièces>        actes, photos, PDF fournis par la famille
```

Le dossier porte **le nom de famille en capitales, un tiret, le prénom de la personne pour
qui on travaille** — `DUPONT - Prenom`, `MARTIN - Prenom`. Sans accents ni cédilles :
c'est un chemin Windows lu par des scripts.

**RIEN NE VA DANS `data/`.** C'est le corpus du généalogiste. Une personne d'une autre famille qui
y entre y reste, et pollue son arbre, son GEDCOM et sa page.

**RIEN NE VA DANS LE DÉPÔT NON PLUS** — ni les JSON, ni les images. Le `.gitignore` refuse
déjà les binaires d'images ; les JSON d'un tiers, eux, passeraient. C'est au versement de ne
pas les y mettre.

---

## 2. Inscrire l'arbre dans la table, et le nommer en argument

**DEPUIS LE 18 SEPTEMBRE 2026, UN ARBRE SE NOMME, IL NE SE DÉCRIT PLUS EN CINQ VARIABLES.**
Ajouter une entrée dans **`scripts/corpus.json`** — les chemins y sont écrits en toutes
lettres, pas déduits d'une convention :

```json
"dupont": {
 "nom": "DUPONT & MARTIN — la famille de <Prénom>",
 "racine": "<archives>/<NOM> - <Prénom>",
 "data": "data", "media": "media.json", "page": "index.html", "gedcom": "dupont.ged",
 "titre": "<Nom> & <Nom>"
}
```

```bash
python scripts/build_all.py dupont            # valide, médias, page
python scripts/build_all.py dupont --gedcom   # + export GEDCOM
```

Un nom inconnu est refusé avec la liste des candidats. Et la dernière ligne du build affiche
**l'adresse de l'artefact du corpus**, lue dans `_meta.artefact` de son `persons.json` : la
poser dès la première publication, sinon elle n'est nulle part et elle se perd — c'est arrivé
trois fois au corpus du généalogiste, deux artefacts abandonnés.

**POURQUOI CE CHANGEMENT.** Cinq variables à poser d'un coup, c'est cinq occasions d'en
oublier une, et rien ne vérifiait qu'elles parlaient du même arbre. Le 18 septembre 2026, un
`import build_poc` lancé avec `GENEALOGIA_DATA` seul a réécrit `poc/index.html`, la page du
corpus du généalogiste, avec les 105 personnes d'un corpus tiers. `corpus_io.sortie()` **refuse**
désormais cet attelage croisé ; l'argument, lui, le rend **inexprimable**. Le généalogiste : *« plus
qu'une leçon, il faut que ce soit mécaniquement infaisable. »*

*Les variables ci-dessous restent acceptées pour qui appelle les scripts un par un, et la
garde veille alors.*

```bash
export GENEALOGIA_DATA="<archives>/<NOM> - <Prénom>/data"
export GENEALOGIA_MEDIA="<archives>/<NOM> - <Prénom>/media.json"
export GENEALOGIA_OUT="<archives>/<NOM> - <Prénom>/index.html"
export GENEALOGIA_GEDCOM="<archives>/<NOM> - <Prénom>/<nom>.ged"
export GENEALOGIA_TITRE="<Nom> &amp; <Nom>"     # l'onglet du navigateur
```

`GENEALOGIA_QUI` et `GENEALOGIA_DEPUIS` ne servent qu'à **tirer une page par destinataire**
dans un même corpus (voir `build_poc.py`) — pas à ouvrir un corpus neuf.

⚠️ **`GENEALOGIA_MEDIA` N'EST PAS FACULTATIF, MALGRÉ CE QUE DIT LE COMMENTAIRE.** Sans elle,
`build_poc.py` retombe sur `poc/media.json` — **quatorze mégaoctets de photos de la famille
du généalogiste**. Les identifiants ne concordant pas, aucune ne s'affiche ; mais on charge et on
parcourt le mauvais fichier, et un identifiant qui coïnciderait un jour collerait le visage
d'un PAIRÉ sur la fiche d'un inconnu. **Un corpus sans photo pose un `media.json` vide.**

**QUATRE SCRIPTS SUR SEPT HONORENT `GENEALOGIA_DATA` ; LES TROIS AUTRES L'IGNORAIENT.**
`build.py`, `build_media.py`, `build_poc.py` et `corpus_io.py` la lisent depuis le
4 septembre 2026. `relire.py` et `lieux_wikipedia.py` ont été alignés le 17 septembre —
avant, lancés sur un second corpus, **ils rendaient le résultat du premier sans que rien ne
le signale** : `relire.py` a sorti 341 signalements sur la famille PEYRET pendant qu'on
versait les MARTIN, et ils étaient parfaitement plausibles. `lieux_coords.py` ne l'a
toujours pas ; il ne sert qu'aux lieux-dits.

> **Le contrôle qui ne coûte rien** : le premier résultat d'un script doit nommer quelqu'un
> du corpus qu'on vient d'ouvrir. S'il nomme un PEYRET, la variable n'est pas passée.

---

## 3. Le bandeau, ou la page ment sur qui elle raconte

`poc/template.html` écrit en dur le bandeau et le pied de page de la famille PAIRÉ. Un second
corpus **doit** fournir le sien dans `_meta.entete` de `persons.json`, sinon la page d'un
inconnu s'ouvre sur « Pairé · Le Pipe · Bariteau · Pediroda » **au-dessus de chiffres qui,
eux, sont les bons** — c'est arrivé aux DUPONT le 4 septembre 2026, et rien ne le signalait.

```json
"_meta": {
  "corpus": "MARTIN — famille d'une amie",
  "note": "Corpus distinct de celui de la famille PAIRÉ / PEDIRODA. Établi le …",
  "avertissement": "…ce qui reste à vérifier sur acte…",
  "de_cujus": "martin-prenom",
  "artefact": { "url": "https://claude.ai/artifact/…", "note": "Republier TOUJOURS ici." },
  "entete": {
    "familles":    "Arrouard · Vithmann · Groffe · Delanoye · Chacandré",
    "titre":       "Quatre générations,<br>de la Haute-Marne<br>aux <em>deux Quevilly</em>",
    "chapeau":     "De Saint-Dizier … Voici ce que la famille a gardé en mémoire …",
    "plus_ancien": "1912",
    "personne":    "martin-pierrette",
    "racine":      "martin-prenom",
    "provenance":  "Établi pour <b>une amie</b> en septembre 2026, à partir de …"
  }
}
```

- `personne` — **la fiche qui s'ouvre**. On y met ce que la personne est venue chercher, pas
  la plus fournie : cette amie veut sa grand-mère Pierrette, la page s'ouvre sur Pierrette.
- `racine` — **depuis qui les parentés se disent** (« son grand-oncle »). C'est le
  destinataire.
- `plus_ancien` — l'année de la personne la plus ancienne *datée*, pas la plus ancienne.
- `titre` et `chapeau` acceptent `<br>`, `<em>` et `<b>`. **Ils doivent être vrais.** Un
  titre qui promet un département qu'aucune source n'établit est un mensonge affiché en
  quarante-huit points.

`build_poc.py` **lève une assertion** si un de ces motifs ne se retrouve pas dans le gabarit :
si le template change, c'est ici que ça casse, et c'est voulu.

---

## 4. La marche à suivre, dans l'ordre

### ① Lire ce qu'on apporte, vraiment

Une feuille manuscrite se lit **au grossissement natif**, pas sur la vignette du message.
Un PDF n'est souvent qu'une photo : `PyMuPDF` en sort l'image d'origine, qui fait trois fois
la taille du rendu.

```python
import fitz
d = fitz.open(chemin); p = d[0]
pix = fitz.Pixmap(d, p.get_images(full=True)[0][0]); pix.save("natif.png")
```

Puis : redresser si le scan est tourné, découper en zones qui se recouvrent, et lire chacune
à 1400 px de large minimum. **Une main se déchiffre par comparaison avec elle-même** — c'est
en comparant le mot litigieux au « Rouen » qu'cette amie écrit quatre fois qu'on a écarté
Rosny-sous-Bois, et en comparant « 1572 » à « 1984 » qu'on a su que son 9 se ferme comme
un 5.

**Tout ce qui n'a pas été lu au grossissement s'écrit `[non lu]`**, et les lectures douteuses
vont en `note` de la source. On ne comble pas un blanc avec ce qui est plausible.

### ② Poser la question à qui peut répondre

Le témoin est **vivant et joignable** — c'est toute la différence avec un acte de 1774. Les
lectures incertaines, les liens ambigus, les prénoms nus : **ça se demande dans la réponse à
Le généalogiste, tout de suite, nommément**. Pas dans une `note`, que personne ne lit ; pas dans un
fichier de questions, qui reporte au lieu de demander.

Le versement des MARTIN a été corrigé quatre fois en cours de route parce que les questions
étaient posées à voix haute : « Christian Jacques » était deux frères, un « fils » était un mari et non un fils, le nom s'écrivait VITHMANN, la commune était Reugny.

### ③ Passer l'INSEE AVANT d'écrire

**C'est le meilleur rapport travail / résultat de toute la chaîne, et il est gratuit.** Le
fichier des décès (voir `archives-fr`, fiche INSEE) est saisi sur l'état civil, pas océrisé :
il donne la date et le **lieu de naissance exacts** de toute personne morte en France depuis
1970, et **il tranche les graphies**. Sur les MARTIN, en une demi-heure : Thierry né à
Mont-Saint-Aignan et non à Rouen, Michel mort en 1999 et non en 2000, André daté au jour, et
surtout **VITHMANN avec un H**, sans quoi aucune recherche ne rendait rien sur cette branche.

Écrire d'abord et vérifier ensuite, c'est écrire deux fois — et laisser des erreurs dans des
résumés qu'on oubliera de relire.

⚠️ **ET IL NE TROUVE AUCUNE FEMME MARIÉE SOUS SON NOM D'USAGE** — il n'indexe que les noms de
NAISSANCE. Un corpus moderne en est plein : sur vingt-deux fiches MARTIN, **deux grands-mères
étaient bloquées par ce seul défaut**, et un négatif a été tiré à tort avant qu'on le
comprenne. **La sortie est de chercher une DATE et non un nom**, en balayant les fichiers bruts
de `data.gouv.fr` — c'est ainsi que Simonne COULBEAU a été nommée. La recette complète, les
largeurs de champs et les pièges sont dans `archives-fr`, fiche INSEE, section « on ne cherche
plus un nom, on cherche une date ».

### ④ Verser, en suivant `trame-fr`

Charger `trame-fr`. Tout ce qu'elle dit s'applique : le français accentué, pas de markdown
dans un champ affiché, un résumé qui présente une vie sans réciter la trame, un fait daté qui
devient un moment, un lieu qui porte son département.

**Ce qui est propre à un corpus neuf :**

- **La confiance est basse par défaut.** Un souvenir de famille est `medium`, jamais `high`.
  `high` est réservé à ce qu'une source primaire ou l'INSEE établit. Sur les vingt-deux
  MARTIN : huit dates `high`, dix `medium`.
- **Un lien de parenté que la source n'écrit pas ne s'écrit pas**, même quand tout converge.
  Michel MARTIN est presque certainement le frère de Pierrette — il n'est rattaché à
  personne, et `build.py --orphelins` le signale. **Cet avertissement-là est le bon état**,
  pas une dette.
- **Un nom qu'on n'a pas se dit `[nom inconnu]`**, pas emprunté au conjoint.
- **Les vivants portent `living: true`.** Ils sont nombreux dans un corpus neuf — c'est la
  famille de quelqu'un d'aujourd'hui, pas une lignée du XVIIIᵉ.
- **Écrire par `corpus_io.sauve`**, qui lit `GENEALOGIA_DATA` et écrit de façon atomique.
  Jamais un `io.open(chemin, "w")`.

### ⑤ Contrôler

```bash
python scripts/build.py              # 0 erreur, sinon on ne publie pas
python scripts/build.py --vues --pasnes --postes --sansdate --fourchettes --orphelins
python scripts/relire.py             # redites, jargon, liens manqués
```

Le premier versement des MARTIN a fait passer `relire.py` de 2 signalements à 0 : les
résumés de deux vivants dataient des naissances qu'aucun moment ne portait. **La
bonne réponse n'a pas toujours été de créer le moment** — une naissance d'enfant écrite en
événement redisait ce que la fiche de l'enfant portait déjà. On a gardé le mariage, retiré
les deux naissances, et réécrit les résumés sans les années.

### ⑥ Générer et publier

```bash
python scripts/build_poc.py          # avec les quatre variables
```

Puis publier avec l'outil Artifact. **Un corpus neuf = un artefact neuf**, avec son favicon
🌳, son titre et sa description. Copier la page dans le répertoire de travail d'abord :
l'outil n'accepte pas un chemin sur `X:`.

**PUIS ÉCRIRE L'URL DANS `_meta.artefact` DE `persons.json`, IMMÉDIATEMENT.** C'est le seul
endroit qui survit à la session. Sans elle, la session suivante publie à côté et crée un
doublon — le corpus principal l'a payé trois fois, et deux artefacts abandonnés traînent
encore dans son CLAUDE.md.

### ⑦ Écrire les trois fichiers de travail — **TROIS, ET NON UN**

C'est le livrable qui fait revenir la personne. **Il se découpe en trois, et chacun ne
contient qu'une seule sorte de chose** — c'est la règle d'`open-questions.md` du corpus
principal, appliquée ici. Le premier jet des MARTIN mélangeait les trois dans un seul
fichier ; le généalogiste, le 18 septembre 2026 : *« il n'y a pas que les demandes d'actes mais
d'autres questions, il faut séparer »*.

| fichier | ce qu'il contient, et rien d'autre |
|---|---|
| `demandes-actes.md` | **des actes à demander à une mairie.** Un par section, classés par ce qu'ils rapportent, avec sous chacun un encadré « ce que ça ouvre ». Dire **à quelle mairie**, et **qui a le droit** de le demander |
| `questions-alexandra.md` | **des questions pour la personne** — sa mémoire, ses tiroirs, sa famille. Plus une section « déjà réglées », qu'on vide une fois la page relue |
| `ou-chercher.md` | **des fonds à dépouiller** — séries, tables décennales, départements manquants au référentiel |

**Qui a le droit de demander quoi, et ça change tout le classement :**

- **Un acte de décès est communicable à n'importe qui**, sans justificatif, **et il nomme les
  père et mère du défunt** (art. 79 du Code civil). C'est l'acte le plus rentable d'un dossier
  moderne, et **on n'a besoin de personne pour l'obtenir**.
- **Une copie intégrale de naissance ou de mariage de moins de 75 ans** est réservée à
  l'intéressé, ses ascendants, ses descendants et son conjoint. Elle passe donc par la
  personne pour qui on travaille.

**ET UN FICHIER DE QUESTIONS SE LIT PAR L'INTÉRESSÉE.** N'y écrire aucun jugement, aucune
raison supposée, rien sur les relations de famille. Si elle n'a pas demandé quelque chose à
un proche vivant, **ce n'est pas au fichier de le remarquer** : on propose la voie
documentaire et on se tait. Chez les MARTIN, deux actes de décès donnaient le nom cherché
sans qu'il faille interroger une grand-mère de quatre-vingt-quatorze ans — c'est cela qu'on
écrit, et rien de plus.

**Ce sont des livrables vivants** : une pièce obtenue en sort, une piste nouvelle y entre.
Celui des DUPONT était faux au bout d'un jour.

---

## 5. Ce qu'on ne fait pas

- **On ne touche pas à l'application.** `poc/template.html` et le rendu de `build_poc.py`
  sont le produit du généalogiste. Un besoin d'affichage se signale, il ne s'implémente pas.
- **On ne publie pas les vivants au-delà de ce que la personne a donné.** Elle a apporté sa
  famille ; on n'y ajoute pas ce qu'on trouverait ailleurs sur des gens vivants.
- **On ne mélange jamais deux corpus.** Pas de personne, pas de lieu, pas de source en
  commun — même pour un lieu identique. `rouen` existe deux fois, et c'est très bien.
