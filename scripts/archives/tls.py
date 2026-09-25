# -*- coding: utf-8 -*-
"""RÉPARE LA VÉRIFICATION TLS DE CETTE MACHINE — à importer, rien d'autre à faire.

    import tls   # en tête d'un module qui fait du HTTPS

POURQUOI CE FICHIER EXISTE, ET C'ÉTAIT UN FAUX DIAGNOSTIC RÉPÉTÉ QUATRE FOIS.

Le carnet des portails accusait les sites, un par un : « le magasin de certificats de la machine
refuse `francearchives.gouv.fr` **et** `culture.gouv.fr` » (7 septembre 2026), puis « le
certificat TLS de matchID a expiré » (12 septembre), puis « l'API de Wikipédia ne répond pas »
(18 septembre), puis `data.gouv.fr` le même jour. **Quatre fiches, quatre coupables, une seule
cause** : le magasin de racines que Windows sert à Python porte une racine périmée, et les quatre
sites sont chez Let's Encrypt. Mesuré le 18 septembre 2026 :

    contexte par défaut (magasin Windows)   fr.wikipedia.org  KO   data.gouv.fr  KO
                                            francearchives    KO   culture.gouv  KO
    contexte certifi                        les quatre        OK
    truststore (vérificateur Windows)       les quatre        OK

**ET LA RÉPARATION QU'ON AVAIT FAITE ÉTAIT PIRE QUE LE MAL** : désactiver la vérification
(`CERT_NONE`), écrit deux fois dans le dossier « c'est de la lecture seule sur un portail
public ». C'est une raison, ce n'est pas une bonne : on lit alors n'importe qui sans le savoir,
et on prend l'habitude. **Un certificat qui ne se vérifie pas est un problème à corriger, pas à
contourner.**

CE QUE CE MODULE FAIT, DANS CET ORDRE :

1. `truststore` s'il est là — il délègue au vérificateur de Windows, qui sait aller chercher une
   racine manquante. C'est le plus proche de ce que fait un navigateur, et il ne périme pas.
2. Sinon `certifi`, dont le paquet se met à jour.
3. Sinon il ne fait rien et le dit une fois, sans casser l'appelant.

Il agit **sur tout le processus** : `ssl.create_default_context()` est remplacé, donc `urllib`,
`http.client` et tout ce qui passe par là en profitent sans être modifiés.

⚠️ **ET ÇA SE VÉRIFIE, PARCE QUE ÇA SE REPÉRIME.** `certifi` est un fichier figé : il vieillit
comme le magasin de Windows a vieilli. Une racine qui expire dans six mois rendra les mêmes
`CERTIFICATE_VERIFY_FAILED`, et la session qui les verra accusera le site — c'est exactement ce
qui s'est passé quatre fois. **La contre-mesure est une commande, pas une intention :**

    python scripts/archives/tls.py              # quatre sites témoins, OK ou KO
    python scripts/archives/tls.py reparer      # met certifi et truststore a jour, puis verifie

À lancer **dès qu'un `CERTIFICATE_VERIFY_FAILED` apparaît, avant d'écrire quoi que ce soit sur le
site**, et de temps en temps sans raison. Les quatre témoins sont chez Let's Encrypt, l'autorité
qui renouvelle le plus souvent : ils cassent les premiers.

Ligne de commande :

    python tls.py           # vérifier
    python tls.py reparer   # mettre à jour puis vérifier
"""
import os
import ssl
import sys
import time

INSTALLE = None          # "truststore", "certifi", ou None


def _dit(msg):
    print("[tls] " + msg, file=sys.stderr)


def installe():
    """Répare la vérification pour tout le processus. Rend le nom de la méthode retenue."""
    global INSTALLE
    if INSTALLE:
        return INSTALLE
    try:
        import truststore
        truststore.inject_into_ssl()
        INSTALLE = "truststore"
        return INSTALLE
    except Exception:
        pass
    try:
        import certifi
        _defaut = ssl.create_default_context

        def _avec_certifi(purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None,
                          cadata=None):
            if cafile is None and capath is None and cadata is None:
                cafile = certifi.where()
            return _defaut(purpose, cafile=cafile, capath=capath, cadata=cadata)

        ssl.create_default_context = _avec_certifi
        ssl._create_default_https_context = _avec_certifi
        INSTALLE = "certifi"
        return INSTALLE
    except Exception:
        pass
    _dit("ni truststore ni certifi : la vérification reste celle de Windows, et elle échoue "
         "sur Let's Encrypt. `python -m pip install truststore certifi`")
    return None


installe()


# ------------------------------------------------------- le rappel, parce qu'on oubliera
JETON = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tls-verifie")
PEREMPTION = 30          # jours


def _age():
    """Depuis combien de jours la vérification n'a pas été passée ? None si jamais."""
    try:
        return (time.time() - os.path.getmtime(JETON)) / 86400.0
    except OSError:
        return None


def _rappelle():
    """UN CONTRÔLE QU'ON DOIT PENSER À LANCER EST UN CONTRÔLE QU'ON NE LANCE PAS.

    `certifi` est un fichier figé : il se repérimera comme le magasin de Windows s'est
    repérimé, et la session qui verra le premier CERTIFICATE_VERIFY_FAILED accusera le site,
    comme ce dossier l'a fait quatre fois. Le module dit donc lui-même quand sa dernière
    vérification date — une ligne sur stderr, jamais une exception : il ne casse rien.
    """
    a = _age()
    if a is None:
        _dit("la vérification TLS n'a jamais été passée — `python scripts/archives/tls.py`")
    elif a > PEREMPTION:
        _dit("dernière vérification TLS il y a %d jours — `python scripts/archives/tls.py`"
             % a)


_rappelle()


# --------------------------------------------------------------------------- le contrôle
TEMOINS = [
    "https://fr.wikipedia.org/w/api.php?action=query&format=json&titles=Paris",
    "https://www.data.gouv.fr/api/1/datasets/fichier-des-personnes-decedees/",
    "https://francearchives.gouv.fr/fr",
    "https://deces.matchid.io/deces/api/v1/search?lastName=DUPONT&size=1",
]


def verifie(temoins=TEMOINS, timeout=45):
    """Interroge les quatre témoins. Rend [(hôte, ok, message)].

    ⚠️ ON VÉRIFIE AVEC LE CONTEXTE PAR DÉFAUT, celui que le module vient de réparer — c'est
    lui qu'on veut mesurer, pas un contexte fabriqué pour l'occasion.
    """
    import urllib.request
    ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
    out = []
    for u in temoins:
        hote = u.split("/")[2]
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers=ua), timeout=timeout)
            out.append((hote, True, "HTTP %s" % r.status))
        except Exception as e:
            msg = str(e)
            out.append((hote, "CERTIFICATE_VERIFY_FAILED" not in msg, msg[:110]))
    return out


def repare():
    """Met à jour les deux paquets, puis vérifie. C'est la commande à lancer sur un
    CERTIFICATE_VERIFY_FAILED, avant d'accuser le site."""
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "--quiet",
                    "certifi", "truststore"])
    print("certifi et truststore mis à jour ; relancer le processus pour en profiter.")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if len(sys.argv) > 1 and sys.argv[1] == "reparer":
        repare()
    print("méthode retenue : %s" % (INSTALLE or "AUCUNE — la vérification échouera"))
    ko = 0
    for hote, ok, msg in verifie():
        print("  %-3s %-26s %s" % ("ok" if ok else "KO", hote, msg))
        ko += not ok
    if ko:
        print("\n⚠️ %d témoin(s) refusent le certificat. `python tls.py reparer`, puis "
              "relancer." % ko)
    else:
        # LE JETON N'EST POSÉ QUE SUR UN SUCCÈS COMPLET : c'est lui qui éteint le rappel, et
        # un rappel éteint par une vérification ratée ne vaudrait rien.
        io.open(JETON, "w", encoding="utf-8").write(
            "%s  %s  %d temoins ok\n"
            % (time.strftime("%Y-%m-%d %H:%M"), INSTALLE, len(TEMOINS)))
        print("\njeton posé : le rappel se taira %d jours." % PEREMPTION)
    sys.exit(1 if ko else 0)
