"""
Inspecte un fichier Heredis (ou n'importe quel fichier genealogique inconnu) et dit
ce que c'est, sans rien modifier.

  python scripts/inspect_heredis.py "D:\\vieux disque\\genealogie.heredis"

Ne depend d'aucune bibliotheque externe : sqlite3 et zipfile sont dans la stdlib.
Ouvre toujours en LECTURE SEULE -- un fichier de famille irremplacable ne se teste
pas en ecriture.
"""
import sys, os, sqlite3, zipfile, string

MAGICS = {
    b"SQLite format 3\x00": "base SQLite (Heredis 2014+, lisible directement)",
    b"PK\x03\x04": "archive ZIP (probablement un paquet Heredis : base + medias)",
    b"\x00\x01\x00\x00Stan": "base Microsoft Access (.mdb)",
}


def human(n):
    for u in ("o", "Ko", "Mo", "Go"):
        if n < 1024:
            return f"{n:.0f} {u}"
        n /= 1024
    return f"{n:.1f} To"


def sniff(path):
    with open(path, "rb") as f:
        head = f.read(64)
    for magic, label in MAGICS.items():
        if head.startswith(magic):
            return label, head
    return None, head


def dump_sqlite(path):
    """Liste les tables et leur volume. Connexion en lecture seule."""
    uri = "file:" + path.replace("\\", "/").replace("?", "%3f").replace("#", "%23") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    cur = con.cursor()
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print(f"\n  {len(tables)} tables :")
    interesting = []
    for t in tables:
        try:
            n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        except sqlite3.Error:
            n = "?"
        cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{t}")')]
        flag = ""
        low = t.lower()
        if any(k in low for k in ("individu", "person", "pers", "union", "famil", "event",
                                  "evenem", "lieu", "place", "source", "media", "note")):
            flag = "  <<<"
            interesting.append(t)
        print(f"    {t:<28} {str(n):>8} lignes   {len(cols):>2} colonnes{flag}")
        if flag:
            print(f"        {', '.join(cols[:14])}{' …' if len(cols) > 14 else ''}")
    if interesting:
        print(f"\n  Tables a exploiter en priorite : {', '.join(interesting)}")
        t = interesting[0]
        try:
            row = cur.execute(f'SELECT * FROM "{t}" LIMIT 1').fetchone()
            cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{t}")')]
            print(f"\n  Exemple de ligne dans {t} :")
            for c, v in list(zip(cols, row or []))[:20]:
                s = str(v)
                print(f"    {c:<24} {s[:70]}{'…' if len(s) > 70 else ''}")
        except sqlite3.Error as e:
            print(f"    (lecture impossible : {e})")
    con.close()


def dump_zip(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        print(f"\n  {len(names)} entrees :")
        for n in names[:40]:
            info = z.getinfo(n)
            print(f"    {n:<50} {human(info.file_size):>10}")
        if len(names) > 40:
            print(f"    … et {len(names) - 40} autres")
        db = [n for n in names if n.lower().endswith((".sqlite", ".db", ".heredis", ".hz"))]
        if db:
            print(f"\n  Base(s) a extraire puis re-inspecter : {', '.join(db)}")


def dump_unknown(path, head):
    print("\n  Signature non reconnue. Premiers octets :")
    print("   ", " ".join(f"{b:02x}" for b in head[:32]))
    printable = set(bytes(string.printable, "ascii")) - set(b"\x0b\x0c")
    with open(path, "rb") as f:
        blob = f.read(200_000)
    runs, cur_run = [], bytearray()
    for b in blob:
        if b in printable and b not in b"\r\n\t":
            cur_run.append(b)
        else:
            if len(cur_run) >= 6:
                runs.append(cur_run.decode("latin-1"))
            cur_run = bytearray()
    seen, uniq = set(), []
    for r in runs:
        if r not in seen:
            seen.add(r); uniq.append(r)
    print(f"\n  {len(uniq)} chaines lisibles dans les 200 premiers Ko. Echantillon :")
    for r in uniq[:30]:
        print(f"    {r[:76]}")
    print("\n  -> Format proprietaire ancien (Heredis .hmw / .hz d'avant 2014).")
    print("     Voie la plus sure : reinstaller Heredis (une version d'essai suffit a ouvrir")
    print("     et a exporter) puis Fichier > Exporter > GEDCOM.")


def main(path):
    if not os.path.isfile(path):
        sys.exit(f"Introuvable : {path}")
    size = os.path.getsize(path)
    print(f"\n{os.path.basename(path)}  —  {human(size)}")
    print(f"  chemin : {path}")
    label, head = sniff(path)
    print(f"  format : {label or 'inconnu'}")
    if not label:
        dump_unknown(path, head)
    elif "SQLite" in label:
        dump_sqlite(path)
    elif "ZIP" in label:
        dump_zip(path)
    else:
        dump_unknown(path, head)
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
