# Le monde — l'annuaire de ce qu'on n'a PAS ouvert

**Ce fichier n'est pas le carnet.** [`portails.md`](portails.md) porte les fonds qu'on sait
interroger, avec leurs pièges payés ; celui-ci porte **ce qui existe ailleurs et qu'on n'a
jamais touché**. On ne cite rien d'ici comme une source vérifiée : on y cherche une porte
quand une branche sort du périmètre français.

> **Provenance.** La matière de ce fichier vient du catalogue de
> **[`sliday/genealogy-research`](https://github.com/sliday/genealogy-research)**, sous
> licence **MIT** (Copyright © 2026 Stas Kulesh), réorganisé et annoté ici. Leur travail
> couvre le monde là où le nôtre couvre la France en profondeur : les deux se complètent
> presque sans se recouvrir. **Rien de ce qui suit n'a été vérifié par ce dossier.**

---

## L'ordre de vérification d'accès est dans la SKILL, pas ici

C'est la leçon de fond de leur travail, et elle vaut plus que la liste qui suit. Elle est
donc passée dans la méthode, le 20 septembre 2026 : **l'échelle d'accès et les quatre normes
sont en tête de « Ouvrir un portail qu'on ne connaît pas » dans
[`SKILL.md`](../SKILL.md)** — on ne la recopie pas ici, parce qu'une recette dupliquée est
une recette qui pourrit.

En un mot : **API, export, données ouvertes, IIIF, OAI-PMH/SRU, autorisation — et le HTML en
dernier.** Les modes d'accès notés dans les tables ci-dessous servent à savoir *à quel rang
on entre* avant d'ouvrir un navigateur.

---

## International — les API qui servent partout

| service | accès | notes |
|---|---|---|
| **FamilySearch** — plateforme développeur | API, OAuth 2 | clés et revue d'application. **Usage NON COMMERCIAL** — fiche au registre |
| FamilySearch Places | API | normalisation des lieux |
| FamilySearch Catalog | manuel | dit **ce qui n'est PAS en ligne** : c'est son meilleur usage |
| **WikiTree** | API en lecture, 200 req/min | passer un `appId` |
| WikiTree — dumps | export en gros | conserver la date du dump |
| **Geni** | OAuth, applications approuvées | les liens du graphe sont des pistes, pas des preuves |
| **Internet Archive** | API de recherche, **IIIF** | vérifier les droits pièce par pièce |
| **Google Books** | API | annuaires, monographies locales |
| **HathiTrust** | API multiples | accès variable selon les droits |
| **Wikidata** | **SPARQL** | contexte et autorité de lieux |
| **GeoNames** | API, compte requis | géocodage **moderne** — la juridiction historique diffère |
| **Getty TGN** | données liées ouvertes | contrôle d'autorité ; garder les noms d'origine |
| **Europeana** | API (clé parfois requise) | suivre `edm:isShownAt` jusqu'au fournisseur |

---

## France et Belgique

*Le détail français est dans [`portails.md`](portails.md) — 45 portails, 14 moteurs. Ce qui
suit ne liste que ce qui n'y est pas encore.*

| service | accès | notes |
|---|---|---|
| **Gallica / BnF** | **API** (`api.bnf.fr`), SRU, IIIF, OCR | au registre. Identifiants ARK ; l'OCR sert à trouver, pas à prouver |
| **FranceArchives** | annuaire + état civil + recensements | au registre. Routage vers chaque service départemental et municipal |
| **Mémoire des hommes** | Arkothèque | au registre. Morts, services, résistance, déportation |
| **ANOM** | base nominative, `http` seul | au registre depuis le 20/9/2026 |
| **RetroNews** | abonnement | au registre. Presse, fonds distinct de Gallica |
| **GeneaBank** | adhésion associative | au registre. Relevés des associations françaises |
| **Archives municipales** | variable | complètent le départemental dans les grandes villes |
| **Open Archives (NL/BE)** | **API, OAI-PMH, OpenSearch** | 4 requêtes/seconde par IP. La porte pour la Belgique |
| **WieWasWie** | abonnement | préférer l'API d'Open Archives pour l'automatisation |

---

## Royaume-Uni et Irlande

| service | accès | notes |
|---|---|---|
| **TNA Discovery** | API | descriptions de catalogue ; noter les références |
| FreeBMD / FreeREG / FreeCEN | manuel, données ouvertes partielles | index et transcriptions, **à vérifier sur image** |
| **GRO** (Angleterre-Galles) | compte, commande | index officiels et certificats |
| **ScotlandsPeople** | paiement à la vue | état civil, recensements, registres d'église |
| IrishGenealogy.ie | libre | seuils de confidentialité variables selon le type |
| National Archives of Ireland | libre | recensements, évaluations, testaments, militaire |
| **PRONI** | libre, demande d'archive | testaments, évaluations, annuaires, registres d'église |
| RootsIreland | abonnement | transcriptions à vérifier |
| British Newspaper Archive | abonnement | vérifier l'OCR sur l'image |

---

## Allemagne et pays germanophones

| service | accès | notes |
|---|---|---|
| **Matricula Online** | libre | registres paroissiaux. **Ne sert pas le Frioul** — vérifié le 20/9/2026 |
| Bundesarchiv | catalogue, demande | militaire, naturalisations ; règles de confidentialité |
| **Archion** | abonnement | registres paroissiaux protestants |
| CompGen / GOV | libre, téléchargements | index, annuaires, dictionnaire de lieux |
| Volksbund | inscription | morts et sépultures allemandes |

---

## Pologne

| service | accès | notes |
|---|---|---|
| Szukaj w Archiwach | manuel, endpoints observés | métadonnées et téléchargement non documentés |
| Geneteka | libre | index paroissiaux et civils, **à vérifier sur scan** |
| Skanoteka · Metryki | libre | scans de registres |
| **PRADZIAD** | catalogue | **essentiel pour l'analyse de couverture** — quelles années existent |
| Poznań Project | libre | mariages du XIXᵉ |
| AGAD | catalogue et scans | archives centrales, Varsovie |
| JRI-Poland | libre | actes juifs avec références d'archives |

---

## Scandinavie et pays baltes

| service | accès | notes |
|---|---|---|
| **Riksarkivet** (Suède) | **API, OAI-PMH, IIIF** | certaines interfaces en bêta |
| Digitalarkivet (Norvège) | libre, téléchargements | pas d'API générale vérifiée |
| Arkivalieronline (Danemark) | libre | registres d'église, recensements, successions |
| Astia (Finlande) | libre | église, militaire, justice, cartes |
| ePaveldas (Lituanie) · Raduraksti (Lettonie) · Saaga (Estonie) | libre ou inscription | registres d'église, recensements, listes de révision |

---

## Europe centrale et orientale

| service | accès | notes |
|---|---|---|
| Porta fontium (Tchéquie) | libre | fonds tchéco-bavarois |
| Acta Publica (Tchéquie) | libre | registres paroissiaux moraves |
| Archives nationales de Hongrie | catalogue, demande | civil, église, recensements, militaire |
| Portail archivistique ukrainien | catalogue, demande | accès affecté par la guerre |

---

## Italie et Europe du Sud

| service | accès | notes |
|---|---|---|
| **Portale Antenati** | libre | au registre. État civil napoléonien et italien |
| **Albo d'Oro** | ASP.NET WebForms | au registre. Morts italiens de 14-18 |

*Ce que le dossier a appris et que leur catalogue n'a pas : pour le Frioul, **1816-1871 n'est
ni chez Antenati ni chez FamilySearch** — le curé était l'officier d'état civil, et la copie
est à la **curie épiscopale**. Voir le carnet.*

---

## Amériques, Océanie

| service | accès | notes |
|---|---|---|
| **NARA** (États-Unis) | API, jeu de données ouvert | noter NAID, record group, série |
| **Library of Congress** | API JSON/YAML, sans clé | identifiants de collection et champs de droits |
| **Chronicling America** | API `loc.gov` | presse ; vérifier l'OCR sur l'image |
| DPLA | API (clé) | citer l'institution d'origine, pas l'agrégateur |
| Ellis Island | compte | vérifier l'image du manifeste et la ligne |
| Fold3 · Newspapers.com · Findmypast | abonnement | |
| Find a Grave · BillionGraves | libre / abonnement | distinguer la transcription de la pierre du reste |
| **CEMLA** · **AGN** (Argentine) | libre | au registre |
| Bibliothèque et Archives Canada | libre | pas d'API publique vérifiée |
| **Canadiana / Héritage** | **IIIF documenté** | citer la bobine et la page |
| **Trove** (Australie) | API (clé) | presse ; vérifier l'OCR |
| Archives NZ · **Papers Past / DigitalNZ** | API v3 | |

---

## Persécutions, déplacements, migrations

| service | accès | notes |
|---|---|---|
| **Arolsen Archives** | recherche et téléchargement | au registre. Travail forcé, camps, personnes déplacées |
| JewishGen | inscription | index juifs mondiaux |
| Yad Vashem | libre | les feuilles de témoignage demandent un recoupement |
| USHMM | catalogue et collections | archives de la Shoah, témoignages oraux |
| OBD Memorial · Pamyat Naroda · Podvig Naroda | libre | pertes et décorations soviétiques |

---

## Plateformes commerciales

Ancestry, MyHeritage, Findmypast, **Geneanet** (au registre), YourRoots : abonnement, et
**l'export GEDCOM de l'utilisateur est souvent la seule voie propre**. Les services d'ADN
(AncestryDNA, MyHeritage, 23andMe, FamilyTreeDNA, GEDmatch) demandent un consentement
explicite et ne se traitent jamais sans lui.

> **⚠️ UN INDEX N'EST PAS UN FONDS**, et ça vaut pour toute cette page. Ce qu'on interroge
> sur ces plateformes, c'est ce que des bénévoles ont dépouillé — jamais la totalité des
> registres. **Zéro résultat n'y prouve rien** : c'est le seul endroit où l'absence ne se
> note même pas comme un négatif.
