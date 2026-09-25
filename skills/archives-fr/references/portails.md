# Fiches des portails déjà ouverts

Une fiche par portail : le moteur, les URL, les identifiants, et les pièges payés. La
**méthode**, elle, ne dépend d'aucun département et vit dans [`../SKILL.md`](../SKILL.md).

**Le code vit par moteur, pas par département.** La configuration lisible par les scripts
est dans `scripts/archives/portails.json` du dépôt `genealog.ia` ; ce fichier-ci porte le
récit, celui qu'on lit avant d'ouvrir un portail.

| Dept | Portail | Moteur | Navigateur ? | Ouvert le |
|---|---|---|---|---|
| **42** Loire | archives.loire.fr | Boscop | oui, WAF | 15 août 2026 |
| **43** Haute-Loire | archives43.fr | Arkothèque | oui, WAF | 17 août 2026 |
| **37** Indre-et-Loire | archives.touraine.fr | Naoned | **non** | 18 août 2026 |
| **45** Loiret | consultation.archives-loiret.fr | Arkothèque | oui, WAF | 25 août 2026 |
| **67** Bas-Rhin | archives67.alsace.eu | Boscop | oui, Anubis | 26 août 2026 |
| **49** Maine-et-Loire | recherche-archives.maine-et-loire.fr | Arkothèque | **non** | 27 août 2026 |
| **17** Charente-Maritime | archinoe.com/v2/ad17/ | **Archinoë** | **non** | 29 août 2026 |
| **16** Charente | lasource.archives.lacharente.fr | **Boscop / Ligeo**, index nominatif propre | oui, Anubis | 7 septembre 2026 |
| **27** Eure | archives.eure.fr | **Mnesys** — reconnaissance seule, module non écrit | **non** | 7 septembre 2026 |
| **06** Alpes-Maritimes | archives06.fr | **Boscop / Ligeo** | oui, TSPD | 7 septembre 2026 |
| **66** Pyrénées-Orientales | archives.cd66.fr | **GAIA 9** — reconnaissance seule, module non écrit | **oui**, formulaire en JS | 12 septembre 2026 |
| **31** Haute-Garonne | archives.haute-garonne.fr | **Boscop / Ligeo** — ⭐ le manifeste IIIF passe Anubis | oui pour les images, **non** pour le manifeste | 18 septembre 2026 |
| 🇫🇷 **FranceArchives** | francearchives.gouv.fr | maison — **redirection JS, pas un WAF** | **non** | 18 septembre 2026 |
| 🇫🇷 **Naturalisations** | siv.archives-nationales.culture.gouv.fr + Gallica | décrets au *Journal officiel*, dossiers en BB/11 | **non** | 18 septembre 2026 |
| 🎖️ **Mémoire des hommes** | **memoiredeshommes.defense.gouv.fr** — ⛔ **plus le `.sga`**, l'ancien domaine est mort | Arkothèque | **non** | 8 septembre 2026 |
| 🇮🇹 **Italie** | antenati.cultura.gov.it | WordPress maison | **non**, mais cadence stricte | 27 août 2026 |
| 🇦🇷 **Argentine** | search.cemla.com | ASP.NET MVC, **captcha** | oui — **et un humain**, le captcha ne se contourne pas | 7 septembre 2026 |

## Les moteurs, et pourquoi il y en a moins qu'il n'y paraît

**LA LISTE DES MOTEURS A PORTÉ CINQ NOMS POUR TROIS PRODUITS JUSQU'AU 27 AOÛT 2026**, et le
doublon coûtait une fausse piste : on croyait avoir deux moteurs à ouvrir là où il n'y en avait
qu'un. **Un portail se signe du nom de son ÉDITEUR ou de son PRODUIT, indifféremment** — c'est
la même maison.

| Éditeur | Produit | Emprise | Ce qu'on cherche dans le HTML |
|---|---|---|---|
| **Boscop** | **Ligeo Archives** | +150 services | `boscop`, `ligeo`, `<meta name="Generator">` |
| **Naoned** | **Mnesys** | +100 services | `naoned`, `mnesys`, `/visualizer/` |
| **1 égal 2** | **Arkothèque** | — | `arko_default_…`, `arko_fiche_…`, `arko-analytics` |
| Anaphore | Thot, Arkhéïa | — | `anaphore` — **aucun portail du dossier n'y tourne encore** |

Trois moteurs couvrent donc les six portails ouverts. **Voir un quatrième nom dans un HTML ne
veut pas dire un quatrième module à écrire.**

---

## AD42 — Loire · moteur **Boscop**

Portail : <https://archives.loire.fr/>

| | |
|---|---|
| **Préfixe ark** | **`ark:/51302/`** — et non `60535`, qui rend la coquille HTML du site |
| **Image** | IIIF : `<ark>/manifest` puis `/iiif/<chemin>/full/full/0/native.jpg` → **3636 × 3000**, ~2 Mo, en double page |
| **WAF** | renvoie **403 à curl et au *headless shell***. Un **vrai Chrome fenêtré** passe : `chromium.launchPersistentContext(profil, {channel:'chrome', headless:false})` |
| **Compte** | aucun |

**Recherche état civil** — formulaire en GET :

```
https://archives.loire.fr/archive/resultats/etatcivil/tabulaire/n:92/page:3
    ?type=etatcivil&RECH_commune=Usson-en-Forez+%28Loire%2C+France%29
```

**TROIS PIÈGES, TOUS PAYÉS :**
- **`RECH_commune` veut le libellé complet** posé par l'autocomplete — `Usson-en-Forez (Loire,
  France)`. Sans lui, 13 160 notices ; avec, 198.
- **LA PAGINATION EST DANS LE CHEMIN** (`/page:N`), pas en query. `&debut=N` est **ignoré** et
  renvoie toujours la première page : c'est ce qui a fait croire pendant une journée que le
  fonds d'Usson comptait 38 unités au lieu de 198, et que l'état civil postérieur à 1792
  n'était pas en ligne. Il l'est en entier, 1793-1942.
- **`RECH_archdesc` est un piège** : `ETATCIVIL` ne rend **rien**, `REGISTRES` ne couvre que
  les BMS d'avant 1793. **Interroger sans filtre.**

**ET UN QUATRIÈME, D'UN AUTRE ORDRE** : le formulaire propose une recherche par nom. C'est de
l'**indexation collaborative**, pas un index de l'état civil. Une commune peut n'y être pas du
tout, et « aucune réponse » n'y prouve rien.

**Outils** : `dl.js <ark> <dossier>` pour un registre, `lot2.js <fichier.tsv>` pour plusieurs
d'affilée, `tout2.js` pour récolter la liste paginée des unités d'une commune. Cadence une vue
par seconde.

---

## Faire tourner les scripts Playwright — **la dépendance n'est pas dans le dépôt**

Les modules de `scripts/archives/moteurs/` sont du **Playwright pour Node** : ils font
`require('playwright')` et pilotent un **Chrome réel et fenêtré**, seule façon de passer les WAF
de l'AD42 comme de l'AD43. Mais **`playwright` n'est installé ni dans ce dépôt ni en global** —
il vit dans les projets GrantForge. On lance donc avec :

```bash
NODE_PATH="<maison>" node scripts/archives/moteurs/arkotheque.js …
```

**Une fenêtre Chrome s'ouvre à l'écran et y reste** : ce n'est pas un bug, c'est la condition pour
que les requêtes passent. Prévenir avant de lancer plusieurs centaines de vues.

*(Ne pas installer `node_modules` ici : le dépôt porte des données, pas une application. Si la
dépendance devait disparaître, `npm i playwright` dans un répertoire quelconque et pointer
`NODE_PATH` dessus suffit — les navigateurs, eux, sont déjà dans `%LOCALAPPDATA%\ms-playwright`.)*

---

## AD43 — Haute-Loire · moteur **Arkothèque**

Portail : <https://www.archives43.fr/> — **le domaine sans `www.` a un certificat invalide.**

| | |
|---|---|
| **Image** | IIIF niveau 2, **1716 × 2500 par vue**, ~530 Ko. **Une page par vue**, pas une double page : la résolution utile équivaut donc à celle de l'AD42 |
| **Compte** | aucun, y compris pour les registres paroissiaux |
| **Page unique** | `/archives-en-ligne/familles-et-individus-en-haute-loire/etat-civil-de-la-haute-loire` — **paroissial et état civil sont dans le même moteur** |

**Recherche** — les paramètres portent des identifiants Arkothèque stables pour ce portail :

| rôle | identifiant |
|---|---|
| instance du formulaire | `arko_default_616fd22b91d20` |
| champ « Commune » | `arko_default_616fd46414cf1` |
| fiche du référentiel des communes | `arko_fiche_6141ac4cbe893` |
| visionneuse | `arko_default_616fd3b20ac86` |

**LE CHAMP COMMUNE SE CONTENTE D'UNE SEULE VALEUR `q[]`, ET ELLE PEUT ÊTRE PARTIELLE.** Le carnet
a exigé deux valeurs — le libellé affiché *et* l'identifiant interne — jusqu'au 17 août 2026 au
soir, où le généalogiste a collé une URL de sa propre session : elle porte `[q][]=Saint-Pal`, sans accent,
sans suffixe `[[fiche]]`, et elle marche. **« Saint-Pal » comme « Saint-Pal-de-Chalençon » sont
acceptés.** Le préfixe de tous les paramètres est l'instance :

```
…?arko_default_616fd22b91d20--filtreGroupes[mode]=simple
 &arko_default_616fd22b91d20--filtreGroupes[groupes][0][arko_default_616fd46414cf1][q][]=Saint-Pal
 &arko_default_616fd22b91d20--filtreGroupes[groupes][0][arko_default_616fd46414cf1][extras][mode]=popup
 &arko_default_616fd22b91d20--from=0&arko_default_616fd22b91d20--resultSize=25
 &arko_default_616fd22b91d20--modeRestit=arko_default_616fd47714b7b
```

**`--modeRestit` ET LE PRÉFIXE D'INSTANCE SUR CHAQUE PARAMÈTRE MANQUAIENT AU MONTAGE DU CARNET**,
et c'est ce qui faisait rendre la page d'accueil au lieu de la liste — **vérifié le 18 août 2026 :
avec eux, la requête sort les onze registres de Saint-Pal d'un coup**, chacun avec son libellé, son
nombre de vues, sa fiche et son numéro de registre. Ajouter aussi `--ficheFocus=` vide et
`--filtreGroupes[mode]=simple`. `resultSize=100` suffit pour une paroisse.

**LA LISTE SE LIT DANS LE HTML RENDU, PAS DANS UNE API** : chaque ligne de résultat porte deux
`arko_fiche_…` — le référentiel de la commune puis **la fiche du registre** — et un `/image/<n>`
qui est le numéro de registre. C'est ce que fait `arkotheque_infos.js 43 --commune "Saint-Pal"`.

**Le filtre « date de fin » ne fonctionne pas correctement** (signalé par le généalogiste) : filtrer sur la
commune seule et trier à l'œil sur la colonne Période. **Le nom de commune peut être partiel** —
« Saint-Pal » rend aussi Saint-Pal-de-Mons, ce qui est un rappel utile qu'il y a trois Saint-Pal
en Haute-Loire.

**La visionneuse est dans le FRAGMENT de l'URL**, après le `#` :

```
#/_recherche-api/visionneuse-infos/<instance>/<fiche du registre>/<visionneuse>/image/<id image>
```

Le même chemin, appelé en JSON, rend le manifeste IIIF de la vue : dimensions, tuiles, ark, et
la `src` de l'image.

**`?size=full` OU ON PERD UN QUART DU CÔTÉ POUR RIEN.** Sans paramètre, l'endpoint plafonne à
**2000 px** sur le grand côté ; `?size=full` rend la taille native, **2500 × 1691 en double
page**, soit ~1250 px par page. `?size=4000,` rend bien 4000 px, mais c'est un **agrandissement
serveur** — `full` étant par définition la taille native, il n'y a aucune information de plus,
juste un fichier deux fois plus lourd. **Et l'AD43 numérise en DOUBLE PAGE** pour les registres
anciens : la résolution utile est donc environ deux tiers de celle de l'AD42, ce qui suffit à
lire un acte mais laisse peu de marge pour trancher un patronyme douteux.

**« IL FAUT ZOOMER À LA MOLETTE POUR AVOIR DE LA QUALITÉ » — ET C'EST UNE ILLUSION D'AFFICHAGE.**
Le généalogiste l'a signalé, et la remarque valait d'être creusée : dans la visionneuse, zoomer révèle
du détail **sans que l'URL change**, et un grand écran en montre plus qu'un portable. Ce n'est
pas qu'un tuilage haute résolution se déclencherait au zoom — **c'est qu'il n'y a rien de plus
à aller chercher.** La visionneuse tient déjà l'image entière et la met à l'échelle localement :
dans une petite fenêtre elle est réduite, donc on voit moins que ce que le fichier contient.
Le tableau `sizes` du manifeste IIIF le confirme — il s'arrête à 1716 × 2500 pour une vue,
2059 × 2500 pour une autre, et **en IIIF la dernière entrée de `sizes` est la taille du
master**. `?size=full` rend exactement cela. **Rien ne se perd à télécharger plutôt qu'à
capturer l'écran.**

**CE QU'UNE SOIRÉE DE SONDAGE A ÉTABLI, LE 17 AOÛT 2026 — ET CE SUR QUOI ELLE A BUTÉ.** Cherchant
à télécharger E-dépôt 2/7 sans relever l'identifiant à la main :

- **L'ÉCART ENTRE NUMÉRISATION ET REGISTRE N'EST PAS UNE CONSTANTE, ET IL NE FAUT PAS S'EN
  SERVIR.** Il vaut +630 sur 27781 → 28411 et 27780 → 28410, ce qui donnait envie d'y voir une
  règle ; il vaut **+633** sur 27771 → 28404. **Le numéro s'obtient par `visionneuse-infos`, comme
  le carnet le disait, et pas autrement** — c'est ce que fait `arkotheque_infos.js`.
- **LE NOMBRE DE VUES SE TROUVE PAR DICHOTOMIE SUR LE RANG**, sans rien connaître du registre : un
  rang hors bornes est refusé, donc on double jusqu'à l'échec puis on resserre. Sept requêtes pour
  un volume de 700 vues.
- **LES IDENTIFIANTS DE REGISTRE NE SONT PAS CONTIGUS PAR COMMUNE, ET C'EST LE PIÈGE.** Le carnet
  disait « deux registres voisins portent des numéros consécutifs » d'après 27781/27782 : c'est
  vrai *à l'intérieur d'un lot de numérisation*, pas d'une commune. **27780 n'est pas E-dépôt 2/7 :
  c'est une paroisse voisine, registre de 1727-1736, 713 vues**, avec les hameaux de La Varenne et
  de Fourchayt. 27777, 27778 et 27779 font 400, 594 et 584 vues — aucun ne fait les 422 annoncées.
  **Les volumes anciens de Saint-Pal ont donc été numérisés dans une autre campagne.**
- **LE FORMULAIRE DE RECHERCHE NE SE PILOTE PAS SIMPLEMENT.** Le montage d'URL décrit plus haut
  rend la page d'accueil du moteur, pas la liste filtrée ; et la page servie ne contient **aucun
  `<input>`** au chargement (0 champ dans 80 Ko de HTML) — le formulaire est injecté après coup ou
  dans un cadre. À reprendre en attendant le sélecteur réel, ou en écoutant les requêtes XHR de la
  page pendant une vraie recherche.
- **LE RACCOURCI QUI COÛTE TRENTE SECONDES** : ouvrir le registre à la main dans la visionneuse et
  relever l'identifiant dans le fragment d'URL, après le `#`. Tant que le formulaire n'est pas
  piloté, c'est la voie la plus courte — et `arkotheque_infos.js 43 <registre>` fait le reste.

**COMMENT ON PASSE D'UN REGISTRE À SES 504 VUES.** L'identifiant qui figure dans l'URL de la
visionneuse (`…/image/27781`) **numérote le REGISTRE, pas la vue** — deux registres du même lot de
numérisation portent des numéros consécutifs, 27781 pour E-dépôt 2/8 et 27782 pour le 2/9. Le
**rang de la vue est le dernier segment** de la `src` rendue par `visionneuse-infos` :

```
/_recherche-images/show/<numérisation>/image/<registre>/<rang>      rang = 0 … n-1
```

Le numéro de numérisation ne se devine pas : il s'obtient en appelant `visionneuse-infos` avec
la fiche du registre. Vérifié sur E-dépôt 2/8 — numérisation 28411, registre 27781, rangs 0 à
503 servis, 504 refusé : le compte tombe exactement sur les 504 vues annoncées.

**LE PIÈGE QUI COÛTE UNE HEURE — UN JETON ANTI-ROBOT.** La première requête sur une URL
d'image ne rend **pas** l'image mais une page HTML de 264 octets contenant
`window.location.href='/redirect_<JETON>/…'`. Il faut **suivre cette redirection une fois** :
le cookie est alors posé et **toutes les requêtes suivantes servent le JPEG directement**.
Sans ça on croit que l'URL est fausse — quatre motifs d'URL ont été essayés en vain avant de
lire le corps de la réponse. **ET LE JETON VAUT AUSSI POUR L'API JSON**, pas seulement pour les
images : `visionneuse-infos` rend la même redirection au premier appel, ce qui fait échouer un
`JSON.parse` sur « Unexpected token '<' » si on ne l'a pas prévu.

```js
let r = await fetch(u); let t = await r.text();
const m = t.match(/window\.location\.href='([^']+)'/);
if (m) r = await fetch(m[1]);          // le cookie est pose, l'image arrive
```

**ET CE CODE NE VAUT QUE DEPUIS L'INTÉRIEUR D'UN VRAI CHROME — L'AD43 A UN WAF, COMME L'AD42.**
Essayé le 17 août 2026 au soir : `curl` obtient bien la page de 322 octets et le jeton, mais
suivre la redirection avec un bocal à cookies rend **`403 Attack detected`**. Le portail ne
distingue donc pas seulement les clients qui exécutent JS : il inspecte la requête elle-même.
`arkotheque.js` marche parce qu'il évalue ce `fetch` **dans le contexte d'une page** ouverte par
`chromium.launchPersistentContext({channel:'chrome', headless:false})`. **Conséquence pratique :
tout appel à cette API — images comme `visionneuse-infos` — passe par le script, jamais par curl
ni par un `WebFetch`.** Et une fenêtre Chrome s'ouvre à l'écran : ce n'est pas discret, et ça se
prévient avant de lancer 422 vues.

**Registres de SAINT-PAL-DE-CHALENÇON — la table complète, sortie du moteur le 18 août 2026.**
`registre` est ce qui va dans l'URL d'image ; `fiche` est ce qu'attend `visionneuse-infos` ;
`numérisation` s'en déduit et **ne se devine pas**.

| période | actes | cote | vues | registre | fiche | numérisation |
|---|---|---|---|---|---|---|
| 1603-1622 | B | E-dépôt 2/3 | 87 | 27767 | `arko_fiche_61657c05d3900` | |
| 1661-1663 | B M | E-dépôt 2/4 | 24 | 27768 | `arko_fiche_61657c05db879` | |
| 1663-1673 | M | E-dépôt 2/5 | 64 | 27769 | `arko_fiche_61657c05e39e6` | |
| **1672-1687** | **BMS** | **E-dépôt 2/6** | **157** | **27770** | `arko_fiche_61657c05eaf03` | **28403** |
| **1687-1737** | **BMS** | **E-dépôt 2/7** | **422** — *en partie dans le désordre* | **27771** | `arko_fiche_61657c05f2193` | **28404** |
| **1737-1771** | **BMS** | **E-dépôt 2/8** | **504** | **27781** | `arko_fiche_61657c0c6200b` | **28411** |
| 1772-1796 | BMS | E-dépôt 2/9 | 415 | 27782 | `arko_fiche_61657c0c6e8cf` | |
| 1793-1796 | BMS | 3 Num 33/2-1 | 112 | 43487 | `arko_fiche_6165802a55840` | |
| 1797-1800 | BMS | 3 Num 33/2-2 | 169 | 43488 | `arko_fiche_6165802a6240d` | |
| 1801-1802 | BMS | 3 Num 33/2-3 | 75 | 43489 | `arko_fiche_6165802a6b24d` | |
| 1802-1806 | BMS | 3 Num 33/2-4 | — | 43490 | `arko_fiche_6165802a73eb5` | |

*Le référentiel des communes, lui, est `arko_fiche_6141ac4cbe893` pour Saint-Pal-de-Chalençon et
`arko_fiche_6141ac4cbf521` pour Saint-Pal-de-Mons — à ne pas confondre avec les fiches de registre.*

**CADRAGE DES TROIS VOLUMES TÉLÉCHARGÉS**, relevé en ouvrant quelques vues — ça évite de balayer
à l'aveugle, et ça se complète au fil des sessions :

| volume | repères datés | rythme |
|---|---|---|
| **2/5** — M 1663-1673 | v32 = **novembre 1669** | ~6,4 vues/an. **UN SEUL MARIAGE PAR DEMI-PAGE**, en colonne étroite : ~128 actes pour tout le volume, et le nom du marié tombe au milieu de l'acte, pas en tête |
| **2/6** — BMS 1672-1687 | v80 = **mai 1680** | ~10,5 vues/an. Marges au hameau. Curés BOUCHET puis PELISSE |
| **2/7** — BMS 1687-1737 | v120 = 1697 · v178 = 1703 · v215 = **sept. 1708** · v234 = fév. 1711 · v241 = fév. 1712 · v320 = 1724 | ~7 vues/an, mais **en partie dans le désordre** — un acte peut être écrit des années après |
| **2/8** — BMS 1737-1771 | v8 = sept. 1737 · v94 = mars 1745 · v117 et v132 = **janvier 1747, en double** | voir le doublement de 1747 plus bas |

**ET LES IDENTIFIANTS DE CETTE COMMUNE NE SE SUIVENT PAS** : dix numéros séparent 27771 de 27781,
et ce qui est entre appartient à d'autres paroisses — 27780 est un registre de 1727-1736 aux
hameaux de La Varenne et de Fourchayt. Ne rien déduire d'un voisinage de numéro.

**`visionneuse-infos` VEUT LA FICHE DU REGISTRE, ET IGNORE LE NUMÉRO QU'ON LUI PASSE.** Piège payé
le 18 août 2026 : appelé avec la fiche du 2/7 et `image/27770`, il rend la numérisation du 2/7.
On croit sonder les voisins, on interroge sept fois le même registre. **C'est la fiche qui
désigne le volume**, pas le dernier segment de l'URL.

**À NOTER SUR LES INTITULÉS** : le nombre d'actes par type affiché dans le panneau de droite
ne dit pas qu'un registre est monotype — un même volume porte souvent B, M et S ensemble.

**ET CE VOLUME PORTE L'ANNÉE 1747 EN DOUBLE — LE CAHIER DU CURÉ ET SON DOUBLE DE GREFFE.**
Découvert le 17 août 2026 parce que deux agents rapportaient *le même acte* à deux numéros de
vue différents. Les deux séries sont séparées par une page de titre — « Registre de l'église de
St Pal en Chalençon pour l'année 1747 » — et par une certification du bailliage datée du
31 décembre 1746, signées du prévôt et du greffier. Correspondances relevées :

| acte | copie A | copie B |
|---|---|---|
| baptême de Jean PEYRET, 16 janvier 1747 | vue **117 G** | vue **132 G** |
| sépulture de Paule CATHEBARD, 14 novembre 1747 | vue **141 D** (suite) | vue **126 G/D** |
| sépulture de Marie VIALAVON, 16 novembre 1747 | vue **141 D** | vue **126 D** |

**CE N'EST PAS UNE REDONDANCE, C'EST UN INSTRUMENT, ET C'EST LE MEILLEUR QUE CE PORTAIL OFFRE.**
Le plafond de résolution de l'AD43 — ~1250 px par page — laisse régulièrement un mot indécis ;
**deux plumes indépendantes copiant le même acte donnent deux chances au même mot**. Le 17 août
au soir, il a tranché en une image ce que quatre zooms n'avaient pas tranché : le jour d'un
baptême (« ſezieme », contre « dixième » et « sixième » proposés par deux agents) et un âge au
décès sur lequel **trois** lectures se contredisaient — 45 dans les deux copies, contre 46, 57
et 75 ailleurs.

**DONC : avant de noter un mot `[non lu]` dans un registre d'Ancien Régime, chercher si l'année
existe en double dans le même volume.** Le repère est une page de titre ou une certification de
bailliage au milieu du volume, et une plage de dates qui recommence.

**ET UN COMPTE DE VUES N'EST PAS UN COMPTE DE FEUILLETS.** E-dépôt 2/8 annonce 504 vues et en
porte **sept qui re-photographient le feuillet précédent** — v020-021-022, v127-128, v281-282,
v299-300, v301-302, v401-402. Les fichiers diffèrent en octets, donc ce ne sont pas des
téléchargements en double : ce sont deux prises du même feuillet. Deux agents l'ont signalé
indépendamment le 17 août 2026 en croyant à un bogue de rendu. **Une couverture annoncée en
vues surestime donc légèrement le travail fait**, et une plage qui « ne rend rien » peut être
plus courte qu'elle n'en a l'air. Le détecteur tient en dix lignes — corrélation de deux
vignettes 64 × 64 consécutives, seuil 0,90.

**DEUX CHOSES SONT PROPRES À CE REGISTRE, ET ELLES SEULES** — le reste se lit comme partout
ailleurs, avec le moteur unique. Mais **elles ne se devinent pas, donc on entre par
`sp.py`**, qui n'est plus qu'une façade sur ce moteur et ne garde que ces deux réglages :
`python sp.py <a> <b>` pour rendre, `python sp.py z <vue> <G|D> <y0> <y1> <dest> …` pour
zoomer. Appeler `nas.py` directement sur ce registre fonctionne aussi, mais **fait perdre
les deux**.

**1. Trois vues au moins sont photographiées la tête en bas** dans E-dépôt 2/8. Elles sont
restées illisibles plusieurs jours faute d'une rotation, et rien dans l'image ne le signale
avant qu'on l'ouvre. `NAS_ROT=10,11,12` donne la liste des vues à retourner.

**2. Le seuil de boîte d'encre y vaut 0,012, et il ne doit pas bouger.** Les outils
historiques ne s'accordaient pas — 0,010 ailleurs, 0,012 ici — et **les fractions de zoom
déjà notées dans le corpus sont relatives à l'un ou à l'autre**. Changer la valeur les
déplacerait toutes, et avec elles les découpes d'actes déjà publiées. Chaque appelant garde
donc la sienne.

*Ces vues sont des doubles pages à 2500 px. Un seuil de découpe en pixels absolus les prenait
pour des pages simples et coupait le texte en deux ; c'est désormais l'orientation qui
tranche, et le problème ne se pose plus.*

**ET LE PLAFOND DE RÉSOLUTION SE PAIE ICI, PAS AILLEURS.** 2500 px en double page font environ
**1250 px par page**, contre 1818 à l'AD42. C'est assez pour lire un acte, trop peu pour
trancher une lettre finale : le 17 août 2026, le patronyme d'un parrain est resté « PEYREL ou
PEYRET » parce qu'un « l » bouclé et un « t » barré en bout de mot sont le même dessin à cette
échelle. Agrandir n'ajoute rien — `?size=full` est déjà la taille du master. **Un nom qui se
joue à une lettre, sur ce portail, se note `[lecture incertaine]` et se tranche en salle de
lecture.**

---

## AD37 — Indre-et-Loire · moteur **Naoned**

**Le portail le plus facile des trois, et le seul qui ne demande aucun navigateur.** Fiche
complète dans [`scripts/archives/portails.json`](../../../../scripts/archives/portails.json), clé `37` ;
le code est dans [`scripts/archives/moteurs/naoned.py`](../../../../scripts/archives/moteurs/naoned.py).
Trois fonctions, trois requêtes HTTP ordinaires : `recherche()`, `vues()`, `telecharge()`.

| Ce qu'on veut | Comment |
|---|---|
| les registres d'une commune | `/search/results?formUuid=…&0-controlledAccessGeographicName[]=…` — **rendu côté serveur**, 50 Ko de HTML avec arks, cotes et nombre de vues. `&page=N`, vingt par page |
| le libellé exact d'une commune | il est dans le HTML de `/search/form/{formUuid}`, doublement encodé — `libelles()` le décode |
| **les vues d'un registre** | **`/iiif/ark:/{naan}/{arkName}/manifest.json`** — les 143 vues en une requête, dans l'ordre |
| une image | `{base}/images/{uuid}.jpg`, ~2000 × 2915, sans cookie ni compte |

**Ce qu'il ne faut pas faire**, et qui a été payé : passer par
`/visualizer/api/record/…/media/…`, que le bundle JS construit et qui rend 404 depuis
l'extérieur ; demander une URL au bouton de téléchargement, qui produit un blob et n'en a pas ;
filtrer sur le type « Table decennale », qui ne répond pas pour toutes les communes.

**LE SERVEUR LAISSE TOMBER UNE IMAGE DE TEMPS EN TEMPS**, et il le fait en silence : la réponse
arrive tronquée, et le JPEG lève un `MemoryError` ou une erreur de décodage **au moment de la
lecture**, c'est-à-dire une demi-heure après le tirage, quand plus personne ne pense au réseau.
**Vérifier chaque image reçue par `Image.verify()` et la redemander** — c'est une seconde par
vue, contre un dépouillement à recommencer.

**LE MÊME MOTEUR SERT L'AD19 (Corrèze)**, où attendent les mariages de Bort-les-Orgues pour les
ANTIGNAC, les DUTOUR et les LE PIPE. Il n'y a qu'à changer `base` et `naan` — et vérifier le
`formUuid`, qui est propre à chaque portail.

**DEUX PORTAILS MANQUENT À CE DOSSIER, ET ILS BLOQUENT LA SUITE DE LA BRANCHE CHASLES :**

| | Ce qui y attend |
|---|---|
| **AD49 — Maine-et-Loire** | **BREIL**, à huit kilomètres de Lublé : la naissance de Jeanne MÉRAY vers 1776, ses parents Jean MÉRAY × Jeanne CHARPENTIER, et son mariage avec Urbain CHASLE avant octobre 1805 |
| **AD72 — Sarthe** | **AUBIGNÉ** (Aubigné-Racan depuis 1932 ; les registres du XIXᵉ sont sous « Aubigné ») : le baptême de Michel François GALET vers 1777, qui donnerait l'âge et le métier de Jean GALET et Marie DORISSE |

**Commencer par regarder si leur moteur est déjà écrit** — c'est le cas nominal, vérifié deux
fois : ni l'AD45 ni l'AD67 n'ont demandé une ligne de code.

### AD43 — le fonds des MATRICULES MILITAIRES est un AUTRE moteur Arkothèque, avec sa propre instance

**Découvert le 6 septembre 2026, en cherchant la fiche matricule n° 1264 de Jean Régis PAIRÉ,
classe 1903.** La page unique état civil ci-dessus ne sert QUE l'état civil — les registres
matricules militaires (série 1 R) vivent sur une page séparée, avec sa propre instance
Arkothèque, sans rapport avec `arko_default_616fd22b91d20` :

```
/archives-en-ligne/familles-et-individus-en-haute-loire/tables-et-registres-matricules-militaires
```

| rôle | identifiant |
|---|---|
| instance de ce fonds | `arko_default_616fd4be9e095` |
| id de contenu (le tableau des 454 registres) | `2512873` (parfois vu `2512872` selon le rendu) |
| visionneuse de ce fonds | `arko_default_616fd58fe6fce` |

**LE TABLEAU DE RÉSULTATS EST LA LISTE DES REGISTRES, PAS UNE RECHERCHE NOMINATIVE.** 454 lignes,
colonnes Classe / Table-registre-liste-PV / Contenu / Cote / Commentaires / Images, triées par
classe croissante. Une classe se découpe en plusieurs cotes : plusieurs « Registre matricule,
Matricules N-M » qui couvrent le département dans l'ordre (ex. classe 1903 : 1-497, 498-988,
989-1490, 1491-1993, 1994-2396, réparties sur 1 R 944 à 1 R 948), **plus un « Conscrits de
l'arrondissement de Brioude »** à part (1 R 949 pour la classe 1903) et **une « Table des
registres matricules · Table alphabétique »** de la classe entière (1 R 950, ~30 images
seulement — bon marché à lire en entier).

**LE FONDS « ARRONDISSEMENT DE BRIOUDE » N'EST PAS CE QU'ON CROIT.** Son image de couverture est
un « Bordereau des feuillets matricules adressés au bureau de Recrutement du Puy » **par le
Bureau de Recrutement d'AURILLAC** (13ᵉ Corps d'Armée, Cantal) — des conscrits transférés d'un
bureau voisin, pas la population de l'arrondissement de Brioude en général. **Ne pas supposer
qu'un homme né dans l'arrondissement de Brioude y est classé : la numérotation matricule
principale (1-2396 pour 1903) couvre tout le département, Brioude compris**, et c'est elle qu'il
faut chercher en premier à partir du numéro de matricule seul.

**RÉCUPÉRER LE TABLEAU COMPLET SANS CLIQUER LA PAGINATION** — elle est fragile (fenêtre
glissante de boutons numérotés, `.page_en_cours` qui ne change pas toujours de façon fiable
après un clic). L'API JSON sous-jacente rend le HTML déjà formaté dans son propre champ, page
par page :

```
GET /_recherche-api/search/60
  ?arko_default_616fd4be9e095--filtreGroupes[mode]=simple
  &arko_default_616fd4be9e095--filtreGroupes[op]=AND
  &arko_default_616fd4be9e095--from=<0,25,50…>
  &arko_default_616fd4be9e095--resultSize=25
  &arko_default_616fd4be9e095--contenuIds[]=2512873
  &arko_default_616fd4be9e095--modeRestit=arko_default_616fd648a113e
```

La réponse porte `{"total":454,"results":[{intitule, refUnique, …}], "html": "<tr>…</tr>…"}` —
**`results[].refUnique` (un `arko_fiche_…`) et le `html` rendu sortent dans LE MÊME appel**,
inutile de les récupérer séparément. Appelé depuis `page.evaluate(fetch(...))` **dans le
contexte du navigateur** (le cookie anti-robot posé par la navigation initiale suffit), 19
appels couvrent les 454 lignes en une minute.

**POUR OUVRIR LES IMAGES D'UNE COTE PRÉCISE** (ex. la table alphabétique 1 R 950) : chercher son
`refUnique` dans les lignes ci-dessus, puis lire dans le HTML de sa ligne l'attribut
`data-visionneuse-url` du bouton « Visualiser les images » — il porte l'`idArkoFile` (l'image de
départ) tout fait :

```
/_recherche-api/visionneuse-infos/arko_default_616fd4be9e095/<refUnique>/arko_default_616fd58fe6fce/image/<idArkoFile>
```

Appelé en JSON, il rend `medias[0].sources[0].src` — `.../…/show/<numerisation>/image/<idArkoFile>/0`,
exactement l'entrée qu'attend `node arkotheque.js 43 <numerisation> <idArkoFile> <nb_vues> <dossier>`.

**MAIS UN `idArkoFile` NE COUVRE PAS TOUJOURS TOUTES LES IMAGES ANNONCÉES PAR LA COTE.** Sur
1 R 946 (989-1490, annoncé 653 images), le téléchargement rend 89 vues puis « rien » en boucle
à partir de la 90ᵉ — recompté deux fois, ce n'est pas un raté transitoire. Une cote de cette
taille est probablement fragmentée en plusieurs `idArkoFile` (le JSON de la visionneuse porte un
champ `position` qui le suggère) ; celui qu'on lit dans `data-visionneuse-url` n'est que le
PREMIER. **Non résolu au 6 septembre 2026** — reste à trouver comment lister les fragments
suivants d'une même cote plutôt que d'en déduire l'existence par un nombre d'images qui ne
correspond pas.

**LA TABLE ALPHABÉTIQUE N'EST PAS STRICTEMENT ALPHABÉTIQUE, ET LA MAJUSCULE `P` MANUSCRITE DE CE
GREFFIER SE LIT COMME UN `I`.** Sur la table de la classe 1903 (1 R 950), toute la section des
patronymes commençant par P — Pabiou, Pagnac, Pascal, Paulet, Perrier, Petit… — est illisible
comme telle : la capitale ressemble à un « I » ou un « J » cursifs. Il a fallu lire « Ietit » et
reconnaître « Petit » pour comprendre. **Chercher un P dans ce registre veut donc dire lire
aussi tout ce qui ressemble à un I ou un J en tête de nom.** Et l'ordre secondaire (par prénom)
n'est pas toujours respecté à l'intérieur d'un même nom — des ajouts tardifs semblent posés en
bas de la case plutôt qu'insérés à leur place.

---

## AD16 — Charente · moteur **Boscop / Ligeo**, mais un index NOMINATIF, pas une liste de registres

Portail : « La Source », <https://archives.lacharente.fr/> — **la vitrine.** Le moteur vit sur un
autre domaine : `https://lasource.archives.lacharente.fr/`. Les formulaires (`RECH_nom`,
`RECH_communenaissance_Md5`…) pointent dessus, et c'est lui qu'il faut appeler.

**Anubis protège tout le domaine** — même préfixe `.within.website/x/cmd/anubis/…` qu'ailleurs.
Un Chrome fenêtré ordinaire le passe seul en quelques secondes ; lui laisser le temps.

**LES MATRICULES MILITAIRES SE CHERCHENT PAR NOM, ET C'EST RARE — LA PLUPART DES PORTAILS
N'OFFRENT QU'UNE LISTE DE REGISTRES (voir AD43 ci-dessus).** Page :
`/s/16/registres-matricules`, formulaire posté vers `.../archive/recherche/matricules/n:123`.
Champs utiles, en clair, SANS résolution facette : `RECH_nom`, `RECH_prenom`. D'autres
(`RECH_communenaissance`, `RECH_dptnaissance`, `RECH_bureau`) portent un `_Md5` et suivent la
convention Boscop habituelle (résoudre par `arcfacette.php` avant de filtrer dessus — non
tenté, le nom seul a suffi).

**LA RECHERCHE PAR NOM FAIT DE LA SOUS-CHAÎNE, PAS DE L'EXACT.** `RECH_nom=PAIRE` a rendu
48 réponses : PAIRÉ, mais aussi DUREPAIRE, LAPAIRE, VEMPAIRE, DURREPAIRE — tout ce qui contient
la chaîne. C'est un avantage, pas un défaut : ça a permis de trouver « PAIRÉ » sans connaître
sa forme exacte à l'avance.

**SOUMETTRE LE FORMULAIRE PAR `el.form.submit()`, PAS PAR UN CLIC.** Le bouton `RECH_Valid` est
souvent hors du viewport visible (page longue, facettes au-dessus) et Playwright refuse de
cliquer un élément qu'il juge non atteignable. Remplir le champ texte puis
`page.$eval('input[name="RECH_nom"]', el => el.form.submit())` évite le problème.

**UN RÉSULTAT MÈNE À UN `<h3>`, PAS UN `<a>` — LE VRAI LIEN EST DANS UN SVG VOISIN.** Le titre
de la notice (`<h3>1 R 148 - PAIRé Jean Régis</h3>`) n'est pas cliquable ; il faut remonter à la
`<tr class="arc_pair">` qui l'entoure pour trouver `data-visionneuse-url` sur le bouton
« Visualiser les images » ou, plus simple, l'URL de la vignette IIPImage directement dans
l'`<img src>` :

```
https://lasource.archives.lacharente.fr/cgi-bin/iipsrv.fcgi?FIF=<chemin encodé>&HEI=240&…
```

Le chemin porte tout ce qu'il faut : `.../images/SERIE_R/1R/1R_0148/FRAD016_1R_0148_0081.jpg`.

### ⚠️ MAIS LE MANIFESTE IIIF RÉPOND, ET IL FAUT PASSER PAR LUI *(complété le 7 septembre 2026)*

`{base}/ark:/61904/{ark}/manifest` rend un manifeste IIIF en règle — **exactement l'URL que
`boscop.js` construit déjà**. Ce portail est donc servi par le module existant, il n'y avait
aucune ligne de code à écrire, et sa fiche est désormais dans `portails.json`. Le paragraphe
ci-dessus n'est pas faux, il est seulement le chemin le plus long : IIPImage reste utilisable
en direct, mais il ne dit ni combien de vues porte une notice, ni lesquelles.

**IIPIMAGE INTERPOLE SANS LE DIRE, ET `WID=2400` EST UN MAUVAIS CONSEIL.** Le TIFF source fait
**1699 × 2063** (`{base}/iiif/SERIE_R/1R/1R_0148/FRAD016_1R_0148_0081.jpg/info.json` le dit).
Demander `WID=2400` rend 2400 × 2914, `WID=6000` rend 6000 × 7285 : un fichier trois fois plus
lourd, pas un pixel d'information de plus. **Omettre `WID`, ou prendre IIIF `full/full`** —
les deux rendent le natif. C'est la règle générale de la skill, appliquée ici : quand on
atteint la résolution native, on s'arrête.

**« 3 VUES » NE VEUT PAS DIRE TROIS PAGES DE LA MÊME PERSONNE**, et c'est le manifeste qui
tranche. La notice de PAIRÉ Jean Régis annonce 3 vues ; ses canvas sont **`_0081`, `_0082` et
`_0083`**, soit **trois fiches de trois hommes différents** — PAIRÉ (n° 80 de la liste),
BEAUCHAMPS Pierre Roger (n° 81) et CARTEAU Pierre André (n° 82) —, une fiche par page, rangées
à la file. La notice ouvre donc une **fenêtre** de vues autour du nom indexé, pas le dossier
d'un homme. *Ne pas extrapoler la numérotation : une première lecture avait supposé
`_0080/_0081/_0082` et attribué la vue voisine à un « Veillon » qui n'y est pas. Le manifeste
donne les numéros, il ne coûte qu'une requête.*

**UNE FICHE MATRICULE PEUT S'ARRÊTER NET, ET LE TRAIT DIAGONAL N'A RIEN DE PERSONNEL.** Celle
de PAIRÉ Jean Régis est barrée d'un large trait et son encadré « campagnes, blessures,
décorations » reste vide au-delà de l'engagement de 1904. **Ses deux voisines de registre le
sont aussi** : BEAUCHAMPS et CARTEAU sont, comme lui, des engagés volontaires de mars 1904,
tous trois « classés dans la 3ᵉ partie de la liste », tous trois barrés, tous trois muets sur
la suite. C'est ce que ce registre fait à **tous** ceux dont le service se suit ailleurs —
registres du corps, puis dossier d'officier au SHD de Vincennes. Ne pas lire une intention
dans ce trait, et ne pas conclure d'une fiche muette que rien d'autre n'existe.

**ET LA « 3ᵉ PARTIE DE LA LISTE » EST CELLE DES ENGAGÉS VOLONTAIRES.** L'article cité par le
conseil de révision est l'**article 59 de la loi du 15 juillet 1889**, celui qui régit
l'engagement volontaire — la note imprimée en bas de la fiche, elle, ne nomme que les 5ᵉ
(ajourné), 6ᵉ (service auxiliaire) et 7ᵉ (Marine) parties. Les trois fiches voisines le
confirment par l'usage. *Attention à la lecture du numéro : le greffier écrit d'abord
« art. 50 » puis corrige en « 59 » sur deux des trois fiches, et laisse « 50 » sur la
troisième.*

---

## AD45 — Loiret · moteur **Arkothèque**

Ouvert le 25 août 2026 pour le chantier STENGEL-HUME (voir
[`stengel-hume/RACCORDEMENT.md`](../../../../stengel-hume/RACCORDEMENT.md)). **Le moteur était déjà
écrit** : c'est de l'Arkothèque, comme la Haute-Loire, et `moteurs/arkotheque.js` sert les deux.
Il n'a fallu qu'une fiche dans `portails.json` — le cas nominal annoncé par le README, vérifié
pour la première fois.

**Comment on l'a su, et ça a pris cinq minutes.** Onglet Réseau : `arko-analytics-*.js`,
et des paramètres d'URL en `arko_default_…` et `arko_fiche_…`. La signature est dans le nom
des choses ; inutile de chercher plus loin.

| | |
|---|---|
| Recherche, visionneuse, API | `https://consultation.archives-loiret.fr` |
| **Images** | **`https://www.archives-loiret.fr`** |
| Page état civil | `/faire-vos-recherches/archives-numerisees/etat-civil` |
| Instance | `arko_default_61e6b3f775f99` |
| Champ commune | `arko_default_61e6b4731902f` · mode `popup` |
| Champ type de registre | `arko_default_61e6b47300d5d` · mode `select` |
| Visionneuse | `arko_default_61e6b4c898689` |
| Compte | aucun |

**LE PIÈGE DU PORTAIL : DEUX DOMAINES.** La recherche et la visionneuse sont sur
`consultation.`, **les JPEG sont servis par `www.`**. Le champ `src` de `visionneuse-infos` le
dit en clair — le lire, plutôt que de reconstruire l'URL sur le domaine où l'on se trouve, qui
ne sert pas les images. C'est la leçon de l'AD37 appliquée d'avance : *lire la réponse en entier
avant de deviner une URL*.

**Trois différences avec l'AD43, et elles cassent le script de l'AD43 si on les ignore :**

1. Tout paramètre porte le préfixe `{instance}--`, y compris `filtreGroupes`, `from` et
   `resultSize`.
2. Le champ commune se contente du **libellé accentué** en une seule valeur `q[]` — pas du
   doublon « sans-accents`[[fiche_communes]]` » qu'exige la Haute-Loire.
3. C'est `/_recherche-api/moteur` qui répond, en JSON, et `resultats.html` porte le tableau
   complet. D'où `moteurs/arkotheque_liste.js`, qui parle l'API plutôt que de tordre le script
   de page de l'AD43.

**ET `resultSize` EST PLAFONNÉ À 25, EN SILENCE.** Demander 200 rend 25 sans erreur ni
avertissement — même famille que les paramètres ignorés sans bruit de l'AD37. On pagine sur
`from` et **on vérifie le compte final contre `resultats.total`** : c'est ce qui distingue une
liste complète d'une liste tronquée qu'on croit complète.

```bash
NODE_PATH="<maison>" \
  node scripts/archives/moteurs/arkotheque_liste.js 45 "Cléry-Saint-André" > clery.tsv
```

Le TSV rend la **cote**, la **paroisse**, les **dates**, le **nombre de vues** et surtout
l'**idArkoFile** du registre — lu dans l'attribut `data-visionneuse` du bouton œil. Plus besoin
d'ouvrir la visionneuse à la main pour l'obtenir, contrairement à ce que faisait la Haute-Loire.

**Images** : `{www}/_recherche-images/show/{numérisation}/image/{registre}/{rang}?size=full`,
même recette de jeton anti-robot qu'en Haute-Loire.

**ET LE FETCH DOIT PARTIR DU DOMAINE DES IMAGES.** Ancré sur `consultation.`, il tire vers
`www.` et le navigateur le bloque en CORS — « TypeError: Failed to fetch », le téléchargement
meurt à la première vue. `arkotheque.js` s'ancre donc sur `base_images` quand la fiche en
déclare un. Le piège n'existe pas en Haute-Loire, où recherche et images partagent une origine :
c'est le double domaine qui le crée.

**LA RÉSOLUTION VARIE D'UN REGISTRE À L'AUTRE, ET UN ÉCHANTILLON NE VAUT PAS RÈGLE.** La fiche
a d'abord annoncé « 1650 × 2500 en page simple » sur la foi du premier registre ouvert ;
`GG/121` est en **double page 2500 × ~2200**, soit ~1250 px par page — le plafond de la
Haute-Loire, avec la pliure à trouver. Interroger `infosImage` registre par registre.

**Ce que couvre Cléry-Saint-André** : 206 registres, dont **122 antérieurs à 1793**, le plus
ancien de **1577**. **La commune a DEUX paroisses**, Notre-Dame et Saint-André, et elles ont
chacune leur série : filtrer sur la commune les rend toutes les deux, filtrer sur une paroisse
en perd la moitié.

**`216 O-SUPPL GG/121` N'EST PAS UNE TABLE ALPHABÉTIQUE, MALGRÉ SON INTITULÉ AU CATALOGUE.**
C'est une table **chronologique** — année, mois, jour, puis le nom du baptisé — et elle compte
trois séquences qui repartent chacune au début : baptêmes, mariages, sépultures. On n'y saute
donc pas à la lettre du patronyme cherché ; on y entre par la date. Elle commence en **1573**,
vingt ans avant la fourchette annoncée. Le catalogue décrit ici le genre du document, pas son
classement : **l'ouvrir avant de bâtir une stratégie de dépouillement dessus.**

---

## AD67 — Bas-Rhin · moteur **Boscop / Ligeo-Archives**

Ouvert le 26 août 2026. **Le moteur était déjà écrit** — c'est celui de la Loire, et la
balise `<meta name="Generator">` le dit en clair : « Boscop / Ligeo-Archives ». Deuxième
fois d'affilée qu'un département nouveau ne demande qu'une fiche de configuration.

| | |
|---|---|
| Recherche et visionneuse | `https://archives67.alsace.eu` |
| Vitrine | `https://archives.alsace.eu` — CMS Umbraco, **aucun moteur d'archives** : ne pas y chercher les registres |
| Haut-Rhin | `https://archives68.alsace.eu`, mêmes Archives d'Alsace, à vérifier séparément |
| Page état civil | `/archive/recherche/etatcivil/n:128` |
| Résultats | `/archive/resultats/etatcivil/lineaire/n:128?type=etatcivil&…` |
| ARK | `ark:/78665/{id}` |
| Compte | aucun |

**LE PORTAIL EST DERRIÈRE ANUBIS**, une preuve-de-travail. `curl` reçoit 4 185 octets
portant un CSS `/.within.website/x/xess/` et rien d'autre. Un vrai Chrome la résout seul en
une dizaine de secondes — **lui laisser le temps avant de lire la page**, sinon toutes les
requêtes rendent le HTML du défi au lieu du JSON attendu, et le script conclut à tort que le
registre est vide.

**`RECH_commune` SEUL NE REND RIEN, ET LE PIÈGE COÛTE UNE DEMI-HEURE.** Il faut
`RECH_commune_Libel` **et** `RECH_commune_Md5`, tous deux suffixés d'une **barre verticale**.
Le libellé est en **majuscules sans accent et sans parenthèse de département** — `GOUGENHEIM`,
jamais « Gougenheim (Bas-Rhin, France) », qui est la forme de la Loire et ne rend zéro.

**Et le Md5 est simplement celui du libellé majuscule** : `md5('SOULTZ-SOUS-FORETS')` =
`7bdca7d66d9e3202abf564e5d7474236`, exactement ce que pose le formulaire. Vérifié au
caractère près. **Aucune facette à récupérer : n'importe quelle commune se construit de
tête.** Les paramètres de pagination de la facette, eux, n'ont pas été trouvés — inutile de
chercher, on teste la commune directement.

**La vue s'appelle `lineaire` ici et `tabulaire` en Loire**, et le `n:NN` est propre au
portail : 128 pour l'état civil, 131 recensements, 145 cadastre, 146 successions,
148 chartes, 154 conscription.

**Types d'acte** — liste fermée, avec le nombre de documents en regard : registre de
mariages (67 547), de naissances (66 298), publications de mariages (14 044), tables
décennales (7 750), registre de baptêmes (2 837), sépultures, décès, tables des mariages et
des décès, registre blanc.

**Images : IIIF.** Manifeste `{base}/ark:/78665/{ark}/manifest` — IIIF Presentation 2,
`sequences[0].canvases`, chaque canvas portant `images[0].resource.service['@id']` ; c'est ce
**service** qu'il faut, pas l'`@id` du canvas. Puis `{service}/full/full/0/native.jpg`.
Natif **2592 × 1792**, ~530 Ko la vue. `native.jpg`, `default.jpg` et `full/max` rendent le
même fichier à l'octet près : inutile de chercher mieux.

**Ne pas réassembler les tuiles.** La visionneuse (OpenLayers, `/binocle/monocle/`) tire des
tuiles par `iipsrv.fcgi` — le manifeste donne l'image entière en une requête.

**LE FOND NOIR EST LARGE — jusqu'à 25 % de la surface.** Un recadrage qui cherche les pixels
sombres le prendra pour de l'encre et ne recadrera rien : chercher le papier, c'est-à-dire la
zone claire.

**Couverture** : registres paroissiaux et état civil de toutes les communes, du XVIᵉ siècle à
1912 selon la localité, plus de 3 millions d'images. Une commune ordinaire porte 380 à 400
registres ; Strasbourg en porte 3 311. L'état civil est **année par année**, 7 à 28 vues par
registre.

**LES GRAPHIES DE COMMUNE SONT UN PIÈGE À ELLES SEULES**, parce que l'administration
allemande a laissé ses formes dans les papiers de famille. Relevé sur un arbre alsacien :
GUGENHEIM → **GOUGENHEIM**, KLEINGOFT → **KLEINGOEFT**, FRIEDOLSH → **FRIEDOLSHEIM**,
WILLGOTH → **WILLGOTTHEIM**, JEDERSWILLER → **JETTERSWILLER**, GRIESHEIM →
**GRIESHEIM-SUR-SOUFFEL**. Et **ZORNHOF n'est pas une commune** mais un écart de MONSWILLER.
Le formulaire imprimé de 1872 porte « Bürgermeisterei Gugenheim, Kreis Straßburg » : la
graphie familiale n'est pas une faute, c'est celle de son époque — elle est seulement
inutilisable pour interroger le portail.

---

## AD49 — Maine-et-Loire · moteur **Arkothèque**

Ouvert le 27 août 2026 pour la branche CHASLE, dont trois lieux — **Breil, Auverse,
Meigné-le-Vicomte** — sont à moins de quinze kilomètres de Lublé, de l'autre côté de la limite
départementale. **Le moteur était déjà écrit**, troisième fois d'affilée. Mais ce portail-ci a
demandé du code quand même, et pour une bonne raison : **il ne se défend pas**.

| | |
|---|---|
| Recherche, visionneuse, images | `https://recherche-archives.maine-et-loire.fr` |
| Vitrine | `https://archives.maine-et-loire.fr` — **TYPO3, aucun moteur d'archives**. `archives49.fr` ne résout pas ; `www.archives49.fr` y redirige |
| Page état civil et paroissial | `/rechercher-et-consulter/archives-consultables-en-ligne/etat-civil-et-registres-paroissiaux` |
| Instance | `arko_default_6825f9c6950b1` — **13 347 registres** |
| Compte | aucun |
| **Résolution** | **5496 × 3896**, ~1,2 Mo la vue |

**C'EST LE SEUL PORTAIL ARKOTHÈQUE DU DOSSIER QUI NE DEMANDE PAS DE NAVIGATEUR.** L'AD43 et
l'AD45 rendent « 403 Attack detected » à tout ce qui n'est pas un vrai Chrome ; ici une requête
Python ordinaire passe de bout en bout, du référentiel des communes au JPEG. D'où
**[`moteurs/arkotheque.py`](../../../../scripts/archives/moteurs/arkotheque.py)**, à côté du
`.js` qui reste nécessaire pour les deux autres. Le drapeau `http_simple` de `portails.json`
décide : sans lui le module refuse de servir un portail, **parce qu'un WAF répondrait par du
HTML de défi que le code prendrait pour du JSON, et conclurait à tort qu'un registre est vide.**

```bash
python scripts/archives/moteurs/arkotheque.py 49 communes breil
python scripts/archives/moteurs/arkotheque.py 49 registres "Auverse"
python scripts/archives/moteurs/arkotheque.py 49 tirer <arko_fiche_…> <idArkoFile> "<dossier>" 1 85
```

### Ce que ce portail apprend et qui vaut pour les autres

**LE PORTAIL PUBLIE SA PROPRE TABLE DE ROUTAGE, ET ELLE REMPLACE TOUT LE TÂTONNEMENT.**
`{base}/js/routing` rend **583 routes FOSJsRouting en JSON**, chemins compris. C'est de là que
sont sortis, sans en deviner un seul : l'API du moteur, la signature exacte de
`visionneuse-infos`, l'existence d'un proxy IIIF. **À essayer sur tout portail Arkothèque avant
de tâtonner** — c'est la leçon « lire la réponse avant de deviner une URL », mais en amont : ici
le site distribue lui-même sa documentation.

**ET L'API DU MOTEUR SE DÉCRIT ELLE-MÊME.** `/_recherche-api/moteur?refUnique={instance}`,
appelée **sans aucun filtre**, rend `filtres`, `restits`, `tris` et `routes` : les identifiants
de tous les champs, en clair. Aucun n'a été gratté dans un HTML de formulaire — ce qui avait
coûté une soirée en Haute-Loire, où la page servie ne contient **aucun `<input>`**. Le formulaire
de l'AD49 non plus n'en contient aucun ; **il n'a pas fallu le chercher.**

| rôle | identifiant |
|---|---|
| instance (état civil + paroissial) | `arko_default_6825f9c6950b1` |
| champ Commune | `arko_default_6825fa8970a3c` — type **`select`**, et non `popup` comme à l'AD45 |
| structure du référentiel des communes | `arko_default_67fcedf5535c0` |
| champ Arrondissement / paroisse | `arko_default_6825fa8986424` |
| champ Type d'acte | `arko_default_6825fa8993189` |
| visionneuse | `arko_default_6825fb982f56a` |

*Autres formulaires du portail* : recensements `arko_default_6841a02713045`, matricules
militaires `arko_default_67fcd5fcb1798`, base des combattants `arko_default_6826fed908a50`,
inventaires `arko_default_67fd2361374ed`.

**LES 442 COMMUNES SORTENT EN UNE REQUÊTE, SANS FILTRE.** La réponse du moteur porte une
agrégation — `resultats.aggregations[0][structure][structure + '_terms'].buckets` — qui liste
**toutes** les communes avec leur `arko_fiche` et leur nombre de registres. C'est la réponse la
plus courte jamais obtenue au piège *« un libellé de commune se lit, il ne se reconstruit pas »* :
un HTML de formulaire à gratter en Touraine, une facette impaginable en Alsace, **et ici une
ligne**.

**DEUX PIÈGES DE LIBELLÉ QUAND MÊME :**
- **l'article passe à la fin**, à la française — `Ponts-de-Cé (Les)`, `Breille-les-Pins (La)`,
  `Meignanne (La)` ;
- **« Breil » n'est pas « Breille-les-Pins (La) »**. Deux communes distinctes, qu'une recherche
  partielle attrape ensemble — même famille que les trois Saint-Pal de Haute-Loire.

**LES REGISTRES SONT CLASSÉS SOUS LES ANCIENS NOMS DE COMMUNE, JAMAIS SOUS LA COMMUNE
NOUVELLE.** Breil, Auverse, Meigné-le-Vicomte, Chigné et Genneteil sont communes déléguées de
**Noyant-Villages** depuis le 15 décembre 2016 ; chacune a son entrée, et **Noyant-Villages n'en
a aucune**. Le « Noyant » du référentiel est l'ancienne commune de Noyant. Vérifié, et c'est ce
qu'annonçait le handoff.

### Les deux collections — l'atout de ce portail

**LA COMMUNALE ET LA DÉPARTEMENTALE SONT NUMÉRISÉES TOUTES LES DEUX**, et la colonne
`collection` du tableau le dit. À Breil, les BMS 1773-1782 existent dans un **registre communal
de 85 vues** *et* dans le **volume départemental 1757-1792 de 316 vues**. À Auverse, un communal
1773-1782 de 110 vues et un départemental 1764-1792 de 337.

**C'est le « 1747 en double » de l'AD43, mais à l'échelle du département** — et là-bas c'était un
accident de reliure qu'il fallait repérer à des indices, ici c'est systématique et annoncé.
**Deux plumes indépendantes copiant le même acte donnent deux chances au même mot.** Avant de
noter un nom `[non lu]` sur ce portail : **aller voir l'autre collection.**

### Les images

| | |
|---|---|
| liste des vues | il n'y en a pas : le **rang** va de `0` à `n-1`, et `n` est le nombre de vues du tableau |
| une vue | `{base}/_recherche-images/show/{numérisation}/image/{idArkoFile}/{rang}?size=full` |
| la numérisation | `visionneuse-infos`, puis **lire `medias[0].sources[0].src`** — elle ne se déduit pas |

**`?size=full` OU L'ON PERD LES DEUX TIERS DE L'IMAGE.** Sans lui, 2000 × 1418 au lieu de
5496 × 3896. Même plafond de 2000 px qu'en Haute-Loire, **et il coûte bien plus cher ici parce
que le master est bien plus grand.**

**LE COMPTE DE VUES EST EXACT, ET C'EST RARE.** Vérifié sur `idArkoFile 76458`, annoncé à
85 vues : les rangs 0 à 84 sont servis, **85 rend 404**. Rien à voir avec l'AD43, dont sept vues
re-photographiaient le feuillet précédent.

**LA SIGNATURE DE `visionneuse-infos` A SIX SEGMENTS, ET NOS FICHES N'EN NOTAIENT QUE CINQ** —
`{refUniqueMoteur}/{refUniqueFiche}/{refUniqueField}/{mediaType}/{idArkoFile}/{position}`. La
table de routage l'a donnée en clair. **Le dernier segment est ignoré** : `position` 0 et 1
rendent le même corps. C'est le même piège qu'en Haute-Loire, où l'endpoint ignorait déjà le
numéro passé en fin d'URL — **c'est la FICHE qui désigne le volume.**

`infosImage` déclare un profil **IIIF Image API 2 niveau 2** et un ark (`naan 71821`). Comme
`?size=full` rend déjà le master en une requête, **le tuilage n'a pas été exploré et n'a rien à
apporter.**

### Deux pièges qui ne sont pas ceux du portail

**LE MAGASIN TLS DE WINDOWS FAIT ÉCHOUER PYTHON, ET LE SITE N'Y EST POUR RIEN.** Le certificat
remonte à **« ISRG Root YE »**, racine Let's Encrypt de mai 2026 que le magasin système ne
connaît pas encore : Python lève « certificate has expired » alors que le certificat court
jusqu'au 1er novembre 2026 et que la chaîne servie se vérifie (`openssl` rend
`Verify return code: 0`). **Passer `cafile=certifi.where()`** — et ne pas désactiver la
vérification, ni noter ça comme une panne du site. Une demi-heure a été perdue à croire le
portail cassé.

**ET LES IMAGES SONT ASSEZ GROSSES POUR FAIRE TOMBER LA CHAÎNE DE LECTURE.** 5496 × 3896, c'est
**2,4 fois la surface d'une vue de l'AD42**. `numpy` a levé un `_ArrayMemoryError` sur un
`np.percentile`, qui recopie le tableau à plat — 20 Mio par appel. Ça n'est arrivé qu'une fois,
sur un poste chargé, mais **c'est le premier portail du dossier où la taille des vues est
elle-même un sujet.**

### LE CADRAGE — `NAS_CROP=auto` À BREIL ET À MEIGNÉ, **RIEN À MÉON**

**LE FOND DE SCANNER N'EST PAS UNE PROPRIÉTÉ DU PORTAIL, C'EST UNE PROPRIÉTÉ DE LA CAMPAGNE
DE NUMÉRISATION.** Cette fiche a annoncé pendant vingt-quatre heures que « lire l'AD49 demande
`NAS_CROP=auto` » : c'est vrai de Breil et de Meigné-le-Vicomte, dont le registre est posé sur
du **blanc**. **Le BMS 1668-1736 de Méon est posé sur du NOIR** — `papier()`, qui cherche la
zone claire, y fait exactement ce qu'il faut, et `NAS_CROP=auto` y **coupe le bord droit du
texte** en prenant le feuillet pour une reliure. Vérifié le 28 août 2026 sur la vue 10, où
l'acte du 8 novembre 1668 perdait ses fins de lignes.

**Le réflexe qui coûte vingt secondes et qui vaut pour tout nouveau registre : rendre UNE vue,
la regarder, puis décider.** Un cadrage raté ne se signale pas — le texte reste lisible, il est
seulement amputé ou noyé.

**Lire Breil et Meigné demande une variable d'environnement, et une seule :**

```bash
NAS_CROP=auto python nas.py "49/breil" 71 72          # rendre
NAS_CROP=auto python nas.py t "49/breil" 66 78 c.png  # cadrer sans lire
```

`volume()` dans `nas.py` cherche alors **la reliure**, qui est sombre, **après avoir ignoré 4 % de
marge extérieure** — c'est tout le secret, et c'est ce qui manquait à trois tentatives : le scan
porte un **liseré noir sur son pourtour**, si bien qu'une recherche de pixels sombres part du bord
et rend la vue entière. Mesuré sur les 85 vues de Breil : **x 0,233-0,799, y 0,230-0,758, stable à
1 % près**. On peut aussi passer les fractions à la main, `NAS_CROP=0.23,0.23,0.80,0.76`.

**Elle ne s'allume que sur demande**, et c'est délibéré : sans la variable, rien ne change pour les
111 registres déjà sur le NAS, dont les fractions de zoom notées dans le corpus et les découpes
d'actes publiées dépendent du cadrage actuel. **Le jour où l'on saura décider tout seul du sens du
fond, elle deviendra automatique.**

### Pourquoi il a fallu ça, et les deux impasses à ne pas rouvrir

**Ce portail photographie le registre au milieu d'un très grand fond BLANC** : le volume
n'occupe que ~45 % de la largeur et ~52 % de la hauteur, et un liseré noir court sur tout le
pourtour du scan. Nos deux détecteurs échouent, chacun à sa façon :

- **`papier()` ne connaît que le fond SOMBRE.** Elle a été écrite pour l'AD67, où le fond noir
  fait 25 % de la surface, et elle cherche donc *la zone claire, c'est le papier*. Ici **le fond
  est plus clair que le papier du registre** : tout est « clair », elle n'ôte que le liseré.
- **`boite()` retient toute la page.** Elle prend le premier et le dernier index qui dépassent
  son seuil ; l'ombre du bord suffit. **Monter le seuil de 0,010 à 0,050 n'y change rien** —
  vérifié sur quatre vues, la boîte reste à 100 %.

**Résultat : la demi-page rendue est lisible mais dépense les trois quarts de ses 1990 px à
photographier du vide.**

**Deux réparations ont été tentées le 27 août et REJETÉES, il ne faut pas les refaire :**

1. **Détecter le feuillet par la TEXTURE** (un fond de scanner est uniforme, un feuillet écrit
   ne l'est pas), en écart-type par blocs de 24 px. Élégant, et **il perd 80 % de l'image sur
   `AD37 - Courcelles / N 1906-1922`** — 19,5 % de surface retenue, du texte coupé. Testé sur
   les 111 registres du NAS.
2. **Ajouter la branche symétrique** — fond clair, feuillet sombre — décidée par l'écart de
   luminosité entre bords et centre. **L'écart est du mauvais signe** : le centre de la vue est
   majoritairement du fond, pas du feuillet, donc il mesure −8,8 au lieu de +8.

**LE CONTOURNEMENT MARCHE ET IL EST BON** — le zoom par fractions, qui ne dépend d'aucune
détection :

```bash
python nas.py z "49/breil" 2 G 0.24 0.79 sortie.png 0.42 1.0
```

Il rend 1570 × 2073 px de texte plein cadre, parfaitement lisible. **Les fractions dépendent de
la mise en page du scan, pas de la vue** : les relever une fois par registre, puis les réutiliser.

*Pourquoi on n'a pas corrigé le moteur : les fractions de zoom déjà notées dans le corpus, et les
découpes d'actes déjà publiées, sont relatives au cadrage actuel. Le déplacer les déplacerait
toutes. Le chantier est réel, il est dans `open-questions.md`, et il se traite en une passe
dédiée avec un test de non-régression sur les 111 registres — pas au fil de l'eau.*

### Deux choses apprises sur le registre de Méon, et elles valent ailleurs

**CHAQUE ANNÉE OUVRE PAR SA PAGE DE TITRE IMPRIMÉE**, et c'est une carte vue↔année gratuite :
« REGISTRE POUR LES BAPTEMES, MARIAGES & Sépultures de la Paroisse de Méon pour l'Année 1697,
contenant douze feuillets ». Une planche de têtes (`nas.py t`, quatre vues, `part` 0,16) la
trouve sans lire une seule page entière, **et le nombre de feuillets annoncé dit d'avance
combien de vues l'année occupe**. Chercher cette page avant tout balayage : c'est l'équivalent
d'Ancien Régime de la table annuelle.

**ET LE BALAYAGE DES MARGES N'Y SERT À RIEN.** Le curé Rabier n'écrit aucune mention de marge
entre 1668 et 1736 : `nas.py m` ne rend que la reliure et le bord déchiré. Testé sur v128-135
le 28 août 2026. **La marge est une convention de scribe, pas une propriété des registres** —
Meigné-le-Vicomte, à six kilomètres, porte les patronymes en marge à la même époque.

### Les registres qui attendent

**Breil** (24 registres), **Auverse** (27), **Meigné-le-Vicomte** (18), **Méon** (10),
Chigné (13), Genneteil (20). Les fiches de référentiel sont dans `portails.json`, clé `49`,
`communes_du_dossier` — **et « Méon » ne se cherche pas en tapant `meon` : le filtre `communes`
ne gère pas les accents, chercher `éon`.**

Déjà sur le NAS :

| Registre | Vues | idArkoFile | fiche |
|---|---|---|---|
| `AD49 - Breil/BMS 1773-1782` | 85 | `76458` | `arko_fiche_6822ebd0d7fd4` |
| `AD49 - Meigne-le-Vicomte/BMS 1713-1752` | 345 (330 tirées) | `74036` | `arko_fiche_6822eb5e9bbc1` |
| `AD49 - Meigne-le-Vicomte/BMS 1753-1782` | 274 (93 tirées) | `74039` | `arko_fiche_6822eb5e9eb84` |
| **`AD49 - Meigne-le-Vicomte/BMS 1659-1712`** | **389** | `74035` | `arko_fiche_6822eb5e990b5` |
| **`AD49 - Meon/BMS 1668-1736`** | **421** | `74041` | `arko_fiche_6822eb5ea6502` |

*Méon a dix registres et **aucun doublon départemental avant 1792** : le BMS 1620-1667
(`79103`, 172 vues) et le BMS 1737-1792 (`74042`, 464 vues) encadrent celui-ci, et il n'y a
pas de seconde plume à consulter pour ces années-là.*

---

## Geneanet — **ne pas automatiser, demander au généalogiste**

Testé le 28 août 2026, pour chercher la sépulture de Charlotte MABON. **`WebFetch` reçoit un 403
sec.** Un vrai Chrome fenêtré passe **une fois** — le premier appel a rendu HTTP 200 et montré
qu'il existe plusieurs « MABON Charlotte » dans les bases — puis **Cloudflare marque le profil et
sert « Un instant… » indéfiniment** : soixante secondes d'attente n'y ont rien changé, là où
l'Anubis du Bas-Rhin cède en une dizaine.

**ET CE N'EST PAS L'AUTOMATISATION QUI DÉCLENCHE ÇA — LE DIAGNOSTIC ÉTAIT FAUX ET PASCAL L'A
CORRIGÉ DANS LA MINUTE.** La fiche a d'abord dit « Cloudflare marque le profil », en supposant que
le Chrome piloté s'était fait repérer. Or le généalogiste, **dans son propre navigateur, en cliquant
lui-même**, s'est vu redemander la vérification humaine **cinq fois de suite**. Le mur n'est donc
pas dressé contre les robots : il l'est contre tout le monde, ce jour-là, depuis cette connexion.

**La leçon est celle du certificat TLS de l'AD49** : quand un accès échoue, se demander d'abord si
le problème est bien là où on le croit. Ici, s'acharner sur le pilotage n'aurait rien donné —
c'était le site qui était fermé, pas notre façon de frapper.

**On n'insiste pas non plus pour une autre raison** : c'est un site commercial dont les résultats
détaillés demandent un compte, et forcer une protection anti-robot n'est ni fiable ni correct.
**Réessayer plus tard** est le premier réflexe, la protection étant vraisemblablement temporaire.

**LA BONNE MANŒUVRE EST DE PASSER LA MAIN.** le généalogiste a un compte, et sa recherche manuelle prend
trente secondes là où l'automatisation échoue — c'est déjà lui qui avait trouvé l'arbre de Hugues
MAURICE et le formulaire des matricules de l'AD37. **Lui donner la requête toute faite** plutôt
que de s'acharner :

> `geneanet.org` → Rechercher → nom `MABON`, prénom `Charlotte`, période 1690-1780, lieu
> Maine-et-Loire. Ce qu'on veut : **une sépulture ou un décès avant 1774**, avec sa paroisse.

*Et se souvenir de la règle : un index n'est pas un fonds. Un zéro sur Geneanet ne prouve rien —
c'est le seul endroit où l'absence ne se note même pas comme un négatif.*

---

## 🇮🇹 Portale Antenati — l'Italie · moteur **WordPress maison**

Portail : <https://antenati.cultura.gov.it/> · ouvert le 27 août 2026

**CE CARNET N'EST PLUS TOUT À FAIT FRANÇAIS, ET C'EST VOULU.** La skill s'appelle
`archives-fr` parce qu'elle est née sur la Loire et la Haute-Loire, mais **sa méthode ne dépend
d'aucun pays** : identifier le moteur, lire la réponse en entier avant de deviner une URL, ne
jamais reconstruire un libellé de commune, recompter contre le total annoncé, noter le négatif.
Toutes ont resservi telles quelles ici. Seul le nom de la skill est étroit ; on ne le change pas
au fil de l'eau, parce que `/archives-fr` est la commande qui se tape.

| | |
|---|---|
| **Emprise** | Tout l'état civil numérisé des *Archivi di Stato* italiens |
| **Moteur** | WordPress ordinaire. Résultats **rendus côté serveur**, dans le HTML |
| **Navigateur** | **OUI, un vrai Chrome fenêtré** — `moteurs/antenati.js`. Voir ci-dessous |
| **Préfixe ark** | **`ark:/12657/`**, forme `an_uaNNNNNN` |
| **Image** | IIIF Presentation **2.0**, sur un domaine à part |
| **Compte** | aucun |

### ⚠️ CE PORTAIL BANNIT LES REQUÊTES NUES — ET LA SKILL LE DISAIT DÉJÀ

**C'est la faute la plus chère du 27 août 2026, et elle a consisté à ne pas lire sa propre
première règle.** Le portail a été ouvert avec `urllib` + un User-Agent de Chrome, sur la foi
d'une note du matin : « c'est un WordPress ordinaire, les résultats sont dans le HTML, pas
besoin de navigateur ». **Trois requêtes coup sur coup et tout le domaine s'est fermé** — la
racine, `robots.txt`, `/suggest/`, les images, et jusqu'au domaine `dam-antenati` : 403
`awselb/2.0` pendant des heures, **depuis n'importe quelle machine**, y compris `WebFetch`
depuis les États-Unis. On a cru à un blocage d'IP, à un problème de TLS, à une panne du site.

La réparation d'alors fut pire que le mal : une cadence de 2,5 s et un repli de 30/90/240 s,
consignés comme *la méthode*. **le généalogiste, en le lisant : « si ta méthode conduit à un
bannissement du site, c'est de la merde, qu'on ne va pas mettre en skill. »** Il a raison, et
la règle était écrite en tête du carnet depuis la Loire : **UN VRAI CHROME FENÊTRÉ, JAMAIS
`curl` NI LE *HEADLESS SHELL***.

**LE NAVIGATEUR PASSE LÀ OÙ `urllib` ÉCHOUE** : `antenati.js` a sorti le manifeste du registre
des morts de 1813 **du premier coup, pendant que le bannissement d'`urllib` courait encore**.
Un vrai Chrome porte le cookie de session que l'ALB pose, charge les assets et envoie un
référent cohérent. **Rien n'est masqué** : `navigator.webdriver` reste à `true`.

**MAIS IL SE FAIT BANNIR EXACTEMENT PAREIL SUR LE VOLUME, ET JE L'AI ÉCRIT FAUX AVANT DE LE
VÉRIFIER.** Cette fiche a affirmé pendant vingt minutes qu'« un vrai navigateur ne se fait pas
bannir par ce genre de limiteur ». **Trente-trois navigations d'image en trente-cinq secondes,
depuis le Chrome fenêtré, et tout le domaine s'est refermé** — la page d'accueil elle-même
rendait « 403 Forbidden » dans la fenêtre, capture d'écran à l'appui. La deuxième affirmation
était aussi fausse que la première, et pour la même raison : **écrite avant d'être testée.**

> **CE QUI EST VRAI, ET C'EST TOUT CE QU'ON SAIT : le limiteur compte le VOLUME, pas le type de
> client.** Un navigateur ne l'exonère de rien. La seule méthode qui tienne sur ce portail est
> donc **chirurgicale** : l'index d'abord, l'acte ensuite, **deux ou trois vues, jamais un
> registre entier**. C'est de toute façon la bonne pratique — la même que « chercher la table
> annuelle avant de balayer les marges ».

**ET QUAND C'EST FERMÉ, ON S'ARRÊTE.** Chaque tentative supplémentaire creuse le trou : les
soixante-six requêtes d'image refusées de l'après-midi du 27 août ont prolongé le bannissement
et l'ont étendu du domaine des images à celui des pages. *Le registre des morts de 1813 n'a
donc pas été tiré ce jour-là — son inventaire seul est acquis.*

**COMBIEN DE TEMPS ÇA DURE : ON NE SAIT PAS, ET IL FAUT LE DIRE COMME ÇA.** Une seule mesure
propre le 27 août — **environ 45 minutes** entre le premier bannissement et le retour du 200.
Le second a tenu **plus d'une heure** et n'était pas retombé en fin de session. Les règles
*rate-based* d'AWS WAF se configurent avec un blocage à durée fixe qui peut aller jusqu'à
plusieurs heures ; on ne voit pas le réglage de l'extérieur. **Ce qui est sûr, c'est que
relancer recharge le compteur** — donc la seule stratégie qui marche est d'arrêter pour de bon
et de revenir le lendemain.

**ET LE TEST « EST-CE NOUS OU EST-CE LE SITE ? » NE MARCHE PAS ICI** : `WebFetch`, qui part
d'une IP américaine, reçoit 403 **en permanence**, bannissement ou pas — le portail refuse
aussi les IP de datacenter. Il ne peut donc pas servir de témoin. *Pour savoir si le site est
debout, il n'y a que le navigateur de la maison.*

**LE VPN N'EST PAS LA RÉPONSE, ET PAS SEULEMENT POUR LA FORME.** Changer d'IP marcherait sans
doute, mais c'est contourner une protection posée exprès par une archive publique ; les IP de
sortie des VPN grand public sont souvent déjà bloquées par ce même WAF ; et un contournement
repéré se paie plus cher que l'attente. **Surtout : le besoin réel est de trois vues, pas de
trente-trois.** Un portail qui limite dit quelque chose de vrai sur la façon dont on l'utilise.

**CE QUI EST LÉGITIME, EN REVANCHE, C'EST DE L'OUVRIR SOI-MÊME.** Le limiteur vise le trafic
scripté ; une personne qui feuillette la visionneuse est exactement l'usage prévu. Quand le
dossier est bloqué, **donner au généalogiste l'URL du registre et le numéro d'acte** vaut mieux que
n'importe quel contournement : `https://antenati.cultura.gov.it/ark:/12657/<ark>/`.

### LE GARDE-FOU — parce qu'une consigne en commentaire ne suffit pas

**Tout ce qui précède était déjà écrit, en majuscules, et n'a rien empêché.** Le module a
envoyé **99 requêtes en une heure**, dont 66 refusées qu'il a continué d'envoyer, et l'IP de la
maison s'est retrouvée bloquée — le généalogiste ne pouvait plus ouvrir le site lui-même. *« Tu as
bourriné comme un salaud. »* Une règle qu'on peut ignorer n'est pas une règle : elle est
désormais **dans le code**, elle compte pour de vrai, et elle **survit à la session** — le
journal est sur le disque, dans le profil Chrome.

| Verrou | Effet |
|---|---|
| **Un 403 arrête tout** | quarantaine de **2 h** posée sur le disque ; toute exécution suivante refuse de démarrer |
| **Budget glissant** | **6 requêtes par heure**, tenu entre les exécutions, pas seulement dans une session |
| **Cadence** | **12 s**, plancher |

⚠️ **CETTE FICHE A ANNONCÉ 30 REQUÊTES ET 3 SECONDES JUSQU'AU 12 SEPTEMBRE 2026, ET LE CODE EN
APPLIQUAIT 12 ET 12.** Le carnet mentait sur son propre garde-fou — et c'est le genre d'écart qui
fait qu'on croit avoir de la marge. **Quand la fiche et le code se contredisent, c'est le code qui
fait foi**, et c'est la fiche qu'on corrige.

**ET LE BUDGET EST PASSÉ DE 12 À 6 LE 12 SEPTEMBRE 2026, SUR UNE MESURE.** Une session a fait
quatre requêtes de recherche, puis trois pour un `registre` — et **la huitième, la première qui
demandait une IMAGE, a rendu 403**. Le garde-fou a coupé net, ce pour quoi il existe ; mais il
n'avait rien empêché, puisqu'il autorisait douze.

*Ce qu'on en déduit, et ce qu'on ne sait toujours pas* : les sept premières étaient des **pages**
et sont passées, la première **image** a été refusée. Soit le domaine `dam-antenati` compte à part
et plus serré, soit une image pèse plus qu'une page dans le même compteur. Une seule mesure ne
fait pas une loi — d'où six, la moitié de ce qui a suffi à nous faire fermer. **Un inventaire, un
manifeste et deux vues font quatre requêtes : le budget reste suffisant pour l'usage réel.**

**ET LE DÉPOUILLEUR S'EST CASSÉ EN SILENCE LE MÊME JOUR.** `depouille()` a rendu **soixante lignes
dont tous les champs valaient « ? »** : le portail écrit désormais `Stato civile napoleonico &nbsp;
&gt; &nbsp; Vito d'Asio` là où il mettait un `>` nu, et la regex ne mordait plus. Même défaut que
les deux modules Archinoe de la veille — **rendre des lignes sans dire qu'on ne les comprend pas**.
Deux corrections : les entités se décodent avant lecture, et **le module écrit maintenant le HTML
brut dans `antenati-derniere-recherche.html` et crie quand il n'a pas su dépouiller**. Réparer à
l'aveugle coûtait une requête par essai sur un portail qui en autorise six.

**Les deux premiers coupent AVANT que Chrome s'ouvre** — pas de fenêtre, pas de requête, sortie
en code 2. `node antenati.js etat` dit où on en est. Le budget est large pour l'usage réel :
un inventaire, un manifeste et trois vues font **cinq** requêtes. **Il n'y a aucun scénario
légitime à 99** — si le budget s'épuise, c'est qu'on s'y prend mal.

*Et ce garde-fou vaut d'être copié ailleurs. Aucun autre portail du carnet n'en a, parce
qu'aucun ne nous avait encore fermé la porte au nez.*

```bash
NODE_PATH="<maison>" \
  node scripts/archives/moteurs/antenati.js chercher '"Valvasone Arzene"'   # 88 registres, 1 requête
  node scripts/archives/moteurs/antenati.js registre an_ua750235            # le manifeste, 33 vues
  node scripts/archives/moteurs/antenati.js vue      an_ua750235 12 "<archives>/…"  # UNE vue
```

**`tirer` n'existe pas, et c'est délibéré.** Il a existé une heure, il a fait bannir le
dossier, il est parti.

**LA LEÇON GÉNÉRALE, ET ELLE NE VAUT PAS QUE POUR L'ITALIE.** Un 403 qui apparaît après
quelques requêtes n'est pas un problème d'en-tête. Deux réponses ont été essayées ce jour-là et
**aucune des deux n'est la bonne** : temporiser plus finement (2,5 s, repli 30/90/240) n'a fait
que ralentir la casse, et ouvrir un navigateur n'a déplacé le seuil que de quelques dizaines de
requêtes. **La bonne réponse est de demander moins** — prendre l'inventaire en un appel, lire
l'index, et n'ouvrir que les vues dont on a besoin. Un portail qui limite dit quelque chose de
vrai : on n'a pas besoin des trente-trois vues, on a besoin de l'acte n° 20.

*Le module Python écrit le matin a été supprimé : une recette dupliquée est une recette qui
pourrit, et celle-là était fausse deux fois.*

**On prend quand même le maximum par page** quand c'est gratuit : `s_size=100` rend les
88 registres d'une commune en une seule requête, là où la pagination en demanderait neuf.

### ⛔ → ✅ LE FILTRE PAR COMMUNE : C'ÉTAIT UNE PAIRE DE GUILLEMETS

La fiche du matin disait « **le paramètre `localita` ne filtre RIEN** : `?localita=Valvasone`,
`Arzene` et `Valvasone Arzene` rendent exactement les mêmes 10 résultats ». Le constat était
exact ; la conclusion — « c'est le piège de l'AD42, un autocomplete qui pose un identifiant
ailleurs dans la requête » — était fausse. **Il n'y a aucun identifiant caché.** Le champ fait
une recherche en **texte libre**, qui matche tout ; l'autocomplete, lui, **entoure la valeur de
guillemets**, et c'est ça, le filtre. C'est écrit en clair dans le JS de la page de recherche :

    localita.addEventListener("selection", function (event) {
      localita.value = '"' + event.detail.selection.value.trim() + '"';   // <-- LE FILTRE
    });

```
sans guillemets : ?localita=Valvasone Arzene                     -> « Pagina 1 di 1 », 10 lignes fausses
avec guillemets : ?localita="Valvasone Arzene"                   -> « Pagina 1 di 9 », 88 registres
                  ?localita="Valvasone Arzene"&s_size=100        -> les 88 en UNE requête
```

**Le moteur ne dit jamais qu'il n'a pas filtré** : il rend dix lignes plausibles dans les deux
cas. C'est la cinquième recherche négative fausse que ce dossier paie, et la première dont la
cause soit une ponctuation.

### Le vocabulaire des communes se LIT — il y a un endpoint pour ça

```
/suggest/?campo=localita&localita=Valvason&tipologia=      ->  ["Valvasone Arzene"]
/suggest/?campo=tipologia&tipologia=Mor&localita=          ->  les typologies
```

Trois caractères minimum. **« Valvasone » seul n'existe pas dans le vocabulaire** : la commune a
fusionné avec Arzene en 2015 et le portail n'indexe que le nom moderne. Chercher sous l'ancien
rend zéro, et zéro ne veut pas dire absent — la leçon des graphies, appliquée cette fois à une
fusion de communes.

### LE PIÈGE DE TOPONYMIE, ET IL EST L'INVERSE DU PRÉCÉDENT

Le nom moderne ramène **trois communes historiques distinctes**. Relevé le 27 août 2026 :

| Contexte archivistique | Registres |
|---|---|
| **Valvasone** (ora in provincia di Pordenone) | **58** |
| **Arzene** (ora in provincia di Pordenone) | 15 |
| **San Lorenzo** (oggi frazione di Arzene) | 15 |

**Un registre rendu par une recherche « Valvasone Arzene » a deux chances sur cinq de ne pas
être celui de Valvasone.** Le champ `Contesto archivistico` du manifeste, et la ligne du tableau
de résultats, le disent à chaque fois. **Le lire systématiquement.**

**ET LA PROVINCE AFFICHÉE EST CELLE D'AUJOURD'HUI, PAS CELLE DES ACTES** : « ora in provincia di
Pordenone » — *aujourd'hui*. Valvasone relevait d'**UDINE** jusqu'en 1968, et c'est
l'**Archivio di Stato di Udine** qui tient ses registres. Chercher à Pordenone, c'est chercher
au mauvais endroit ; la fiche de `ou-chercher.md` l'a dit faux pendant deux semaines.

### La recherche

```
/search-registry/?localita="<commune>"&tipologia=<Nati|Morti|Matrimoni|Diversi>
                 &anno=<année>&s_size=<10|20|50|100>&s_page=<n>
```

Les résultats portent, **dans le HTML rendu côté serveur** : l'**ark**, l'**année**, la
**typologie**, la **cote** (*Segnatura attuale*), le **contexte archivistique** et l'archive
dépositaire. Il n'y a donc pas à ouvrir les fiches pour dresser l'inventaire d'une commune.

`s_size` est une **liste fermée** — 10, 20, 50, 100. Le total s'affiche en toutes lettres,
« Pagina 1 di 9 » : **recompter contre lui**, comme partout ailleurs.

### Les images

1. La page du registre est `{base}/ark:/12657/{ark}/` — **le slash final compte**, sans lui 301.
2. Elle contient **une seule URL utile** :
   `https://dam-antenati.cultura.gov.it/antenati/containers/<id>/manifest`
3. Le manifeste est du **IIIF Presentation 2.0** et porte tout : nombre de vues, labels,
   typologie, datation, contexte archivistique complet, et un service **IIIF Image API** par vue
   sur `https://iiif-antenati.cultura.gov.it/iiif/2/<id>`.
4. La vue : `{service}/full/full/0/default.jpg`.

*`dam-antenati.../containers/` en racine rend 403 : c'est normal, il faut un container précis.*

### Ce que ce fonds couvre, et le trou qu'il ne couvre pas

**DEUX FENÊTRES, ET ELLES NE SE TOUCHENT PAS** : l'**état civil napoléonien 1806-1815**, puis
l'**état civil italien à partir de 1871**. **Entre les deux, rien** — la Vénétie est
autrichienne, il n'y a pas d'état civil, ce sont les **registres paroissiaux** qui font foi et
ils sont à l'**archive diocésaine** (Concordia-Pordenone pour le Frioul occidental), sur demande
d'admission, **rien en ligne**.

**ET POUR VALVASONE, SEULE LA PREMIÈRE FENÊTRE EST NUMÉRISÉE** : les 88 registres rendus le
27 août 2026 sont **tous** du `Stato civile napoleonico`. Aucun post-1871.

**CLAUZETTO, MESURÉ LE 18 SEPTEMBRE 2026 : PAREIL.** Soixante-cinq registres, 1806 à 1815, plus
trois index 1806-1810 — *Nati*, *Morti*, *Matrimoni*, leurs index, les *pubblicazioni* et les
*allegati*. **Rien après 1815.** Deux communes du Frioul occidental, deux fois le même verdict :
pour l'état civil postérieur à 1871 de ce coin-là, **ce portail n'est pas la porte** — c'est le
fonds du *tribunale* de Pordenone, microfilmé par FamilySearch, ou le comune.
*Une requête sur les six de l'heure, et une piste fermée au lieu d'être devinée.* Ça ne prouve pas
qu'ils n'existent pas — mais **une recherche sur cette commune ne les rend pas**, et il faut
donc s'adresser au **comune de Valvasone Arzene** pour tout ce qui est postérieur à 1871.

**Les années présentes pour Valvasone** : 1806, 1807, 1808, puis 1810 à 1815 — **pas de 1809**,
dont les actes tombent dans un registre voisin ou dans l'**index 1806-1810**, qui, lui, existe.
*Une année absente du catalogue n'est pas une année perdue : chercher l'index.*

**LES INDEX SONT LA MEILLEURE PORTE**, et ils sont catalogués **comme des registres à part**
(*Nati, indice* · *Morti, indice* · *Matrimoni, indice*), certains couvrant cinq ans d'un coup.
C'est l'équivalent italien de la table décennale — **chercher l'index avant de feuilleter**.

**ET LES *ALLEGATI* SONT UN FONDS À PART ENTIÈRE** : les pièces annexes d'un mariage
napoléonien — extraits de baptême des époux, actes de décès des parents, consentements. C'est là
que se trouvent recopiées les dates prises sur les registres paroissiaux d'Ancien Régime, donc
**un pont par-dessus 1806 vers l'avant**. Un *Matrimoni, allegati* vaut souvent mieux que l'acte
de mariage lui-même — c'est la version italienne de « un mariage vaut trois baptêmes ».

### Ce qui reste à faire sur ce portail

- **La recherche nominative** (`?nominativi=true`, champs `nome` / `cognome`) n'a pas été
  essayée. Une partie du fonds est indexée par des bénévoles : comme l'indexation collaborative
  de l'AD42, **une absence n'y prouve rien**.
- **Les autres archives** : le portail sert une centaine d'*Archivi di Stato*. Le paramètre
  `archivio` (numérique — Udine est `166`) et `fondo` apparaissent dans les URL indexées par les
  moteurs de recherche, mais n'ont pas été testés.

---

## AD79 + AD86 — Deux-Sèvres et Vienne, **portail commun** · moteur **Boscop / Ligeo**

**Ouvert le 29 août 2026**, en une soirée, pour la famille de Jean DURAND. Le moteur était déjà
écrit — c'est celui de l'AD42 — mais **la pose des critères y est différente**, et c'est là que
tout le temps est passé.

| | |
|---|---|
| Base | `https://archives-deux-sevres-vienne.fr` |
| Module | `scripts/archives/moteurs/boscop_7986.js` — `communes` · `registres` · `manifeste` · `tirer` |
| Page de recherche | `/archive/recherche/ecalternatif/n:100` |
| Index Solr | `ad7986diffusion_exploit_etatcivil` |
| Images | **IIIF**, `{base}/ark:/{ark}/manifest`, puis `{service}/full/full/0/native.jpg` |
| Compte | non — **sauf** pour les actes de 1913 à 1952, voir plus bas |

### Les trois pièges, et le deuxième est le plus cher

**1. Le slug et le type ne sont pas le même mot.** L'URL de recherche dit `ecalternatif`, le
`type` interne dit `etatcivil`, et les deux se croisent dans les URL de résultats :
`/archive/resultats/**etatcivil**/registres/n:100/…?…&type=etatcivil`, atteint depuis
`/archive/recherche/**ecalternatif**/n:100`.

**2. REMPLIR LE CHAMP TEXTE DE LA COMMUNE NE FILTRE RIEN.** Le formulaire a bien un
`#ArchivesRECHCommune`, on peut y écrire « Lavausseau (Vienne, France) » — le libellé exact — et
soumettre : le moteur **rend les 43 017 registres des deux départements**, triés par date
croissante. Vingt lignes de registres paroissiaux du XVIᵉ siècle s'affichent, et **ça ressemble
parfaitement à un résultat de commune**. Ce que le moteur lit, ce sont les deux champs cachés :

```
RECH_commune_Libel = "Lavausseau (Vienne, France)|"
RECH_commune_Md5   = "98b398117c6932df3d418b88c0548526|"
```

C'est la variante Ligeo du « paramètre inventé ignoré en silence ». **Toujours recompter contre
le total annoncé**, qui se lit ici « *N réponses dans M inventaires* ».

**3. Le md5 se demande à la facette, qui exige un jeton.** `/arcfacette.php`, avec
`ind=ad7986diffusion_exploit_etatcivil`, `id=RECH_commune&autoc=1` et le `token=` que porte le
HTML de la page de recherche. La réponse est du JavaScript ; les valeurs sont dans des
`<button class="facette-select-rech_commune" value="…" data-md5="…">`.

*Le `.ui-autocomplete` ne se remplit jamais : inutile de piloter la frappe au clavier, on
interroge `arcfacette.php` directement depuis le contexte de la page.*

**Pagination** : `/limit:25` est le maximum offert (5, 10, 15, 20, 25) et `/page:N` suit — les
deux dans le chemin, pas dans la requête. `/page:N` **sans** les `_Libel` / `_Md5` rend une page
vide, pas une erreur.

**WAF** : une requête nue rend `Access Denied: error code …`. Un vrai Chrome fenêtré passe, rien
à masquer.

### Ce qu'il faut savoir du fonds avant de conclure à une lacune

**UNE COMMUNE JEUNE N'A PAS D'ÉTAT CIVIL ANCIEN, ET CE N'EST PAS UNE LACUNE DE NUMÉRISATION.**
Lavausseau ne rend que 31 registres, **tous postérieurs à 1869**, quand Benassay en rend 45 depuis
1823. Ce n'est pas un fonds incomplet : **Lavausseau a été créée le 11 juillet 1868 par
démembrement de Benassay.** Tout ce qui s'y est passé avant est aux registres de Benassay. Le
réflexe à prendre — le même que « vérifier comment *ce* scribe-là écrit le mot cherché » — est de
**vérifier la date de création de la commune** avant de déclarer un trou.

De même, l'**arrêt à 1922** n'est pas la fin du fonds : les registres de 1923 à 1952 existent et
sont numérisés, ils ne sont simplement pas publiés en accès libre.

### La salle de lecture virtuelle — le vrai levier pour le XXᵉ siècle

Le portail offre, **sur inscription et depuis chez soi**, l'accès aux documents que le délai légal
interdit de publier :

- **actes d'état civil de 1913 à 1952**, quand ils sont numérisés ;
- **recensements de 1954 à 1975** ;
- **registres matricules de 1922 à 1940**.

C'est ce qu'il faut ouvrir le jour où une naissance d'après 1922 manque — et c'est le cas de celle
de Jean DURAND, né en 1943, introuvable dans les tables décennales des deux communes où sa famille
vivait.

### Communes déjà interrogées

| Libellé exact (celui de la facette) | md5 | Registres |
|---|---|---|
| `Lavausseau (Vienne, France)` | `98b398117c6932df3d418b88c0548526` | 31, de 1869 à 1952 |
| `Benassay (Vienne, France)` | *(à redemander)* | 45, de 1823 à 1952 |

Tirés sur le NAS : `AD86 - Benassay/N 1903-1912`, `M 1893-1902`, `M 1903-1912`, `TD 1873-1902`,
`TD 1903-1912`, `TD 1933-1942`, `TD 1943-1952` · `AD86 - Lavausseau/N 1883-1892`, `N 1913-1922`,
`M 1913-1922`, `TD 1943-1952`.

### La panne du 29 août 2026 au soir, et comment la reconnaître

Le portail est tombé en pleine séance. Le symptôme est net et il ne ressemble à rien d'autre :
**toute URL rend une page « Erreur système (code : 256) »** avec un identifiant de rapport
d'erreur, y compris le manifeste IIIF d'un registre tiré une heure plus tôt sans incident.

```
Erreur système (code : 256)
Une erreur système est survenue durant le traitement de la page.
Un rapport d'erreur a été transmis à l'administrateur de la plateforme.
```

**Le test qui tranche en une commande** : redemander le manifeste d'un ark qu'on a DÉJÀ tiré.
S'il échoue, c'est le serveur ; s'il passe, c'est l'ark.

```bash
node boscop_7986.js manifeste 28387/vtac6113fdf4525e9f4   # Benassay, N 1903-1912
```

**Ce que ça n'est pas** : un ark périmé, une commune absente du fonds, un registre non numérisé.
La règle de la skill vaut ici mot pour mot — *une erreur réseau n'est pas un négatif* — et le
piège serait d'écrire « le registre des décès 1823-1833 de Benassay n'est pas en ligne » dans
`open-questions.md`, ce qui enverrait la session suivante chercher ailleurs pour rien.

Un autre signe, plus discret et donc plus dangereux : la commande `registres` rend
**« total annoncé : null — lignes récupérées : 0 »**. Zéro ligne sans total, ce n'est pas une
commune vide : le moteur de recherche est tombé aussi, et la facette a bien rendu son md5 avant
lui. **Un total à `null` invalide le résultat**, il ne le confirme pas.

---

## 🇦🇹 MATRICULA ONLINE — les registres paroissiaux d'Europe centrale, et pourquoi ils ne servent pas le Frioul

Portail : <https://data.matricula-online.eu/en/> · reconnu et **fermé** le 20 septembre 2026.

**Registres paroissiaux numérisés d'Autriche, d'Allemagne, du Luxembourg, de Pologne, de Serbie
et de Slovénie.** Aucun compte, pas de WAF, une application Django ordinaire.

### ⭐ LA ROUTE DE RECHERCHE EST UN GET, ET ELLE N'EST PAS SUR L'ACCUEIL

C'est ce qui avait fait échouer la première reconnaissance, le matin même : la page d'accueil ne
porte **aucun formulaire**, et on en avait conclu qu'on ne savait pas chercher. Le moteur est
derrière l'entrée « Search for Places » du menu :

```
/en/suchen/?place=<lieu>
```

Réponse en HTML ; les résultats sont des liens `/en/<pays>/<diocèse>/<paroisse>/` et la page
annonce « N hits ».

⚠️ **Le contrôle du vide, parce qu'une page sans résultat ne le dit pas clairement** : une
requête absurde (`?place=zzzzqqq`) rend **13 725 octets**. Toute réponse de cette taille est un
zéro. Comparer, ne pas chercher une phrase.

### ⛔ L'ITALIE Y EST ANNONCÉE, ET ELLE SE RÉDUIT À DEUX CHOSES

| ce que la page d'accueil promet | ce qu'il y a vraiment |
|---|---|
| « Autriche, Allemagne, **Italie**, Luxembourg, Pologne, Serbie, Slovénie » | **Reggio Calabria**, 105 paroisses · **Südtirol, diocèse de Bozen-Brixen**, 1 entrée — et cette entrée n'est **pas un fonds**, c'est un renvoi vers le site propre du diocèse (« stehen in einem eigenen Webangebot zur Verfügung ») |

**Recherches faites, toutes à zéro** : `Valvasone`, `Pordenone`, `Friuli`.

⚠️ **`Udine` rend UNE réponse, et c'est un faux ami** : **Kanaltal, Uggowitz** — l'ancien Val
Canale autrichien près de Tarvisio, rattaché à l'Italie en 1919. Cent kilomètres de Valvasone,
et un autre monde administratif : c'est de la Carinthie, pas du Frioul vénitien. Fonds privé,
*Archiv Delussu*. **Une province n'est pas un diocèse.**

### ⛔ CE QUE ÇA VEUT DIRE POUR LE DOSSIER

**Ni le diocèse de Concordia-Pordenone, ni celui d'Udine.** Les quarante-cinq années de
Valvasone que rien ne couvre — **1816-1871, quand le curé tenait l'état civil sous l'Autriche** —
ne sont pas ici. Le raisonnement qui rendait Matricula séduisant était juste : ces registres
SONT paroissiaux, et leur copie EST dans une curie épiscopale. Mais c'est celle de
Concordia-Pordenone, qui n'a rien mis sur Matricula, et à qui la lettre est écrite.

*Négatif complet. Ne pas le repayer — et si un arbre tiers touche l'Autriche, l'Allemagne ou la
Slovénie, le module est affaire de quelques lignes : GET, HTML, liens.*

---

## 🇩🇪 Arolsen Archives — les travailleurs forcés et les camps · moteur **ASP.NET `.asmx`**

Ce n'est pas de l'état civil : c'est l'ancien *International Tracing Service*, trente millions de
documents sur les déportés, les internés et **les travailleurs étrangers requis en Allemagne
1939-1945**. Gratuit, sans compte. Fiche écrite le 29 août 2026, en cherchant Antonio Pietro
PEDIRODA — sans le trouver.

`collections.arolsen-archives.org` est une application **Angular** : la page ne rend rien sans
JavaScript. Mais l'API répond en JSON, sans authentification, et **la recherche est *stateful* en
trois appels** — on enregistre la requête côté serveur sous un `uniqueId`, puis on la lit.

```bash
API="https://collections-server.arolsen-archives.org/ITS-WS.asmx"
JAR=$(mktemp); ID=$(head -c 300 /dev/urandom | tr -dc 'A-Za-z0-9' | head -c 20)
CURL=(curl -s -b "$JAR" -c "$JAR" -H "Content-Type: application/json"
      -H "Origin: https://collections.arolsen-archives.org")

"${CURL[@]}" -X POST "$API/BuildQueryGlobalForAngular" \
  -d "{\"uniqueId\":\"$ID\",\"lang\":\"en\",\"archiveIds\":[],\"strSearch\":\"Battocletti\",\"synSearch\":true}"
"${CURL[@]}" -X POST "$API/GetCount" \
  -d "{\"uniqueId\":\"$ID\",\"lang\":\"en\",\"searchType\":\"person\",\"useFilter\":false}"
"${CURL[@]}" -X POST "$API/GetPersonList" \
  -d "{\"uniqueId\":\"$ID\",\"lang\":\"en\",\"rowNum\":0,\"orderBy\":\"LastName\",\"orderType\":\"asc\"}"
```

Une fiche rend `LastName`, `FirstName`, `MaidenName`, `PlaceBirth`, `Dob`, `Father`, `Mother`,
`Nationality`, `Occupaton` *(sic, dans leur schéma)*, `Place_of_incarceration`, `Date_of_decease`,
`Signature` (le fonds), `DescId`, `ObjId`. `GetIdbyUrlId` avec `{"id":"2-2"}` rend l'identifiant
numérique d'un fonds, à passer dans `archiveIds` — **un tableau, jamais une chaîne**.

**QUATRE PIÈGES, TOUS PAYÉS LE MÊME JOUR.**

1. **Le cookie de session est obligatoire.** Sans `-b/-c`, `BuildQuery` répond `{"d":true}` — donc
   l'air d'avoir marché — puis `GetCount` rend **33 708 576**, le total de l'archive. La requête
   vit dans la session ASP.NET ; sans elle, chaque appel repart à vide.
2. **`synSearch` doit valoir `true`, toujours.** Avec `false`, *toute* recherche rend 0, y compris
   un `Kowalski` qui en a 31 498. Ce n'est pas un mode « précis », c'est un paramètre mort — et il
   fabrique des négatifs parfaitement crédibles.
3. **`orderBy` ne doit pas être vide**, sinon `GetPersonList` rend `[]` quand `GetCount` annonce
   des dizaines. Valeurs valides : `LastName`, `FirstName`, `sortDob`.
4. **`rowNum` est un décalage**, par pages de 1000.

**ET LA « RECHERCHE PAR SYNONYMES » N'EST PAS FLOUE — c'est ce qui décide de toute la méthode.**

| requête | réponse | | requête | réponse |
|---|---|---|---|---|
| `Battocletti` | 12 | | `Batocleti` | **0** |
| `Vaccher` | 28 | | `Waccher` | **0** |
| `Cherubin` | 107 | | `Kerubin` | **0** |

Une consonne doublée ou changée suffit à tout perdre. **Chaque graphie s'essaie séparément, et un
zéro sur l'une ne dit rien de l'autre** — c'est la règle du patronyme de ce dossier, appliquée à un
moteur. Les jokers **mentent** : `Valvasone` rend 26, `Valvas*` seulement 12. **Un résultat joker
n'est pas un sur-ensemble de l'exact** et ne prouve donc aucune absence.

**CHERCHER PAR LIEU DE NAISSANCE, SANS LE NOM.** C'est le contrôle qui rend un négatif citable :
il prouve que le fonds couvre la commune. `Valvasone` rend 25 personnes et 22 patronymes, tous du
profil recherché — ouvriers civils italiens, fonds 2.1.2.1, 7.5.7, 2.2.2.1, 2.2.2.2. Les dates
sont indexées aussi (`12/12/1906` rend 1 704 fiches), ce qui donne un troisième axe.

**LA LIMITE QUI COMPTE, ET ELLE INVALIDE TOUT NÉGATIF EN LIGNE.** Le fonds **DE ITS 0.1, le
*Central Name Index*** — le fichier central de renvoi que l'ITS consultait lui-même — **n'est pas
interrogeable par nom sur le web** : restreint à ce fonds, `Kowalski` rend 0, `Rossi` rend 0. Ce
n'est pas qu'il est vide, c'est qu'il est hors de portée. **Un négatif en ligne ne vaut donc pas
un négatif d'Arolsen**, et la demande écrite n'est pas une formalité :
`https://arolsenarchives.my.site.com/guest/s/?language=en_US` — Große Allee 5-9, D-34454 Bad
Arolsen. **Délai annoncé : cinq mois en moyenne, jusqu'à treize.**

**Et il existe un second index sur les mêmes documents** : le miroir gratuit d'Ancestry,
`ancestry.com/alwaysremember`, **indexé indépendamment**. Un nom mal saisi d'un côté peut être bon
de l'autre — c'est le premier recours quand Arolsen rend zéro.

*Piège de dépouillement, pas de portail* : ne pas dédoublonner les résultats sur `ObjId`, le même
identifiant réapparaît d'un fonds à l'autre et fait disparaître des personnes. Dédoublonner sur
(nom, prénom, date de naissance).

---

## Toulouse — Archives **MUNICIPALES** · moteur **4D**

**⚠️ CE N'EST PAS L'AD31, ET C'EST LA PREMIÈRE CHOSE À SAVOIR.** Toulouse tient ses propres
Archives municipales ; les AD31 ont l'état civil des *autres* communes du département. Chercher
un Toulousain sur le site du département, c'est chercher dans le mauvais fonds.

> Archives municipales de Toulouse, 2 rue des Archives, 31500 Toulouse · 05 36 25 23 80
> Salle de lecture du lundi au vendredi, 9 h – 13 h · `www.archives.toulouse.fr`
> Base de données : `basededonnees.archives.toulouse.fr`

**⚠️ ET ELLES NE DÉLIVRENT QUE LES ACTES DE PLUS DE CENT ANS.** Réponse écrite des Archives
municipales le 17 septembre 2026, à deux demandes (un mariage de 1939, un décès de 1940) : *« pour
les recherches d'actes de moins de cent ans (de 1926 à 2026), il convient de s'adresser au service
de l'état civil »*. Le dossier avait écrit le contraire — qu'un acte de plus de 75 ans passait par
les Archives — et deux demandes ont été perdues une semaine. **La frontière est cent ans, glissante,
et elle ne suit pas le délai de communicabilité.**

> État civil de Toulouse — Site Duranti, 6 rue du Lieutenant-colonel Pélissier, 31000 Toulouse
> 05 61 22 30 26 · formulaire : `metropole.toulouse.fr/demarches/demander-une-copie-dacte-detat-civil`
> (naissance, mariage, reconnaissance, décès de moins de cent ans — une demande par acte)

Et ce formulaire **renvoie lui-même vers le téléservice national** de demande d'acte d'état civil
(vérifié par le généalogiste le 17 septembre 2026) : c'est par là que la demande part vraiment. Les deux
réponses des Archives — mariage et décès — étaient identiques.

### Le moteur — un sixième, et il est facile

**4D (4th Dimension)**, un serveur applicatif propriétaire. Il se signe dans **toutes** ses URL
par `/4DCGI/` et `/4Daction/`, et son pied de page donne une version (`12.0.4hf1`). Rien à voir
avec Arkothèque, Boscop, Naoned ni Anaphore.

**Bonne nouvelle : il rend du HTML serveur.** Pas de JavaScript à exécuter, pas de jeton, pas de
WAF — un simple `POST` de formulaire passe avec `urllib`, sans navigateur. C'est le portail le
plus simple du carnet.

**Mauvaise nouvelle : il est lent.** Prévoir un `timeout` de 90 s et un réessai ; il rend des
*read timeout* sous charge.

```
formulaire  GET  /4DCGI/Web_ActesRechSimple/ILUMP25828
recherche   POST /4DCGI/WEB_ActesResultRechSimple/ILUMP25828
```

| paramètre | |
|---|---|
| `T` | `indif` · `naissance` · `mariage` · `deces` |
| `wNom3` · `wPrenom` | nom, prénom |
| `wNomEP3` · `wPrenomEP` | nom et prénom d'épouse |
| `wLieuEP` · `wcote` · `wnum` | lieu de rédaction, cote, n° d'acte |
| `wannee` · `wdate` · `wdatedeb` · `wdatefin` | `aaaa` et `jj/mm/aaaa` |
| `warrobase=1` · `btout=Lancer la recherche` | à passer tels quels |

Les champs acceptent `OU` pour une recherche multiple : *« Untel ou Untel »*.
Zéro réponse s'écrit **« Désolé, aucune notice ne correspond à votre recherche ! »**

### ⚠️ LE PIÈGE, ET IL EST ÉNORME : L'INDEX NE COUVRE QUE LES NAISSANCES 1900-1925

**79 359 notices pour tout Toulouse.** C'est minuscule, et il a fallu mesurer le périmètre avant
de croire un seul zéro — parce que la recherche par nom rend « aucune notice » pour un mariage de
1939 exactement comme elle le ferait pour un nom qui n'existe pas.

| requête | |
|---|---|
| années 1900, 1902, 1905, 1910, 1912, 1915, 1920, 1922, 1924, **1925** | des résultats |
| années **1926**, 1927, 1930, 1939 | **rien** |
| 1920 `naissance` | des résultats |
| 1920 `mariage` · 1920 `deces` | **rien** |
| 1750 `mariage` · 1850 `mariage` · année 1875 | **rien** |

**Donc : naissances seules, 1900-1925.** Ni mariages ni décès, à aucune époque ; rien du XIXᵉ
siècle ni des registres paroissiaux. La borne de 1925 est la règle des cent ans : elle glissera
sur 1926 en 2027.

**Conséquence** : chercher un mariage ou un décès par nom sur ce portail rend **toujours** zéro,
quel que soit le nom. Ce n'est pas un négatif, c'est un hors-périmètre — la leçon « un index
n'est pas un fonds », dans sa forme la plus coûteuse, puisque l'outil ne dit rien de ce qu'il
couvre.

**Contrôle positif à faire avant de croire un zéro** : `wNom3=MARTIN`, ou `wannee=1900`. L'un ou
l'autre doit rendre des résultats.

### Les recensements s'arrêtent à 1911

En ligne : **1790-1911**, une soixantaine de milliers de vues. Les listes nominatives de 1921,
1926, 1931 et **1936** sont communicables — soixante-quinze ans — mais **non numérisées** : elles
se consultent en salle, et **on les feuillette PAR RUE, pas par nom**. Il faut donc l'adresse
avant d'y aller, et l'adresse se prend sur un acte. *Ordre à respecter : l'acte d'abord, le
recensement ensuite.*

### Obtenir un acte des années 1930-1950 — deux circuits, et un seul est ouvert

**Le service de l'État civil de la mairie** garde les registres de moins de cent ans et ne délivre
une **copie intégrale** qu'à l'intéressé, à ses ascendants et à ses descendants. **Un collatéral
n'y a pas droit** — une petite-nièce, un arrière-neveu se voient refuser.

**Les Archives municipales** appliquent le Code du patrimoine : **tout acte de plus de
soixante-quinze ans est communicable à quiconque**, sans lien de parenté à justifier. Et elles
font les **recherches par correspondance gratuitement** quand elles tiennent en moins de trente
minutes.

**Pour un acte des années 1930-1950, c'est donc par les Archives qu'il faut passer, jamais par
l'État civil.** La règle vaut partout ailleurs en France.

---

## AD50 — Manche · moteur **Arkothèque**

**Ouvert le 4 septembre 2026**, en une soirée, pour la famille DUPONT — des imprimeurs
venus de Villeneuve-sur-Lot s'installer à Coutances en 1910. Le moteur était déjà écrit ;
tout le temps est parti dans deux pièges, et le second est le plus cher.

| | |
|---|---|
| Base | `https://www.archives-manche.fr` |
| Module | `moteurs/arkotheque.py`, sans navigateur |
| Page de recherche | `/rechercher/registres-paroissiaux-et-detat-civil/rechercher-dans-letat-civil` |
| API | `/_recherche-api/moteur` |
| Images | `/_recherche-images/show/{numérisation}/image/{idArkoFile}/{rang}?size=full` |
| Compte | non |

### 1. IL A L'AIR D'AVOIR UN WAF, ET IL N'EN A PAS

Une requête curl ordinaire rend 214 octets portant
`window.location.href='/redirect_<JETON>/…'`, et **demander ce chemin-là directement rend
« 403 Attack detected »**. On croit tenir l'AD43 ou l'AD45, on sort Playwright, on ouvre un
Chrome fenêtré — et c'était inutile. Le jeton doit être suivi **dans la même session, depuis
l'URL de départ**, ce que fait `_get()` d'`arkotheque.py` depuis toujours. **Ne pas conclure
au navigateur obligatoire sur la foi d'un `curl -L`** : le tester avec le module avant.

*Une fenêtre Chrome a quand même servi à une chose : l'URL d'accueil rendue
(`/?arko_default_636a80ee7d203--ficheFocus=`) a signé le moteur. L'ark `ark:/57115/a011…`
faisait penser à Mnesys — c'est un faux ami, Arkothèque frappe le même genre d'identifiant.*

### 2. DEUX MOTEURS COHABITENT SUR LA MÊME PAGE

- `arko_default_63692f9dd5e9d` — **index NOMINATIF** collaboratif, 34 256 entrées, colonnes
  Nom / Prénom(s) / Commune / Type d'acte / Année / Qualité. **Très partiel** : DUPONT et
  LEVASSIER y rendent 0 quand LEMOINE rend 63. *Un index n'est pas un fonds* — un zéro n'y
  prouve rien.
- `arko_default_635b873d1f4a7` — **le CATALOGUE des registres**, 25 594. C'est lui qui mène
  aux images.

Les prendre l'un pour l'autre fait chercher un registre dans une liste de personnes.

### 3. L'AGRÉGATION N'EST PAS LE FILTRE, ET L'ERREUR EST SILENCIEUSE

| | |
|---|---|
| agrégation commune | `arko_default_635fe00fbe2ee` |
| **filtre** commune | `arko_default_635fe0c23fd4c` |
| filtre type d'acte | `arko_default_635fe0c25c8b6` |
| filtre période (slider) | `arko_default_635fe0c2535eb` |
| filtre cote | `arko_default_635fe0c263e11` |
| `refUniqueField` visionneuse | `arko_default_635fc93dd76a6` |

Poser l'agrégation au lieu du filtre **ne rend aucune erreur** : le moteur ignore le critère
et rend les **25 594 registres du département**, avec des agrégations parfaitement crédibles
— types d'acte, décennies, tout y est. **Recompter contre le total sans filtre** : Coutances
rend 285, « rien » en rend 25 594.

Les quatre `refUnique` ne se devinent pas et ne se grattent pas : `/_recherche-api/moteur`
interrogé **sans aucun filtre** rend `filtres`, chacun avec son intitulé en clair
(« Commune ou paroisse », « Type d'acte », « Période », « Cote »). Recette de l'AD49, qui a
resservi une troisième fois.

**Référentiel** : 573 communes dans l'agrégation, chacune avec son `arko_fiche`. Les libellés
sont **nus** — « Coutances », sans département ni pays, contrairement à l'AD24.
`resultSize` plafonne à 25 en silence, comme partout.

### 4. Les matricules sont le meilleur levier du portail

`arko_default_636a6a86849b7` — **204 144 fiches indexées nominativement**, champ nom
`arko_default_636a6c27c2b7b`, champ prénom `arko_default_636a6c27d6428`. Une fiche matricule
nomme **les parents du conscrit** et leur domicile : c'est la pièce qui rattache une
génération quand l'état civil du XXᵉ siècle n'est pas communicable.

### 5. Ce que le 6 juin 1944 a changé au fonds

**Les Archives départementales de la Manche ont brûlé le 6 juin 1944.** Ce qui est en ligne
vient donc des **collections communales déposées** — à Coutances, la cote `250 Num`. D'où un
fonds qui s'arrête à **1913** pour cette commune, quand d'autres montent aux années 1923-1932.
Ce n'est ni une lacune de numérisation ni un délai légal : c'est ce qui a survécu.

*Corollaire, et il retourne une règle de la skill : ici il n'y a **pas** de second exemplaire.
La parade « aller voir l'autre collection » avant d'écrire `[non lu]` ne joue pas dans la
Manche.*

**Images** : 2800 × 1951 en **double page**, soit ~1400 px par page. Suffisant pour une
écriture de 1910, à la limite pour du XVIIIᵉ.

| Commune | `arko_fiche` | Registres |
|---|---|---|
| `Coutances` | `arko_fiche_63736ceb4aa14` | 285 au catalogue, 107 à l'index nominatif |
| `Saint-Nicolas-de-Coutances` | `arko_fiche_63736cf55bfef` | 662 à l'index nominatif |
| `Saint-Pierre-de-Coutances` | `arko_fiche_63736cf565adf` | 17 |

Tirés sur le NAS : `AD50 - Coutances/N 1908-1910` (vues 96-134) et `TD 1903-1912` (vues 1-40).

---

## AD47 — Lot-et-Garonne · moteur **Prismia ViSiON** *(septième moteur du dossier)*

**Ouvert le 4 septembre 2026**, en une heure, pour Henri DUPONT — né rue du Gaz à
Villeneuve-sur-Lot le 21 septembre 1878, père de l'imprimeur de Coutances. Moteur inconnu,
et pourtant la méthode a tenu sans qu'une règle soit réécrite.

| | |
|---|---|
| Vitrine TYPO3 | `archivesdepartementales.lotetgaronne.fr` — **aucun registre** |
| Moteur | `https://lotetgaronne.archives.prismia.fr` |
| Backend | `https://ad47.backend.archives.prismia.fr/api/` |
| Module | `moteurs/prismia.py`, sans navigateur |
| Images | **IIIF Image API 3**, manifeste IIIF Presentation 3 |
| Compte | non |

### 1. LA VITRINE N'EST PAS LE MOTEUR — et ici elle ne partage même pas le domaine

`archives.lotetgaronne.fr` et `www.archives47.fr` **ne résolvent pas**. Le portail public
est un TYPO3 qui ne porte pas un registre ; le moteur est sur un domaine tiers, et son
adresse ne se trouve qu'en lisant les liens de la vitrine.

### 2. TOUT EST DANS LE BUNDLE JAVASCRIPT, EN CLAIR

Prismia est une application React **d'une seule page** : `/`, `/Recherche/Etat civil`,
`/js/routing`, `/swagger` — **toutes rendent la même coquille de 1375 octets**. Chercher un
formulaire dans le HTML ne rend rien, et essayer des chemins à la main non plus.

```
/runtimeConfig.js          window.prismConfig = { serverUrl, apiKey, title, … }
/static/js/main.<hash>.js  39 points d'entrée, dont /presentation/v1/Query
```

C'est « **lire la réponse en entier avant de deviner une URL** » appliqué à un bundle : le
front publie la configuration du backend, clé d'API comprise. **On la lit à chaque session,
on ne la code pas en dur** — le portail peut la tourner, et une clé périmée rend 401 partout,
ce qui ressemble à une panne du site.

### 3. LE MOTEUR SE DÉCRIT, DEUX FOIS

`/presentation/v1/instrument/list` rend les **20 formulaires** du portail, chacun avec ses
chemins de fonds et ses facettes — nom, `aggregateTag`, et la clé exacte à passer. Le n° 13
est « Registres paroissiaux et état civil » ; il y a aussi Matricules militaires, Recensements,
Notaires, Cadastre. C'est la recette de l'AD49 en Arkothèque, sur un moteur qui n'a rien à
voir : **la première chose à faire sur un portail inconnu est de lui demander sa liste de
formulaires.**

Et la réponse de `/presentation/v1/Query` **renvoie la requête complète** dans `searchQuery` :
tous les paramètres qu'on n'a pas passés y apparaissent avec leur valeur par défaut —
`codesCommunes`, `prismThematicId`, `getTimeline`, `getLocation`. L'API se documente en
répondant.

| | |
|---|---|
| facette Commune | `geogname||Commune||Commune` · tag `Lieux` |
| facette Type d'acte | `extrafield||Actes` · tag `ExtraField` |
| valeurs | Baptêmes ou Naissances · Mariages · Sépultures ou Décès · Tables décennales · Actes divers · Autres |

Les critères se posent en `tagSelectedFilters: [{keys: […], values: […]}]`. Le libellé de
commune **se lit** par `getFacetValues` — « Villeneuve-sur-Lot », nu, sans département.
Faux amis d'une recherche partielle : « Villeneuve » rend aussi Sainte-Colombe-de-Villeneuve,
Villeneuve-de-Duras et Villeneuve-de-Mézin.

**Et `prismPathOrId` n'est pas optionnel.** Sans les quatre chemins de l'instrument, le filtre
de période rend tous les fonds : 653 documents pour Villeneuve-sur-Lot en 1878, correspondance
de gendarmerie comprise. Avec eux : **un seul registre**.

### 4. LE NUMÉRO DE VUE N'EST PAS LE NUMÉRO DE PAGE, ET LE REGISTRE SE RÉPÈTE

Les vues **64 et 65** des naissances 1878-1882 de Villeneuve-sur-Lot portent **les mêmes deux
actes** (n° 192 et 194) : la même double page, photographiée deux fois, avec le volet de la
mention marginale replié autrement. Ce n'est pas un défaut, c'est un service rendu — on lit
la mention *et* le texte qu'elle recouvre. Mais **estimer une date en divisant le nombre de
vues par le nombre d'années se trompe alors toujours dans le même sens : trop loin dans le
registre.** Reculer plus que le calcul ne le dit.

*C'est le pendant du timbre fiscal de Lublé, à l'envers : là un objet cachait l'acte, ici il
est écarté et la vue est doublée.*

### 4 bis. UN guid NE SE DEVINE PAS, ET DEUX guid VOISINS SONT DEUX REGISTRES

`470028587` est *Naissances 1878-1882*, `470028593` est *Naissances 1883-1887*,
`470028594` est *Naissances 1888-1892*. **Les identifiants consécutifs numérotent des
REGISTRES, pas des vues** — deux voisins peuvent être à cinq ans l'un de l'autre. Le
4 septembre 2026, un guid déduit du registre voisin a fait tirer quarante-quatre vues de
1884-1885 dans un dossier nommé « N 1888-1892 » : aucune erreur, aucun avertissement, et
un dossier qui ment sur son contenu pour toutes les sessions suivantes. **Demander le guid
au moteur, toujours** — `registres()` le rend avec la cote et le nombre de vues.

C'est la même faute que le numéro de numérisation de la Haute-Loire, où un écart qui
semblait constant (+630) valait +633 ailleurs.

### 4 ter. `resultSize` PLAFONNE EN SILENCE ICI AUSSI, ET ÇA FABRIQUE DE FAUX TROUS

Villeneuve-sur-Lot a **224** registres de mariages. Une requête à `size=200` en rend 200
sans un mot — et la liste tronquée montrait des lacunes de 1878-1880 et 1888-1892 dans le
fonds, **qui n'existent pas**. On a failli conclure que l'AD47 n'avait pas numérisé ces
années. `registres()` pagine désormais et compare au total annoncé. Même piège qu'à
l'AD45, l'AD49 et l'AD24 : **recompter, toujours.**

### 5. Les images

Le manifeste `{serverUrl}/iiif/presentation/v3/{guid}/manifest` rend **tout le registre en une
requête**, un canvas par vue. L'URL de l'image **se lit** dans
`items[].items[0].items[0].body.id` — ne pas la reconstruire : elle encode l'arborescence du
serveur de fichiers (`/ad47/medias/etat_civil/frad047_002miec323/…`).

**3496 × 2480 en double page**, soit ~1750 px par page : mieux que l'AD50 (1400), moitié moins
que le Maine-et-Loire (2748).

| Commune | Registre | Cote | guid | Vues |
|---|---|---|---|---|
| Villeneuve-sur-Lot | Naissances 1878-1882 | `4E322-58` | `470028587` | 438 |
| Villeneuve-sur-Lot | Tables décennales 1873-1882 | `5 E 322-16` | `470024429` | 430 |

448 registres d'état civil pour la commune, 9 877 documents tous fonds confondus.
Tirés sur le NAS : `AD47 - Villeneuve-sur-Lot/N 1878-1882` (vues 40-90).

---

## AD02 — Aisne · moteur **Boscop / Ligeo**, derrière **Anubis**

**Ouvert le 4 septembre 2026**, pour chercher le mariage des parents d'une personne vivante à
Laon. Le moteur était écrit, la fiche voisine existait — et elle m'a induit en erreur.

| | |
|---|---|
| Base | `https://archives.aisne.fr` |
| Recherche | `/archive/recherche/etatcivil/n:11` · résultats `/archive/resultats/etatcivil/n:11` |
| WAF | **Anubis**, résolu par un Chrome fenêtré en **quatre secondes** |
| Compte | non |

### 1. LE PIÈGE DE L'AD79/86 EST ICI RETOURNÉ

À l'AD79/86, remplir le champ **texte** de la commune ne filtrait rien : seul le `md5` posé
par la facette comptait. **Ici c'est exactement l'inverse.** `RECH_commune`, le champ texte,
filtre ; le couple `RECH_commune_Libel` / `RECH_commune_Index` est **ignoré**.

Six variantes recomptées contre le total sans filtre, le 4 septembre 2026 :

| Forme posée | Réponses |
|---|---|
| `RECH_commune_Libel` + `RECH_commune_Index` | 313 |
| les mêmes avec des pipes finaux | *erreur* |
| `RECH_commune_Index` seul | 313 |
| **`RECH_commune` seul** | **1** |
| les trois ensemble | 313 |
| *aucun critère de commune (témoin)* | 313 |

**Même moteur, convention opposée. Ne pas transposer la fiche voisine** — et recompter
toujours contre le total sans filtre, seul moyen de voir qu'un critère est tombé.

### 2. Ni token ni index Solr : on écoute le réseau

Le HTML de la page de recherche ne porte **ni `token=` ni `ind=`**, contrairement à l'AD79/86 :
la recette par `arcfacette.php` échoue en silence. L'endpoint réel se trouve en **écoutant le
trafic pendant qu'on tape** :

```
POST /archive/xhr/gettheslist/listecommunes/0/etatcivil/RECH_commune_Index
corps : RECH_commune=Laon
→ <ul><li id="0"><strong>Laon</strong> (Aisne, France)</li></ul>
```

Le libellé doit être **complet, avec son suffixe** : `Laon (Aisne, France)`.

### 3. Faux ami : la recherche texte fait de la sous-chaîne

`Laon` attrape **Aulnois-sous-Laon**, Athies-sous-Laon et Chivres-en-Laonnois. Un résultat
isolé sur une fenêtre où la commune devrait être absente est presque toujours l'un d'eux :
**lire la colonne « Contexte »**, qui donne la commune réelle. C'est ce qui a failli faire
prendre `1 E 49/9 • 1935-1950` d'Aulnois pour un registre de Laon.

### 4. L'état civil de Laon s'arrête en 1937 en ligne

Vérifié avec témoin, ce qui est la seule façon d'écrire un négatif :

| Fenêtre | Laon | Tout le département (témoin) |
|---|---|---|
| 1930-1937 | **18** dont « 1 E 453/69, 1929-1932, mariages » | 2 039 |
| 1938-1945 | 1 — *et c'est Aulnois* | 656 |
| 1946-1952 | 1 — *et c'est Aulnois* | 403 |
| 1938-1960 | 1 — *et c'est Aulnois* | 828 |

Le moteur répond ; il n'y a simplement rien. **Et ce n'est pas un délai légal** : les registres
de naissance et de mariage jusqu'à 1951 sont communicables depuis 2026. C'est un choix de
publication. **Pour un acte des années 1940 à Laon, il faut écrire à la mairie** — elle tient
les tables annuelles, et un patronyme rare sur une fenêtre de trois ans est une demande
recevable.

### 5. Et les recensements s'arrêtent en 1931

Le second réflexe, quand l'état civil est muet, est le recensement : il nomme tout le ménage,
**les épouses y figurant sous leur nom de jeune fille**, et celui de 1946 est communicable
depuis 2021. Ici il ne sert pas. La série de Laon est en ligne, complète et souvent **indexée
nominativement** — 1831, 1841, 1846, 1851, 1856, 1861, 1866, 1872, 1876, 1881, 1886, 1891,
1901, 1906, 1911, 1921, 1926, **1931** — et elle s'arrête là. Ni 1936 ni 1946.

*Attention en revanche : sur la recherche `rp`, le filtre de dates ne mord pas — une fenêtre
1940-1950 rend des tableaux de l'an IV. C'est la liste par commune qui fait foi, pas le
compte.*

---

## Geneanet — la facette de LIEU rapproche, elle ne filtre pas

**Payé le 4 septembre 2026**, sur la branche LE MOUEL. Une recherche
`nom=LE MOUEL` + `place=Laon` dans « Archives et documents » a rendu cinq réponses, dont
**deux fiches de prisonniers de guerre 39-45** affichées avec la mention
« **Laon, Aisne, France** ». Le nom LE MOUEL n'ayant aucune naissance dans l'Aisne avant
1941, la conclusion s'imposait : ce « Laon » devait être une garnison ou une résidence — et
c'était exactement le profil du grand-père cherché, militaire en garnison à Laon.

**C'était faux.** La source de ces fiches est libre : les *Listes officielles de prisonniers
de guerre français* sont numérisées sur Gallica (`ark:/12148/cb34458709m`, 100 fascicules de
1940-1941), et Gallica cherche dans leur texte par son service `ContentSearch`. Vingt-neuf
fragments, vingt-cinq LE MOUEL relevés, et le format de chaque entrée donne le lieu :

```
Le Mouel (François), 7-8-17,  Poullaouen,        2e cl., …
Le Mouel (Robert),   24-1-17, Pontivy (Morb.),   2e cl., …
```

**Poullaouen et Pontivy. Zéro occurrence de « Laon » dans les vingt-neuf fragments.** Le
rapprochement venait de la facette de lieu de Geneanet, qui **classe par ressemblance au
lieu de filtrer** — la règle déjà écrite pour FamilySearch, qui rendait une Anna Volpatti
morte à San Francisco pour une recherche à Valvasone. Elle vaut ici aussi, et j'ai lu
l'affichage « Laon, Aisne, France » comme une donnée du document alors que c'est
**le critère de la requête, réaffiché**.

**À retenir** : sur Geneanet, un lieu montré à côté d'un résultat n'est pas forcément un
lieu *du* résultat. Et quand un index payant montre une piste, **chercher si la source
imprimée est sur Gallica** : ici elle l'était, gratuite, et plus riche que l'index.


---

## AD17 — Charente-Maritime · moteur **ARCHINOË** — *reconnaissance du 29 août 2026, module non écrit*

**C'EST LE SEPTIÈME MOTEUR DU DOSSIER, ET LE PREMIER QUI NE SOIT AUCUN DES SIX.** La règle
« regarder si le moteur est déjà écrit, c'est le cas nominal » a été vérifiée trois fois
d'affilée — AD45, AD67, AD49 — et **elle vient de rencontrer son exception**. Ni Boscop, ni
Arkothèque, ni Naoned, ni Anaphore : le portail de la Charente-Maritime tourne sur
**Archinoë**, et il faudra lui écrire son module.

| | |
|---|---|
| Vitrine | `https://archives.charente-maritime.fr` — **Drupal, aucun moteur d'archives** |
| Page « archives en ligne » | `/archives-en-ligne` — c'est elle qui porte les liens vers le moteur |
| Moteur, état civil et registres | `https://archinoe.com/v2/ad17/registre.html` |
| Autres formulaires | `/v2/ad17/recensement` · `/v2/ad17/cadastre.html` · `/v2/ad17/conscrit_nominal.html` · `/v2/ad17/photo.html` · `/v2/ad17/carte_postale.html` |
| Inventaires (EAD) | `https://archinoe.com/ead/AD17/<FONDS>` — p. ex. `FRAD017_Bagne`, `FRAD017_Terriers` |
| Compte | aucun repéré |

**`archives.lacharentemaritime.fr` NE RÉSOUT PAS** — l'adresse qu'on croit connaître n'existe
pas. C'est `archives.charente-maritime.fr`, et la vitrine est sur un autre hôte que le moteur :
troisième portail du dossier dans ce cas.

### Ce qui est établi, et ce qui reste à faire

**LE FORMULAIRE EST À SÉLECTEURS EN CASCADE**, et il est lisible dans le HTML — contrairement à
l'AD43 et à l'AD49, dont les pages ne contiennent aucun `<input>` :

```
<select id="inputcommune"    name="commune"    data-select="collection" data-page="registre">
<select id="inputcollection" name="collection" data-select="registre"   data-page="registre">
<select id="inputregistre"   name="registre"   data-select="acte"       data-page="registre">
<select id="inputacte"       name="acte">
<input  id="inputannee"      name="annee" type="tel" maxlength="4">
```

Le formulaire poste vers **`registre_liste.html`**, et chaque `<select>` se remplit par AJAX
quand le précédent change (`class="onchange"`, `data-select` désigne le suivant).

**LE MODULE EST ÉCRIT DEPUIS LE 29 AOÛT 2026 AU SOIR** —
[`moteurs/archinoe.py`](../../../../scripts/archives/moteurs/archinoe.py) — et **il ne demande
aucun navigateur** : quatre requêtes HTTP ordinaires, du référentiel des communes au JPEG.

```bash
python scripts/archives/moteurs/archinoe.py 17 communes mathes
python scripts/archives/moteurs/archinoe.py 17 registres 170000379
python scripts/archives/moteurs/archinoe.py 17 tirer 170022778 "<dossier>" 1 81
```

La cascade est décrite dans `/v2/console/js/script.js`, sous la forme
`{page}.html?{champ}={valeur}&type={champ_suivant}&id_lieu_ref=` — la réponse est une liste
d'`<option>`. D'où : `registre.html` rend les **552 communes en une requête**, puis
`?commune=&type=collection`, puis `&collection=&type=registre`, puis `registre_liste.html`,
puis `visualiseur/registre.html?id=` qui porte **toutes les vues du registre**.

### DEUX FAUSSES PISTES, ET ELLES SE RESSEMBLENT

**1. `recherche_data.php` RÉPOND POLIMENT À CÔTÉ.** Interrogée avec `type=commune`, elle rend
`{"query":"Marennes","suggestions":[]}` : elle échoit la question et rend une liste vide. J'en ai
conclu le 29 août « il manque une session », et **c'était faux** — `session.js` n'est qu'un shim
`sessionStorage` côté navigateur, il n'authentifie rien. Cette route sert **l'autocomplétion de
l'indexation collaborative**, pas les sélecteurs du formulaire. *Un endpoint qui répond
poliment à côté n'est pas un endpoint cassé : c'est le mauvais.*

**2. LE BOUTON DE TÉLÉCHARGEMENT EXPIRE, LE VISUALISEUR NON — ET ÇA A COÛTÉ UNE SESSION.** Le
1er septembre 2026, en ouvrant l'AD17 pour les matricules, une session a noté dans
`portails.json` : *« image : trouvée, et elle échoue côté serveur… ne pas repartir de là »*,
après neuf tentatives sur trois sessions. Elle passait par `telechargement.html`, qui demande un
hash puis **génère l'image à la demande et expire à vingt secondes**. Le visualiseur, lui, ne
demande jamais ça :

```
/v2/images/genereImage.html?o=IMG&image=<chemin disque>&l=<largeur>&r=0&n=0&b=0&c=0
```

Il rend **sept champs séparés par des tabulations** — `[1]` le chemin du JPEG dans `/cache/`,
`[2][3]` la taille servie, **`[4][5]` la taille du master** — et le JPEG suit immédiatement.
**La leçon n'est pas « le portail est cassé » mais « j'ai pris la porte de l'utilisateur au lieu
de celle de la page ».** Quand un chemin échoue, regarder ce que le site fait pour **afficher**,
pas ce qu'il propose pour **télécharger**.

**`data-original` reste un piège**, et sur ce point la note du 1er septembre avait raison :
`/mnt/lustre/ad17/…jpg` est le chemin disque du serveur, pas une URL — les trois formes
évidentes rendent 404. Il ne se fetch pas, **il se passe en paramètre à `genereImage.html`**.

**`l` ET `h` SONT LA LARGEUR ET LA HAUTEUR MAXIMALES — ET « DEMANDER PLUS NE REND PAS PLUS »
ÉTAIT FAUX.** Cette fiche l'a affirmé du 29 août au 11 septembre 2026 : avec `l=4264` sur un
master de 4264 × 3104, le serveur rendait 2472 × 1800, et j'en avais conclu que la hauteur
plafonnait. **Elle plafonnait parce que `h` n'était pas passé : 1800 est sa valeur par défaut.**
Le nom du fichier en cache le disait — `…_4264_1800_0_0_0_0_img.jpg`, la largeur puis la hauteur.
Avec `l=12359&h=8880`, le plan de Royan sort à **12 359 × 8 880, son master entier**. Pour un
registre, 1800 px suffisent presque à la recette de lecture ; pour un plan au 1/10 000, rien ne se
lit en dessous du master. `image()` fait donc deux appels : le premier lit la taille du master
(champs `[4][5]`), le second la demande.

*Vérifié de bout en bout le 29 août : table décennale des Mathes 1802-1813 (`170022778`,
81 vues), trois vues tirées, passées dans `nas.py`, parfaitement lisibles.*

### LES LISTES SONT PAGINÉES PAR VINGT — ET LE MODULE LE TAISAIT

**`registre_liste.html` et `cadastre_liste.html` rendent vingt lignes, et la page suivante tient
à un cookie.** `?page=2` sans cookie rend une page vide ; avec le `PHPSESSID` posé par la
recherche, il rend les vingt suivantes. Jusqu'au 11 septembre 2026, `registres()` ne lisait que
la première page, sans avertir : **Royan a 85 registres, le module en rendait 20.** Le module
tient désormais une session à cookies et lit les pages jusqu'à ce qu'une page n'apporte plus
rien de neuf. *C'est la règle « recompter contre le total annoncé », qui s'appliquait ici aussi.*

**Et ce que la pagination a rendu, au passage** : la collection du GREFFE de l'état civil de
Royan est en ligne **au moins jusqu'en 1932** (`2 E 318/130`, décès 1928-1932). La collection
communale s'arrête à 1899 ; celle du greffe, non.

### LE CADASTRE — ouvert le 11 septembre 2026

**Même mécanique que l'état civil, d'autres noms** : `cadastre.html` (formulaire),
`cadastre_liste.html?canton=&commune=<id>&cadastre=&plan=` (liste, paginée comme ci-dessus),
`visualiseur/cadastre.html?id=<id>` (vues), puis `genereImage.html` comme pour un registre.

```bash
python scripts/archives/moteurs/archinoe.py 17 cadastre 170000390          # les plans de Royan
python scripts/archives/moteurs/archinoe.py 17 tirer-plan 170080750 "<dossier>"   # pleine résolution
```

| | |
|---|---|
| Types de cadastre | napoléonien · remanié · remembré · rénové · rénové « dernière mise à jour avant informatisation » |
| Types de plan | tableau d'assemblage · feuille de section · néant |
| Une vue | un plan entier, jusqu'à 12 359 × 8 880 px — **à tirer en pleine résolution**, sinon rien ne se lit |

**CE SONT DES PLANS, PAS DES MATRICES : aucun propriétaire n'y figure.** Ils disent où est une
parcelle et quel est son numéro, jamais à qui elle est. **Et ils ont des trous** : Royan a
**167 plans, dont aucun entre 1838 et 1964** — 14 napoléoniens de 1838, puis le remembré de
1964, le rénové de 1969 et sa mise à jour de 1985. Pour savoir si une maison était debout avant
1945, le cadastre en ligne de Royan ne répond donc pas : il n'a pas de plan de ces années-là. Il
faut les **matrices cadastrales** (non proposées par ce formulaire) ou le **dossier de dommages
de guerre**.

### Pourquoi ce département compte

**C'est le pays de la branche maternelle du généalogiste** — Les Mathes, Marennes, La Palmyre,
Bourcefranc — et il n'avait jamais été ouvert. Trois murs d'ascendance du XIXᵉ l'attendent :
**Pierre DIOT × Marguerite COURNEGICHE** († 1837), **Jean PAVAILLON × Anne LAMBERTON** († 1850),
**Pierre AUGY × Jeanne DESMAISON**. Tous morts après 1792, donc tous à portée d'un acte de décès
— le levier qui a fait tomber la branche CHASLE en deux jours.

---

## AD46 — Lot · moteur **Arkothèque** · *le fonds le mieux indexé du dossier*

**Ouvert le 5 septembre 2026**, pour Antoine DUPONT, tailleur au lieu-dit Séniergues.
Trois actes trouvés et lus en une demi-heure — et c'est l'indexation qui explique ce
rendement, pas la chance.

| | |
|---|---|
| Base | `https://archives.lot.fr` |
| Module | `moteurs/arkotheque.py`, **sans navigateur** |
| Instance état civil | `arko_default_67ebab2c7f97d` — **160 411 entrées** |
| Compte | non |

*L'accueil rend le HTML court du jeton anti-robot, comme l'AD50. **Ne pas en conclure qu'il
faut un Chrome** : `_get()` suit le jeton dans la même session et tout passe.*

### L'ÉTAT CIVIL EST DÉCOUPÉ ANNÉE PAR ANNÉE, ET ÇA CHANGE TOUT

Ailleurs, un registre couvre cinq ou dix ans et il faut le cadrer, balayer ses marges ou
lire sa table décennale. **Ici, un document = une commune × un type d'acte × une année.**
D'où les 160 411 entrées, et une agrégation de périodes qui rend **1 368 valeurs, une par
année couverte**.

Conséquence concrète : **l'année 1883 des décès de Montfaucon fait huit vues.** On demande
l'année, on tire, on lit. Aucun dépouillement.

| | |
|---|---|
| filtre Commune | `arko_default_67ebadbab042e` · structure `arko_default_67ea6e78e7543` (531 communes) |
| filtre Type d'acte | `arko_default_67ebadbabdf53` · structure `arko_default_67ea8213addd5` (9 types) |
| filtre Période | `arko_default_67ebadbb0434b` (slider) · structure `arko_default_67ea666394cb5` |

Les neuf types, avec leurs effectifs : mariages 39 842 · naissances 39 357 · décès 39 333 ·
publications de mariages 34 379 · les trois séries de tables décennales ~3 820 chacune ·
baptêmes 1 589 · sépultures 1 572.

*Une seconde instance, `arko_default_67ecd8414d6cc` (606 entrées, filtre « Localité »), n'est
pas l'état civil.*

### LE CATALOGUE PORTE SES RENVOIS DANS LE LIBELLÉ, ET IL FAUT LES LIRE

**Séniergues n'a que deux entrées.** On croit à une commune sans archives ; c'est faux. La
seconde entrée s'intitule :

> « **1802-1902 (tables décennales : voir Labastide-Murat)** »

Une commune à deux entrées n'est pas une commune sans archives — **c'est une commune dont
les archives sont rangées ailleurs, et le catalogue le dit en clair dans l'intitulé.**

Autre variante du même soin : certains libellés portent « *(actuellement commune de X)* » —
Salgues, Beaussac, Goudou, Labastide-Marsa. Ce sont d'anciennes communes absorbées, avec
leur propre fonds.

### Deux pièges plus petits

**`telecharge()` ne tire qu'UNE vue si on ne lui passe pas le compte.** Avec `fin=None` il
s'arrête à la première. Le nombre est dans la colonne `vues` du tableau de résultats — le
lire et le passer.

**Une actualité du portail annonce une « indisponibilité temporaire des registres d'état
civil 1913-1932 ».** À vérifier avant de conclure à une lacune sur cette tranche.

### Le négatif consigné

**Le mariage DUPONT × PÉZERET n'est pas à Montfaucon.** Tables décennales des mariages
1823-1832 et 1833-1842 lues **en entier** à la lettre E : Escapoulade, Escudié, Estival, rien
d'autre. Et les registres de mariage de la commune sont **complets de 1830 à 1845** — le
négatif ne vient pas d'un trou. Antoine étant né vers 1807 et son fils aîné Pierre vers 1838,
l'union tombe entre 1827 et 1838 : elle est ailleurs, vraisemblablement dans la commune de la
mariée. **Reste à balayer le canton** : Carlucet, Soulomès, Ginouillac, Fontanes-du-Causse,
Caniac-du-Causse, Blars, Sénaillac-Lauzès.

| Commune | `arko_fiche` | Entrées |
|---|---|---|
| `Montfaucon` | `arko_fiche_681db1776b1a8` | 496, de 1675 à 1922 |
| `Labastide-Murat` | `arko_fiche_681db1742e25b` | 560 |
| `Séniergues` | `arko_fiche_681db17cdbb2d` | 2 — voir le renvoi ci-dessus |

Tirés sur le NAS : `AD46 - Montfaucon/D 1883`, `D 1884`, `N 1851`, `TD M 1823-1832`,
`TD M 1833-1842` · `AD46 - Labastide-Murat/TD M 1823-1832`, `TD M 1833-1842`.

---

## 🇮🇹 Caduti della Grande Guerra — l'Albo d'Oro · moteur **ASP.NET WebForms**

**`https://www.cadutigrandeguerra.it`** — signalé par un correspondant le 7 septembre 2026.

**Ce que c'est, et pourquoi ça compte** : l'**Albo d'Oro**, la liste officielle des militaires
italiens morts pour la patrie en 1915-1918, publiée en vingt-huit volumes de 1924 à 1954 par le
ministère de la Défense et mise en ligne en entier — environ 530 000 noms. **C'est un FONDS, pas
un index de bénévoles** : sur son périmètre il est exhaustif, et un zéro y est un vrai négatif.
C'est assez rare pour être dit.

### Le moteur — un septième, et il est facile une fois qu'on sait

ASP.NET **WebForms** : `.aspx`, et trois champs cachés `__VIEWSTATE`, `__VIEWSTATEGENERATOR`,
`__EVENTVALIDATION`. La recette : **GET** de `/CercaNome.aspx`, on en extrait les trois, on les
**REPOSTE** avec le formulaire, cookies de session gardés. Pas de WAF, pas de navigateur.

*Ne pas le confondre avec Arolsen, qui est aussi de l'ASP.NET mais en `.asmx` — là ce sont des
services web JSON, ici un POST de formulaire.*

### ⚠️ Le piège qui coûte : **le mois vaut « 0 », pas la chaîne vide**

Les deux `<select>` de mois — `tMeseNasc` et `tMeseMorte` — ont **`0`** pour valeur vide. Leur
envoyer `""` rend un **HTTP 500 sec**, sans message. Les autres selects (`tAlbo`, `tReg`,
`tRegAtt`) veulent bien la chaîne vide.

### ⚠️ Et le nom est un **préfixe**, pas une égalité

`MIGOT` rend **treize** fiches — toutes `MIGOTTI` ou `MIGOTTO`, **aucune MIGOT**. Donc **un zéro
strict se lit dans la liste, jamais dans le compte** : l'écran affiche « 13 nominativi » quand la
réponse à la question posée est zéro. C'est le piège inverse de celui de Toulouse, et il trompe
dans l'autre sens.

*En revanche c'est une chance sur un patronyme à graphies flottantes : `PEDEROD` attraperait
PEDERODA et PEDERODI d'un coup.*

### Le vocabulaire se lit, il ne se devine pas

```
/GetValoriCampo.ashx?Campo=ComuneNascita&q=VALVASON   ->  [{"Key":"Valvasone",...}]
/GetValoriCampo.ashx?Campo=ComuneNascita&q=VITO       ->  [{"Key":"Vito D'Asio",...}]
```

`Campo` vaut `ComuneNascita`, `ProvNascitaOrig`, `ComuneNascitaAttuale`, `ProvNascitaAtt`,
`Grado`, `GradoUniformato`, `Reparto`, `RepartoUniformato`, `Distretto`, `Decorazioni`,
`LuogoMorte`, `CausaMorte`, `CausaMorteUniformato`. **À interroger avant de taper un libellé** —
c'est la règle « un libellé de commune ne se reconstruit pas, il se lit », et ici le site le sert.

### ⭐ Le raccourci qui marche : chercher par **comune di nascita**

Sur un village, la liste entière tient en une page — **Valvasone rend 40 morts**, avec pour chacun
le nom, le prénom du père, la classe, le grade, l'unité, l'année, le lieu et la cause de la mort.
**C'est ainsi qu'on répond à « un tel du village est-il mort à la guerre ? » quand on n'a pas son
nom**, et ça ne coûte qu'une requête.

### Deux liens par ligne, et c'est le second qui porte tout

- `ShowImg.aspx?id=…` → **l'image** de la page de l'Albo d'Oro.
- `DettagliNominativi.aspx?id=…` → **la fiche complète**, et elle donne ce que le tableau tait :
  la **date de naissance au jour**, le **district militaire de recrutement**, la **date de mort au
  jour**, et la **page et le sub** dans l'Albo.

---

## 🇫🇷 Le fichier des décès de l'INSEE — **l'outil des branches d'émigrés**

**`https://deces.matchid.io/`** · jeu de données brut : `data.gouv.fr/datasets/fichier-des-personnes-decedees`

Le dossier s'en sert depuis le 11 août 2026 et **presque toutes les sessions y passent** — ce qui
suit n'est donc pas une présentation, mais **les trois choses que le carnet n'avait pas écrites**,
et qui ont valu une identification le 2 septembre 2026.

### ① Il porte la commune de naissance **même à l'étranger**

C'est ce qui en fait l'outil de la branche italienne, et personne ne l'avait noté. Un natif
d'Italie mort en France y figure avec sa **commune de naissance en clair** et le code pays
**`99127`**. Le moteur normalise les variantes : `birthCity=Valvasone` attrape aussi
« Valvasone Arzene » et « Valvasone, Province De Udine ».

### ② ⭐ On peut chercher **par commune de naissance seule**, sans nom

C'est le raccourci, et c'est le même geste que l'Albo d'Oro : **on ne cherche plus quelqu'un, on
lit le village.** `birthCity=Valvasone` rend **175 personnes** — dix mortes en Savoie, les autres
à Grenoble, Toulouse, Givors, Lyon, Sarrebourg, Mantes, Antibes.

**C'est ainsi qu'a été identifié l'ami d'enfance d'Alfiero PEDIRODA**, dont le généalogiste ne savait que
le prénom : *un seul Achille parmi les 175*. Sans le patronyme, aucune recherche par nom n'était
possible ; la commune de naissance, elle, suffisait.

### ③ L'API, qui évite de cliquer

```
https://deces.matchid.io/deces/api/v1/search?firstName=&lastName=&birthCity=&birthCountry=
                                            &birthDate=&deathDepartment=&size=
```

`birthDate` accepte une **plage** écrite `1936-1941`. La réponse est du JSON :
`response.total` et `response.persons[]`, chacun avec `name.first[]`, `name.last`, `birth.date`
(AAAAMMJJ), `birth.location.city/country`, `death.date`, `death.location.city/departmentCode`.

### ③ bis ⛔ DEUX PIÈGES DE L'API, PAYÉS LE 18 SEPTEMBRE 2026

**UNE APOSTROPHE DANS `birthCity` NE FILTRE PLUS RIEN, ET LE TOTAL A L'AIR D'UN RÉSULTAT.**
Mesuré le même jour, sur la même commune :

| requête | total rendu |
|---|---|
| `birthCity=Clauzetto` | **208** |
| `birthCity=Vito d'Asio` | **406 201** — la base entière |
| `birthCity=Vito-d-Asio` | **406 201** |
| `birthCity=Vito dAsio` | 4 667 — du bruit |

C'est la famille du `REch_commune` de l'AD16 : **le filtre ne proteste pas, il s'efface.** Le
contrôle est toujours le même — comparer à une requête sans filtre. **La parade qui marche pour
une commune à apostrophe : passer par `lastName` + `birthCountry=ITALIE`**, qui rend la commune
de naissance en clair dans chaque réponse, et trier à l'œil.

**ET L'USAGE ANONYME A UN QUOTA, QUI NE DIT PAS SON NOM.** Au bout de quelques requêtes, l'API
rend un **422** dont le corps est : *« No token provided and temporary anonymous usage expired,
please register with email or wait 0 hours »*. Un 422 ressemble à une erreur de paramètre — on a
cru pendant deux essais que c'était `birthCountry` qui n'était pas reconnu. **Lire le corps de la
réponse, pas seulement le code.** Le quota retombe vite (quelques minutes) ; `size=300` est
refusé, **200 est le maximum**.

### ④ ⭐ QUAND matchID EST EN PANNE — ET IL L'ÉTAIT ENCORE LE 12 SEPTEMBRE 2026

⛔ **CE PARAGRAPHE A ACCUSÉ LE MAUVAIS COUPABLE PENDANT ONZE JOURS.** Le certificat de matchID n'a jamais expiré : c'est **le magasin de racines de Windows servi à Python** qui portait une racine périmée, et il refusait aussi Wikipédia, `data.gouv.fr`, `francearchives.gouv.fr` et `culture.gouv.fr` — tous chez Let's Encrypt. **`scripts/archives/tls.py` répare ça pour tout le processus, et `python scripts/archives/tls.py` le vérifie sur quatre témoins.** À lancer dès qu'un `CERTIFICATE_VERIFY_FAILED` apparaît, AVANT d'écrire quoi que ce soit sur le site. *Ce qui suit reste vrai comme méthode de repli, et le passage par `data.gouv.fr` reste le bon geste pour un balayage de masse.*

**matchID est une COMMODITÉ, PAS LA SOURCE.** Son certificat TLS a paru expiré le **7 septembre 2026**
et ne l'était toujours pas renouvelé cinq jours plus tard : `curl` rend `SEC_E_CERT_EXPIRED`, la
requête ne part pas. L'hôte est le bon, l'autorité est Let's Encrypt, **seule la fraîcheur
manque** — la recherche du 8 septembre était passée outre en désactivant la vérification.

**Ce n'est pas la bonne réponse. La bonne réponse est de changer de porte** : l'INSEE diffuse
**les mêmes données en fichiers bruts sur `data.gouv.fr`**, sous un certificat valide, et on les
balaye plus vite qu'on ne clique.

```bash
curl -s "https://www.data.gouv.fr/api/1/datasets/fichier-des-personnes-decedees/"   # liste les fichiers
curl -s "<url du fichier>" | grep -a -E '^MONNOM'                                   # en flux, rien sur disque
```

**Mesuré le 12 septembre 2026 : 34 fichiers — 2000-2025 par année, 2026 par mois —, 2,9 Go,
QUATRE MINUTES.** Un fichier annuel fait ~110 Mo et se télécharge en 5 s. Format à **largeur
fixe** : `nom*prénoms/` sur 80 caractères, puis sexe (1 M / 2 F), date de naissance AAAAMMJJ, code
commune de naissance sur 5, commune en clair sur 30, pays sur 30, date de décès, code commune de
décès sur 5, **numéro de l'acte de décès**.

**⚠️ TROIS PIÈGES, TOUS PAYÉS LE MÊME JOUR.**

- **`curl` placé dans une boucle `while read` du shell rend ZÉRO OCTET sans le dire.** Le premier
  balayage a « lu » 34 fichiers de 110 Mo en 35 secondes et conclu à zéro partout. Le seul indice
  était le temps. **JOURNALISER LE NOMBRE D'OCTETS REÇUS, pas seulement le nombre de résultats** —
  un négatif sans volume n'est pas un négatif. *(Le `< /dev/null` sur `curl` n'a pas suffi ; c'est
  la boucle qu'il faut abandonner, au profit d'un script `sh` séparé.)*
- **Python refuse le certificat de `static.data.gouv.fr` que `curl` accepte** — les deux ne lisent
  pas le même magasin d'autorités. Sur Windows, faire le téléchargement en `curl`.
- **LE FICHIER N'EST PAS TRIÉ PAR NOM**, mais par ordre d'acte. Vérifié par trois requêtes de plage
  HTTP au début, au milieu et à la fin d'une année. **Aucune recherche dichotomique n'est
  possible** : il faut tout lire, et c'est pourquoi quatre minutes est un bon résultat.

**CE QUE ÇA A DONNÉ** : `FLORETTE*PIERRE ERNEST LOUIS/` — né le 23 avril 1922 à Millas (66108),
mort le 12 décembre 2006 à Argelès-sur-Mer (66008), acte n° 129. **Un seul dans tout le fichier
2000-2026**, là où le corpus ne lui connaissait aucune date.

### ⚠️ Le périmètre, et il décide de ce qu'un zéro veut dire

**DEPUIS 1970, ET LES DÉCÈS À L'ÉTRANGER Y SONT.** Cette fiche a écrit pendant des semaines
« uniquement les décès survenus en France », et **c'est faux** : la page officielle du jeu de
données l'écrit noir sur blanc — *« Ils incluent les décès survenus à l'étranger. »* Vérifié le
18 septembre 2026 sur `data.gouv.fr/api/1/datasets/fichier-des-personnes-decedees/`. L'erreur
coûtait cher dans le mauvais sens : elle offrait « mort à l'étranger » comme explication
commode à toute absence, et affaiblissait tous les négatifs qu'on en tirait.

**Ce qu'une absence veut donc dire, maintenant que le périmètre est juste** : la personne est
vivante, ou elle est morte avant 1970, ou son décès n'a pas été transmis, ou **la clé de
recherche est mauvaise**. C'est ce dernier cas qui est le plus fréquent, et il a deux formes :
le nom d'épouse (voir plus bas), et **une date de naissance incomplète dans le fichier lui-même**
— l'Insee écrit `AAAA=0000 si année inconnue ; MM=00 si mois inconnu ; JJ=00 si jour inconnu`.
Un filtre sur une date exacte rate donc quiconque n'est enregistré qu'à l'année.

**Et les fichiers 1970-1975 sont lacunaires**, de l'aveu de l'Insee : « le début de
l'informatisation des fichiers de décès peut comporter quelques manques ».

> **Le producteur est l'INSEE ; `data.gouv.fr` n'est que la plateforme de diffusion de
> l'État ; `deces.matchid.io` est un TIERS dont l'Insee se désolidarise explicitement en tête
> de la page du jeu de données.** Même donnée, trois portes, et une seule fait autorité : les
> fichiers bruts.

**Et le moteur classe par ressemblance au lieu de filtrer** — il rend des GIRAUDEAU pour une
recherche FRAUDEAU. Chaque réponse se relit nom par nom.

### ⚠️⚠️ IL INDEXE SOUS LE **NOM DE NAISSANCE**, ET C'EST CE QUI FAIT ÉCHOUER LES FEMMES MARIÉES

Le carnet l'écrivait déjà en passant ; il n'en tirait pas la conséquence, et elle a coûté une
recherche le 8 septembre 2026. **Une femme connue de la famille sous son nom de mari est
introuvable ici** — le fichier ne porte aucun nom d'usage. « Madame Dannepond », l'épicière
d'Angoulême, n'y est pas, et ne pouvait pas y être si Dannepond est son nom de mariage.

**Avant de chercher une femme dans ce fichier : savoir si le nom qu'on a est son nom de
naissance.** Si on l'ignore, un zéro ne veut rien dire du tout — ce n'est même pas un négatif.

### ⭐⭐ ET LA SORTIE EXISTE : ON NE CHERCHE PLUS UN NOM, ON CHERCHE UNE DATE

**Le carnet décrivait l'impasse sans donner l'issue. La voici, trouvée le 18 septembre 2026 sur
la famille MARTIN, et elle a levé deux murs dans la même journée.**

Une femme connue sous son nom d'épouse est introuvable par son nom — mais **son nom n'est pas
la seule colonne du fichier**. Si l'on connaît sa date de décès, ou sa date de naissance, ou
même seulement le département où elle est morte, on lit **tout le fichier** et on filtre
là-dessus. Le nom devient le RÉSULTAT au lieu d'être la question.

L'API de matchID ne sait pas faire ça : elle refuse `deathDate` par un 422 et exige un nom.
**Il faut donc les fichiers bruts de `data.gouv.fr`** — et ils se balayent vite :

| | |
|---|---|
| un fichier annuel | ~110 Mo, **6 secondes** de téléchargement, ~500 000 lignes |
| le fonds entier, 1970-2026 | **86 fichiers, 6,27 Go, 31 356 377 lignes, 387 secondes** |

```python
def champs(l):                       # largeurs fixes
    return dict(nom=l[0:80].strip(),    sexe=l[80:81],   naiss=l[81:89],
                cnaiss=l[89:94],        vnaiss=l[94:124].strip(),
                pays=l[124:154].strip(), deces=l[154:162],
                cdeces=l[162:167],      acte=l[167:176].strip())
# nom*PRENOMS/ ; sexe 1=H 2=F ; dates AAAAMMJJ ; codes commune INSEE sur 5
```

**LE CAS QUI L'A ÉTABLIE.** Simonne, grand-mère maternelle, connue de sa petite-fille sous
VITHMANN — le nom de son mari. Nom de naissance inconnu, donc aucune recherche possible. On
savait seulement « morte le 10 novembre 2018 à Tours ». Filtre sur `deces == "20181110"` et
`cdeces` commençant par 37 : **vingt personnes, une seule Simonne.** Elle s'appelait
**COULBEAU**, elle était née à Versailles — où sa fille était née en 1943, ce qui a confirmé
l'identification sans rien devoir à la mémoire familiale. Et elle était morte à
**Chambray-lès-Tours**, pas à Tours : la commune de l'hôpital, où meurent les Tourangeaux.

**TROIS LEÇONS QUI EN SORTENT :**

1. **Une date de décès vaut un nom.** C'est même mieux : elle ne se déforme pas au mariage.
2. **Le lieu de décès d'une famille est souvent la commune de l'HÔPITAL, pas celle où l'on
   vivait.** Chambray-lès-Tours enregistre quarante-neuf décès pour la seule année 2018 sur
   des gens nés ailleurs. Balayer le DÉPARTEMENT, jamais la seule commune que dit la famille.
3. **Un négatif obtenu par ce moyen est solide**, là où un négatif par nom d'épouse ne vaut
   rien. Sur Pierrette, le balayage a porté sur *née le 25 juin 1932* (1 599 personnes, dont
   trois à Rouen, aucune Pierrette) et sur *Pierrette née en 1932, morte en Auvergne* (198,
   aucune née un 25 juin) : **là, l'absence veut dire quelque chose** — sous réserve que la
   date de naissance, qui vient de la mémoire, soit juste.

### ⭐ ET IL TRANCHE UNE ORTHOGRAPHE, PARCE QU'IL NE DÉPEND D'AUCUN OCR

C'est un usage que le carnet ne mentionnait pas, et il est excellent. Là où la presse numérisée
rend « Dannepond » et « Dannepont » avec des comptes voisins — l'OCR ne distingue pas le D du T
final —, le fichier des décès est **saisi, pas océrisé** : il donne la forme exacte de l'état
civil. Interrogé sur six graphies, il a rendu **trente-sept personnes, toutes à DEUX N**, et
montré que les formes à un seul N n'existent pas.

**Et il donne le berceau du nom par surcroît** : lire les communes de NAISSANCE des porteurs
dessine la carte de la famille. Les trente-sept DANNEPOND se concentrent autour de Saintes —
Chaniers, Corme-Royal, La Clisse, Varzay, Luchat, Thénac — et non à Angoulême, où on les
cherchait.

### ⚠️ Panne du 7 septembre 2026 — le certificat TLS du site a expiré

`deces.matchid.io` a cessé de répondre en pleine session : *« certificate verify failed: certificate has expired »*. **Ce n'est pas le magasin de racines local** — vérifié en repassant par le paquet `certifi`, l'erreur persiste : c'est bien le certificat du serveur. **TOUJOURS PAS RENOUVELE AU 8 SEPTEMBRE 2026** : il a expire le 7 septembre a 02 h 22 UTC, et le certificat servi reste le meme. L'hote (CN=deces.matchid.io) et l'autorite (Let's Encrypt) sont les bons ; seule la fraicheur manque. Pour une donnee publique en lecture seule, on peut passer outre en desactivant la verification — mais on l'ECRIT DANS LA SOURCE, et on reverifie au renouvellement. Panne qui se repare chez eux, mais qui coupe l'outil sans prévenir au milieu d'une recherche. **Le repli, s'il faut absolument avancer : les fichiers bruts de l'INSEE sur `data.gouv.fr`**, qui ne dépendent d'aucun service tiers.

### Le contrôle positif qui ne coûte rien

**Chercher quelqu'un dont on connaît déjà la mort.** Alfiero PEDIRODA figure dans la liste de
Valvasone — *« né 19380711 à Valvasone, mort 20190204 à Rochefort »* — et sa présence a prouvé que
la requête par commune étrangère fonctionnait avant qu'on en tire un négatif.

---

## 🕰️ La Wayback Machine — **quand l'administration a disparu avec son site**

Ce n'est pas une archive généalogique, et c'est pour ça qu'on n'y pense pas. Elle a pourtant
rendu, le 7 septembre 2026, une information qui n'existait plus nulle part ailleurs.

**LE CAS QUI L'A INTRODUITE.** Valvasone a fusionné avec Arzene le 1ᵉʳ janvier 2015 : la commune
a cessé d'exister, et son site `comune.valvasone.pn.it` est mort — le corpus le notait déjà
comme tel. Avec lui avait disparu **la composition de son conseil municipal et de sa giunta**,
qu'aucune autre source publique ne donne. Les deux pages sont dans l'archive.

**La règle qui en sort : une commune fusionnée, un service supprimé, une association dissoute
emportent leur site — et c'est souvent là que dorment les listes nominatives qu'on cherche.**

### Les deux API, et la seconde est la vraie

```
# la capture la plus proche d'une date — ne sert que si l'on connaît déjà l'adresse
http://archive.org/wayback/available?url=<url>&timestamp=YYYY

# TOUTES les URL archivées d'un domaine — c'est celle-ci qui sert
http://web.archive.org/cdx/search/cdx?url=<domaine>/*&output=text
    &fl=timestamp,original&filter=statuscode:200&collapse=urlkey&limit=400
    &from=2001&to=2008
```

La seconde **liste ce qu'on ne sait pas chercher** : c'est elle qui a montré que le site de
Valvasone avait soixante captures de 2001 à 2012 et une page `Amministrazione.2768.0.html` dont
on ignorait l'existence.

### ⚠️ Quatre pièges, tous payés le même jour

**`WebFetch` NE PASSE PAS sur `web.archive.org`** — il refuse net. Il faut appeler `urllib` en
direct depuis un script.

**UN 503 N'EST PAS UN 404.** L'archive limite le débit et rend `503 Service Unavailable` dès
qu'on enchaîne. J'ai failli conclure que la page de la *Giunta* n'existait pas : elle répondait
503 quand ses voisines répondaient 404. **Un 404 est une absence, un 503 est une attente** —
réessayer après vingt secondes.

**LE `timestamp` DEMANDE UNE DATE, IL N'EN GARANTIT AUCUNE.** L'API rend la capture *la plus
proche*, pas celle de l'année demandée : `timestamp=2005` a rendu une capture de **2021**.
Toujours lire la date réelle dans l'URL retournée — `/web/20211227031848/`.

**⭐ ET LE PIRE : LIRE UNE SEULE PAGE D'UNE RUBRIQUE PRODUIT UN FAUX NÉGATIF.** J'ai lu le
*Consiglio Comunale* et conclu qu'un homme n'y figurait pas — sans lire la *Giunta*, qui est une
page voisine et un organe différent. Or la giunta de Valvasone comptait une **`assessore
esterno`** : en droit italien depuis 1993, **un adjoint peut siéger à l'exécutif sans être
conseiller municipal**. La liste du conseil ne l'aurait jamais montrée. **Repérer les pages
sœurs dans le menu de navigation, et les lire toutes.**

### Ce qu'il faut en retenir

Avant d'écrire « ce fonds n'est plus en ligne » : **chercher si le site a été archivé**. Ça vaut
pour les communes fusionnées, les anciens portails d'archives remplacés par un nouveau moteur,
et les bases associatives éteintes.


---

## 📖 GALLICA — l'IMPRIMÉ, et c'est un autre métier que le registre

Module : [`moteurs/gallica.py`](../../../../scripts/archives/moteurs/gallica.py). **Fiche
`gallica` dans `portails.json`** — ce paragraphe a dit « pas de fiche : ce n'est pas un portail
d'archives départementales, il n'a ni commune ni cote » jusqu'au 18 septembre 2026. La raison se
défendait, et elle laissait un registre qui ignorait la moitié des fonds qu'on interroge, donc
incapable de servir de contrôle. Les sources sans département y entrent avec `dept: null`.
**Gallica sert à trouver ce que la PRESSE et les LIVRES ont gardé de quelqu'un** — une
nomination, une citation, une mise à la retraite, un avis de décès. C'est le complément de
l'état civil, pas son concurrent.

### Les fonds qui ont servi, avec leurs arks

| Fonds | ark | Couverture |
|---|---|---|
| **Annuaire officiel de l'armée française** | `cb32698403m` | 1906-1920 (1906, 07, 08, 10, 11, 13, 14, 1920) |
| **Listes d'ancienneté des officiers** (hors série) | `cb32808399p` | 1922-1937 |
| **Annuaire officiel des officiers de l'armée active** | `cb32698448k` | 1924-1937 |
| **Journal officiel, Lois et décrets** | `cb34378481r` | 1881-2015, quotidien |
| **Table annuelle du Journal officiel** | `cb371291967` | 1881-2015 |

**LES TROIS SÉRIES D'ANNUAIRES SE RELAIENT ET SE RECOUPENT**, et c'est en les balayant toutes
qu'on suit une carrière d'officier année par année : grade, régiment, garnison, décorations. Une
seule d'entre elles laisse des trous de plusieurs années.

### Ce que ce fonds coûte, en vrai

Le 7 septembre 2026 : **4 083 numéros du Journal officiel** dépouillés — 2 247 pour la fenêtre
1920-1922, 1 836 pour 1929-1931 — plus neuf annuaires. Compter **une heure par année** de
quotidien, `dans()` sur chaque numéro, deux graphies. **Ne jamais lancer plus d'un balayage à
la fois** : Gallica rend des `429` et les deux ralentissent. Le script doit **écrire son résultat
tous les vingt-cinq numéros**, sinon une coupure perd tout.

### Deux fonds pour un village, et le piège de graphie qui les cache

Trouvés le 9 septembre 2026 en cherchant les LOYAU de **Benassay** (Vienne). Ils ne servent pas
qu'à ce dossier : **toute recherche sur un hameau ou une famille rurale passe par là.**

| Fonds | ark | Ce qu'il donne |
|---|---|---|
| **Nomenclature des localités du département de la Vienne** | `bpt6k65599510` | chaque commune **village par village**, avec sa **population** et ses **principaux habitants** |
| **Dictionnaire topographique de la Vienne**, Rédet, 1881 | `bpt6k110098j` | tous les noms de lieux, **y compris disparus**, avec leur **plus ancienne attestation datée** |

La Nomenclature a placé les DERBORD à **l'Étang**, les BÉCHON à **la Counière** et à **Grassai** ;
Rédet donne « la Pinelière, **1528** ». **Les autres départements ont leur Dictionnaire
topographique** — c'est une collection nationale, `Dictionnaire topographique de la France`.

**ET LA COMMUNE S'ÉCRIT AUTREMENT DANS CES OUVRAGES.** « Benassay » rend **zéro** dans la
Nomenclature ; **« Benassais »** en rend deux, et c'est la graphie de l'acte de 1828. La règle des
graphies du patronyme vaut pour les communes, et elle se paie de la même façon : un négatif qui
n'en est pas un.

### Les pièges payés

**⚠️ UNE CHAÎNE EST UNE LOCUTION, UNE LISTE EST DES TERMES SÉPARÉS — ET LA CONFUSION REND ZÉRO.**
C'est l'erreur la plus vite commise sur ce fonds, et elle est silencieuse :

```python
cherche("Chasles Lublé")        # gallica adj "Chasles Lublé"   ->   0
cherche(["Chasles", "Lublé"])   # adj "Chasles" AND adj "Lublé" -> 154
```

Un fait divers écrit « le sieur Chasles, cultivateur à Lublé » : les deux mots ne sont jamais
collés. **Dès qu'on cherche plus d'un fait — un nom ET un lieu, un nom ET un métier — passer une
LISTE.** Le 9 septembre 2026, la forme chaîne a fait conclure « Gallica n'a rien sur les
CHASLES » ; la forme liste rend 154 documents pour Lublé et 118 pour Ambillou.

### La presse de Touraine et d'Anjou, relevée le 9 septembre 2026

| Titre | Période | ark | Pour qui |
|---|---|---|---|
| **Le Tourangeau** — *hebdomadaire, organe des intérêts agricoles* | 1890-1940 | `cb32878322j` | **le meilleur** : le journal des cultivateurs de Touraine, et **52 numéros par an** au lieu de 365 |
| Le Républicain de Chinon | 1903-1944 | `cb328523053` | arrondissement de Chinon |
| L'Écho de Chinon — *hebdomadaire* | 1926-1942 | `cb32759927k` | idem, plus tardif |
| Journal de Chinon | 1843-1926 | `cb32797301k` | la longue durée |
| L'Anjou, journal de l'Ouest | 1883-1903 | `cb34522104b` | côté Maine-et-Loire |
| L'Ami du peuple (Angers) | 1849-1940 | `cb32691585c` | idem, quotidien — cher |

*Ces titres couvrent Lublé, Couesmes, Villiers-au-Bouin, Château-la-Vallière, Ambillou d'un
côté, Noyant, Méon et Meigné de l'autre. Ils ne servent à rien avant 1840.*

**`adj` CONTRE `all`, ET LES GUILLEMETS DANS `dans()`.** Déjà dans le module, et ça reste la
première cause de bruit. `ContentSearch` racinise aussi : `"Espéret"` avec guillemets rend 0 là
où `Espéret` nu rend 209 « espérer ».

**LE NUMÉRO RENDU PAR `dans()` EST UNE VUE, PAS UNE PAGE IMPRIMÉE.** Sur l'annuaire de 1920,
vue = page + 100. Sur le Journal officiel, vue = page. **Le vérifier une fois par ouvrage** en
tirant la vue et en lisant le folio imprimé, sinon on cite une page qui n'existe pas.

**`obj=Max-size` ET LES AUTRES PARAMÈTRES IIPIMAGE NE VALENT PAS ICI** — Gallica sert du IIIF :
`image(ark, vue, dest, taille="full")`. La taille native suffit toujours ; agrandir n'ajoute
rien.

**ET L'OCR MENT.** Voir la section « Chercher dans un imprimé » de la skill : les négatifs, le
contrôle de cohorte, la légende des symboles. C'est là qu'est la méthode ; ici il n'y a que les
adresses.

---

## 🎖️ SHD (Vincennes) et FRANCEARCHIVES — le catalogue du producteur n'indexe pas tout

**LA LEÇON, ET ELLE VAUT BIEN AU-DELÀ DU SHD : quand le catalogue de celui qui CONSERVE reste
muet, interroger l'agrégateur — et inversement.** Le 7 septembre 2026, la recherche du dossier
d'officier d'un capitaine a rendu, sur le site du SHD, **53 notices** sous cinq graphies
(PAIRE, PAYRE, PAIRET, PEYRET, PERRET) — **toutes en GR 4, 5, 7 ou 9 Ye, aucune en 6 Ye**. La
sous-série GR 6 Ye n'y est pas indexée au dossier ; son inventaire n'existe que sous forme de
« PDF liste complète », derrière un générateur côté navigateur. **FranceArchives, lui, publie le
même inventaire découpé en tranches alphabétiques et le rend cherchable au nom** : une requête,
et la cote sortait.

| | |
|---|---|
| Recherche SHD | `GET https://www.servicehistorique.sga.defense.gouv.fr/resultats-recherche?cles=<mots>&cote=<cote>&page=<n>` |
| Champs du formulaire | `cles`, `cote`, `thematiques`, `lieu`, `debut`, `fin`, `type[]` |
| Notices | trois lignes de texte : intitulé, **cote**, nature. Se lisent dans `document.body.innerText`, pas par un sélecteur CSS |
| Recherche FranceArchives | `https://francearchives.gouv.fr/fr/search?q=<requête>` — ⚠️ **cette ligne a dit « vrai Chrome obligatoire » jusqu'au 18 septembre 2026, et c'était faux** : voir la fiche FranceArchives plus bas |

### Les sous-séries de dossiers d'officiers, et le piège qui coûte des mois

| Sous-série | Période |
|---|---|
| GR 2 Ye | 1791-1847 |
| GR 5 Ye | 1848-1925 |
| **GR 6 Ye** | **1926-1940** — 61 673 dossiers |
| GR 8 Ye | 1941-1970 |

**LA DATE EST CELLE DE LA CLÔTURE DU DOSSIER, DONC DE LA CESSATION D'ACTIVITÉ — PAS DES ANNÉES
DE SERVICE.** Un officier entré en 1904 et rayé des cadres en 1930 est en **6 Ye**, pas en 5 Ye.
Le corpus a porté « GR 8 Ye » pendant trois semaines, ce qui aurait fait écrire une lettre à la
mauvaise série.

### CE QUE LE CATALOGUE DU SHD INDEXE AU NOM, ET CE QU'IL N'INDEXE PAS

Mesuré le 7 septembre 2026 sous cinq graphies. **La recherche par nom marche très bien — sur
certaines séries seulement**, et rien sur la page ne dit lesquelles.

| Série | Lieu | Ce que c'est | Indexée au dossier ? |
|---|---|---|---|
| **AC 21 P** | **Caen** | victimes des conflits contemporains — morts pour la France, prisonniers, déportés | **oui**, abondamment (11 dossiers pour le seul nom PAIRE) |
| GR 4, 5, 7, 9 Ye | Vincennes | dossiers d'officiers, autres périodes | **oui** |
| **GR 6 Ye** | Vincennes | **officiers rayés des cadres 1926-1940** | **NON** — 53 notices rendues sous cinq graphies, aucune en 6 Ye |

**Conséquence pratique : ne pas conclure d'un silence du catalogue que le dossier n'existe pas.**
Il a fallu **FranceArchives** pour trouver `GR 6 YE 34299`. Et inversement, quand on cherche un
homme mort ou disparu pendant un conflit, **AC 21 P à Caen est la série que ce catalogue sert le
mieux** — c'est le premier réflexe pour un mort pour la France.

### ⚠️ LE CHAMP « COTE » DE LA RECHERCHE SIMPLE APPARIE LE NOMBRE, PAS LA SÉRIE

**Piège vérifié le 7 septembre 2026, et il rend un faux positif crédible.** Interrogé avec
`cote=GR 6 YE 34299`, le moteur du SHD répond **« 1 résultat »** — et c'est *« Dossier individuel
de personnel de **JOSSIER Nicolas** — **GR 5 YE 34299** »*. Autre série, autre homme, même
nombre. Rien ne signale la substitution : la page annonce un résultat, on croit avoir vérifié sa
cote, et on a lu celle de quelqu'un d'autre.

C'est la variante « cote » du travers déjà connu — *un moteur qui classe au lieu de filtrer rend
toujours quelque chose*. **Une cote ne se vérifie donc pas dans ce champ** : elle se vérifie là
où l'inventaire est publié, c'est-à-dire sur **FranceArchives** pour GR 6 Ye. Et une recherche
par NOM n'y rend rien non plus pour cette sous-série — `cles=PAIRE Jean Regis` : « Il n'y a pas
de résultat à votre recherche ».

### Demander une reproduction : DEUX formulaires, et le premier réflexe est le mauvais

Le fonds GR 6 Ye est **librement communicable**. Mais **le formulaire « Ma demande
administrative » n'est pas le bon**, et c'est sa propre page qui l'écarte : elle porte un
tableau d'aiguillage — *« Pour les cas énumérés ci-après, contactez directement le centre ou le
service indiqué »* — dont une ligne dit **« les officiers rayés des cadres avant le 1er janvier
1971 (de sous-lieutenant à colonel inclus) → Service historique de la Défense, Centre des
archives de Vincennes »**. Tout dossier d'officier ancien tombe donc hors de ce formulaire.
*Erreur faite le 7 septembre 2026, et vue par le généalogiste sur la page elle-même.*

| Ce qu'on veut | Le formulaire |
|---|---|
| **On a la cote** et on veut une copie | `/form/reproduction-de-documents` — « Demander une reproduction » |
| On ne sait pas où chercher | `/form/contact` — « Demande d'orientation » |
| Démarche administrative (états de services pour soi, pensions…) | `/form/demande-de-demarche-administrative`, **sauf les cas du tableau d'aiguillage** |

**Et le centre n'accepte que ces voies** : *« les demandes d'orientation et de reproduction de
documents doivent être exclusivement formulées via les formulaires dédiés »* du site ou par
courrier postal ; le reste n'est pas traité. Compter **trois mois** pour une orientation,
**quatre** pour une reproduction, plus les frais.

*Centre des archives de Vincennes — château de Vincennes, avenue de Paris, 94306 Vincennes
Cedex · 01 41 93 45 45 · `shd-vincennes.secretaire.fct@intradef.gouv.fr`.*

**Une autre ligne du tableau d'aiguillage vaut d'être retenue** : les **personnels nés avant
1921, sous-officiers et militaires du rang**, relèvent des **archives départementales** du lieu
de recensement — pas du SHD. C'est la règle qui renvoie aux registres matricules.

---

## AD27 — Eure · moteur **Mnesys** — *reconnaissance du 7 septembre 2026, module non écrit*

| | |
|---|---|
| Base | `https://archives.eure.fr/` |
| Moteur | **Mnesys** (éditeur Naoned) — donc `naoned.py` devrait servir |
| Recherche | `GET /search/results?q=<mots>&scope=<portée>` — **lu dans le formulaire de la page d'accueil** |
| ark | `ark:/26335/<id>` |

**DEUX URL DE RECHERCHE INVENTÉES ONT RENDU 404** — `/rechercher/tout?q=` et `/search?q=` — avant
que le formulaire de la page d'accueil ne donne la vraie, `/search/results`. C'est exactement la
règle « lire la réponse en entier avant de deviner une URL », enfreinte par paresse. Le
formulaire était à deux lignes de code.

**CE QUE CE PORTAIL N'A PAS** : l'**École militaire préparatoire des Andelys**, une des six E.M.P.
ouvertes par la loi du 19 juillet 1884 et inaugurée en 1887, n'y a **aucun fonds d'archives**. La
recherche « école militaire préparatoire » rend 65 résultats, **tous dans l'inventaire des cartes
postales de l'Eure**, plus trois brochures de bibliothèque. Les archives de l'établissement sont
ailleurs — au SHD le seul fonds à ce nom est **GR 7 P 196** et il ne couvre que **1940-1946** ;
reste le **Musée national des enfants de troupe**, à Autun.

---

## 🇦🇷 CEMLA — les entrées de passagers au port de Buenos Aires, 1882-1960

Portail : <https://cemla.com/buscador/> · **moteur réel** <https://search.cemla.com/> · ouvert
le 7 septembre 2026

*Centro de Estudios Migratorios Latinoamericanos*, Independencia 20, Buenos Aires. La base
reproduit les **livres de la Dirección General de Migraciones** — 32 739 voyages, 5 350 000
personnes. Gratuite.

| | |
|---|---|
| **Emprise** | Entrées **par le port de Buenos Aires** uniquement, **1882-1960** |
| **Moteur** | ASP.NET MVC, résultats en tableau trié côté client |
| **Navigateur** | **OUI** — `cemla.com` rend 403 à `WebFetch`. `lire_page.js` passe |
| **Compte** | aucun |
| **⛔ CAPTCHA** | **BotDetect. La recherche demande un humain, et on ne le contourne pas** |

### La recherche ne s'automatise pas, et c'est à écrire en clair

`cemla.com/buscador/` n'est qu'une **iframe** ; le moteur est sur `search.cemla.com`. Son
formulaire porte quatre champs — `Lastname` (*Apellido*, **obligatoire**), `Name` (*Nombre*),
`DateFrom` (défaut `1800/01/01`), `DateTo` (défaut `1960/12/31`) — **et un captcha BotDetect**,
avec jeton `LBD_VCID_SampleCaptcha` et `__RequestVerificationToken`.

**Donc : c'est le généalogiste qui interroge, et une session lui donne les graphies à taper.** Lire le
captcha à sa place serait défaire une protection posée exprès par une archive publique, pour
une base qui est par ailleurs gratuite et ouverte à tous. *Le besoin réel est de six requêtes,
pas de six mille.*

Le tableau rendu porte dix colonnes : **Apellido · Nombre · Edad · Estado Civil · Nacionalidad ·
Lugar de Nacimiento · Profesión · Fecha de Arribo · Barco · Puerto**. ⚠️ **Demander une capture
en fenêtre large** : la première, le 7 septembre, était coupée après `Puerto` et on ne sait
toujours pas s'il en reste.

### ⛔ LES TROUS DU FONDS, ET ILS DÉCIDENT DE CE QU'UN ZÉRO VEUT DIRE

Tout ceci est écrit par le CEMLA lui-même, dans sa FAQ, et **il faut le lire avant de consigner
un négatif** :

| Période | Ce qu'il y a |
|---|---|
| avant 1870 | **pas ici** — les livres sont à l'Archivo General de la Nación |
| **1870-1881** | **PERDUS OU ÉGARÉS.** Rien, nulle part |
| 1882-1932 | complet en principe, mais **un pourcentage de listes est semi-détruit ou en mauvais état** |
| **1933-1937** | **SEULS LES ITALIENS ET LES ESPAGNOLS** sont saisis ; les autres nationalités, quelques mois çà et là. Si négatif → **AGN, archivo intermedio** |
| 1938-1960 | saisi |

**ET LA BASE NE CONNAÎT QUE LE PORT DE BUENOS AIRES.** Une entrée par **Montevideo, le Brésil
ou le Chili**, puis par voie de terre, n'y est pas — et pour qui visait le Río de la Plata,
débarquer à Montevideo et traverser était courant. Le CEMLA renvoie là aussi à l'AGN, archivo
intermedio. **Un zéro au CEMLA ne dit donc jamais « cette personne n'est pas venue » ; il dit
« elle n'est pas entrée par Buenos Aires, ou son livre est détruit, ou son nom est écrit
autrement ».**

Autres pièges que la FAQ donne : le buscador **ne rend que 100 lignes** ; un **patronyme
composé** se cherche d'abord au premier nom seul (donc `GIROLAMI` avant `DE GIROLAMI`) ; les
**enfants** sont parfois inscrits sous le nom de la mère ; et les noms « ont subi des
altérations d'une lettre ou d'un accent », ce que le CEMLA écrit lui-même — c'est la règle des
sept graphies, en espagnol.

### ⚠️ DEUX PIÈGES PAYÉS LE 7 SEPTEMBRE 2026, ET LE SECOND EST UTILISABLE AILLEURS

**① LE LIEU DE NAISSANCE EST VIDE AVANT 1923.** Les deux lignes PEDIRODA portent « Lugar de
Nacimiento : **DESCONOCIDO** », et ce n'est pas un accident : les autorités argentines ne
notent systématiquement le lieu de naissance des débarqués **qu'à partir de 1923** (Javier
Grossutti, *L'emigrazione dal Friuli Venezia Giulia in Argentina e in Uruguay*). **Une ligne du
CEMLA ne rattache donc personne à une commune.** Ce qui rattache, c'est la rareté du patronyme,
la date de naissance, et une source de famille — jamais le document lui-même.

**② LA COLONNE « ESTADO CIVIL » EST FAUSSE, ET C'EST NOTRE PROPRE ACTE QUI L'A MONTRÉ.** Antonio
PEDIRODA y est « S », *soltero*, le 11 juin 1885 — alors que son acte de mariage du 6 février
1873 est au dossier et qu'il avait des jumeaux de dix ans. La liste était remplie par la
**compagnie de navigation**, non vérifiée, et les passagers y étaient inscrits **par groupe
familial** : « S » dit peut-être « voyage seul ». **Le contrôle vaut méthode : quand une base
sérielle porte une colonne douteuse, la tester sur la personne du corpus dont on connaît déjà
la réponse.**

### Ce que la base ne donne pas, et que l'image donne

La liste manuscrite d'origine porte des colonnes que le buscador ne rend pas — au premier chef
**« observaciones »**, qui dit si le passage était **PRÉPAYÉ**, donc si quelqu'un attendait sur
place. **C'est la pièce qui prouve une chaîne migratoire**, et elle n'est pas dans la base. Elle
nomme aussi les autres passagers du même bord. Les livres — *Libros de entrada de pasajeros vía
marítima*, 808 volumes, 1882-1937, inscrits au registre Mémoire du monde de l'UNESCO — sont à
l'**Archivo General de la Nación**, et l'AGN a son propre moteur, qui cherche **par nom de
navire et par plage de dates** : <https://www.argentina.gob.ar/interior/archivo-general-de-la-nacion/consulta-de-antecedentes-migratorios>.
*Quand on tient le navire et le jour — et c'est le cas ici —, on n'a pas besoin de savoir écrire
le nom.*

Pour une attestation formelle (*Certificado de Arribo a América*, apostillable) : `base@cemla.com`.

### ⚠️ DEUX PIÈGES DE PLUS, TROUVÉS EN LISANT LES 42 LIGNES DE GIROLAMI

**③ UN COMPTE DE RÉSULTATS N'EST PAS UN COMPTE DE PERSONNES.** Sur les 42 lignes, **onze
personnes figurent deux fois et une trois fois** — même prénom, même âge, même navire, même
jour. La **seule** différence entre les doublons est la colonne « Lugar de Nacimiento », tantôt
vide, tantôt `DESCONOCIDO`, tantôt `D`. C'est un artefact de saisie, pas deux voyages : les 42
lignes font **31 personnes**. *Dédoublonner avant de citer un chiffre, et ne jamais lire un
doublon comme un aller-retour.*

**④ LA BASCULE DE 1923 SE VOIT AU MOIS PRÈS, ET ELLE SE VÉRIFIE SANS RIEN SAVOIR DE SA FAMILLE.**
Tout ce qui arrive en 1913, 1921 et 1923 porte un lieu de naissance vide ou `DESCONOCIDO` ; le
premier renseigné est celui d'une passagère du **18 janvier 1924**, née à Ascoli P. Ensuite la
colonne est servie. **C'est le contrôle interne de la règle** — et il se refait sur n'importe quel
patronyme un peu répandu, en une requête.

**⑤ ET LA COLONNE « ESTADO CIVIL » SAIT DIRE « MARIÉ ».** Onze des 42 portent `C`, dont un couple
débarqué ensemble avec ses cinq enfants. Le champ n'est donc pas décoratif — ce qui rend le `S`
d'Antonio PEDIRODA, marié depuis douze ans, plus intéressant et non moins : la lecture la plus
économique est qu'il **voyageait seul**, les passagers étant inscrits par groupe familial. *Elle
n'est pas établie ; ce qui l'est, c'est que le champ ne peut pas servir d'état civil.*


### Les recherches faites, et leur résultat

| Cherché | Fenêtre | Résultat |
|---|---|---|
| **PEDIRODA** | 1800-1960 | **2 lignes** — Antonio 1885/06/11 *Adria*, Silvio 1890/09/26 *Umberto 1*. Voir `src-cemla-2026-09` |
| PEDERODA · PIEDIRODA · PIEDERODA | 1800-1960 | 0 |
| **DEGIROLAMI** en un mot | 1800-1960 | **0** — et ce zéro ne voulait rien dire |
| **GIROLAMI** | 1800-1960 | **42 lignes** (31 personnes), toutes antérieures à 1928, des Marches et de Toscane |
| ⭐ **`DE GIROLAMI`** avec l'espace | 1800-1960 | **9 lignes, et c'est la bonne graphie** — trois arrivées d'après-guerre nées à San Michele al Tagliamento ou dans la province de Venise |
| DI GIROLAMO · GIROLAMO · DEGIROLAMO | 1800-1960 | 100 (plafonné), 43, 3 — des noms du Sud : Bari, Benevento, Trapani, Catanzaro |
| **MIGOT** | 1800-1960 | **0** |

> **LA LEÇON, ET ELLE VAUT POUR TOUT PATRONYME À PARTICULE.** Six graphies rendaient zéro ou du
> bruit ; **c'est l'espace qui décidait**. `DEGIROLAMI` → 0, `GIROLAMI` → une autre famille,
> `DE GIROLAMI` → la nôtre. La FAQ du CEMLA le dit — « chercher d'abord le premier nom seul, puis
> les deux » — mais elle ne dit pas qu'il faut aussi essayer **les deux formes du composé**, collée
> et séparée. **Sur un nom en DE / DI / LA / DEL, les trois formes se passent, toujours.**

⚠️ **Le zéro sur DEGIROLAMI et MIGOT ne clôt pas la question.** Ines MIGOT et Luigi DEGIROLAMI
partent avec un nourrisson né en avril 1934 ; ils sont **italiens**, donc la fenêtre 1933-1937
les couvre malgré la lacune. Mais **`GIROLAMI` seul n'a pas été essayé** — c'est ce que la FAQ
demande pour un patronyme composé, et `DE GIROLAMI` en deux mots est la forme qu'un employé
argentin écrit le plus volontiers. Et **une entrée par Montevideo n'est pas dans cette base.**

---

## AD06 — Alpes-Maritimes · moteur **Boscop / Ligeo**

Portail : <https://archives06.fr/> · ouvert le 7 septembre 2026

**Cinquième portail Boscop du carnet, et cinquième fois que le cas nominal se vérifie** : le
moteur était déjà écrit, il n'y avait qu'une fiche à poser dans `portails.json`. Vingt minutes,
dont dix passées sur la seule chose qui comptait — ce que le portail refuse de montrer.

| | |
|---|---|
| **Moteur** | **Boscop / Ligeo** — `<meta name="Generator">` le dit en clair |
| **WAF** | **TSPD (F5/Shape)**, un `/TSPD/?type=19`. Un vrai Chrome passe sans attente notable ; `WebFetch` et `curl`, non |
| **Préfixe ark** | `ark:/79346/` |
| **Image** | IIIF, `{base}/{ark}/manifest` — même recette qu'en Loire |
| **Compte** | aucun |

### Les paramètres, et les trois noms du même moteur

L'entrée d'état civil est **`type=etatcivil2`**, node **`n:101`**, et la vue s'appelle
**`tableau`** :

```
/archive/recherche/etatcivil2/n:101                        le formulaire
/archive/resultats/etatcivil2/tableau/n:101/page:{n}?type=etatcivil2&RECH_commune=Cannes
```

**La Loire dit `etatcivil` / `tabulaire` / `n:92`, le Bas-Rhin `lineaire` / `n:128`, l'AD06
`etatcivil2` / `tableau` / `n:101`.** Trois portails du même moteur, trois vocabulaires : rien ne
se recopie d'une fiche à l'autre.

**`RECH_commune` seul suffit ici** — pas besoin des `_Libel` et `_Md5` qu'exige le Bas-Rhin,
bien que le formulaire les porte aussi. Le libellé rendu est en majuscules nues (`CANNES`), mais
la casse d'interrogation est indifférente. **Et `RECH_date_debut` / `RECH_date_fin` acceptent une
année nue et fonctionnent** : c'est le moyen le moins cher de savoir ce qui existe pour une année
— une requête au lieu de quatorze pages.

Autres entrées repérées, non ouvertes : **`/archive/recherche/immigration2/n:151`** — un fonds
d'immigration propre au département, ce qui n'est pas rien sur une côte peuplée d'Italiens —,
conscription `n:103`, cadastre `n:104`, notaires `n:149`, presse `n:107`, mariages et baptêmes
`n:105`, catalogue des communes `/archive/catalogue/communes06/n:205`.

### ⛔ LES NAISSANCES DE MOINS DE CENT ANS SONT NUMÉRISÉES ET NON SERVIES — et c'est le seul piège du portail

**Mesuré sur Cannes le 7 septembre 2026, et la borne est nette :**

| | |
|---|---|
| Naissances **1925** (2 E 268) | **318 vues, libres** |
| Naissances **1926** (2 E 270) | **aucune vue** |
| Naissances **1931** (2 E 277) | 260 vues au manifeste, **restreintes** |
| **Mariages 1931** (2 E 277, *même cote*) | **204 vues, libres** |
| Décès 1931 (2 E 278) | 186 vues, libres |
| **Tables décennales N/M/D 1923-1932** (2 E 285) | 358 vues, **restreintes** |

Donc : **cent ans glissants sur les seules NAISSANCES**, quand les mariages et les décès des
mêmes années sont ouverts — et le même volume physique peut être moitié libre, moitié fermé. **Et
la restriction contamine les TABLES DÉCENNALES** dès qu'elles couvrent des naissances, ce qui
ferme l'index en même temps que la série. *La borne bouge d'un an par an : 1926 s'ouvrira en 2027.*

**Deux signatures, et prendre la moins chère.**

- **Dans le tableau de résultats, la colonne « Vue(s) » est VIDE.** Une requête de liste dit d'un
  coup ce qui est servi et ce qui ne l'est pas. **C'est le test à faire.**
- Dans le manifeste — qui se charge quand même et annonce le bon nombre de vues —, chaque canvas
  porte `ligeoRestrictedAccess: true` et `ligeoRestrictMessage: "Document numérisé uniquement
  accessible en salle de lecture"`, et son `images[0].resource` **n'a pas de `service`** : il
  pointe `/img/acces_sl.png`. Le `label` du manifeste le dit aussi en clair, suffixé
  « - Document numérisé non affichable ».

⚠️ **Un manifeste qui répond n'est pas un registre disponible.** C'est la première fois que le
dossier rencontre ça : ailleurs, un manifeste qui se charge donne les images. Ici il donne 260
canvas qui pointent tous la même vignette « accès salle de lecture ». **Un script qui compte les
vues conclurait que tout va bien.**

### Ce qu'il faut faire à la place

**LE SERVICE D'ARCHIVES, PAS LE GUICHET D'ÉTAT CIVIL — et la nuance décide de tout.** Pour
Cannes : **Archives municipales, Villa Montrose, 9 avenue Montrose, 06400 Cannes**. *Se rappeler
que `annuaire-mairie.fr` et consorts facturent 35 € ce qui est gratuit.*

### ⚠️⚠️ LE DÉLAI DE SOIXANTE-QUINZE ANS N'OUVRE PAS LA PORTE QU'ON CROIT

**Cette fiche a écrit « un acte de plus de soixante-quinze ans est librement communicable, la
commune le délivre » — et c'est faux à moitié.** Vérifié sur Légifrance le 18 septembre 2026,
après s'être heurté au mur sur un acte de 1929 à Lisieux. Deux textes, deux portes :

| texte | ce qu'il régit | ce qu'il dit |
|---|---|---|
| **Décret n° 2017-890 du 6 mai 2017, art. 30** | la **copie intégrale délivrée par l'officier d'état civil** | réservée à l'intéressé, ses **ascendants**, ses **descendants**, son conjoint — **AUCUNE exception d'ancienneté** |
| **Même décret, art. 26** | la **consultation** des actes | moins de 75 ans : agents habilités. Au-delà : renvoi au code du patrimoine |
| **Code du patrimoine, art. L213-2, I, 4°, e)** | la **communication de l'archive** | libre pour tous, **75 ans après la CLÔTURE DU REGISTRE** — et non après la date de l'acte |

**Donc, pour quelqu'un qui n'est pas de la famille :**

- **Au guichet et sur `service-public.fr`, jamais de copie intégrale**, quel que soit l'âge de
  l'acte. Le téléservice qui répond *« votre lien vous permet de demander uniquement un extrait
  sans filiation »* applique correctement l'article 30. **Insister ne sert à rien**, et se faire
  passer pour un proche serait une fausse déclaration à un officier public.
- **Ce qui s'ouvre à soixante-quinze ans, c'est l'ARCHIVE** — consultation du registre et
  reproduction, auprès du **service d'archives**, départementales ou municipales. C'est la seule
  porte, et la phrase à écrire cite **L213-2, I, 4°, e)**.
- **Et la mairie renvoie souvent au téléservice national**, ce qui referme le cercle : celle de
  Lisieux le fait. Ce n'est pas un mauvais vouloir, c'est la loi qu'elle applique.

**Corollaire qui fait gagner des semaines : quand un descendant direct existe et qu'on peut lui
demander, c'est TOUJOURS la route la plus courte.** Une petite-fille obtient en cinq minutes ce
qu'un tiers n'obtiendra jamais au guichet.

---

## AD66 — Pyrénées-Orientales · moteur **GAIA 9** — *reconnaissance du 12 septembre 2026, module non écrit*

**HUITIÈME MOTEUR DU CARNET, ET IL NE RESSEMBLE À AUCUN AUTRE.** Ni Boscop, ni Arkothèque, ni
Naoned, ni Anaphore, ni Archinoë, ni 4D, ni Prismia. Il se nomme lui-même dans son `<title>` :
**« GAIA 9 : moteur de recherche - 9.4.8 »**.

| | |
|---|---|
| **Portail** | <https://archives.cd66.fr> — **et c'est la seule des trois adresses testées qui réponde** |
| **Adresses mortes** | `archivesdepartementales.cd66.fr`, `ad66.cd66.fr`, `archivesenligne.cd66.fr` : aucune ne résout |
| **Signature** | chemins en `/mdr/index.php/<controleur>/…` ; `<title>GAIA 9 : moteur de recherche - 9.4.8` |
| **Entrée** | la racine rend 76 octets — un `<meta http-equiv="refresh">` vers `/mdr/index.php/rechercheTheme` |
| **WAF** | **aucun** ; mais `curl` sans `User-Agent` de navigateur prend un **403** sur certains chemins |
| **Compte** | non requis pour la page des thèmes |

### Les dix thèmes, relevés le 12 septembre 2026

Chaque thème est un formulaire distinct, à `/mdr/index.php/rechercheTheme/requeteConstructor/<id>/1/R/0/0` :

| id | Thème |
|---|---|
| **1** | **État civil** |
| 2 | Préparation militaire et recrutement de l'armée |
| **3** | **Recensement de la population, liste nominative** |
| 4 | Registres hypothécaires (1799-1955) |
| 5 | Plans cadastraux |
| 6 | Tables des décès, successions et absences (1704-1968) |
| 7 | Fonds François Bernadi, artiste colliourenc |
| 8 | Iconographie de la Retirada et des camps d'internement (1939-1948) |
| 10 | Contrôle des actes et insinuations (1693-1791) |
| 13 | Réfugiés et camps d'internement (1939-1942) : sélection d'archives nominatives |

### ⛔ CE QUI BLOQUE, ET IL NE FAUT PAS LE REDÉCOUVRIR

**LE FORMULAIRE EST CONSTRUIT EN JAVASCRIPT.** La page du thème 1 fait 13 213 octets et ne
contient **qu'un seul `<input>`, `tmprappval`, caché** : ni liste de communes, ni champ d'année,
ni type d'acte. Un `curl` ne verra jamais le formulaire. **Il faut un vrai navigateur** —
`scripts/archives/moteurs/lire_page.js`, qui garde un profil Chrome par domaine.

> ### ✅ CE PARAGRAPHE ÉTAIT VRAI DE LA PREMIÈRE PAGE, ET FAUX DE TOUT LE RESTE
>
> Repris le 18 septembre 2026 : **une fois le thème ouvert, GAIA 9 est du HTML de 2008, et
> `urllib` suffit.** Le parcours est une suite de liens ordinaires, puis un POST de formulaire
> ordinaire. Il faut seulement **rejouer les étapes dans l'ordre sur la même session à
> cookies** — GAIA garde la requête en session, et une étape appelée seule rend un
> `Invalid argument supplied for foreach()` qui ressemble à une panne alors que c'est un
> oubli de contexte.
>
> ```
> GET  /mdr/index.php/rechercheTheme                                   ouvre la session
> GET  /mdr/index.php/rechercheTheme/requeteConstructor/<thème>/1/R/0/0
> GET  …/requeteConstructor/<thème>/1/A/<id>/<libellé>                 1er critère
> GET  …/requeteConstructor/<thème>/2/A/<id>/<libellé>                 2e critère
> POST …/requeteConstructor/<thème>/3/A/0/0    typeDate=simple&dateSimple=1965
> POST …/requeteConstructor/<thème>/4/T/0/0    -> « LISTE DES REPONSES »
> ```
>
> ⚠️ **Le libellé fait partie de l'URL**, avec ses virgules et ses espaces : il se **copie**
> depuis le HTML, il ne se reconstruit pas. Et **la page se déclare `iso-8859-1`** — la lire en
> UTF-8 rend « requ�te ».
>
> ⛔ → ✅ **LA VISIONNEUSE EST OUVERTE DEPUIS LE 18 SEPTEMBRE 2026, ET LE MUR ÉTAIT UNE URL
> DEVINÉE.** Ce paragraphe a porté six jours la mention « pour voir les images, passer par le
> navigateur » — conclusion tirée de `detailNotice(0,0,'360573:…')` passé en segments d'URL, qui
> rend l'erreur SQL brute `SELECT TEXTE FROM ud WHERE ID_UD=360573:…`. **Cet appel-là n'est pas
> celui de la visionneuse, et la bonne adresse était dans la même page**, en clair, dans le
> `onClick` de la vignette :
>
> ```
> /mdr/index.php/docnumViewer/calculHierarchieDocNum/<idUd>/<cheminHierarchie>/<hauteur>/<largeur>
> ```
>
> **C'est le module `scripts/archives/moteurs/gaia.py` qui porte tout ça maintenant** — thèmes,
> critères, date, résultats, vues, sections alphabétiques et tirage sur le NAS.

### ⭐ CE QUE LA PAGE DE LA VISIONNEUSE DONNE, ET C'EST TOUT LE REGISTRE

Elle porte, dans son appel à `main({docs:[…]})`, **la liste complète des vues**, chacune avec
son `chemin` :

```
PERPIGNAN@PERPIGNAN_VILLE@1304W553@P@FRAD066_1304W0553_095.JPG
                                    ^ la lettre alphabétique
```

⭐⭐ **LA LETTRE EST DANS LE CHEMIN, ET ELLE VAUT UNE TABLE DES MATIÈRES.** Une table des
successions est rangée **par lettre, puis chronologiquement par date de décès dans la lettre** :
les 144 vues de 1965 se réduisent à treize dès qu'on cherche un P. `gaia.py vues` rend cette
table sans tirer une seule image.

### Le serveur d'images — ni jeton, ni cookie, et un plafond qui n'en est pas un

Les gabarits sont écrits en clair dans `/mdr/assets/visualiseur/js/contentManager.js` :

```
{HOST}/mdr/index.php/docnumserv/getImageVisualiseur/{RCODE}/{RVCODE}/{FILE}/{CACHE}/{TAILLE}/{COMPR}/{CRC}
```

`RCODE`/`RVCODE` viennent de la fiche de la vue (`TSAI`/`TSAV` pour les tables de successions),
`FILE` est le `chemin`, `CACHE=N`, `COMPR=100`, `CRC=200`.

⚠️ **`TAILLE` EST UN CODE, ET LA PAGE DEMANDE LE PETIT.** La visionneuse passe `T17` ; le
maximum est **`T20`, soit 2400 px** sur le grand côté. Mesuré : T15 = 800, T18 = 1600,
T20 = 2400. Au-delà — T21, T25, `ORI` — le serveur rend **1 286 octets qui ne sont pas une
image**, sans le dire. *Même leçon qu'à l'AD17 : un plafond peut n'être qu'une valeur par
défaut, et il faut sonder.*

> **Ce que ça a rendu le 18 septembre 2026** : thème 6, PERPIGNAN → PERPIGNAN VILLE → 1965,
> cote `11NUM1304W553`, `idUd=361490`, hiérarchie `360573:361650:361652:361490`. Lettre P aux
> vues 95-107. **Benigno PERESSON est la ligne 69 de la vue 101**, et la page de droite dit que
> sa déclaration de succession a été **déposée à Toulouse**, son domicile étant *6 place de
> Belfort*.

⚠️ **ET LE LIBELLÉ D'UN CRITÈRE S'ARRÊTE AU GUILLEMET, PAS À L'APOSTROPHE.** Une expression qui
exclut `'` du libellé tronque « ALBERE (L') » en « ALBERE (L » — et l'URL du critère devient
fausse en silence. Les liens sont délimités par des guillemets doubles : c'est eux qui bornent.

**LE PÉRIMÈTRE N'A PAS ÉTÉ MESURÉ**, et tant qu'il ne l'est pas, **un zéro ne veut rien dire**.
Ni la borne de communicabilité des naissances (les AD voisines appliquent 100 ans glissants — à
l'AD06, 1925 est libre et 1926 fermé), ni ce que couvre l'index nominatif, ne sont connus.
**Faire un contrôle positif avant de croire un négatif.**

### ⛔ ET CES DIX THÈMES SONT TOUT CE QUI EXISTE EN LIGNE — vérifié le 18 septembre 2026

La liste des thèmes est **la même qu'au 12 septembre** : dix formulaires nominatifs, et
**aucun moteur d'inventaire général**. On ne peut donc pas chercher une cote, une série ni un
fonds sur ce portail — seulement les dix thèmes.

**FranceArchives, lui, connaît l'AD66 — mais peu, et pas le commerce.** La facette « Lieux de
conservation » lui donne **381 notices sur « Perpignan »**, 160 sur « Millas », 22 sur
« Argelès-sur-Mer » : le service y a versé une partie de ses inventaires (fonds photographique
**26 FI**, fonds privés **217 J**, quelques versements **W**). Il est donc faux d'écrire qu'il
n'y est pas — *ce que cette fiche a failli dire avant de le mesurer.*

**En revanche, aucune des requêtes essayées n'a fait sortir un inventaire du greffe du tribunal
de commerce de Perpignan** : « tribunal de commerce Perpignan » (61 réponses, toutes du fonds
CCI du ministère de l'Industrie et des Archives nationales), « registre du commerce Perpignan »
(8 réponses, aucune de l'AD66), « greffe tribunal de commerce Perpignan 6 U » (528 réponses,
qui rendent la Meuse, la Haute-Loire et l'Hérault). **Ni sur le portail départemental, ni sur le
portail national, la sous-série du commerce de ce département n'est décrite.** Pour elle, il
faut écrire.

> **Archives départementales des Pyrénées-Orientales**
> 74 avenue Paul Alduy, BP 906, 66906 Perpignan Cedex · 04 68 85 84 00 · `archives@cd66.fr`
> Lundi au vendredi 8 h 30-17 h ; premier mardi du mois à partir de 13 h.

*Ce qu'on leur demandera : la sous-série **6 U** (greffe du tribunal de commerce), qui garde
d'ordinaire **la collection entière des registres du commerce jusqu'en 1954**, date de la
réforme de leur tenue ; puis la **série W** du même greffe pour l'après-1954. Cette répartition
est celle qu'écrivent les inventaires des autres départements — elle n'a pas été vérifiée sur
le fonds de Perpignan, qui n'est décrit nulle part en ligne.*

### Ce que le dossier y cherche

- ⭐ **L'acte de naissance de Pierre Ernest Louis FLORETTE, Millas, 23 avril 1922** — et surtout
  ses **mentions marginales**, qui portent la date de son mariage avec Paolina MIGOT. *(⚠️ un
  registre déposé aux AD peut ne pas porter les mentions postérieures au dépôt : la mairie de
  Millas reste le premier guichet.)*
- La famille **FLORETTE** de Millas, Saint-Féliu-d'Avall et Corneilla-la-Rivière — trois communes
  voisines, un seul foyer du nom.
- **Palau-del-Vidre** et **Argelès-sur-Mer**, où finissent les deux sœurs MIGOT.

---

## 🇦🇷 L'ARCHIVO GENERAL DE LA NACIÓN — le même fonds que le CEMLA, pris par l'autre bout

Formulaire : <https://www.argentina.gob.ar/interior/archivo-general-de-la-nacion/consulta-de-antecedentes-migratorios>

**Le fonds est le même** — les *Libros de entrada de pasajeros vía marítima*, 808 volumes, inscrits
au registre Mémoire du monde de l'UNESCO — mais l'accès n'a ni les mêmes bornes ni les mêmes
champs que le CEMLA.

**IL A UNE API PUBLIQUE, ET ELLE EST ÉCRITE EN CLAIR DANS LE JAVASCRIPT DE LA PAGE** :

```
https://agnbicentenario.mininterior.gob.ar/api/migrante/search
    ?apellido=   &nombre=   &anioDesde=   &anioHasta=   &barconombre=
https://agnbicentenario.mininterior.gob.ar/api/pdf/constanciamigraciones/?migrante=<id>
```

| | |
|---|---|
| **⭐ `barconombre`** | **on cherche PAR NAVIRE**, ce que le CEMLA ne permet pas. Quand on tient le bateau et le jour, on n'a plus besoin de savoir écrire le nom |
| **⛔ Bornes** | **1882-1937**, et le formulaire refuse toute année hors de là. **Il ne verra jamais l'après-guerre** |
| **Plafond** | 500 lignes, avec un message dédié au-delà |
| **Sortie** | une constancia en PDF ; et si le livre est numérisé, **le PDF du volume entier** |
| **Compte** | aucun |

⛔ **LE DOMAINE EST INJOIGNABLE DEPUIS AU MOINS LE 7 SEPTEMBRE 2026, ET C'EST POURQUOI AUCUN
MODULE N'EST ÉCRIT.** Constaté ce jour-là depuis la maison *et* depuis `WebFetch`, qui part d'une
IP américaine. **Re-testé le 19 septembre 2026, et le diagnostic est maintenant précis** :

```
agnbicentenario.mininterior.gob.ar  DNS ok -> 190.104.197.27, 200.70.32.26, 201.216.193.132
                                    TCP 443 -> timeout sur chaque IP essayée
www.argentina.gob.ar                TCP 443 -> ouvert
cemla.com                           TCP 443 -> ouvert
```

**Le nom résout, les machines ne répondent pas.** Ce n'est ni un WAF, ni un 403, ni un blocage
géographique : il n'y a pas de poignée de main. Et les deux témoins de contrôle — le guichet
`argentina.gob.ar` et le CEMLA — répondent depuis la même machine à la même seconde, **donc ce
n'est pas le réseau d'ici**.

⚠️ **Ça ne prouve toujours pas que le service est supprimé.** Un ministère argentin peut être
derrière douze jours de panne ou de migration. *La signature d'un service injoignable n'est pas
celle d'un service mort* — mais **le guichet humain, lui, est debout**, et c'est par là qu'on passe
en attendant.

**QUAND IL RÉPONDRA, LE MODULE EST À ÉCRIRE** : les deux points d'entrée sont ci-dessus, les
paramètres aussi, et `agn` est déjà au registre avec `moteur: null, module: null` — il n'y a qu'à
les remplir. Ne pas écrire le module à l'aveugle : on ne code pas contre une API qu'on n'a jamais
vue répondre.

**CE QU'IL FAUT LUI DEMANDER QUAND IL RÉPONDRA** : `barconombre=ADRIA&anioDesde=1885&anioHasta=1885`
et `barconombre=UMBERTO&anioDesde=1890&anioHasta=1890`. La liste manuscrite porte la colonne
« observaciones » — **billet prépayé, donc quelqu'un qui attend sur place** — et elle nomme les
autres passagers du même bord. C'est ce qui prouverait une chaîne migratoire, et le buscador du
CEMLA ne le rend pas.

---

## 🎖️ MÉMOIRE DES HOMMES — les JMO de 14-18, et **le domaine a changé**

Portail du ministère des armées : **journaux des marches et opérations** de 14-18 (série
**26 N**, ~18 000 journaux, 1,5 million de pages), morts pour la France, fusillés,
historiques régimentaires, sépultures de guerre, registres de l'inscription maritime.

> ### ⛔ L'ANCIENNE ADRESSE EST MORTE, ET C'EST ELLE QUE RENDENT TOUS LES MOTEURS
>
> `www.memoiredeshommes.SGA.defense.gouv.fr` — celle des forums, des articles de presse
> généalogique, et de `data/ou-chercher.md` jusqu'au 8 septembre 2026 :
>
> - **certificat TLS expiré le 20 novembre 2025** (`curl` : `SEC_E_CERT_EXPIRED`) ;
> - **403 Forbidden sur TOUTE URL du domaine**, racine comprise, même avec un vrai Chrome
>   fenêtré et `ignoreHTTPSErrors`.
>
> Ce n'est pas un WAF : **le site est mort à cette adresse.** La Wayback Machine le
> confirme — dernier 200 le 1er octobre 2025, puis 403 à chaque passage. *Deux symptômes
> qui vont ensemble — un certificat périmé depuis des mois ET un 403 uniforme — disent un
> domaine abandonné, pas une défense.*
>
> ### ✅ **`https://www.memoiredeshommes.defense.gouv.fr`** — sans le `sga`
>
> Répond **200 à une requête Python nue**. Ni WAF, ni jeton anti-robot, ni compte.

| | |
|---|---|
| **Moteur** | **Arkothèque** (`arkotheque` dans le HTML, instances `arko_default_…`) |
| **Module** | `scripts/archives/moteurs/memoiredeshommes.py` — `unite`, `fiche`, `vues`, `tire` |
| **Routage** | ⭐ **`/js/routing` rend les 589 routes Symfony en JSON**, chemins et paramètres compris |
| **Recherche** | `/_recherche-api/**search-simple/{id}**` — `{id}` est l'entier `id` du moteur (13 pour les JMO), pas son `refUnique` |
| **Description** | `/_recherche-api/moteur?refUnique={instance}` — rend les filtres, les modes de restitution et le total |
| **Détail** | `/_recherche-api/render-fiche/{moteur}/{fiche}/{restit}/detail/html` — cote, dates, et les deux entiers de l'image |
| **Vues** | `/_recherche-api/visionneuse-infos/{moteur}/{fiche}/{champ}/image/{idArkoFile}` — **une entrée par vue, avec son URL et la taille du master** |
| **Image** | `/_recherche-images/show/{idFiche}/image/{idArkoFile}/{rang}**?size=full**` — rang à partir de **0** |
| **Résolution** | JMO : **2282 × 1638** en double page avec `?size=full` ; **2000 px sans**, soit deux tiers de l'information perdus |

### Les quatre pièges payés le 8 septembre 2026

**① `/moteur` NE CHERCHE PAS, IL DÉCRIT.** `arkotheque.py` lit les résultats dans
`resultats.html` de cet endpoint : vrai à l'AD49, **faux ici**. Le même appel rend le bon
`total` — donc les filtres marchent — mais `count` reste à 0 et `html` vide. On croit à un
filtre cassé alors qu'il ne fait que compter. C'est `search-simple/{id}` qui rend les fiches.

**② UNE FICHE N'EST PAS UN DOCUMENT.** L'inventaire est un arbre EAD : une réponse mêle les
nœuds (« 55e régiment d'infanterie ») et les feuilles (« J.M.O. - 24 février 1917-9 octobre
1918 - 26 N 644/16 »). Le drapeau **`dernierNiveau`** distingue les deux ; seules les feuilles
portent des vues.

**③ LE 503 N'EST PAS UNE PANNE, C'EST UNE IMAGE PAS ENCORE FABRIQUÉE.** La première demande
d'une vue jamais servie rend **503 avec 115 ko de page d'erreur** ; la même URL, quelques
secondes plus tard, rend le JPEG. Un tireur qui abandonne au premier 503 conclut que le
journal n'est pas en ligne — **et ces vues-là sont justement celles que personne n'a encore
ouvertes, donc exactement celles qu'on vient chercher.** Sept essais, attente doublée.

**④ UNE TAILLE INVENTÉE REND DU HTML, SANS ERREUR HTTP.** `?size=!4000,4000` rend 3 ko de
page. Toujours vérifier l'octet de tête `\xff\xd8` avant d'écrire un fichier.

### Lire un JMO

Une vue est une **double page** paysage : deux colonnes « DATES | HISTORIQUE DES FAITS ».
`nas.py` la coupe en G et D par défaut ; `NAS_ENTIER=1` rend les deux d'un coup, et à
1990 px c'est déjà lisible. La colonne DATES est **souvent vide** — le scribe ne la remplit
qu'au changement de jour, et le récit d'une journée de combat court sur cinq ou six vues sans
qu'aucune date reparaisse. **Dater un JMO se fait donc par remontée**, pas par balayage.

**⭐ LES PAGES « ENCADREMENT DU RÉGIMENT AU <date> » SONT LA MEILLEURE PIÈCE DU VOLUME** :
un tableau nominatif de tous les officiers, bataillon par bataillon et compagnie par
compagnie, dressé après chaque gros engagement. Deux états encadrant une bataille donnent, en
une image, qui commandait quoi, qui est mort et qui est resté — **c'est le contrôle de cohorte,
appliqué à un régiment.**

### Les autres moteurs du portail

Relevés le 8 septembre 2026, à ajouter à `MOTEURS` du module en même temps qu'on les ouvre :
`arko_default_66faadcbce66f`, `arko_default_670f920646a08`, `arko_default_66f28af5b7b22`
(fusillés), `arko_default_66f5333ac7318`. Chacun se décrit par `/_recherche-api/moteur`.

---

## 🇫🇷 FRANCEARCHIVES — le portail national, et la porte de service des portails défendus

*Ouvert pour de bon le 18 septembre 2026, en cherchant l'entreprise de Benigno PERESSON à
Toulouse et à Perpignan.*

### ⭐ TROUVER LA COTE D'UN NOTAIRE — payé le 24 septembre 2026, et c'est une porte neuve

**Le problème** : un acte d'Ancien Régime cite « reçu Me UNTEL, notaire royal à X », et il faut
la cote pour commander en salle. L'état général des notaires d'un département donne la **cote de
la liasse** — `3 E 529` — mais une liasse porte vingt notaires, et un magasinier demande **le
numéro qui suit**. Le moteur notarial de l'AD43 n'a jamais répondu ; ce sont les inventaires
versés à FranceArchives qui l'ont donné.

**La requête est le seul nom du notaire.** Le fonds s'appelle « Minutes et répertoires
notariaux », et une notice porte la cote complète et les dates extrêmes :

```
f.cherche(["PONCETON"])   ->  3 E 529/183          1638-1692   AD Haute-Loire
f.cherche(["CHASTELLE"])  ->  3 E 391/1-2, 3 E 529/112-126   1643-1700
f.cherche(["RIBEYRON"])   ->  3 E 440/1-7, 3 E 529/207       1631-1772
```

Neuf notaires de Saint-Pal-de-Chalençon ont été datés et cotés ainsi en une requête chacun.

⛔ **LE NOM D'UN NOTAIRE A DES GRAPHIES, EXACTEMENT COMME UN PATRONYME.** L'acte de 1744 écrit
**RÉBEYRON** ; la recherche sur `REBEYRON` rend **4 documents et rien en Haute-Loire**, celle sur
`RIBEYRON` rend **la cote**. Et **RIBERON** — `3 E 529/184`, 1721-1799 — est un TROISIÈME homme,
pas une variante. Une seule forme essayée fabrique un faux négatif ; trois formes proches peuvent
cacher trois études distinctes.

⛔ **ET LA COUVERTURE EST DÉPARTEMENTALE : UN ZÉRO PEUT NE RIEN DIRE DU NOTAIRE.** Me DAUVELLE,
notaire royal à **Usson-en-Forez (Loire)**, cité par deux actes de 1774 et 1775, ne sort pas —
mais **aucun fonds notarial des AD de la Loire n'est publié ici** : « Usson-en-Forez » rend 126
documents dont **un seul** aux AD42, un enregistrement sonore. **Le négatif porte sur l'index,
pas sur l'étude.** Avant d'écrire qu'un notaire n'a pas de fonds conservé, vérifier que son
département est dans l'agrégateur — une requête sur la commune suffit.

*Contre-épreuve utile : Me Jean COLOMB, notaire royal à Saint-Pal cité en 1669, est absent de
l'état général de la Haute-Loire ET de l'inventaire national, alors que le département y est
largement présent. Ce négatif-là, lui, compte.*

**LA FICHE DU SHD DISAIT « UNE REQUÊTE NUE REND 286 OCTETS, VRAI CHROME OBLIGATOIRE ». C'ÉTAIT
FAUX, ET C'EST LE MÊME TRAVERS QUE LE « MUR » DU TOKEN DE FACETTE** : une conclusion tirée de la
taille de la réponse, pas de sa lecture. Les 242 octets rendus sont un **contrôle anti-robot
ordinaire, écrit en clair** :

```html
<script>window.location.href='/redirect_<jeton>/fr/search?q=Peresson';</script>
```

On lit le jeton, on redemande cette URL-là avec un cookie jar, et la page vient — 97 ko de
résultats, sans navigateur. Deux pièges tout de même :

| | |
|---|---|
| **TLS** | ⛔ → ✅ **RÉPARÉ LE 18 SEPTEMBRE 2026, ET CE N'ÉTAIT PAS LE SITE.** Ce portail a été accusé, comme `culture.gouv.fr`, `data.gouv.fr` et Wikipédia : la cause est **le magasin de racines de Windows servi à Python**, qui porte une racine périmée. `scripts/archives/tls.py` le répare pour tout le processus — un `import tls` suffit, et la vérification est rétablie |
| **Redirection** | la première réponse est le `<script>` ci-dessus ; suivre le chemin, sur le même opener |

### ⛔ ET LE PIÈGE QUI REND UN FAUX ZÉRO PARFAITEMENT CRÉDIBLE

**N'AJOUTER AUCUN PARAMÈTRE « RAISONNABLE ».** `sort=`, `per_page=50` et `es_cw_etypes=` — trois
paramètres vides, copiés de l'allure d'un moteur de recherche ordinaire — font répondre
**« Les paramètres de la requête ne donnent aucun résultat »** sur une requête qui rend 21
documents sans eux. Et **le filtre par service `es_publisher=Archives départementales de la
Haute-Garonne` rend « Aucun résultat » sur une requête dont la FACETTE de la même page annonce
2 résultats pour ce service**. C'est la variante FranceArchives du piège `REch_commune` de
l'AD16 : le nom du champ ne se devine pas.

**Donc : `?q=<termes>&page=<n>`, rien d'autre, et on trie à l'œil.** La colonne « Lieux de
conservation » du panneau de facettes, elle, est fiable pour savoir *où* sont les réponses.

### ⭐ LE MODULE EXISTE DEPUIS LE 18 SEPTEMBRE 2026 — `scripts/archives/moteurs/francearchives.py`

La recette ci-dessus était écrite et le code nulle part : chaque session le refaisait en
`urllib`, dans un one-liner. Le module franchit le contrôle anti-robot, tient la session à
cookies, et sert **trois fonds** :

```bash
python francearchives.py cherche "Peresson"            # les inventaires
python francearchives.py noms Migot --prenom Pietro    # la base de noms
```

### ⭐⭐ LA BASE DE NOMS EST UN AUTRE MOTEUR, SUR UNE AUTRE URL, AVEC D'AUTRES CHAMPS

`/fr/basedenoms` — **430 992 353 lignes nominatives** versées par les AD : recensements,
registres matricules, état civil, morts pour la France. Chaque fiche porte un **badge** qui dit
son type.

⛔ **`?q=Peresson` Y EST IGNORÉ EN SILENCE ET REND LES QUATRE CENT TRENTE MILLIONS DE LIGNES** —
une page qui ressemble parfaitement à un résultat. Les champs s'appellent **`es_names`**,
**`es_forenames`**, **`es_locations`**, `es_date_min`, `es_date_max`, et ils se **lisent sur le
formulaire**. C'est le piège `REch_commune` de l'AD16, une troisième fois. *Le contrôle qui ne
ment pas : comparer le total à celui d'une requête sans filtre.*

⭐ **ET ELLE S'EXPORTE EN CSV, CE QUI VAUT MIEUX QUE DE GRATTER LES PAGES** :
`/fr/basedenomsexport/export.csv?es_names=…`, mêmes paramètres, jusqu'à 10 000 lignes en une
requête, **dix colonnes dont la PROFESSION et le LIEN VERS LE DOCUMENT NUMÉRISÉ** — deux
informations qui ne sont nulle part sur la page de résultats.

⛔ **LE MOT « RÉSULTATS » FIGURE AUSSI DANS L'AIDE DE LA PAGE, AVEC UN NOMBRE.** Un `re.search`
sur « N résultats » rend **10 000** sur une requête qui n'a rien trouvé — l'aide dit « il est
possible d'exporter jusqu'à 10 000 résultats ». On a lu « 10000 lignes annoncées, 0 lue » pour
PEDIRODA avant de s'en apercevoir. Le compte se lit dans le `<span>` du titre ; le zéro se
reconnaît à **sa** phrase, « Aucun résultat correspondant à votre recherche n'a été trouvé » —
et cette phrase-là figure elle aussi dans l'aide, donc on la lit **après** avoir cherché le
compte, jamais avant.

*Mesuré le 18 septembre 2026 : PEDIRODA rend zéro partout — inventaires, base de noms, Sûreté
nationale. MIGOT ne rend, dans la base de noms, que des recensements et des matricules, aucun de
Haute-Garonne après 1911. **Une base de noms est un index de dépouillements, pas un fonds** : un
zéro n'y prouve rien.*

### Ce que ça sert vraiment

- **Les inventaires de presque toutes les AD**, y compris ceux que le portail départemental
  cache derrière un WAF — l'AD31 y publie 1 619 inventaires et 354 284 notices.
- ⭐ **L'index nominatif des décrets de naturalisation des Archives nationales** : les notices
  y viennent avec date de naissance, lieu de naissance, profession, résidence et **le numéro
  de dossier BB/11**. Voir la fiche « Naturalisations » ci-dessous.
- Les dossiers du **Fichier central de la Sûreté nationale** (`19940469/…`), qui indexe
  nominativement des étrangers surveillés dans les années 1930.
- **La base Leonore** (Légion d'honneur) et les **dossiers AC 21 P** de Caen.

### ⚠️ MAIS UN MOTEUR D'INVENTAIRE LIT DES DESCRIPTIONS, PAS DES DOSSIERS

Règle déjà écrite pour l'AD31 dans `portails.json`, et re-vérifiée ici : une série décrite
« dossiers individuels classés par ordre alphabétique » ne rendra **jamais** un patronyme. **Le
tribunal de commerce de Toulouse en est le cas d'école** — 17 lignes de versement pour
1825-2016, aucun nom — **alors que l'AD06 a versé le sien à l'article**, et qu'on y lit
« Péresson Jean-Baptiste, travaux publics, Nice (n° 24580) ». Deux départements, même série,
deux profondeurs de description : **un zéro ne dit rien tant qu'on n'a pas regardé à quelle
maille l'inventaire descend.**

---

## 🇫🇷 LES NATURALISATIONS — trouver le décret, puis le dossier

*Ouvert le 18 septembre 2026. C'est la pièce la plus riche qui existe sur un étranger installé
en France : profession, adresses successives, composition de la famille, et souvent une enquête
de police.*

### ⓪ ⛔ AVANT DE CHERCHER UN DÉCRET, VÉRIFIER QU'IL EN FAUT UN

**C'est la faute la plus coûteuse de tout ce dossier, parce qu'elle fabrique un négatif de
plusieurs milliers de numéros de JO sur une pièce qui n'a jamais existé.** « Devenir français »
et « être naturalisé » ne sont pas la même chose : il y a **trois voies**, et **une seule
laisse une trace au *Journal officiel***.

| Voie | Texte (code de la nationalité, ordonnance du 19 octobre 1945) | Publiée au JO ? | Où est la trace |
|---|---|---|---|
| **Naturalisation par décret** | art. 64 et s. | ⭐ **OUI** | JO, puis dossier BB/11 aux AN |
| **Déclaration** (art. 55 et s.) | enregistrée au ministère de la Justice | **NON** | registre des déclarations, ministère de la Justice ; mention en marge de l'acte de naissance |
| **De plein droit, par l'effet de la loi** | art. 37 (mariage), art. 84 (effet collectif) | **NON** | **aucun acte nominatif** — seul un **certificat de nationalité française** la constate |

**⚠️ ET LA FEMME ÉTRANGÈRE QUI ÉPOUSE UN FRANÇAIS ENTRE 1945 ET 1973 N'A RIEN À DEMANDER.**
Article 37 : « **La femme étrangère qui épouse un Français acquiert la nationalité française au
moment de la célébration du mariage.** » C'est automatique. Elle pouvait seulement **décliner**
avant la noce (art. 38) si sa loi nationale lui laissait sa nationalité d'origine ; et le
gouvernement pouvait **s'y opposer par décret dans les six mois** (art. 39) — *cette
opposition-là, elle, paraît au JO : c'est le seul motif d'y chercher son nom.* La règle vaut de
l'ordonnance de 1945 à la **loi du 9 janvier 1973**, qui supprime la distinction entre les sexes.

**ET L'EFFET COLLECTIF SUR L'ENFANT MINEUR NE LAISSE PAS DAVANTAGE DE PAPIER.** Article 84,
rédaction initiale de 1945 : « Sous réserve que sa filiation soit établie conformément à la loi
civile française, devient de plein droit Français : 1° l'enfant mineur légitime ou légitimé
**dont le père ou la mère, si elle est veuve**, acquiert la nationalité française ; 2° l'enfant
mineur naturel dont celui des parents à l'égard duquel la filiation a été établie en premier
lieu ou, le cas échéant, dont le parent survivant acquiert la nationalité française. »

> **La condition « si elle est veuve » est le piège de cet article, et elle décide de tout.**
> Pour un enfant légitime, l'acquisition par **la mère** ne produit d'effet collectif **que si
> elle est veuve** — pas si elle est divorcée, pas si le père vit. *(Ces mots ont été déclarés
> contraires à la Constitution le 25 avril 2024, décision n° 2024-1086 QPC ; la loi du 9 janvier
> 1973 les avait déjà supprimés pour l'avenir, sans effet rétroactif.)*

**Et le dernier alinéa du même article dit où s'arrête l'exigence de mention** : « les
dispositions du présent article ne sont applicables à l'enfant d'une personne qui acquiert la
nationalité française **par décision de l'autorité publique ou par déclaration de nationalité**
que si son nom est mentionné dans le décret ou dans la déclaration ». Une acquisition **par
mariage** n'est ni l'une ni l'autre : **l'enfant est français sans être nommé nulle part.**
*Chercher son nom dans un décret, c'est alors chercher une pièce que la loi n'a pas prévue.*

**Ce qu'on demande à la place, pour ces deux voies** : un **certificat de nationalité française**
(CNF), délivré par le **service de la nationalité des Français nés à l'étranger**, pôle du
tribunal judiciaire de Paris, pour qui est né hors de France ; ou par le tribunal judiciaire du
domicile. Et, en amont, **la copie intégrale de l'acte de mariage**, qui porte les mentions
marginales.

### ⓪ bis ⭐⭐ LE RACCOURCI QUI VAUT POUR LES TROIS VOIES : L'ACTE DE NAISSANCE FRANÇAIS

**Quelle que soit la voie — décret, déclaration ou plein droit —, celui qui est né à l'étranger
et devient français reçoit un ACTE DE NAISSANCE FRANÇAIS**, dressé par le **service central
d'état civil** (SCEC) du ministère de l'Europe et des Affaires étrangères, à Nantes. **Et c'est
en marge de cet acte qu'est inscrit LE MODE ET LA DATE de l'acquisition.** Une copie intégrale
répond donc à la question sans passer ni par le *Journal officiel*, ni par Pierrefitte, ni par un
tribunal.

| | |
|---|---|
| **⭐ Où la déposer** | **<https://demarches.service-public.gouv.fr/mademarche/demarcheGenerique/?codeDemarche=delivrance_demat>** — c'est le formulaire, et `etat-civil.diplomatie.gouv.fr` ne fait que rediriger dessus |
| **Par courrier** | SCEC, 11 rue de la Maison Blanche, 44941 Nantes Cedex 09 |
| **Coût** | **gratuit**, comme toute délivrance d'acte d'état civil |
| **Qui y a droit** | l'intéressé, ses **ascendants**, ses **descendants**, son conjoint — c'est le décret du 6 mai 2017, art. 30, et il n'a **pas** d'exception d'ancienneté |
| **Ce qu'on demande** | **copie intégrale, avec mentions marginales** — un extrait sans filiation ne dit rien |

> **C'est le raccourci du descendant direct appliqué à la nationalité** : un fils ou un
> petit-enfant obtient en quelques minutes, gratuitement, ce qu'un chercheur tiers n'obtiendra
> jamais. **Avant de monter une demande d'archives, regarder qui, dans la famille, peut la
> faire.**

### ① Où le décret est PUBLIÉ

| Période | Publication |
|---|---|
| avant 1924 | **Bulletin des lois**, partie supplémentaire — Gallica `cb32726274t` |
| **à partir de 1924** | ⭐ **Journal officiel, Lois et décrets** — Gallica `cb34378481r` |

**Gallica ne sert le JO que jusqu'en 1955.** 1955-2006 n'existe qu'en **Gallica *intra muros***,
dans les salles de recherche de la BnF. Légifrance répond **403** à une requête nue et, pour ce
qu'on cherche ici, ne sert utilement qu'à partir de 2016.

### ② Où le décret est INDEXÉ AU NOM — et où il ne l'est pas

Les décrets originaux sont aux Archives nationales, **BB/34/387 à BB/34/511** (1883-1948),
librement communicables (art. L213-2 du code du patrimoine). Numérisés, mais **indexés
seulement en partie**, par la plateforme collaborative *Natnum* :

**⚠️ CE TABLEAU A ÉTÉ ÉCRIT FAUX UNE PREMIÈRE FOIS, LE MATIN DU 18 SEPTEMBRE 2026, ET LA FAUTE
EST INSTRUCTIVE** : il disait « 1883-1898 · 1913-1927 · 1929-1930 » parce que c'est ce
qu'annonce la page des Archives nationales, **et parce que dix patronymes frioulans n'avaient
rendu que du 1929-1930**. Deux erreurs empilées : la page de l'AN est **en retard sur son propre
chantier d'indexation**, et un échantillon de dix noms rares ne mesure pas un périmètre — il
mesure le classement par pertinence du moteur. Le lendemain, une recherche sur un tout autre nom
a fait sortir `TONEATTI, Pie — 12532 X 31 — Décrets de naturalisation de l'année **1931**`.

**Le périmètre remesuré, et par quelle méthode.** Quatre requêtes larges (« décret
naturalisation Italie maçon », « … Pologne mineur », « … Espagne cultivateur », « … Italie
manœuvre »), trois pages chacune, plus dix patronymes courants de deux pages
(ROSSI, NOWAK, GARCIA, MULLER, BIANCHI, KOWALSKI, LOPEZ, SCHMITT, FERNANDEZ, ZANELLA) :
**une centaine de notices de personnes**, dont les années de décret se répartissent ainsi :

| Années | Indexées au nom ? |
|---|---|
| 1883-1896 · 1913-1931 | **OUI** — cherchables sur FranceArchives et dans la salle de lecture virtuelle. **1928 et 1931 en font partie**, contrairement à ce qu'annonce l'AN |
| **1932-1948** | **pas une seule notice de personne n'est apparue** sur ~300 notices de décret échantillonnées, alors que 1931 en rend à foison |

**Ce que ce négatif vaut, et ce qu'il ne vaut pas.** Il dit qu'un nom cherché sur 1932-1948
ne sortira pas — donc qu'**un zéro sur ces années-là ne prouve rien**. Il ne prouve pas que
l'indexation n'y a jamais mordu : elle avance, et ce tableau se repérime tout seul.
**Le refaire avant de s'appuyer dessus**, la mesure coûte cinq minutes.

*Contrôles positifs conservés* : `Peresson, Pietro` (1929) et `Toneatti, Pie` (1931) sortent
avec leur fiche complète — si l'un des deux cesse de répondre, c'est l'outil qui a changé, pas
le fonds.

### ③ Ce que porte une notice indexée — et c'est beaucoup

> **Peresson, Pietro** — décret du **18 décembre 1929** — né le 27 octobre 1876 à
> **Vito d'Asio (Italie)** — profession : **maçon** — résidence : **Tarn-et-Garonne** —
> enfants : Maria, Domenica, Louis, Fernand — cote **4092 X 29** *(numéro du dossier à
> consulter en sous-série BB/11)*.

Numéro de dossier, nom, prénom, profession, date et lieu de naissance, résidence, épouse et
enfants. **Le numéro de dossier ouvre le dossier complet à Pierrefitte.**

### ④ Quand l'index se tait : les listes alphabétiques 1900-1979

Elles existent, **sur papier**, et ce sont elles qui donnent la date du décret quand on ne l'a
pas — établies à partir du *Journal officiel*, par tranches décennales :

- **Archives nationales, Pierrefitte, salle des microfilms** ;
- **BnF**, en salle de recherche (Gallica intra muros) ;
- et le CD-ROM « **Votre nom dans l'Histoire** » pour 1900-1960.

**À partir de 1949, le numéro de dossier figure DANS le décret** : le JO suffit alors, on n'a
plus besoin de la liste.

### ⑤ La parade à distance, et elle marche : balayer le JO sur Gallica

Le SRU de Gallica indexe la presse **au titre**, jamais au numéro : `cherche("Peresson")` ne
verra jamais un nom dans un fascicule du JO. C'est **`ContentSearch`, numéro par numéro**, qui
descend là — `gallica.dans(ark, "Peresson")`.

**Contrôle positif obtenu le 18 septembre 2026**, et il valide toute la méthode : le balayage a
rendu, au JO du 15 novembre 1936, *« PERESSON (Luigi), cultivateur, né le 24 janvier 1902 à
Méd[uno] (Italie), ayant une fille mineure, Odette-Analie, née le 10 mars 1931 à
Laroque-Timbaut (Lot-et-Garonne) »* — **les listes de naturalisation du JO sont bien
océrisées et cherchables.** Un négatif obtenu par cette voie est donc un vrai négatif, aux
fautes d'OCR près : la plage est **COUVERTE**, pas **CLOSE**.

### ⚠️ ET VOICI LA PREUVE, SUR UNE SEULE LIGNE, QU'UN NÉGATIF DE JO EST « COUVERT » ET NON « CLOS »

Le 19 septembre 2026, la **même ligne du même numéro** — JO du 8 février 1953, page 1281 —
a été **trouvée** par un balayage sur `Peresson` et **manquée** par un balayage sur `Migot`,
lancé le lendemain sur la même année :

```
ce qui est imprimé :  PERESSON, née MIGOT, Vito d'Asio (Italie), 08-12-19.
ce que l'OCR rend   :  PERESSON, n?e CdlGOT, Viio d?Asio (Ilalie), 03-12-19.
```

`MIGOT` est devenu `CdlGOT`, et la date `08` est devenue `03`. **Un seul des deux patronymes de
la ligne était cherchable.** C'est pour ça qu'on balaie **le nom le plus rare et le mieux formé**
d'abord, qu'on croise deux patronymes quand on en a deux, et qu'un compte rendu écrit
« couvert », jamais « clos ».

Coût mesuré : **environ 610 numéros par année** (le JO a plusieurs éditions par jour sur
Gallica, et deux collections numérisées qui se doublent), **3 à 4 minutes par année** à 0,33 s
par appel. 1930-1955, c'est une heure et demie sans surveillance.

⚠️ **Le même décret sort deux fois**, sous deux `ark` différents : Gallica sert deux
exemplaires du même jour. Ce n'est pas un doublon de recherche, c'est le fonds.

⚠️ **ET LA COUVERTURE DE GALLICA S'EFFONDRE APRÈS 1945.** Comptes relevés : ~615 numéros par an
de 1930 à 1945 (deux collections), puis **176 pour 1946**, 269 pour 1947, 260 pour 1948, ~310
par an ensuite. 1946 est donc **à moitié couvert** et il faut l'écrire ainsi. *Et les listes de
1954 et 1955 ont refusé de se charger après 12 358 numéros lus d'affilée : **Gallica coupe la
connexion** au-delà d'un certain volume, et il faut attendre quelques minutes. Un
`ConnectionResetError` en fin de balayage n'est pas une année vide, c'est une année non lue.*

### ⑧ LIRE UNE LIGNE DE DÉCRET — et la grammaire change en 1949

**Avant 1949**, l'entrée est une phrase : *« PERESSON (Umberto), maçon, né le 27 février 1893 à
Vito d'Asio (Italie), ayant deux enfants mineurs : 1° Gertrude, née le 17 août 1918 à Vito
d'Asio… »* — profession, filiation des enfants, domicile.

**À partir de 1949**, elle se réduit à quatre champs, et **le troisième est le numéro de
dossier** :

```
PERESSON (Benigno), Vito d'Asio (Italie), 07-08-06.  —  15218 × 52 — 31.
   nom            lieu de naissance        naissance      dossier  année  dépt
```

**Le dernier nombre est le DÉPARTEMENT, et ça se lit sur les voisins, pas sur la ligne.** Sur la
même page : `—39` (Jura), `—10` (Aube), `—06`, `—02`, `—23`, `—34`, `—81`, `—25`, `—59`, `—01`,
et `—98` pour un natif du Liban. Tous des codes valides : c'est le contrôle de cohorte appliqué
à un formulaire. *Ne pas confondre avec le nombre du milieu, qui est l'**année de la demande** —
`× 52` pour un décret de 1953 : le dossier a un an de plus que le décret.*

**Et la date du décret n'est pas sur la ligne** : elle est dans le titre du bloc, plusieurs pages
plus haut — « NATURALISATIONS ET RÉINTÉGRATIONS · Décret du 12 janvier 1953 portant
naturalisation… ». Une même livraison du JO en porte **trois ou quatre**. Pour savoir duquel
relève une ligne, chercher `Décret|Décrète|NATURALISATIONS|Art\.` sur les vues intermédiaires :
**si elles ne rendent rien, c'est que la liste court sans interruption** depuis le dernier titre.

### ⑥ Le raccourci départemental, moins connu et plus rapide

**L'AD31 tient les « fichiers alphabétiques des demandes de naturalisation, 1939-2005 »**
(inventaire « Nationalités », 1897-2016) : numéro de dossier, nom, prénom, date de naissance,
nationalité, adresse, date de dépôt, **et le plus souvent une photographie d'identité**. La
notice de l'AD31 le dit elle-même : **ici on trouve le NUMÉRO, à Pierrefitte le DOSSIER.**
Beaucoup d'AD ont l'équivalent. Une lettre au service départemental coûte moins qu'un balayage
de vingt ans de *Journal officiel*.

### ⑦ Demander le dossier

Tout passe par la **Salle de lecture virtuelle** des Archives nationales
(`https://www.siv.archives-nationales.culture.gouv.fr/siv/`), depuis un espace personnel à
créer. À partir de 1832 la communication se fait **par extrait** — le dossier est sorti du
carton, donc en différé : **attendre impérativement la réponse du département Justice et
Intérieur avant tout déplacement.** Le dossier reste 21 jours en salle.

| | |
|---|---|
| **Communicabilité** | libre à l'expiration des délais de L213-1 et L213-2 — un dossier des années 1930-1950 est ouvert |
| **Reproduction** | **18 € par dossier** (naturalisation par décret), **7 €** (par déclaration), à demander depuis l'espace personnel de la SLV |
| **Sur place** | photographie sans flash autorisée, donc gratuite |
| **Dossiers non aboutis** | pas de décret, donc pas d'index : demande de recherche dans la SLV, **en précisant l'année de la demande** |

*Fiche de recherche officielle : `siv.archives-nationales.culture.gouv.fr/siv/cms/content/helpGuide.action?uuid=804c95a9-6550-4b00-b97b-78b0d52816cd`*

---

## AD31 — Haute-Garonne · moteur **Boscop / Ligeo**, derrière **Anubis**

*Reconnu le 7 septembre 2026, ouvert le 18 septembre 2026. ⚠️ **Ce n'est PAS le fonds de
l'état civil de Toulouse** — la ville a ses propres Archives municipales, fiche plus haut.*

| | |
|---|---|
| **Portail** | <https://archives.haute-garonne.fr> |
| **Moteur** | **Boscop / Ligeo-Archives**, il le dit dans son `<meta name="Generator">` |
| **WAF** | **Anubis**, franchi en 3 à 18 s par un Chrome réel — `lire_page.js` suffit |
| **⭐ `ark_prefixe`** | **`ark:/44805/`** — la fiche disait « il manque seulement l'ark_prefixe », le voici |
| **Contact** | `archives@cd31.fr` · 05 34 32 50 00 · 11 boulevard Griffoul-Dorval, 31400 Toulouse |
| **Salle** | lundi 13 h-17 h, mardi au vendredi 8 h 30-17 h — *et le vendredi ferme à 13 h depuis 2026* |

### ⭐ LES RECENSEMENTS D'APRÈS-GUERRE SONT EN LIGNE — 1954, 1962, 1968, 1975

*Vérifié le 19 septembre 2026, et c'est un réflexe à casser.* Le libre accès s'arrête à
**1936**, ce qui fait conclure « soixante-quinze ans, donc rien après » et refermer la piste.
Faux : **quatre années supplémentaires sont numérisées et consultables à distance**, derrière
un compte certifié — `/archive/recherche/recensement/n:114` le dit en toutes lettres.

Ces fichiers sont **librement communicables au regard du Code du patrimoine** ; ce qui est
interdit, c'est leur **diffusion** en ligne, au titre du décret n° 2018-1117 du 10 décembre
2018 (art. D. 312-1-3 du CRPA) et de l'article 8 de la loi Informatique et Libertés.
L'accès réservé est la voie réglementaire, pas une faveur — et la même logique vaut sur tout
portail qui affiche une icône d'accès réservé.

| | |
|---|---|
| **Aussi en accès réservé** | arrêts des juridictions d'exception 1939-1945 · fichiers nominatifs d'internés · index et inventaires nominatifs · fonds privés de photographies |
| **Les trois étapes** | ① compte personnel sur le site · ② validation par le lien reçu par courriel *(voir les indésirables)* · ③ formulaire `/wform/wform/fill/demande_accesreserve/n:396` + pièce d'identité en cours de validité (passeport tous pays, ou CNI de l'UE recto-verso) |
| **Délai** | **dix jours ouvrés**. Valable un an, renouvelé tant qu'on se connecte ; sans connexion pendant un an, tout est à refaire, pièce d'identité comprise |
| **Téléchargement** | autorisé pour un usage privé — pas de rediffusion en ligne des données personnelles |

⚠️ **Le nom et le prénom de la demande doivent être identiques à ceux du compte**, sinon le
département rejette sans discuter.

⛔ **Trois murs que l'accès réservé ne franchit pas** : ① **aucun acte d'état civil de moins
de cent ans n'est numérisé**, le compte n'y change rien ; ② **les recensements de 1946 n'ont
pas été conservés** en Haute-Garonne — inutile de les chercher ; ③ **Toulouse n'est pas dans
ce fonds** : ses listes nominatives à partir de 1921 sont aux Archives municipales de la
ville. Les communes de la périphérie — L'Union, Tournefeuille, Montréjeau — sont bien à
l'AD31.

#### La recherche est un formulaire en GET — donc une URL

*Relevé le 19 septembre 2026, et ça vaut pour tout portail Boscop.* Pas besoin de piloter un
formulaire : le champ caché `RECH_lieux_Index` n'est pas nécessaire, le libellé en clair suffit.

```
/archive/recherche/recensement/n:114?RECH_lieux=<commune>&RECH_unitdate_debut=<a>
                                    &RECH_unitdate_fin=<b>&type=recensement
```

Chaque résultat porte un lien `/archive/fonds/<FONDS>/view:<id>/n:114` et un `ark:/44805/…`.
`lire_page.js --html` récupère les deux d'un coup — c'est ainsi que les deux cotes ci-dessous
ont été trouvées sans compte, l'inventaire étant public même quand les images ne le sont pas.

⚠️ **L'indexation collaborative des noms ne monte que jusqu'à 1921.** Les champs `collab-nom`,
`collab-nomepouse`, `collab-prenom`, `collab-rue`, `collab-profession` ne servent à rien sur
1954-1975 : ces années-là se lisent à l'œil, commune par commune.

⛔ **Et on ne force pas les images réservées.** L'inventaire se lit, les scans non. Le décret
encadre précisément leur diffusion ; le compte est la voie, et il est nominatif.

*Ce que le dossier y cherche : **quand Irma MIGOT et Roger SOULIÉ ont quitté Montréjeau pour
Toulouse**, entre leur mariage du 12 novembre 1955 et l'été 1963. **Fonds `1925 W`** —
L'Union 1962 = `view:618739` (arrondissement de Toulouse, canton de Toulouse-Centre),
Montréjeau 1962 = `view:618188` (arrondissement de Saint-Gaudens, canton de Montréjeau).
⛔ **1954 n'est numérisé pour aucune des deux**, la série saute de 1936 à 1962 : un seul
document tranche, celui de 1962. L'Union s'arrête à 1968, Montréjeau va jusqu'à 1975.*

### ⭐ LE MANIFESTE IIIF PASSE ANUBIS, LA PAGE NON

Trouvé le 18 septembre 2026, et ça vaut d'être essayé sur tout portail Boscop défendu :

```
/ark:/44805/<id>                       -> 4 569 octets de défi Anubis
/ark:/44805/<id>/manifest              -> 200, JSON IIIF complet, sans navigateur
/archive/download?file=<url encodée>   -> 4 138 octets de défi Anubis
```

Le manifeste rend le titre, la cote, **toutes les métadonnées de la notice** et l'URL de chaque
vue. Seul le **téléchargement de l'image** reste derrière le mur — donc `boscop.js` pour les
images, `urllib` pour tout le reste. *C'est l'application de la règle « lire la réponse en
entier avant de deviner une URL », à l'envers : ici c'est le chemin normalisé qui n'était pas
gardé.*

### Le registre du commerce — **ce qu'on cherche pour une entreprise toulousaine**

Inventaire **« W - Tribunal de commerce de Toulouse, Muret et Villefranche-de-Lauragais »**
(1825-2016, identifiant `FRAD031_TC_TLSE_EV`), `ark:/44805/vta613b980d0eef38e9` :

| Cote | Contenu | Dates |
|---|---|---|
| ⭐ **2396 W 1-277** | **Registre du commerce, déclarations aux fins d'immatriculations et de modifications** — *registres chronologiques **et analytiques***, 18 m.l. | **1920-1954** |
| 8178 W 1-28 | Registre du commerce et des sociétés, **immatriculation des commerçants** (dossiers) | 1954-1968 |
| 8179 W 1-365 | idem, **sociétés commerciales**, 45 m.l. | 1954-1977 |
| 6 U | le reste — la notice de 2396 W signale « des articles à réintégrer dans la sous-série 6U » | — |
| 6 U 2 260-333 | même chose pour le **tribunal de commerce de Saint-Gaudens** | — |

**⛔ L'INVENTAIRE NE DESCEND PAS À L'ARTICLE, ET LE NÉGATIF EST DE CETTE NATURE-LÀ.** Dix-sept
lignes de versement pour deux siècles, aucun nom : une recherche nominative sur ce fonds rendra
toujours zéro, **quel que soit le nom**. Vérifié le 18 septembre 2026 sur FranceArchives et sur
le portail lui-même. La seule voie est d'**écrire au service** en citant la cote.

*Ce qui est « numérisé » sous 2396 W est **le bordereau de versement**, une seule image — pas
les 277 registres. Ne pas annoncer un fonds en ligne sur la foi d'un bouton « Consulter le
document numérisé ».*

### Ce que le dossier y cherche encore

- **6 M 283** — *Relevé nominatif des Italiens recensés dans les arrondissements*.
- **Fichiers alphabétiques des demandes de naturalisation, 1939-2005** — voir la fiche
  Naturalisations ci-dessus.
- Dossiers individuels de naturalisation : **1724 W 1-7** (jusqu'à 1955), **1726 W 1-6**
  (1900-2016), **8243 W** (1930-2016).
- **1 M 690** (étrangers suspects et associations, 1920-1940), **1 M 686-69x** (surveillance).

---

## 📰 CE QUI EST EN LIGNE DE LA PRESSE DE TOULOUSE ET DE PERPIGNAN

*Mesuré le 18 septembre 2026, parce qu'on cherchait une entreprise de maçonnerie entre 1936
et 1965 et qu'il fallait savoir où s'arrêtaient les fonds numérisés.*

| Titre | ark Gallica | Couverture | Balayé « Peresson » |
|---|---|---|---|
| **La Dépêche** (Toulouse) | `cb327558876` | 1874-**1944**, 24 819 numéros | 1936-1944, 2 748 numéros → **6 occurrences** |
| **Le Midi socialiste** (Toulouse) | `cb32815893g` | 1908-**1944** | c'est lui qui porte les publications de mariage de 1939 |
| **Le Roussillon** (Perpignan) | `cb328630151` | 1870-**1944**, hebdomadaire | 1936-1944, **370 numéros, ZÉRO** |
| **L'Indépendant** (Perpignan) | — | **pas sur Gallica** pour l'après-guerre ; BnF microfilm **1975-2003** seulement | — |

**AUCUN TITRE DES DEUX VILLES NE DÉPASSE 1944 EN LIGNE.** Toute la période perpignanaise
(1952-1965) est donc hors d'atteinte à distance : *L'Indépendant* de ces années-là se lit
**aux AD66 ou à la Médiathèque de Perpignan**, sur microfilm.

### Et il n'y a AUCUN annuaire du commerce de ces deux départements sur Gallica après 1930

Cherché le 18 septembre 2026 au catalogue, en locution exacte : « Annuaire de la
Haute-Garonne » (1862-1880 seulement), « Annuaire des Pyrénées-Orientales » (rien), « Annuaire
de Perpignan » (**0**), « Annuaire général du Roussillon » (**0**), « Indicateur toulousain »,
« Annuaire du commerce de Toulouse », « Didot-Bottin » et « Annuaire officiel des abonnés au
téléphone » filtrés sur 1930-1965 — **aucune série des deux départements.** Le plus tardif est
le *Nouvel annuaire général de la Haute-Garonne*, `cb32825973b`, qui s'arrête en **1930**.

⭐ **La collection qui existe vraiment est ailleurs, et elle est complète** :

> **Bibliothèque historique des postes et des télécommunications (BHPT)**
> 89-91 rue Pelleport, 75020 Paris · 01 53 39 90 81 · `bhpt.org/annuaires`
> *Annuaire officiel des abonnés au téléphone, **1880-2018**, Paris **et province**, imprimé et
> microfilm. Consultation sur rendez-vous, du lundi au vendredi 9 h 30-17 h 30. Photocopies
> payantes par correspondance.*

C'est là que se lit « PERESSON, entrepreneur » à son adresse de Toulouse puis de Perpignan,
année par année — **et c'est la seule source qui date un déménagement d'entreprise sans passer
par un greffe.**

---

## AD95 — Val-d'Oise · moteur **Boscop / Ligeo-Archives**, derrière **Anubis**

*Ouvert le 18 septembre 2026, en poursuivant la branche parisienne des MIGOT.*

| | |
|---|---|
| **Portail** | <https://archives.valdoise.fr> |
| **Moteur** | **Boscop / Ligeo-Archives**, il le dit dans son `<meta name="Generator">` |
| **WAF** | **ANUBIS** — 4 207 octets de défi, titre « Making sure you're not a bot! », la même page quelle que soit l'URL. **Franchi en 3 s** par `lire_page.js` ; le profil persistant fait que seule la première page paie |
| **Préfixe ark** | **`ark:/18127/`**, forme `vta…` |
| **Compte** | aucun |

### Le fonds qui nous intéresse : les RECENSEMENTS

| | |
|---|---|
| **Formulaire** | `/archive/recherche/RecensementsPopulation/n:420` |
| **Résultats** | `/archive/resultats/RecensementsPopulation/lineaire/n:420/page:{n}?type=RecensementsPopulation&RECH_Commune={commune}` |
| **Commune** | **`RECH_Commune`, capitale C** — le libellé nu suffit, « Sannois ». *Le formulaire porte aussi `_Index` et `_Libel`, cachés : ne pas s'en soucier.* |
| **Pagination** | `page:2` **dans le chemin**, vingt notices par page |

⛔ **LES DEUX FILTRES DE DATE NE FILTRENT PAS — ILS VIDENT.** `RECH_AnneeExacte=1936` et le couple
`RECH_Unitdate_debut`/`RECH_Unitdate_fin` rendent **zéro réponse** sur une commune qui en a
vingt-cinq sans eux. Ce ne sont pas des paramètres inventés, ils sont sur le formulaire — et ils
ne marchent pas en GET. **On prend les vingt-cinq et on lit les années dans les notices**, qui les
portent en clair sous la cote : `9 M 889 - 1817`, `9 M 893 - 1931`.

*Le contrôle qui valide le filtre de commune : une requête sans critère rend le formulaire nu
(31 701 octets, aucune réponse), « Sannois » en rend 25. Le filtre filtre.*

### ⭐⭐ MAIS LA BONNE PORTE N'EST PAS CE PORTAIL — C'EST L'INDEX NOMINATIF

**Le Val-d'Oise a versé ses dépouillements de recensements à la base de noms de FranceArchives**,
et `francearchives.py noms <NOM> --lieu <commune>` rend en une requête ce qu'un dépouillement par
rue coûterait des heures à trouver. Mesuré le 18 septembre : `Migot --lieu Val-d'Oise` rend
**quatorze lignes**, dont les cinq du ménage de Sannois en 1931, **avec leur profession**.

### ⭐⭐⭐ ET LA NOTICE HTML PORTE LA PAGE ET LA LIGNE — LE CSV NE LE DIT PAS

**C'est la clef de tout, et elle a été trouvée après coup.** L'export CSV donne dix colonnes et
renvoie, pour « le document numérisé », à la page de recherche du portail — inutilisable. **La
page HTML de la notice, elle, porte huit champs de plus :**

> Naissance **1894 ; Paris** · Lien avec le chef de ménage **chef** · Profession (source)
> **vaçon** · Nationalité **française** · **Page et position de la ligne dans le recensement :
> 240 ; 2** · *Voir les autres membres du ménage : Migot Mathilde, épouse ; Migot Joséphine,
> fille*

**« Page » est le NUMÉRO DE VUE**, vérifié le 19 septembre 2026 : la vue 240 du registre de
Sannois porte le folio 239, et c'est bien à la vue 240 qu'est la ligne annoncée page 240. *Un
registre de 390 vues sans index se réduit alors à quatre pages.* Et **« les autres membres du
ménage » donnent la composition du foyer avant même d'ouvrir l'image.**

⛔ **MAIS C'EST UNE TRANSCRIPTION PAR IA, ET ELLE SE TROMPE — MESURÉ SUR CETTE LIGNE-LÀ.** Le
projet **SocFace** a transcrit ces recensements automatiquement, et la notice le dit en bas de
page. Sur la ligne 7142 de Sannois, l'index annonce « né en 1894 à **PARIS**, nationalité
**FRANÇAISE** » ; le registre écrit **CLAUZETTO** et **ITALIEN**. Trois erreurs sur une ligne.
Pire, une des cinq entrées **n'existe pas** : le « MIGOT Victorie » de la vue 259 est en réalité
un PERESSINI, et sa « nationalité polonaise » vient de la ligne suivante, un BURIANEK.

> **L'index dit OÙ REGARDER ; il ne dit pas CE QUI EST ÉCRIT.** On y prend la page et la ligne,
> puis on lit l'image — et on ne verse jamais un champ de l'index sans l'avoir vu sur le
> registre.

⚠️ **Et ce que l'index ne donne pas non plus** : la rue, le numéro de ménage, et les voisins —
qui sont souvent ce qui compte. C'est en ouvrant la vue 240 qu'on a vu que les MIGOT de Clauzetto
avaient pour voisins de palier des FABRIS et des ZANNIER de Clauzetto, tous maçons.

### Ce que le dossier y cherche

- **Sannois 1931, `9 M 893`, `ark:/18127/vta520275a56599f`** — le ménage MIGOT : Francesco-Alberto,
  Mathilde, Joséphine, et deux Vittorio. **Le registre n'a pas été ouvert.**
- **Soisy-sous-Montmorency 1926** — « MIGOT Lugi, menuisier », à trois kilomètres d'Eaubonne.
- **La série de Sannois s'arrête à 1931** en ligne : 1817, 1831, 1836, 1841, 1846, 1851, 1856,
  1861, 1866, 1872, 1876, 1881, 1886, 1891, 1896, 1901, 1906, 1911, 1921, 1926, 1931. *Pas de
  1936 ni de 1946 — et les listes de 1946 du département ne sont connues que par un microfilm de
  mauvaise qualité.*

---

## AD09 — Ariège · moteur **GAIA 9**

*Ouvert le 19 septembre 2026, pour la mention marginale d'un acte de 1903.*

| | |
|---|---|
| **Vitrine** | <https://archives.ariege.fr> — un CMS, **et ce n'est PAS le moteur** |
| **⭐ Moteur** | **<http://mdr-archives.ariege.fr>** — GAIA 9, le même qu'à l'AD66, au caractère près |
| **WAF** | ⚠️ **sur la vitrine seulement**, voir ci-dessous |
| **Compte** | aucun |

### ⛔ LE PARE-FEU DE LA VITRINE A FAILLI FAIRE DÉCLARER LE PORTAIL MORT

`urllib` reçoit un **418** sur `archives.ariege.fr`. Un vrai Chrome reçoit **41 776 octets** dont
le titre est « **archives.ariege.fr | Anti-DDoS Flood Protection and Firewall** » : un compte à
rebours de **trois secondes**, encodé en base64 dans un `eval(atob(...))`, qui pose un cookie et
recharge.

**Et `lire_page.js` l'a rendu en annonçant « défi franchi ».** Sa page fait 41 ko — bien au-dessus
du seuil de 6 000 — et ne portait aucune des signatures connues. **C'est exactement la faute que
l'entrée F5/Shape documentait la veille**, par l'autre bout : F5 passait *sous* le seuil par sa
taille, celui-ci passe *au-dessus*. Les signatures `anti-ddos` et `flood protection` sont
ajoutées ; le défi tombe alors en **6 s**.

*Le sous-domaine `mdr-archives`, lui, n'a pas de WAF : `gaia.py` l'interroge en direct.*

### ⛔ `cherche` NE LISAIT QUE LA PREMIÈRE PAGE DE L'ALPHABET — corrigé le 20 septembre 2026

`criteres()` parcourait l'abécédaire, **`cherche()` non**. La page d'entrée de l'AD09 s'arrête à
AXIAT : **toute commune après les premières lettres était injoignable par `cherche`**, et le
message d'erreur — « le critère n'est offert à aucun rang de cette page » — se lisait « ce
portail ne connaît pas cette commune ». Vu sur **VÈBRE**, que `criteres 1` listait et que
`cherche 1 272123 …` refusait, le même jour.

*Même famille que le défaut de l'abécédaire lui-même, corrigé la veille : une liste tronquée qui
ne dit pas qu'elle l'est.* La boucle de `cherche` passe maintenant par `_abecedaire`.

### ⛔ ET LA COUVERTURE S'ARRÊTE À 1912 — mesuré sur Vèbre le 20 septembre 2026

```
python scripts/archives/moteurs/gaia.py --dept 09 criteres 1              # les 346 communes
python scripts/archives/moteurs/gaia.py --dept 09 criteres 1 272123       # les types de registre
python scripts/archives/moteurs/gaia.py --dept 09 cherche 1 272123 274756 # les décès
```

| type de registre | id | dernier registre en ligne |
|---|---|---|
| naissances | `274757` | **1903-1912** (`1NUM/4E6140`) |
| mariages | `274759` | **1903-1912** |
| décès | `274756` | **1903-1912** |
| publications de mariage | `274755` | **1903-1912** |
| **tables décennales** | `274762` | **1923-1932** (`1NUM74/2E145`) |
| baptêmes `274760` · sépultures `274758` | | l'Ancien Régime |

**Rien après 1912 pour les actes, rien après 1932 pour les tables.** Une recherche sur les
années 1930-1950 en Ariège ne se fait donc PAS en ligne : elle se fait **à la mairie** — et pour
un **acte de décès**, la copie intégrale se délivre *à toute personne, sans justificatif et sans
délai*, ce qui en fait la seule pièce d'état civil récente qu'on obtienne sans lien de parenté.

*Vèbre = `272123`. Le thème ÉTAT CIVIL est le `1`.*

### ⭐ GAIA SERT DEUX DÉPARTEMENTS, ET LE MODULE LE SAIT DEPUIS CE JOUR-LÀ

`gaia.py` portait le domaine de Perpignan **en dur** — la faute que le dépôt interdit en première
ligne. Il lit désormais `portails.json`, et `--dept` le rebranche :

```bash
python gaia.py --dept 09 themes
python gaia.py --dept 09 criteres 1          # les communes, par lettre initiale
```

### ⚠️ ET LES LISTES DE CRITÈRES SONT PAGINÉES PAR LETTRE INITIALE

L'AD66 ne l'avait pas montré, parce que ses listes tenaient en vingt lignes. **L'Ariège a
331 communes, et la page n'en rend que les trente-deux premières** — celles en A. Les autres sont
derrière `…/requeteConstructor/<thème>/<rang>/R/<LETTRE>/0` :

```
/mdr/index.php/rechercheTheme/requeteConstructor/1/1/R/V/0    → VALS … VIVIES
```

**Une liste de critères qui paraît complète ne l'est pas.** Sans ces liens, on conclut que la
commune cherchée n'existe pas au catalogue — un faux négatif parfaitement crédible.

### Le fonds

Un seul thème, **`1` — ÉTAT CIVIL**. Puis, par commune : baptêmes, naissances, publications des
mariages, mariages, sépultures, décès, **tables décennales**. La date se pose comme à l'AD66,
`typeDate=simple&dateSimple=<année>`, en POST.

> **Ce que ça a rendu le 19 septembre 2026** : VÈBRE, naissances 1903 → un registre,
> `1NUM/4E6140`, 1903-1912, **652 vues**, `idUd=405826`, hiérarchie
> `261748:272123:274757:405826`. L'acte n° 6 est à la **vue 4, page de droite**, et la **table
> annuelle à la vue 6** — six naissances dans l'année, deux garçons et quatre filles. *L'année
> commence à la vue 3 : sur un registre de village, l'index d'une année se trouve en trois
> vues.*

## 🇫🇷 GENEAL43 — un index nominatif de la Haute-Loire, gratuit, et il descend **sous 1792**

**`http://www.geneal43.com`** · tables indexées : `basesphp/tablesindexees/index.php` ·
inventaire : `basesphp/tablesindexees/Inventaire.htm`

**Accès entièrement gratuit, sans adhésion ni compte.** Le site annonce **plus de trois
millions de permaliens** vers les actes numérisés de la Haute-Loire.

### ⭐ Il descend sous 1792, et c'est ce qui le distingue de l'indexation de l'AD43

Les exemples affichés en page d'accueil vont de **Cayres 1640** à **Saint-Rémy 1742-1791**.
L'indexation versée chez l'AD43, elle, porte sur les **tables décennales 1802-1882** et
l'état civil. Pour une branche d'Ancien Régime — les PEYRET de Saint-Pal, les AUBERT — c'est
donc **Geneal43 qu'il faut interroger, pas le WikiTag des archives**.

### ⛔ DEUX BASES, ET L'UNE EST LE DIXIÈME DE L'AUTRE

Environ **110 000 relevés** ont été versés dans l'outil WikiTag de l'AD43 ; le site de
Geneal43 en annonce **plus d'un million**. Chercher chez l'AD43, ne rien trouver et conclure,
c'est avoir lu un dixième du fonds. **Le négatif ne vaut que sur la base qu'on a réellement
interrogée** — et il faut le dire dans le compte rendu.

### Les champs, LUS sur le formulaire le 20 septembre 2026

Deux formulaires, tous deux en **POST**, sans jeton CSRF ni cookie visible :

| champ | ce que c'est |
|---|---|
| `R1` | type d'acte — **1** naissance · **2** mariage · **3** décès |
| `comm` | commune (liste déroulante) |
| `nom` | patronyme |
| **`grepoux`** | **1 = époux, 2 = épouse** |
| `annee_min` / `annee_max` | les bornes |
| `R2` | tri, 1 à 4 |

`resultat.php` sert la recherche par nom ; `resultat2.php`, un second formulaire par commune
(`comm0`).

> **`grepoux` VISE EXACTEMENT LE MUR LE PLUS FRÉQUENT DU MÉTIER.** Une femme mariée n'est pas
> indexée sous le nom qu'on lui connaît — c'est le mur qui a bloqué Margot
> DANNEPOND. Un index qui laisse chercher **du côté de l'épouse** répond à la question qu'on
> pose vraiment.

### Ce que le moteur rend — PAYÉ le 12 septembre 2026 sur Saint-Pal-de-Chalençon

Un dépouillement complet des PEYRET, AUBERT et MEY de la paroisse est passé par ce formulaire.
Ce qu'il a appris, et qui ne se devine pas :

- **Pas de pagination.** Un résultat de 490 lignes sort en **une seule page** : rien à parcourir,
  rien qui plafonne en silence. C'est l'inverse du piège habituel.
- **`%` EST UN JOKER SQL, ET SANS LUI LA CORRESPONDANCE EST EXACTE.** `PEYRE` rend **0**,
  `PEYR%` rend **4 166**. Chercher une graphie devinée ne rend donc rien alors que le nom est
  là sous une autre forme — **on interroge par joker, jamais par graphie supposée.** C'est la
  règle « lire toute la section de la lettre » appliquée à un index.
- **L'index NE PORTE AUCUNE FILIATION.** Colonnes : `Nom | Prénom | Date | Acte | Commentaires |
  Commune`. Le champ « Commentaires » donne parfois le conjoint d'un défunt (« veuve de… ») ;
  **les parents ne sont jamais donnés.** Toute filiation demande l'image — et pour les actes les
  plus anciens, la mention « nv » signale que le dépouilleur n'a relié l'acte à aucune vue.
- **Le permalien pointe une VUE, pas un acte** : préfixe `https://www.archives43.fr/ark:47539/`,
  et plusieurs actes d'une même page partagent le même lien.
- **`resultat2.php` rend la couverture réelle d'une commune** — années dépouillées, volumes, et
  les années déclarées manquantes. **C'est ce qui donne sa valeur à une absence**, et il faut le
  consulter avant d'écrire un négatif : Tiranges ne commence qu'en **1750**, Solignac-sous-Roche
  en **1802**, Valprivas et Malvalette en **1851**. Un zéro chez elles ne veut rien dire.
- **Contrôle de fiabilité fait** : le mariage PEYRET × MEY du 18 juillet 1668, connu du corpus par
  l'acte original, sort de l'index au jour exact.

⚠️ **CE QUI RESTE À PAYER** : `grepoux` n'a pas encore été essayé, et la couverture ne dépasse
pas la Haute-Loire — **Usson-en-Forez et Apinac sont dans la Loire et n'y sont pas**, alors que
la branche PEYRET les traverse.

## 🇩🇿 ANOM — l'état civil d'Algérie, et un serveur qui ne parle que `http`

**`http://anom.archivesnationales.culture.gouv.fr/caomec2/`**

L'état civil des anciens territoires d'outre-mer, consultable **à distance, gratuitement,
sans compte**. Pour le corpus, c'est la seule porte sur **Constantine**.

### ⛔ LE PIÈGE EST TECHNIQUE, ET IL SE REDIAGNOSTIQUE TROIS FOIS SI ON NE L'ÉCRIT PAS

**Le serveur ne sert pas de TLS.** Toute requête forcée en `https` échoue par
`UNSUPPORTED_PROTOCOL`.

> **Ce n'est PAS un `CERTIFICATE_VERIFY_FAILED`, et `tls.py` n'y peut rien.** La fiche TLS du
> carnet dit qu'un certificat refusé est de notre côté ; celle-ci dit l'inverse et il ne faut
> pas les confondre — ici le magasin de certificats est hors de cause, c'est **l'outil qui
> réécrit `http` en `https`** qui se trompe de site. On interroge en `http://` simple, et
> `urllib` suffit.

Second détail d'encodage : la page **se déclare et se sert en ISO-8859-1**.

### Les champs, LUS sur le formulaire le 20 septembre 2026

`<form action="resultats.php">` — **GET**, pas de JavaScript, pas de cookie observé :
`territoire`, `commune`, `nom`, `prenom`, `typeacte`, `annee`, `debut`, `fin`, `vue`.

### ⭐ Et un suggesteur de noms, qui vaut mieux qu'une recherche à l'aveugle

```
noms.php?territoire=ALGERIE&commune=&nom=
```

Il rend **les noms qui existent réellement dans la base**. C'est le moyen d'essayer une
graphie sans lancer de recherche — exactement ce qu'il faut pour un patronyme qui n'a pas de
forme fixe.

### ⛔ LA BORNE DE 1904 EST CELLE DE L'INDEX, PAS CELLE DU FONDS — payé le 20 septembre 2026

C'était une réserve de fiche ; c'est maintenant un fait, et il se retourne.

**La recherche nominative s'arrête vers 1904** : recompté sur pièce, le plus récent des 10 PAIRE
d'Algérie est de 1901, le plus récent des 27 PAYRE de 1903. Chercher un nom après cette date ne
rend rien — **et ça ne prouve rien du tout.**

**LES REGISTRES POSTÉRIEURS SONT LÀ, ET ILS SE FEUILLETTENT.** On interroge alors **sans nom** :
commune + type d'acte + année. `CONSTANTINE / Naissance / 1923` rend trois registres, dont les
naissances — **419 vues**. C'est ainsi qu'a été trouvé l'acte n° 942 du 5 juillet 1923.

> **Le piège est de conclure du silence de l'index à l'absence du fonds.** Une famille arrivée
> en Algérie dans les années 1920 n'est indexée nulle part ici : elle est dans les registres,
> et nulle part ailleurs.

### Les images : OpenSeadragon et DeepZoom

La ligne de résultat porte son lien en clair dans son `onclick` — `osd.php?territoire=…&registre=<n>` —
et la page de la visionneuse porte **la liste complète des vues**, une par `.dzi`. Chaque vue est un
DeepZoom : manifeste `…_NNNN.dzi` (Width, Height, TileSize 254, Overlap 1), tuiles sous
`…_NNNN_files/<niveau>/<col>_<ligne>.jpeg`.

⚠️ **LES TUILES SONT EN `.jpeg`, PAS EN `.jpg`.** Le manifeste le dit — `Format="jpeg"` — et une
requête en `.jpg` rend 404. Trois niveaux ont été essayés en `.jpg` avant qu'on lise le manifeste :
c'est le faux négatif que la skill interdit, payé une fois de plus.

**Le niveau maximal est `ceil(log2(max(W,H)))`** ; un cran en dessous suffit largement à lire un
acte d'état civil imprimé — 2170 × 1568 pour une double page — et coûte quatre fois moins.

### Le module

**`scripts/archives/moteurs/anom.py`** — neuvième moteur du dossier.

```
python anom.py registres ALGERIE CONSTANTINE 1923     # les registres d'une année
python anom.py vues 40976                             # combien de vues
python anom.py tirer 40976 363 372 --niveau 12        # assembler les vues sur X:
python anom.py noms ALGERIE PAIR                      # le suggesteur de patronymes
python anom.py chercher ALGERIE PAIRE                 # la recherche nominative
```

La pagination se fait par `&page=N`, **lu dans le HTML** et non supposé.

## 🌍 FAMILYSEARCH — l'index, le CATALOGUE, et une API qu'on n'a pas le droit de vendre

**`https://www.familysearch.org`** · compte gratuit requis

**Cette fiche existe parce qu'elle manquait.** Le dossier interroge FamilySearch depuis le
début — le catalogue de Valvasone, le fonds du tribunal de Pordenone, les pièges de son
moteur sont écrits dans la skill —, et **la source n'avait aucune entrée au registre**. C'est
précisément ce que la règle « écrire la fiche de la SOURCE » interdit.

### Deux usages, et le second est le sous-employé

- **La RECHERCHE** d'actes indexés — mondiale, mais partielle.
- **LE CATALOGUE**, qui dit **quels fonds existent pour un lieu**. C'est lui qui a établi que
  Valvasone n'a chez eux que **1806-1815** et **1871-1910**, et **rien entre les deux** — un
  fait négatif qui a réorienté toute la recherche italienne vers la curie de Concordia-
  Pordenone. **Un catalogue qui dit ce qui n'est PAS en ligne fait gagner des semaines.**

### Les deux pièges, déjà payés

**IL CLASSE AU LIEU DE FILTRER.** Interrogé sans son `f.collectionId`, le moteur trie par
ressemblance et rend toujours quelque chose de crédible : pour « Anna VOLPATTI née à
Valvasone », une Anna Volpatti **née en 1879, morte à San Francisco en 1953**.

**MAIS RESSERRER LE FILTRE EST SOUVENT PIRE.** Quatre recherches « propres » verrouillées sur
la collection ont rendu trois fois zéro ; la recherche large du généalogiste, elle, avait sorti un
recensement argentin de 1895 qui a ouvert une branche entière. **Ratisser large, trier à
l'œil, puis passer aux IMAGES par le numéro de film.**

### ⚠️ La réserve qui engage le produit

**L'API est gratuite mais réservée à un usage NON COMMERCIAL.** Elle peut servir la recherche
personnelle ; **elle ne peut pas porter un modèle économique** — c'est écrit dans
`ROADMAP.md`, et ça vaut pour tout ce qui serait distribué comme produit.

### État de la reconnaissance au 20 septembre 2026

L'URL de documentation de l'authentification essayée ce jour-là **rend 404**. La porte
d'entrée de l'API est donc **à retrouver** avant d'écrire une ligne de module — et le gist de
`peas` affirme qu'un simple jeton de session suffirait, ce qui **n'a pas été vérifié**.

## OAI-PMH et EAD — la porte à côté du mur, et elle existe **six fois sur soixante-trois**

`python scripts/archives/oai.py` · `--controle` · `--ecrire` · ou un département : `oai.py 37`

**Le dossier interroge les portails par la voie la plus chère et la plus fragile** — piloter
un vrai Chrome sur du HTML. C'est justifié quand il n'y a rien d'autre. Mais **OAI-PMH est
une norme d'archives**, et personne ici ne l'avait jamais essayée.

### Ce que ça rend, et pourquoi c'est deux réponses en une requête

| verbe | ce qu'on apprend |
|---|---|
| `?verb=Identify` | si ça répond, **tout le catalogue est moissonnable** : on miroite l'inventaire une fois, en local, et on cherche hors ligne |
| `?verb=ListMetadataFormats` | si l'**EAD** est servi — le format des instruments de recherche : fonds, série, cote, dates |

**L'EAD ne se sonde pas tout seul : il ARRIVE par OAI-PMH.** D'où une seule sonde pour les
deux. Et c'est lui qui compte, parce qu'il donne comme **donnée** ce qu'on reconstitue à la
main en pilotant un navigateur : *quel registre couvre quelles années*. C'est là que sont nos
pièges les plus chers — le libellé de commune qui se lit et ne se reconstruit pas, le filtre
qui rend les 8 409 registres du département en ayant l'air d'un résultat de commune.

### Les six, au 20 septembre 2026 — et tous servent l'EAD

| fonds | dépôt | formats |
|---|---|---|
| **AD37 Indre-et-Loire** | `https://archives.touraine.fr/oai-pmh` | oai_dc, **ead** |
| AD19 Corrèze | `https://www.archives.correze.fr/oai-pmh` | oai_dc, **ead** |
| AD14 Calvados | `https://archives.calvados.fr/oai-pmh` | oai_dc, **ead** |
| AD51 Marne | `https://archives.marne.fr/oai-pmh` | oai_dc, **ead** |
| AD58 Nièvre | `https://archives.nievre.fr/oai-pmh` | oai_dc, **ead** |
| **SHD Vincennes** | `https://www.servicehistorique.sga.defense.gouv.fr/oai-pmh` | **ead** seul |

**L'AD37 est le département de la branche CHASLE** — Lublé, Villiers-au-Bouin, Couesmes. Le
SHD, lui, sert l'EAD **sans même l'oai_dc** : un fonds militaire dont on n'avait jamais su
lister l'inventaire.

### ⛔ CE N'EST PAS UNE PROPRIÉTÉ DU MOTEUR, ET C'ÉTAIT L'HYPOTHÈSE ÉVIDENTE

Cinq des six sont des portails **Naoned**, ce qui ressemblait à la règle habituelle du
dossier — le code vit par moteur, pas par département. **Mais l'Eure et le Haut-Rhin sont
Naoned aussi et rendent 404** ; la Savoie, génération ancienne, rend 403. **Cinq sur sept.**
C'est donc une option que le département active, pas un trait de l'éditeur — et il faut
sonder chaque portail, pas en déduire un du voisin.

### ⛔ LA PREMIÈRE VERSION A RENDU ZÉRO, ET LE ZÉRO ÉTAIT FAUX

Sept chemins sur l'hôte du portail : **0 sur 63**. Avant d'écrire ce négatif, trois dépôts
OAI-PMH connus ont été essayés — **et les trois auraient été manqués** :

| témoin | adresse | ce qui échappait |
|---|---|---|
| HAL | `api.archives-ouvertes.fr/oai/hal/` | autre hôte, chemin profond |
| Internet Archive | `archive.org/services/oai2.php` | chemin absent de la liste |
| Persée | `oai.persee.fr/oai` | **sous-domaine dédié** |

**Un dépôt OAI-PMH ne vit presque jamais à la racine du site qu'on regarde.** La sonde essaie
donc maintenant douze chemins, le sous-domaine `oai.<domaine>`, **et les liens que la page
d'accueil désigne elle-même** — c'est la règle du dossier, lire la réponse avant de deviner
une URL. Le chemin qui a tout rendu, `/oai-pmh`, n'était dans aucune des listes de départ.

> **ET LE CONTRÔLE POSITIF EST DÉSORMAIS DANS L'OUTIL.** `oai.py` interroge les trois
> témoins avant de sonder quoi que ce soit, et **refuse de tourner** s'ils ne répondent pas.
> Une sonde qui ne rend que des « non » ne se distingue d'une sonde cassée que par là.

### Ce que vaut le négatif des cinquante-sept autres

**« Aucun des chemins essayés ne répond »**, et rien de plus. Un portail peut servir OAI-PMH
à une adresse qu'on n'a pas devinée. Chaque fiche porte donc `oai.NEGATIF_PARTIEL` avec la
liste des chemins essayés, et non un « pas d'OAI-PMH » qui fermerait la question.

### ⚠️ Un piège de la sonde, qui est le piège du dossier

**Beaucoup de portails rendent 200 sur n'importe quel chemin** — `francearchives.gouv.fr/oai`
répond 200 en servant sa page d'accueil. Un `200` pris pour un « oui » est exactement la
famille du paramètre inventé qu'on ignore en silence. **La sonde exige l'espace de noms
`OAI-PMH` et la balise `<Identify`**, jamais le code de retour.
