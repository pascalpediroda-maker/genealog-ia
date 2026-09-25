# -*- coding: utf-8 -*-
"""GALLICA — la bibliotheque numerique de la BnF, par ses API publiques.

CE MODULE EXISTE PARCE QUE CE CODE A ETE ECRIT DEUX FOIS ET PERDU DEUX FOIS. Le
depouillement des cent fascicules de « Listes officielles de prisonniers de guerre » pour
chercher les LE MOUEL, puis la recherche sur les DUPONT : deux scripts jetables, deux
repertoires temporaires de session, deux disparitions. C'est exactement la faute que
`scripts/archives/` existe pour empecher.

CE N'EST PAS UN PORTAIL D'ARCHIVES DEPARTEMENTALES — pas de commune, pas de registre, pas
de cote — ET C'EST POURQUOI IL N'A LONGTEMPS EU AUCUNE FICHE. Il en a une depuis le
18 septembre 2026, sous `dept: null` : un registre qui ignore la moitie des fonds qu'on
interroge ne peut pas servir de controle. Gallica sert a trouver ce
que la PRESSE et les LIVRES ont garde de quelqu'un — un avis de deces, une nomination, un
compte rendu de conges, une necrologie. C'est le complement de l'etat civil, pas son
concurrent.

IL N'Y A PAS DE CAPTCHA SUR LES API. Le « je ne suis pas un robot » que rencontre le généalogiste
est pose par l'interface web, qui rend ses resultats cote client. Les services ci-dessous
sont publics, documentes (https://api.bnf.fr) et repondent a une requete HTTP ordinaire.

    LE PIEGE QUI DECIDE DE TOUT : `all` CONTRE `adj`
    ------------------------------------------------
    L'operateur par defaut du formulaire est `all`. Il decoupe, il lemmatise, il
    « rapproche » — et sur un patronyme il noie tout :

        gallica all "Esperet"   ->  256 566 documents
        gallica adj "Esperet"   ->    1 517 documents

    `adj` est la locution exacte. Dans le formulaire web, c'est la case
    « Recherche exacte », en bas au milieu. TOUJOURS la cocher pour un nom propre.
    Les accents sont ignores : « Esperet » et « Espéret » rendent le meme compte.

    ET METTRE LE PRENOM VAUT MIEUX QUE TOUS LES FILTRES :
        gallica adj "Esperet"          -> 1 517
        gallica adj "Gérard Espéret"   ->    87
        gallica adj "Henri Espéret"    ->     3

    LA PRESSE EST INDEXEE AU TITRE, PAS AU NUMERO. Une recherche SRU sur un journal rend
    « L'Ouest-Eclair, 1912-1944 », pas le numero du 3 mars 1924. Pour descendre au numero,
    il faut enchainer `annees()` + `numeros()` + `dans()` — c'est ce que fait `balaye()`.

    UN ANNUAIRE MILITAIRE SE CHERCHE COMME UN LIVRE, PAS COMME UN JOURNAL — ET C'EST
    BIEN PLUS RAPIDE. Trouve le 7 septembre 2026 pour verifier la carriere d'un officier
    (grade, regiment, affectation) que la famille racontait de troisieme main. `cherche()`
    localise le bon volume (« Annuaire officiel de l'armee francaise ... 1920 »,
    ark bpt6k176447s pour cette annee-la), puis `dans(ark, "Nom")` cherche DANS ce seul
    document — pas besoin de `annees()`/`numeros()`/`balaye()`, un annuaire est un livre
    unique, pas une collection de numeros. Une entree comme :

        p.603  2560 PAIRE (Jean-Régis), capitaine à T. T., 1er mixte de zouaves et tirailleurs

    se lit : `capitaine à T. T.` = capitaine A TITRE TEMPORAIRE, un grade de commandement
    de guerre sans etre encore le grade permanent (le grade permanent, ici lieutenant
    depuis le 1/10/17, se lit sur la liste d'anciennete correspondante). LES ANNUAIRES
    SE SUIVENT ANNEE PAR ANNEE (chercher « Annuaire officiel de l'armée française » +
    l'annee dans `cherche()`) : une serie d'editions successives montre une carriere
    avancer, grade confirme, changement de regiment. LES PETITS SYMBOLES A COTE D'UN NOM
    (etoile, autre glyphe) MARQUENT UNE DECORATION — a verifier sur la legende de l'ouvrage,
    pas a deviner. Un nom SANS symbole dans une edition donnee dit qu'il n'etait pas
    encore decore a cette date, pas qu'il ne l'a jamais ete : verifier une edition
    posterieure.

Les cinq services utilises :

    /SRU                        le catalogue, en CQL
    /services/Issues            les annees d'un titre, puis les numeros d'une annee
    /services/ContentSearch     chercher DANS un document numerise, rend les pages
    /services/Pagination        le nombre de vues et la structure
    /iiif/...                   l'image d'une vue, en IIIF Image API

Ligne de commande :

    python gallica.py cherche "Gérard Espéret"          # le catalogue
    python gallica.py cherche "Espéret" --large         # sans la recherche exacte
    python gallica.py annees cb32798129n                # les annees d'un journal
    python gallica.py numeros cb32798129n 1910          # les numeros d'une annee
    python gallica.py dans bpt6k23529807 "Espéret"      # chercher dans un numero
    python gallica.py balaye cb32798129n "Espéret" 1909 1927   # tout un journal
    python gallica.py page bpt6k23529807 3 sortie.jpg   # tirer une vue
    python gallica.py extrait bpt6k63595492 11 "APPLICATION|anciennet" tete.png
"""
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# La verification TLS de cette machine est reparee par `scripts/archives/tls.py` :
# le magasin de racines de Windows porte une racine perimee, et tous ces portails sont
# chez Let's Encrypt. Un import suffit, il agit sur tout le processus.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tls  # noqa: F401,E402

# NE PAS REASSIGNER sys.stdout AU NIVEAU DU MODULE : ca ferme le flux de l'importateur.
# Deja paye sur ad46.py et ad47.py, puis une troisieme fois sur ce fichier meme.
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
BASE = "https://gallica.bnf.fr"
NS = {"srw": "http://www.loc.gov/zing/srw/", "dc": "http://purl.org/dc/elements/1.1/"}
CADENCE = 0.4          # secondes entre deux appels ; la BnF ne s'en plaint pas
MAX_LU = 1990          # au-dela, l'image est reduite avant lecture — meme seuil que nas.py


def _get(url, essais=4, timeout=90):
    """Un GET qui reessaie : un balayage de journal dure des minutes, et sur cette duree
    une coupure n'est pas un cas rare, c'est le cas normal. Meme lecon qu'Arkotheque."""
    for essai in range(essais):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                       timeout=timeout)
            return r.read()
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500 and e.code != 429:
                raise                       # une URL fausse ne devient pas vraie en 4 essais
            if essai == essais - 1:
                raise
        except Exception:
            if essai == essais - 1:
                raise
        time.sleep(2 ** essai)


# ------------------------------------------------------------------- le catalogue (SRU)
def cherche(termes, exact=True, type_doc=None, annees=None, nb=20, debut=1):
    """Cherche dans le catalogue et le texte integral. Rend (total, [notices], requete).

    `termes` : une chaine ou une liste de chaines qui doivent TOUTES figurer.
    `exact`  : True -> operateur `adj`, la locution exacte. C'est la « recherche exacte »
               du formulaire, et c'est elle qui fait la difference entre 1 517 et 256 566.
    `type_doc` : "fascicule", "monographie", "carte", "image", "manuscrit"...
    `annees` : (debut, fin) sur dc.date.
    """
    if isinstance(termes, str):
        termes = [termes]
    op = "adj" if exact else "all"
    q = " and ".join('gallica %s "%s"' % (op, t) for t in termes if t)
    if type_doc:
        q += ' and dc.type all "%s"' % type_doc
    if annees:
        q += ' and dc.date >= "%s" and dc.date <= "%s"' % (annees[0], annees[1])
    url = ("%s/SRU?operation=searchRetrieve&version=1.2&maximumRecords=%d"
           "&startRecord=%d&query=%s" % (BASE, nb, debut, urllib.parse.quote(q)))
    x = ET.fromstring(_get(url))
    total = int(x.findtext(".//srw:numberOfRecords", default="0", namespaces=NS))
    out = []
    for rec in x.findall(".//srw:record", NS):
        d = {}
        for champ in ("title", "date", "creator", "publisher", "type", "identifier",
                      "description", "language"):
            v = [e.text for e in rec.findall(".//dc:" + champ, NS) if e.text]
            if v:
                d[champ] = v
        ark = [i for i in d.get("identifier", []) if "ark:" in i]
        d["ark"] = ark[0].split("ark:/12148/")[-1] if ark else None
        out.append(d)
    return total, out, q


# ------------------------------------------------------- descendre au numero d'un journal
def annees(ark_titre):
    """Les annees numerisees d'un periodique. `ark_titre` est le cbXXXXXXXX du titre."""
    x = ET.fromstring(_get("%s/services/Issues?ark=ark:/12148/%s/date"
                           % (BASE, ark_titre.replace("/date", ""))))
    return [e.text for e in x.findall(".//year") if e.text], \
           int(x.getroot().get("totalIssues") if hasattr(x, "getroot")
               else x.get("totalIssues") or 0)


def numeros(ark_titre, annee):
    """Les numeros d'une annee : [(ark, libelle)].

    LE PARAMETRE `date` NE MARCHE QU'AVEC L'ARK NU, sans le suffixe `/date` — avec, le
    service a rendu un 500 puis la liste des annees, ce qui est pire qu'une erreur : on
    croit avoir la reponse et on a autre chose.
    """
    a = ark_titre.replace("/date", "")
    x = ET.fromstring(_get("%s/services/Issues?ark=ark:/12148/%s&date=%s"
                           % (BASE, a, annee)))
    return [(e.get("ark"), (e.text or "").strip()) for e in x.findall(".//issue")]


def dans(ark, requete, exact=True):
    """Cherche DANS un document numerise. Rend [(page, extrait)].

    C'est le seul moyen de savoir a quelle page se trouve un nom : le catalogue, lui, ne
    descend pas sous le titre pour la presse.

    LE MEME PIEGE QUE `all` CONTRE `adj`, UN CRAN PLUS BAS — ET IL A FAILLI PASSER.
    ContentSearch racinise aussi. Interroge avec « Espéret » nu, il a rendu 209
    occurrences pour la seule annee 1909 du Journal de la Manche : deux par numero, ce qui
    ressemblait a s'y meprendre au nom de l'imprimeur dans l'ours. C'etaient des
    « esperer », « esperait », « espere ».

        ContentSearch  Espéret     -> 2 sur le numero du 1er janvier 1910
        ContentSearch "Espéret"    -> 0

    LES GUILLEMETS FONT LA LOCUTION EXACTE, et ils ne coutent rien : sur un mot qui figure
    vraiment, « Coutances » et « "Coutances" » rendent tous les deux 60. On les met
    toujours. `exact=False` pour les retirer volontairement.
    """
    if exact and not (requete.startswith('"') and requete.endswith('"')):
        requete = '"%s"' % requete
    url = "%s/services/ContentSearch?ark=ark:/12148/%s&query=%s" % (
        BASE, ark, urllib.parse.quote(requete))
    x = ET.fromstring(_get(url))
    out = []
    for it in x.findall(".//item"):
        p = (it.findtext("p_id") or "").replace("PAG_", "")
        c = it.findtext("content") or ""
        c = re.sub(r"<[^>]+>", "", c)
        c = c.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        c = re.sub(r"&#\d+;", "?", c)
        out.append((p, re.sub(r"\s+", " ", c).strip()))
    return out


def vues(ark):
    """Le nombre de vues d'un document."""
    x = ET.fromstring(_get("%s/services/Pagination?ark=ark:/12148/%s" % (BASE, ark)))
    return int(x.findtext(".//nbVueImages") or 0)


def alto(ark, vue):
    """L'OCR d'une vue en ALTO : [(mot, x, y, largeur, hauteur)], dans l'ordre de lecture.

    NE PAS PASSER PAR `/fN.texteBrut` : ce chemin rend la page WEB de Gallica, menus
    compris, et depuis 2026 il renvoie vers leur captcha « altcha ». On y a lu le menu
    « Hugo, Victor » en croyant lire un journal de 1935. RequestDigitalElement, lui, rend
    l'ALTO brut — le texte ET la position de chaque mot, ce qui permet ensuite de decouper
    l'image juste autour d'un nom.
    """
    b = _get("%s/RequestDigitalElement?O=%s&E=ALTO&Deb=%d" % (BASE, ark, vue))
    # L'ALTO SE DECLARE ISO-8859-1 ET CONTIENT DE L'UTF-8. Le parseur croit l'en-tete et
    # rend « GÃ©rard EspÃ©ret » pour « Gérard Espéret ». On corrige l'en-tete avant de
    # parser : c'est le seul endroit ou le mensonge est reparable proprement.
    b = re.sub(br'encoding="[^"]*"', b'encoding="UTF-8"', b, count=1)
    try:
        x = ET.fromstring(b)
    except ET.ParseError:                    # certains ALTO sont vraiment en latin-1
        x = ET.fromstring(re.sub(br'encoding="[^"]*"', b'encoding="ISO-8859-1"', b, 1))
    out = []
    for s in x.iter():
        if not s.tag.endswith("String"):
            continue
        c = s.get("CONTENT")
        if not c:
            continue
        out.append((c, int(s.get("HPOS") or 0), int(s.get("VPOS") or 0),
                    int(s.get("WIDTH") or 0), int(s.get("HEIGHT") or 0)))
    return out


def texte(ark, vue, largeur=110):
    """Le texte OCR d'une vue, remis en lignes lisibles."""
    mots = alto(ark, vue)
    lignes, courante, y = [], [], None
    for c, hx, vy, w, h in mots:
        if y is None or abs(vy - y) > (h or 20) * 0.6:
            if courante:
                lignes.append(" ".join(courante))
            courante, y = [], vy
        courante.append(c)
    if courante:
        lignes.append(" ".join(courante))
    return "\n".join(lignes)


def situe(ark, vue, motif):
    """Ou se trouve un mot dans la vue : [(mot, x, y, w, h)] pour tout ce qui correspond.

    Sert a decouper l'image autour d'un nom plutot que de lire une pleine page de journal
    a la loupe.
    """
    r = re.compile(motif, re.I)
    return [m for m in alto(ark, vue) if r.search(m[0])]


def image(ark, vue, dest, taille="full"):
    """Tire une vue en IIIF. `taille` : "full", ou "1500," pour 1500 px de large."""
    url = "%s/iiif/ark:/12148/%s/f%d/full/%s/0/native.jpg" % (BASE, ark, vue, taille)
    b = _get(url, timeout=180)
    os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
    io.open(dest, "wb").write(b)
    return dest, len(b)


def extrait(ark, vue, motif, dest, marge=0.04, mini=900):
    """DECOUPE L'IMAGE AUTOUR D'UN MOT — la moitie que `situe()` annoncait sans la faire.

    `situe()` disait depuis le premier jour servir « a decouper l'image autour d'un nom
    plutot que de lire une pleine page de journal a la loupe », et la decoupe n'existait
    pas : chaque session la refaisait a la main en PIL, en recalculant des fractions a
    partir de coordonnees ALTO. C'est la recette dupliquee que `scripts/archives/` existe
    pour empecher.

    POURQUOI IL LE FAUT : une page du « Journal officiel » fait 3 500 x 5 000 px sur
    quatre colonnes. Reduite a 1990 px pour etre lue, le corps de texte tombe sous le seuil
    de lisibilite — et c'est precisement la que se lisent les en-tetes qui donnent son sens
    a une liste de noms. Cadree sur les mots trouves, la meme page se lit d'un coup.

    Rend (dest, boite, [mots]) ; leve ValueError si le motif ne repond pas — un cadrage
    silencieux sur toute la page ferait croire qu'on a lu ce qu'on n'a pas trouve.
    """
    from PIL import Image, ImageOps

    mots = situe(ark, vue, motif)
    if not mots:
        raise ValueError("« %s » ne repond pas sur la vue %d de %s" % (motif, vue, ark))

    tmp = os.path.join(os.path.dirname(os.path.abspath(dest)) or ".",
                       "_%s_f%d.jpg" % (ark, vue))
    if not os.path.exists(tmp):
        image(ark, vue, tmp)
    im = Image.open(tmp)
    L, H = im.size

    x0 = min(m[1] for m in mots)
    y0 = min(m[2] for m in mots)
    x1 = max(m[1] + m[3] for m in mots)
    y1 = max(m[2] + m[4] for m in mots)
    # La marge est prise sur la PAGE, pas sur la boite : une boite de trois mots aurait
    # une marge de rien du tout, et le contexte est justement ce qu'on vient chercher.
    mx, my = int(L * marge), int(H * marge)
    x0, y0 = max(0, x0 - mx), max(0, y0 - my)
    x1, y1 = min(L, x1 + mx), min(H, y1 + my)
    if x1 - x0 < mini:                      # un cadre trop etroit n'aide personne a lire
        c = (x0 + x1) // 2
        x0, x1 = max(0, c - mini // 2), min(L, c + mini // 2)
    if y1 - y0 < mini // 2:
        c = (y0 + y1) // 2
        x = mini // 4
        y0, y1 = max(0, c - x), min(H, c + x)

    coupe = ImageOps.autocontrast(im.crop((x0, y0, x1, y1)).convert("L"))
    # AU-DELA DE 2000 px SUR LE GRAND COTE, L'IMAGE EST REDUITE AVANT LECTURE : agrandir
    # ne rend rien. On ne monte donc pas, on redescend seulement si besoin.
    if max(coupe.size) > MAX_LU:
        r = MAX_LU / float(max(coupe.size))
        coupe = coupe.resize((int(coupe.size[0] * r), int(coupe.size[1] * r)),
                             Image.LANCZOS)
    coupe.save(dest)
    return dest, (x0, y0, x1, y1), [m[0] for m in mots]


# --------------------------------------------------------------- le balayage d'un journal
def balaye(ark_titre, requete, an_debut=None, an_fin=None, journal=None, cadence=CADENCE):
    """Cherche `requete` dans TOUS les numeros d'un periodique, annee par annee.

    Rend une liste de dict : annee, date, ark du numero, page, extrait.
    `journal` : une fonction appelee a chaque annee, pour dire ou on en est.

    UN NEGATIF SE NOTE. Si le balayage ne rend rien, ecrire dans le corpus la plage
    exactement couverte : c'est ce qui evite de la repayer.
    """
    ans, total = annees(ark_titre)
    ans = [a for a in ans
           if (an_debut is None or int(a) >= int(an_debut))
           and (an_fin is None or int(a) <= int(an_fin))]
    trouves = []
    for a in ans:
        nums = numeros(ark_titre, a)
        n_a = 0
        for ark, lib in nums:
            try:
                for page, extrait in dans(ark, requete):
                    trouves.append({"annee": a, "date": lib, "ark": ark,
                                    "page": page, "extrait": extrait})
                    n_a += 1
            except Exception as e:
                trouves.append({"annee": a, "date": lib, "ark": ark, "page": None,
                                "extrait": None, "erreur": "%s" % type(e).__name__})
            time.sleep(cadence)
        if journal:
            journal(a, len(nums), n_a)
    return trouves


# ------------------------------------------------------------------------ ligne de commande
def _usage():
    print(__doc__.split("Ligne de commande :")[1].strip())


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    a = sys.argv[1:]
    if not a:
        _usage()
        sys.exit(0)
    cmd = a[0]

    if cmd == "cherche":
        exact = "--large" not in a
        mots = [x for x in a[1:] if not x.startswith("--")]
        total, res, q = cherche(mots, exact=exact, nb=30)
        print("requête : %s\n%d document(s)\n" % (q, total))
        for d in res:
            print("  %-11s %-66s %s" % ((d.get("date") or [""])[0][:11],
                                        (d.get("title") or [""])[0][:66], d.get("ark") or ""))

    elif cmd == "annees":
        ans, total = annees(a[1])
        print("%s : %d numéros, %d années — %s à %s"
              % (a[1], total, len(ans), ans[0] if ans else "?", ans[-1] if ans else "?"))

    elif cmd == "numeros":
        for ark, lib in numeros(a[1], a[2]):
            print("  %-16s %s" % (ark, lib))

    elif cmd == "dans":
        r = dans(a[1], a[2])
        print("%d occurrence(s)" % len(r))
        for p, e in r:
            print("  p.%-4s %s" % (p, e[:150]))

    elif cmd == "balaye":
        deb, fin = (a[3], a[4]) if len(a) > 4 else (None, None)
        def dire(an, n, t):
            print("  %s : %3d numéros, %d occurrence(s)" % (an, n, t), flush=True)
        r = balaye(a[1], a[2], deb, fin, journal=dire)
        ok = [x for x in r if x.get("page")]
        print("\n%d occurrence(s) retenue(s)" % len(ok))
        for x in ok:
            print("  %-22s p.%-4s %-16s %s"
                  % (x["date"], x["page"], x["ark"], (x["extrait"] or "")[:110]))
        # ⛔ LE NOM DE SORTIE ETAIT CODE EN DUR, ET IL L'ETAIT DEUX FOIS DE TROP.
        # ① DEUX BALAYAGES EN PARALLELE S'ECRASAIENT L'UN L'AUTRE, en silence : on lance
        #    trois journaux d'affilee pour gagner du temps, et il ne reste que le dernier.
        # ② ET LE FICHIER TOMBAIT A LA RACINE DU DEPOT, ou il n'a rien a faire -- meme
        #    famille que les dumps `*-derniere-recherche.*` des moteurs, ecartes la veille.
        # `--out` le nomme ; le defaut garde l'ancien comportement pour qui l'appelait.
        i = sys.argv.index("--out") if "--out" in sys.argv else -1
        dest = sys.argv[i + 1] if i > 0 else "gallica_balayage.json"
        io.open(dest, "w", encoding="utf-8").write(
            json.dumps(r, ensure_ascii=False, indent=1))
        print("\n-> " + dest)

    elif cmd == "page":
        d, n = image(a[1], int(a[2]), a[3])
        print("%s (%d octets)" % (d, n))

    elif cmd == "extrait":
        d, boite, mots = extrait(a[1], int(a[2]), a[3], a[4])
        print("%s\n  boîte %s\n  sur : %s" % (d, boite, ", ".join(mots[:12])))

    else:
        _usage()
