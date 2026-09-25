---
name: archives-fr
description: Dépouiller les archives d'état civil en ligne — ouvrir un portail, retrouver un registre, tirer ses vues, lire un acte au bon grossissement, et consigner ce qu'on a trouvé sans fabriquer d'ancêtre. À charger dès qu'il est question d'un acte d'état civil ou paroissial, d'un registre, d'une commune, d'archives départementales, d'une fiche matricule, d'un recensement, d'un GEDCOM, ou de lire l'image d'un registre ancien. Couvre près de la moitié des départements français, l'Italie, l'Algérie, et un catalogue mondial pour le reste. La méthode ne dépend d'aucun pays ; les fiches des fonds ouverts sont dans references/portails.md.
---

# Chercher dans les archives d'état civil en ligne

Chaque règle ci-dessous vient d'une erreur commise et payée. Elles sont écrites en clair
pour qu'on ne les repaie pas.

**LA SKILL S'APPELLE `archives-fr`, ELLE NE L'EST PLUS TOUT À FAIT, ET C'EST LA MÉTHODE QUI
L'A DÉBORDÉE.** Elle est née sur la Loire et la Haute-Loire ; le 27 août 2026 elle a servi
telle quelle à ouvrir le **Portale Antenati** italien, sans qu'une seule règle ait à être
réécrite. Identifier le moteur, lire la réponse en entier avant de deviner une URL, ne jamais
reconstruire un libellé de commune, recompter contre le total annoncé, ne pas conclure d'une
recherche négative : rien de tout ça n'est français. **Le nom reste** — c'est la commande
qu'on tape — mais ne pas hésiter à la charger pour un acte étranger.

## Le principe, et il décide de tout

**LE CODE VIT PAR MOTEUR, PAS PAR DÉPARTEMENT.** Il y a une centaine de départements et
**six moteurs de portail** — Boscop (alias Ligeo-Archives), Arkothèque, Naoned/Mnesys,
Anaphore, plus quelques développements maison. Écrire un module par département reviendrait
à écrire cent fois la même chose ; écrire un module par moteur ouvre quinze départements
d'un coup. Le département n'est alors plus que de la **configuration**.

**ET LES OUTILS DE LECTURE NE DÉPENDENT DE RIEN.** Ils travaillent sur des JPEG déjà sur le
disque et ignorent d'où ils viennent. C'est voulu : la moitié des images arrivent par un
autre chemin — téléchargement manuel, envoi d'un cousin, photo d'un livret de famille.

## Où vivent les images

**TOUT CE QUI EST ACTE OU IMAGE VIT SUR `<archives>/\`**, jamais dans un dépôt
de code et jamais dans un répertoire temporaire de session.

```
<archives>/\
    AD<NN> - <Commune>\<Registre>\vNNN.jpg     registres tirés d'un portail
    _corpus\actes\                              actes isolés, images reçues, livrets
    actes-decoupes\                             les découpes publiées
    _planches\                                  planches de travail
```

Un registre se **désigne** au lieu de se déclarer — « 37/luble/D 1837 » suffit. Rien à
configurer, donc rien à oublier.

### ⚠️ ET CETTE RÈGLE A ÉTÉ ENFREINTE DE 4,4 GIGAOCTETS — parce qu'il en manquait une seconde

**Le 12 septembre 2026, le disque C: est tombé à ZÉRO OCTET DISPONIBLE en pleine session**, et
l'écriture dans `data/` a échoué. Le corpus n'a rien perdu — `corpus_io.sauve()` écrit dans un
`.tmp` avant de basculer, et c'est précisément le cas contre lequel il a été écrit —, mais tout
s'est arrêté.

La cause : **5,5 Go dans `%TEMP%\claude\`**, dont **4,4 Go d'images de registres** laissées par
sept sessions successives, la plus vieille du 7 septembre. Le généalogiste : *« 5,5 Go dans un temp… jamais
nettoyé, c'est abusé ! »*

**LA RÈGLE CI-DESSUS ÉTAIT DÉJÀ ÉCRITE, EN GRAS, ET N'A RIEN EMPÊCHÉ** — parce qu'elle dit où
vivent les images *qu'on garde*, et qu'un balayage produit surtout des images **qu'on ne garde
pas** : huit cents demi-pages, des zooms à trois grossissements, des planches d'essai. Elles n'ont
rien à faire sur `X:`. Personne n'avait donc tort de les mettre dans le scratchpad — **tort était
de les y laisser.**

> **UN BALAYAGE SE NETTOIE À LA FIN DE LA SÉANCE.** Ce qui mérite d'être gardé part sur `X:` —
> l'acte découpé dans `actes-decoupes\`, la planche dans `_planches\`. **Tout le reste se
> supprime avant de rendre la main**, et ça se dit dans le compte rendu, en une ligne. Un
> gigaoctet par session de dépouillement, c'est le débit réel mesuré.

Et deux déchets qu'on n'imagine pas : **les profils Chrome des modules** (`.chrome-*` dans le
scratchpad) pesaient **514 Mo** à eux seuls, et **un `bobine2.mp4` de 337 Mo** dormait depuis le
7 septembre. Un profil Chrome ne se garde jamais entre deux séances.

## Ouvrir un portail qu'on ne connaît pas

**D'ABORD, REGARDER S'IL EST DÉJÀ RÉPERTORIÉ.** Les fonds qu'on sait interroger sont dans
[`references/portails.md`](references/portails.md) ; **ce qui existe ailleurs et qu'on n'a
jamais touché est dans [`references/monde.md`](references/monde.md)** — une centaine de
services, par pays, avec leur mode d'accès. Rien n'y est vérifié par ce dossier, mais ça
évite de redécouvrir un fonds de zéro, et ça dit souvent qu'une API existe là où on
s'apprêtait à piloter un navigateur.

### ⛔ ET ON VÉRIFIE LES ACCÈS DANS CET ORDRE — le HTML est le DERNIER recours

**On commence presque toujours par la fin de cette échelle, et c'est la faute la plus chère
du dossier.** Piloter un vrai Chrome sur du HTML, c'est rétro-concevoir une interface qui
change sans prévenir ; une API, une norme, un export sont des **contrats**.

| rang | voie | comment on l'essaie |
|---|---|---|
| 1 | **API officielle** | la page développeur, et `{base}/js/routing` quand c'est du Symfony |
| 2 | **export utilisateur** / téléchargement fourni | regarder l'interface |
| 3 | **jeu de données ouvert** | `data.gouv.fr`, la page open data du service |
| 4 | **IIIF** — les images | le manifeste ; souvent dans `media[].location.iiif` de la visionneuse |
| 5 | **OAI-PMH / SRU** — le catalogue et l'inventaire | `python scripts/archives/oai.py <dept>` |
| 6 | **autorisation écrite** | un courriel au service |
| 7 | **HTML, prudemment** | Chrome fenêtré — et seulement ici |

**Les quatre normes, et ce que chacune donne :**

- **IIIF** rend **les images** — toutes les vues d'un registre en une requête, dans l'ordre.
  C'est une norme, pas une API maison, et ça remplace un Chrome piloté par une ligne de code.
- **EAD** rend **l'inventaire** — fonds, série, cote, dates. C'est exactement ce qu'on
  reconstitue à la main en pilotant un navigateur pour savoir *quel registre couvre quelles
  années*, et c'est là que sont nos pièges les plus chers : le libellé de commune qui se lit
  et ne se reconstruit pas, le filtre qui rend les 8 409 registres du département en ayant
  l'air d'un résultat de commune.
- **OAI-PMH** est **la livraison en gros** — « donne-moi tout ton catalogue, paginé ». C'est
  par là que l'EAD arrive : l'EAD ne se sonde pas seul.
- **SRU** est **la recherche normalisée** sur un catalogue. Gallica le sert.

**Mesuré le 20 septembre 2026 : six fonds sur soixante-trois répondent en OAI-PMH, et tous
servent l'EAD** — l'AD37, l'AD19, l'AD14, l'AD51, l'AD58 et le SHD de Vincennes. **Ce n'est
pas une propriété du moteur** : l'Eure et le Haut-Rhin sont des Naoned comme cinq d'entre eux
et rendent 404. On sonde chaque portail, on n'en déduit pas du voisin. Détail, sonde et
limites du négatif : section « OAI-PMH et EAD » du [carnet](references/portails.md).

1. **Identifier le moteur** — il se signe dans le HTML de la page d'accueil : chercher
   `arkotheque`, `boscop`, `ligeo`, `mnesys`, `naoned`, `anaphore`, ou la balise
   `<meta name="Generator">`. Cinq minutes, et ça décide de tout le reste.
   **Un nom d'éditeur et un nom de produit désignent le même moteur** — Boscop édite Ligeo,
   Naoned édite Mnesys : voir la table des moteurs dans `references/portails.md`. Et
   **la vitrine n'est pas le moteur** : trois portails sur six servent leur CMS sur un
   domaine (TYPO3, Umbraco) et leurs archives sur un autre.
2. **Si le moteur existe déjà** : ajouter une fiche de configuration, et c'est tout. C'est
   le cas nominal — vérifié trois fois de suite, l'AD45, l'AD67 et l'AD49.
3. **Sinon** : écrire le module, et **capturer le trafic réseau d'une vue affichée** plutôt
   que de deviner les URL.
4. **Écrire sa fiche en repartant**, pièges compris. C'est la seule chose qui empêche la
   session suivante de tout repayer.

**ET AVANT TOUT ÇA : CHERCHER SI LE PORTAIL PUBLIE SA PROPRE DOCUMENTATION.** Beaucoup sont
des applications Symfony, et **`{base}/js/routing` rend alors la table de routage complète en
JSON** — 583 routes à l'AD49, chemins compris. C'est de là que sont sortis en cinq minutes
l'API du moteur, la signature exacte de l'endpoint des images et l'existence d'un proxy IIIF,
là où l'AD43 avait coûté une soirée de tâtonnement. Chercher `fos.Router`, `routing`, ou un
`.js` de configuration dans le HTML.

**DE MÊME, UNE API DE RECHERCHE SE DÉCRIT SOUVENT ELLE-MÊME.** Interrogée **sans aucun
filtre**, elle rend la liste de ses champs, de ses tris et de ses modes de restitution — donc
tous les identifiants qu'on allait chercher dans le HTML d'un formulaire. Ça vaut le détour
avant de gratter une page : à l'AD43 comme à l'AD49, **la page du formulaire ne contient aucun
`<input>`**, et le chercher est une perte de temps.

## Interroger un portail — les pièges qui coûtent des jours

**⛔ UN `CERTIFICATE_VERIFY_FAILED` N'EST PAS UN PROBLÈME DU SITE, ET CE DOSSIER A ACCUSÉ QUATRE
SITES INNOCENTS.** « Le magasin de certificats refuse `francearchives.gouv.fr` », « le certificat
de matchID a expiré », « l'API de Wikipédia ne répond pas », « `data.gouv.fr` échoue » — quatre
fiches, quatre coupables, **une seule cause** : le magasin de racines que Windows sert à Python
porte une racine périmée, et ces quatre-là sont chez Let's Encrypt. Pire, la « réparation »
retenue avait été de **désactiver la vérification**, au motif que c'est de la lecture seule sur un
portail public. Ce n'est pas une réparation.

> **`python scripts/archives/tls.py`** interroge quatre témoins et dit OK ou KO ;
> **`python scripts/archives/tls.py reparer`** met `certifi` et `truststore` à jour.
> Un `import tls` en tête d'un module répare tout le processus, et les moteurs l'ont déjà.
> **À lancer dès qu'un certificat est refusé, avant d'écrire quoi que ce soit sur le site — et de
> temps en temps sans raison, parce que `certifi` est un fichier figé qui se repérime comme le
> magasin de Windows s'est repérimé.**

**UN VRAI CHROME FENÊTRÉ, JAMAIS `curl` NI LE *HEADLESS SHELL*.** Les portails se
défendent : 403 en Loire, « Attack detected » dans le Loiret, une preuve-de-travail
**Anubis** dans le Bas-Rhin qu'un vrai navigateur résout seul en une dizaine de secondes —
il faut lui laisser le temps avant de lire la page. Rien n'est masqué, `navigator.webdriver`
reste à `true` ; c'est la fenêtre qui compte, pas la dissimulation.

**UN NOM DE CHAMP NE SE DEVINE PAS, ET UNE CASSE DIFFÉRENTE SUFFIT À TOUT CASSER — EN SILENCE.**
Le champ de commune de l'état civil de l'AD16 s'appelle **`REch_commune`** : capitale E, minuscule
c. Interrogé en `RECH_commune`, le moteur **ignore le paramètre inconnu** et rend les **8 409
registres du département triés par date** — une page qui ressemble parfaitement à un résultat de
commune, avec une colonne « COMMUNE » et des noms plausibles. C'est la même famille de piège que
les paramètres `size` et `limit` inventés, appliquée aux critères.

**Donc : le nom d'un champ se LIT sur le formulaire, jamais ne se transpose d'un portail à
l'autre ni d'un fonds à l'autre.** Le même portail de la Charente filtre la commune **en texte
clair** sur les recensements (`RECH_geogname=Dignac`) et **exige le md5 d'une facette** sur l'état
civil : deux fonds, deux comportements, aucun moyen de le deviner. Et la vérification qui ne ment
pas tient en une requête : **comparer le total obtenu à celui d'une requête SANS filtre.** S'ils
sont égaux, le filtre n'a pas filtré.

**ET LE « MUR » D'UN TOKEN DE FACETTE N'EN EST PAS TOUJOURS UN.** Une fiche de ce carnet a porté
une demi-journée la mention « le token de `arcfacette.php` n'est pas dans le HTML, on ne peut donc
pas filtrer par commune ». C'était faux : **ce portail-là n'attend aucun token**, l'appel passe
tel quel. La conclusion avait été tirée d'un token cherché et non trouvé, pas d'un appel essayé et
refusé. **Piloter le formulaire à la main et écouter le trafic** rend la réponse en cinq minutes,
et c'est la seule méthode qui ne suppose rien.

**LIRE LA RÉPONSE EN ENTIER AVANT DE DEVINER UNE URL.** Huit chemins ont été essayés à la
main sur un portail pour trouver la liste des vues d'un registre — `/medias/`, `/img/`,
`/api/media/`, la racine… — et la fiche s'est refermée sur « l'endpoint n'est pas trouvé ».
Une semaine plus tard, la réponse JSON de la visionneuse s'est révélée porter, dans
`media[].location.iiif`, **l'adresse du manifeste qui résout tout**. Elle y était depuis le
premier appel.

**BEAUCOUP DE PORTAILS SERVENT UN MANIFESTE IIIF**, et six en servent un dépôt OAI-PMH avec
l'EAD. **Ce sont des normes, pas des API maison, et elles s'essaient AVANT d'écrire quoi que
ce soit** — voir l'échelle d'accès en tête de « Ouvrir un portail qu'on ne connaît pas », qui
dit dans quel ordre et avec quel outil.

**UN PARAMÈTRE INVENTÉ EST IGNORÉ EN SILENCE.** `size`, `limit`, `from`, `resultSize` :
selon le portail, ils rendent toujours la première page, ou plafonnent sans le dire —
`resultSize=200` rend 25 réponses dans le Loiret. **Toujours recompter contre le total
annoncé.**

**ET UNE PAGE 2 VIDE NE VEUT PAS DIRE « FIN DE LISTE » : ELLE PEUT TENIR À UN COOKIE.** À
l'AD17, `?page=2` sans cookie rend une page vide ; avec le `PHPSESSID` posé par la recherche, il
rend les vingt suivantes. Le module Archinoë a ainsi rendu **20 registres de Royan sur 85**
pendant deux semaines, sans un mot — alors que la recette était notée dans `portails.json` pour
les conscrits. **Un client d'archives tient une session à cookies, toujours, et lit les pages
jusqu'à ce qu'une page n'apporte plus rien de neuf.**

**UN PLAFOND PEUT N'ÊTRE QU'UNE VALEUR PAR DÉFAUT.** Archinoë rendait toute image à 1800 px de
haut, et la fiche en avait conclu « demander plus ne rend pas plus ». Il manquait le paramètre
`h` : avec lui, le master entier sort, 12 359 × 8 880 pour un plan de Royan. **Le nom du fichier
servi le disait** — `…_4264_1800_…_img.jpg`. Quand une réponse porte un nombre qu'on n'a pas
demandé, c'est un paramètre qu'on n'a pas passé.

**LE CADASTRE EN LIGNE, CE SONT DES PLANS, PAS DES PROPRIÉTAIRES.** L'AD17 le sert par le même
moteur que l'état civil (`archinoe.py 17 cadastre <commune>`, puis `tirer-plan`) : il dit où est
une parcelle, jamais à qui elle est — ça, ce sont les **matrices**. Et les séries ont des trous :
Royan n'a **aucun plan entre 1838 et 1964**. Avant de promettre qu'un plan « tranchera », lister
les plans de la commune et regarder leurs dates.

**UN MOTEUR QUI *CLASSE* AU LIEU DE FILTRER REND TOUJOURS QUELQUE CHOSE**, trié par
ressemblance et l'air crédible : FamilySearch interrogé sans son `f.collectionId` a rendu, pour
« Anna VOLPATTI née à Valvasone », une Anna Volpatti **née en 1879, morte à San Francisco en
1953** — les lignes affichaient « Italy » là où on lisait « Valvasone ». Bon à savoir avant de
retenir un résultat.

**MAIS RESSERRER LE FILTRE EST SOUVENT LA PIRE RÉPONSE, ET C'EST L'ERREUR QUE J'AI FAITE.** Le
27 août 2026, voyant ça, j'ai reproché au généalogiste d'avoir retiré ses filtres et lui ai fabriqué
quatre recherches « propres », verrouillées sur la collection. **Trois ont rendu ZÉRO, et la
quatrième n'a rendu que l'acte qu'on avait déjà.** Sa recherche large, elle, avait sorti un
recensement argentin de 1895 qui a ouvert une branche entière — que ma version filtrée
n'aurait jamais pu rendre.

> **UN INDEX N'EST PAS UN FONDS.** Ce qu'on interroge sur FamilySearch, Geneanet ou un relevé
> d'association, c'est ce que des bénévoles ont dépouillé — jamais la totalité des registres.
> Dans un index partiel, **filtrer transforme un « pas encore dépouillé » en « n'existe pas »**.
> Zéro résultat n'y prouve rien du tout : c'est le seul endroit où l'absence ne se note même
> pas comme un négatif.

**D'où la manœuvre juste, qui est celle du généalogiste** : ratisser large d'abord, trier à l'œil
ensuite. On accepte le bruit — quelques Californiennes homonymes — parce que c'est le prix des
trouvailles latérales, et elles sont nombreuses : une émigration, un remariage, un enfant qu'on
ne cherchait pas. **Puis, quand l'index se tait, on passe aux IMAGES** : la fiche d'un acte
indexé donne son numéro de film, et le film se feuillette en entier. C'est là qu'est l'acte que
personne n'a saisi.

**UNE ABSENCE N'EST UN FAIT QUE SI L'ON A VÉRIFIÉ COMMENT L'OUTIL DIT « RIEN ».** Le test
« la page contient-elle *Aucun* ? » a fait déclarer une commune dépourvue de registres —
elle en a 158. Le mot venait du panneau de facettes, « Aucune valeur disponible », affiché
sur presque toutes les pages. **Tester la phrase entière, et la vérifier une fois sur une
requête dont on sait qu'elle rend des résultats.**

**UN LIBELLÉ DE COMMUNE NE SE RECONSTRUIT PAS, IL SE LIT.** La plupart des portails exigent
la forme exacte de leur vocabulaire — « Courcelles-de-Touraine (Indre-et-Loire, France) » en
Touraine, « GOUGENHEIM » en majuscules nues dans le Bas-Rhin. Elle est dans le HTML du
formulaire, parfois **deux fois encodée** : entités HTML par-dessus échappements JSON, si
bien que « Rillé » y dort sous la forme `Rill&eacute;`. Décoder les deux couches avant de
conclure que la commune est absente. **Zéro réponse = mauvaise graphie**, jamais « la
commune n'y est pas ».

**ET UN TYPE D'ACTE N'EST PAS TOUJOURS TYPÉ.** Des tables décennales portent parfois un
titre nu — « 1903-1912 » — et un filtre sur « Table decennale » ne rend rien alors qu'elles
sont en ligne. **Quand un filtre rend zéro, lister toute la commune.**

## Lire une image de registre

**CETTE RECETTE EST DÉJÀ ÉCRITE — NE PAS LA RÉÉCRIRE.** Tout ce que dit cette section est
implémenté dans un moteur unique, `scripts/archives/lire/nas.py`, **et le département n'y est
qu'un argument**. Les six outils qui l'ont précédé — `page.py`, `zoomb.py`, `sp.py`,
`marges.py`, `tete.py`, `strip.py` — ne sont plus que des façades qui gardent leur ligne de
commande : ils passent tous par lui.

**ET IL N'Y A RIEN À DÉCLARER POUR UN NOUVEAU DÉPARTEMENT.** Le NAS étant rangé
`AD<NN> - <Commune>/<Registre>/vNNN.jpg`, un registre se **désigne** au lieu de se configurer
— sans accent, sans casse, sans nom exact. Une désignation ambiguë est refusée avec la liste
des candidats : une commande qui ouvre le mauvais registre est pire qu'une commande qui échoue.

```bash
python nas.py l 37                                    # les registres d'un département
python nas.py   "37/luble/D 1837" 124 127             # rendre les demi-pages à 1990 px
python nas.py t "43/saint-pal/BMS 1737" 90 105 t.png  # cadrer : 15 vues en UNE image
python nas.py m "42/usson/BMS 1773" 80 92 marge       # balayer les marges (type, hameau)
python nas.py z "37/villiers/D 1906" 26 G 0.30 0.40 z.png 0.28 1.0 1   # zoomer sur l'encre
```

*Écrire un script de lecture jetable est la faute que ce moteur existe pour empêcher : le
26 août 2026, neuf actes d'Indre-et-Loire ont été lus avec un script du répertoire temporaire
de la session, perdu avec elle, parce que les outils d'alors ne savaient parler qu'à l'AD42 et
à l'AD43.*

**UNE DEMI-PAGE PAR IMAGE, À 1154 × 1990 px.** Entièrement lisible, une quinzaine d'actes,
~3 100 jetons. **Au-delà de 2000 px sur le grand côté, l'image est réduite avant lecture** :
rendre plus grand ne rend rien, et tout ce qu'on gagne sur les blancs du papier est gagné
sur l'écriture.

**RECADRER SUR LA BOÎTE D'ENCRE, APRÈS AVOIR ÔTÉ LE FOND DU SCANNER.** Beaucoup de portails
photographient le registre au milieu d'un large fond noir — 25 % de la surface dans le
Bas-Rhin, 12 à 17 % en Touraine. Un détecteur qui cherche les pixels *sombres* prend ce fond
pour du texte et ne recadre rien : il faut d'abord chercher la zone **claire**, le papier.
**Mais une boîte d'encre qui couvre toute la page n'est pas toujours une panne** : les pages
réglées de lignes imprimées n'ont rien à recadrer.

**ET LE FOND DU SCANNER N'EST PAS TOUJOURS NOIR — LE MAINE-ET-LOIRE L'A EN BLANC, PLUS CLAIR
QUE LE PAPIER DU REGISTRE.** La règle ci-dessus, écrite sur le Bas-Rhin, s'y retourne
exactement : *chercher la zone claire* retient alors le fond et laisse le feuillet, qui
n'occupe que 45 % de la largeur, perdu au milieu du vide. **Regarder une vue avant de faire
confiance au cadrage** — les trois quarts des 1990 px peuvent partir en papier blanc sans que
rien ne le signale, puisque le texte reste lisible.

**Deux réparations « évidentes » ont été essayées et rejetées le 27 août 2026**, il ne faut
pas en tenter une troisième à l'aveugle : détecter le feuillet par sa **texture** (un fond de
scanner est uniforme) perd 80 % d'une vue de Touraine ; décider du sens par l'écart de
luminosité **bords contre centre** mesure le mauvais signe, parce que le centre d'une telle vue
est encore du fond. **En attendant, on cadre à la main par fractions** — c'est ce que fait
`nas.py z`, qui ne dépend d'aucune détection.

**SIMPLE OU DOUBLE PAGE : C'EST L'ORIENTATION QUI TRANCHE, PAS LA LARGEUR.** Un seuil en
pixels se trompe dans les deux sens — des doubles pages font 2500 px et passent pour des
pages simples, texte coupé en deux. Une double page est plus large que haute.

**LE NUMÉRO DE VUE EST DANS LE NOM DU FICHIER, PAS DANS SA POSITION.** Un registre n'est
presque jamais tiré en entier : on prend la fenêtre d'une année, puis une autre dix ans plus
loin. Indexer la liste triée rend alors la vue 60 quand on demande la 36 — erreur
silencieuse, qui fait lire un acte pour un autre et conclure qu'une année est vide.

**LE ZOOM SE PREND AUX MÊMES FRACTIONS QUE LE RENDU**, sur la boîte d'encre : on repère sur
l'image qu'on vient de lire, sans recalculer. Pour un mot pâle ou dans l'ombre de pliure,
**diviser par un fond flouté** tue le dégradé. (Sur une page entière, en revanche, cette
division est *pire* : elle fait ressortir le grain du papier. Elle ne vaut que sur une
fenêtre déjà cadrée.)

**POUR CADRER UN REGISTRE SANS LE LIRE** : empiler les premières lignes de chaque demi-page.
Quinze vues en une image, contre trente images à 3 100 jetons pièce — la première ligne d'un
acte porte toujours sa date. **Certaines vues sont photographiées la tête en bas** ; prévoir
de les retourner plutôt que de les déclarer illisibles.

**ET ELLE SERT À DATER, PAS À CHERCHER — LA CONFONDRE A COÛTÉ UNE SEMAINE.** Une demi-page
d'Ancien Régime porte **trois ou quatre actes** ; la bande haute n'en montre **qu'un, le
premier**. Chercher un patronyme aux têtes, c'est donc regarder un tiers du registre en croyant
l'avoir vu. Ce n'est pas « un négatif moins sûr » : **c'est un outil qui ne répond pas à la
question posée.**

Le 6 septembre 2026, Méon a été déclaré négatif sur 1678-1690 après un balayage aux têtes, et
tout un raisonnement a été construit dessus — « le mariage n'est ni à Méon ni à Meigné », « la
règle du mariage chez la mariée est prise en défaut une deuxième fois », un plan de
dépouillement à neuf paroisses. **Le mariage était à Méon, le 2 août 1689, TROISIÈME ACTE de la
vue 99D.** Il a fallu qu'un correspondant Geneanet donne la date au jour pour rouvrir une porte
qu'on avait fermée soi-même.

**Donc : les têtes pour trouver où commence une année. Puis la pleine page, ou les marges quand
le scribe y écrit les noms. Et un compte rendu dit TOUJOURS par quelle méthode le négatif a été
obtenu** — « lu en pleine page » et « balayé aux têtes » ne sont pas la même affirmation.

### ⚠️ ET UN NÉGATIF QU'ON NE RETROUVE PAS SERA REFAIT — il doit porter les mots qu'on tapera

Tout ce qui précède dit comment obtenir un négatif solide. Rien ne disait qu'il faut pouvoir le
**retrouver**, et c'est la moitié de sa valeur : un négatif sert à ne pas repayer la recherche,
donc il ne vaut que si la session suivante tombe dessus.

Le 7 septembre 2026, le CEMLA a été interrogé sur **sept graphies** du nom DEGIROLAMI pour y
chercher Ines MIGOT et sa fille — un travail sérieux, trois entrées au `journal.md`, une source
détaillée, le compte des lignes et des doublons. La ligne du TODO qui le portait s'intitulait
**« Où sont passées Ines MIGOT et Anna Maria ? »**. Pas un patronyme, pas le nom du fonds. Le
14 septembre, une session a cherché « DEGIROLAMI », puis « cemla », n'a trouvé que la source
elle-même — et **a proposé au généalogiste de refaire la recherche**. C'est lui qui a arrêté le geste :
*« Cemla déjà cherché… mais cette ligne est ingrepable. »*

**Une ligne de négatif porte donc, dans son TITRE :**

- **le ou les PATRONYMES**, et toutes les graphies essayées — c'est ce qu'on tapera ;
- **le nom du FONDS** interrogé (CEMLA, AGN, Antenati, l'AD et sa cote) ;
- **le mot qui dit la nature de la question** — migration, mariage, décès.

`« Où sont passées Ines et Anna Maria ? »` → `« QUAND INES MIGOT ET SA FILLE ANNA MARIA
DE GIROLAMI SONT-ELLES ARRIVÉES EN ARGENTINE ? — migration, CEMLA, DEGIROLAMI / DE GIROLAMI /
GIROLAMI »`. La question est la même ; la seconde se retrouve.

**Et le corollaire vaut pour celui qui cherche : avant de proposer une recherche, ouvrir la
source qui porte déjà son nom.** Voir qu'un `src-…` existe ne suffit pas — il faut le LIRE. Une
source qu'on n'a pas ouverte ne dit pas ce qu'on croit qu'elle dit.

**POUR BALAYER UNE PLAGE SUR UN HAMEAU** : empiler la bande de marge, pleine hauteur. La
marge porte le **type d'acte** et le **hameau**. Bon filtre pour une cible rare, mauvais
pour tout le reste — et il s'effondre dès que la famille habite le bourg, qui est la valeur
la plus fréquente. **Elle ne donne jamais le patronyme.**

**ET ELLE NE VOIT PAS LES MARIAGES** : leur texte part du bord gauche, ils n'ont pas de
mention de marge. Une plage balayée par les marges est donc négative pour les baptêmes et
les sépultures, et **muette sur les mariages**.

**ELLE NE VOIT PAS NON PLUS CE QUE LE TIMBRE RECOUVRE, ET ÇA A COÛTÉ UN ANCÊTRE.** Sur les
registres d'Empire, le **timbre fiscal imprimé** — une vignette de 25 ou 75 centimes — occupe
justement le coin haut de la marge. Le 26 août 2026, un balayage des marges de Lublé pour
1808 et 1809 a conclu « aucun CHALLE », et le négatif est entré au dossier noir sur blanc :
Jean CHALLE y était né le 22 septembre 1808, et sa mention de marge passait à moitié sous le
timbre. **Un négatif de marges prouve qu'on a balayé, pas qu'il n'y a rien.**

**LA PARADE EST GRATUITE, ET ELLE VAUT MIEUX QUE LES MARGES** : dans beaucoup de registres
d'état civil, **chaque année se clôt par sa table annuelle** — naissances, mariages et décès,
sur une ou deux vues. C'est un index contemporain de l'acte, il ne dépend d'aucune image, et
il couvre les trois types y compris les mariages. **Chercher la table annuelle avant de
balayer les marges** ; c'est elle qui a rendu l'acte manqué, et qui l'a confirmé.

**QUATRE TENTATIVES D'AUTOMATISER LA DÉTECTION DES MARIAGES ONT ÉCHOUÉ**, et il faut le
savoir pour ne pas en tenter une cinquième : les lignes « plus à gauche que la médiane » ne
marchent pas (sur une page de mariages, la médiane *est* le bord) ; le bord gauche de
l'encre attrape le liseré du scan ; l'exclure améliore le profil sans séparer ; et la
densité d'encre en marge donne des distributions qui se recouvrent entièrement.
**On lit à l'œil.**

**RENDRE UNE IMAGE N'EST PAS LA LIRE, ET UN COMPTE RENDU DOIT DIRE CE QU'ON A REGARDÉ.** Le
28 août 2026, un mariage a été déclaré introuvable après que la session eut annoncé « les vues
300-309 relues en pleine page ». **La vue 303 n'avait jamais été ouverte** : elle avait été
rendue avec les autres, son nom était passé dans la sortie du script, et seules 301, 302 et 304
avaient été lues. L'acte était sur la 303, et il faisait remonter la branche de deux
générations. **Le négatif ne porte que sur les images effectivement regardées** — les compter,
une par une, avant d'écrire qu'une plage est vide.

**QUAND ON ATTEINT LA RÉSOLUTION NATIVE, ON S'ARRÊTE.** Agrandir six fois un scan n'ajoute
aucune information. Le mot se note `[non lu]` et on demande une seconde paire d'yeux.

**MAIS AVANT DE NOTER `[non lu]`, CHERCHER LE SECOND EXEMPLAIRE — IL EXISTE PLUS SOUVENT
QU'ON NE CROIT.** Un acte d'Ancien Régime a été écrit **deux fois**, dans le registre du curé
et dans son double de greffe ; l'état civil a de même une **collection communale** et une
**collection départementale**. Beaucoup de portails ont numérisé les deux, et le disent dans
une colonne du tableau de résultats. **Deux plumes indépendantes copiant le même acte donnent
deux chances au même mot** : en Haute-Loire, deux copies de l'année 1747 ont tranché en une
image un jour de baptême que quatre zooms n'avaient pas tranché, et un âge au décès sur lequel
trois lectures se contredisaient. **Ça vaut mieux que n'importe quel traitement d'image**, et
c'est gratuit.

## Chercher un patronyme

**IL N'A PAS DE FORME FIXE, ET IL FAUT CESSER DE VOULOIR LA TROUVER.** Un même nom peut
avoir sept graphies — PAIRÉ, PAYRÉ, PAIRET, PERRET, PEYRET, PAYRE, PEYRA — parfois trois sur
un seul acte. HUME s'écrit HUMES en 1613. Un lieu aussi change : Gougenheim s'écrit
**Gugenheim** sous l'administration allemande, et le catalogue moderne ne connaît que la
forme française. **Chercher un nom, c'est lire toute la section de la lettre**, jamais
interroger une chaîne.

**UN SCRIBE ABRÈGE.** Un registre écrit « M. / gr. n. » là où le registre voisin écrit
« Grange neuve » en toutes lettres. Avant de conclure qu'un acte n'existe pas, vérifier
comment *ce* scribe-là écrit le mot cherché.

**UN NÉGATIF SE NOTE.** « Vues 48-70 dépouillées, du 5 septembre 1752 au 26 septembre 1753,
aucun PEYRET » vaut autant qu'une trouvaille : c'est ce qui évite de relire.

**UNE FEMME MARIÉE N'EST PAS INDEXÉE SOUS LE NOM QU'ON LUI CONNAÎT, ET C'EST LE MUR LE PLUS
FRÉQUENT DE TOUT LE MÉTIER.** Les fichiers d'état civil — le fichier des décès de l'INSEE au
premier chef — indexent sous le **NOM DE NAISSANCE**. Les listes nominatives de recensement, au
contraire, inscrivent les épouses sous le **NOM DU MARI**. Une aïeule connue de la famille comme
« Madame X » est donc invisible des deux côtés à la fois : le fichier ne connaît pas X, et le
recensement ne dit pas son vrai nom.

**LA PARADE EST DANS LE MÉNAGE, PAS DANS LA LIGNE DE L'INTÉRESSÉE.** Un recensement porte les
ascendants qui vivent au foyer, avec leur lien au chef : une **« belle-mère »** du chef de ménage
est la mère de son épouse, et **elle, on l'inscrit sous SON nom de femme mariée à elle** — celui
du père de l'épouse. Cette ligne-là donne donc le nom de jeune fille qu'on cherchait.

Le 9 septembre 2026, le mur de « Margot DANNEPOND » est tombé comme ça :
la ligne « HAYS Flavie, 1862, Fouquebrune, belle-mère » a rendu **HAYS**, le fichier des décès a
rendu la ligne unique, et l'acte de naissance a montré que la mère elle-même s'appelait en
réalité **PICHON** — le même piège, une génération plus haut. **Descendre d'un cran dans le
ménage à chaque fois : le nom cherché est toujours sur la ligne d'à côté.**

**ET UNE SÉRIE PEUT ÊTRE COUPÉE PAR UNE FRONTIÈRE ADMINISTRATIVE AU MILIEU DE LA RUE.** Dans un
recensement de ville, les quartiers sont dépouillés séparément et **l'ordre alphabétique des rues
recommence dans chacun** — une dichotomie sur l'ensemble du registre ne peut donc pas marcher, et
on tombe sur un H puis sur un B trois cents vues plus loin. Pire : une rue qui sert de limite est
**scindée en deux**, les numéros pairs dans un quartier et les impairs dans l'autre, à des
centaines de vues d'écart. Le seul indice est le mot **« (pair) »** ajouté au nom de la rue, et il
se lit comme une précision anodine. Dix-sept pages ont été balayées du mauvais côté avant qu'il ne
soit compris. **Quand un dépouillement de rue ne rend pas la maison cherchée, vérifier d'abord
qu'on est du bon côté de la chaussée.**

**ENFIN, LE CLASSEMENT ALPHABÉTIQUE SE FAIT SUR LE MOT DISTINCTIF, JAMAIS SUR « RUE ».**
« Rue Paul Abadie » est à A, « Boulevard Aristide Briand » à B, « Rempart de l'Est » à E,
« Route de Bordeaux » à B. Chercher « rue de Limoges » à R ne rend rien.

## Chercher un nom dans un IMPRIMÉ — deux erreurs qui rendent zéro

**PREMIÈRE ERREUR, ET ELLE FABRIQUE DE FAUX NÉGATIFS EN UNE SECONDE : `adj` PORTE SUR UNE
LOCUTION, PAS SUR DEUX FAITS.** Chercher un nom ET un lieu, c'est **deux termes exacts joints
par `and`** — jamais une seule phrase. Le 9 septembre 2026, sur Gallica :

| requête | ce que ça demande vraiment | résultat |
|---|---|---|
| `cherche("Chasles Lublé")` | la phrase « Chasles Lublé », mots collés | **0** |
| `cherche(["Chasles", "Lublé"])` | Chasles quelque part **et** Lublé quelque part | **154** |

Un fait divers écrit « le sieur Chasles, cultivateur à Lublé » : les deux mots ne sont jamais
côte à côte. **Le zéro ne mesurait que la requête.** Et le piège est silencieux — dans
`gallica.cherche()`, une chaîne devient une locution, une **liste** devient des termes séparés.
Passer une liste dès qu'on cherche plus d'un fait.

**SECONDE ERREUR, ET ELLE FERME UNE PISTE ENTIÈRE : « un homme ordinaire n'entre pas dans un
livre » EST FAUX.** J'ai écrit ça le 9 septembre pour expliquer que les CHASLE, cultivateurs,
n'auraient rien dans la presse. Le généalogiste a rappelé le contre-exemple, qui était **déjà au corpus** :
**Joseph Marie LE PIPE, mordu par un chien enragé, est dans *Le Laboureur du Morbihan* du 21 août
1892** — trouvé par un correspondant, en balayant.

**LE FAIT DIVERS EST PRÉCISÉMENT LE REGISTRE OÙ LE PAYSAN ENTRE DANS L'IMPRIMÉ** : une morsure,
un accident de battage, un incendie, un vol, un procès, un prix de comice agricole, une liste de
conscrits. Ce qui n'y entre jamais, c'est la filiation — mais on ne cherche pas la même chose.

**CE QUI RESTE VRAI, ET C'EST LA SEULE VRAIE BORNE : IL N'Y A PAS DE PRESSE AVANT LA PRESSE.**
La presse locale de province commence dans les années 1830-1840. Tout ce qui est antérieur —
et tous les murs d'Ancien Régime le sont — est hors d'atteinte. Pour ces siècles-là, l'imprimé
utile n'est pas le journal mais l'**inventaire d'archives** et le **dictionnaire topographique**,
qui disent où sont les minutes notariales : un contrat de mariage nomme les grands-parents.

**AVANT DE BALAYER CINQ CENTS NUMÉROS POUR UN NOM, BALAYER DIX NUMÉROS POUR LE VILLAGE.**
C'est le test qui manquait, et il coûte dix minutes contre plusieurs heures. **Un journal qui ne
nomme jamais la commune ne nommera pas ses cultivateurs.** Le 9 septembre 2026, quatre titres ont
été mesurés ainsi sur le canton de Château-la-Vallière :

| Titre | échantillon | Lublé | Couesmes | Villiers-au-Bouin | Château-la-Vallière | Ambillou |
|---|---|---|---|---|---|---|
| Le Tourangeau | 12 nos de 1911 | 0 | — | 0 | — | **1** |
| Le Républicain de Chinon | 10 nos de 1911 | 0 | 0 | 0 | 0 | — |
| Journal de Chinon | 10 nos de 1911 | 0 | 0 | 0 | 0 | — |
| L'Écho de Chinon | 10 nos de 1930 | 0 | 0 | 0 | **1** | — |

**Le balayage complet du Tourangeau sur 1906-1916 — 479 numéros, onze années — a rendu ZÉRO
« Chasles ».** Le test de couverture explique pourquoi : ces villages sont au bord de tout ce qui
est numérisé. Il aurait fait gagner l'heure du balayage.

**ET IL FAUT D'ABORD VÉRIFIER QUE L'OUTIL SAIT DIRE AUTRE CHOSE QUE « RIEN ».** Sur le même
numéro témoin : « cultivateur » rend 1, « Tours » rend 6. Sans ce contrôle, un zéro peut n'être
qu'une recherche plein texte indisponible sur ce titre — et on note un faux négatif.

*Ce que le test ne prouve pas : dix numéros ne sont pas une année. Un zéro sur l'échantillon dit
que la commune est marginale dans ce titre, pas qu'elle en est absente.*

**ET L'OCR MANGE LES ACCENTS** — le texte rendu écrit « R?DACTION », « salari? de l?Etat ». Sur
un fonds de cette qualité, essayer la graphie **sans accent** aussi.

**ET PRÉFÉRER UN HEBDOMADAIRE À UN QUOTIDIEN.** Le coût d'un balayage est le nombre de numéros :
cinquante-deux par an contre trois cent soixante-cinq. Un hebdomadaire agricole couvre le même
canton pour un septième du travail.

## ⛔⛔ QUI A DROIT À QUOI — deux textes, deux portes, et on se trompe de porte

**C'est la règle la plus utile de cette section, et le dossier l'a apprise dans un mur le
18 septembre 2026.** On croit qu'« après soixante-quinze ans, tout le monde peut avoir une
copie intégrale ». **C'est faux à moitié**, et la moitié fausse fait perdre des jours.

| texte | ce qu'il régit | ce qu'il dit |
|---|---|---|
| **Décret n° 2017-890 du 6 mai 2017, art. 30** | la **copie intégrale délivrée par l'officier d'état civil** | réservée à l'intéressé, ses **ascendants**, ses **descendants**, son conjoint — **AUCUNE exception d'ancienneté** |
| **Code du patrimoine, art. L213-2, I, 4°, e)** | la **communication de l'archive** | libre pour tous, **soixante-quinze ans après la CLÔTURE DU REGISTRE** — et non après la date de l'acte |

**Ce qui s'ouvre à soixante-quinze ans, c'est l'ARCHIVE — pas le guichet.**

- **Un tiers n'obtient JAMAIS de copie intégrale en mairie ni sur `service-public.fr`**, même
  sur un acte de 1904. Le téléservice qui répond *« votre lien vous permet de demander
  uniquement un extrait sans filiation »* applique correctement l'article 30. Insister ne sert
  à rien. **Et se faire passer pour un proche, même avec son accord, est une fausse
  déclaration à un officier public : on ne le propose pas, on ne le fait pas.**
- **La porte ouverte est le SERVICE D'ARCHIVES** — départementales ou municipales —, pour la
  consultation du registre et sa reproduction, en citant **L213-2, I, 4°, e)**.
- **Beaucoup de mairies renvoient au téléservice national**, ce qui referme le cercle. Celle de
  Lisieux le fait. Ce n'est pas un mauvais vouloir.

> **⭐ LE RACCOURCI QUI FAIT GAGNER DES SEMAINES : QUAND UN DESCENDANT DIRECT EXISTE, C'EST LUI
> QUI DEMANDE.** Une petite-fille obtient en cinq minutes, gratuitement, ce qu'un tiers
> n'obtiendra jamais au guichet — et pour un acte de n'importe quel âge. Avant de monter une
> demande d'archives, regarder qui, dans la famille, a le droit de la faire.

## ⛔ DEMANDER UN ACTE NE COÛTE RIEN — les sites qui le facturent ne sont pas l'administration

**Piège rencontré le 7 septembre 2026, et il a failli coûter 35 €.** Cherchant l'acte de décès de
Royan, le généalogiste est tombé sur `annuaire-mairie.fr`, qui présente un formulaire d'acte d'état civil
d'apparence officielle — logo, nom de la commune, coordonnées de la mairie — et réclame **35 €**
au moment de valider, bénéficiaire *DEMARCHES.FR*. Le site l'écrit en petit en haut de page :
« **Site distinct de l'administration** ».

**La délivrance d'un acte d'état civil est GRATUITE.** Toujours. Sans justificatif pour un acte
de plus de soixante-quinze ans. Ces intermédiaires sont nombreux, bien référencés, et sortent
**avant** la mairie sur un moteur de recherche.

**⭐ ET LE PLUS COURT EST LE FORMULAIRE NATIONAL : LA PLUPART DES COMMUNES Y SONT RACCORDÉES.**
Trois adresses, une par type d'acte, vérifiées par le généalogiste le 19 septembre 2026 :

| acte fait **en France** | formulaire |
|---|---|
| **naissance** | <https://demarches.service-public.gouv.fr/mademarche/EtatCivil/demarche?execution=e5s1> |
| **mariage** | <https://demarches.service-public.gouv.fr/mademarche/EtatCivil/demarche?execution=e6s1> |
| **décès** | <https://demarches.service-public.gouv.fr/mademarche/EtatCivil/demarche?execution=e7s1> |

*Le `eNs1` est un jeton de parcours : si un lien retombe sur l'accueil, entrer par
`…/mademarche/EtatCivil/demarche` et choisir le type d'acte — l'ordre est le même, naissance,
mariage, décès.*

⚠️ **Ce formulaire-là est pour les actes dressés EN FRANCE.** Pour un Français **né à
l'étranger** — naturalisé, ou né de parents français hors de France —, l'acte est au **service
central d'état civil de Nantes** et le formulaire est un autre :
`…/mademarche/demarcheGenerique/?codeDemarche=delivrance_demat`. Voir la fiche
« Naturalisations ».

**Les autres voies gratuites, si la commune n'est pas raccordée :** le **site officiel de la
commune** — vérifier le domaine, `royan.fr` redirige vers `ville-royan.fr` — ; le **courrier ou
le téléphone** à la mairie.

**Les signes qui doivent arrêter la main** : un paiement demandé pour un acte d'état civil ; un
bénéficiaire qui n'est pas le Trésor public ; un domaine en `.fr` commercial — `annuaire-mairie`,
`demarches`, `service-etat-civil`, `acte-*` — au lieu du domaine de la ville ou d'un `.gouv.fr`.
**Le seul cas où une archive facture est la REPRODUCTION d'un document dans un service
d'archives** — un devis du SHD, par exemple : là c'est légitime, et c'est annoncé comme un devis.

## Chercher dans un IMPRIMÉ : l'OCR ment, et il faut savoir de combien

Un annuaire, un journal officiel, une liste d'ancienneté se cherchent en plein texte — et c'est
mille fois plus rapide qu'un registre manuscrit. Mais tout ce qui suit vient d'un dépouillement
de 4 083 numéros du *Journal officiel* et de neuf annuaires militaires, le 7 septembre 2026, et
chaque règle y a été payée.

**UN NÉGATIF DE RECHERCHE PLEIN TEXTE NE VAUT QUE CE QUE VAUT L'OCR.** Celui du *Journal
officiel* rend « **Dure-paire** », « **paire d'artillerie** » pour *parc d'artillerie*, « la
div?sion- paire ». Un nom peut donc être présent et manqué. Une plage ainsi balayée est
**COUVERTE**, elle n'est pas **CLOSE**, et le compte rendu doit employer ces mots-là.

**UNE TABLE ANNUELLE N'INDEXE PAS LES LISTES NOMINATIVES.** Les tables du *Journal officiel*
1919-1923 n'ont rien rendu sur un homme qui y figure quatre fois dans le corps du journal :
elles indexent les *matières*, pas les milliers de noms des listes de promotions. **Un négatif
de table ne prouve presque rien** — il fait gagner du temps quand il rend quelque chose, jamais
quand il ne rend rien.

**ET LE MOYEN DE SAVOIR SI UNE ABSENCE EST RÉELLE : LE CONTRÔLE DE COHORTE.** C'est la trouvaille
de méthode de cette séance, et elle vaut pour toute liste sérielle — listes d'ancienneté, rôles,
annuaires, recensements. Quand quelqu'un disparaît d'une édition à l'autre, on ne peut pas savoir
si la ligne a été retirée ou si l'OCR l'a perdue. **Alors on prend ses VOISINS comme témoins.**

> Édition de 1929 : `2838 BOQUILLON · 2839 PAIRÉ · 2840 VALLET`, trois entrées consécutives.
> Édition de 1930 : `2473 BOQUILLON · 2474 VALLET`, **devenus consécutifs**. VALLET est encore là
> en 1931.

Les voisins sont restés et se sont refermés sur la place vide : **la ligne a bien été retirée.**
Si les voisins avaient disparu aussi, c'était le volume ou l'OCR, et l'absence ne prouvait rien.
Le contrôle coûte deux requêtes et transforme une impression en fait.

**UN SYMBOLE NE SE LIT JAMAIS DANS L'OCR — IL SE LIT DANS LA LÉGENDE DU VOLUME.** Le même glyphe
a été rendu « ✳ », « $£ », « ^ », « # » et rien du tout selon la page. La page des signes, en
tête de l'ouvrage, le nomme : sous LÉGION D'HONNEUR, « GC ✳ Grand-Croix · GO ✳ Grand-Officier ·
C ✳ Commandeur · O ✳ Officier · ✳ Chevalier », puis une **médaille ronde** pour la médaille
militaire et une **croix** pour la croix de guerre. Sans elle, l'étoile seule pouvait être trois
décorations différentes. **Chercher la légende AVANT d'interpréter un signe**, et la lire sur
l'image, pas dans le texte océrisé qui l'efface.

**ET UNE ABRÉVIATION SE LIT AU MÊME ENDROIT.** La même page disait : « **P. C.** signifie
**portion centrale** et **P. P.** **portion principale** ». Le corpus avait lu « poste de
commandement » pendant un jour, ce qui changeait le sens d'un régiment entier.

**UN RECTIFICATIF EST UNE SOURCE, ET SOUVENT LA MEILLEURE.** Une erreur administrative engendre
un second document, plus explicite que le premier parce qu'il doit s'expliquer. C'est un
rectificatif de 1921 — annulant une inscription faite en double — qui a daté une décoration :
« déjà décoré par arrêté du 2 octobre 1920 (*Journal officiel* du 4 octobre 1920) ». **Quand on
cherche une date de nomination, chercher aussi les annulations, les rectificatifs et les
errata.**

**UN FORMULAIRE A UNE QUEUE, ET ELLE NE PARLE PAS DU MÊME JOUR QUE LE CORPS.** Une citation
militaire se termine sur un décompte — « **Une blessure. Une citation antérieure.** », « Deux
blessures. Quatre citations antérieures. » C'est le **palmarès cumulé** de l'officier, pas la
fin du récit de la journée. Le corpus a lu cette queue comme un fait du 9 août 1918, l'a écrite
dans un résumé affiché, et s'est trompé pendant un jour.

**Ce qui l'a détrompé est sur la même page** : la citation imprimée juste au-dessus écrit dans
son **motif** « le 9 août 1918, … ; **a été blessé au cours de l'action** », *puis* ajoute
« Deux blessures. Quatre citations antérieures. » Les deux formules coexistent sur le même
homme : quand le *Journal officiel* veut dire « blessé ce jour-là », il l'écrit dans le motif.

**La règle générale, et elle vaut pour tout document sériel** : avant d'attribuer une phrase à
la date de l'acte, **lire les entrées voisines pour apprendre la grammaire du formulaire**. Un
libellé ne se comprend pas seul ; il se comprend contre ses voisins. C'est la même mécanique
que le contrôle de cohorte — et que la ligne du *JO* de 1917 où l'absence de la mention
« capitaine à titre temporaire » ne se voit qu'à côté d'un voisin qui la porte. **Deux fois le
même jour, le fait était dans ce que le texte n'écrivait PAS.**

## Déléguer le balayage

**LES AGENTS TROUVENT, LE VÉRIFICATEUR RELIT.** Six agents ont balayé 130 vues en vingt
minutes et rendu quatre actes que des recherches ciblées n'avaient pas trouvés en trois
jours. **Aucune de leurs lectures n'entre au corpus sans que la page soit rouverte au
grossissement natif** — l'un d'eux a proposé un patronyme qui aurait fabriqué une fausse
fusion.

Le brief qui marche : la plage exacte, les graphies cibles, **les faux amis connus**,
l'ordre de signaler un doute comme un doute, et le format de rendu. Ne jamais leur demander
de transcrire ni d'écrire dans le corpus.

## LE REGISTRE MATRICULE — la pièce la plus rentable du XIXᵉ finissant

**Une fiche matricule donne, sur une seule page, ce qu'il faut trois actes pour obtenir** :
date **et commune de naissance**, **les deux parents avec leur domicile**, la profession à
vingt ans, le **signalement** — cheveux, yeux, front, nez, visage, taille —, le degré
d'instruction, toute la carrière militaire, les **domiciles successifs avec leur date**, et
les mentions tardives (mariage, décorations, dispenses). Tout homme né entre 1867 et 1921 en a
une, et elle est **librement communicable au bout de cent vingt ans**, donc en ligne pour les
classes jusqu'aux années 1920.

**CHERCHER LA RECHERCHE NOMINATIVE AVANT DE FEUILLETER UN RÉPERTOIRE.** Beaucoup de portails
n'offrent qu'une liste de registres, et il faut alors passer par la table alphabétique de la
classe. Mais **certains indexent nominativement**, et c'est un gain d'un autre ordre : le
Morbihan rend, sans ouvrir une seule image, nom, prénoms, classe, matricule, cote, **date et
commune de naissance**, commune de résidence et profession. Interrogé sur « MOUEL », classes
1911-1915, il rend 53 hommes avec leur fiche d'état civil — de quoi écarter deux homonymes
sans tirer une image.

**LA CLASSE SE CALCULE, ET ELLE SE PREND LARGE.** Un homme est de la classe de ses vingt ans :
né en 1892 → classe 1912. **Mais l'âge du corpus vient souvent d'un âge déclaré**, à un ou deux
ans près : chercher sur **cinq classes**, jamais une seule. Et un ajourné, un engagé volontaire
ou un réformé peut figurer dans une classe voisine.

**LE MÉTIER ET LE DOMICILE TRANCHENT ENTRE LES HOMONYMES, PAS LE PRÉNOM.** Trois « Pierre Marie
LE MOUËL » dans les classes 1911-1915 du Morbihan : c'est **le métier de charron** et le village
de **Kerchopine, en Cléguer**, porté aux domiciles successifs, qui ont désigné le bon — les deux
autres étaient cultivateurs, nés ailleurs, de parents différents. Lire les fiches des candidats
coûte une vue chacune : les lire toutes vaut mieux qu'un raisonnement.

**ET CE QU'ELLE NE DONNE PAS : LE NOM DE L'ÉPOUSE.** La ligne « Marié le » est le plus souvent
**vide**. Une fiche matricule ne rattache donc pas un homme à une famille par son mariage : elle
le rattache **vers le haut**, à ses parents. Quand trois candidats portent le même nom et qu'aucune
fiche ne nomme de femme, **on ne choisit pas** — on note les trois et on attend l'acte de mariage.

**CE QU'ON EN FAIT DANS LE CORPUS** (voir la skill `trame-fr` pour l'écriture) :

- **Le signalement va dans le champ `signalement` — un OBJET** `{cheveux, yeux, front, nez,
  visage, taille_cm, source, confidence, note}` — **et il se reprend dans le `summary`**, en
  incise : « — châtain, les yeux gris, le visage ovale, un mètre soixante-trois — ». C'est
  souvent le seul portrait qui existe de cet homme. Un champ inventé (`sig`) ne s'affiche pas,
  et `build.py --champs` le signale désormais.
- **La guerre est un moment**, pas une ligne de notes : unité, dates aux armées, blessures,
  citations. **Une citation se transcrit mot à mot dans la source** — c'est de la prose
  d'époque, et elle dit ce qu'un homme a fait un jour précis.
- **Les domiciles successifs sont des moments datés**, un par déménagement. Ils racontent une
  trajectoire — le bourg, la ville, le chantier — et ils recoupent les actes.
- **Les mentions tardives apprennent des faits de famille** : une dispense « comme père de sept
  enfants vivants » donne un nombre d'enfants qu'aucun acte ne donnait.

## Lire un acte, et ne pas conclure trop vite

**LE LIEU D'UN ACTE N'EST PAS LE LIEU D'UN HOMME.** **Un mariage se célèbre chez la
mariée** ; un enfant naît où son père travaille. **Ce sont les baptêmes des cadets qui
disent l'origine** — c'est là que le curé écrit « originaires de ». Quatre fois un dossier a
pris l'un pour l'autre et déplacé un berceau de deux départements.

**ET UN NOTAIRE DE CHEF-LIEU REÇOIT TOUT SON CANTON.** C'est la même règle appliquée à
l'acte notarié, et elle s'est vérifiée le 8 septembre 2026. Le corpus faisait habiter Jean
PAVAILLON **à Couhé** parce qu'il y avait fait passer, en août 1858, le consentement au
mariage de sa fille devant Me LACROIX. Or les recensements de Couhé — 1856, 1881, 1886,
1891, lus en entier — **ne portent ni lui ni sa fille**, et pas un seul blanchisseur. Couhé
est un chef-lieu de canton : l'étude y est, les clients viennent de vingt communes. **Le
domicile d'un homme se lit dans le corps de l'acte, jamais dans l'adresse de l'officier
public qui l'a reçu.**

**UN MARIAGE VAUT TROIS BAPTÊMES** : il nomme les parents des deux époux, souvent leurs
âges, leurs professions, dit lesquels sont vivants et présents, et **cite l'acte de
naissance de chacun**. C'est par là qu'il faut entrer quand on cherche une génération.

**UN ÂGE DÉCLARÉ PAR UN TIERS NE BORNE RIEN** — quarante ans pour quarante-sept,
soixante-neuf pour soixante-six. Un acte de mariage, lui, *recopie* les dates prises sur les
registres de naissance : il l'emporte toujours sur un âge rapporté.

**ET DANS UNE SOURCE MILITAIRE, UN RANG D'ANCIENNETÉ N'EST PAS UNE DATE DE NOMINATION.** Les
deux se ressemblent, les deux sont des dates officielles, et elles ne disent pas la même chose.
Une décision du 10 mars 1922, appliquant la loi du 30 mars 1921, « **reporte** » le rang
d'ancienneté d'un officier au 12 février 1915 : ça ne prouve pas qu'il fut nommé ce jour-là,
seulement qu'à partir de 1922 il **comptait comme tel** depuis cette date. Corollaire : **deux
sources peuvent donner deux anciennetés différentes sans qu'aucune se trompe** — un annuaire de
1920 disait « 1/10 17 », quatre listes postérieures disent « 12 février 1917 », et c'est le
rappel d'ancienneté d'après-guerre qui les sépare. Chacune était vraie à sa date.

**UNE BORNE N'EST PAS UNE DATE.** « Avant 1750 » ne veut pas dire 1750 : la personne peut
être née vingt-cinq ans plus tôt. Comparer deux bornes comme deux dates fabrique des mères
de trois ans — c'est ce que font les détecteurs d'anomalies des sites de généalogie, et
c'est d'où venaient neuf signalements sur dix sur un arbre récent. **Ne conclure que
lorsqu'une borne va dans le sens de la contradiction** : « mort après 1828 » n'interdit pas
un enfant en 1840, « mort avant 1913 » interdit un enfant en 1950.

**UN NOM PROPRE QU'ON N'A PAS ZOOMÉ S'ÉCRIT `[non lu]`**, et les lectures douteuses vont
dans un champ dédié de la source. Combler un blanc avec ce qui est plausible, c'est la
mécanique qui fabrique un ancêtre — une « Clotilde » née d'une transcription automatique, un
curé « Massaignon » emprunté au registre voisin.

**NE JAMAIS CRÉER UNE PERSONNE SUR UNE DÉDUCTION.** Nommée par un acte primaire → on la
crée, sans demander : ces gens ont existé, l'acte le dit. Déduite d'un souvenir, d'un
homonyme, d'un âge plausible ou d'une transcription → **on ne crée pas, on pose la
question.** La règle vise l'inférence, pas le document.

**LE VERBATIM NE SE CORRIGE JAMAIS**, parce que le bruit de transcription porte du signal :
c'est une phrase incohérente qui a permis de repérer qu'un « cancer » était un ulcère. Mais
un verbatim est une **parole transcrite**, pas un message tapé par un vivant — là, une
coquille est une coquille, et elle se signale.

## En repartant

- **Écrire la fiche de la SOURCE — et pas seulement d'un portail départemental.** Moteur, URL,
  identifiants, périmètre exact, pièges payés. Voir
  [`references/portails.md`](references/portails.md).
  **LA RÈGLE A ÉTÉ ÉCRITE POUR LES PORTAILS D'ÉTAT CIVIL, ET ELLE VAUT POUR TOUT CE QU'ON
  INTERROGE.** Le fichier porte déjà l'Albo d'Oro des morts italiens de 14-18, le fichier des
  décès de l'INSEE, les archives Arolsen, Geneanet et la Wayback Machine : aucun n'est un
  portail d'archives départementales, et chacun a coûté une demi-journée à apprivoiser.
  *Le nom du fichier a vieilli avant son contenu.*
- **Consigner le négatif** autant que la trouvaille.
- **Ranger les images sur `X:`**, jamais dans un dépôt de code ni dans un répertoire
  temporaire — un script ou une image écrits dans le temporaire meurent avec la session.
- **Enrichir l'outillage plutôt que le dupliquer.** Si l'outil de lecture ne sait pas faire
  quelque chose, on l'étend. Trois copies d'une même fonction ont vécu côte à côte dans un
  projet, dont une avec son test inversé pendant des semaines : **une recette dupliquée est
  une recette qui pourrit.**
