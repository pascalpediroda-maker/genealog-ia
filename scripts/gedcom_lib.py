# -*- coding: utf-8 -*-
"""
Lecture de GEDCOM et remontée d'ascendance.

Bibliothèque partagée : `fix_gedcom_ftsk.py` répare, `gedcom_graft.py` cherche
où souder deux arbres, et les deux ont besoin de lire un GEDCOM de la même
façon. Rien ici n'écrit de fichier.

Le point délicat est la comparaison de dates. Une date GEDCOM n'est pas un
nombre : « BEF 1755 » est une BORNE, et la traiter comme une année fabrique des
mères de trois ans. `Date` porte donc l'année ET le sens de la borne, et
`compatible()` refuse de conclure quand les bornes ne se contredisent pas.
"""

import re
import unicodedata

LINE_RE = re.compile(r"^(\d+)(?: @([^@]+)@)? ([A-Za-z0-9_]+)(?: (.*))?$")
MOIS = {m: i + 1 for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL",
     "AUG", "SEP", "OCT", "NOV", "DEC"])}


def sans_accents(s):
    """« Béatrice » → « BEATRICE ». Les deux bases n'accentuent pas pareil."""
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper()


class Date:
    """Une date GEDCOM réduite à ce qui sert : une année et un sens de borne."""

    __slots__ = ("annee", "sens", "mois", "jour", "brut")

    def __init__(self, brut=""):
        self.brut = brut or ""
        self.annee = self.mois = self.jour = None
        self.sens = None
        v = self.brut.upper().strip()
        if not v:
            return
        for pref, sens in (("BEF", "<"), ("AFT", ">"), ("ABT", "~"),
                           ("EST", "~"), ("CAL", "~"), ("BET", "~"),
                           ("FROM", "~"), ("TO", "<")):
            if v.startswith(pref + " ") or v.startswith(pref):
                self.sens = sens
                break
        else:
            self.sens = "="
        m = re.search(r"(?<!\d)(\d{3,4})(?!\d)", v)
        if m:
            self.annee = int(m.group(1))
        m = re.search(r"(?<!\d)(\d{1,2}) ([A-Z]{3}) (\d{3,4})", v)
        if m and m.group(2) in MOIS:
            self.jour, self.mois = int(m.group(1)), MOIS[m.group(2)]

    def __bool__(self):
        return self.annee is not None

    def __repr__(self):
        return self.brut or "—"

    @property
    def ferme(self):
        """Vrai si la date est exacte, donc utilisable dans les deux sens."""
        return self.sens == "="

    @property
    def au_plus_tot(self):
        """Année minimale possible, ou None si la borne ne la donne pas."""
        return self.annee if self.sens in ("=", ">") else None

    @property
    def au_plus_tard(self):
        return self.annee if self.sens in ("=", "<") else None


def compatible(a, b, tolerance=2):
    """
    Ces deux dates peuvent-elles désigner le même événement ?

    Rend True quand rien ne les sépare — y compris quand l'une est vide : une
    date manquante n'est pas une preuve de différence. Ne rend False que si les
    intervalles possibles sont disjoints.
    """
    if not a or not b:
        return True
    if a.ferme and b.ferme:
        # Un écart de quelques jours ne sépare pas deux personnes : entre l'acte
        # et la déclaration, un décès glisse d'un jour couramment. Louis HUME
        # meurt le 18 décembre 1855 dans un fichier et le 19 dans l'autre, et
        # c'est le même homme — même naissance au jour près, même épouse.
        # L'exactitude est un point de score, pas un critère de rejet.
        return abs(a.annee - b.annee) <= tolerance
    lo_a, hi_a = a.au_plus_tot, a.au_plus_tard
    lo_b, hi_b = b.au_plus_tot, b.au_plus_tard
    if hi_a is not None and lo_b is not None and lo_b - hi_a > tolerance:
        return False
    if hi_b is not None and lo_a is not None and lo_a - hi_b > tolerance:
        return False
    return True


class Personne:
    __slots__ = ("id", "noms", "sexe", "naissance", "deces", "famc", "fams",
                 "metier", "lieu_naissance", "lieu_deces")

    def __init__(self, pid):
        self.id = pid
        self.noms = []          # [(prenom, patronyme)] — plusieurs si variantes
        self.sexe = ""
        self.naissance = Date()
        self.deces = Date()
        self.famc = []
        self.fams = []
        self.metier = ""
        self.lieu_naissance = ""
        self.lieu_deces = ""

    @property
    def prenom(self):
        return self.noms[0][0] if self.noms else ""

    @property
    def patronyme(self):
        return self.noms[0][1] if self.noms else ""

    @property
    def patronymes(self):
        """Toutes les graphies connues — ce corpus en a jusqu'à trois."""
        return [n[1] for n in self.noms if n[1]]

    def __repr__(self):
        d = f" ({self.naissance}–{self.deces})" if (self.naissance or self.deces) else ""
        return f"{self.prenom} {self.patronyme}{d}"


class Famille:
    __slots__ = ("id", "mari", "femme", "enfants", "mariage", "lieu_mariage")

    def __init__(self, fid):
        self.id = fid
        self.mari = None
        self.femme = None
        self.enfants = []
        self.mariage = Date()
        self.lieu_mariage = ""


class Gedcom:
    def __init__(self, chemin, encodage=None):
        self.chemin = chemin
        self.personnes = {}
        self.familles = {}
        self._charger(chemin, encodage)

    def _charger(self, chemin, encodage):
        brut = open(chemin, "rb").read()
        if encodage is None:
            try:
                txt = brut.decode("utf-8")
            except UnicodeDecodeError:
                txt = brut.decode("cp1252")
        else:
            txt = brut.decode(encodage)
        courant = None
        pile = {}
        for ligne in txt.replace("\r\n", "\n").split("\n"):
            if not ligne:
                continue
            m = LINE_RE.match(ligne)
            if not m:
                continue
            niv, xref, tag, val = (int(m.group(1)), m.group(2),
                                   m.group(3), (m.group(4) or "").strip())
            if niv == 0:
                if tag == "INDI":
                    courant = Personne(xref)
                    self.personnes[xref] = courant
                elif tag == "FAM":
                    courant = Famille(xref)
                    self.familles[xref] = courant
                else:
                    courant = None
                pile = {}
                continue
            if courant is None:
                continue
            pile[niv] = tag
            for k in list(pile):
                if k > niv:
                    del pile[k]
            parent = pile.get(niv - 1, "")
            ptr = val[1:-1] if val.startswith("@") and val.endswith("@") else None

            if isinstance(courant, Personne):
                if niv == 1 and tag == "NAME":
                    p = val.split("/")
                    courant.noms.append((p[0].strip(),
                                         p[1].strip() if len(p) > 1 else ""))
                elif niv == 1 and tag == "SEX":
                    courant.sexe = val
                elif niv == 1 and tag == "OCCU":
                    courant.metier = val
                elif niv == 1 and tag == "FAMC" and ptr:
                    courant.famc.append(ptr)
                elif niv == 1 and tag == "FAMS" and ptr:
                    courant.fams.append(ptr)
                elif niv == 2 and tag == "DATE":
                    if parent == "BIRT" and not courant.naissance:
                        courant.naissance = Date(val)
                    elif parent in ("CHR", "BAPM") and not courant.naissance:
                        courant.naissance = Date(val)
                    elif parent == "DEAT" and not courant.deces:
                        courant.deces = Date(val)
                elif niv == 2 and tag == "PLAC":
                    if parent in ("BIRT", "CHR", "BAPM") and not courant.lieu_naissance:
                        courant.lieu_naissance = val
                    elif parent in ("DEAT", "BURI") and not courant.lieu_deces:
                        courant.lieu_deces = val
            else:
                if niv == 1 and tag == "HUSB" and ptr:
                    courant.mari = ptr
                elif niv == 1 and tag == "WIFE" and ptr:
                    courant.femme = ptr
                elif niv == 1 and tag == "CHIL" and ptr:
                    courant.enfants.append(ptr)
                elif niv == 2 and parent == "MARR":
                    if tag == "DATE":
                        courant.mariage = Date(val)
                    elif tag == "PLAC":
                        courant.lieu_mariage = val

    # -- navigation ---------------------------------------------------------

    def parents(self, pid):
        """[(id_pere, id_mere)] — une liste, car FAMC peut être multiple."""
        out = []
        p = self.personnes.get(pid)
        if not p:
            return out
        for fid in p.famc:
            f = self.familles.get(fid)
            if f:
                out.append((f.mari, f.femme))
        return out

    def conjoints(self, pid):
        out = []
        p = self.personnes.get(pid)
        if not p:
            return out
        for fid in p.fams:
            f = self.familles.get(fid)
            if not f:
                continue
            autre = f.femme if f.mari == pid else f.mari
            if autre:
                out.append(autre)
        return out

    def enfants(self, pid):
        out = []
        p = self.personnes.get(pid)
        if not p:
            return out
        for fid in p.fams:
            f = self.familles.get(fid)
            if f:
                out.extend(f.enfants)
        return out

    def ascendance(self, pid, max_gen=30):
        """{generation: {id, ...}}, la génération 0 étant la personne."""
        gens = {0: {pid}}
        vus = {pid}
        g = 0
        while g < max_gen and gens.get(g):
            suivant = set()
            for i in gens[g]:
                for pere, mere in self.parents(i):
                    for a in (pere, mere):
                        if a and a not in vus and a in self.personnes:
                            vus.add(a)
                            suivant.add(a)
            if not suivant:
                break
            g += 1
            gens[g] = suivant
        return gens

    def frontiere(self, pid, max_gen=30):
        """Les ascendants dont on ne connaît aucun parent : là où l'arbre s'arrête."""
        gens = self.ascendance(pid, max_gen)
        out = []
        for g, ids in gens.items():
            for i in ids:
                if not any(pe or me for pe, me in self.parents(i)):
                    out.append((g, i))
        return sorted(out)
