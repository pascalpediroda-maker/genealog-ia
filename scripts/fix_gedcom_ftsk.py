# -*- coding: utf-8 -*-
"""
Remise en conformité des exports GEDCOM du logiciel FTSK 1.6 (Windows XP).

Les trois fichiers de un proche sortent d'un logiciel qui écrivait toute date
qu'il ne savait pas formater dans le champ LIEU de l'événement. Résultat : environ
1 100 personnes naissent « à AV 1703 » et n'ont aucune date. Ce script remet ces
dates à leur place, reconstruit l'en-tête au format GEDCOM 5.5.1, réencode en UTF-8
et répare les liens familiaux non réciproques.

    python scripts/fix_gedcom_ftsk.py

Entrée  : stengel-hume/*.ged            (inchangés, jamais réécrits)
Sortie  : stengel-hume/corrige/*.ged    + RAPPORT.md

Principe : ne jamais détruire une valeur d'origine. Une conversion évidente
(« AV 1703 » → « BEF 1703 ») se fait en silence ; dès qu'il a fallu couper une
valeur en deux, deviner, ou renoncer, le texte d'origine est conservé dans une
NOTE sur l'événement et la ligne est listée dans le rapport.
"""

import os
import re
import sys
import datetime
import collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "stengel-hume")
DST = os.path.join(SRC, "corrige")

FILES = [
    ("STENGEL 2026.ged", "STENGEL 2026 - corrige.ged"),
    ("HUME 2026.ged", "HUME 2026 - corrige.ged"),
    ("LEO-colin.ged", "LEO-colin - corrige.ged"),
]

SUBMITTER = "KILIEN /STENGEL/"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL",
          "AUG", "SEP", "OCT", "NOV", "DEC"]

# Les tags d'événement sous lesquels un PLAC peut cacher une date.
EVENT_TAGS = {"BIRT", "DEAT", "MARR", "BURI", "CHR", "BAPM", "DIV", "OCCU",
              "RESI", "EVEN", "CENS", "MARB", "CREM", "ENGA", "GRAD", "RETI"}

LINE_RE = re.compile(r"^(\d+)(?: @([^@]+)@)? ([A-Za-z0-9_]+)(?: (.*))?$")


# ---------------------------------------------------------------------------
# Reconnaissance des dates cachées dans les champs lieu
# ---------------------------------------------------------------------------

# Un jeton date : 24/7/1812, 11/1666, ou 1812 tout seul. Trois ou quatre
# chiffres seulement : « 75015 » et « 67700 » sont des codes postaux, pas des
# années, et ne doivent jamais être convertis.
DATE_TOK = r"(?:\d{1,2}/\d{1,2}/\d{3,4}|\d{1,2}/\d{3,4}|(?<!\d)\d{3,4}(?!\d))"

QUAL_BEF = r"AVANT|AV"
QUAL_AFT = r"APRES|APR\.|AP"
QUAL_ABT = r"VERS|ENV|CA|V"
QUALS = f"{QUAL_BEF}|{QUAL_AFT}|{QUAL_ABT}"


def to_gedcom_date(tok):
    """« 24/7/1812 » → « 24 JUL 1812 » ; « 11/1666 » → « NOV 1666 » ; « 1812 » → « 1812 »."""
    tok = tok.strip()
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{3,4})", tok)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{d:02d} {MONTHS[mo - 1]} {y}"
        return None
    m = re.fullmatch(r"(\d{1,2})/(\d{3,4})", tok)
    if m:
        mo, y = int(m.group(1)), m.group(2)
        if 1 <= mo <= 12:
            return f"{MONTHS[mo - 1]} {y}"
        return None
    m = re.fullmatch(r"\d{3,4}", tok)
    if m:
        return tok
    return None


def qual_prefix(q):
    q = q.upper().rstrip(".")
    if re.fullmatch(QUAL_BEF, q):
        return "BEF"
    if re.fullmatch(QUAL_AFT, q):
        return "AFT"
    return "ABT"


def clean_place(p):
    """
    Nettoie le reliquat de lieu : « a Freistett/bade » → « Freistett/bade ».

    Rend une chaîne vide si le reliquat est en fait une seconde date : « av 1668
    vers 1655 » laissait « vers 1655 » comme lieu de naissance. Un reliquat qui
    ressemble à une date n'est pas un lieu — il part en note et rien d'autre.
    """
    p = p.strip(" ,;-")
    p = re.sub(r"^(?:[aàAÀ]|AU|au|EN|en|DE|de)\s+", "", p)
    p = p.strip(" ,;-")
    if re.fullmatch(r"(?i)(?:(?:%s|OU|ET|ENTRE)\s*)*%s\??\s*" % (QUALS, DATE_TOK), p):
        return ""
    return p


def parse_place_field(v):
    """
    Analyse une valeur de champ PLAC.

    Retourne (date, lieu, note, categorie) où date est une valeur GEDCOM prête
    à l'emploi ou None, lieu le reliquat géographique ou None, note le texte à
    conserver ou None, et categorie sert au rapport.
    """
    v = re.sub(r"\s+", " ", v).strip()
    if not v:
        return None, None, None, None

    # Aucun indice de date : on ne touche à rien. Protège les codes postaux.
    if not re.search(DATE_TOK, v) and not re.match(r"(?i)^(?:%s|OU|ENTRE)\b" % QUALS, v):
        return None, v, None, None

    up = v.upper()

    # --- « OU » : une alternative que le logiciel n'a jamais tranchée ---------
    if re.search(r"(?i)(?:^|\s)OU\s*\d", v) or re.match(r"(?i)^OU\d", v):
        reste = re.sub(r"(?i)(?:^|\s)OU\s*%s\??" % DATE_TOK, " ", v)
        reste = re.sub(r"(?i)^OU\s*", "", reste)
        reste = clean_place(re.sub(r"\d", "", reste)) if re.search(r"[A-Za-zÀ-ÿ]", reste) else ""
        return None, (reste or None), f"valeur d'origine du champ lieu : « {v} »", "alternative « ou » non tranchée"

    # --- « ENTRE 1696 ET 1704 » ---------------------------------------------
    m = re.fullmatch(r"(?i)ENTRE\s*(%s)\s*ET\s*(%s)\s*(.*)" % (DATE_TOK, DATE_TOK), v)
    if m:
        d1, d2 = to_gedcom_date(m.group(1)), to_gedcom_date(m.group(2))
        if d1 and d2:
            reste = clean_place(m.group(3))
            return (f"BET {d1} AND {d2}", reste or None,
                    None if not reste else f"valeur d'origine du champ lieu : « {v} »",
                    "fourchette")

    # --- « AP1725 av 1732 » : deux bornes ------------------------------------
    m = re.match(r"(?i)^(?:%s)\s*(%s)\s*(?:%s)\s*(%s)\s*(.*)$"
                 % (QUAL_AFT, DATE_TOK, QUAL_BEF, DATE_TOK), v)
    if m:
        d1, d2 = to_gedcom_date(m.group(1)), to_gedcom_date(m.group(2))
        if d1 and d2:
            return (f"BET {d1} AND {d2}", None,
                    f"valeur d'origine du champ lieu : « {v} »", "fourchette")

    # --- « VERS 1700-1720 » / « V 1790 1800 » --------------------------------
    m = re.fullmatch(r"(?i)(?:%s)\s*(\d{3,4})\s*[-–/ ]\s*(\d{3,4})" % QUAL_ABT, v)
    if m:
        return (f"BET {m.group(1)} AND {m.group(2)}", None,
                f"valeur d'origine du champ lieu : « {v} »", "fourchette")

    # --- qualificatif en tête : « AV 1700 a Freistett/bade » -----------------
    m = re.match(r"(?i)^(%s)\s*(%s)(\?*)\s*(.*)$" % (QUALS, DATE_TOK), v)
    if m and to_gedcom_date(m.group(2)):
        date = f"{qual_prefix(m.group(1))} {to_gedcom_date(m.group(2))}"
        reste = clean_place(m.group(4))
        doute = bool(m.group(3))
        note = None
        cat = "date seule"
        if reste or doute:
            note = f"valeur d'origine du champ lieu : « {v} »"
            cat = "date + lieu mêlés" if reste else "date incertaine"
        return date, (reste or None), note, cat

    # --- qualificatif en queue : « CRASTATT av 1672 » ------------------------
    m = re.match(r"(?i)^(.+?)\s+(%s)\s*(%s)(\?*)$" % (QUALS, DATE_TOK), v)
    if m and to_gedcom_date(m.group(3)) and re.search(r"[A-Za-zÀ-ÿ]", m.group(1)):
        date = f"{qual_prefix(m.group(2))} {to_gedcom_date(m.group(3))}"
        return (date, clean_place(m.group(1)) or None,
                f"valeur d'origine du champ lieu : « {v} »", "date + lieu mêlés")

    # --- date nue, éventuellement suivie d'autre chose : « 26/9/1684 HAEGEN » -
    m = re.match(r"^(%s)(\?*)\s*(.*)$" % DATE_TOK, v)
    if m and to_gedcom_date(m.group(1)):
        date = to_gedcom_date(m.group(1))
        reste = clean_place(m.group(3))
        doute = bool(m.group(2))
        note = None
        cat = "date seule"
        if reste or doute:
            note = f"valeur d'origine du champ lieu : « {v} »"
            cat = "date + lieu mêlés" if reste else "date incertaine"
        return date, (reste or None), note, cat

    # Un chiffre traîne mais rien de reconnaissable : on laisse le lieu tel quel.
    return None, v, None, None


# ---------------------------------------------------------------------------
# Lecture / écriture
# ---------------------------------------------------------------------------

class Rec:
    """Un enregistrement de niveau 0 et toutes ses lignes filles."""

    def __init__(self, xref, tag):
        self.xref = xref
        self.tag = tag
        self.lines = []          # [level, tag, value]

    def sub_block(self, i):
        """Indices des lignes filles de self.lines[i]."""
        lvl = self.lines[i][0]
        j = i + 1
        while j < len(self.lines) and self.lines[j][0] > lvl:
            j += 1
        return range(i + 1, j)

    def values(self, tag, level=1):
        return [l[2] for l in self.lines if l[0] == level and l[1] == tag]


def read_gedcom(path):
    raw = open(path, "rb").read()
    txt = raw.decode("cp1252")
    recs, head_time = [], None
    cur = None
    for ln in txt.replace("\r\n", "\n").split("\n"):
        if not ln:
            continue
        m = LINE_RE.match(ln)
        if not m:
            raise ValueError("ligne illisible : " + ln[:80])
        lvl, xref, tag, val = int(m.group(1)), m.group(2), m.group(3), (m.group(4) or "")
        val = val.rstrip()
        if lvl == 0:
            cur = Rec(xref, tag)
            recs.append(cur)
        else:
            cur.lines.append([lvl, tag, val])
        if tag == "TIME" and cur is not None and cur.tag == "HEAD":
            head_time = val
    return recs, head_time


def write_gedcom(path, recs):
    out = []
    for r in recs:
        out.append(f"0 @{r.xref}@ {r.tag}" if r.xref else f"0 {r.tag}")
        for lvl, tag, val in r.lines:
            out.append(f"{lvl} {tag} {val}".rstrip())
    with open(path, "wb") as f:
        f.write(("\r\n".join(out) + "\r\n").encode("utf-8"))


# ---------------------------------------------------------------------------
# Corrections
# ---------------------------------------------------------------------------

def fix_header(recs, out_name, src_name, head_time, stats):
    head = next(r for r in recs if r.tag == "HEAD")
    today = datetime.date.today()
    mois = MONTHS[today.month - 1]
    head.lines = [
        [1, "SOUR", "FTSK"],
        [2, "VERS", "1.6"],
        [2, "NAME", "FTSK (Windows XP)"],
        [1, "DATE", "02 FEB 2024"],
        [2, "TIME", head_time or "00:00:00"],
        [1, "SUBM", "@1@"],
        [1, "FILE", out_name],
        [1, "GEDC", ""],
        [2, "VERS", "5.5.1"],
        [2, "FORM", "LINEAGE-LINKED"],
        [1, "CHAR", "UTF-8"],
        [1, "LANG", "French"],
        [1, "NOTE", f"Export FTSK 1.6 du 2 fevrier 2024 ({src_name}), remis en"],
        [2, "CONC", " conformite GEDCOM 5.5.1 le "
                    f"{today.day:02d} {mois} {today.year}."],
        [2, "CONT", "Les dates approximatives que FTSK ecrivait dans le champ lieu ont ete"],
        [2, "CONC", " replacees en DATE (AV/AP/VERS -> BEF/AFT/ABT)."],
        [2, "CONT", "Le texte d'origine est conserve en NOTE sur l'evenement"],
        [2, "CONC", " chaque fois qu'il a fallu couper une valeur en deux."],
    ]
    stats["en-tête reconstruit"] = 1


def fix_submitter(recs, stats):
    subm = next((r for r in recs if r.tag == "SUBM"), None)
    if subm is None:
        subm = Rec("1", "SUBM")
        recs.insert(-1 if recs[-1].tag == "TRLR" else len(recs), subm)
    ancien = next((v for l, t, v in subm.lines if t == "NAME"), "")
    subm.lines = [[1, "NAME", SUBMITTER]]
    if ancien.strip() and ancien.strip() != SUBMITTER:
        stats["auteur du fichier normalisé"] = 1
    return ancien


def fix_names(recs, stats):
    """« ANNE /STENGEL/STENGLERIN/ » → un NAME principal + un NAME par variante."""
    variantes = []
    for r in recs:
        if r.tag != "INDI":
            continue
        i = 0
        while i < len(r.lines):
            lvl, tag, val = r.lines[i]
            if lvl == 1 and tag == "NAME":
                if val != val.strip():
                    stats["espace parasite en tête de nom"] += 1
                v = re.sub(r"\s+", " ", val).strip()
                parts = v.split("/")
                if len(parts) > 3:
                    given = parts[0].strip()
                    surnames = [p.strip() for p in parts[1:] if p.strip()]
                    r.lines[i][2] = f"{given} /{surnames[0]}/".strip()
                    insert = i + 1
                    for extra in surnames[1:]:
                        r.lines.insert(insert, [1, "NAME", f"{given} /{extra}/".strip()])
                        insert += 1
                    i = insert - 1
                    variantes.append((r.xref, v, surnames))
                    stats["patronymes à variantes éclatés"] += 1
                else:
                    r.lines[i][2] = v
            i += 1
    return variantes


def fix_places(recs, stats, journal):
    """Le cœur : sortir les dates du champ lieu."""
    for r in recs:
        i = 0
        while i < len(r.lines):
            lvl, tag, val = r.lines[i]
            if not (lvl == 1 and tag in EVENT_TAGS):
                i += 1
                continue
            bloc = list(r.sub_block(i))
            plac_idx = [j for j in bloc if r.lines[j][0] == 2 and r.lines[j][1] == "PLAC"]
            if not plac_idx:
                i += 1
                continue
            j = plac_idx[0]
            date, lieu, note, cat = parse_place_field(r.lines[j][2])
            if cat is None and date is None:
                if lieu is not None and lieu != r.lines[j][2]:
                    r.lines[j][2] = lieu
                i += 1
                continue

            a_deja_une_date = any(r.lines[k][0] == 2 and r.lines[k][1] == "DATE"
                                  for k in bloc)
            nouvelles = []
            if date and a_deja_une_date:
                note = (note or f"valeur d'origine du champ lieu : « {r.lines[j][2]} »")
                note += " — l'événement portait déjà une date, celle-ci n'a pas été écrasée"
                cat = "conflit : date déjà présente"
                date = None
            if date:
                nouvelles.append([2, "DATE", date])
                stats["dates sorties du champ lieu"] += 1
            if lieu:
                nouvelles.append([2, "PLAC", lieu])
            if note:
                nouvelles.append([2, "NOTE", note])
                stats["notes de sauvegarde ajoutées"] += 1

            journal.append((r.xref, tag, r.lines[j][2], date, lieu, cat))
            r.lines[j:j + 1] = nouvelles
            i += 1


def borne(rec, tag):
    """
    Date d'un événement sous forme de borne : (année, sens).

    Le sens vaut « = » (date ferme), « < » (au plus tard), « > » (au plus tôt)
    ou « ~ » (approximative). Il est indispensable : « BEF 1755 » ne dit pas
    qu'une femme est née en 1755, il dit qu'elle est née *avant*, peut-être
    vingt-cinq ans avant. S'en servir comme d'une date ferme fabrique des mères
    de trois ans — c'est exactement ce que fait le détecteur d'anomalies de
    Geneanet, et il ne faut pas le refaire ici.
    """
    for i, (lvl, t, v) in enumerate(rec.lines):
        if lvl == 1 and t == tag:
            for j in rec.sub_block(i):
                if rec.lines[j][1] == "DATE":
                    val = rec.lines[j][2].upper()
                    m = re.search(r"(?<!\d)(\d{3,4})(?!\d)", val)
                    if not m:
                        return None, None
                    y = int(m.group(1))
                    for pref, sens in (("BEF", "<"), ("AFT", ">"),
                                       ("ABT", "~"), ("EST", "~"),
                                       ("CAL", "~"), ("BET", "~")):
                        if val.startswith(pref):
                            return y, sens
                    return y, "="
    return None, None


def lien_impossible(parent, enfant, role):
    """
    Motif si ce lien parent-enfant est certainement faux, sinon None.

    « Certainement » est le mot : on ne conclut que lorsqu'une borne va dans le
    sens de la contradiction. Un doute laisse passer le lien.
    """
    cb, cs = borne(enfant, "BIRT")
    if cb is None:
        cb, cs = borne(enfant, "CHR")
    if cb is None:
        return None
    au_plus_tot = cb if cs in ("=", ">") else None   # né pas avant cb
    au_plus_tard = cb if cs in ("=", "<") else None  # né pas après cb

    pd, ds = borne(parent, "DEAT")
    if pd is not None and ds in ("=", "<") and au_plus_tot is not None:
        # un père peut avoir un enfant posthume, une mère non
        if au_plus_tot - pd > (1 if role == "HUSB" else 0):
            return f"mort{'e' if role == 'WIFE' else ''} en {pd}"

    pb, bs = borne(parent, "BIRT")
    if pb is not None and bs in ("=", ">") and au_plus_tard is not None:
        if au_plus_tard < pb:
            return f"né{'e' if role == 'WIFE' else ''} en {pb}, après l'enfant"
        if au_plus_tard - pb < 13:
            return f"aurait eu {au_plus_tard - pb} ans"
    return None


def incoherences(recs):
    """
    Les contradictions de dates qui tiennent debout, bornes comprises.

    Geneanet en signale une trentaine sur LEO-colin ; la plupart viennent de ce
    qu'il lit « avant 1750 » comme « 1750 ». Cette fonction ne conclut que
    lorsqu'une borne va dans le sens de la contradiction, ce qui ramène la liste
    à ce qui mérite vraiment d'être rouvert.
    """
    indi = {r.xref: r for r in recs if r.tag == "INDI"}
    fam = {r.xref: r for r in recs if r.tag == "FAM"}

    def ptrs(r, tag):
        return [v[1:-1] for l, t, v in r.lines
                if l == 1 and t == tag and v.startswith("@")]

    def nom(i):
        r = indi.get(i)
        if not r:
            return "?"
        v = next((v for l, t, v in r.lines if t == "NAME"), "")
        return re.sub(r"\s+", " ", v.replace("/", " ")).strip() or "? ?"

    out = []
    for fid, f in fam.items():
        my, ms = borne(f, "MARR")
        roles = [(p, "HUSB") for p in ptrs(f, "HUSB")] + \
                [(p, "WIFE") for p in ptrs(f, "WIFE")]
        for pid, role in roles:
            p = indi.get(pid)
            if p is None:
                continue
            pb, bs = borne(p, "BIRT")
            pd, ds = borne(p, "DEAT")
            if pb and bs in ("=", ">") and my and ms in ("=", "<") and my - pb < 13:
                out.append((nom(pid), pid, f"marié(e) à {my - pb} ans au plus",
                            f"naissance {pb}, mariage {'≤' if ms == '<' else ''}{my}"))
            for cid in ptrs(f, "CHIL"):
                c = indi.get(cid)
                if c is None:
                    continue
                cb, cs = borne(c, "BIRT")
                if cb is None:
                    cb, cs = borne(c, "CHR")
                if cb is None:
                    continue
                tot = cb if cs in ("=", ">") else None
                tard = cb if cs in ("=", "<") else None
                if pd and ds in ("=", "<") and tot \
                        and tot - pd > (1 if role == "HUSB" else 0):
                    out.append((nom(pid), pid, f"mort(e) avant la naissance de {nom(cid)}",
                                f"décès {'≤' if ds == '<' else ''}{pd}, enfant "
                                f"{'≥' if cs == '>' else ''}{cb}"))
                if pb and bs in ("=", ">") and tard:
                    if tard < pb:
                        out.append((nom(pid), pid, f"né(e) après son enfant {nom(cid)}",
                                    f"parent {pb}, enfant ≤{cb}"))
                    elif tard - pb < 13:
                        out.append((nom(pid), pid,
                                    f"{tard - pb} ans au plus à la naissance de {nom(cid)}",
                                    f"parent {pb}, enfant ≤{cb}"))
                if pb and bs in ("=", "<") and tot:
                    age = tot - pb
                    if (role == "WIFE" and age > 55) or (role == "HUSB" and age > 75):
                        out.append((nom(pid), pid,
                                    f"{age} ans au moins à la naissance de {nom(cid)}",
                                    f"parent {'≤' if bs == '<' else ''}{pb}, enfant {cb}"))
    return sorted(set(out))


def dedupe_pointers(recs, stats):
    """
    Supprime les pointeurs répétés à l'identique sur un même enregistrement.

    FTSK a écrit jusqu'à trois fois « 1 FAMS @002809@ » sur la même personne.
    Les logiciels d'import en font autant d'unions distinctes : André FRITSCH
    se retrouve marié deux fois à la même femme le même jour.
    """
    for r in recs:
        vus, garder = set(), []
        for lvl, tag, val in r.lines:
            if lvl == 1 and tag in ("FAMS", "FAMC", "CHIL", "HUSB", "WIFE") \
                    and val.startswith("@"):
                if (tag, val) in vus:
                    stats[f"pointeurs {tag} dupliqués supprimés"] += 1
                    continue
                vus.add((tag, val))
            garder.append([lvl, tag, val])
        r.lines = garder


def fix_links(recs, stats, conflits, refuses):
    """
    Rétablit les liens INDI <-> FAM manquants dans un sens.

    FTSK laisse des pointeurs unilatéraux : l'enfant déclare son `FAMC` mais la
    famille ne le compte pas dans ses `CHIL`. La plupart sont de vraies moitiés
    de lien, et les compléter sauve l'enfant de l'orphelinat dans l'arbre. Mais
    certains sont des pointeurs égarés, et les compléter écrit une filiation que
    personne n'a saisie : trois FRITSCH nés en 1940-1950 sont ainsi devenus les
    enfants d'un couple marié en 1869 dont le père est mort en 1913. D'où le
    garde-fou ci-dessous — il ne juge pas la famille, il refuse d'inventer une
    ligne quand les dates l'excluent avec certitude.
    """
    indi = {r.xref: r for r in recs if r.tag == "INDI"}
    fam = {r.xref: r for r in recs if r.tag == "FAM"}

    def refus_parente(f, enfant, indi_map):
        for role in ("HUSB", "WIFE"):
            for par in [v[1:-1] for l, t, v in f.lines
                        if l == 1 and t == role and v.startswith("@")]:
                p = indi_map.get(par)
                if p is None:
                    continue
                m = lien_impossible(p, enfant, role)
                if m:
                    v = next((x for l, t, x in p.lines if t == "NAME"), "")
                    return f"{v.replace('/', '').strip()} {m}"
        return None

    def nom(pid):
        p = indi.get(pid)
        if p is None:
            return "?"
        v = next((v for l, t, v in p.lines if t == "NAME"), "")
        return v.replace("/", "").strip() or "?"

    def annees(pid):
        """« 1759-1810 » à partir des blocs BIRT et DEAT, pour situer la personne."""
        p = indi.get(pid)
        if p is None:
            return ""
        out = {}
        for i, (lvl, tag, val) in enumerate(p.lines):
            if lvl == 1 and tag in ("BIRT", "DEAT"):
                for j in p.sub_block(i):
                    if p.lines[j][1] == "DATE":
                        v = p.lines[j][2]
                        m = re.search(r"\d{3,4}", v)
                        if m:
                            # « BEF 1683 » doit rester « <1683 » : dans ce tableau
                            # l'écart de dates est justement ce qu'on regarde.
                            signe = {"BEF": "<", "AFT": ">", "ABT": "~",
                                     "BET": "~"}.get(v.split()[0], "")
                            out.setdefault(tag, signe + m.group(0))
                        break
        if not out:
            return ""
        return f"{out.get('BIRT', '?')}-{out.get('DEAT', '?')}"

    def mariage(fid):
        f = fam.get(fid)
        if f is None:
            return ""
        for i, (lvl, tag, val) in enumerate(f.lines):
            if lvl == 1 and tag == "MARR":
                for j in f.sub_block(i):
                    if f.lines[j][1] == "DATE":
                        return f.lines[j][2]
        return ""

    def ptrs(rec, tag):
        return [v[1:-1] for l, t, v in rec.lines
                if l == 1 and t == tag and v.startswith("@") and v.endswith("@")]

    for fid, f in fam.items():
        for role in ("HUSB", "WIFE"):
            for pid in ptrs(f, role):
                p = indi.get(pid)
                if p is not None and fid not in ptrs(p, "FAMS"):
                    p.lines.append([1, "FAMS", f"@{fid}@"])
                    stats["liens FAMS rétablis"] += 1
        for cid in ptrs(f, "CHIL"):
            c = indi.get(cid)
            if c is None or fid in ptrs(c, "FAMC"):
                continue
            motif = refus_parente(f, c, indi)
            if motif:
                refuses.append(("FAMC", cid, nom(cid), annees(cid), fid, motif))
                stats["liens non rétablis (dates incompatibles)"] += 1
                continue
            c.lines.append([1, "FAMC", f"@{fid}@"])
            stats["liens FAMC rétablis"] += 1

    for pid, p in indi.items():
        sex = next((v for l, t, v in p.lines if t == "SEX"), "")
        for fid in ptrs(p, "FAMC"):
            f = fam.get(fid)
            if f is None or pid in ptrs(f, "CHIL"):
                continue
            motif = refus_parente(f, p, indi)
            if motif:
                refuses.append(("CHIL", pid, nom(pid), annees(pid), fid, motif))
                stats["liens non rétablis (dates incompatibles)"] += 1
                continue
            f.lines.append([1, "CHIL", f"@{pid}@"])
            stats["liens CHIL rétablis"] += 1
        for fid in ptrs(p, "FAMS"):
            f = fam.get(fid)
            if f is None:
                continue
            if pid in ptrs(f, "HUSB") + ptrs(f, "WIFE"):
                continue
            role = "WIFE" if sex == "F" else "HUSB"
            if ptrs(f, role):
                occupant = ptrs(f, role)[0]
                conflits.append((pid, nom(pid), annees(pid), fid, mariage(fid),
                                 role, occupant, nom(occupant), annees(occupant)))
                stats["conjoint laissé en l'état (place déjà occupée)"] += 1
                continue
            f.lines.append([1, role, f"@{pid}@"])
            stats["liens HUSB/WIFE rétablis"] += 1


def drop_empty(recs, stats):
    for r in recs:
        garder = []
        for k, (lvl, tag, val) in enumerate(r.lines):
            if val == "" and tag in ("ADDR", "CONT", "NOTE"):
                enfants = any(l > lvl for l, _, _ in r.lines[k + 1:k + 2])
                if not enfants:
                    stats["lignes vides supprimées"] += 1
                    continue
            garder.append([lvl, tag, val])
        r.lines = garder


# ---------------------------------------------------------------------------

def main():
    os.makedirs(DST, exist_ok=True)
    rapport = []

    for src_name, out_name in FILES:
        src = os.path.join(SRC, src_name)
        if not os.path.exists(src):
            print(f"  !! introuvable : {src}")
            continue
        stats = collections.Counter()
        journal, conflits, refuses = [], [], []
        recs, head_time = read_gedcom(src)

        ancien_subm = fix_submitter(recs, stats)
        variantes = fix_names(recs, stats)
        fix_places(recs, stats, journal)
        dedupe_pointers(recs, stats)
        fix_links(recs, stats, conflits, refuses)
        drop_empty(recs, stats)
        fix_header(recs, out_name, src_name, head_time, stats)

        incoh = incoherences(recs)

        # TRLR toujours en dernier
        recs = [r for r in recs if r.tag != "TRLR"] + [Rec(None, "TRLR")]

        out = os.path.join(DST, out_name)
        write_gedcom(out, recs)

        n_indi = sum(1 for r in recs if r.tag == "INDI")
        n_fam = sum(1 for r in recs if r.tag == "FAM")
        print(f"{src_name}  ->  {out_name}")
        print(f"   {n_indi} individus, {n_fam} familles")
        for k, v in sorted(stats.items()):
            print(f"   {v:5d}  {k}")
        print()

        rapport.append({
            "src": src_name, "out": out_name, "indi": n_indi, "fam": n_fam,
            "stats": stats, "journal": journal, "variantes": variantes,
            "subm": ancien_subm, "conflits": conflits, "refuses": refuses,
            "incoh": incoh,
        })

    write_report(rapport)
    print(f"Rapport : {os.path.join(DST, 'RAPPORT.md')}")


def write_report(rapport):
    L = []
    A = L.append
    today = datetime.date.today()
    A("# Correction des GEDCOM FTSK 1.6")
    A("")
    A(f"Généré le {today.day:02d}/{today.month:02d}/{today.year} "
      "par `scripts/fix_gedcom_ftsk.py`.")
    A("")
    A("Les fichiers d'origine ne sont **jamais modifiés**. Les versions corrigées sont")
    A("dans ce dossier, prêtes à être importées dans Geneanet, Gramps, Hérédis ou")
    A("Filae.")
    A("")
    A("## Ce qui a été corrigé, fichier par fichier")
    A("")
    for r in rapport:
        A(f"### {r['src']} → `{r['out']}`")
        A("")
        A(f"{r['indi']} individus, {r['fam']} familles.")
        A("")
        A("| Correction | Nombre |")
        A("|---|---:|")
        for k, v in sorted(r["stats"].items()):
            A(f"| {k} | {v} |")
        A("")

    A("## Les cas à relire")
    A("")
    A("Une conversion évidente — « AV 1703 » → « BEF 1703 » — s'est faite en silence.")
    A("Tout le reste est ci-dessous, avec la valeur d'origine conservée en NOTE sur")
    A("l'événement dans le fichier corrigé. Ce sont les seules lignes où le script a")
    A("coupé une valeur en deux ou renoncé à trancher.")
    A("")
    for r in rapport:
        durs = [j for j in r["journal"]
                if j[5] not in (None, "date seule", "fourchette")]
        if not durs:
            continue
        A(f"### {r['src']} — {len(durs)} cas")
        A("")
        A("| Individu | Événement | Valeur d'origine | Date retenue | Lieu retenu | Cas |")
        A("|---|---|---|---|---|---|")
        for xref, tag, orig, date, lieu, cat in sorted(durs, key=lambda x: x[5]):
            A(f"| `@{xref}@` | {tag} | `{orig}` | {date or '—'} "
              f"| {lieu or '—'} | {cat} |")
        A("")

    A("## Patronymes à variantes")
    A("")
    A("FTSK empilait les graphies dans un seul champ (`/STENGEL/STENGLE/STANGLE/`),")
    A("ce que GEDCOM interdit — un nom porte exactement deux barres obliques. Chaque")
    A("variante est devenue un `1 NAME` supplémentaire : les logiciels de généalogie")
    A("les affichent comme noms alternatifs, et la recherche les trouve tous.")
    A("")
    for r in rapport:
        if not r["variantes"]:
            continue
        A(f"### {r['src']} — {len(r['variantes'])} personnes")
        A("")
        A("| Individu | Valeur d'origine | Nom principal | Variantes ajoutées |")
        A("|---|---|---|---|")
        for xref, orig, surnames in r["variantes"]:
            A(f"| `@{xref}@` | `{orig}` | {surnames[0]} | "
              f"{', '.join(surnames[1:])} |")
        A("")

    A("## À lire avant de regarder les anomalies signalées par Geneanet")
    A("")
    A("Après import, Geneanet signale une trentaine d'anomalies sur `LEO-colin`.")
    A("**La plupart sont des faux positifs, et ils viennent d'un progrès, pas d'un**")
    A("**dégât.**")
    A("")
    A("Avant correction, 591 personnes de ce fichier n'avaient aucune date de")
    A("naissance : elle était coincée dans le champ lieu, invisible pour tout")
    A("logiciel. Geneanet ne pouvait donc rien vérifier sur elles. Maintenant qu'elles")
    A("ont une date, il les contrôle — et il traite « avant 1750 » comme s'il lisait")
    A("« 1750 ».")
    A("")
    A("D'où des messages comme « François HUME s'est marié à 2 ans ». Sa naissance est")
    A("`BEF 1750`, son mariage en 1752 : s'il est né en 1725, il s'est marié à 27 ans.")
    A("Rien ne cloche, sinon que le détecteur prend une **borne** pour une **date**.")
    A("Même chose pour « Martin BOURDIN, 10 ans » — lui `BEF 1686`, son fils")
    A("`BET 1696 AND 1704` : deux bornes comparées comme deux dates.")
    A("")
    A("La règle de lecture : **une anomalie dont les deux dates sont fermes mérite**")
    A("**qu'on la regarde ; une anomalie qui repose sur un « avant » ou un « entre »**")
    A("**se masque sans remords.** Les dates fermes, ce sont celles qui portent un jour")
    A("et un mois, ou une année seule sans qualificatif.")
    A("")
    A("Le tri a été fait ci-dessous. Une borne n'y compte que dans le sens où elle")
    A("conclut : « mort après 1828 » n'empêche pas un enfant en 1840, mais « mort")
    A("avant 1913 » interdit un enfant en 1950.")
    A("")
    for r in rapport:
        A(f"### {r['src']} — {len(r['incoh'])} contradictions qui tiennent")
        A("")
        if not r["incoh"]:
            A("Aucune.")
            A("")
            continue
        A("| Personne | Ce qui cloche | Dates |")
        A("|---|---|---|")
        for pnom, pid, quoi, dates in r["incoh"]:
            A(f"| {pnom} `@{pid}@` | {quoi} | {dates} |")
        A("")

    if any(r["refuses"] for r in rapport):
        A("## Liens de filiation volontairement non rétablis")
        A("")
        A("FTSK laisse des pointeurs unilatéraux : l'enfant déclare `FAMC` vers une")
        A("famille qui ne le compte pas parmi ses `CHIL`. Compléter ces moitiés de lien")
        A("est presque toujours juste, et 219 l'ont été. Les cas ci-dessous ont été")
        A("**laissés tels quels**, parce que les compléter aurait écrit une filiation")
        A("que personne n'a saisie et que les dates excluent.")
        A("")
        A("Le pointeur d'origine est conservé, intact. C'est la ligne réciproque qui n'a")
        A("pas été ajoutée. À trancher dans le logiciel : soit la date est fausse, soit")
        A("le pointeur vise la mauvaise famille.")
        A("")
        for r in rapport:
            if not r["refuses"]:
                continue
            A(f"### {r['src']} — {len(r['refuses'])} cas")
            A("")
            A("| Personne | Années | Famille visée | Pourquoi c'est exclu |")
            A("|---|---|---|---|")
            for sens, pid, pnom, pan, fid, motif in r["refuses"]:
                A(f"| {pnom} `@{pid}@` | {pan or '—'} | `@{fid}@` | {motif} |")
            A("")

    if any(r["conflits"] for r in rapport):
        A("## Conjoints laissés en l'état")
        A("")
        A("**Les remariages n'ont posé aucun problème et n'ont pas été touchés.** En")
        A("GEDCOM, un remariage s'écrit avec plusieurs `FAMS` sur la personne, pointant")
        A("vers plusieurs enregistrements `FAM` distincts. Il y en a beaucoup dans ces")
        A("fichiers — François-Joseph OSWALD, Arsène FRITSCH, Nicole HEIM, Lydia DUMONT")
        A("en ont chacun deux — et tous sont passés intacts.")
        A("")
        A("Les cas ci-dessous sont d'une autre forme : une personne porte un `FAMS` vers")
        A("une famille dont la place d'époux correspondante est **déjà tenue par**")
        A("**quelqu'un d'autre**. GEDCOM 5.5.1 n'admet qu'un `HUSB` et qu'une `WIFE` par")
        A("enregistrement `FAM` ; deux `HUSB` dans la même famille, la plupart des")
        A("logiciels les ignorent sans le dire.")
        A("")
        A("**Le script n'a rien supprimé.** Le `1 FAMS` saisi par un proche est toujours là,")
        A("mot pour mot, dans le fichier corrigé. La seule chose qui n'a pas été faite,")
        A("c'est d'ajouter une deuxième ligne `1 HUSB` à l'intérieur de la famille.")
        A("")
        A("Si l'un de ces liens est un vrai second mariage, la façon de l'écrire n'est")
        A("pas d'ajouter un époux à la famille existante mais de **donner au couple son**")
        A("**propre enregistrement `FAM`** — exactement comme les remariages déjà")
        A("présents dans ces fichiers. Les années sont données pour que la décision")
        A("revienne à celui qui connaît le dossier.")
        A("")
        for r in rapport:
            if not r["conflits"]:
                continue
            A(f"### {r['src']} — {len(r['conflits'])} cas")
            A("")
            A("| Personne | Années | Famille | Mariage | Place | Déjà tenue par | Années |")
            A("|---|---|---|---|---|---|---|")
            for pid, pnom, pan, fid, marr, role, oid, onom, oan in r["conflits"]:
                A(f"| {pnom} `@{pid}@` | {pan or '—'} | `@{fid}@` | {marr or '—'} "
                  f"| {role} | {onom} `@{oid}@` | {oan or '—'} |")
            A("")

    A("## Ce qui n'a pas été touché, volontairement")
    A("")
    A("- **Les trois fichiers restent séparés.** `LEO-colin` est l'arbre relié de Léo")
    A("  et Colin ; les deux autres sont les personnes non encore rattachées. Les")
    A("  fusionner effacerait cette distinction, qui est une information.")
    A("- **Les patronymes `?`** (16 dans STENGEL, 96 dans LEO-colin) sont laissés tels")
    A("  quels : c'est une inconnue assumée, pas une erreur de format.")
    A("- **Les individus jamais reliés à une famille** (127 au total) sont conservés.")
    A("- **Les codes postaux** (`75015`, `HAEGEN 67700`, `CHU TOURS 37000`) n'ont pas")
    A("  été pris pour des années : le détecteur ignore les nombres de cinq chiffres.")
    A("")
    A("## Ce qui manque encore, et que seul un proche peut ajouter")
    A("")
    A("Les fichiers ne contiennent **aucune source** (0 enregistrement `SOUR`),")
    A("**aucune photo** (0 `OBJE`) et aucune date de modification. C'est un arbre de")
    A("noms et de dates sans provenance : rien n'indique quel acte a fourni quelle")
    A("date. Ce n'est pas un défaut de format et aucun script ne peut le réparer,")
    A("mais c'est ce qui distingue un arbre vérifiable d'un arbre à croire sur parole.")

    with open(os.path.join(DST, "RAPPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
