"""
Prepare les portraits pour la page : extrait les quatre visages encore prisonniers
du poster scanne, charge les photos de la base Heredis, et ecrit un fichier de
vignettes encodees en base64 (la page publiee ne peut lire aucun fichier local).

  python scripts/build_media.py
"""
import json, io, os, base64, sys
from PIL import Image, ImageOps
import fitz
import config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Le poster de ce correspondant a rejoint le NAS le 26 aout 2026 avec le reste des images :
# le depot ne porte plus une seule photographie, seulement les donnees qui les citent.
PDF = os.path.join(config.archives(), "_corpus", "documents-famille",
                   "arbre-genealogique.pdf")
# ⚠️ LE POSTER A DEMENAGE LE 20 SEPTEMBRE 2026, de `_corpus/` a `_corpus/documents-famille/`,
# ou il est a sa place : la convention du dossier range la les livrets et les carnets. Le
# build a REFUSE DE PUBLIER, ce qui est exactement son role -- il aurait pu servir une page
# amputee du poster sans le dire, comme le 26 aout ou un orage avait demonte S:.
# UN SECOND CORPUS N'A NI CE POSTER NI CES QUATRE VISAGES, et il n'en a pas besoin :
# le decoupage du poster est propre a la famille PAIRE, l'encodage des medias cites
# ne l'est pas. GENEALOGIA_DATA fait donc DEUX choses ici — il deplace le corpus lu
# ET il eteint l'etape du poster. Sans lui, rien ne change.
D = os.environ.get("GENEALOGIA_DATA") or os.path.join(ROOT, "data")
# LA SORTIE NE SE RESOUT PLUS SEULE. Un GENEALOGIA_DATA pose sans GENEALOGIA_MEDIA
# ecrivait les medias d'un corpus dans le media.json d'un autre, en silence.
# `corpus_io.sortie()` refuse cet attelage AVANT tout travail -- voir ce module.
import corpus_io as _garde
OUT =_garde.sortie("GENEALOGIA_MEDIA", os.path.join(ROOT, "poc", "media.json"))
POSTER = not os.environ.get("GENEALOGIA_DATA")

# CE SCRIPT NE TOURNE PLUS SANS LE NAS, ET IL DOIT LE DIRE AVANT DE RIEN FAIRE.
# Les 237 images du corpus vivent toutes sur X: et S: depuis ce jour-la. Sans les
# disques montes, `os.path.exists` rendait faux partout, chaque media etait saute
# en silence, et le script finissait par ecrire un media.json vide en annoncant
# « 0 portraits » d'un ton neutre -- que build_all.py aurait pris pour un succes,
# avant de publier une page sans une seule image. Meme raison que le garde-fou de
# build_all.py : une etape qui echoue en silence est pire qu'une etape qui manque.
if POSTER and not os.path.exists(PDF):
    sys.exit(f"Le poster est introuvable :\n  {PDF}\n\n"
             "Les images du corpus sont sur le NAS (X: et S:). Si les lecteurs ne sont "
             "pas montes,\nrien ne sera regenere -- monte-les et relance. "
             "`--rapide` saute cette etape si tu n'as\nbesoin que des donnees.")
TAILLE = 260          # cote long de la vignette
QUALITE = 74

# Zones des quatre blocs a portrait, relevees a la main sur le scan.
# `repli` = fractions (x0, y0, x1, y1) de la photo dans le bloc redresse, pour les
# deux blocs les plus flous du scan, ou la detection automatique echoue.
BLOCS = {
    "paire-jean-regis-celestin": (1, (408, 670, 545, 775), None),
    "bariteau-germaine-adrienne": (1, (421, -2, 546, 59), (.27, .47, .80, .81)),
    "le-pipe-joseph-marie": (2, (444, 129, 567, 201), (.30, .53, .78, .88)),
    "antignac-jeanne": (3, (447, 262, 566, 372), None),
}

doc = fitz.open(PDF) if POSTER else None
_native = {}


def page_native(n):
    if n not in _native:
        p = doc[n - 1]
        info = doc.extract_image(p.get_images(full=True)[0][0])
        img = Image.open(io.BytesIO(info["image"]))
        _native[n] = (img, img.width / p.rect.width, img.height / p.rect.height)
    return _native[n]


def ouvre(m):
    """Charge le fichier d'une entree `media`, en appliquant son `crop` s'il en a un.

    Une photographie de famille est rarement un portrait : l'homme au beret marche au
    milieu d'une rue, le visage occupe un vingtieme de l'image, et la vignette de 260 px
    ne montrerait qu'une silhouette. `crop` est un cadrage en fractions (x0, y0, x1, y1)
    releve a la main -- on garde le fichier d'origine intact et le cadrage dans la donnee.
    """
    img = ImageOps.exif_transpose(Image.open(m["source_file"])).convert("RGB")
    # `rotate` : certains scans sont couches dans un fichier portrait, SANS balise EXIF
    # d'orientation -- exif_transpose ne peut alors rien redresser. L'angle est en degres,
    # sens trigonometrique (90 = quart de tour a gauche), et s'applique AVANT le cadrage
    # pour que les fractions de `crop` se lisent sur l'image droite.
    r = m.get("rotate")
    if r:
        img = img.rotate(r, expand=True)
    c = m.get("crop")
    if c:
        w, h = img.size
        img = img.crop((int(c[0] * w), int(c[1] * h), int(c[2] * w), int(c[3] * h)))
    return img


def vignette(img):
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((TAILLE, TAILLE), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=QUALITE, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


media = {}

def trouve_photo(bloc):
    """Isole la photographie dans un bloc de l'arbre.

    Le bloc contient, de haut en bas : du texte noir sur blanc, la photo, puis le
    cadre dore. On cherche la plus grande bande contigue de lignes « photographiques » :
    beaucoup de gris moyens (un visage), peu de blanc pur (le fond du bloc) et pas de
    dore (le cadre). Detecter le contenu vaut mieux que fixer un pourcentage : les
    quatre blocs n'ont ni la meme taille ni la meme mise en page.
    """
    px = bloc.convert("RGB")
    W, H = px.size
    lignes = []
    for y in range(H):
        gris = dore = clair = 0
        for x in range(0, W, 2):
            r, v, b = px.getpixel((x, y))
            if r - b > 40 and r > 105:
                dore += 1
            elif r > 215 and v > 215 and b > 215:
                clair += 1
            else:
                gris += 1
        n = len(range(0, W, 2))
        lignes.append(dore / n < .10 and gris / n > .18)
    best = cur = (0, 0)
    for y, ok in enumerate(lignes + [False]):
        if ok:
            cur = (cur[0] or y, y)
        else:
            if cur[1] - cur[0] > best[1] - best[0]:
                best = cur
            cur = (0, 0)
    y0, y1 = best
    if y1 - y0 < H * .10:
        return None
    bande = px.crop((0, y0, W, y1 + 1))
    # meme critere applique aux colonnes : le cadre dore borde la photo des deux cotes
    bw, bh = bande.size
    cols = []
    for x in range(bw):
        gris = dore = 0
        for y in range(0, bh, 2):
            r, v, b = bande.getpixel((x, y))
            if r - b > 40 and r > 105:
                dore += 1
            elif not (r > 215 and v > 215 and b > 215):
                gris += 1
        n = len(range(0, bh, 2))
        cols.append(dore / n < .10 and gris / n > .30)
    dedans = [x for x, ok in enumerate(cols) if ok]
    if dedans:
        bande = bande.crop((max(0, dedans[0] - 1), 0, min(bw, dedans[-1] + 2), bh))
    return bande


# --- les quatre visages du poster -----------------------------------------
for pid, (page, (x0, y0, x1, y1), repli) in (BLOCS if POSTER else {}).items():
    img, sx, sy = page_native(page)
    box = (max(0, int(x0 * sx)), max(0, int(y0 * sy)),
           min(img.width, int(x1 * sx)), min(img.height, int(y1 * sy)))
    bloc = img.crop(box).rotate(-90, expand=True)      # redresse : texte en haut
    photo, comment = (None, "") if repli else (trouve_photo(bloc), "détecté")
    if photo is None and repli:
        w, h = bloc.size
        photo = bloc.crop((int(repli[0] * w), int(repli[1] * h),
                           int(repli[2] * w), int(repli[3] * h)))
        comment = "cadrage manuel"
    if photo is None:
        print(f"  [!] {pid} : aucune photo isolee", file=sys.stderr)
        continue
    media[pid] = {"img": vignette(photo), "src": "poster scanné"}
    print(f"  {pid:<32} poster, {comment} ({photo.width}x{photo.height})")

# Tout `source_file` cite par le corpus et absent du disque atterrit ici. La liste
# est relue a la fin : un media saute ne doit pas se deviner en comparant deux
# chiffres d'un build a l'autre.
introuvables = []

# --- les photos de la base Heredis ----------------------------------------
persons = json.load(io.open(os.path.join(D, "persons.json"), encoding="utf-8"))["persons"]
for p in persons:
    dispo = []
    for m in p.get("media", []):
        if not m.get("source_file"):
            continue
        if os.path.exists(m["source_file"]):
            dispo.append(m)
        else:
            introuvables.append((p["id"], m["source_file"]))
    if not dispo:
        continue
    # `type` decide, pas l'ordre de la liste. Les medias d'une personne sont ranges
    # chronologiquement, si bien qu'une photo ajoutee plus tard mais prise plus tot
    # passait en tete et devenait sa vignette : la communion de Denise a remplace son
    # portrait d'atelier sans que personne l'ait demande. Un `portrait` est cadre sur
    # un visage, une `photo` est une scene -- a 260 px, l'un se lit et l'autre non.
    m = next((x for x in dispo if x.get("type") == "portrait"), dispo[0])
    # Une vraie photographie l'emporte toujours sur un visage detoure du poster,
    # qui n'est qu'un pis-aller a 600 dpi dans un scan flou.
    if p["id"] in media and media[p["id"]]["src"] != "poster scanné":
        continue
    try:
        media[p["id"]] = {"img": vignette(ouvre(m)),
                          "src": m.get("note") or "collection de famille"}
        print(f"  {p['id']:<32} {os.path.basename(m['source_file'])}")
    except Exception as e:
        print(f"  [!] {p['id']} : {e}", file=sys.stderr)

# --- les photos rattachees a un evenement ---------------------------------
# Deux tailles : une vignette pour la trame, une version large pour l'agrandissement.
#
# UN ACTE N'EST PAS UNE PHOTOGRAPHIE, ET LE PIPELINE LES CONFONDAIT. Le 18 aout
# 2026, treize actes de Saint-Pal sont entres au corpus et la page a saute le
# plafond de 16 Mo de l'artefact : les documents pesaient 9,5 Mo a eux seuls,
# plus que toutes les photos de famille reunies. Une page manuscrite est le pire
# cas du JPEG -- que du detail haute frequence, aucune zone lisse -- et on la
# stockait en couleur, a la qualite d'une photo de mariage.
#
# Un acte est en NIVEAUX DE GRIS par nature : le passer en "L" supprime les deux
# plans de chrominance, qui ne portaient que du bruit de scan. La qualite peut
# descendre bien plus bas que sur un visage, l'oeil ne lisant ici que des traits.
# CE QU'ON GAGNE EN OCTETS, ON LE REMET EN PIXELS : 1500 px de large au lieu de
# 1150, ce qui est ce qui compte pour dechiffrer une main de 1711.
# ET LE FORMAT COMPTE PLUS QUE LA QUALITE. Le JPEG a ete concu pour des scenes
# naturelles ; sur une page manuscrite -- que des traits, aucune zone lisse -- il
# depense ses octets en artefacts de sonnerie autour de chaque jambage. LE WEBP
# tient la meme lisibilite pour un tiers de moins, et il est lu partout depuis
# des annees. Les cinquante-trois documents du corpus passaient de 8,9 Mo a
# 5,7 Mo le 18 aout 2026, ce qui a ramene la page sous le plafond de 16 Mo de
# l'artefact SANS RIEN PERDRE : on gagne meme 350 px de large.
#
# ET LES PHOTOGRAPHIES ONT SUIVI LE 25 AOUT 2026, ce que la version precedente de
# ce commentaire ecartait d'une phrase -- « les photographies, elles, restent en
# JPEG, c'est leur cas d'usage ». L'argument etait vrai et hors sujet : il disait
# pourquoi le WEBP est MEILLEUR sur du trait, pas pourquoi il serait MOINS BON sur
# un visage. Vingt-deux photographies scannees par une cousine ont porte la page a
# 18,0 Mo, deux megaoctets au-dessus du plafond, et les photos pesaient alors
# 8,2 Mo contre 7,0 aux actes -- le rapport de 2024 s'etait inverse sans que
# personne le regarde. Mesure faite sur les soixante-deux photographies du corpus,
# A RESOLUTION ET A QUALITE INCHANGEES (1150 px, q78) : 6,0 Mo en JPEG, 3,4 Mo en
# WEBP. La page retombe a 14,6 Mo. On ne descend pas la qualite, on change de
# format -- et cette fois il reste de la marge pour le prochain lot.
# Q_PHOTO EST DESCENDU DE 78 A 73 LE 27 AOUT 2026 AU SOIR, ET C'EST LE BON LEVIER
# CETTE FOIS. L'ouverture de l'import Heredis aux cousins germains a fait entrer
# 72 images d'un coup, et la page est repassee a 16,08 Mio contre 16,00 de plafond.
# LE REFLEXE AURAIT ETE DE REDESCENDRE Q_DOC : il est a bout de course a 21, le
# commentaire ci-dessous le dit, et surtout CE NE SONT PAS LES ACTES QUI ONT GROSSI.
# Mesure du soir sur `media.json` : 101 portraits pour 0,89 Mio, 310 medias
# d'evenements pour 13,99 Mio -- et le lot neuf est du cote des PHOTOGRAPHIES.
# On rogne donc la ou le poids est arrive. A 1150 px, sur des tirages de famille
# deja scannes, cinq crans de WEBP jouent sur le grain du fond, pas sur les visages ;
# c'est le contraire d'un acte, ou le meme cran mange une deliee. IL RESTE DE LA
# MARGE ICI : q65 rendrait encore plusieurs centaines de kilo-octets avant que ca
# se voie.
# Q_PHOTO EST DESCENDU DE 73 A 68 LE 31 AOUT 2026, ET C'EST LA MARGE ANNONCEE
# CI-DESSUS QU'ON PREND. Deux photographies d'un même parent -- 104 Ko a elles
# deux -- ont porte la page a 16,09 Mio et la publication a ete REFUSEE : « too
# large: 17MB (max 16MB) ». Ce ne sont pas ces deux images qui debordent, la page
# etait deja a 16,08 le 27 au soir : c'est le lot Heredis qui a rempli le budget,
# et le moindre ajout passe desormais par la.
# ON NE TOUCHE NI A GRAND_PHOTO NI A Q_DOC. Le premier parce que 1150 px est ce
# qui rend un visage lisible en plein ecran ; le second parce qu'a 21 il est a
# bout de course et que ce ne sont toujours pas les actes qui ont grossi.
# Q_PHOTO DESCEND DE 68 A 64 LE 1er SEPTEMBRE 2026 AU SOIR, et c'est le meme geste qu'a
# midi : la page etait a 16,021 Mio pour 16,000 de plafond -- vingt-deux mille octets de
# trop, pour une soiree qui n'a ajoute AUCUNE image. Ce sont les textes qui ont grossi.
# q65 etait annonce comme le fond de la marge par le commentaire d'origine ; on y est, et
# le prochain ajout demandera autre chose que ce levier-ci.
GRAND_PHOTO, Q_PHOTO = 1150, 64
# Q_DOC EST DESCENDU DE 68 A 58 LE 18 AOUT 2026, quand deux actes de plus ont
# remis la page a 16,02 Mo -- vingt kilo-octets au-dessus du plafond. Sur du
# trait en niveaux de gris, l'ecart ne se voit pas ; sur une photographie il se
# verrait tout de suite, et c'est pourquoi les deux chemins restent separes : le
# document perd ses couleurs et gagne des pixels, la photo garde les siennes.
# Q_DOC EST DESCENDU DE 50 A 28 LE 26 AOUT 2026, quand NEUF ACTES d'Indre-et-Loire
# sont entres d'un coup et ont porte la page a 19,0 Mo. Sur du trait en niveaux de
# gris, l'ecart entre 50 et 28 ne se voit pas a l'ecran ; les 1500 px de large, eux,
# sont ce qui permet de lire une main de 1881, et ils ne bougent pas.
# Q_DOC EST DESCENDU DE 28 A 22 LE 26 AOUT 2026 AU SOIR, quand les quatre actes qui
# font remonter la branche CHASLE de deux generations ont porte la page a 16,4 Mo.
# ET LA NOTE DE DETTE TECHNIQUE SE TROMPAIT : elle annoncait, mesure a l'appui, que
# descendre sous 28 « ne rendrait que 0,6 Mo » et que « l'ecriture commencerait a
# souffrir ». Mesure refaite sur les 77 documents : 7 774 Ko a q28, 7 280 a q25,
# 6 804 a q22 -- soit 971 Ko, pas 600. Et l'ecriture ne souffre pas : la ligne de
# filiation de l'acte de 1870, agrandie DEUX FOIS la taille d'affichage, est
# indiscernable entre q28 et q22. Sur du trait en niveaux de gris a 1500 px, ce
# reglage n'agit presque que sur le grain du papier.
# Q_DOC EST DESCENDU DE 22 A 21 LE 27 AOUT 2026 AU SOIR, pour 65 kilo-octets. La
# page etait a 16,06 Mio contre 16,00 de plafond -- 0,4 % de trop -- apres une
# soiree ou six actes angevins sont entres et ou une autre session a verse la
# branche italienne. ECARTER UN DOCUMENT AURAIT ETE DISPROPORTIONNE pour cet
# ecart-la : un cran de qualite sur du trait en niveaux de gris ne se voit pas,
# retirer un acte se voit toujours.
# SI LA PAGE REDEPASSE : ce levier-ci est A BOUT DE COURSE, pour de bon. q18
# rendrait encore ~400 Ko et le grain commencerait a manger les deliees. La suite
# n'est plus un reglage : c'est `embarque: false` document par document, nommement,
# comme le généalogiste l'a tranche le 27 aout -- ou sortir les images du HTML, voir
# `journal.md`, section Dette technique.
GRAND_DOC, Q_DOC = 1500, 21


def grand(img, doc=False):
    img = img.copy()
    if doc:
        # un acte est en niveaux de gris par nature : les deux plans de
        # chrominance ne portaient que du bruit de scan.
        img = img.convert("L")
        img.thumbnail((GRAND_DOC, GRAND_DOC), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "WEBP", quality=Q_DOC, method=6)
        return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    img.thumbnail((GRAND_PHOTO, GRAND_PHOTO), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=Q_PHOTO, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


ev_media = {}
absents, ecartes = [], []
events = json.load(io.open(os.path.join(D, "events.json"), encoding="utf-8"))["events"]
for ev in events:
    for m in ev.get("media", []):
        chemin = m.get("source_file")
        if not chemin:
            continue                       # les quatre portraits tires du poster n'en ont pas
        if not os.path.exists(chemin):
            absents.append((ev["id"], chemin))
            continue
        # `embarque: false` — LE DOCUMENT EXISTE, IL N'EST PAS DANS LA PAGE, ET C'EST
        # DELIBERE. Le plafond de 16 Mo de l'artefact ne laisse plus la place a chaque
        # acte lu ; plutot que de baisser encore la qualite de TOUS les documents pour
        # loger les derniers, on en ecarte quelques-uns nommement. Le `source_file` reste
        # dans le corpus : la piece est citee, datee, transcrite dans sa source, et
        # rangee sur le NAS -- seule l'image ne voyage pas. Decide par le généalogiste le
        # 27 aout 2026 : « tu peux ne pas mettre les actes nouveaux, trace juste qu'ils
        # n'y sont pas ». Le compte est affiche en fin de build.
        if m.get("embarque") is False:
            ecartes.append((ev["id"], chemin))
            continue
        try:
            img = ouvre(m)
            doc = m.get("type") == "document"
            ev_media.setdefault(ev["id"], []).append({
                "vignette": vignette(img),
                "grand": grand(img, doc),
                "legende": m.get("note") or ""})
            print(f"  événement {ev['id']:<30} {os.path.basename(chemin)}")
        except Exception as ex:
            print(f"  [!] {ev['id']} : {ex}", file=sys.stderr)

# UN MEDIA QUI MANQUE DOIT LE DIRE, ET AU-DELA D'UN SEUIL DOIT ARRETER LE BUILD.
# Le garde-fou du haut ne protege qu'un disque : il verifie le poster, donc X:. Le
# 26 aout 2026 au soir, S: n'etait pas monte apres un orage -- 121 medias sur 241 ont
# ete sautes UN PAR UN SANS UN MOT, la page est passee de 15,7 a 10,6 Mo, et rien dans
# la sortie ne le disait. Cinq megaoctets de photographies de famille auraient ete
# publies en moins si personne n'avait mesure. Meme raison que le garde-fou du poster :
# une etape qui echoue en silence est pire qu'une etape qui manque.
if absents:
    import collections
    par_racine = collections.Counter(c[:2].upper() if c[1:2] == ":" else "?" for _, c in absents)
    print(f"\n  [!] {len(absents)} medias introuvables : "
          + ", ".join(f"{n} sur {r}" for r, n in par_racine.most_common()), file=sys.stderr)
    for eid, c in absents[:5]:
        print(f"      {eid} -> {c}", file=sys.stderr)
    if len(absents) > 5:
        print(f"      ... et {len(absents) - 5} autres", file=sys.stderr)
    if len(absents) > 0.05 * (len(absents) + sum(len(v) for v in ev_media.values())):
        sys.exit("\nPLUS DE 5 % DES MEDIAS MANQUENT : media.json N'EST PAS ECRIT.\n"
                 "Un disque n'est probablement pas monte. Monte-le et relance ; "
                 "`--rapide` saute cette etape\nsi tu n'as besoin que des donnees.")

json.dump({"portraits": media, "evenements": ev_media},
          io.open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
poids = os.path.getsize(OUT) // 1024
n_ev = sum(len(v) for v in ev_media.values())
print(f"\n{len(media)} portraits, {n_ev} photos d'événements -> {OUT} ({poids} Ko)")

# LA TRACE DE CE QU'ON N'A PAS MIS, ET ELLE EST AUSSI IMPORTANTE QUE LE RESTE.
# Un document ecarte existe : il est sur le NAS, cite, date et transcrit dans sa source.
# Seule son image ne voyage pas, faute de place sous le plafond de 16 Mo de l'artefact.
# Sans cette liste, la difference entre « pas encore trouve » et « trouve mais pas
# montre » se perdrait au premier build suivant.
if ecartes:
    print(f"  {len(ecartes)} documents ÉCARTÉS À DESSEIN (`embarque: false`) — ils sont sur le "
          f"NAS et le corpus\n  les cite, mais la page ne les embarque pas :")
    for eid, c in ecartes:
        print(f"      {eid:<34} {os.path.basename(c)}")
