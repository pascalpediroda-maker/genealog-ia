# -*- coding: utf-8 -*-
"""Moteur ARKOTHEQUE en HTTP simple — AD49 (Maine-et-Loire), et tout portail
Arkotheque qui n'a pas de WAF.

POURQUOI CE MODULE EXISTE A COTE DE `arkotheque.js`. Le module JavaScript pilote un
Chrome fenetre, ce qui coute une fenetre, une preuve-de-travail et des secondes ; la
plupart des portails Arkotheque n'en demandent pas tant. Une requete Python ordinaire
passe, du referentiel des communes jusqu'au JPEG de 1,2 Mo.

LA FICHE DECIDE, ET ELLE SEULE : `http_simple: true` dans portails.json. Sans ce
drapeau, ce module refuse de servir le portail et renvoie vers le module JavaScript —
un portail derriere un WAF repondrait par du HTML de defi que le code prendrait pour
du JSON, et conclurait a tort qu'un registre est vide.

    ⚠️ CETTE DOCSTRING A MENTI, ET ELLE A COUTE UN NAVIGATEUR OUVERT POUR RIEN. Elle a
    porte jusqu'au 24 septembre 2026 la phrase « l'AD43 et l'AD45 renvoient 403 Attack
    detected a tout client qui n'est pas un vrai navigateur » -- vraie quand elle a ete
    ecrite le 27 aout, fausse depuis que le jeton anti-robot est suivi ici. Le registre,
    lui, disait juste : `"http_simple": true`, verifie le 19 septembre 2026, « 306
    communes, 74 registres pour Blassac ». Une session a lu la docstring, cru l'AD43
    inaccessible sans Chrome, et lance `lire_page.js` pour une page que `_get` sert.
    **LA RECETTE D'UN PORTAIL SE LIT DANS `portails.json`, JAMAIS DANS UN COMMENTAIRE DE
    MODULE** : le registre est tenu a jour par le controle de coherence, une prose ne
    l'est par personne.

    communes(dept)                  -> {libelle: (fiche, nb_registres)}  -- 442 pour l'AD49
    registres(dept, commune)        -> (total, [{cote, type_acte, date, vues, idArkoFile...}])
    numerisation(dept, fiche, idf)  -> (numero, infosImage)  -- le numero ne se devine pas
    telecharge(dept, num, idf, ...) -> les vues sur le disque, v001.jpg, v002.jpg, ...

TROIS PIEGES PAYES LE 27 AOUT 2026, TOUS DEJA CONNUS AILLEURS :

  1. LE JETON ANTI-ROBOT. La premiere requete rend 312 octets de HTML portant
     window.location.href='/redirect_<JETON>/...'. La suivre UNE FOIS pose le cookie
     `bot_mitigation_cookie` ; tout passe ensuite. C'est la recette de l'AD43, et elle
     vaut pour l'API JSON autant que pour les images.
  2. `?size=full` OU L'ON PERD LES DEUX TIERS DE L'IMAGE. Sans lui, l'endpoint plafonne
     a 2000 px sur le grand cote : 2000 x 1418 au lieu de 5496 x 3896. Meme piege qu'en
     Haute-Loire, et il coute bien plus cher ici parce que le master est bien plus grand.
  3. LA RACINE TLS. Le certificat du portail remonte a « ISRG Root YE », une racine
     Let's Encrypt de mai 2026 que le magasin systeme de Windows ne connait pas encore :
     Python leve « certificate has expired » alors que le certificat servi est valide et
     que la chaine se verifie (openssl rend « Verify return code: 0 »). On passe donc
     `cafile=certifi.where()`. Le portail n'y est pour rien — ne pas noter ce piege
     comme une panne du site.
"""
import gzip
import http.client
import http.cookiejar
import html as _h
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

# La verification TLS de cette machine est reparee par `scripts/archives/tls.py` :
# le magasin de racines de Windows porte une racine perimee, et tous ces portails sont
# chez Let's Encrypt. Un import suffit, il agit sur tout le processus.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tls  # noqa: F401,E402

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}
CADENCE = 1.0
CONF = os.path.join(os.path.dirname(__file__), "..", "portails.json")

_sessions = {}


def _contexte():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:            # magasin systeme : peut ne pas connaitre ISRG Root YE
        return ssl.create_default_context()


def fiche(dept):
    """La fiche du portail, ou une erreur qui dit quoi faire."""
    c = json.load(open(CONF, encoding="utf-8"))
    p = next((x for x in c["portails"]
              if x["dept"] == str(dept) and x["moteur"] == "arkotheque"), None)
    if p is None:
        raise SystemExit(f"pas de portail arkotheque pour le departement {dept}")
    if not p.get("http_simple") and not os.environ.get("GENEALOGIA_ESSAYER"):
        # ⚠️ CE GARDE-FOU EMPECHAIT DE DECOUVRIR QU'IL N'AVAIT PLUS LIEU D'ETRE. Il refuse
        # de servir un portail sans le drapeau, pour ne pas prendre une page de defi
        # anti-robot pour du JSON — et c'est juste. Mais du coup PERSONNE NE POUVAIT
        # S'APERCEVOIR QU'UN PORTAIL AVAIT CESSE DE SE DEFENDRE : le 19 septembre 2026, le
        # drapeau etait absent sur HUIT portails sur douze qui, mesure faite, passent tous
        # sans navigateur. Un drapeau pose une fois et jamais remesure devient un mensonge
        # silencieux. Le refus est donc desormais VERIFIABLE : `GENEALOGIA_ESSAYER=1`
        # essaie quand meme et laisse voir ce qui arrive.
        raise SystemExit(
            f"l'AD{dept} n'est pas declare `http_simple` : il se defend contre les clients\n"
            f"qui ne sont pas un navigateur. Passer par moteurs/arkotheque.js (Playwright).\n"
            f"POUR VERIFIER SI C'EST ENCORE VRAI : GENEALOGIA_ESSAYER=1 relance sans le\n"
            f"garde-fou. Si ca passe, poser `http_simple: true` dans la fiche.")
    return p


def _field(p, R):
    """Le champ de visionneuse, et il ne vit pas toujours dans la fiche.

    ⚠️ `numerisation()` et `sources()` levaient `KeyError: 'visionneuse'` des que la fiche
    n'avait pas la cle — l'AD46 par exemple — ALORS QUE CHAQUE LIGNE DE `registres()`
    PORTE LE SIEN, lu dans `refUniqueField`. Preferer le `field` de la ligne est plus juste
    que celui de la fiche : le champ peut varier d'un FONDS a l'autre sur un meme portail.
    Cette fonction n'est donc que le dernier recours, et elle dit quoi faire.
    """
    f = R.get("visionneuse")
    if f:
        return f
    raise SystemExit(
        "la fiche de l'AD%s ne porte pas `recherche.visionneuse`, et aucun `field` n'a ete\n"
        "passe. CHAQUE LIGNE RENDUE PAR `registres()` PORTE LE SIEN, sous la cle `field` :\n"
        "le passer au lieu de compter sur la fiche." % p["dept"])


def _session(p):
    if p["dept"] not in _sessions:
        cj = http.cookiejar.CookieJar()
        _sessions[p["dept"]] = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj),
            urllib.request.HTTPSHandler(context=_contexte()))
    return _sessions[p["dept"]]


def _get(p, url, binaire=False, timeout=90, essais=4):
    """Suit UNE FOIS le jeton anti-robot, puis rend le corps.

    IL REESSAIE, ET CE N'EST PAS DU LUXE. Le 27 aout 2026 au soir, apres environ 350 vues
    tirees dans la soiree, le portail a ferme la connexion sans repondre — un
    `RemoteDisconnected` brut, au milieu d'un lot de 90 vues, et le script est mort sur la
    PREMIERE image en laissant un dossier vide. Un tirage de registre dure plusieurs
    minutes : sur cette duree, une coupure n'est pas un cas rare, c'est le cas normal.
    Quatre essais avec une attente qui double (2, 4, 8 s), et on repose le cookie en
    rouvrant une session quand la connexion a saute — c'est souvent lui que le serveur a
    laisse tomber.
    """
    op = _session(p)
    depart = url
    for essai in range(essais):
        try:
            url = depart
            for _ in range(2):
                r = op.open(urllib.request.Request(url, headers=UA), timeout=timeout)
                b = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    b = gzip.decompress(b)
                if binaire and not b[:200].lstrip().startswith(b"<html"):
                    return b
                t = b.decode("utf-8", "replace")
                m = re.search(r"window\.location\.href='([^']+)'", t)
                if not m:
                    return b if binaire else t
                url = p["base"] + m.group(1) if m.group(1).startswith("/") else m.group(1)
            return b if binaire else t
        except (urllib.error.URLError, http.client.HTTPException, OSError) as e:
            # UN 404 N'EST PAS UNE COUPURE : le reessayer quatre fois ne fait que perdre
            # du temps et masquer la vraie cause, qui est une URL fausse.
            if isinstance(e, urllib.error.HTTPError) and 400 <= e.code < 500:
                raise
            if essai == essais - 1:
                raise
            print(f"  [reseau] {type(e).__name__} — nouvel essai dans {2 ** (essai + 1)} s",
                  file=sys.stderr)
            time.sleep(2 ** (essai + 1))
            _sessions.pop(p["dept"], None)      # le cookie a peut-etre saute avec la connexion
            op = _session(p)


def _moteur(p, params):
    inst = p["recherche"]["instance"]
    q = "&".join(urllib.parse.quote(k, safe="") + "=" + urllib.parse.quote(str(v), safe="")
                 for k, v in params)
    return json.loads(_get(p, p["base"] + p["recherche"]["api"] + "?refUnique="
                           + inst + "&" + q))


# ------------------------------------------------------- le referentiel des communes
def communes(dept):
    """{libelle: (arko_fiche, nb_registres)} — TOUTES les communes, en une requete.

    C'EST LA REPONSE AU PIEGE « UN LIBELLE DE COMMUNE SE LIT, IL NE SE RECONSTRUIT PAS ».
    Ailleurs il a fallu gratter le HTML d'un formulaire, ou renoncer (AD67, dont la
    facette ne se pagine pas). Ici la reponse du moteur porte, SANS AUCUN FILTRE, une
    agregation qui liste les 442 communes du departement avec leur identifiant et leur
    nombre de registres. Rien a deviner, rien a paginer.

    ATTENTION AUX ARTICLES : le portail les rejette en fin de libelle, a la francaise —
    « Ponts-de-Ce (Les) », « Breille-les-Pins (La) », « Meignanne (La) ». Et « Breil »
    n'est pas « Breille-les-Pins (La) » : deux communes distinctes, qu'une recherche
    partielle attrape ensemble.
    """
    p = fiche(dept)
    inst = p["recherche"]["instance"]
    d = _moteur(p, [(inst + "--from", "0"), (inst + "--resultSize", "1")])
    struct = p["recherche"]["structure_commune"]
    ag = d["resultats"]["aggregations"][0][struct][struct + "_terms"]["buckets"]
    out = {}
    for b in ag:
        m = re.match(r"(.*)\[\[(arko_fiche_[0-9a-f]+)\]\]$", b["key"])
        if m:
            out[m.group(1)] = (m.group(2), b["doc_count"])
    return out


# -------------------------------------------------------------- les registres d'une commune
def registres(dept, commune, fiche_commune=None, pas=25):
    """(total, [ligne]) pour une commune. Une ligne porte de quoi telecharger.

    LE PLAFOND DE `resultSize` EST SILENCIEUX, comme a l'AD45 : demander 200 rend 25
    sans erreur. On pagine sur `from` et ON COMPARE LE COMPTE FINAL AU TOTAL ANNONCE —
    c'est ce qui distingue une liste complete d'une liste tronquee qu'on croit complete.
    """
    p = fiche(dept)
    R, inst = p["recherche"], p["recherche"]["instance"]
    if fiche_commune is None:
        C = communes(dept)
        if commune not in C:
            proches = [k for k in C if commune.lower() in k.lower()]
            raise SystemExit(f"commune « {commune} » absente du referentiel."
                             + (f" Proches : {', '.join(proches[:8])}" if proches else
                                " Lister avec : arkotheque.py %s communes" % dept))
        fiche_commune = C[commune][0]
    g = f"{inst}--filtreGroupes[groupes][0]"
    ch = R["champ_commune"]
    tout, debut, total = [], 0, None
    while total is None or debut < total:
        d = _moteur(p, [
            (f"{inst}--ficheFocus", ""), (f"{inst}--filtreGroupes[mode]", "simple"),
            (f"{inst}--filtreGroupes[op]", "AND"), (f"{g}[{ch}][op]", "AND"),
            (f"{g}[{ch}][q][]", f"{commune}[[{fiche_commune}]]"),
            (f"{g}[{ch}][extras][mode]", "select"),
            (f"{inst}--from", str(debut)), (f"{inst}--resultSize", str(pas))])
        r = d["resultats"]
        total = r["total"] if total is None else total
        lot = _lignes(r["html"])
        if not lot:
            break
        tout += lot
        debut += len(lot)
    return total, tout


def _lignes(html):
    """Le tableau de resultats, lu par `data-champ` et non par position de colonne.

    Le HTML d'Arkotheque type ses cellules — data-champ="type_acte", "date",
    "collection". Les lire par leur nom resiste a un ajout de colonne ; les lire par
    leur rang ne resiste a rien.
    """
    out = []
    for bloc in re.split(r'<tr class="resultat_container', html)[1:]:
        r = {}
        for champ, val in re.findall(r'data-champ="([^"]+)"[^>]*>([^<]*)<', bloc):
            r.setdefault(champ, _h.unescape(val).strip())
        # ON LIT LE TYPE DE LA CELLULE, PAS SON NOM -- ET C'EST LA DEUXIEME FOIS QUE
        # CETTE FONCTION CHANGE DE CLE DE LECTURE. Lire par position ne resistait a
        # rien ; lire par `data-champ` resistait a un ajout de colonne mais pas au
        # changement de portail : l'AD24 dit `precision` / `precision2` la ou l'AD43
        # dit `type_acte` / `date`, et l'AD46 dit `ark_fiche_champ_14`, un NUMERO DE
        # CASE qu'aucune liste de synonymes n'aurait devine. Resultat, `registres`
        # rendait 404 lignes de Javerlhac et 2 de Begoux SANS AUCUN LIBELLE : les
        # donnees etaient la, jetees faute d'un nom connu.
        #
        # `data-type-champ`, lui, est renseigne partout et decrit ce que la cellule
        # EST : `relation_fiche` pour le lieu, `cote` pour la cote, `varchar` et
        # `date` pour les colonnes descriptives, dans l'ordre du tableau. Les noms
        # canoniques restent prioritaires quand le portail les emploie.
        types = re.findall(r'data-type-champ="([^"]+)"[^>]*>([^<]*)<', bloc)
        descr = [_h.unescape(v).strip() for t, v in types
                 if t in ("varchar", "date", "texte") and v.strip()]
        for canon, val in (("type_acte", descr[0] if len(descr) > 0 else ""),
                           ("date", descr[1] if len(descr) > 1 else ""),
                           ("collection", descr[2] if len(descr) > 2 else "")):
            if val and not r.get(canon):
                r[canon] = val
        if not r.get("cote"):
            c = [_h.unescape(v).strip() for t, v in types if t == "cote" and v.strip()]
            if c:
                r["cote"] = c[0]
        _rel = [_h.unescape(v).strip() for t, v in types
                if t == "relation_fiche" and v.strip()]
        p = re.findall(r"<p>(?:<strong>)?([^<]+)", bloc)
        r["lieu"] = " / ".join(_h.unescape(x).strip() for x in p[:2])
        if not r["lieu"] and _rel:          # l'AD24 et l'AD46 n'ont pas de <p> ici
            r["lieu"] = _rel[0]
        m = re.search(r'data-visionneuse="([^"]+)"', bloc)
        if m:
            v = json.loads(_h.unescape(m.group(1)))
            r["fiche"] = v.get("refUniqueFiche")
            r["idArkoFile"] = v.get("idArkoFile")
            r["field"] = v.get("refUniqueField")
        mv = re.search(r"\((\d+)\s*images?\)", bloc)
        r["vues"] = int(mv.group(1)) if mv else None
        out.append(r)
    return out


# ------------------------------------------------------- la numerisation, puis les images
def numerisation(dept, fiche_registre, id_arkofile, field=None):
    """(numero, infosImage) — le numero de numerisation ne se DEDUIT pas, il se DEMANDE.

    L'ecart entre le numero de registre et celui de la numerisation a semble constant en
    Haute-Loire (+630, puis +633 : ce n'en etait pas un). On appelle donc
    `visionneuse-infos`, et on LIT le champ `src`, qui porte l'URL complete.

    `infosImage` est le profil IIIF du master : largeur, hauteur, tuiles, ark. C'est lui
    qui dit qu'un registre est en double page — et il varie d'un registre a l'autre,
    donc un echantillon ne vaut pas regle (lecon de l'AD45).
    """
    p = fiche(dept)
    R = p["recherche"]
    field = field or _field(p, R)
    u = (f"{p['base']}/_recherche-api/visionneuse-infos/{R['instance']}/"
         f"{fiche_registre}/{field}/image/{id_arkofile}/0")
    d = json.loads(_get(p, u))
    s = d["medias"][0]["sources"][0]
    m = re.search(r"/show/(\d+)/image/", s["src"])
    return (int(m.group(1)) if m else None), s.get("infosImage", {})


def url_vue(dept, num, id_arkofile, rang):
    """L'URL d'une vue RECONSTRUITE — ne marche que sur un registre d'un seul tenant.

    Garde pour compatibilite ; preferer `sources()`, qui LIT les URL au lieu de les
    fabriquer. Voir l'avertissement de `sources()`.
    """
    p = fiche(dept)
    base = p.get("base_images", p["base"])
    return f"{base}/_recherche-images/show/{num}/image/{id_arkofile}/{rang}?size=full"


def sources(dept, fiche_registre, id_arkofile, field=None, instance=None):
    """[url] de TOUTES les vues du registre, dans l'ordre — lues, pas reconstruites.

    `instance` OUVRE LES AUTRES FONDS DU MEME PORTAIL, et il en faut un. Un service
    d'archives sert plusieurs moteurs Arkotheque sur le meme domaine : l'etat civil, les
    matricules militaires, les recensements, chacun avec son `arko_default_…`. La fiche de
    `portails.json` n'en porte qu'un, celui de l'etat civil ; sans ce parametre, tirer une
    table alphabetique de matricules obligeait a reecrire le telechargement ailleurs — la
    duplication meme que ce dossier existe pour empecher. Le 8 septembre 2026, l'AD24 a
    demande le fonds `2 R` alors que sa fiche ne connait que le fonds d'etat civil.

    LA REPONSE PORTAIT LA LISTE DEPUIS LE PREMIER APPEL, ET JE RECONSTRUISAIS QUAND MEME.
    `visionneuse-infos` rend `medias[0].sources` : une entree par vue, chacune avec son
    `src` complet. Le 27 aout 2026 ce module n'en lisait que la premiere et fabriquait les
    autres en incrementant un rang — ce qui marche tant qu'un registre tient dans UNE
    numerisation, et casse des qu'il n'y tient plus.

    LE REGISTRE BMS 1713-1752 DE MEIGNE L'A MONTRE : 345 vues annoncees, mais la
    numerisation 307279 n'en sert que ONZE. Les rangs 100, 239, 300 rendaient 404, et
    `position` ne changeait rien — parce que le registre est reparti sur TROIS idArkoFile,
    que `metadata.valeurIds` annonce en clair : [74036, 74037, 74038]. Aucune arithmetique
    ne pouvait le deviner ; la liste, elle, le disait.

    C'est le meme piege qu'a l'AD37, ou un registre decoupe en lots faisait planter le
    module Naoned, et la meme lecon que la fiche de ce portail repete deja : LIRE LA
    REPONSE EN ENTIER AVANT DE DEVINER UNE URL.
    """
    p = fiche(dept)
    R = p["recherche"]
    field = field or _field(p, R)
    u = (f"{p['base']}/_recherche-api/visionneuse-infos/{instance or R['instance']}/"
         f"{fiche_registre}/{field}/image/{id_arkofile}/0")
    d = json.loads(_get(p, u))
    # ⛔ LE `src` N'EST PAS TOUJOURS ABSOLU, ET `telecharge()` MOURAIT DESSUS. Mesure le
    # 19 septembre 2026 sur les douze portails Arkotheque : il est RELATIF sur HUIT d'entre
    # eux — 43, 50, 36, 38, 54, 72, 78, 83 — et absolu sur les quatre autres (24, 45, 46,
    # 49), les seuls sur lesquels ce module avait jamais servi. L'erreur etait
    # `ValueError: unknown url type: '/_recherche-images/show/…'`, qu'on lisait comme une
    # panne de portail : c'est ce qui bloquait l'AD50, et non un WAF.
    racine = p.get("base_images") or p["base"]
    out = []
    for s in d["medias"][0]["sources"]:
        src = s.get("src")
        if src:
            src = urllib.parse.urljoin(racine.rstrip("/") + "/", src)
            out.append(src + ("&" if "?" in src else "?") + "size=full")
    return out


def telecharge(dept, num, id_arkofile, dossier, debut=1, fin=None, cadence=CADENCE,
               urls=None):
    """Ecrit v001.jpg ... pour les vues [debut, fin], NUMEROTEES A PARTIR DE 1.

    `urls` est la liste rendue par `sources()`. Quand elle est fournie — et c'est le cas
    nominal depuis le 27 aout 2026 — les adresses sont LUES et non reconstruites, ce qui
    est la seule facon de tirer un registre reparti sur plusieurs numerisations.

    LE RANG DU PORTAIL COMMENCE A 0, LE NOM DE FICHIER A 1. C'est la convention du NAS, et
    `lire/nas.py` la suppose : v001.jpg est la premiere vue. Un decalage d'une unite ici
    fait lire un acte pour un autre trois jours plus tard, sans que rien ne le signale.

    Ne retelecharge jamais un fichier deja present et non tronque, et verifie chaque JPEG
    recu plutot que de decouvrir le probleme au moment de lire.
    """
    p = fiche(dept)
    os.makedirs(dossier, exist_ok=True)
    fin = fin or debut
    if urls is not None and fin > len(urls):
        raise SystemExit(f"le registre n'a que {len(urls)} vues, {fin} demandee")
    faits = []
    for n in range(debut, fin + 1):
        chemin = os.path.join(dossier, "v%03d.jpg" % n)
        faits.append(chemin)
        if os.path.exists(chemin) and os.path.getsize(chemin) > 50_000:
            continue
        u = urls[n - 1] if urls is not None else url_vue(dept, num, id_arkofile, n - 1)
        b = _get(p, u, binaire=True)
        if not _jpeg_entier(b):
            time.sleep(2)
            b = _get(p, u, binaire=True)
            if not _jpeg_entier(b):
                raise SystemExit(f"vue {n} : image tronquee ou absente ({len(b)} octets)")
        open(chemin, "wb").write(b)
        time.sleep(cadence)
    return faits


def _jpeg_entier(b):
    return len(b) > 20_000 and b[:2] == b"\xff\xd8" and b[-2:] == b"\xff\xd9"


# ---------------------------------------------------------------------------- la ligne de commande
def _usage():
    raise SystemExit(
        "usage :\n"
        "  arkotheque.py <dept> communes [motif]\n"
        "  arkotheque.py <dept> registres \"<Commune>\"\n"
        "  arkotheque.py <dept> vues <arko_fiche_...> <idArkoFile>\n"
        "  arkotheque.py <dept> tirer <arko_fiche_...> <idArkoFile> <dossier> [debut] [fin]")


if __name__ == "__main__":
    import sys
    a = sys.argv[1:]
    if len(a) < 2:
        _usage()
    dept, cmd = a[0], a[1]

    if cmd == "communes":
        motif = a[2].lower() if len(a) > 2 else ""
        for k, (f, n) in sorted(communes(dept).items()):
            if motif in k.lower():
                print(f"{n:5d}  {f}  {k}")

    elif cmd == "registres":
        total, regs = registres(dept, a[2])
        print(f"# {a[2]} : {total} annonces, {len(regs)} lus", file=sys.stderr)
        print("\t".join(["lieu", "type", "dates", "collection", "vues", "idArkoFile", "fiche"]))
        for r in regs:
            print("\t".join([r.get("lieu", ""), r.get("type_acte", ""), r.get("date", ""),
                             r.get("collection", ""), str(r.get("vues") or ""),
                             str(r.get("idArkoFile") or ""), r.get("fiche", "")]))

    elif cmd == "vues":
        num, info = numerisation(dept, a[2], int(a[3]))
        print(f"numerisation {num}   master {info.get('width')} x {info.get('height')}"
              f"   ark:{info.get('ark', {}).get('naan')}/{info.get('ark', {}).get('name')}")

    elif cmd == "tirer":
        num, info = numerisation(dept, a[2], int(a[3]))
        us = sources(dept, a[2], int(a[3]))
        d = int(a[5]) if len(a) > 5 else 1
        f = int(a[6]) if len(a) > 6 else len(us)
        print(f"numerisation {num}, master {info.get('width')}x{info.get('height')}, "
              f"{len(us)} vues listees", file=sys.stderr)
        print(len(telecharge(dept, num, int(a[3]), a[4], d, f, urls=us)), "images",
              file=sys.stderr)

    else:
        _usage()
