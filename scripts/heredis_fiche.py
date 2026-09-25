# -*- coding: utf-8 -*-
"""Interroge la base Heredis d'Alfiero sur une personne, EN LECTURE SEULE.

POURQUOI CE SCRIPT EXISTE. Le noeud de la branche PEDIRODA se rouvre a chaque
session — « d'ou sort cette filiation ? », « qui d'autre porte ce prenom ? », « la
base dit-elle vraiment ca ? » — et jusqu'au 27 aout 2026 il fallait a chaque fois
rouvrir un sqlite3 a la main et retrouver les jointures. `inspect_heredis.py`
identifie un FICHIER, `rattrapage_heredis.py` compare la base au corpus EN MASSE :
aucun des deux ne repond a « montre-moi Vincenzo ».

Il ne repond QUE ce que la base dit. Il ne deduit rien, il ne cree rien, il n'ecrit
nulle part — c'est un lecteur, et la regle « ne jamais creer une personne sur une
deduction » commence par pouvoir lire la source sans la reformuler.

    python scripts/heredis_fiche.py 291              # la fiche du CodeID 291
    python scripts/heredis_fiche.py VINCENZO         # cherche par prenom ou nom
    python scripts/heredis_fiche.py PEDIRODA --liste # toutes les fiches d'un nom
    python scripts/heredis_fiche.py 291 --lignee     # ascendance et descendance
    python scripts/heredis_fiche.py --anomalies      # les ages impossibles

CHERCHER UNE CHAINE N'EST PAS CHERCHER : « Algira » a coute trois jours parce
qu'elle s'appelle ARGIRA. La recherche par nom est donc APPROXIMATIVE par defaut —
elle ignore les accents, la casse, et tolere une consonne de travers.
"""
import sqlite3, sys, os, re, unicodedata, difflib

import os as _os
import config

HRD = _os.path.join(config.archives(), "le généalogiste.hmw", "le généalogiste.heredis")

# Les types d'evenement d'Heredis, tels qu'ils sortent de la base d'Alfiero.
# 61 et 68 sont les mariages, et ils sont attaches aux UNIONS : c'est la perte
# n°2 de l'import du 11 aout, retrouvee le 27.
EV = {4: "naissance", 12: "deces", 61: "mariage", 68: "mariage (religieux)",
      2: "bapteme", 13: "inhumation", 5: "bapteme", 69: "contrat de mariage",
      70: "divorce", 6: "profession", 74: "residence"}

MOIS = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}


def plat(s):
    """Sans accent, sans casse — pour comparer deux graphies d'un meme nom."""
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper()


def annee(dateged):
    m = re.search(r"(\d{4})", dateged or "")
    return int(m.group(1)) if m else None


class Base:
    def __init__(self, path=HRD):
        if not os.path.exists(path):
            sys.exit(f"base introuvable : {path}\n"
                     "Le NAS X: est-il monte ? Cette base ne vit que la.")
        uri = "file:" + path.replace("\\", "/") + "?mode=ro"
        self.c = sqlite3.connect(uri, uri=True)
        self.c.row_factory = sqlite3.Row
        self.noms = {r["CodeID"]: r["Nom"] for r in self.c.execute("select CodeID, Nom from Noms")}
        self.lieux = {r["CodeID"]: self._lieu(r) for r in self.c.execute("select * from Lieux")}
        self.notes = {}
        for r in self.c.execute("select CodeProprietaire, Note from Notes where Note is not null"):
            self.notes.setdefault(r["CodeProprietaire"], []).append(r["Note"])

    @staticmethod
    def _lieu(r):
        bouts = [r["Ville"], r["Departement"], r["Region"], r["Pays"]]
        return ", ".join(b for b in bouts if b) or "?"

    # --- lecture -------------------------------------------------------------
    def indi(self, cid):
        return self.c.execute("select * from Individus where CodeID=?", (cid,)).fetchone()

    def nom(self, cid):
        i = self.indi(cid)
        if not i:
            return f"#{cid} (absent)"
        return f"{i['Prenoms'] or '?'} {self.noms.get(i['CodeNom'], '?')}"

    def evenements(self, cid):
        """Les evenements dont cette personne est PROPRIETAIRE (naissance, deces...)."""
        out = []
        for r in self.c.execute("select * from Evenements where CodeProprietaire=?", (cid,)):
            out.append((EV.get(r["EventType"], f"type {r['EventType']}"), r["DateGed"],
                        self.lieux.get(r["CodeLieu"], ""), r["Titre"], r["AgeSurActe"],
                        r["RechercheActe"], r["CodeID"]))
        return sorted(out, key=lambda x: (annee(x[1]) or 9999))

    def unions(self, cid):
        return self.c.execute(
            "select * from Unions where Epoux=? or Epouse=?", (cid, cid)).fetchall()

    def mariage(self, union_cid):
        """Les evenements 61/68 sont proprietaires de l'UNION, pas de l'individu."""
        r = self.c.execute(
            "select * from Evenements where CodeProprietaire=? and EventType in (61,68)",
            (union_cid,)).fetchone()
        return r

    def enfants(self, union_cid):
        return [r["CodeID"] for r in self.c.execute(
            "select CodeID from Individus where CodeUnionParents=? "
            "order by MainEventNaissanceTri", (union_cid,))]

    def vital(self, cid):
        """(annee de naissance, annee de deces) telles que la base les trie."""
        i = self.indi(cid)
        if not i:
            return None, None
        n = d = None
        for typ, dg, *_ in self.evenements(cid):
            if typ == "naissance" and n is None:
                n = annee(dg)
            if typ == "deces" and d is None:
                d = annee(dg)
        return n, d

    # --- recherche -----------------------------------------------------------
    def cherche(self, terme):
        """Approximative : sans accent, sans casse, et tolerante d'une consonne."""
        t = plat(terme)
        exact, proche = [], []
        for r in self.c.execute("select CodeID, Prenoms, CodeNom from Individus"):
            plein = plat(f"{r['Prenoms'] or ''} {self.noms.get(r['CodeNom'], '')}")
            if t in plein:
                exact.append(r["CodeID"])
                continue
            for mot in plein.split():
                if difflib.SequenceMatcher(None, t, mot).ratio() >= 0.80:
                    proche.append(r["CodeID"])
                    break
        return exact, proche


def fiche(b, cid, indent=""):
    i = b.indi(cid)
    if not i:
        print(f"{indent}#{cid} : absent de la base")
        return
    sexe = {109: "M", 102: "F"}.get(i["Sexe"], "?")
    print(f"{indent}#{cid}  {b.nom(cid)}   [{sexe}]"
          + (f"   {i['Profession']}" if i["Profession"] else ""))
    for typ, dg, lieu, titre, age, acte, _ in b.evenements(cid):
        bout = f"{indent}    {typ:22} {dg or '?':14} {lieu}"
        if age:
            bout += f"   age sur l'acte : {age}"
        print(bout)
        if titre:
            print(f"{indent}      titre : {titre}")
        if acte:
            print(f"{indent}      RechercheActe : {acte}")
    # parents
    if i["CodePere"] or i["CodeMere"]:
        p = b.nom(i["CodePere"]) if i["CodePere"] else "?"
        m = b.nom(i["CodeMere"]) if i["CodeMere"] else "?"
        print(f"{indent}    pere  #{i['CodePere']}  {p}")
        print(f"{indent}    mere  #{i['CodeMere']}  {m}")
    for u in b.unions(cid):
        autre = u["Epouse"] if u["Epoux"] == cid else u["Epoux"]
        ev = b.mariage(u["CodeID"])
        d = f"{ev['DateGed']} {b.lieux.get(ev['CodeLieu'], '')}" if ev else "(pas d'acte)"
        print(f"{indent}    union #{u['CodeID']} avec #{autre} {b.nom(autre) if autre else '?'}"
              f"   mariage : {d}")
        for e in b.enfants(u["CodeID"]):
            n, m = b.vital(e)
            print(f"{indent}        enfant #{e:5} {b.nom(e):40} {n or '?'}-{m or '?'}")
    for note in b.notes.get(cid, []):
        for ligne in note.strip().splitlines():
            if ligne.strip():
                print(f"{indent}    note : {ligne.strip()}")


def lignee(b, cid, haut=6):
    """Ascendance directe, avec l'ecart d'age parent-enfant a chaque marche."""
    print("== ASCENDANCE ==")
    vu, courant, gen = set(), [(cid, "")], 0
    while courant and gen <= haut:
        suivant = []
        for c, chemin in courant:
            if c in vu:
                continue
            vu.add(c)
            i = b.indi(c)
            if not i:
                continue
            n, d = b.vital(c)
            print(f"  g{gen}  {chemin:14} #{c:5} {b.nom(c):42} {n or '?'}-{d or '?'}")
            for role, p in (("p", i["CodePere"]), ("m", i["CodeMere"])):
                if not p:
                    continue
                pn, _ = b.vital(p)
                ecart = (n - pn) if (n and pn) else None
                alerte = ""
                if ecart is not None:
                    sexe_p = {109: "M", 102: "F"}.get((b.indi(p) or {"Sexe": 0})["Sexe"], "?")
                    if ecart < 14:
                        alerte = f"  <<< {ecart} ans : IMPOSSIBLE"
                    elif sexe_p == "F" and ecart > 45:
                        alerte = f"  <<< mere de {ecart} ans : IMPOSSIBLE"
                    elif sexe_p == "F" and ecart > 42:
                        alerte = f"  <<< mere de {ecart} ans : douteux"
                    elif ecart > 60:
                        alerte = f"  <<< pere de {ecart} ans : douteux"
                if alerte:
                    print(f"       {'':14} {'':6} -> {b.nom(p)} avait {ecart} ans{alerte}")
                suivant.append((p, chemin + role))
        courant, gen = suivant, gen + 1


def anomalies(b):
    """Les ecarts d'age impossibles, sur TOUTE la base — pas seulement l'importe."""
    print("== ECARTS D'AGE PARENT-ENFANT ==")
    lignes = []
    for r in b.c.execute("select CodeID, CodePere, CodeMere from Individus"):
        n, _ = b.vital(r["CodeID"])
        if not n:
            continue
        for role, p in (("pere", r["CodePere"]), ("mere", r["CodeMere"])):
            if not p:
                continue
            pn, pd = b.vital(p)
            if not pn:
                continue
            e = n - pn
            verdict = None
            if e < 14:
                verdict = "IMPOSSIBLE"
            elif role == "mere" and e > 45:
                verdict = "IMPOSSIBLE"
            elif role == "mere" and e > 42:
                verdict = "douteux"
            elif e > 60:
                verdict = "douteux"
            if pd and n > pd + 1 and role == "mere":
                verdict = "IMPOSSIBLE (mere deja morte)"
            if verdict:
                lignes.append((verdict, e, r["CodeID"], role, p))
    for v, e, c, role, p in sorted(lignes, key=lambda x: (x[0] != "IMPOSSIBLE", -x[1])):
        print(f"  [{v:26}] #{c:5} {b.nom(c):38} ne en {b.vital(c)[0]} — "
              f"{role} #{p} {b.nom(p)} avait {e} ans")
    print(f"\n  {len(lignes)} ecart(s) signale(s)")
    print("\n  RAPPEL : un ecart impossible ne dit pas laquelle des deux dates est fausse,")
    print("  ni si c'est la FILIATION qui l'est. Il dit qu'il faut un acte.")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = {a for a in sys.argv[1:] if a.startswith("--")}
    b = Base()
    if "--anomalies" in opts:
        return anomalies(b)
    if not args:
        return sys.exit(__doc__)
    terme = args[0]
    if terme.isdigit():
        cids = [int(terme)]
    else:
        exact, proche = b.cherche(terme)
        cids = exact or proche
        if proche and not exact:
            print(f"(aucune fiche ne porte « {terme} » — voici les graphies voisines)")
        if not cids:
            return print(f"rien pour « {terme} »")
        if len(cids) > 1 and "--liste" not in opts and "--lignee" not in opts:
            print(f"{len(cids)} fiches portent « {terme} » :")
            for c in cids:
                n, d = b.vital(c)
                print(f"  #{c:5} {b.nom(c):44} {n or '?'}-{d or '?'}")
            return print("\nrelancer avec un CodeID, ou --liste pour tout deplier")
    for c in cids:
        if "--lignee" in opts:
            lignee(b, c)
        else:
            fiche(b, c)
        print()


if __name__ == "__main__":
    main()
