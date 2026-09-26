---
name: trame-fr
description: Écrire dans le corpus — verser un témoignage ou un acte en personnes, unions et moments, rédiger un narratif, un résumé, une note, choisir ce qui se masque, et contrôler la cohérence d'une fiche avant de publier. À charger dès qu'il s'agit d'ÉCRIRE dans le corpus : ajouter une personne, un moment, une union, un lieu, une source ; corriger une date ; réécrire un résumé ; relire une trame. `archives-fr` sert à TROUVER, celle-ci à VERSER. Les deux se chargent souvent ensemble : on cherche un acte, puis on l'écrit.
---

# Écrire dans le corpus

`archives-fr` couvre la recherche. Celle-ci couvre **ce qu'on en fait** : le versement, la
rédaction, et le contrôle avant publication.

Elle existe parce que les règles d'écriture vivaient dans `CLAUDE.md`, lu au début de session
puis oublié — et que le corpus a déjà écrit noir sur blanc pourquoi ça ne marche pas :

> « Elle était écrite ici depuis le début, relue à chaque session, oubliée à chaque session :
> rien ne la contrôlait, donc chacun la jugeait au cas par cas et l'oubli passait. »

**Tout ce qui suit vient d'une erreur commise, et la plupart ont été vues par le généalogiste sur la page
publiée, pas par la session qui les avait faites.**

---

## 1. Verser, c'est aussi RETIRER

**C'est l'erreur la plus coûteuse, et la plus récente : 31 août 2026.** Un témoignage neuf est
arrivé sur Jean DURAND. Il a été versé en créant des moments précis — et **sans reprendre les
anciens**, approximatifs, qui racontaient déjà la même chose en plus flou. Les deux jeux ont
cohabité sur la même trame :

- la rencontre avec sa future femme **racontée deux fois**, une version vague dans le moment de
  Rochefort et la version complète sur son propre moment ;
- **Rochefort de 1975 à 1990** pendant que Mururoa est en 1978 et l'état-major de Tours de 1981
  à 1985 ;
- **un « Tours 1965-1975 » vivant à côté d'un « Tours 1963-1968 »** — deux fois le même poste ;
- les huîtres datées de 1990 quand la retraite militaire est au 1er avril 1985 ;
- un prénom resté sans son nom alors que le témoin avait donné les deux.

**Avant d'ajouter un moment à quelqu'un, lire toute sa trame.** Pas sa fiche : sa trame, dans
l'ordre. La question n'est pas « ce que j'écris est-il juste ? » mais **« que dit déjà cette
trame, et qu'est-ce que ceci remplace ? »**.

Un moment entièrement repris ailleurs **se supprime**. Ce n'est pas perdre un fait : c'est
cesser de le dire deux fois. Vérifier avant que chacun de ses détails a bien trouvé un autre
toit — le bureau des affectations de Jean a été ramené sur l'état-major avant que l'ancien
moment de Tours ne disparaisse.

**ET LE `summary` SE DÉGONFLE QUAND LA TRAME SE REMPLIT.** C'est la même règle, appliquée au
champ qu'on oublie de relire. Le 2 septembre 2026, la guerre de l'oncle Jo est passée d'une
phrase à neuf moments — et la phrase est restée, enrichie de Cherbourg, des canons de marine, de
la Champagne et de l'Oise. Puis un fait neuf, les vignes, y a été ajouté **en plus** de son
propre moment. Le généalogiste : *« c'est un résumé, c'est pas le lieu pour tout ajouter »*. **Un résumé
présente une vie ; il ne récite pas la trame qui suit, et chaque moment créé lui retire du
travail plutôt que de lui en donner.** Le sien est passé de 1063 à 829 caractères en ne perdant
aucun fait — tous étaient devenus des moments.

**ET LE DÉFAUT INVERSE EST PIRE : UN RÉSUMÉ QUI PORTE DES FAITS QUE LA TRAME N'A PAS.** Le
14 septembre 2026, la fiche de Juan Pablo BARBERO annonçait l'association de 2012 au 620 Quaglia,
la société de la rue Onelli de 2015, le café DuCoin et le Ski Club — et **sa trame ne portait que
deux naissances**. Le généalogiste : *« tout est dans le putain de résumé »*. Quatre faits datés, quatre
moments à écrire, chacun avec sa source et ses réserves ; le résumé est retombé à quatre lignes.
**Un fait qui a une date est un MOMENT ; le résumé dit qui était la personne, pas ce qu'elle a
fait tel jour.**

**Et le contrôle existe depuis ce jour-là** : `relire.py` sans argument rend « DES FAITS DATÉS
DORMENT DANS UN RÉSUMÉ » — une fiche dont le résumé cite au moins deux années qu'aucun moment de
sa trame ne porte, alors qu'elle a six moments ou moins. Vingt-huit fiches au premier passage.
*Sans les deux seuils il en rendait 114 : un résumé cite légitimement l'année d'un proche.*

---

## 2. Un narratif raconte une VIE, pas un dépouillement

**Ce que les REGISTRES gardent d'une personne se dit** — « c'est la seule ligne qui porte son
nom », « l'acte ne la nomme que pour la dire défunte ». Ça appartient à cette vie-là.

**Ce que LE CORPUS savait, croyait ou vient de trouver ne se dit pas.** « le corpus tenait pour
le premier », « ce qui recule leur mariage de trois ans », « deux siècles plus tard », « c'est
la plus ancienne image que garde le corpus ». Ça raconte le travail, pas la personne, et **ça
périme au premier acte suivant**. Sa place est dans `notes` et dans `journal.md`.

**Ne pas non plus raconter la collecte** : « Jean décrivait son père comme un homme très
costaud » se réécrit « Clément était un homme très costaud ». Le témoin se dit par la `source`.

**ET ON NOMME LES GENS COMME ON LES APPELAIT, PAS COMME L'ACTE LES ÉCRIT.** Un narratif doit
nommer son sujet — ce n'est pas une raison pour lui remettre son état civil complet à chaque
paragraphe. Le 2 septembre 2026, les onze moments de l'oncle Jo ouvraient tous sur « Albert
Georges Samuel NEAU », neuf fois de suite sur la même trame. Le généalogiste : *« c'est lourd dingue, et
on l'appelait Georges ou Jo »*. **L'état civil complet se dit UNE FOIS, dans le `summary`, où la
personne se présente** ; les moments prennent le nom d'usage. Le défaut vient du versement en
série : neuf moments écrits d'affilée au même gabarit, et le gabarit portait le nom long.

---

## 3. Le texte affiché est du TEXTE BRUT, en français accentué

- **Pas de markdown.** La page n'affiche ni `**gras**` ni `` `code` `` : elle imprime les
  astérisques. **L'emphase se met en CAPITALES.** Le markdown est légitime dans `notes`, les
  sources et les `.md` — rien ne les affiche.
- **Accents partout.** Un script qui écrit dans `data/` s'écrit en UTF-8 et se relit sur la
  page, pas dans un terminal Windows qui ment sur ce qu'il affiche. « Meigne », « etait »,
  « generation » ont détonné au milieu d'un corpus accentué.
- **Un lieu ne s'affiche jamais nu.** `lieu()` dans `build_poc.py` ajoute la subdivision ou le
  pays : ne pas le réécrire à la main dans un narratif. Mais tout lieu créé doit porter `admin2`
  **et** `admin2_name` — département en France, province en Italie, wilaya en Algérie — plus
  `country` hors de France, sinon la règle tombe. *Ces champs s'appelaient `dept` / `dept_name`
  jusqu'au 25 septembre 2026 ; `dept` n'est plus reconnu.*

**ET UN NOM ÉCRIT N'EST UN LIEN QUE SI LA PAGE LE RECONNAÎT.** Le 11 septembre 2026, le mariage
de 1938 nommait « René DANNEPOND » et « Georges NEAU », tous deux participants, et aucun des deux
n'était cliquable. Le généalogiste : *« tu n'as pas fait les liens vers René et l'oncle Jo »*. La page
(`link()` dans `template.html`) pose un lien sur un participant **seulement si son `given` exact
figure en mot entier dans le texte** — et René portait « René Paul ». Trois règles en sortent :

1. **`given` = LE PRÉNOM D'USAGE, celui qu'on écrit dans les narratifs.** L'état civil complet va
   dans `given_civil`, que la fiche affiche déjà (« à l'état civil : … »). C'est la convention de
   `SCHEMA.md` ; treize fiches l'enfreignaient encore le même jour (Angéline Marie, Clodomir
   Eutrope, Silvio Vittorio Anforio…) et aucun de leurs moments ne les liait.
2. **Le narratif écrit le prénom EXACTEMENT comme `given`** — accents compris : « Andre » dans la
   fiche ne lie pas « André » dans le texte. Si le document écrit autrement (Mathieu / Matthieu,
   Ysabeau / Isabeau), c'est le `given` qu'on écrit dans le narratif, et la graphie du document
   dans la source.
3. **Deux participants du même prénom dans un moment : la page n'en lie qu'un**, au premier
   endroit où le prénom apparaît — donc parfois sur le mauvais. La donnée n'y peut rien ; ne pas
   « corriger » en changeant un `given`, le signaler.

**Et le contrôle existe** : `relire.py` sans argument rend une section « LIENS QUE LA PAGE NE
FERA PAS » — chaque « Prénom NOM » d'un texte affiché dont le NOM est celui d'un participant, et
que la page ne liera pas. **Un moment qu'on vient d'écrire n'y figure pas, ou on sait pourquoi.**

---

## 4. Un narratif n'a pas de point de vue — et parfois le participant n'a rien à faire là

Un narratif nomme toujours son sujet, ne commence jamais par un pronom ni par un attribut
suspendu, et reste vrai lu depuis la fiche de **n'importe quel participant**. Sinon : une
variante dans `narrative_for`, ou `vue_ok` quand on a **vérifié** que le texte générique tient.

**MAIS LA BONNE RÉPONSE EST SOUVENT DE RETIRER LE PARTICIPANT.** `build.py --vues` demande « que
lit cette personne ? » et pousse à répondre par un texte ; il ne demande jamais **« a-t-elle
quelque chose à faire là ? »**. Deux cas, symétriques :

- **Après sa mort.** « Untel était mort depuis trente-trois ans quand… » ne dit rien de lui, ça
  date l'autre. Deux exceptions étroites : quand la mention est **la seule trace connue** de la
  personne, et quand elle **apprend un fait**.
- **Avant sa naissance.** Jean DURAND figurait sur la vie de maréchal-ferrant de son père, datée
  1930-1970 : il en est le **témoin**, et un témoin se dit par la `source`.

---

## 5. Ce qui se masque, et ce qui ne se masque pas

- **`health` ne se met pas sur un mort.** Le cœur de Clément LOYAU, le cancer d'Antonio, les
  ulcères d'Alfiero s'affichent. Il reste légitime pour une personne **vivante**.
- **`family_private` couvre ce qu'un tiers rapporte au détriment de quelqu'un**, et c'est **qui
  ça peut encore atteindre** qui décide. Ni une déportation, ni une maladie, ni un mariage
  discret.
- **Ce qui est inscrit à l'état civil n'est jamais masqué** — un divorce figure au livret de
  famille.
- **Le masquage se découpe à la phrase, pas à l'événement** : quand une seule incise pose
  problème, on la sort dans un moment séparé.
- **Le doute se tranche vers l'affichage pour un fait SUBI**, vers le masque pour un **jugement
  porté** sur quelqu'un.

**ET MASQUER N'EST PAS UNE RÉPONSE À TOUT : CERTAINES PHRASES NE DOIVENT PAS ÊTRE ÉCRITES.**
`family_private` protège d'une lecture distraite, pas d'une lecture attentive — et ce corpus est
fait pour être montré à la famille. Le 3 septembre 2026, un moment masqué portait « Avec le recul,
Claudine reconnaissait que sans cela elle n'aurait jamais épousé Rémy » : sa sœur la rapportant,
sur une confidence sans date ni circonstances, disant à un homme VIVANT que sa femme ne l'aurait
pas épousé, et à leur fille VIVANTE qu'elle était la raison du mariage. **Le corpus ne fixe pas par
écrit le regret intime d'une personne vivante sur la foi d'une tierce personne.** Le fait d'état
civil reste ; le jugement s'en va. Le test : *le lirait-on à voix haute devant les intéressés ?*

**ET LE FAIT D'ÉTAT CIVIL SE PORTE SANS FAIRE LA SOUSTRACTION.** Une date de mariage et une date
de naissance peuvent vivre chacune à sa place ; écrire « elle était enceinte — l'enfant naît quatre
mois plus tard » énonce une cause là où deux dates suffisaient. Le lecteur qui veut compter
comptera.

**ET APRÈS TOUT MASQUAGE, RELIRE LE `summary` DE CHAQUE PARTICIPANT.** Un résumé qui redit en
clair ce qu'un moment cache annule le masquage, sur la même page, sans que personne le voie.
C'est arrivé sur Hippolyte CARRÉ.

---

## 6. Ne jamais créer une personne sur une déduction

- **Nommée par un acte primaire → créer, sans demander.**
- **Déduite d'un souvenir, d'un homonyme, d'un âge plausible ou d'une transcription → ne pas
  créer, poser la question.** C'est de là que vient la « Clotilde », qui a vécu plusieurs jours
  avec fiche, relations et événements.
- **Une compilation n'est pas un acte.** Un arbre Geneanet se verse avec sa source, ses
  réserves, et la liste de ce qui reste à relire sur registre.
- **Un lien de parenté que l'acte n'écrit pas ne s'écrit pas.** Pierre LOYAU, trente ans,
  premier déclarant du décès de Jacques, même nom, même commune : sa fiche a été créée sans
  rattachement jusqu'à ce qu'une source l'établisse.

**MAIS CETTE RÈGLE NE PARLE QUE DE CRÉER, ET J'AI CRU QU'ELLE PARLAIT AUSSI DE RATTACHER.** Le
1er septembre 2026, une photographie légendée « Jacque, Jean, Michel en pyramide » est entrée au
corpus avec ce narratif : « un homme que la légende appelle **Jacques** ». Or le corpus contenait
**Jacques KINDE**, mari de Jeannine LE PIPE donc beau-frère de Denise, seul Jacques du cercle, et
présent dans le même lot de photographies. **Il n'y avait rien à créer** — seulement à rattacher
quelqu'un qui existait déjà, ou à demander. L'hypothèse a été écrite dans une `note`, et le prénom
est resté nu sur la page. C'est le généalogiste qui l'a vu, et sa réponse tient en une ligne : *« on doit
avoir les skills pour écrire et vérifier qui ne laissent pas ce genre de trou »*.

**Trois choses en sortent, et elles sont distinctes :**

1. **Créer et rattacher ne sont pas le même geste.** Créer une personne sur une déduction fabrique
   un fantôme, et c'est interdit. Rattacher une personne **qui existe déjà** ne fabrique rien : au
   pire on se trompe de participant, et ça se défait. Le faisceau se pèse — un prénom, un lien de
   parenté qui colle, un cercle où il est le seul, une présence dans le même lot — et **on demande**.

2. **Une question posée dans une `note` n'est pas posée.** Personne ne lit les notes : le généalogiste lit la
   page. Une question ouverte se dit **dans la réponse, nommément**, en même temps qu'elle se range
   dans `open-questions.md`. C'est la règle « une correction qui s'arrête aux notes n'en est pas
   une », appliquée aux questions.

   **ET `open-questions.md` N'EST PAS UNE ADRESSE OÙ POSER UNE QUESTION NON PLUS. Le généalogiste, le
   12 septembre 2026 : *« je ne regarde jamais le fichier de questions, et ne trouvant pas il
   fallait me le dire »*.** Ce fichier est une liste de travail pour la session suivante, pas une
   boîte aux lettres : ce qui y est rangé n'est pas *demandé*, c'est *reporté*.
   **Le cas d'école coûte onze jours.** Le 1er septembre, le baptême du généalogiste a été versé avec
   « sa marraine s'appelle Lucile » et une note disant qu'elle « attend son nom de famille ». Le
   refus de créer une personne sur un prénom nu était juste. **Mais il n'y avait rien à créer, et
   surtout il y avait quelqu'un à qui demander** : sa marraine est **Lucie CEOLIN**, la fille de
   Severina MIGOT, entrée au corpus le 7 septembre — cousine germaine de son père. Une phrase
   dans la réponse — *« comment s'appelait ta marraine ? »* — refermait tout le premier jour.

   **Le partage, donc : ce qui dépend d'un ARCHIVE va dans `open-questions.md` ; ce qui dépend
   d'une PERSONNE VIVANTE se demande dans la réponse, tout de suite, et se range ensuite.** Un
   acte attend, un témoin répond.

3. **Et le contrôle existe maintenant.** `relire.py` signale les textes affichés qui portent une
   formule d'ignorance — « que la légende appelle X », « nommé X », « un certain X », « s'appelle
   X » — quand le corpus porte une personne de ce prénom qui n'est pas au moment. Calibré le
   1er septembre : la première version, qui signalait tout prénom nu, rendait **241** signalements
   et noyait le signal ; celle-ci en rend **un**. Un prénom nu n'est pas fautif en soi — « tante
   Yvonne », « l'oncle Jo » sont la bonne façon d'écrire quand la personne est là.

---

## 7. Le corpus dit ce qui est VRAI MAINTENANT

Git et `journal.md` disent quand ça a changé. Une phrase devenue fausse **se réécrit**, elle ne
s'annote pas : « jusqu'au 15 août 2026 » n'apprend rien et fait trébucher.

**Et un drapeau doit dire vrai.** `disputed_by` fait afficher « deux versions » : il ne se met
que s'il y a **vraiment deux lectures défendables**. Une approximation corrigée par l'intéressé
n'est pas une version concurrente — elle disparaît, et son histoire reste dans `journal.md`.

**Corollaire à vérifier après chaque trouvaille** : chercher les absolus qu'elle périme — « le
dernier », « le seul », « tout ce qu'on a », « il n'existe que par ».

**Et une correction qui s'arrête aux `notes` n'est pas une correction.** Le champ corrigé et le
champ affiché ne sont pas les mêmes. Après toute découverte qui déplace une date, un lieu ou une
filiation : **relire le `summary` et les `narrative` de chaque personne touchée**, et rouvrir la
page.

---

## 8. Toute valeur porte sa source et sa confiance

`high` / `medium` / `low`. En cas de conflit, la version retenue prend le champ, l'autre va dans
`<champ>_disputed` **avec la raison de l'arbitrage**. On n'écrase jamais en silence.

**Un âge déclaré par un tiers ne borne rien** — le corpus a vu trois, cinq, huit et neuf ans
d'écart. Un acte de mariage, qui recopie les registres, l'emporte toujours sur un âge rapporté.
**Une date précise au jour l'emporte sur tous les âges** : Jean DURAND a été dit engagé à quatorze
puis dix-sept ans ; le 26 avril 1960 contre une naissance le 17 septembre 1943 fait seize.

---

## 8 bis. UN CHAMP QU'ON INVENTE NE CASSE RIEN — IL DISPARAÎT, ET C'EST PIRE

Le 18 septembre 2026, le signalement de Pierre Marie LE MOUËL — châtain, les yeux gris, un
mètre soixante-trois — a été écrit dans un champ **`sig`**, inventé sur place. Le schéma attend
un objet **`signalement`**, que `build_poc.py` sait rendre. Rien n'a protesté : le JSON était
valide, le build passait, et **la page n'affichait rien**. Le généalogiste l'a vu, comme toujours, en
ouvrant la fiche. Le contrôle écrit le jour même a trouvé **quatre autres `sig`** dans le corpus
PAIRÉ, invisibles depuis des semaines.

- **`python scripts/build.py --champs`** liste maintenant tout champ hors schéma dans
  `persons`, `events`, `unions` et `places`. Il **exclut `sources.json` à dessein** : une fiche
  de source porte des champs libres, qui sont de la prose rangée.
- **Avant d'écrire un champ qu'on n'a jamais écrit, le chercher dans `SCHEMA.md` et dans le
  corpus** : `grep -o '"[a-z_]*":' data/persons.json | sort | uniq -c`. S'il n'existe nulle
  part, c'est presque toujours qu'il porte un autre nom.
- **Et un synonyme est une invention** : `surname_married` là où le corpus dit `married_name`
  est le même défaut, en plus discret.

**Le cas particulier du signalement** : il ne suffit pas de le ranger dans son champ, **il se
reprend dans le `summary`**, en incise — c'est souvent le seul portrait qu'on ait d'un homme.
Voir la skill `archives-fr`, section « Le registre matricule ».

---

## 9. Le protocole d'écriture

**Recharger les fichiers juste avant de les enregistrer** : plusieurs sessions travaillent en
parallèle, et un script qui réécrit un JSON entier écrase tout ce qui est arrivé entre-temps.

**Respecter la forme de chaque fichier, et la MESURER au lieu de la supposer** — elle change
quand une autre session réécrit avec un autre `indent`. Le test qui ne ment pas : recharger,
`json.dumps(indent=N)`, réinjecter le saut de ligne, comparer aux octets.

**`git add -A` est interdit.** Stager ses propres chemins un par un. Et si le fichier contient
aussi le travail d'une autre session, fabriquer le contenu « moi seul » et le poser dans l'index
par `git hash-object -w --path` puis `git update-index --cacheinfo` — sans toucher au répertoire
de travail.

---

## 10. LA CHECKLIST AVANT DE PUBLIER

Rien de ceci n'est facultatif. Les quatre premiers points sont automatiques.

```bash
python scripts/build.py                 # 0 erreur, sinon on ne publie pas
python scripts/build.py --pasnes        # participants nés après l'événement
python scripts/build.py --postes        # deux lieux à la fois sur une même personne
python scripts/build.py --vues          # participants sans point de vue vérifié
python scripts/build.py --orphelins     # ascendants rattachés à aucune union
python scripts/build.py --sansdate      # moments sans borne : ils tombent APRÈS la mort
python scripts/build.py --fourchettes   # un mariage daté sur quinze ans n'est pas daté
python scripts/relire.py <personne>      # redites, jargon et liens manqués sur une trame
```

**`relire.py` a un TROISIÈME détecteur depuis le 1er septembre 2026** : les **formules d'ignorance**
dans un texte affiché — « que la légende appelle X », « nommé X », « un certain X » — quand le
corpus porte quelqu'un de ce prénom qui n'est pas au moment. Il tourne sur tout le corpus, sans
argument. C'est le trou de Jacques KINDE, décrit au § 6.

**Et depuis le 11 septembre 2026, les LIENS QUE LA PAGE NE FERA PAS** : un participant nommé
« Prénom NOM » dans un texte affiché, et que `link()` ne reconnaîtra pas — `given` trop long,
accent différent, homonyme de prénom. Voir § 3. Le premier passage en a rendu 83 ; les 29 qui
tenaient à la donnée ont été corrigés le jour même, les autres sont des homonymes de prénom
que seule la page peut régler.

**ET UN DÉTECTEUR QUI EXISTE NE SUFFIT PAS : IL FAUT TRAITER CE QU'IL REND.** La PLOMBERIE du
§ 2 est contrôlée par `relire.py` **depuis le 9 septembre 2026**, et elle en signalait **34** ce
jour-là. Le 12 septembre elle en signale **53**. *La dette a grandi sous un contrôle qui
fonctionnait* — parce qu'on lance le script, on lit le total, et on passe. Un avertissement
qu'on ne traite jamais ne vaut pas mieux qu'un contrôle absent.

⚠️ **Le détecteur ne tranche pas, et il ne peut pas** : la plupart de ces 53 sont un fait
légitime dit avec le mauvais sujet. « la seule trace d'elle que **le corpus** possède » veut dire
« la seule trace qui **subsiste** d'elle » — le fait appartient à cette vie-là, c'est le mot qui
est du jargon, et *« le corpus »* ne veut rien dire pour les lecteurs de la page. Il faut
donc **lire la phrase** et décider : la réécrire (le fait reste) ou la supprimer (elle racontait
la recherche). Les neuf corrigées le 12 septembre étaient du second genre : *« la règle que le
corpus a payée cher du côté PEYRET »* sur un mariage de 1999, *« une question que le corpus
laissait ouverte depuis trois jours »*, *« ce que le corpus cherchait depuis des semaines »*.

*Et une leçon de méthode au passage : ce jour-là un SECOND détecteur a été écrit pour ça, en
doublon du premier, faute d'avoir lu `relire.py` en entier. **Avant d'ajouter un contrôle,
lister ceux qui existent déjà.***

**ET DEUX GARDE-FOUS DE DATE DANS `build.py`, LE MÊME JOUR, POUR LA MÊME RAISON.** le généalogiste a lu
la trame de Paolina MIGOT et y a vu deux défauts dont aucun script ne parlait :

- **`--sansdate`** — un moment dont la date est `unknown` **tombe en fin de trame, après la
  mort**, parce que la page trie par date. Le magasin de souvenirs d'Argelès-sur-Mer, vingt ans
  de sa vie, s'affichait après son décès. *Ne pas savoir quand est légitime ; laisser le moment
  sans borne ne l'est pas* — et une borne est presque toujours déductible : un commerce tenu
  avec le second mari est postérieur au veuvage, dont on a la date.
- **`--fourchettes`** — un **fait ponctuel** daté par une plage de plus de dix ans. Son second
  mariage s'affichait « entre le 14 juillet 1965 et le 1er janvier 2000 » : trente-cinq ans, et
  **la borne haute était sa propre mort** — la phrase disait donc « elle s'est mariée entre son
  veuvage et son décès ». Le contrôle ne mesure PAS la largeur d'une fourchette : il regarde si
  elle porte un fait ponctuel. Sur les douze plages de plus de quinze ans du corpus, **onze sont
  des durées parfaitement justes** — la chasse dans les marais de 1947 à 2007, le
  maréchal-ferrant de 1930 à 1970. Les signaler toutes noierait le seul cas qui compte.
  Quand la fourchette est **irréductible** — un acte fermé jusqu'en 2031 —, le champ
  `fourchette_assumee` porte la raison et le cas passe en anomalie confirmée.

**`relire.py` est le seul qui lise les TEXTES**, et c'est le contrôle qui manquait le plus.
`build.py` valide la structure — des identifiants qui existent, des dates cohérentes ; il ne
voit pas qu'une trame raconte deux fois la même chose. Deux détecteurs :

- **une date au jour écrite en clair alors qu'elle est déjà un moment** de la même trame —
  « Stéphane naît le 15 février 1967 » dans le texte du mariage, quand la naissance est le
  moment suivant ;
- **deux moments qui partagent des suites de mots rares** — la signature d'un ancien texte
  laissé en place à côté de sa version neuve.

Il compare **le texte que la personne lit vraiment** : sa variante `narrative_for` si elle en a
une, le générique sinon. Et il ignore les suites de mots fréquentes dans tout le corpus, qui
sont des formules d'acte (« il n'a pas été fait de contrat de mariage ») et non des redites.
Sans ces deux réglages il rendait 2941 signalements illisibles ; il en rend 186.

Puis, sur les champs **affichés** seulement — `summary`, `narrative`, `narrative_for` :

| Chercher | Pourquoi |
|---|---|
| `**` et `` ` `` | la page imprime les astérisques |
| `le corpus`, `deux siècles`, `on croyait`, `tenait pour` | l'histoire de la recherche à la place de celle des gens |
| l'ancienne valeur qu'on vient de corriger | une correction qui s'arrête aux `notes` n'en est pas une |
| le contenu de tout moment `sensitivity` | un résumé qui le redit annule le masquage |

**ET CETTE RELECTURE EST LE POINT QUI SE SAUTE, PARCE QU'ON VIENT DE FAIRE PASSER LES SCRIPTS.**
Le 12 septembre 2026, cinq trames de sœurs MIGOT ont été remplies, `build.py` rendait 0 erreur et
`relire.py` 0 signalement sur les textes écrits — et **la trame de Paolina n'a pas été ouverte**,
parce qu'on n'avait rien écrit sur elle ce jour-là. C'est le généalogiste qui l'a lue : *« ce n'est pas du
bon travail »*. Trois défauts en une lecture — un moment sans date rangé après sa mort, un mariage
daté sur trente-cinq ans, une adresse tombée de sa variante. **Les scripts passent sur ce qu'on
vient d'écrire ; la trame se lit en ENTIER, y compris les moments qu'on n'a pas touchés**, parce
que c'est la page entière que le lecteur voit d'un coup.

Et **la relecture qu'aucun script ne remplace** : **ouvrir la trame de chaque personne touchée,
dans l'ordre, et la lire.** Les doublons, les postes qui se chevauchent et les redites ne se
voient pas dans le JSON — ils sautent aux yeux sur la page. Toutes les erreurs listées ici ont
été vues comme ça, et par le généalogiste.
