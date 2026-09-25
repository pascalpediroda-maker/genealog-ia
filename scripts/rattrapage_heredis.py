# -*- coding: utf-8 -*-
"""Rattrape ce que `import_heredis.py` avait laisse tomber de la base d'Alfiero.

TROIS PERTES, TROUVEES LE 27 AOUT 2026 en comparant la base au corpus :

1. LE SEXE, ET C'EST UN BUG FRANC. Heredis encode `Individus.Sexe` en 109 et 102 --
   les codes ASCII de « m » et « f ». L'import testait `sexe == 1` / `sexe == 2` :
   AUCUN sexe n'a jamais ete importe, les 811 individus sont tombes en « U ».
   Consequence silencieuse : `build.py` ne controle l'age des meres que si le sexe
   vaut « F », donc il etait aveugle sur toutes les personnes venues d'Heredis.

2. LES MARIAGES. Les types d'evenement 61 et 68 portent 150 mariages, dates et lieux
   compris, attaches aux UNIONS et non aux individus. L'import ne lisait que les types
   4 (naissance) et 12 (deces) : les 150 sont restes dehors, et des unions du corpus
   portaient `marriage: null` alors que la base avait la date.

3. LE CHAINON MANQUANT. Le corpus ne gardait aucun lien vers la base : impossible de
   savoir quelle fiche venait de quel `CodeID`. Ce script ecrit `heredis_cid`, pour que
   la question ne se repose plus.

Usage :
    python scripts/rattrapage_heredis.py            # rapport, n'ecrit rien
    python scripts/rattrapage_heredis.py --write    # applique
"""
import sqlite3, json, io, os, re, sys, unicodedata, collections

import os as _os
import config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
HRD = _os.path.join(config.archives(), "le généalogiste.hmw", "le généalogiste.heredis")
SRC = "src-heredis-alfiero"
EV_MARIAGE = (61, 68)

MOIS = {"JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
        "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"}


def date_value(g):
    """« 11 JUL 1938 » -> {'kind': 'exact', 'iso': '1938-07-11'}"""
    if not g:
        return None
    g = g.strip().upper()
    kind = "exact"
    for p, k in (("ABT ", "about"), ("BEF ", "before"), ("AFT ", "after")):
        if g.startswith(p):
            kind, g = k, g[len(p):]
    m = re.match(r"^(\d{1,2}) ([A-Z]{3}) (\d{4})$", g)
    if m:
        return {"kind": kind, "iso": "%s-%s-%02d" % (m.group(3), MOIS[m.group(2)], int(m.group(1)))}
    m = re.match(r"^([A-Z]{3}) (\d{4})$", g)
    if m:
        return {"kind": kind, "iso": "%s-%s" % (m.group(2), MOIS[m.group(1)])}
    m = re.match(r"^(\d{4})$", g)
    if m:
        return {"kind": "year" if kind == "exact" else kind, "iso": m.group(1)}
    return None


def nrm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z]", "", s)


def charge(n):
    return json.load(io.open(os.path.join(DATA, n), encoding="utf-8"))


def ecris(n, o):
    json.dump(o, io.open(os.path.join(DATA, n), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=2)
    print("  ecrit", n)


# ------------------------------------------------------------------ lecture Heredis
con = sqlite3.connect("file:%s?mode=ro" % HRD, uri=True)
con.text_factory = lambda b: b.decode("utf-8", "replace")
q = con.cursor()

ind = {}
for cid, nom, pre, sexe, prof in q.execute(
        "SELECT i.CodeID, n.Nom, i.Prenoms, i.Sexe, i.Profession "
        "FROM Individus i LEFT JOIN Noms n ON n.CodeID = i.CodeNom"):
    ind[cid] = {"nom": (nom or "").strip(), "pre": (pre or "").strip(),
                # 109 = ord('m'), 102 = ord('f') -- LE BUG ETAIT ICI
                "sexe": "M" if sexe == 109 else ("F" if sexe == 102 else "U"),
                "prof": (prof or "").strip()}

naissance = {}
for cid, dg in q.execute("SELECT CodeProprietaire, DateGed FROM Evenements WHERE EventType = 4"):
    if cid in ind:
        d = date_value(dg)
        naissance[cid] = d["iso"] if d else None

unions_hrd = {}
cols = [c[1] for c in q.execute("PRAGMA table_info(Unions)")]
for r in q.execute("SELECT * FROM Unions"):
    d = dict(zip(cols, r))
    unions_hrd[d["CodeID"]] = (d["Epoux"], d["Epouse"])

mariages = {}
for cu, dg, ville, pays in q.execute(
        "SELECT e.CodeProprietaire, e.DateGed, l.Ville, l.Pays FROM Evenements e "
        "LEFT JOIN Lieux l ON l.CodeID = e.CodeLieu WHERE e.EventType IN (%s)"
        % ",".join(str(t) for t in EV_MARIAGE)):
    if cu not in unions_hrd:
        continue
    d = date_value(dg)
    if not d and not ville:
        continue
    # on garde la plus precise si deux lignes pour la meme union
    old = mariages.get(cu)
    if old and old[0] and not d:
        continue
    mariages[cu] = (d, ville, pays)
con.close()

# ------------------------------------------------------------------ appariement
persons = charge("persons.json")
idx = collections.defaultdict(list)
for cid, v in ind.items():
    prenom = v["pre"].split(",")[0].split()[0] if v["pre"] else ""
    idx[(nrm(v["nom"]), nrm(prenom), naissance.get(cid))].append(cid)

cid_of, ambigus, sans = {}, [], 0
for p in persons["persons"]:
    b = ((p.get("birth") or {}).get("date") or {}).get("iso")
    prenom = (p.get("given") or "").split()[0] if p.get("given") else ""
    c = idx.get((nrm(p.get("surname")), nrm(prenom), b), [])
    if len(c) == 1:
        cid_of[p["id"]] = c[0]
    elif len(c) > 1:
        ambigus.append((p["id"], c))
    else:
        sans += 1

print("APPARIEMENT corpus <-> Heredis")
print("  %d surs, %d ambigus, %d sans correspondance (sur %d fiches)"
      % (len(cid_of), len(ambigus), sans, len(persons["persons"])))
for pid, c in ambigus:
    print("    ambigu : %-28s -> %s" % (pid, c))

# ------------------------------------------------------------------ 1. le sexe
sexes = [(p["id"], ind[cid_of[p["id"]]]["sexe"]) for p in persons["persons"]
         if p["id"] in cid_of and p.get("sex") in (None, "U")
         and ind[cid_of[p["id"]]]["sexe"] != "U"]
print("\n1. SEXE : %d fiches a corriger (le bug 109/102 contre 1/2)" % len(sexes))

# ------------------------------------------------------------------ 2. professions
profs = [(p["id"], ind[cid_of[p["id"]]]["prof"]) for p in persons["persons"]
         if p["id"] in cid_of and ind[cid_of[p["id"]]]["prof"]
         and not p.get("occupations")]
print("2. METIERS : %d fiches sans occupation alors que la base en donne une" % len(profs))
for pid, pr in profs[:8]:
    print("     %-28s %s" % (pid, pr))

# ------------------------------------------------------------------ 3. mariages
p2c = cid_of
c2p = {v: k for k, v in cid_of.items()}
unions = charge("unions.json")
par_couple = {}
for u in unions["unions"]:
    k = frozenset(x for x in (u.get("partners") or []) if x)
    if k:
        par_couple[k] = u

a_remplir = []
for cu, (a, b) in unions_hrd.items():
    if cu not in mariages:
        continue
    pa, pb = c2p.get(a), c2p.get(b)
    if not (pa and pb):
        continue
    u = par_couple.get(frozenset([pa, pb]))
    if u and not u.get("marriage"):
        a_remplir.append((u, mariages[cu]))
print("3. MARIAGES : %d unions du corpus sont vides alors que la base a la date" % len(a_remplir))
for u, (d, v, pays) in a_remplir:
    print("     %-42s %-11s %s" % (u["id"], (d or {}).get("iso"), v or "-"))

# ------------------------------------------------------------------ ecriture
if "--write" not in sys.argv:
    print("\n(--write pour appliquer)")
    sys.exit(0)

persons = charge("persons.json")          # rechargement juste avant d'ecrire
by_id = {p["id"]: p for p in persons["persons"]}
n_sex = n_cid = n_prof = 0
for pid, cid in cid_of.items():
    p = by_id.get(pid)
    if not p:
        continue
    if p.get("heredis_cid") != cid:
        p["heredis_cid"] = cid
        n_cid += 1
for pid, s in sexes:
    if pid in by_id and by_id[pid].get("sex") in (None, "U"):
        by_id[pid]["sex"] = s
        n_sex += 1
for pid, pr in profs:
    p = by_id.get(pid)
    if p and not p.get("occupations"):
        p["occupations"] = [{"value": pr[:1].upper() + pr[1:], "confidence": "medium",
                             "source": SRC,
                             "note": "Metier porte par la base genealogique d'Alfiero PEDIRODA, "
                                     "recupere le 27 aout 2026 : le premier import l'avait laisse."}]
        n_prof += 1
ecris("persons.json", persons)
print("  sexes corriges : %d | heredis_cid poses : %d | metiers ajoutes : %d" % (n_sex, n_cid, n_prof))

unions = charge("unions.json")
by_uid = {u["id"]: u for u in unions["unions"]}
n_mar = 0
for u, (d, ville, pays) in a_remplir:
    cible = by_uid.get(u["id"])
    if not cible or cible.get("marriage"):
        continue
    m = {"date": d or {"kind": "unknown"}, "confidence": "medium", "source": SRC}
    if ville:
        m["place_raw"] = ville + ((" (%s)" % pays) if pays else "")
    cible["marriage"] = m
    cible.setdefault("notes", []).append(
        "DATE DE MARIAGE RECUPEREE LE 27 AOUT 2026 dans la base d'Alfiero, ou elle etait "
        "depuis toujours : le premier import ne lisait que les naissances et les deces, et "
        "laissait dehors les 150 mariages que la base porte sur ses unions. "
        "`place_raw` attend d'etre normalise vers places.json.")
    n_mar += 1
ecris("unions.json", unions)
print("  mariages remplis : %d" % n_mar)
