"""
Valide le jeu de donnees et exporte un GEDCOM 5.5.1.

  python scripts/build.py            -> validation seule
  python scripts/build.py --gedcom   -> validation + export/paire.ged

La validation n'est pas cosmetique : elle est le seul garde-fou contre les erreurs
de saisie silencieuses (reference cassee, enfant ne avant sa mere, mariage apres le
deces). Sur des donnees extraites d'un scan flou, c'est indispensable.
"""
import json, os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("GENEALOGIA_DATA") or os.path.join(ROOT, "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


_persons_liste = load("persons.json")["persons"]
persons = {p["id"]: p for p in _persons_liste}
unions = load("unions.json")["unions"]
places = {p["id"]: p for p in load("places.json")["places"]}
sources = {s["id"]: s for s in load("sources.json")["sources"]}
events = load("events.json")["events"]

errors, warnings, acked = [], [], []

# Anomalies reelles, verifiees, qu'on ne veut plus voir remonter comme suspectes.
# Un validateur qui crie a chaque passage finit par etre ignore : ce qui est confirme
# doit sortir de la liste des alertes sans disparaitre du dossier.
ACKNOWLEDGED = {
    "u-dutour-miallet/dutour-marie-1863":
        "confirme par l'acte de naissance n. 74 de Bort, 27 octobre 1863 : « Magdeleine "
        "Miallet son epouse » y est nommee mere de l'enfant. Nee en 1820, elle a bien "
        "quarante-trois ans. Naissance tardive, pas erreur de saisie.",
}


def year(dv):
    """Annee entiere d'une date_value, ou None."""
    if not dv:
        return None
    iso = dv.get("iso") or dv.get("from")
    m = re.match(r"^(\d{4})", iso or "")
    return int(m.group(1)) if m else None


def vital(pid, key):
    p = persons.get(pid)
    return year((p.get(key) or {}).get("date")) if p else None


# --- integrite referentielle -------------------------------------------------
# CE CONTROLE ETAIT MORT DEPUIS LE PREMIER JOUR, et il gardait la porte qui a cede le
# 27 aout 2026. Il bouclait sur `persons.items()` — un DICTIONNAIRE, construit deux
# lignes plus haut par une comprehension qui avait deja ecrase les doublons : `pid in
# seen` ne pouvait jamais etre vrai. Trois identifiants en double sont ainsi entres sans
# un mot, et ce sont leurs CONSEQUENCES qu'on a vues (six dates impossibles), pas leur
# cause. Un controle d'unicite se fait sur la LISTE, jamais sur le dictionnaire qu'on
# en tire.
seen = set()
for p in _persons_liste:
    if p["id"] in seen:
        errors.append(
            f"id duplique : {p['id']} — deux fiches portent cet identifiant, et la "
            f"seconde MASQUE la premiere partout dans le corpus")
    seen.add(p["id"])
for pid, p in persons.items():
    for key in ("birth", "death"):
        pl = (p.get(key) or {}).get("place")
        if pl and pl not in places:
            errors.append(f"{pid}.{key}.place -> lieu inconnu '{pl}'")
    for s in p.get("sources", []):
        if s not in sources:
            errors.append(f"{pid}.sources -> source inconnue '{s}'")
    # UNE SOURCE NE SE CITE PAS QU'AU NIVEAU DE LA FICHE, et le controle s'arretait la.
    # Le 30 aout 2026, `durand-jean.birth.source` a ete ecrit `src-arbre-jean-durand` quand
    # la source s'appelle `src-arbre-jean-durand-2026` : build.py a rendu 0 erreur, et la
    # page aurait affiche une naissance dont le lien de source ne menait nulle part. Chaque
    # `source` du corpus doit designer une source qui existe, a quelque profondeur qu'il soit.
    for cle in ("birth", "death"):
        s = (p.get(cle) or {}).get("source")
        if s and s not in sources:
            errors.append(f"{pid}.{cle}.source -> source inconnue '{s}'")
    for o in p.get("occupations") or []:
        s = o.get("source")
        if s and s not in sources:
            errors.append(f"{pid}.occupations -> source inconnue '{s}'")

# DEUX FICHES POUR UNE SEULE PERSONNE — le doublon que rien ne signalait.
# Le 27 aout 2026, l'ouverture de l'import aux cousins a fait entrer une deuxieme
# ARGIRA ANNA PEDIRODA a cote de la `zia-algira` deja travaillee : meme jour de
# naissance, meme jour de mort, meme escalier. Le rapprochement de `merge_heredis.py`
# ne les a pas vues parce qu'il compare des CHAINES, et que la premiere s'ecrit
# ALGIRA et la seconde ARGIRA. C'est la lecon PAIRE / PAYRE / PERRET, appliquee
# cette fois au code qui fusionne au lieu du chercheur qui interroge.
#
# LE CONTROLE NE TRANCHE PAS, IL FAIT REGARDER : deux PIEDERODA nes le meme
# 2 juillet 1662 sont ressortis avec, et ce sont de VRAIS JUMEAUX, morts a deux jours
# d'intervalle. Un meme jour de naissance est un signal, jamais une preuve.
par_naissance = {}
for p in _persons_liste:
    d = ((p.get("birth") or {}).get("date") or {}).get("iso")
    if d and len(d) == 10:
        par_naissance.setdefault((re.sub(r"\W", "", (p.get("surname") or "").upper()), d),
                                 []).append(p["id"])
for (nom, d), ids in sorted(par_naissance.items()):
    if len(ids) > 1:
        warnings.append(
            f"MEME NOM, MEME JOUR DE NAISSANCE : {nom} ne(e) le {d} -> {', '.join(ids)}"
            " -- jumeaux, ou deux fiches pour une seule personne ? A regarder.")

for u in unions:
    for pid in u["partners"]:
        if pid is not None and pid not in persons:
            errors.append(f"{u['id']}.partners -> personne inconnue '{pid}'")
    for c in u.get("children", []):
        if c not in persons:
            errors.append(f"{u['id']}.children -> personne inconnue '{c}'")
    pl = (u.get("marriage") or {}).get("place")
    if pl and pl not in places:
        errors.append(f"{u['id']}.marriage.place -> lieu inconnu '{pl}'")
    ms = (u.get("marriage") or {}).get("source")
    if ms and ms not in sources:
        errors.append(f"{u['id']}.marriage.source -> source inconnue '{ms}'")

for e in events:
    for part in e.get("participants", []):
        if part["person"] not in persons:
            errors.append(f"{e['id']} -> personne inconnue '{part['person']}'")
    if e.get("place") and e["place"] not in places:
        errors.append(f"{e['id']}.place -> lieu inconnu '{e['place']}'")
    if e["source"] not in sources:
        errors.append(f"{e['id']}.source -> source inconnue '{e['source']}'")
    # `sources_complementaires` ETAIT ECRIT PAR PERSONNE ET LU PAR PERSONNE. Trente-cinq
    # evenements le portaient le 21 septembre 2026 -- un moment peut tenir de trois temoins,
    # et c'est le cas d'une adresse du corpus -- mais rien ne verifiait ces identifiants et
    # rien ne les affichait : la page ne citait que le premier. Meme famille que le champ
    # `sig` du 18 septembre, un champ valide, invisible, et faux sans qu'on le sache.
    for s in e.get("sources_complementaires") or []:
        if s not in sources:
            errors.append(f"{e['id']}.sources_complementaires -> source inconnue '{s}'")
        elif s == e["source"]:
            errors.append(f"{e['id']}.sources_complementaires -> '{s}' est deja la source "
                          f"principale")

# --- coherence chronologique -------------------------------------------------
for u in unions:
    my = year((u.get("marriage") or {}).get("date"))
    for pid in u["partners"]:
        if not pid:
            continue
        b, d = vital(pid, "birth"), vital(pid, "death")
        # Un enfant ne avant le mariage de ses parents n'est pas une anomalie de saisie
        # des qu'un acte l'explique : `naissance_avant_mariage` porte la raison, et
        # l'avertissement la repete au lieu de reposer la question. Cas d'espece :
        # Angeline BARITEAU, reconnue par son pere des la declaration, legitimee en 1890.
        motif_nm = u.get("naissance_avant_mariage")
        if my and b and my - b < 15:
            warnings.append(f"{u['id']} : {pid} aurait {my - b} ans a son mariage")
        if my and d and my > d:
            errors.append(f"{u['id']} : mariage ({my}) apres le deces de {pid} ({d})")
    for c in u.get("children", []):
        cb = vital(c, "birth")
        if not cb:
            continue
        for pid in u["partners"]:
            if not pid:
                continue
            pb, pd = vital(pid, "birth"), vital(pid, "death")
            if pb and cb - pb < 14:
                errors.append(f"{u['id']} : {c} ({cb}) ne quand {pid} ({pb}) a {cb - pb} ans")
            if pb and cb - pb > 42 and persons[pid]["sex"] == "F":
                key = f"{u['id']}/{c}"
                msg = f"{u['id']} : {c} ({cb}) ne quand sa mere {pid} a {cb - pb} ans"
                (acked if key in ACKNOWLEDGED else warnings).append(
                    f"{msg} -- {ACKNOWLEDGED[key]}" if key in ACKNOWLEDGED else msg)
            if pd and cb > pd + 1:
                errors.append(f"{u['id']} : {c} ({cb}) ne apres le deces de {pid} ({pd})")
        if my and cb < my:
            msg = f"{u['id']} : {c} ne en {cb}, avant le mariage de {my}"
            (acked if motif_nm else warnings).append(
                f"{msg} -- {motif_nm}" if motif_nm else msg + " (legitimation ?)")

# --- un participant porte TOUJOURS un role -----------------------------------
# AJOUTE LE 14 SEPTEMBRE 2026, APRES DEUX BUILDS CASSES EN UNE JOURNEE. `build_poc.py`
# lit `q["role"]` sans filet : un participant ecrit sans role fait tomber la generation
# de la page avec un KeyError, APRES que la validation a dit « 0 erreur ». Le defaut
# vient du versement a la main -- on ecrit {"person": "..."} et on oublie le reste --
# et il ne se voyait qu'au moment de publier, sur un message de traceback.
# LA VALIDATION DOIT ATTRAPER CE QUI CASSE LE BUILD, sinon elle ne protege de rien.
for e in events:
    for q in list(e.get("participants", [])) + list(e.get("participants_extra", [])):
        if "person" not in q:
            errors.append(f"{e['id']} : participant sans `person` -- {q}")
        elif "role" not in q:
            errors.append(f"{e['id']} : {q['person']} n'a pas de `role` "
                          f"(subject / spouse / mentioned / participant / witness...)")

# --- une date, un seul endroit ----------------------------------------------
# Naissances et deces vivent dans persons.json. Quand un evenement narratif porte le
# meme fait, sa date doit y etre identique : sinon la fiche affiche le 9 juillet 1939
# et la trame « 1939-1940 » pour la meme naissance.
for e in events:
    if e["type"] not in ("birth", "death"):
        continue
    for w in e.get("participants", []):
        if w["role"] != "subject" or w["person"] not in persons:
            continue
        fiche = (persons[w["person"]].get(e["type"]) or {}).get("date")
        dv = e.get("date")
        if fiche and dv and (fiche.get("iso") != dv.get("iso") or fiche.get("kind") != dv.get("kind")):
            errors.append(f"{e['id']} : date {dv} != fiche de {w['person']} {fiche}")

# --- controle d'extraction via la numerotation du poster ---------------------
# `sosa_in_source` n'est PAS la structure du modele : la parente vit dans unions.json,
# qui porte les fratries entieres. Mais tant que le poster est une source, sa numerotation
# reste un excellent controle de relecture -- c'est elle qui a fait apparaitre une erreur
# de lecture des numeros (752/753 au lieu de 756/759).
by_sosa = {p["sosa_in_source"]: pid for pid, p in persons.items() if p.get("sosa_in_source")}
for sosa, pid in sorted(by_sosa.items()):
    if sosa < 2:
        continue
    expected_sex = "M" if sosa % 2 == 0 else "F"
    if persons[pid]["sex"] != expected_sex and sosa > 2:
        errors.append(f"sosa {sosa} ({pid}) : sexe {persons[pid]['sex']}, attendu {expected_sex}")
    father, mother = by_sosa.get(sosa * 2), by_sosa.get(sosa * 2 + 1)
    if father or mother:
        ok = any(pid in u.get("children", []) and
                 (father in u["partners"] or mother in u["partners"]) for u in unions)
        # Un ecart declare n'est pas une erreur de saisie : c'est un arbitrage.
        # `sosa_parents_disputed` porte la raison, et l'ecart passe en avertissement --
        # de sorte qu'un detachement REFLECHI reste visible sans bloquer, tandis qu'un
        # detachement accidentel continue de lever une erreur. Premier cas : sosa 22,
        # dont l'acte de naissance nomme d'autres parents que le poster.
        motif = persons[pid].get("sosa_parents_disputed")
        if not ok and motif:
            warnings.append(f"sosa {sosa} ({pid}) : detache de ses parents sosa "
                            f"{sosa*2}/{sosa*2+1} -- {motif}")
        elif not ok:
            errors.append(f"sosa {sosa} ({pid}) : aucune union ne le relie a ses parents sosa {sosa*2}/{sosa*2+1}")

# --- un participant qui n'etait pas ne ---------------------------------------
# LA REGLE DES POINTS DE VUE, PRISE PAR L'AUTRE BOUT. `--vues` demande « que lit cette
# personne ? » et pousse a repondre par un texte ; il ne demande jamais « a-t-elle quelque
# chose a faire la ? ». CLAUDE.md le dit deja pour les evenements POSTERIEURS a la mort
# d'un participant -- Urbain CHASLE et ses trois moments posthumes. Le 31 aout 2026, le généalogiste
# a vu le cas symetrique et personne ne le controlait : la vie de marechal-ferrant de
# Clement LOYAU, datee 1930-1970, s'affichait sur la trame de son fils Jean, NE EN 1943.
# Elle y etait parce qu'il en est le TEMOIN -- et un temoin se dit par la `source`, pas en
# entrant dans les participants.
#
# Le controle ne tranche pas, il fait regarder : un enfant peut legitimement etre nomme
# dans un acte anterieur a sa naissance (une clause de contrat, une promesse de mariage),
# et `vue_ok` sert alors a le dire. Mais un ecart de treize ans sur un souvenir, non.
pas_nes = []
for e in events:
    ey = year(e.get("date"))
    if not ey:
        continue
    for q in list(e.get("participants", [])) + list(e.get("participants_extra", [])):
        pid = q["person"]
        if pid not in persons or pid in (e.get("vue_ok") or []):
            continue
        b = vital(pid, "birth")
        if b and ey < b:
            pas_nes.append((e["id"], pid, b - ey))
if pas_nes:
    warnings.append(
        f"PAS ENCORE NES : {len(pas_nes)} participants figurent sur un evenement anterieur a "
        f"leur naissance -- ils en sont le temoin ou la source, pas l'acteur, et le moment "
        f"s'affiche sur leur trame avant qu'ils existent. Detail : "
        f"`python scripts/build.py --pasnes`")

if "--pasnes" in sys.argv:
    print("")
    print(">> participants d'un evenement anterieur a leur naissance")
    for eid, pid, ecart in sorted(pas_nes, key=lambda t: -t[2]):
        print(f"  {eid:<40} {pid:<28} {ecart} ans avant sa naissance")

# --- un participant deja mort ------------------------------------------------
# LE MEME CONTROLE PAR L'AUTRE BOUT, ET IL MANQUAIT. `--pasnes` attrape celui qui n'etait
# pas encore ne ; rien n'attrapait celui qui etait DEJA MORT. CLAUDE.md decrit pourtant le
# cas depuis le 27 aout 2026 -- Urbain CHASLE et ses trois moments posthumes, « il etait
# mort depuis trente-trois ans quand... », qui ne disent rien de lui et datent l'autre.
#
# Le 9 septembre 2026, ANDREE LE PIPE est entree comme participante du recensement de 1931
# avec un narratif expliquant pourquoi, A QUINZE ANS, elle n'etait pas au foyer de sa mere.
# Elle etait morte en aout 1916, A HUIT MOIS, et sa fiche le disait. Son absence du
# registre n'etait pas un fait a expliquer : c'etait la seule chose possible. Le corpus
# ecrivait « ses DEUX soeurs » ; la correction en « trois » a ete versee par-dessus.
#
# LE CONTROLE NE TRANCHE PAS, IL FAIT REGARDER, et CLAUDE.md nomme lui-meme les deux
# exceptions : quand la mention est la SEULE TRACE connue de la personne (Charle PINEAUX,
# Jeanne GOUSSON, Jean Marie MERIEN n'existent que par un acte qui les dit defunts), et
# quand elle APPREND un fait. `vue_ok` sert a le dire, comme pour `--pasnes`.
posthumes = []
for e in events:
    ey = year(e.get("date"))
    if not ey:
        continue
    for q in list(e.get("participants", [])) + list(e.get("participants_extra", [])):
        pid = q["person"]
        if pid not in persons or pid in (e.get("vue_ok") or []):
            continue
        d = vital(pid, "death")
        if d and ey > d:
            posthumes.append((e["id"], pid, ey - d))
if posthumes:
    warnings.append(
        f"DEJA MORTS : {len(posthumes)} participants figurent sur un evenement posterieur a "
        f"leur mort -- le moment s'affiche sur leur trame apres qu'ils ont cesse d'exister, "
        f"et il ne dit d'eux que le temps ecoule. Detail : "
        f"`python scripts/build.py --posthumes`")

if "--posthumes" in sys.argv:
    print("")
    print(">> participants d'un evenement posterieur a leur mort")
    for eid, pid, ecart in sorted(posthumes, key=lambda t: -t[2]):
        print(f"  {eid:<40} {pid:<28} {ecart} ans apres sa mort")

# --- deux postes au meme moment ----------------------------------------------
# ON NE PEUT PAS ETRE EN POSTE A DEUX ENDROITS A LA FOIS, et rien ne le verifiait.
# Le 31 aout 2026, le généalogiste a lu sur la trame de Jean DURAND : Rochefort de 1975 a 1990,
# Mururoa en 1978, l'etat-major de Tours de 1981 a 1985. Les trois se chevauchaient, et
# la rencontre avec sa future femme etait racontee DEUX FOIS -- une version approximative dans le
# moment de Rochefort, une version complete sur son propre moment.
#
# LA CAUSE EST UNE FACON DE TRAVAILLER, PAS UNE FAUTE DE SAISIE : un temoignage neuf a ete
# verse en creant des moments precis, sans reprendre les anciens, approximatifs, qui
# racontaient deja la meme chose en plus flou. C'est le genre d'incoherence qu'on ne voit
# pas en relisant ce qu'on vient d'ecrire, et qui saute aux yeux sur la page.
#
# Le controle ne regarde que les moments de type `life` QUI PORTENT UN LIEU : un poste, une
# affectation, un sejour. Deux d'entre eux qui se recouvrent sur la meme personne sont a
# regarder -- pas forcement faux (on peut etre affecte quelque part et partir en mission),
# mais jamais anodin.
def _bornes(dv):
    if not dv:
        return None
    a = year(dv)
    b = re.match(r"^(\d{4})", dv.get("to") or dv.get("iso") or "")
    return (a, int(b.group(1))) if a and b else ((a, a) if a else None)

postes = {}
for e in events:
    if e.get("type") != "life" or not e.get("place"):
        continue
    b = _bornes(e.get("date"))
    if not b:
        continue
    for q in e.get("participants", []):
        if q.get("role") == "subject" and q["person"] in persons:
            postes.setdefault(q["person"], []).append((b, e["id"], e["place"]))

chevauche = []
for pid, lot in postes.items():
    lot.sort()
    for i in range(len(lot)):
        for j in range(i + 1, len(lot)):
            (a1, b1), e1, l1 = lot[i]
            (a2, b2), e2, l2 = lot[j]
            if l1 != l2 and a2 <= b1 and a1 <= b2:
                chevauche.append((pid, e1, l1, a1, b1, e2, l2, a2, b2))

if chevauche:
    warnings.append(
        f"DEUX POSTES A LA FOIS : {len(chevauche)} paires de moments situes se recouvrent sur "
        f"la meme personne -- on n'est pas affecte a deux endroits en meme temps. Detail : "
        f"`python scripts/build.py --postes`")

if "--postes" in sys.argv:
    print("")
    print(">> moments situes qui se recouvrent sur une meme personne")
    for pid, e1, l1, a1, b1, e2, l2, a2, b2 in sorted(chevauche):
        print(f"  {pid}")
        print(f"      {e1:<34} {l1:<22} {a1}-{b1}")
        print(f"      {e2:<34} {l2:<22} {a2}-{b2}")

# --- un moment sans date se range APRES la mort -------------------------------
# LA PAGE TRIE PAR DATE, ET CE QUI N'EN A PAS TOMBE A LA FIN. Sur la trame de Paolina
# MIGOT, le magasin de souvenirs d'Argeles-sur-Mer -- vingt ans de sa vie -- s'affichait
# APRES sa mort, en dernier, parce que son `date.kind` valait "unknown". Le généalogiste, le
# 12 septembre 2026 : « son travail a Argeles n'est pas date il est a la fin ».
#
# Ne pas savoir quand est legitime ; laisser le moment sans borne ne l'est pas. Une borne
# approximative -- `after`, `about`, `range` -- le remet a sa place dans la vie, et c'est
# presque toujours possible : un magasin tenu avec le second mari est posterieur au
# veuvage, et le corpus connait la date du veuvage.
sansdate = []
for e in events:
    d = e.get("date") or {}
    if d.get("kind") in (None, "unknown"):
        qui = [q["person"] for q in e.get("participants", []) if q["person"] in persons]
        sansdate.append((e["id"], qui))

if sansdate:
    warnings.append(
        f"MOMENTS SANS DATE : {len(sansdate)} moments n'ont aucune borne -- la page trie par "
        f"date, donc ils s'affichent EN DERNIER sur chaque trame, apres la mort. Detail : "
        f"`python scripts/build.py --sansdate`")

if "--sansdate" in sys.argv:
    print("")
    print(">> moments sans aucune borne de date -- ils tombent en fin de trame")
    for eid, qui in sorted(sansdate):
        print(f"  {eid:<40} {', '.join(qui[:4])}")

# --- une fourchette n'est pas une date sur un fait PONCTUEL -------------------
# UN MARIAGE ARRIVE UN JOUR ; UNE CARRIERE DURE QUARANTE ANS. Le controle ne mesure donc
# pas la largeur d'une fourchette -- il regarde si elle porte un fait ponctuel. Sur les
# douze fourchettes de plus de quinze ans du corpus, onze sont des DUREES parfaitement
# justes : la chasse dans les marais de 1947 a 2007, le marechal-ferrant de 1930 a 1970,
# le généalogiste qui grandit a Marennes de 1973 a 2001. Les signaler toutes noierait le seul cas
# qui compte.
#
# Le cas qui compte : le second mariage de Paolina MIGOT, affiche « entre le 14 juillet
# 1965 et le 1er janvier 2000 ». Trente-cinq ans, et la borne haute EST SA PROPRE MORT --
# la phrase dit donc « elle s'est mariee entre son veuvage et son deces », ce que le
# lecteur savait deja. Le généalogiste, le 12 septembre 2026 : « son mariage est date dans une
# fourchette jusqu'a 2000 ».
PONCTUELS = {"birth", "death", "marriage", "baptism", "divorce", "burial"}
LARGEUR = 10

def _etendue(dv):
    a = year(dv)
    m = re.match(r"^(\d{4})", (dv or {}).get("to") or "")
    return (a, int(m.group(1))) if a and m else None

# UNE FOURCHETTE IRREDUCTIBLE EXISTE, ET ELLE NE DOIT PAS CRIER INDEFINIMENT : un acte
# ferme jusqu'en 2031 ne se datera pas mieux aujourd'hui. Le champ `fourchette_assumee`
# porte alors la raison et le cas passe en anomalie confirmee -- meme mecanique que
# `sosa_parents_disputed` : un choix REFLECHI reste visible sans bloquer, un oubli
# continue d'avertir.
fourchettes, fourchettes_ok = [], []
for e in events:
    if (e.get("date") or {}).get("kind") != "range" or e.get("type") not in PONCTUELS:
        continue
    b = _etendue(e["date"])
    if b and b[1] - b[0] > LARGEUR:
        sujets = [q["person"] for q in e.get("participants", [])
                  if q.get("role") in ("subject", "spouse")]
        cible = fourchettes_ok if e.get("fourchette_assumee") else fourchettes
        cible.append(("evenement", e["id"], b[0], b[1], sujets, e.get("fourchette_assumee")))

for u in unions:
    m = u.get("marriage") or {}
    if (m.get("date") or {}).get("kind") != "range":
        continue
    b = _etendue(m["date"])
    if b and b[1] - b[0] > LARGEUR:
        motif = u.get("fourchette_assumee") or m.get("fourchette_assumee")
        cible = fourchettes_ok if motif else fourchettes
        cible.append(("union", u["id"], b[0], b[1], list(u.get("partners", [])), motif))

if fourchettes:
    warnings.append(
        f"FOURCHETTE SUR UN FAIT PONCTUEL : {len(fourchettes)} mariages, naissances ou deces "
        f"sont dates par une plage de plus de {LARGEUR} ans -- c'est de l'ignorance presentee "
        f"comme une date. Detail : `python scripts/build.py --fourchettes`")

for quoi, ident, a, b, _s, motif in fourchettes_ok:
    acked.append(f"{ident} : fourchette de {b - a} ans ({a}-{b}) sur un fait ponctuel -- {motif}")

if "--fourchettes" in sys.argv:
    print("")
    print(">> faits ponctuels dates par une plage trop large")
    for quoi, ident, a, b, sujets, _m in sorted(fourchettes):
        print(f"  {quoi:<10} {ident:<36} {a}-{b}  ({b - a} ans)")
        # LA BORNE HAUTE EGALE A LA MORT D'UN PARTICIPANT NE BORNE RIEN : elle dit
        # seulement qu'un vivant peut se marier, ce que personne n'ignore.
        for pid in sujets:
            p = persons.get(pid) or {}
            mort = year((p.get("death") or {}).get("date"))
            if mort and mort == b:
                print(f"             ^ la borne haute EST la mort de {pid} -- elle ne borne rien")

# --- points de vue ------------------------------------------------------------
# LA REGLE EST DANS CLAUDE.MD DEPUIS LE DEBUT, ET RIEN NE LA VERIFIAIT.
# « Un narratif reste vrai lu depuis la fiche de N'IMPORTE QUEL participant. Quand un
# meme evenement se raconte differemment selon le lecteur, ecrire une variante dans
# narrative_for. » Chaque participant voit l'evenement sur SA fiche : sans variante, il
# y lit le texte generique, ecrit du point de vue du sujet. Le 16 aout 2026, le généalogiste a
# rouvert ce point pour la enieme fois -- le bapteme de 1776 disait « le pere etait
# absent » et se lisait tel quel sur la fiche du pere, ou le fait qui le concerne est
# justement qu'il n'y etait pas. Il ne manquait pas la regle, il manquait le controle.
#
# Le sujet est exempt : le texte generique est ecrit de son cote, par construction.
# Pour les autres, deux issues -- une variante, ou une exemption explicite dans
# `vue_ok: [person_id, ...]`, qui dit « verifie, le texte generique se lit bien depuis
# cette fiche ». Le silence n'est pas une des deux.
vues_manquantes = []
for e in events:
    if not e.get("narrative"):
        continue
    vus = set((e.get("narrative_for") or {}).keys()) | set(e.get("vue_ok") or [])
    for q in list(e.get("participants", [])) + list(e.get("participants_extra", [])):
        if q.get("role") == "subject" or q["person"] in vus:
            continue
        if q["person"] not in persons:
            continue
        vues_manquantes.append((e["id"], q["person"], q.get("role")))

if vues_manquantes:
    par_ev = {}
    for eid, pid, role in vues_manquantes:
        par_ev.setdefault(eid, []).append(f"{pid} ({role})")
    warnings.append(
        f"POINTS DE VUE : {len(vues_manquantes)} participants sur {len(par_ev)} evenements "
        f"n'ont ni variante `narrative_for` ni exemption `vue_ok` -- ils lisent sur leur "
        f"fiche un texte ecrit du point de vue d'un autre. Detail : `python scripts/build.py --vues`")

# --- champs inconnus ---------------------------------------------------------
# UN CHAMP INVENTE NE CASSE RIEN : IL DISPARAIT, ET C'EST PIRE. Le 18 septembre 2026,
# le signalement de Pierre Marie LE MOUEL -- chatain, yeux gris, 1 m 63 -- a ete ecrit
# dans un champ `sig` invente de toutes pieces. Le schema attend un OBJET `signalement`,
# que `build_poc.py` sait rendre ; `sig` n'est lu par personne. Rien n'a protege : la
# validation regardait les identifiants, les dates et les liens, jamais les NOMS DE CHAMPS.
# le généalogiste, en ouvrant la fiche : « le signalement n'est pas decrit ». Et le controle, ecrit
# le jour meme, a trouve QUATRE AUTRES `sig` dans le corpus PAIRE, invisibles depuis des
# semaines, plus un `surname_married` la ou le corpus dit `married_name`.
#
# C'EST UN AVERTISSEMENT, PAS UNE ERREUR, et il ne couvre pas sources.json : une fiche de
# source porte deliberement des champs libres -- `ce_qu_il_resout`, `le_prenom_de_la_mariee`,
# `les_militaires_du_sud` -- qui sont de la prose rangee, pas un schema. Ailleurs, un champ
# hors liste est presque toujours une faute de frappe ou un synonyme invente.
CHAMPS_CONNUS = {
    "persons.json": {
        "id", "surname", "given", "given_usual", "given_civil", "nickname", "names_used",
        "married_name", "sex", "living", "circle", "relations", "sources", "media",
        "birth", "death", "occupations", "residences", "education", "matricule",
        "signalement", "summary", "notes", "sensitivity", "sosa_in_source", "in_tree_pdf",
        "heredis_cid", "arrivee_argentine",
    },
    "events.json": {
        "id", "type", "date", "time", "place", "participants", "participants_extra",
        "narrative", "narrative_for", "vue_ok", "media", "source",
        "sources_complementaires", "confidence", "confidence_note", "note", "notes",
        "note_datation", "note_lieu", "verbatim", "verbatim_source", "verbatim_speaker",
        "timecode", "sensitivity", "disputed_by", "a_verifier", "todo",
    },
    "unions.json": {
        "id", "partners", "children", "marriage", "type", "start", "contract", "confidence",
        "source", "sources_complementaires", "note", "notes", "naissance_avant_mariage",
        "fourchette_assumee",
    },
    "places.json": {
        # `admin2` / `admin2_name` -- LE NIVEAU QUI SITUE, ET IL N'EST PAS FRANCAIS. Ces deux
        # champs s'appelaient `dept` / `dept_name` jusqu'au 25 septembre 2026 : departement en
        # France, province en Italie, wilaya en Algerie, c'est la meme idee et elle portait un
        # nom qui n'en couvrait qu'un tiers du monde. `dept` n'est plus reconnu -- un lieu qui
        # le porte encore ressort ici, et c'est voulu.
        "id", "name", "aliases", "commune", "admin2", "admin2_name", "region", "country",
        "insee", "coords", "coords_source", "coords_approx", "wikipedia",
        "wikipedia_cherche", "note", "lectures_incertaines", "todo",
    },
}
# Un `<champ>_disputed` est legitime partout ou `<champ>` l'est : on n'ecrase jamais en
# silence, l'autre version reste a cote avec la raison de l'arbitrage.
inconnus = []
for nom, objets in (("persons.json", persons.values()), ("events.json", events),
                    ("unions.json", unions), ("places.json", places.values())):
    connus = CHAMPS_CONNUS[nom]
    for o in objets:
        for k in o:
            base = k[:-9] if k.endswith("_disputed") else k
            if base not in connus:
                inconnus.append((nom, o.get("id", "?"), k))
if inconnus:
    warnings.append(
        f"CHAMPS INCONNUS : {len(inconnus)} champs ne sont dans aucun schema -- ils sont "
        f"ecrits dans le JSON et LUS PAR PERSONNE. Detail : "
        f"`python scripts/build.py --champs`")

if "--champs" in sys.argv:
    print("\n>> champs qu'aucun schema ne connait (sources.json est exclu a dessein)")
    for nom, oid, champ in sorted(inconnus):
        print(f"  {nom:<14} {oid:<34} {champ}")

# --- un pays dementi par ses propres coordonnees ------------------------------
# UN CHAMP PEUT PORTER LE BON NOM ET LA MAUVAISE VALEUR, ET AUCUN CONTROLE NE REGARDAIT
# LA VALEUR. Le 25 septembre 2026, trois lieux du corpus se disaient EN FRANCE pendant
# que leurs propres coordonnees -- ecrites dans le meme enregistrement, par Wikipedia,
# avec l'article -- les placaient en Italie : AZZANO DECIMO (45,88 / 12,72, Frioul),
# SALERNE (40,68 / 14,77, c'est-a-dire SALERNO en Campanie et non la commune du Var) et
# GONNOSFANADIGA (39,49 / 8,66, Sardaigne).
#
# ILS VIENNENT TOUS DE L'IMPORT HEREDIS, QUI A ESTAMPILLE « France » SUR TOUT CE QU'IL
# CREAIT. Leur `note` le dit d'ailleurs en toutes lettres -- « a verifier et completer
# (departement/pays a confirmer) » -- et personne n'est revenu confirmer. L'erreur etait
# invisible a l'affichage : `lieu()` n'ecrit pas « France » a un lecteur francais, donc
# un lieu italien marque France s'affichait NU, exactement ce que la regle interdit.
#
# LE TEST NE DEDUIT RIEN : il oppose deux valeurs deja ecrites. Des boites genereuses,
# et on ne signale que ce qui tombe franchement dehors.
#
# ET LA FRANCE N'EST PAS D'UN SEUL TENANT -- premiere version du test, meme journee : elle
# n'avait qu'une boite metropolitaine, et elle a accuse MURUROA, FANGATAUFA et HAO, qui
# sont francais. Un detecteur qui crie sur du vrai est du bruit, et c'est ainsi qu'on
# apprend a ne plus le lire. Chaque pays porte donc une LISTE de boites.
BOITES = {
    "France": [
        (41.3, 51.2, -5.2, 9.6),        # metropole et Corse
        (14.3, 16.6, -61.9, -60.7),     # Guadeloupe, Martinique
        (2.0, 6.0, -54.7, -51.5),       # Guyane
        (-21.5, -12.5, 44.9, 55.9),     # La Reunion, Mayotte
        (-28.0, -7.0, -155.0, -134.0),  # Polynesie francaise
        (-23.0, -18.0, 163.0, 169.0),   # Nouvelle-Caledonie
        (46.7, 47.2, -56.5, -56.1),     # Saint-Pierre-et-Miquelon
    ],
    "Italie":    [(35.4, 47.2, 6.5, 18.6)],
    "Suisse":    [(45.8, 47.9, 5.9, 10.6)],
    "Allemagne": [(47.2, 55.1, 5.8, 15.1)],
    "Algérie":   [(18.9, 37.2, -8.7, 12.0)],
    "Maroc":     [(27.6, 35.95, -13.2, -0.9)],
    "Argentine": [(-55.1, -21.7, -73.6, -53.6)],
    "Albanie":   [(39.6, 42.7, 19.2, 21.1)],
}
pays_dementis = []
for pl in places.values():
    c, xy = pl.get("country"), pl.get("coords")
    boites = BOITES.get(c or "France")
    if not boites or not (isinstance(xy, list) and len(xy) == 2):
        continue
    lat, lon = xy
    if not any(s <= lat <= n and o <= lon <= e for s, n, o, e in boites):
        pays_dementis.append((pl["id"], c or "France (implicite)", lat, lon))

if pays_dementis:
    warnings.append(
        f"PAYS DEMENTI PAR SES COORDONNEES : {len(pays_dementis)} lieux declarent un pays "
        f"ou leurs propres coordonnees ne tombent pas -- la valeur est fausse dans l'un des "
        f"deux champs, et un lieu etranger marque France s'affiche NU. Detail : "
        f"`python scripts/build.py --pays`")

if "--pays" in sys.argv:
    print("\n>> pays dementis par les coordonnees du meme enregistrement")
    for lid, c, lat, lon in sorted(pays_dementis):
        print(f"  {lid:<28} dit {c:<22} coords {lat}, {lon}")

# --- personnes hors de l'arbre -----------------------------------------------
# LA PARENTE VIT DANS unions.json, ET UNE PERSONNE QU'ON Y OUBLIE N'EXISTE PAS POUR
# L'ARBRE. Le 26 aout 2026, URBAIN CHASLE, JEANNE MEE, MICHEL FRANCOIS GALLET et
# MADELAINE BARDEAU sont entres avec leur fiche, leur source et leur narratif -- et
# aucune union. Sur la fiche de leur fils on lisait « conjointe » et « fils », jamais
# « pere » ni « mere » : deux generations trouvees le jour meme, invisibles dans
# l'arbre, et c'est le généalogiste qui l'a vu sur la page publiee.
#
# LA REGLE SEULE NE SUFFISAIT PAS -- elle n'etait meme ecrite nulle part. Le compte est
# donc affiche a chaque build : il ne tombera jamais a zero (un temoin, un parrain, un
# voisin nomme par un acte n'ont pas a etre rattaches), mais IL EST STABLE, et deux de
# plus apres une session qui vient de creer des ascendants se voient d'un coup d'oeil.
rattaches = {c for u in unions for c in (u.get("children") or [])}
rattaches |= {p for u in unions for p in (u.get("partners") or []) if p}
hors_arbre = sorted(pid for pid in persons if pid not in rattaches)
if hors_arbre:
    warnings.append(
        f"HORS DE L'ARBRE : {len(hors_arbre)} personnes ne figurent dans AUCUNE union, ni "
        f"comme partenaire ni comme enfant -- elles ont une fiche que rien ne relie. Un "
        f"temoin ou un parrain a le droit d'y etre ; UN ASCENDANT QU'ON VIENT DE TROUVER, "
        f"NON. Detail : `python scripts/build.py --orphelins`")

if "--orphelins" in sys.argv:
    print("\n>> personnes ne figurant dans aucune union")
    for pid in hors_arbre:
        p = persons[pid]
        print(f"  {pid:<34} {p.get('given','')} {p.get('surname','')}")

if "--vues" in sys.argv:
    print("\n>> participants sans point de vue verifie")
    for eid in sorted({v[0] for v in vues_manquantes}):
        print(f"  {eid}")
        for _, pid, role in [v for v in vues_manquantes if v[0] == eid]:
            print(f"      {pid:<32} {role}")

# --- rapport -----------------------------------------------------------------
print(f"{len(persons)} personnes, {len(unions)} unions, {len(events)} evenements narratifs, "
      f"{len(places)} lieux, {len(sources)} sources")
in_pdf = sum(1 for p in persons.values() if p.get("sosa_in_source") and p.get("in_tree_pdf") is not False)
print(f"  dont {in_pdf} issues de l'arbre PDF, {len(persons) - in_pdf} du seul recit oral")
conf = {}
for p in persons.values():
    for k in ("birth", "death"):
        c = (p.get(k) or {}).get("confidence")
        if c:
            conf[c] = conf.get(c, 0) + 1
print(f"  confiance des dates vitales : {conf}")

for a in acked:
    print(f"  [ok] {a}")
for w in warnings:
    print(f"  [!] {w}")
for e in errors:
    print(f"  [ERREUR] {e}")
print(f"\n{len(errors)} erreur(s), {len(warnings)} avertissement(s), {len(acked)} anomalie(s) confirmee(s)")


# --- export GEDCOM 5.5.1 -----------------------------------------------------
def ged_date(dv):
    if not dv:
        return None
    MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    kind = dv.get("kind")
    if kind == "unknown":
        return None

    def fmt(iso):
        parts = (iso or "").split("-")
        if len(parts) == 3:
            return f"{int(parts[2])} {MONTHS[int(parts[1]) - 1]} {parts[0]}"
        if len(parts) == 2:
            return f"{MONTHS[int(parts[1]) - 1]} {parts[0]}"
        return parts[0]

    if kind in ("exact", "year", "republican"):
        return fmt(dv.get("iso"))
    if kind == "about":
        return "ABT " + fmt(dv.get("iso"))
    if kind == "before":
        return "BEF " + fmt(dv.get("iso"))
    if kind == "range":
        return f"BET {fmt(dv.get('from'))} AND {fmt(dv.get('to'))}"
    return None


def export_gedcom(path):
    xref = {pid: f"@I{i + 1:04d}@" for i, pid in enumerate(persons)}
    L = ["0 HEAD", "1 SOUR genealog.ia", "2 VERS 0.1", "1 GEDC", "2 VERS 5.5.1",
         "2 FORM LINEAGE-LINKED", "1 CHAR UTF-8",
         "1 NOTE Corpus genealog-ia : chaque valeur porte sa source.",
         "2 CONT Les personnes vivantes sont marquees RESN privacy."]

    fam_of, fams_of = {}, {}
    for i, u in enumerate(unions):
        fx = f"@F{i + 1:04d}@"
        fam_of[u["id"]] = fx
        for pid in u["partners"]:
            if pid:
                fams_of.setdefault(pid, []).append(fx)

    for pid, p in persons.items():
        L.append(f"0 {xref[pid]} INDI")
        given = p.get("given") or ""
        L.append(f"1 NAME {given} /{p.get('surname') or '?'}/")
        L.append(f"1 SEX {p.get('sex', 'U')}")
        if p.get("living"):
            L.append("1 RESN privacy")
        for occ in p.get("occupations", []):
            # Cinq metiers du corpus s'ecrivent `label` et non `value` -- entres par
            # les actes d'Usson et de Saint-Pal. `build_poc.py` accepte les deux
            # depuis le debut ; l'export GEDCOM, lui, plantait sur le premier.
            metier = occ.get("value") or occ.get("label")
            if metier:
                L.append(f"1 OCCU {metier}")
        for key, tag in (("birth", "BIRT"), ("death", "DEAT")):
            ev = p.get(key)
            if not ev:
                continue
            L.append(f"1 {tag}")
            d = ged_date(ev.get("date"))
            if d:
                L.append(f"2 DATE {d}")
            if ev.get("place"):
                L.append(f"2 PLAC {places[ev['place']]['name']}")
            if ev.get("confidence") in ("medium", "low"):
                L.append(f"2 NOTE confiance : {ev['confidence']} (scan flou ou deduction)")
            orig = (ev.get("date") or {}).get("original")
            if orig:
                L.append(f"2 NOTE date republicaine d'origine : {orig}")
        for n in p.get("notes", []):
            L.append("1 NOTE " + n.replace("\n", " "))
        if p.get("sosa_in_source"):
            L.append(f"1 REFN {p['sosa_in_source']}")
            L.append("2 TYPE Sosa (position dans le poster source)")
        for fx in fams_of.get(pid, []):
            L.append(f"1 FAMS {fx}")
        for u in unions:
            if pid in u.get("children", []):
                L.append(f"1 FAMC {fam_of[u['id']]}")

    for u in unions:
        L.append(f"0 {fam_of[u['id']]} FAM")
        for pid in u["partners"]:
            if not pid:
                continue
            L.append(f"1 {'HUSB' if persons[pid]['sex'] == 'M' else 'WIFE'} {xref[pid]}")
        for c in u.get("children", []):
            L.append(f"1 CHIL {xref[c]}")
        m = u.get("marriage")
        if m:
            L.append("1 MARR")
            d = ged_date(m.get("date"))
            if d:
                L.append(f"2 DATE {d}")
            if m.get("place"):
                L.append(f"2 PLAC {places[m['place']]['name']}")
        for n in u.get("notes", []):
            L.append("1 NOTE " + n)

    L += ["0 TRLR", ""]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    print(f"\nGEDCOM ecrit : {path} ({len(L)} lignes)")


if "--gedcom" in sys.argv:
    # LE NOM DU FICHIER DIT « paire », ET RIEN NE VERIFIAIT QUE C'EST BIEN LUI QU'ON
    # EXPORTE. `--gedcom` ecrivait `export/paire.ged` sans regarder GENEALOGIA_DATA : une
    # validation lancee sur le corpus d'un ami -- DUPONT, MARTIN -- y aurait verse SON
    # arbre sous le nom de celui du généalogiste. Et contrairement a `poc/index.html`, que git
    # ignore, CE FICHIER-LA EST SUIVI : la session suivante l'aurait committe sans le voir.
    # Meme famille de faute que l'attelage croise de `build_media.py` et `build_poc.py`,
    # corrige le 18 septembre 2026 ; meme garde, et pour la meme raison -- le généalogiste :
    # « plus qu'une lecon, il faut que ce soit mecaniquement infaisable ».
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import corpus_io as _garde
    export_gedcom(_garde.sortie("GENEALOGIA_GEDCOM",
                                os.path.join(ROOT, "export", "paire.ged")))

sys.exit(1 if errors else 0)
