"""Genere le bundle de donnees compact embarque dans la page de demonstration."""
import json, io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# UN SECOND CORPUS SE CONSTRUIT SANS TOUCHER AU PREMIER. Trois variables suffisent :
#   GENEALOGIA_DATA   le repertoire des cinq JSON
#   GENEALOGIA_MEDIA  le media.json
#   GENEALOGIA_OUT    la page produite
# Sans elles, le comportement est exactement celui d'avant : data/, poc/media.json,
# poc/index.html. Ajoute le 4 septembre 2026 pour la famille DUPONT, qui n'est pas
# celle du généalogiste et n'a donc rien a faire dans data/.
#
# ELLES NE SONT PLUS FACULTATIVES L'UNE SANS L'AUTRE, ET C'EST MECANIQUE : poser
# GENEALOGIA_DATA sans les deux sorties ecrivait les donnees d'un corpus dans la page
# d'un autre, en silence. `corpus_io.sortie()` le refuse maintenant AVANT tout travail
# -- la raison complete est dans ce module, le 18 septembre 2026. Les deux appels sont
# ici, en tete, et non la ou les fichiers s'ecrivent : une garde qui se declenche apres
# trente secondes de calcul est une garde qu'on desactive.
import corpus_io as _garde

D = os.environ.get("GENEALOGIA_DATA") or os.path.join(ROOT, "data")
_MEDIA = _garde.sortie("GENEALOGIA_MEDIA", os.path.join(ROOT, "poc", "media.json"))
_OUT = _garde.sortie("GENEALOGIA_OUT", os.path.join(ROOT, "poc", "index.html"))
load = lambda n: json.load(io.open(os.path.join(D, n), encoding="utf-8"))

_persons_doc = load("persons.json")
persons = {p["id"]: p for p in _persons_doc["persons"]}
unions = load("unions.json")["unions"]
places = {p["id"]: p for p in load("places.json")["places"]}
events = load("events.json")["events"]
sources = {s["id"]: s for s in load("sources.json")["sources"]}


def year(dv):
    if not dv:
        return None
    m = re.match(r"^(\d{4})", dv.get("iso") or dv.get("from") or "")
    return int(m.group(1)) if m else None


def label(dv, ponctuel=False):
    """Date lisible par un humain, pas par une machine.

    `ponctuel` distingue les deux sens que porte un meme `range`. Sur un evenement, il
    decrit une DUREE — le sejour au Lioran, du 8 janvier au 4 mai 1941 — et « A-B » est
    juste. Sur une naissance, un deces ou un mariage, il decrit une INCERTITUDE : on ne
    nait pas pendant treize mois. Joseph PERRET s'affichait « ne 25 janvier 1825-23 janvier
    1826 », ce qui se lisait comme deux dates de naissance ; c'est un intervalle deduit de
    ses deux ages declares. Meme champ, sens opposes, et le rendu ne les distinguait pas.
    """
    if not dv or dv.get("kind") == "unknown":
        return ""
    MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
            "août", "septembre", "octobre", "novembre", "décembre"]
    def fr(iso):
        if not iso:
            return ""
        p = iso.split("-")
        if len(p) == 3:
            # Le premier jour du mois est un ORDINAL en français : « 1er janvier », jamais
            # « 1 janvier ». Vingt-trois dates du corpus tombent un premier, dont la mort
            # de Paolina MIGOT — que son propre résumé, écrit à la main, datait bien du
            # « 1er janvier 2000 » pendant que la fiche affichait « 1 janvier 2000 ».
            j = int(p[2])
            return f"{'1er' if j == 1 else j} {MOIS[int(p[1]) - 1]} {p[0]}"
        if len(p) == 2:
            return f"{MOIS[int(p[1]) - 1]} {p[0]}"
        return p[0]
    # « le » devant un jour, rien devant une annee ou un mois seuls : « le 14 juillet
    # 1965 », mais « 1965 » et « juillet 1965 ». Le `(?:er)?` rattrape le premier du
    # mois, que `fr` rend « 1er » : sans lui, « après le 1er janvier » perdait l'article.
    art = lambda s: ("le " + s) if re.match(r"^\d{1,2}(?:er)? ", s) else s
    k = dv.get("kind")
    if k == "about":
        return "vers " + art(fr(dv["iso"]))
    if k == "before":
        return "avant " + art(fr(dv["iso"]))
    if k == "after":
        # Sans cette branche, un « apres le 14 juillet 1965 » tombait dans le `return`
        # final et s'imprimait en date exacte : la page datait le remariage de Paolina
        # du jour de la mort de son premier mari.
        return "après " + art(fr(dv["iso"]))
    if k == "range":
        a, b = fr(dv.get("from")), fr(dv.get("to"))
        if a == b:
            return a
        if not ponctuel:
            return f"{a}–{b}"
        return f"entre {art(a)} et {art(b)}"
    if k == "republican":
        return f"{dv['original']} ({fr(dv['iso'])})"
    return fr(dv.get("iso"))


def clean(s):
    """Retire les marques de travail (« ? », « (?) ») qui n'ont rien a faire a l'ecran."""
    if not s:
        return ""
    s = re.sub(r"\s*\(\?\)", "", s).strip()
    return "" if s in ("?", "") else s


def signalement(s):
    """Le portrait physique relevé au conseil de révision, en une phrase lisible.

    Un registre matricule décrit chaque homme — cheveux, yeux, front, nez, visage, taille.
    C'est la seule description physique écrite qu'on ait de ceux qui sont morts avant la
    photographie de famille, et elle appartient au lecteur, pas aux notes de travail.
    """
    if not s:
        return None
    bouts = []
    if s.get("cheveux"):
        bouts.append(f"cheveux {s['cheveux']}")
    for k in ("yeux", "front", "nez", "visage"):
        if s.get(k):
            bouts.append(f"{k} {s[k]}")
    t = s.get("taille_cm")
    if t:
        bouts.append(f"{t // 100} m {t % 100}")
    return ", ".join(bouts) or None


def called(p):
    """Les noms sous lesquels on l'appelait, et qui les employait.

    Le nom d'usage n'est pas une decoration. Chez Alfiero PEDIRODA, arrive du Frioul en
    1952, il porte l'histoire de l'assimilation : Alfiero a l'etat civil, ALFRED dans la
    famille parce qu'apres la guerre les Italiens etaient mal vus, FREDDY au judo. Un
    recit qui appelle quelqu'un par un prenom que personne n'a jamais prononce sonne faux
    a ceux qui l'ont connu — c'est exactement ce que ce corpus existe pour eviter.
    """
    out = [{"v": n["value"], "by": n.get("context")}
           for n in (p.get("names_used") or []) if n.get("value")]
    return out or None


def name(pid):
    p = persons[pid]
    g, s = clean(p.get("given")), clean(p["surname"])
    if g and s:
        return f"{g} {s}"
    if g:
        return g
    return s or "personne non identifiée"


def lieu(pid):
    """Libelle lisible d'un lieu : « Madic (Cantal) », « La Bastide (Bort-les-Orgues, Corrèze) ».

    Un lecteur de la page n'est pas geographe. « Ne a Madic » ne dit rien a personne ; le
    departement entre parentheses situe en un mot. Regle : commune de rattachement d'abord
    pour un lieu-dit, puis le departement, puis le pays pour l'etranger. Si le nom porte
    deja une parenthese -- « Le Clapet (La Palmyre) » -- on n'en ajoute pas une seconde,
    on suffixe apres une virgule.
    """
    p = places.get(pid)
    if not p:
        return None
    n = p["name"]
    bouts = []
    if p.get("commune") and p["commune"] not in n:
        bouts.append(p["commune"])
    # SUBDIVISION POUR UN LIEU FRANCAIS, PAYS POUR UN LIEU ETRANGER -- et c'est ECRIT
    # depuis le 25 septembre 2026, alors que ca marchait par ACCIDENT auparavant : le champ
    # s'appelait `dept_name`, un lieu francais n'avait pas de `country`, un lieu etranger
    # n'avait pas de departement, et l'ordre des deux tests suffisait. Le champ unifie
    # `admin2_name` -- province italienne, wilaya, departement -- casse cet accident :
    # Valvasone porte desormais les deux. « Valvasone (Pordenone) » ne dit rien a un lecteur
    # francais, c'est « (Italie) » qu'il lui faut ; l'inverse vaut pour un lecteur italien,
    # et c'est l'application qui le sert, pas cette page-ci.
    pays = p.get("country")
    if pays and pays != "France":
        bouts.append(pays)
    elif p.get("admin2_name"):
        bouts.append(p["admin2_name"])
    elif pays:
        bouts.append(pays)
    # UN LIEU QUI EST SON PROPRE PAYS NE SE REPETE PAS. « Checoslovaquie » est tout ce
    # qu'on sait de l'endroit ou meurent Antonio et Filippo MIGOT : le nom du lieu EST
    # le nom du pays, et la regle generale rendait « Tchecoslovaquie (Tchecoslovaquie) ».
    # Demande du généalogiste, 25 septembre 2026 : « si on n'a que le pays ou la region, c'est ok ».
    bouts = [b for b in bouts if b != n]
    if not bouts:
        return n
    ctx = ", ".join(bouts)
    return f"{n}, {ctx}" if "(" in n else f"{n} ({ctx})"


# UNE FAMILLE N'EST PAS UNE CHAINE DE CARACTERES, ET C'EST TOUT LE SUJET DE CE
# CORPUS. Le filtre du panneau de gauche testait `surname === "CHASLES"`, si bien
# que les ancetres enregistres CHASLE, CHALLE ou CHALE n'y figuraient pas -- six
# personnes sur trente, dont les quatre generations les plus hautes. Un dossier
# dont la lecon centrale est qu'un nom n'a pas de forme fixe ne peut pas grouper
# ses gens sur la forme de leur nom.
#
# La table ci-dessous est EXPLICITE et se relit : chaque variante y est entree
# parce qu'un acte l'ecrit ainsi, pas parce qu'un algorithme l'a rapprochee. Une
# normalisation automatique (sans accents, sans doubles lettres) aurait aussi
# rapproche CHASLE de CHARLES, qui est une autre famille du meme canton -- le
# faux ami qui a coute trois verifications le 27 aout 2026.
VARIANTES = {
    "CHASLES": ("CHASLE", "CHALLE", "CHÂLE", "CHALE", "CHASLÉ", "CHALES"),
    "PAIRÉ": ("PAYRÉ", "PAIRET", "PERRET", "PEYRET", "PAYRE", "PEYRA", "PAIRE"),
    "MÉRAY": ("MEREE", "MAREY", "MAIRAY", "MÉE", "MÉRÉ", "MERAY"),
    # UN TREMA SUFFIT A COUPER UNE FAMILLE EN DEUX, ET PERSONNE NE LE VOIT DANS
    # LE JSON. Chez les DUPONT, le filtre du panneau de gauche affichait cote a
    # cote « LE MOUEL » (8 personnes) et « LE MOUEL » avec trema (6) : deux
    # boutons pour une seule famille de quatorze, qui mangeaient deux des six
    # places. Signale par le généalogiste le 18 septembre 2026, sur une capture de la page.
    # La coupure n'est pas une faute de saisie -- elle suit le siecle, les six
    # ancetres du XIXe portent le trema et les huit modernes non --, donc on ne
    # l'efface pas dans les fiches : on la rabat ici, ou est sa place.
    "LE MOUËL": ("LE MOUEL",),
}
_VERS = {v: canon for canon, vs in VARIANTES.items() for v in vs}


def famille(surname):
    """Le nom sous lequel une personne se range, variantes rabattues."""
    s = (surname or "").strip()
    return _VERS.get(s.upper(), s)


def metier(p):
    """LE METIER D'UNE VIE, PAS LE PREMIER DE LA LISTE.

    Jean PAIRE s'affichait « Etudiant » : la profession qu'il a declaree au
    conseil de revision a dix-neuf ans, avant de s'engager pour trente ans de
    gendarmerie. Sa fiche portait pourtant « militaire de carriere, puis
    gendarme mobile » juste en dessous. Signale par le généalogiste le 17 aout 2026.

    Et l'ancienne ligne ne lisait que `value`, quand la moitie des entrees
    portent `label` : Matthieu PEYRET, qui en a trois, n'avait AUCUN metier sur
    sa fiche. Un champ vide se voit ; un champ faux, non -- c'est le second bogue
    qui aura vecu le plus longtemps.

    L'ordre de la liste n'est pas chronologique (Matthieu porte 1755, 1752,
    1752). On trie donc sur la date quand elle est la, en gardant l'ordre
    d'ecriture pour departager les autres.

    ET QUAND IL Y EN A EU PLUSIEURS, ON LES MONTRE TOUS, DANS L'ORDRE.
    Signale par le généalogiste le 27 aout 2026 sur Jean Victor CHALE : sa fiche affichait
    « metier Meunier » quand son resume racontait deux metiers de plus. Le
    registre matricule venait d'en ajouter un troisieme -- DOMESTIQUE a vingt
    ans, valet de ferme chez un autre -- et c'est justement celui-la qui dit d'ou
    il partait. Un homme qui commence valet et finit meunier n'a pas « un
    metier » : il a une trajectoire, et l'ecraser sur le dernier echelon efface
    la seule chose que la suite raconte.

    Garde-fou : trois metiers longs font un en-tete illisible (le grand-pere
    LE PIPE en a un de soixante caracteres a lui seul). Au-dela du seuil, on
    retombe sur le dernier, qui reste le moins faux des raccourcis.

    LE SEUIL EST PASSE DE 78 A 88 LE 2 SEPTEMBRE 2026, ET LE REPLI EST LE VRAI
    DEFAUT. L'oncle Jo a quatre metiers dates -- forgeron, torpilleur, prepose
    des douanes, quartier-maitre electricien : 85 caracteres, donc l'en-tete
    n'affichait QUE le dernier, celui qu'il n'exerca que deux ans, en guerre.
    le généalogiste l'a vu sur la fiche : « les metiers ne sont pas tous marques dans
    l'en-tete ». Le repli « le dernier » suppose qu'une vie va vers son metier
    principal ; elle y revient parfois par le milieu.
    """
    occ = [o for o in (p.get("occupations") or []) if o.get("value") or o.get("label")]
    if not occ:
        return None
    # L'ordre de la liste n'est pas chronologique : on trie sur la date quand
    # elle est la, en gardant l'ordre d'ecriture pour departager les autres.
    # ON TRIE SUR L'ANNEE, PAS SUR LA REPRESENTATION DU DICTIONNAIRE. La ligne
    # d'avant faisait `str(o["date"])`, si bien qu'une entree datee ("{'kind':
    # 'year'...") passait APRES une entree sans date (""), quel que soit son
    # millesime : Jean Victor CHALE sortait « cultivateur, puis meunier, puis
    # domestique » alors que le domestique a vingt ans ouvre la serie.
    # ET `date` N'A PAS TOUJOURS LA MEME FORME dans occupations : tantot une
    # date_value ({kind, iso}), tantot une chaine nue ("1867"). Les deux sont
    # dans le corpus ; la fonction lit les deux plutot que d'imposer l'une.
    def annee(o):
        d = o.get("date") or ""
        if isinstance(d, str):
            return d[:4]
        return str(d.get("iso") or d.get("from") or "")[:4]
    occ = [o for _, o in sorted(enumerate(occ), key=lambda t: (annee(t[1]), t[0]))]
    # `value` est capitalise, `label` ne l'est pas : sans ca, la fiche affiche
    # « metier journalier » a cote de « metier Vendeuse ».
    vus, suite = set(), []
    for o in occ:
        m = (o.get("value") or o.get("label") or "").strip()
        if m and m.lower() not in vus:
            vus.add(m.lower())
            suite.append(m)
    if not suite:
        return None
    def cap(s):
        return s[:1].upper() + s[1:]
    chaine = cap(suite[0]) + "".join(", puis " + s[:1].lower() + s[1:] for s in suite[1:])
    return chaine if len(chaine) <= 88 else cap(suite[-1])


# --- personnes -------------------------------------------------------------
P = {}
for pid, p in persons.items():
    b, d = p.get("birth") or {}, p.get("death") or {}
    P[pid] = {
        "n": name(pid),
        "given": clean(p.get("given")),
        "surname": clean(p["surname"]),
        "fam": famille(p["surname"]),
        "civil": p.get("given_civil"),
        "called": called(p),
        "sex": p.get("sex", "U"),
        "living": bool(p.get("living")),
        "circle": p.get("circle"),
        "job": metier(p),
        "b": label(b.get("date"), True), "bp": lieu(b.get("place")), "bpid": b.get("place"),
        "by": year(b.get("date")), "bt": b.get("time"),
        "d": label(d.get("date"), True), "dp": lieu(d.get("place")), "dpid": d.get("place"),
        "dy": year(d.get("date")),
        "summary": p.get("summary"),
        "conf": b.get("confidence") or d.get("confidence"),
        # La provenance de chaque date vitale, pour que la trame puisse la montrer :
        # une naissance lue sur un poster et une naissance lue sur un acte ne valent
        # pas la meme chose, et le lecteur doit pouvoir en juger sans nous croire.
        "bsrc": b.get("source"), "dsrc": d.get("source"),
        "disputed": bool(p.get("birth_disputed")),
        "sig": signalement(p.get("signalement")),
    }

# --- parents / enfants / conjoints ----------------------------------------
for u in unions:
    a, b = (u["partners"] + [None, None])[:2]
    for x, y in ((a, b), (b, a)):
        if x and y:
            P[x].setdefault("spouses", []).append(y)
    for c in u.get("children", []):
        P[c].setdefault("parents", []).extend([x for x in (a, b) if x])
        for x in (a, b):
            if x:
                P[x].setdefault("children", []).append(c)
    m = u.get("marriage")
    if m and m.get("date", {}).get("kind") != "unknown":
        for x in (a, b):
            if x:
                P[x].setdefault("mar", []).append(
                    {"d": label(m["date"], True), "y": year(m["date"]),
                     "p": lieu(m.get("place")), "pid": m.get("place"),
                     "src": m.get("source"),
                     "with": (b if x == a else a)})

# --- fratries et amitiés ----------------------------------------------------
# Deux liens que le modèle porte depuis le début sans que la page les montre. La
# fratrie vient de deux endroits — les `children` d'une union, et les `relations`
# de type `sibling` pour les fratries dont les parents manquent (les filles LE PIPE
# en sont un cas). L'amitié n'existe QUE dans `relations` : Margot l'épicière ou
# Mimi DUPUIS ne sont dans aucun arbre, et c'est précisément pour elles que le
# champ existe. Les deux se déclarent dans un seul sens et se lisent dans les deux.
AMITIE = ("close_friend_of", "childhood_friend_of")


def relie(cle, a, b):
    """Pose le lien dans les deux sens, une seule fois.

    Les mêmes fratries arrivent par deux chemins — l'union des parents et la relation
    `sibling` déclarée — et une relation déclarée des deux côtés passe deux fois.
    """
    if a not in P or b not in P or a == b:
        return
    for x, y in ((a, b), (b, a)):
        if y not in P[x].setdefault(cle, []):
            P[x][cle].append(y)


for u in unions:
    fratrie = [c for c in u.get("children", []) if c in P]
    for i, x in enumerate(fratrie):
        for y in fratrie[i + 1:]:
            relie("sibs", x, y)

def pose(cle, a, b):
    """Un lien à sens unique : b entre dans la liste `cle` de a, pas l'inverse."""
    if a in P and b in P and a != b and b not in P[a].setdefault(cle, []):
        P[a][cle].append(b)


for pid, p in persons.items():
    for r in p.get("relations", []):
        if not r.get("person"):
            continue
        if r["type"] == "sibling":
            relie("sibs", pid, r["person"])
        elif r["type"] in AMITIE:
            relie("friends", pid, r["person"])
        # Le parrainage n'est pas symétrique : il se déclare indifféremment d'un côté
        # ou de l'autre, et se lit « parrain » d'un bout, « filleul » de l'autre.
        elif r["type"] in ("godfather_of", "godmother_of"):
            pose("parrains", r["person"], pid)
            pose("filleuls", pid, r["person"])
        elif r["type"] == "godchild_of":
            pose("parrains", pid, r["person"])
            pose("filleuls", r["person"], pid)
        # Oncle et cousin ne se deduisent pas ici : la parente laterale demanderait les
        # fratries des deux generations du dessus, et le corpus ne les a presque jamais.
        # Mais un acte, lui, ECRIT le lien -- « oncle de l'epouse », « cousin de l'epouse ».
        # On le pose tel qu'il est ecrit plutot que de le reconstruire ou de le perdre.
        elif r["type"] == "uncle_of":
            pose("oncles", r["person"], pid)
            pose("neveux", pid, r["person"])
        elif r["type"] == "cousin_of":
            relie("cousins", pid, r["person"])

# --- alliance : beaux-freres et belles-soeurs ------------------------------
# Le corpus ECRIT ce lien -- « les deux hommes etaient beaux-freres, ayant epouse
# deux soeurs » -- et la page ne le montrait pas. Martial MONTUS, qui n'entre dans
# cette famille QUE par alliance, n'affichait qu'un seul lien : sa femme. Georges
# NEAU, qui l'a fait entrer aux douanes, n'etait cliquable nulle part sur sa fiche.
# Trois chemins mènent au même mot en français courant : le frere du conjoint, le
# conjoint du frere, et le conjoint de la soeur du conjoint -- c'est ce troisieme
# qui relie les deux douaniers, et c'est celui qu'on oublie toujours.
#
# MAIS LE MOT SUPPOSE UN MARIAGE, ET LE CALCUL L'AVAIT OUBLIE. Le 29 aout 2026,
# le généalogiste a vu la page donner a Jean DURAND les freres et soeurs de la témoin
# pour beaux-freres et belles-soeurs : ils vivent ensemble depuis plus de quarante
# ans SANS ETRE MARIES, et l'alliance est un lien que seul le mariage cree. Le
# francais n'a d'ailleurs pas de mot pour le frere de sa compagne -- on dit « le
# frere de », et c'est tout.
#
# LA CAUSE EST UNE BONNE DECISION APPLIQUEE AU MAUVAIS ENDROIT. `spouses` est bati
# sur TOUTES les unions, parce que le modele refuse de faire du mariage la condition
# d'existence d'un couple -- sans quoi il effacerait la moitie des familles
# contemporaines. C'est juste pour AFFICHER LE COUPLE ; ce ne l'est pas pour deduire
# une parente par alliance. D'ou un jeu separe, `ALLIES`, qui ecarte les unions
# declarees non maritales.
#
# ET LE TEST NE PEUT PAS ETRE « a-t-elle une date de mariage ? » : la plupart des
# `marriage: null` du corpus sont des mariages dont on ignore la date -- soixante-dix
# unions au 29 aout 2026, presque tout l'Ancien Regime. Tester la date les
# supprimerait toutes. C'est le `type` qui tranche, et lui seul.
NON_MARITAL = {"concubinage", "union libre", "union", "pacs"}
ALLIES = {}
for u in unions:
    if (u.get("type") or "").strip().lower() in NON_MARITAL:
        continue
    a, b = (u["partners"] + [None, None])[:2]
    if a and b:
        ALLIES.setdefault(a, []).append(b)
        ALLIES.setdefault(b, []).append(a)

for pid, p in P.items():
    beaux = set()
    for s in ALLIES.get(pid, []):
        for t in P.get(s, {}).get("sibs", []):
            beaux.add(t)
            beaux.update(ALLIES.get(t, []))
    for s in p.get("sibs", []):
        beaux.update(ALLIES.get(s, []))
    beaux -= {pid}
    beaux -= set(p.get("spouses", []))
    beaux -= set(p.get("sibs", []))
    if beaux:
        p["beaux"] = [x for x in beaux if x in P]
    # `allies` voyage jusqu'a la page : elle en a besoin pour les MEMES raisons.
    # « son mari », « sa belle-mere », « son oncle par alliance » se deduisaient tous
    # de `spouses`, donc tous du concubinage aussi -- et la trame de la témoin appelait
    # Jean DURAND « son mari » apres quarante-cinq ans sans mariage. Le mot juste existe,
    # c'est « son compagnon » ; il fallait seulement savoir lequel des deux dire.
    if ALLIES.get(pid):
        p["allies"] = [x for x in ALLIES[pid] if x in P]

# --- evenements ------------------------------------------------------------
E = []
for e in events:
    parts = list(e.get("participants", [])) + list(e.get("participants_extra", []))
    E.append({
        "id": e["id"],
        "t": e["type"],
        "y": year(e.get("date")),
        "d": label(e.get("date")),
        "time": e.get("time"),
        "p": lieu(e.get("place")), "pid": e.get("place"),
        "txt": e.get("narrative", ""),
        "vue": e.get("narrative_for") or None,
        "v": e.get("verbatim"),
        # Un verbatim peut venir d'une autre source que le fait qu'il illustre, et
        # d'une autre voix que celle de l'entretien : la transcription du 6 aout n'est
        # pas diarisee, et le généalogiste y parle autant que la témoin.
        "vsrc": e.get("verbatim_source"),
        "vspk": (P.get(e.get("verbatim_speaker")) or {}).get("given"),
        "tc": e.get("timecode"),
        "src": e.get("source"),
        # UN MOMENT PEUT TENIR DE PLUSIEURS TEMOINS, et la page n'en citait qu'un. Le
        # 21 septembre 2026, une adresse du corpus portait la témoin pour la misere,
        # Veronique pour la veranda et Rene pour le froid -- sous la seule signature de
        # Rene. Le généalogiste : « tu melanges les sources, il y en a trois ». Le champ
        # `sources_complementaires` existait depuis longtemps et n'etait ni valide ni rendu.
        # ⚠️ `SRC` n'existe pas encore ici — il est construit plus bas ; on filtre donc sur
        # `sources`, la table brute chargee en tete de fichier.
        "srcs": [s for s in (e.get("sources_complementaires") or []) if s in sources] or None,
        "conf": e.get("confidence"),
        "sens": e.get("sensitivity"),
        "note": e.get("note"),
        "disp": bool(e.get("disputed_by")),
        "who": [{"id": q["person"], "r": q["role"]} for q in parts if q["person"] in P],
    })

# Les naissances / mariages / deces deviennent des evenements a l'affichage --
# SAUF quand un evenement raconte du meme type couvre deja la meme personne la meme
# annee : sinon la témoin voit sa propre naissance deux fois de suite.
told = {(w["person"], e["type"], year(e.get("date")))
        for e in events for w in e.get("participants", [])
        if w["role"] in ("subject", "spouse")}


def already(pid, kind, y):
    return (pid, kind, y) in told


for pid, p in P.items():
    if p["by"] and not already(pid, "birth", p["by"]):
        # Les parents sont participants de la naissance de leur enfant : sans ça, la trame
        # d'un pere ou d'une mere ne dit rien de la naissance de ses enfants, alors que
        # c'est un evenement de leur vie a eux aussi.
        qui = [{"id": pid, "r": "subject"}]
        qui += [{"id": x, "r": "parent"} for x in p.get("parents", []) if x in P]
        E.append({"id": f"b-{pid}", "t": "birth", "y": p["by"], "d": p["b"], "time": p.get("bt"),
                  "p": p["bp"], "pid": p["bpid"], "txt": f"Naissance de {p['n']}" + (f", à {p['bp']}" if p["bp"] else "") + ".",
                  "conf": p["conf"], "src": p.get("bsrc"), "who": qui, "vital": True})
    if p["dy"] and not already(pid, "death", p["dy"]):
        E.append({"id": f"d-{pid}", "t": "death", "y": p["dy"], "d": p["d"], "p": p["dp"], "pid": p["dpid"],
                  "txt": f"Mort de {p['n']}" + (f", à {p['dp']}" if p["dp"] else "") + ".",
                  "conf": p["conf"], "src": p.get("dsrc"), "who": [{"id": pid, "r": "subject"}], "vital": True})
    for m in p.get("mar", []):
        if m["y"] and pid < (m["with"] or "") and not already(pid, "marriage", m["y"]):
            E.append({"id": f"m-{pid}", "t": "marriage", "y": m["y"], "d": m["d"], "p": m["p"], "pid": m.get("pid"),
                      "txt": f"Mariage de {p['n']} et {P[m['with']]['n']}" + (f", à {m['p']}" if m["p"] else "") + ".",
                      "conf": "high", "src": m.get("src"), "vital": True,
                      "who": [{"id": pid, "r": "subject"}, {"id": m["with"], "r": "spouse"}]})

def when(e):
    """Tri chronologique fin.

    TROIS ETAGES, ET C'EST LA CONNAISSANCE QUI DECIDE, PAS LA PRECISION SEULE.

    L'ancienne regle -- a annee egale, du plus precis au plus vague -- avait raison
    contre un tri ISO naif : << vers 1942 >> se comparait a << 1942-00-00 >> et passait
    avant le 3 novembre. Mais elle rangeait aussi le MARIAGE du 9 mai 1938 devant la
    rencontre, la cour a l'epicerie et la photographie d'avril qui le precedent tous
    trois. Vu par le généalogiste sur sa page le 10 septembre 2026.

    Renverser le tri sur la borne basse a ete essaye et MESURE sur les 353 trames du
    corpus : 13 trames bougeaient, 49 couples s'inversaient, et une bonne moitie
    devenait FAUSSE -- le certificat d'etudes d'Alfiero passait avant son arrivee en
    France, la declaration de guerre avant une naissance de 1939, l'ete 1964 avant une naissance de la meme annee. Abandonne.

    CE QUI MARCHE : distinguer ce qu'on SAIT de ce qu'on ignore.

      1. LES MOMENTS SITUES -- un point date au jour, ou une PERIODE BORNEE qui tient
         dans son annee -- se classent entre eux par ordre chronologique, la periode sur
         son premier jour. La marche vers Marrakech du 6 au 23 janvier 1956 passe donc
         avant le rembarquement du 28, et la rencontre de 1938 bornee au 9 mai passe
         avant le mariage de ce jour-la.
      2. LES MOMENTS FLOUS -- << vers 1938 >>, << 1964 >> tout court -- viennent APRES
         eux dans l'annee, parce qu'ils peuvent tomber n'importe quand.
      3. LES CADRES PLURIANNUELS viennent en dernier : ils englobent ce qui precede
         (<< 1939-1947 : toute la guerre en demenagements >>).

    CONSEQUENCE POUR LE CORPUS, ET C'EST LA BONNE : pour placer un moment approximatif
    a sa vraie place, on ne triche pas sur sa date -- ON LUI DONNE SES BORNES. Ecrire
    { kind: range, from: 1938-01, to: 1938-05-09 } n'est pas une precision inventee,
    c'est une connaissance : on sait qu'ils se sont rencontres avant de se marier.
    """
    src = next((x for x in events if x["id"] == e["id"]), None)
    dv = (src or {}).get("date") or {}
    iso = dv.get("iso") or dv.get("from") or (str(e["y"]) if e["y"] else "")
    kind = dv.get("kind")
    borne = kind == "range" and dv.get("to") and year(dv) == year({"iso": dv["to"]})
    if kind == "range" and dv.get("to") and not borne:
        etage = 2                                    # cadre pluriannuel
    elif borne or (kind not in ("about", "before", "after") and len(iso) == 10):
        etage = 0                                    # situe
    else:
        etage = 1                                    # flou
    # A l'interieur d'un etage : la date, completee en jour pour comparer des chaines.
    pos = (iso + "-01-01")[:10] if len(iso) == 4 else (
        (iso + "-01")[:10] if len(iso) == 7 else iso)
    precision = {10: 0, 7: 1}.get(len(iso), 2)
    return (e["y"] or 9999, etage, pos, precision, e["id"])


E.sort(key=when)

# `short` est le libelle affiche sous un verbatim : il dit d'ou vient la citation.
# Sans lui la page retombait sur un defaut ecrit en dur, « d'apres la famille »,
# qui transformait un document d'archive en souvenir de famille.
SRC = {k: {"t": v["type"], "title": v.get("title", ""), "s": v.get("short", ""),
           # `support` = le libelle SANS le locuteur, pour les citations ou la
           # voix n'est pas celle qu'on attend. Absent = le libelle suffit.
           "sup": v.get("support", "")}
       for k, v in sources.items()}

# Les lieux voyagent avec leur article et leurs coordonnees : la page peut donc
# lier un nom de commune sans rien demander au reseau, et une carte devient
# possible sans dependance exterieure.
#
# UN LIEU-DIT EMPRUNTE LE LIEN DE SA COMMUNE, ET C'EST TOUT CE QU'ON PEUT FAIRE POUR LUI.
# « Le Radoire », « La Grollerie », « Le Jardinet » : quelques maisons chacun, aucun
# n'aura jamais d'article. Jusqu'au 26 aout 2026 au soir ils s'affichaient donc SANS
# AUCUN LIEN, alors que le libelle rendu par lieu() porte deja leur commune -- « Le
# Radoire (Lublé, Indre-et-Loire) » -- et que Lublé, elle, a son article et le montre
# sur toutes les autres fiches. Vingt-sept lieux-dits etaient dans ce cas. Le lien du
# lieu-dit mene donc a sa commune : c'est elle qui situe le lecteur, et c'est
# exactement ce qu'il cherche en cliquant.
#
# LES COORDONNEES, ELLES, NE S'HERITENT PAS. Un lieu-dit est a un ou deux kilometres du
# clocher : lui preter le point de la commune ferait passer une approximation pour une
# mesure sur la future vue Carte. Le lien situe, la coordonnee pretend -- on ne fait que
# le premier.
_par_nom = {v["name"]: v for v in places.values() if not v.get("commune")}


def _article(v):
    if v.get("wikipedia"):
        return v["wikipedia"]
    mere = _par_nom.get(v.get("commune") or "")
    return mere.get("wikipedia") if mere else None


LIEUX = {k: {"n": lieu(k), "w": _article(v), "c": v.get("coords")}
         for k, v in places.items()}

bundle = {"persons": P, "events": E, "sources": SRC, "lieux": LIEUX,
          "stats": {"persons": len(P), "events": len(E),
                    "narrative": len([e for e in E if not e.get("vital")]),
                    "places": len(places), "sources": len(sources)}}

# portraits encodes en base64 par build_media.py (la page publiee ne lit aucun fichier)
mfile = _MEDIA   # resolu et verifie en tete du fichier
if os.path.exists(mfile):
    M = json.load(io.open(mfile, encoding="utf-8"))
    for pid, m in M.get("portraits", {}).items():
        if pid in P:
            P[pid]["photo"] = m["img"]
            P[pid]["photo_src"] = m["src"]
    PHOTOS_EV = M.get("evenements", {})
    for e in E:
        if e["id"] in PHOTOS_EV:
            e["ph"] = PHOTOS_EV[e["id"]]
    print("  portraits :", sum(1 for p in P.values() if p.get("photo")),
          "| evenements illustres :", sum(1 for e in E if e.get("ph")))

js = "const DATA = " + json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + ";"

tpl = io.open(os.path.join(ROOT, "poc", "template.html"), encoding="utf-8").read()
assert "/*DATA*/" in tpl, "placeholder /*DATA*/ absent du template"
page = tpl.replace("/*DATA*/", js)

# Le titre vit dans le template, qui ne sert qu'un corpus a la fois. GENEALOGIA_TITRE
# le remplace pour un second corpus — c'est le nom de l'onglet et de la galerie.
# LE BANDEAU ET LE PIED DE PAGE SONT ECRITS EN DUR DANS LE TEMPLATE, ET ILS NOMMAIENT
# LA FAMILLE PAIRE SUR LA PAGE DES DUPONT. Le 4 septembre 2026, le second corpus
# affichait « Pairé · Le Pipe · Bariteau · Pediroda » et « De Valvasone en Frioul aux
# marais de Marennes » AU-DESSUS DE CHIFFRES QUI, EUX, ETAIENT LES BONS — 30 personnes,
# 17 moments, 20 lieux. Les donnees suivaient le corpus, le texte non, et rien ne le
# signalait : c'est exactement le genre d'erreur qu'un chiffre juste rend credible.
#
# Un corpus fournit desormais son propre bandeau dans le `_meta` de persons.json, sous
# la cle `entete` : familles, titre, chapeau, plus_ancien, provenance. SANS ELLE, LE
# TEMPLATE GARDE LE SIEN — la page de la famille PAIRE est inchangee.
_ent = (_persons_doc.get("_meta") or {}).get("entete") or {}
if _ent:
    _REMPL = [
        ("familles",    r'<div class="eyebrow">.*?</div>', '<div class="eyebrow">%s</div>'),
        ("titre",       r"<h1>.*?</h1>",                   "<h1>%s</h1>"),
        ("chapeau",     r'<p class="lede">.*?</p>',        '<p class="lede">%s</p>'),
        ("plus_ancien", r"<div><b>1600</b>le plus ancien</div>",
                        "<div><b>%s</b>le plus ancien</div>"),
        ("provenance",  r"<p>Recueilli auprès de.*?</p>", "<p>%s</p>"),
        # Les deux identifiants par defaut du template : la personne affichee a
        # l'ouverture, et la racine depuis laquelle les parentes sont exprimees.
        ("personne",    r'_existe\("exemple-personne"\)', '_existe("%s")'),
        ("racine",      r'_existe\("exemple-racine"\)', '_existe("%s")'),
    ]
    for cle, motif, forme in _REMPL:
        if not _ent.get(cle):
            continue
        page, n = re.subn(motif, lambda _m, f=forme, v=_ent[cle]: f % v, page, count=1,
                          flags=re.S)
        assert n == 1, f"bandeau : « {cle} » introuvable dans le template"

# UNE PAGE PAR DESTINATAIRE, PARCE QUE L'URL NE PASSE PAS. Mesure du 8 septembre 2026 :
# claude.ai fabrique lui-meme l'adresse du cadre ou la page s'execute --
# `https://<uuid>.frame.claudeusercontent.com/_f/<version>/?__frame_t=...&__frame_v=...` --
# et N'Y TRANSMET RIEN de la barre d'adresse. Un `?qui=exemple-cousine` colle sur l'URL de
# l'artefact n'atteint jamais le JavaScript : `location.search` ne porte que les deux
# jetons du cadre. Le hash non plus. Verifie par une sonde publiee expres, qui affichait
# sa propre adresse.
#
# LA VOIE QUI RESTE EST DONC DE CUIRE LA PERSONNE DANS LA PAGE, au lieu de l'attendre du
# lien -- ce que `_meta.entete` fait deja pour un corpus entier. Ces deux variables font
# la meme chose pour un tirage : on genere une page par personne a qui on l'envoie, et
# chacune est un artefact avec sa propre URL.
#
#   GENEALOGIA_QUI=exemple-cousine GENEALOGIA_DEPUIS=exemple-cousine \
#   GENEALOGIA_OUT=poc/cousine.html python scripts/build_poc.py
#
# Elles l'emportent sur `_meta.entete`, qui l'emporte sur les valeurs du template.
_qui = os.environ.get("GENEALOGIA_QUI")
if _qui:
    page, n = re.subn(r'_existe\("[^"]*"\) \|\| RACINE_PARDEFAUT',
                      '_existe("%s") || RACINE_PARDEFAUT' % _qui, page, count=1)
    assert n == 1, "GENEALOGIA_QUI : la personne par defaut est introuvable dans le template"
_depuis = os.environ.get("GENEALOGIA_DEPUIS")
if _depuis:
    page, n = re.subn(r'(const RACINE_PARDEFAUT = )_existe\("[^"]*"\)',
                      lambda m, v=_depuis: m.group(1) + '_existe("%s")' % v, page, count=1)
    assert n == 1, "GENEALOGIA_DEPUIS : la racine par defaut est introuvable dans le template"

titre = os.environ.get("GENEALOGIA_TITRE")
if titre:
    page, n = re.subn(r"<title>.*?</title>", "<title>" + titre + "</title>", page, count=1,
                      flags=re.S)
    assert n == 1, "balise <title> introuvable dans le template"

out = _OUT   # resolu et verifie en tete du fichier
with io.open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(page)
print(f"{out}  —  {os.path.getsize(out) // 1024} Ko")
print("  ", bundle["stats"])
