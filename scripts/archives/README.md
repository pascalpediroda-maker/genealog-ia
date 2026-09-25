# `scripts/archives/` — la boîte à outils du dépouillement

**La méthode est dans la skill [`archives-fr`](../../.claude/skills/archives-fr/SKILL.md), et
les pièges payés portail par portail dans son
[carnet](../../.claude/skills/archives-fr/references/portails.md).** Ici, le code.

## Le principe, et c'est lui qui compte

**Le code vit par MOTEUR, pas par département.** Il y a une centaine de départements en France
et une dizaine de moteurs — **Boscop** (produit *Ligeo Archives*, +150 services), **Naoned**
(produit *Mnesys*, +100 services), **Arkothèque** (éditeur *1 égal 2*, le plus répandu du
dossier), **Prismia ViSiON**, **GAIA 9**, plus *Archinoë*, *Anaphore*, *4D* et quelques
développements maison. Écrire un module par département reviendrait à écrire cent fois la même
chose ; écrire un module par moteur le rend utilisable sur quinze départements d'un coup.

**LES COMPTES EXACTS NE SONT PLUS DANS CETTE PHRASE, ET C'EST VOULU.** Elle a annoncé « trois
moteurs pour six portails » jusqu'au 5 septembre 2026, alors que l'AD46, ouvert le matin même,
ne figurait nulle part ; puis « sept pour seize » jusqu'au 18, quand il y en avait dix pour
trente et un. **Une table recopiée à la main est une table qui ment tôt ou tard** — et l'outil
écrit contre cette dérive portait lui-même deux tables en dur, qui avaient dérivé. La table
ci-dessous se régénère depuis `portails.json`, et un contrôle échoue quand elle ne l'est plus :

```bash
python scripts/archives/moteurs_table.py          # la table markdown
python scripts/archives/moteurs_table.py --court  # une ligne par moteur
python scripts/archives/portails_coherence.py     # échoue si les trois fichiers divergent
```

*Éditeur et produit désignent la même chose : `boscop` et `ligeo` sont un seul moteur, `naoned`
et `mnesys` aussi. La liste en portait cinq pour trois jusqu'au 27 août 2026, et le doublon
faisait croire à des moteurs restant à ouvrir.*

Le département n'est alors plus que de la **configuration** — URL de base, identifiants propres
au portail, pièges — et elle vit dans `portails.json`.

```
lire/          INDÉPENDANT DE TOUT : du traitement d'image sur des JPEG déjà sur le disque.
               Ces outils ignorent d'où viennent les images, et c'est voulu.
moteurs/       UN FICHIER PAR MOTEUR. Sait parler à un type de portail.
portails.json  LE REGISTRE. Une fiche par FONDS qu'on sait interroger — les portails
               départementaux, et depuis le 18 septembre 2026 les sources qui n'ont ni
               commune ni cote : INSEE, Gallica, CEMLA, Arolsen, la Wayback. Elles
               portent `dept: null`, et un `type`.
```

## `lire/` — lire un registre

| outil | ce qu'il fait |
|---|---|
| `page.py <reg> <a> <b>` | rend chaque demi-page à **1154 × 1990 px**, recadrée sur l'encre. C'est la taille utile maximale : au-delà de 2000 px sur le grand côté, l'image est réduite avant lecture |
| `zoomb.py` | zoom sur la **boîte d'encre**, donc aux mêmes fractions que `page.py` — on repère sur l'image qu'on vient de lire. Option `div=True` : division par un fond flouté, qui tue l'ombre de pliure. **Ne sait parler qu'à l'AD42** : il passe par `actes.py`, dont les chemins sont codés en dur |
| `sp.py` | le registre de Saint-Pal (AD43), qui est en **double page à 2500 px** — sous le seuil de découpe d'`actes.py`, donc la pliure s'y cherche vue par vue. `sp.py <a> <b>` rend les demi-pages, `sp.py z <vue> <G\|D> <y0> <y1> <dest> [x0] [x1] [div]` zoome : c'est le `zoomb.py` de ce portail |
| `zoom.py` | même chose, mais en fractions de la page brute |
| `strip.py` / `tete.py` | planches des premières lignes de chaque demi-page, pour **cadrer un registre sans le lire**. `tete.py` recadre sur l'encre — indispensable sur les registres anciens, dont la marge haute fait le quart du feuillet |
| `grille.py` | planches de mentions de marge. **Fragile** : perd des cellules sur les registres aux marges serrées |
| `actes.py` | découpe une vue en demi-pages, avec le garde-fou des **pages simples** — 7 à 9 vues par registre n'ont qu'une page, et y chercher une pliure coupe le texte en plein milieu |

**Dette connue** : `actes.py` porte encore `ROOT` et un dictionnaire `REGS` codés en dur,
hérités du chantier d'Usson. À basculer dans un fichier de configuration au troisième
département.

## `moteurs/` — récupérer les vues

| Moteur | Module | Départements branchés |
|---|---|---|
| **Arkothèque (éditeur *1 égal 2*)** | `arkotheque.js` + `arkotheque.py` + `arkotheque_liste.js` + `arkotheque_infos.js` — `arkotheque.py` SANS NAVIGATEUR sur les douze portails du registre, mesure le 19 septembre 2026. ⚠️ LE « DOUBLE MUR » DES AD36, AD38 ET AD83 N'EN EST PAS UN : les 222 octets de `window.location.href='/redirect_<jeton>/'` sont le jeton anti-robot Arkotheque ordinaire, que `_get()` suit deja depuis l'AD43, et aucun Cloudflare ne se manifeste derriere. | **24** Dordogne · **36** Indre · **38** Isère · **43** Haute-Loire · **45** Loiret · **46** Lot · **49** Maine-et-Loire · **50** Manche · **54** Meurthe-et-Moselle · **72** Sarthe · **78** Yvelines · **83** Var · Mémoire des Hommes |
| **Boscop (produit *Ligeo Archives*)** | `boscop.js` + `boscop_un.js` + `boscop_liste.js` + `boscop_labels.js` + `boscop_7986.js` + `boscop_inventaire.js` — **Chrome obligatoire.** — et `boscop_inventaire.js` pour les portails SANS critere de commune, qui se descendent par l'arbre d'inventaire (AD57). | **02** Aisne · **06** Alpes-Maritimes · **16** Charente · **31** Haute-Garonne — Archives DEPARTEMENTALES · **38-GRENOBLE-AM** Grenoble — Archives MUNICIPALES et metropolitaines · **42** Loire · **56** Morbihan · **57** Moselle · **67** Bas-Rhin — Archives d'Alsace, site de Strasbourg · **74** Haute-Savoie · **76** Seine-Maritime · **79-86** Deux-Sevres et Vienne (portail commun) · **95** Val-d'Oise |
| **Naoned (produit *Mnesys*, generation moderne)** | `naoned.py` — sans navigateur | **14** Calvados · **19** Correze · **27** Eure · **37** Indre-et-Loire · **51** Marne · **58** Nièvre · **68** Haut-Rhin — Archives d'Alsace, site de Colmar |
| **GAIA 9** | `gaia.py` — HTML de 2008, `urllib` suffit — mais il faut rejouer les étapes dans l'ordre sur la même session à cookies, et la page se déclare `iso-8859-1` | **09** Ariège · **61** Orne · **66** Pyrénées-Orientales |
| **Anaphore, produit *Bach* (Symfony)** | `anaphore.py` — sans navigateur — mais une SESSION A COOKIES obligatoire : la recherche est un POST a jeton CSRF, et les facettes s'empilent une par requete | **52** Haute-Marne · **84** Vaucluse |
| **4D (4th Dimension)** | `quatred.py` — **⚠️ `quatred.py` N'A JAMAIS TOURNE CONTRE LE PORTAIL : le 19 septembre 2026 Toulouse refusait la connexion a tout le monde, Chrome compris. Il porte son propre controle positif et refuse de chercher tant qu'il n'est pas passe.** | **31-TOULOUSE-AM** Toulouse — Archives MUNICIPALES (et non les AD31) |
| **Anaphore, produit *Thot* (ASP classique)** | *aucun module — et `anaphore.py` ne convient pas : il parle a *Bach*, l'autre produit du meme editeur, qui n'a rien de commun avec celui-ci* | **35** Ille-et-Vilaine |
| **Archives nationales d'outre-mer (développement propre)** | `anom.py` — ⛔ **Le serveur ne parle que `http`** — une requête forcée en `https` échoue par UNSUPPORTED_PROTOCOL, et **ce n'est PAS un CERTIFICATE_VERIFY_FAILED** : `tls.py` n'y peut rien. Pages en ISO-8859-1. Images en DeepZoom, **tuiles en `.jpeg` et non `.jpg`** (le manifeste le dit : `Format="jpeg"`). ⭐ **La recherche nominative s'arrête vers 1904, le FONDS non** : après cette date on interroge sans nom — commune, type d'acte, année — et on feuillette. Constantine 1923 porte 419 vues de naissances. | ANOM — Archives nationales d'outre-mer (caomec2) |
| **Archinoë, generation `/v2/` (AD17)** | `archinoe.py` — session à cookies obligatoire — une page 2 sans `PHPSESSID` rend du vide | **17** Charente-Maritime |
| **Archinoë, generation **O2 / Oxygene** (ExtJS, sous `/console/`)** | `archinoe_o2.py` — Chrome pour amorcer le mur F5, puis Python. ⭐ ET SA VISIONNEUSE EST CELLE DE LA GENERATION /v2/ : un O2 pose sur un v2. | **62** Pas-de-Calais |
| **ASP.NET `.asmx` (service SOAP/JSON)** | *reconnaissance seule — aucun module écrit* | Arolsen Archives |
| **ASP.NET WebForms** | `albodoro.py` — sans navigateur ; cycle `__VIEWSTATE` / `__EVENTVALIDATION`, et le nom cherche est un PREFIXE | **IT-CGG** Caduti della Grande Guerra — l'Albo d'Oro des morts italiens de 14-18 |
| **Django (application web generique, pas un moteur d'archives)** | *aucun module, et aucun besoin : le seul portail branche dessus, Matricula, a ete ferme le 20 septembre 2026 -- sa couverture italienne ne sert pas ce dossier. La recherche y est un GET (`/en/suchen/?place=`), donc un module tiendrait en quelques lignes le jour ou un arbre toucherait l'Autriche, l'Allemagne ou la Slovenie.* | Matricula Online — registres paroissiaux d'Europe centrale |
| **Naoned, produit *Mnesys* — GENERATION ANCIENNE** | *aucun module — et `naoned.py` ne convient pas : il parle au Mnesys moderne (`/search/form/{uuid}`, arks), celui-ci travaille en query string et rend 403 sur ces chemins* | **73** Savoie |
| **Prismia ViSiON** | `prismia.py` — sans navigateur, images en IIIF | **47** Lot-et-Garonne |
| **WordPress maison (Portale Antenati)** | `antenati.js` — arks en `ark:/12657/` | **IT** Portale Antenati |

*16 moteurs, 49 portails à moteur, plus 15 sources sans moteur (64 fiches en tout). Table générée par `python scripts/archives/moteurs_table.py` — la source de vérité est `portails.json`.*

### Ce que chaque module sait faire

| module | usage |
|---|---|
| `boscop.js` | `node boscop.js <dept> <fichier.tsv>` — plusieurs registres d'affilée, un `ark` et un dossier par ligne |
| `boscop_un.js` | `node boscop_un.js <ark> <dossier>` — un seul registre |
| `boscop_liste.js` | récolte la liste **paginée** des unités numérisées d'une commune |
| `boscop_7986.js` | le portail commun AD79/AD86, dont la pose des critères diffère |
| `arkotheque.js` | `node arkotheque.js <dept> <numérisation> <image_début> <nb_vues> <dossier>` — pour les portails qui exigent un Chrome |
| `arkotheque_liste.js` | les registres d'une commune, en TSV, par `/_recherche-api/moteur` |
| **`arkotheque.py`** | `communes` · `registres` · `numerisation` · `sources` · `telecharge` — **sans navigateur**, quand `http_simple` |
| `naoned.py` | `recherche()` · `noms()` · `vues()` · `vues_api()` · `telecharge()` — **sans navigateur**. Les noms de champs changent d'un portail à l'autre : `recherche(..., champs=noms(fiche))` |
| **`prismia.py`** | `instruments` · `facette` · `registres` · `manifeste` · `tirer` — **sans navigateur**, images en IIIF |
| `antenati.js` | le Portale Antenati italien |
| `boscop_labels.js` | lit le **label** du manifeste IIIF d'une série d'unités et son nombre de vues — la notice de la liste de résultats est tronquée et ne dit pas toujours le TYPE d'acte |
| `arkotheque_infos.js` | résout le **numéro de numérisation** d'un registre, qui ne se devine pas |
| **`archinoe.py`** | `communes` · `registres` · `cadastre` · `tirer-plan` — **sans navigateur** |
| **`gaia.py`** | le moteur des AD66 et de qui l'emploie — session à cookies, pages en `iso-8859-1` |
| **`boscop_inventaire.js`** | `communes` · `registres` · `tirer` · `sonde` — pour les Boscop **sans critère de commune**, qui se descendent par l'arbre d'inventaire et dont les images sortent en IIIF (AD57) |
| **`anaphore.py`** | `cherche` · `facettes` · `parcours` · `vues` · `tirer` — **sans navigateur**. `facettes` rend les libellés exacts : ils se lisent, ils ne se tapent pas |
| **`albodoro.py`** | `commune` · `nom` · `mot` · `fiche` — les 530 000 morts italiens de 14-18. ⚠️ `nom` est un **préfixe** : `--exact` ou relire la liste |
| **`quatred.py`** | `controle` · `cherche` — Toulouse. ⚠️ **jamais exécuté contre le portail** : il refuse de chercher tant que son contrôle positif n'est pas passé |
| **`gallica.py`** | la BnF par ses API publiques. *Ce code avait été écrit deux fois et perdu deux fois avant d'atterrir ici* |
| **`francearchives.py`** | le portail national — **et la porte de service des portails défendus** |
| **`memoiredeshommes.py`** | les JMO de 14-18 et les morts pour la France. Tourne sur **Arkothèque** |
| `identifier.js` | *transverse* — reconnaît le moteur d'un portail inconnu, WAF franchi |
| `lire_page.js` | *transverse* — rend le HTML d'une page derrière un mur, dans un vrai Chrome |
| `insee.py` | *(hors moteurs/)* le fichier des décès — `chercher <année> --sexe --ne-dept --mort-dept` |
| `moteurs_table.py` | *(hors moteurs/)* régénère la table ci-dessus depuis `portails.json` |
| **`portails_coherence.py`** | *(hors moteurs/)* **échoue** si registre, carnet et README divergent. `--ecrire` remet la table |

**Les modules `.js` ouvrent un vrai Chrome fenêtré**, jamais le *headless shell* : le WAF de
l'AD42 renvoie 403 à ce dernier comme à curl. Rien n'est masqué, `navigator.webdriver` reste à
`true`. Cadence d'une vue par seconde.

**Les modules `.py`, eux, n'ouvrent rien** — trois requêtes HTTP ordinaires suffisent. **Tous
les portails Arkothèque ne se valent pas de ce point de vue** : l'AD43 et l'AD45 se défendent,
l'AD49 non. C'est le drapeau **`http_simple`** de `portails.json` qui décide, et
`arkotheque.py` refuse de servir un portail qui ne le porte pas — sans quoi il prendrait le
HTML d'un défi anti-robot pour du JSON et conclurait qu'un registre est vide.

## Ajouter un département

1. **Identifier le moteur** — il se signe dans le HTML de la page d'accueil : chercher
   `arkotheque`, `ligeo`, `mnesys`, `naoned`, `anaphore`, `boscop`.
2. **Si le moteur existe déjà** dans `moteurs/` : ajouter une fiche à `portails.json` et c'est
   tout. C'est le cas nominal.
3. **Sinon**, écrire le module — et **capturer le trafic réseau d'une vue affichée** plutôt que
   de deviner les URL. C'est ce qui a fait perdre une heure sur l'AD43 : quatre motifs essayés
   à l'aveugle avant de lire le corps de la réponse, qui contenait un jeton anti-robot.
4. **Écrire sa fiche dans `portails.json`** — moteur, adresse, champs, murs, couverture. Si le
   moteur est neuf, **l'inscrire aussi dans `_meta.moteurs` ET dans `moteurs/identifier.js`** :
   un moteur reconnu qui n'entre pas dans cette table est un moteur qu'on redécouvrira. C'est
   arrivé à **GAIA**, reconnu le 12 septembre 2026 sur l'AD66 et redécouvert de zéro le 18 sur
   l'AD61, et au **Portale Antenati**, ouvert le 27 août et jamais inscrit.
5. **Écrire les pièges dans le [carnet](../../.claude/skills/archives-fr/references/portails.md)**,
   et porter le titre exact de la section dans le champ `carnet` de la fiche. Une session qui
   les relit ne les repaie pas.
6. **`python scripts/archives/portails_coherence.py`** — il échoue si l'une des étapes
   ci-dessus a été sautée. C'est le seul garde-fou : les trois fichiers avaient divergé de
   quatorze fiches avant qu'il n'existe.
