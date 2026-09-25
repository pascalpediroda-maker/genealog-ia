"""
Importe la lignee directe d'Alfiero depuis la base Heredis de son pere.

  python scripts/import_heredis.py            -> rapport, n'ecrit rien
  python scripts/import_heredis.py --write    -> applique dans data/

Deux principes :
  1. La base Heredis est une SOURCE PARMI D'AUTRES. Elle ne remplace jamais une valeur
     deja etablie par l'etat civil : elle complete les trous et se met en `_disputed`
     quand elle contredit.
  2. On n'importe PAS les 811 personnes. Seulement la lignee directe d'Alfiero, ses
     fratries et ses conjoints : le reste noierait les 111 personnes deja travaillees.
"""
import sqlite3, json, io, os, re, sys, unicodedata

import os as _os
import config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# LA BASE A DEMENAGE LE 27 AOUT 2026 : elle etait sur S:, avec les photos de
# famille ; le généalogiste l'a regroupee sur X: avec les archives. Les photos de famille,
# elles, RESTENT sur S: rangees par date -- ce sont deux fonds differents.
HRD = _os.path.join(config.archives(), "le généalogiste.hmw", "le généalogiste.heredis")
MEDIA = _os.path.join(config.archives(), "le généalogiste.hmw", "Media")
ALFIERO = 20                    # CodeID d'Alfiero Pietro dans la base Heredis
GEN_MAX = 12                    # profondeur d'ascendance
EV_NAISS, EV_DECES = 4, 12

MOIS = {"JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
        "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"}


def parse_date(g):
    """« 11 JUL 1938 » / « SEP 1911 » / « ABT 1600 » -> date_value du modele."""
    if not g:
        return None
    g = g.strip().upper()
    kind = "exact"
    if g.startswith("ABT "): kind, g = "about", g[4:]
    elif g.startswith("BEF "): kind, g = "before", g[4:]
    elif g.startswith("AFT "): kind, g = "after", g[4:]
    m = re.match(r"^(\d{1,2}) ([A-Z]{3}) (\d{4})$", g)
    if m:
        return {"kind": kind, "iso": f"{m.group(3)}-{MOIS[m.group(2)]}-{int(m.group(1)):02d}"}
    m = re.match(r"^([A-Z]{3}) (\d{4})$", g)
    if m:
        return {"kind": "exact" if kind == "exact" else kind, "iso": f"{m.group(2)}-{MOIS[m.group(1)]}"}
    m = re.match(r"^(\d{4})$", g)
    if m:
        return {"kind": "year" if kind == "exact" else kind, "iso": m.group(1)}
    return {"kind": "about", "iso": g, "note": "date non normalisee a l'import"}


def slug(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# L'import posait `living: False` POUR TOUT LE MONDE, et ce n'etait pas anodin : la
# page ecrit « mort — on ne sait ni quand ni ou » des qu'une fiche est dite non vivante
# sans date de deces. Tant que le perimetre s'arretait aux ascendants d'Alfiero, tous
# morts, ca ne se voyait pas. Il suffit d'ouvrir aux cousins pour que ca publie ALIDA
# MIROLO, nee en 1946, VIVANTE, et a qui le généalogiste ecrit, comme morte a une date inconnue.
#
# Heredis ne porte aucun drapeau « vivant ». On deduit donc, et on le fait dans le sens
# prudent : PAS D'ACTE DE DECES ET NE DEPUIS MOINS DE 105 ANS -> vivant. Une naissance
# inconnue ne permet rien, et vaut « mort » : ces fiches-la sont toutes anciennes.
ANNEE_COURANTE = 2026
AGE_LIMITE = 105


def vivant(vit):
    if "d" in vit:
        return False
    m = re.search(r"(\d{4})", (vit.get("b") or ("",))[0] or "")
    return bool(m) and ANNEE_COURANTE - int(m.group(1)) < AGE_LIMITE


con = sqlite3.connect(f"file:{HRD}?mode=ro", uri=True)
con.text_factory = lambda b: b.decode("utf-8", "replace")
q = con.cursor()

# ---------------------------------------------------------------- lecture
indi = {}
for cid, nom, pre, sexe, pere, mere, prof in q.execute("""
        SELECT i.CodeID, n.Nom, i.Prenoms, i.Sexe, i.CodePere, i.CodeMere, i.Profession
        FROM Individus i LEFT JOIN Noms n ON n.CodeID = i.CodeNom"""):
    indi[cid] = {"cid": cid, "nom": (nom or "").strip(), "pre": (pre or "").strip(),
                 # HEREDIS ENCODE LE SEXE EN 109 ET 102 -- les codes ASCII de « m » et
                 # « f », pas 1 et 2. Le test `sexe == 1` a fait tomber les 811 fiches
                 # en « U » a l'import du 11 aout, et le silence coutait : `build.py`
                 # ne controle l'age des meres que si le sexe vaut « F », il etait donc
                 # aveugle sur toute la branche italienne. `rattrapage_heredis.py` a
                 # repare le CORPUS le 27 aout ; la faute est restee ICI, a la source,
                 # jusqu'au soir du meme jour -- reimporter la reintroduisait.
                 "sexe": {109: "M", 102: "F", 1: "M", 2: "F"}.get(sexe, "U"),
                 "pere": pere or None, "mere": mere or None, "prof": (prof or "").strip()}

vitaux = {}
for cid, t, dg, ville, pays in q.execute("""
        SELECT e.CodeProprietaire, e.EventType, e.DateGed, l.Ville, l.Pays
        FROM Evenements e LEFT JOIN Lieux l ON l.CodeID = e.CodeLieu
        WHERE e.EventType IN (?, ?)""", (EV_NAISS, EV_DECES)):
    vitaux.setdefault(cid, {})["b" if t == EV_NAISS else "d"] = (dg, ville, pays)

# Les notes ne sont PAS attachees aux personnes mais aux EVENEMENTS : il faut deux
# jointures pour remonter a l'individu. Une lecture naive de Notes.CodeProprietaire
# donne zero correspondance — le schema d'Heredis n'est documente nulle part, et c'est
# exactement pourquoi un export GEDCOM reste preferable quand il est possible.
# Qui est marie avec qui : il faut ce couplage pour router vers les DEUX epoux ce
# qu'Heredis accroche a l'union — notes de mariage et photos de noces.
epoux_de = {}
for u, ep, ee in q.execute("SELECT CodeID, Epoux, Epouse FROM Unions"):
    epoux_de[u] = [x for x in (ep, ee) if x]

# LE NOM DE L'EVENEMENT, pour que la note dise de quoi elle parle.
NOM_EV = {2: "baptême", 4: "naissance", 5: "baptême", 6: "profession", 8: "recensement",
          10: "confirmation", 12: "décès", 13: "inhumation", 17: "testament",
          23: "émigration", 30: "résidence", 61: "mariage", 68: "mariage religieux",
          69: "contrat de mariage", 70: "divorce", 74: "résidence"}

# ALFIERO ECRIVAIT BEAUCOUP, ET L'IMPORT N'EN LISAIT QUE LES TROIS QUARTS. Il ne
# retenait que les notes portees par une naissance ou un deces — les types 4 et 12 —
# alors qu'elles s'accrochent a n'importe quel evenement. Douze notes restaient dehors,
# dont DIX SUR DES MARIAGES : celles-la ne sont meme pas ratables autrement, parce
# qu'un evenement de mariage appartient a l'UNION et non a une personne, si bien que
# `notes[CodeProprietaire]` cherchait un individu sous un identifiant d'union.
# (Verifie le 27 aout : les deux espaces d'identifiants ne se recouvrent pas dans cette
# base — aucune note n'a donc atterri chez un inconnu. Rien ne garantissait qu'ils ne
# se recouvrent jamais : c'etait un coup de chance, pas une propriete du format.)
notes, notes_vues = {}, 0
for cid, typ, txt in q.execute("""
        SELECT e.CodeProprietaire, e.EventType, n.Note
        FROM Notes n JOIN Evenements e ON e.CodeID = n.CodeProprietaire
        WHERE n.Note <> ''"""):
    if not cid:
        continue
    notes_vues += 1
    quoi = NOM_EV.get(typ, "")
    t = " ".join(txt.split())
    marque = f"[note d'Alfiero, {quoi}] {t}" if quoi else f"[note d'Alfiero] {t}"
    for dest in (epoux_de.get(cid) or [cid]):        # union -> les deux epoux
        notes.setdefault(dest, []).append(marque)

# Six medias sont accroches a une UNION et non a une personne : des photos de noces.
# L'import ne regardait que les individus, elles n'entraient pas.
photos, media_absents = {}, []
for cid, mid, fn, principal in q.execute("""
        SELECT lm.XrefProprietaire, m.CodeID, m.FileName, lm.MediaPrincipal
        FROM LiensMedias lm JOIN Medias m ON m.CodeID = lm.XrefMedia"""):
    p = f"{MEDIA}/#{mid}/{fn}"
    if not os.path.exists(p):
        # LE SILENCE EST LA FAUTE QU'ON A DEJA PAYEE SUR build_media.py, quand 121
        # medias sur 241 ont ete ecartes sans un mot un soir d'orage. On les compte.
        media_absents.append(f"#{mid}/{fn}")
        continue
    for dest in (epoux_de.get(cid) or [cid]):
        photos.setdefault(dest, []).append(
            {"file": p, "portrait": bool(principal) and cid not in epoux_de})
con.close()

# --------------------------------------------------- selection du perimetre
# Par defaut : LIGNEE DIRECTE d'Alfiero + les conjoints de cette lignee + la seule
# fratrie d'Alfiero. Les 811 personnes de la base noieraient les 111 deja travaillees.
# --large ouvre a toutes les fratries de la lignee (134 personnes, dont une branche
# argentine et des MIGOT partis en Siberie).
LARGE = "--large" in sys.argv
COUSINS = "--cousins" in sys.argv

ligne_directe, file = set(), [(ALFIERO, 0)]
while file:
    cid, gen = file.pop()
    if cid in ligne_directe or cid not in indi or gen > GEN_MAX:
        continue
    ligne_directe.add(cid)
    for p in (indi[cid]["pere"], indi[cid]["mere"]):
        if p:
            file.append((p, gen + 1))

enfants_de = {}
for cid, v in indi.items():
    for p in (v["pere"], v["mere"]):
        if p:
            enfants_de.setdefault(p, set()).add(cid)

garder = set(ligne_directe)
if COUSINS:
    # UNE MARCHE DE PLUS QUE `--large`, ET C'EST CELLE OU VIVENT LES TEMOINS.
    # `--large` prend les fratries de la lignee — donc les freres et soeurs d'Antonio
    # Pietro — mais s'arrete la. Il laisse dehors LEURS ENFANTS, c'est-a-dire les
    # cousins germains d'Alfiero : une cousine, qui a raconte cette branche au
    # telephone le 27 aout 2026, ses freres Arturo et Giuseppe, sa soeur Renata, les
    # CONCAS de Leda, Mafalda GUZZONI — et Lino PEDIRODA, deja au corpus, qu'aucun
    # perimetre ne rattachait a son cousin.
    for cid in list(ligne_directe):
        garder |= enfants_de.get(cid, set())
    for cid in list(garder):
        garder |= enfants_de.get(cid, set())
elif LARGE:
    for cid in list(ligne_directe):
        garder |= enfants_de.get(cid, set())
else:
    pere = indi[ALFIERO]["pere"]
    if pere:
        garder |= enfants_de.get(pere, set())      # freres et soeurs d'Alfiero
# CONJOINTS : LES DEUX PARENTS D'UN ENFANT RETENU, ET NON PAS « SI L'AUTRE EST DEJA LA ».
# L'ancienne condition — `p in garder or e in ligne_directe` — laissait dehors le conjoint
# d'un collateral, donc des couples entiers arrivaient a moitie. C'est ce qui manquait
# AFRO GUZZONI, le mari de Giuseppina AVOLEDO : ses quatre enfants etaient au corpus,
# lui non, et « Casa Afro » est justement la maison ou Alfiero descendait quand il
# revenait au pays (une cousine, 27 aout 2026). Une union a deux cotes ou elle n'est
# pas une union.
for cid in list(garder):
    for e in enfants_de.get(cid, set()):
        if e not in garder:
            continue
        for p in (indi[e]["pere"], indi[e]["mere"]):
            if p:
                garder.add(p)

# ------------------------------------------------------------ conversion
# LES IDENTIFIANTS DOIVENT ETRE UNIQUES DANS LE CORPUS, PAS SEULEMENT DANS L'IMPORT.
# La boucle ne regardait que `IDS.values()` — les fiches deja fabriquees par CET import —
# et pas `data/persons.json`. Le 27 aout 2026 au soir, l'ouverture aux cousins a donc
# fabrique trois identifiants qui existaient deja : `antonio-pediroda-2`, `gio-migot-2`,
# `pietro-migot-3`. `merge_heredis.py` les a ajoutes tels quels, et comme le corpus se
# relit partout en `{p["id"]: p for p in persons}`, LA DERNIERE FICHE MASQUE LA PREMIERE :
# Antonio PEDIRODA, ne en 1847, charpentier parti pour Buenos Aires, s'est retrouve
# ne en 1709 et mort en 1795, avec le prenom d'un autre. Rien n'etait perdu — les deux
# fiches etaient dans le fichier — mais la moitie du corpus lisait la mauvaise, et
# `build.py` n'a vu que les six contradictions de dates qui en decoulaient.
_corpus_ids = set()
_p = os.path.join(ROOT, "data", "persons.json")
if os.path.exists(_p):
    _corpus_ids = {x["id"] for x in json.load(io.open(_p, encoding="utf-8"))["persons"]}

IDS, out_p, out_u = {}, [], []
for cid in sorted(garder):
    v = indi[cid]
    base = slug(f"{v['pre'].split(',')[0].split()[0] if v['pre'] else 'inconnu'}-{v['nom']}")
    pris = set(IDS.values()) | _corpus_ids
    pid, k = base, 2
    while pid in pris:
        pid, k = f"{base}-{k}", k + 1
    IDS[cid] = pid

for cid in sorted(garder):
    v, vit = indi[cid], vitaux.get(cid, {})
    p = {"id": IDS[cid], "surname": v["nom"] or "?",
         "given": (v["pre"].split(",")[0].strip() if v["pre"] else None),
         "sex": v["sexe"], "living": vivant(vit), "in_tree_pdf": False,
         "sources": ["src-heredis-alfiero"]}
    full = v["pre"].replace(",", " ").split()
    if len(full) > 1:
        p["given_civil"] = " ".join(full)
    if v["prof"]:
        p["occupations"] = [{"value": v["prof"], "confidence": "medium", "source": "src-heredis-alfiero"}]
    for k, champ in (("b", "birth"), ("d", "death")):
        if k in vit:
            dg, ville, pays = vit[k]
            d = parse_date(dg)
            if d or ville:
                p[champ] = {"date": d or {"kind": "unknown"}, "confidence": "medium",
                            "source": "src-heredis-alfiero"}
                if ville:
                    p[champ]["place_raw"] = ville + (f" ({pays})" if pays else "")
    n = notes.get(cid)
    if n:
        p["notes"] = n
    ph = photos.get(cid)
    if ph:
        p["media"] = [{"type": "portrait" if x["portrait"] else "photo",
                       "source_file": x["file"]} for x in ph]
    out_p.append(p)

# unions reconstituees depuis les couples parentaux
couples = {}
for cid in garder:
    pe, me = indi[cid]["pere"], indi[cid]["mere"]
    if pe or me:
        couples.setdefault((pe, me), []).append(cid)
for (pe, me), enfs in couples.items():
    if pe not in IDS and me not in IDS:
        continue
    out_u.append({"id": "u-" + slug((IDS.get(pe) or "x") + "-" + (IDS.get(me) or "x")),
                  "partners": [IDS.get(pe), IDS.get(me)],
                  "marriage": None,
                  "children": [IDS[e] for e in sorted(enfs) if e in IDS],
                  "notes": ["Union reconstituee depuis la base Heredis d'Alfiero PEDIRODA."]})

# ------------------------------------------------------------- rapport
print(f"{len(garder)} personnes retenues sur {len(indi)} ({len(out_u)} unions)")
avec_notes = sum(1 for p in out_p if p.get("notes"))
avec_photo = sum(1 for p in out_p if p.get("media"))
print(f"  {avec_notes} avec des notes de ton pere, {avec_photo} avec au moins une photo")
n_notes = sum(len(p["notes"]) for p in out_p if p.get("notes"))
n_photos = sum(len(p["media"]) for p in out_p if p.get("media"))
print(f"  {n_notes} notes et {n_photos} images rattachees "
      f"(la base en porte {notes_vues} et {215 - len(media_absents)} lisibles)")
if media_absents:
    print(f"  !! {len(media_absents)} images citees par la base sont ABSENTES du disque — "
          f"elles ne sont pas importees : {', '.join(media_absents[:4])}…")
    print(f"     (le dossier attendu est {MEDIA}/#<id>/<fichier>)")
lieux = sorted({p[c]["place_raw"] for p in out_p for c in ("birth", "death")
                if p.get(c, {}).get("place_raw")})
print(f"  {len(lieux)} lieux a normaliser : {', '.join(lieux[:12])}…")
print("\nLignee directe :")
cur, gen = ALFIERO, 0
while cur and gen < GEN_MAX:
    v = indi[cur]; vit = vitaux.get(cur, {})
    b = parse_date(vit.get("b", (None,))[0])
    print("   " * gen + f"{v['pre']} {v['nom']}" + (f"  {b['iso']}" if b else ""))
    cur, gen = v["pere"], gen + 1

if "--write" in sys.argv:
    out = os.path.join(ROOT, "data", "import-heredis.json")
    json.dump({"_meta": {"source": "src-heredis-alfiero", "fichier": HRD,
                         "perimetre": "lignee directe d'Alfiero PEDIRODA, fratries et conjoints",
                         "a_faire": "normaliser place_raw vers places.json, puis fusionner"},
               "persons": out_p, "unions": out_u},
              io.open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
    print(f"\nEcrit : {out}")
else:
    print("\n(--write pour ecrire data/import-heredis.json)")
