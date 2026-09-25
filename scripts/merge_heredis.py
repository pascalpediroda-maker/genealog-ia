"""
Fusionne data/import-heredis.json dans le corpus.

  python scripts/merge_heredis.py           -> rapport
  python scripts/merge_heredis.py --write   -> applique

Regle de fusion : l'import ne REMPLACE jamais une valeur existante. Le corpus a ete
etabli sur des actes et des livrets de famille ; la base Heredis est une compilation.
Elle complete les trous, et se met en `_disputed` quand elle contredit.
"""
import json, io, os, sys, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
load = lambda n: json.load(io.open(os.path.join(D, n), encoding="utf-8"))
WRITE = "--write" in sys.argv

imp = load("import-heredis.json")
persons_doc, unions_doc, places_doc = load("persons.json"), load("unions.json"), load("places.json")
P = {p["id"]: p for p in persons_doc["persons"]}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def annee(p, champ):
    d = (p.get(champ) or {}).get("date") or {}
    m = re.match(r"^(\d{4})", d.get("iso") or "")
    return m.group(1) if m else None


# --- resolution d'identite : nom + prenom + annee de naissance --------------
index = {}
for pid, p in P.items():
    index.setdefault((norm(p["surname"]), norm((p.get("given") or "").split()[0] if p.get("given") else "")), []).append(pid)

apparies, nouveaux, conflits = [], [], []
for np in imp["persons"]:
    cle = (norm(np["surname"]), norm((np.get("given") or "").split()[0] if np.get("given") else ""))
    cands = index.get(cle, [])
    # un candidat n'est retenu que si les annees de naissance concordent (ou manquent)
    match = None
    for pid in cands:
        a, b = annee(P[pid], "birth"), annee(np, "birth")
        if a is None or b is None or a == b:
            match = pid
            break
    (apparies if match else nouveaux).append((np, match))

# --- lieux : place_raw -> identifiant normalise -----------------------------
have = {p["id"]: p for p in places_doc["places"]}
alias = {}
for pid, p in have.items():
    alias[norm(p["name"])] = pid
    for a in p.get("aliases", []):
        alias[norm(a)] = pid

nouveaux_lieux = {}
def lieu(raw):
    if not raw:
        return None, None
    ville = re.sub(r"\s*\(.*\)$", "", raw).strip()
    pays = (re.search(r"\((.*)\)$", raw) or [None, None])[1]
    k = norm(ville)
    if k in alias:
        return alias[k], None
    lid = re.sub(r"[^a-z0-9]+", "-", norm(ville)).strip("-") or None
    if lid and lid not in nouveaux_lieux:
        e = {"id": lid, "name": ville}
        if pays and norm(pays) != "france":
            e["country"] = pays.title()
        else:
            e["country"] = "France"
        e["note"] = "Importé de la base Hérédis d'Alfiero — à vérifier et compléter (département, code INSEE)."
        nouveaux_lieux[lid] = e
    return lid, ville


# --- application -----------------------------------------------------------
ajouts_notes = 0
for np, pid in apparies:
    cible = P[pid]
    for champ in ("birth", "death"):
        src = np.get(champ)
        if not src:
            continue
        lid, _ = lieu(src.pop("place_raw", None))
        if lid:
            src["place"] = lid
        if champ not in cible:
            cible[champ] = src
        else:
            a, b = annee(cible, champ), re.match(r"^(\d{4})", (src.get("date") or {}).get("iso") or "")
            if a and b and a != b.group(1):
                cible.setdefault(champ + "_disputed", []).append(
                    {**src, "note": "Version de la base Hérédis d'Alfiero, en conflit avec la valeur retenue."})
    for n in np.get("notes", []):
        if n not in cible.setdefault("notes", []):
            cible["notes"].append(n); ajouts_notes += 1
    if np.get("media"):
        cible.setdefault("media", []).extend(np["media"])
    if np.get("occupations") and not cible.get("occupations"):
        cible["occupations"] = np["occupations"]
    if "src-heredis-alfiero" not in cible.setdefault("sources", []):
        cible["sources"].append("src-heredis-alfiero")

# UN IDENTIFIANT DEJA PRIS N'EST PAS UN DETAIL, C'EST UNE FICHE QUI EN MASQUE UNE AUTRE.
# Le corpus se relit partout en `{p["id"]: p for p in persons}` : deux fiches de meme id
# et la seconde efface la premiere pour tout le monde, sans que rien ne le dise. C'est
# arrive le 27 aout 2026 sur trois homonymes. `import_heredis.py` garantit desormais
# l'unicite a la source ; ce garde-fou-ci existe pour le cas ou l'import viendrait
# d'ailleurs — un autre fichier, une version anterieure du script.
deja = {p["id"] for p in persons_doc["persons"]}
collisions = 0
for np, _ in nouveaux:
    if np["id"] in deja:
        base, k = np["id"], 2
        while f"{base}-{k}" in deja:
            k += 1
        ancien, np["id"] = np["id"], f"{base}-{k}"
        for u in imp["unions"]:
            u["partners"] = [np["id"] if x == ancien else x for x in u["partners"]]
            u["children"] = [np["id"] if x == ancien else x for x in u["children"]]
        collisions += 1
        print(f"   ! identifiant deja pris : {ancien} -> {np['id']}")
    deja.add(np["id"])
    for champ in ("birth", "death"):
        if np.get(champ):
            lid, _ = lieu(np[champ].pop("place_raw", None))
            if lid:
                np[champ]["place"] = lid
    persons_doc["persons"].append(np)

# unions : on ne garde que celles dont les deux cotes existent apres fusion
ids_apparies = {np["id"]: pid for np, pid in apparies}
def resol(x):
    return ids_apparies.get(x, x)

connus = {p["id"] for p in persons_doc["persons"]}
existantes = {u["id"] for u in unions_doc["unions"]}
par_paire = {}
for u in unions_doc["unions"]:
    par_paire.setdefault(tuple(sorted(x for x in u["partners"] if x)), u)
n_u, n_enf = 0, 0
for u in imp["unions"]:
    u["partners"] = [resol(x) if x else None for x in u["partners"]]
    u["children"] = [resol(x) for x in u["children"]]
    if not any(x in connus for x in u["partners"] if x):
        continue
    u["children"] = [c for c in u["children"] if c in connus]
    deja_la = par_paire.get(tuple(sorted(x for x in u["partners"] if x)))
    if deja_la is not None:
        # UN COUPLE DEJA CONNU N'EST PAS UNE UNION DEJA COMPLETE, et la nuance a
        # laisse quarante-cinq personnes sans famille le 27 aout 2026. La fusion
        # sautait l'union entiere des que la paire existait — donc les FRERES ET
        # SOEURS nouvellement importes n'etaient rattaches a rien : Lucia Teodora,
        # Ludovica Angela et Leda Anna PEDIRODA, les trois soeurs d'Antonio Pietro
        # dont Alida venait justement de donner l'ordre de naissance, entraient au
        # corpus avec une fiche que rien ne reliait a leurs parents. On verse donc
        # les enfants manquants dans l'union existante, sans toucher au reste.
        for c in u["children"]:
            if c not in deja_la.setdefault("children", []):
                deja_la["children"].append(c); n_enf += 1
        continue
    if u["id"] in existantes:
        u["id"] += "-hrd"
    unions_doc["unions"].append(u)
    par_paire[tuple(sorted(x for x in u["partners"] if x))] = u
    n_u += 1

places_doc["places"].extend(nouveaux_lieux.values())

print(f"{len(apparies)} personnes appariees, {len(nouveaux)} nouvelles")
for np, pid in apparies:
    print(f"   = {np.get('given')} {np['surname']}  ->  {pid}")
print(f"{ajouts_notes} notes d'Alfiero rattachees, {n_u} unions ajoutees, "
      f"{n_enf} enfants verses dans des unions existantes, "
      f"{len(nouveaux_lieux)} lieux crees")
if collisions:
    print(f"{collisions} identifiant(s) renomme(s) pour cause de collision avec le corpus")

if WRITE:
    for nom, doc in (("persons.json", persons_doc), ("unions.json", unions_doc), ("places.json", places_doc)):
        json.dump(doc, io.open(os.path.join(D, nom), "w", encoding="utf-8", newline="\n"),
                  ensure_ascii=False, indent=2)
    print("\nEcrit.")
else:
    print("\n(--write pour appliquer)")
