# -*- coding: utf-8 -*-
"""Relit les TRAMES et signale les redondances : ce que `build.py` ne peut pas voir.

    python scripts/relire.py                  # tout le corpus
    python scripts/relire.py durand-jean       # une personne
    python scripts/relire.py --seuil 5        # n-grammes partages a partir de N mots

POURQUOI CE SCRIPT EXISTE. `build.py` valide la STRUCTURE -- des identifiants qui existent,
des dates coherentes, des participants a leur place. Il ne lit pas les TEXTES, et c'est dans
les textes que se logent les redites. Le 31 aout 2026, le généalogiste a releve coup sur coup sur la
seule trame de Jean DURAND :

  - la rencontre avec sa future femme racontee DEUX FOIS, dans le moment de Rochefort et sur le sien ;
  - << Stephane nait le 15 fevrier 1967, Herve le 5 janvier 1973 >> ecrit dans le texte du
    mariage, alors que les deux naissances sont les DEUX MOMENTS SUIVANTS de la trame ;
  - un << Tours 1965-1975 >> a cote d'un << Tours 1963-1968 >>.

Aucune de ces trois n'est une erreur de structure : chaque moment, pris seul, est juste. Elles
ne se voient qu'en LISANT LA TRAME DANS L'ORDRE, et c'est ce que ce script fait a la place de
l'oeil.

DEUX DETECTEURS, ET ILS PRENNENT LE PROBLEME PAR DEUX BOUTS.

1. UNE DATE ECRITE EN CLAIR QUI EST DEJA UN MOMENT. << le 15 fevrier 1967 >> dans un texte,
   quand un autre moment de la meme trame porte cette date : le lecteur lit la meme chose
   deux fois de suite. C'est le cas le plus frequent et le plus facile a corriger.

2. DEUX TEXTES QUI SE RECOUVRENT. Des suites de mots identiques entre deux narratifs de la
   meme personne -- la signature d'un moment ancien qu'on a laisse en place en versant sa
   version neuve.

CE QUE LE SCRIPT NE FAIT PAS : trancher. Une date peut etre legitimement rappelee (<< veuf
depuis 1935, il se remarie >>), et deux textes peuvent partager une formule sans se repeter.
Il montre, on juge. Comme `--vues` et `--postes`, il fait REGARDER.
"""
import io
import json
import os
import re
import sys
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# GENEALOGIA_DATA, COMME LES QUATRE AUTRES SCRIPTS — il manquait ici. `build.py`,
# `build_media.py`, `build_poc.py` et `corpus_io.py` lisent cette variable depuis le
# 4 septembre 2026 ; `relire.py`, ecrit plus tard, ne l'avait jamais reprise et lisait
# toujours `data/`. Consequence : lance sur un second corpus, il rendait les 341
# signalements du premier sans que rien ne le dise — un rapport plausible et entierement
# hors sujet. Vu le 17 septembre 2026 en versant la famille MARTIN.
D = os.environ.get("GENEALOGIA_DATA") or os.path.join(RACINE, "data")

MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre")
NUM = {m: f"{i + 1:02d}" for i, m in enumerate(MOIS)}
RE_JOUR = re.compile(r"\b(\d{1,2})(?:er)?\s+(" + "|".join(MOIS) + r")\s+(\d{4})\b", re.I)
RE_MOIS = re.compile(r"\b(" + "|".join(MOIS) + r")\s+(\d{4})\b", re.I)
RE_AN = re.compile(r"\b(1[5-9]\d\d|20[0-2]\d)\b")


def _proche(a, b, marge=2):
    """Deux prenoms a `marge` corrections pres -- Lucile contre Lucie, Mathieu contre Matthieu.

    Distance de Levenshtein, ecrite ici parce qu'aucune dependance n'est installee et que le
    corpus doit tourner sans rien.
    """
    if abs(len(a) - len(b)) > marge:
        return False
    prec = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prec[j] + 1, cur[j - 1] + 1, prec[j - 1] + (ca != cb)))
        prec = cur
    return prec[-1] <= marge


def charge(nom):
    d = json.loads(io.open(os.path.join(D, nom), encoding="utf-8").read())
    return d[list(d)[-1]] if isinstance(d, dict) else d


def iso(dv):
    """La date d'un moment, sous la forme la plus precise qu'il porte."""
    if not dv:
        return None
    return dv.get("iso") or dv.get("from")


def dates_du_texte(t):
    """Les dates ecrites en clair, AU JOUR OU AU MOIS, rendues au format iso.

    LES MILLESIMES NUS SONT EXCLUS, et c'est deliberé : un narratif rappelle legitimement
    une annee -- << veuf depuis 1935 >>, << qu'il connaissait depuis 1968 >> -- et les
    compter noyait le signal sous 650 faux positifs. Une date au jour reecrite quand elle
    est deja un moment, elle, se lit deux fois de suite sur la trame.
    """
    out = set()
    for j, m, a in RE_JOUR.findall(t or ""):
        out.add(f"{a}-{NUM[m.lower()]}-{int(j):02d}")
    for m, a in RE_MOIS.findall(t or ""):
        out.add(f"{a}-{NUM[m.lower()]}")
    return out


def nu(t):
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).split()


def lu_par(e, pid):
    """LE TEXTE QUE CETTE PERSONNE-LA LIT SUR SA TRAME, et lui seul.

    La premiere version comparait toutes les surfaces entre elles -- chaque `narrative_for`
    contre chaque autre. Elle rendait 2941 signalements sur le corpus, illisibles : les
    variantes d'un meme moment SONT FAITES pour se ressembler, c'est la meme histoire vue
    d'ailleurs. Or personne ne lit deux variantes a la fois. Sur la fiche de quelqu'un, un
    moment n'a qu'un texte : le sien s'il en a un, le generique sinon.
    """
    v = (e.get("narrative_for") or {}).get(pid)
    return (("narrative_for/" + pid), v) if v else ("narrative", e.get("narrative") or "")


def shingles(t, n):
    m = nu(t)
    return {" ".join(m[k:k + n]) for k in range(len(m) - n + 1)}


FREQ = {}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    seuil = 6
    if "--seuil" in sys.argv:
        seuil = int(sys.argv[sys.argv.index("--seuil") + 1])
    cible = args[0] if args else None

    persons = {p["id"]: p for p in charge("persons.json")}
    events = charge("events.json")

    # Combien de moments DIFFERENTS portent chaque suite de mots : au-dela de deux, c'est
    # une formule du corpus, pas une redite entre deux moments d'une meme vie.
    for e in events:
        vus = set()
        for t in [e.get("narrative") or ""] + list((e.get("narrative_for") or {}).values()):
            vus |= shingles(t, seuil)
        for g in vus:
            FREQ[g] = FREQ.get(g, 0) + 1

    # La trame de chacun : les moments ou il figure, dans l'ordre.
    trames = {}
    for e in events:
        for q in list(e.get("participants", [])) + list(e.get("participants_extra", [])):
            if q["person"] in persons:
                trames.setdefault(q["person"], []).append(e)
    # Les naissances et deces sont des moments de la trame sans etre des `events`.
    vitaux = {}
    for pid, p in persons.items():
        for cle in ("birth", "death"):
            d = iso((p.get(cle) or {}).get("date"))
            if d:
                vitaux.setdefault(pid, []).append((cle, d))

    total = 0
    for pid in sorted(trames) if not cible else [cible]:
        lot = sorted(trames.get(pid, []), key=lambda e: iso(e.get("date")) or "9999")
        signale = []

        # --- 1. une date en clair qui est deja un moment de la meme trame ---
        connues = {}
        for e in lot:
            d = iso(e.get("date"))
            if d:
                connues.setdefault(d, []).append(e["id"])
        for cle, d in vitaux.get(pid, []):
            connues.setdefault(d, []).append(cle)
        for e in lot:
            for surface, t in [lu_par(e, pid)]:
                for d in dates_du_texte(t):
                    porteurs = [x for x in connues.get(d, []) if x != e["id"]]
                    if porteurs:
                        signale.append(("date", f"{e['id']} / {surface}",
                                        f"« {d} » est deja le moment {', '.join(porteurs)}"))

        # --- 2. deux moments de la meme trame qui se recouvrent ---
        pris = []
        for e in lot:
            surface, t = lu_par(e, pid)
            if t:
                pris.append((e["id"] + " / " + surface, shingles(t, seuil)))
        for i in range(len(pris)):
            for j in range(i + 1, len(pris)):
                (n1, s1), (n2, s2) = pris[i], pris[j]
                # On ne retient que les suites de mots RARES dans tout le corpus : une suite
                # qui revient partout est une formule d'acte -- << il n a pas ete fait de
                # contrat de mariage >>, << a neuf heures du matin >> -- pas une redite.
                communs = {g for g in (s1 & s2) if FREQ.get(g, 0) <= 2}
                if len(communs) >= 2:
                    ex = max(communs, key=len)
                    signale.append(("redite", f"{n1}  ↔  {n2}",
                                    f"{len(communs)} suite(s) propres de {seuil} mots, "
                                    f"dont « {ex} »"))

        if signale:
            total += len(signale)
            nom = (persons[pid].get("given", "") + " " + persons[pid]["surname"]).strip()
            print(f"\n{pid}  ({nom})")
            for genre, ou, quoi in signale:
                print(f"  [{genre:6}] {ou}")
                print(f"           {quoi}")

    # --- 3. un PRENOM NU dans un texte affiche, personne du corpus derriere ---
    #
    # LE TROU QUE CE DETECTEUR FERME, ET IL A ETE PAYE LE 1er SEPTEMBRE 2026. La photographie
    # de la pyramide disait << un homme que la legende appelle Jacques >>. Le corpus contenait
    # JACQUES KINDE, mari de Jeannine LE PIPE donc beau-frere de Denise, seul Jacques du cercle,
    # et present dans le meme lot de photographies. L'hypothese a ete ecrite dans une `note` --
    # invisible -- et le narratif a garde son prenom nu. C'est le généalogiste qui l'a vu sur la page.
    #
    # La regle invoquee alors etait << ne jamais creer une personne sur une deduction >>. Elle ne
    # s'appliquait pas : IL NE S'AGISSAIT PAS DE CREER, mais de RATTACHER quelqu'un qui existait.
    # Un prenom nu n'est donc pas fautif en soi -- << tante Yvonne >>, << l'oncle Jo >> sont la
    # bonne facon d'ecrire quand la personne est participante. Il l'est quand PERSONNE de ce
    # prenom n'est au moment : la question est ouverte et rien ne la montre.
    prenoms = {}
    for p in persons.values():
        for champ in ("given", "given_usual", "nickname"):
            v = (p.get(champ) or "").strip()
            if v and len(v) > 2:
                prenoms.setdefault(v.split()[0], set()).add(p["id"])
    # CE N'EST PAS LE PRENOM NU QUI SIGNALE, C'EST LA FORMULE QUI AVOUE L'IGNORANCE. Premiere
    # version de ce detecteur : tout prenom du corpus non suivi d'un patronyme, dont aucun
    # porteur n'etait au moment. 241 signalements, illisible -- parce qu'un narratif nomme
    # legitimement des gens qui ne sont pas participants : << seule Germaine en eut >>, << les
    # trois aines de Jean et Denise >>. Mentionner quelqu'un n'oblige pas a en faire un
    # participant. Ce qu'on cherche est plus etroit : le texte qui DIT qu'on ne sait pas qui
    # c'est, alors que le corpus, lui, porte une personne de ce prenom.
    RE_IGNORE = re.compile(
        r"(?:appell?e|appelait|nomm[ée]e?|pr[ée]nomm[ée]e?|du nom de|s'appelle|s'appelait"
        r"|un certain|une certaine)\s+«?\s*([A-ZÉÈÀÎÔ][a-zéèêàçîôïüû]{2,})",
        re.I)
    nus = []
    for e in events:
        au_moment = {q["person"] for q in
                     list(e.get("participants", [])) + list(e.get("participants_extra", []))}
        for surface, t in ([("narrative", e.get("narrative") or "")]
                           + [("narrative_for/" + k, v)
                              for k, v in (e.get("narrative_for") or {}).items()]):
            for mot in set(RE_IGNORE.findall(t)):
                porteurs = prenoms.get(mot)
                if porteurs and not (porteurs & au_moment):
                    nus.append((e["id"], surface, mot, sorted(porteurs)))
                elif not porteurs:
                    # LUCILE CONTRE LUCIE : UNE LETTRE, ET LE DETECTEUR EST PASSE A COTE.
                    # Du 1er au 12 septembre 2026, le bapteme du généalogiste a porte « sa marraine
                    # s'appelle Lucile », avec une note disant qu'elle « attend son nom de
                    # famille » -- alors que LUCIE CEOLIN etait au corpus depuis le
                    # 7 septembre, fille de Severina MIGOT et cousine germaine de son pere.
                    # C'est le trou de Jacques KINDE une troisieme fois, et le detecteur avait
                    # ete ecrit pour ca : il cherchait un porteur du prenom EXACT.
                    #
                    # Un prenom entendu se deforme -- Lucile/Lucie, Jeannine/Jacqueline,
                    # Mathieu/Matthieu -- et c'est justement dans les formules d'ignorance
                    # qu'il se deforme, puisqu'on ne sait pas qui c'est. On cherche donc un
                    # VOISIN A UNE SUBSTITUTION, UN AJOUT OU UN RETRAIT DE LETTRE. Le filtre
                    # reste etroit : seulement quand le prenom exact ne designe PERSONNE.
                    #
                    # DEUX REGLAGES, ET ILS ONT ETE MESURES. ① `mot[0].isupper()` : le
                    # `re.I` du motif annule son propre `[A-Z...]`, si bien que « sans
                    # profession » se lisait comme un prenom et proposait « Santa ». ② UNE
                    # SEULE correction, pas deux : Lucile -> Lucie en vaut exactement une (on
                    # retire un l), tandis que deux laissaient passer « Margot -> Mario ».
                    # Avec ces deux filtres le detecteur rend le seul cas qui compte.
                    if not mot[0].isupper():
                        continue
                    for autre, gens in prenoms.items():
                        a, b = autre.lower(), mot.lower()
                        if a == b or a[:3] != b[:3] or not _proche(a, b, 1):
                            continue
                        nus.append((e["id"], surface, f"{mot} → {autre} ?", sorted(gens)))
    if nus and not cible:
        print(f"\n--- PRENOMS NUS : {len(nus)} texte(s) affiche(s) nomment quelqu'un "
              f"qui n'est pas au moment ---")
        for eid, surface, mot, porteurs in sorted(nus)[:40]:
            qui = ", ".join(porteurs[:3]) + (" …" if len(porteurs) > 3 else "")
            print(f"  {eid} / {surface}")
            print(f"           « {mot} » — au corpus : {qui}")
        if len(nus) > 40:
            print(f"  … et {len(nus) - 40} autres.")
        total += len(nus)

    # ------------------------------------------------------------------- LA PLOMBERIE
    # UN NARRATIF RACONTE UNE VIE, PAS UN DEPOUILLEMENT -- et ce controle-la n'existait
    # QUE COMME UN GREP A TAPER DE MEMOIRE, dans la checklist de la skill `trame-fr` :
    # << chercher `le corpus`, `deux siecles`, `on croyait`, `tenait pour` dans summary,
    # narrative et narrative_for >>. Une verification qu'il faut penser a faire est une
    # verification qu'on oublie : c'est exactement ce que dit CLAUDE.md des points de vue,
    # << relue a chaque session, oubliee a chaque session >>, avant que build.py ne s'en
    # charge. Le 9 septembre 2026, la checklist passee a la main a rendu 34 textes
    # AFFICHES qui racontent le travail au lieu des gens -- << c'est par cette formule que
    # LE CORPUS a appris son existence >>, sur la fiche d'un homme mort en 1882.
    #
    # Ce que les REGISTRES gardent d'une personne se dit ; ce que LE CORPUS savait, croyait
    # ou vient de trouver ne se dit pas -- ca raconte la recherche, et ca perime au premier
    # acte suivant. Sa place est dans `notes` et dans `journal.md`.
    RE_PLOMB = re.compile(
        r"\b(le corpus|du corpus|au corpus|ce corpus"
        r"|deux si[èe]cles?|trois si[èe]cles?"
        r"|on croyait|on pensait jusqu|tenait pour"
        r"|jusqu'ici le|reste [àa] v[ée]rifier|reste [àa] ouvrir)\b", re.I)
    plomb = []
    for pid, p in persons.items():
        for m in set(RE_PLOMB.findall(p.get("summary") or "")):
            plomb.append((pid, "summary", m))
    for e in events:
        for surface, t in ([("narrative", e.get("narrative") or "")]
                           + [("narrative_for/" + k, v)
                              for k, v in (e.get("narrative_for") or {}).items()]):
            for m in set(RE_PLOMB.findall(t)):
                plomb.append((e["id"], surface, m))
    # Et le markdown, tant qu'on y est : la page imprime les asterisques, elle ne les rend
    # pas. L'emphase d'un texte affiche se met en CAPITALES.
    md = []
    for pid, p in persons.items():
        if "**" in (p.get("summary") or "") or "`" in (p.get("summary") or ""):
            md.append((pid, "summary"))
    for e in events:
        for surface, t in ([("narrative", e.get("narrative") or "")]
                           + [("narrative_for/" + k, v)
                              for k, v in (e.get("narrative_for") or {}).items()]):
            if "**" in t or "`" in t:
                md.append((e["id"], surface))
    if (plomb or md) and not cible:
        print(f"\n--- PLOMBERIE DANS UN TEXTE AFFICHE : {len(plomb) + len(md)} "
              f"signalement(s) ---")
        for eid, surface, mot in sorted(plomb)[:40]:
            print(f"  {eid} / {surface}   « {mot} »")
        if len(plomb) > 40:
            print(f"  … et {len(plomb) - 40} autres.")
        for eid, surface in sorted(md):
            print(f"  {eid} / {surface}   markdown (** ou `) — l'emphase se met en CAPITALES")
        total += len(plomb) + len(md)

    # ----------------------------------------------------- LE FRANCAIS DESACCENTUE
    # DE L'ASCII POSE PAR PRUDENCE D'ENCODAGE DANS UN SHELL, ET IL ARRIVE PAR LOTS.
    # CLAUDE.md le decrit depuis aout 2026 -- << Meigne >>, << etait >>, << generation >>,
    # une quarantaine de champs affiches qui detonnaient au milieu d'un corpus accentue.
    # Le defaut a ete corrige a la main ce jour-la, et rien ne l'a empeche de revenir : le
    # 9 septembre 2026, les HUIT moments verses le 16 aout depuis les photographies d'Alfiero
    # portaient encore << ceremonie >>, << Federation >>, << pere >>, << soeur >> sur DIX-NEUF
    # textes affiches, dont la trame des petits-enfants. Le généalogiste les lisait sur la page.
    #
    # La liste est volontairement etroite : uniquement des formes qui n'existent PAS en
    # francais sans leur accent. << cote >> en est exclu -- le corpus s'en sert pour la cote
    # d'un registre --, comme << ou >>, << a >> et << age >>.
    SANS_ACCENT = (
        "ceremonie|federation|annee|annees|banniere|cliche|cliches|diplome|sixieme"
        "|pere|mere|frere|soeur|apres|etait|etaient|etais|deja|tres|premiere|derniere"
        "|decembre|fevrier|meme|etre|tete|chateau|foret|hopital|eglise|ecole|eleve"
        "|generation|general|epouse|epoux|fete|etudiant|militaire?ment|regiment"
        "|numero|dernier?e|precedent?e|celebre|decede|decedee|marie?e|ne?e"
    )
    # Les formes trop courtes ou ambigues sont retirees a la main du motif ci-dessus.
    SANS_ACCENT = "|".join(w for w in SANS_ACCENT.split("|")
                           if w not in ("ne?e", "marie?e", "dernier?e", "precedent?e",
                                        "militaire?ment", "general"))
    RE_ASCII = re.compile(r"\b(" + SANS_ACCENT + r")\b", re.I)
    ascii_fr = []
    for pid, p in persons.items():
        for m in sorted(set(RE_ASCII.findall(p.get("summary") or ""))):
            ascii_fr.append((pid, "summary", m))
    for e in events:
        for surface, t in ([("narrative", e.get("narrative") or "")]
                           + [("narrative_for/" + k, v)
                              for k, v in (e.get("narrative_for") or {}).items()]):
            for m in sorted(set(RE_ASCII.findall(t))):
                ascii_fr.append((e["id"], surface, m))
    if ascii_fr and not cible:
        surfaces = {(a, b) for a, b, _ in ascii_fr}
        print(f"\n--- FRANCAIS DESACCENTUE : {len(surfaces)} texte(s) affiche(s) ---")
        for eid, surface, mot in sorted(ascii_fr)[:40]:
            print(f"  {eid:<40} {surface:<28} « {mot} »")
        if len(ascii_fr) > 40:
            print(f"  … et {len(ascii_fr) - 40} autres occurrences.")
        total += len(surfaces)

    # ------------------------------------ UN FAIT DATE ENFERME DANS LE RESUME
    # LE 14 SEPTEMBRE 2026, PASCAL A OUVERT LA FICHE DE JUAN PABLO BARBERO : le resume
    # portait l'association de 2012 au 620 Quaglia, la societe de la rue Onelli de 2015,
    # le cafe DuCoin, le Ski Club -- et la trame ne portait QUE DEUX NAISSANCES. Sa
    # reaction : << tout est dans le putain de resume >>. La regle existait dans
    # `trame-fr` depuis le 2 septembre -- << un resume presente une vie, il ne recite pas
    # la trame qui suit, et chaque moment cree lui retire du travail >> -- et rien ne la
    # controlait : c'est le schema habituel, une regle sans detecteur s'oublie.
    #
    # LE SIGNAL : une ANNEE ecrite dans le resume qui n'est l'annee d'AUCUN moment de la
    # trame, ni de la naissance, ni de la mort. Deux reglages, mesures sur le corpus :
    # sans seuil, 114 fiches et 154 annees -- illisible, parce qu'un resume cite
    # legitimement l'annee d'un proche (<< son fils naquit en 1857 >>). Avec DEUX annees
    # orphelines ET UNE TRAME DE SIX MOMENTS AU PLUS, il en reste 28 : ce sont les fiches
    # ou le resume RACONTE a la place de la trame.
    resumes = []
    for pid, p in persons.items():
        ans_trame, n_moments = set(), 0
        for e in trames.get(pid, []):
            ans_trame |= {str(v)[:4] for v in (iso(e.get("date")),
                                              (e.get("date") or {}).get("to")) if v}
            n_moments += 1
        for _, d in vitaux.get(pid, []):
            ans_trame.add(str(d)[:4])
            n_moments += 1
        orphelines = sorted(set(RE_AN.findall(p.get("summary") or "")) - ans_trame)
        if len(orphelines) >= 2 and n_moments <= 6:
            resumes.append((pid, orphelines, n_moments))
    if resumes and not cible:
        print(f"\n--- DES FAITS DATES DORMENT DANS UN RESUME : {len(resumes)} fiche(s) ---")
        for pid, orphelines, n in sorted(resumes):
            print(f"  {pid:<34} {n} moment(s), annees du resume absentes de la trame : "
                  f"{', '.join(orphelines)}")
        total += len(resumes)

    # ------------------------------------------------ LES LIENS QUE LA PAGE NE FERA PAS
    # LE 11 SEPTEMBRE 2026, LE MARIAGE DE 1938 NOMMAIT « René DANNEPOND » ET « Georges NEAU »,
    # TOUS DEUX PARTICIPANTS, ET NI L'UN NI L'AUTRE N'ETAIT CLIQUABLE. Le généalogiste l'a vu sur la
    # page. La cause est mecanique : `link()` dans poc/template.html ne pose un lien que si le
    # `given` EXACT du participant figure en mot entier dans le texte. René portait « René
    # Paul », son etat civil complet : le texte disait « René », le lien cherchait « René
    # Paul ». D'ou le partage `given` (le prenom d'usage, celui que la page cherche) /
    # `given_civil` (l'etat civil, qui ne sert qu'a la fiche).
    #
    # CE DETECTEUR REFAIT LE CALCUL DE LA PAGE, DEPUIS LE PATRONYME. Pour chaque « Prénom NOM »
    # d'un texte affiche dont le NOM est celui d'un participant, il verifie que ce participant
    # sera lie. Il part du patronyme ecrit en capitales parce que c'est ainsi que le corpus
    # nomme les gens, et parce que les deux detecteurs de « liens manques » essayes avant
    # celui-ci -- tout prenom du corpus present dans un texte sans son porteur au moment --
    # rendaient 456 puis 1262 signalements : un narratif CITE legitimement des gens qui ne
    # sont pas participants. Celui-ci ne regarde QUE les participants.
    def mots(s):
        return {w for w in nu(s) if len(w) > 2}

    liens = []
    for e in events:
        qs = [q["person"] for q in
              list(e.get("participants", [])) + list(e.get("participants_extra", []))
              if q["person"] in persons]
        for surface, t in ([("narrative", e.get("narrative") or "")]
                           + [("narrative_for/" + k, v)
                              for k, v in (e.get("narrative_for") or {}).items()]):
            lecteur = surface.split("/", 1)[1] if "/" in surface else None
            # comme la page : un prenom n'est pris qu'une fois, par le plus long d'abord
            pris = set()
            lies = set()
            for pid in sorted((x for x in qs if x != lecteur),
                              key=lambda x: -len(persons[x].get("given") or "")):
                g = (persons[pid].get("given") or "").strip()
                if len(g) > 2 and g not in pris and re.search(
                        r"(?<![\wÀ-ÿ])" + re.escape(g) + r"(?![\wÀ-ÿ])", t):
                    pris.add(g)
                    lies.add(pid)
            par_nom = {}
            for pid in qs:
                if pid != lecteur and persons[pid].get("surname"):
                    par_nom.setdefault(persons[pid]["surname"], []).append(pid)
            for nom, porteurs in par_nom.items():
                for m in re.finditer(r"((?:[A-ZÉÈÀÎÔ][\wÀ-ÿ'-]+\s+){1,4})" + re.escape(nom)
                                     + r"(?![\wÀ-ÿ])", t):
                    prenom = m.group(1).strip()
                    # Le texte nomme-t-il son propre lecteur, ou un porteur deja lie ? Alors
                    # ce « Prénom NOM » est pris : la page n'a rien a lier de plus.
                    def noms(pid):
                        p = persons[pid]
                        return (mots(p.get("given")) | mots(p.get("given_civil"))
                                | mots(p.get("given_usual")) | mots(p.get("nickname")))
                    if lecteur and persons[lecteur].get("surname") == nom \
                            and mots(prenom) & noms(lecteur):
                        continue
                    vise = [pid for pid in porteurs if mots(prenom) & noms(pid)]
                    # UN SEUL CAS EST SIGNALE : le prenom ecrit est bien celui d'un participant
                    # de ce nom, et la page ne le liera pas. Un « Prénom NOM » qui ne ressemble
                    # a aucun participant designe quelqu'un d'autre -- un homonyme, un parent
                    # cite -- et le signaler rendait deux fois plus de bruit que de signal.
                    if vise and not any(pid in lies for pid in vise):
                        for pid in vise:
                            liens.append((e["id"], surface, f"{prenom} {nom}", pid,
                                          persons[pid].get("given") or ""))
    liens = sorted(set(liens))
    if liens and not cible:
        print(f"\n--- LIENS QUE LA PAGE NE FERA PAS : {len(liens)} nom(s) de participant "
              f"sans lien ---")
        for eid, surface, ecrit, pid, g in liens[:40]:
            print(f"  {eid} / {surface}")
            print(f"           « {ecrit} » -> {pid}, dont la page cherche « {g} »")
        if len(liens) > 40:
            print(f"  … et {len(liens) - 40} autres.")
        total += len(liens)

    print(f"\n{total} signalement(s). Le script montre, il ne tranche pas : "
          f"une date peut etre legitimement rappelee, deux textes partager une formule, "
          f"un prenom nu designer un homonyme etranger a la famille.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
