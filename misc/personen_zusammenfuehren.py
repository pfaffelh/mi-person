# Führt mehrere Datensätze einer Person in der Collection vvz.person zusammen.
#
# Aufruf (aus dem Projektverzeichnis):
#   python misc/personen_zusammenfuehren.py --suche Hammerstein
#   python misc/personen_zusammenfuehren.py --behalte <id> --entferne <id> [<id> ...]
#   python misc/personen_zusammenfuehren.py --behalte <id> --entferne <id> [<id> ...] --ausfuehren
#
# Ohne --ausfuehren wird nur angezeigt, was passieren würde (Probelauf).
#
# Vorgehen:
# 1. Im behaltenen Datensatz werden leere Felder (None, "", [], False) aus den
#    entfernten Datensätzen aufgefüllt; Listen (z.B. code, semester, veranstaltung)
#    werden vereinigt. Felder, die es im behaltenen Datensatz nicht gibt (Altlasten),
#    werden nicht übernommen, aber angezeigt.
# 2. In allen Collections der Datenbank (Standard: vvz) wird jede Vorkommnis einer entfernten ID
#    (auch verschachtelt, z.B. veranstaltung.deputat.person) durch die behaltene ID
#    ersetzt. Dabei entstehende Doppelungen in ID-Listen werden entfernt.
# 3. Die entfernten Datensätze werden gelöscht.
# Vor dem Ändern werden alle betroffenen Dokumente als JSON gesichert.

import argparse
import datetime
import sys

from bson import ObjectId, json_util
from pymongo import MongoClient

mongo_location = "mongodb://localhost:27017"


def ist_leer(v):
    return v is None or v == "" or v == [] or v is False


def eindeutig(liste):
    res = []
    for x in liste:
        if x not in res:
            res.append(x)
    return res


def ersetze(o, alt, neu):
    """Ersetzt rekursiv alle IDs aus alt durch neu. Gibt (neues Objekt, geändert?) zurück."""
    if isinstance(o, dict):
        geaendert = False
        res = {}
        for k, v in o.items():
            res[k], g = ersetze(v, alt, neu)
            geaendert = geaendert or g
        return res, geaendert
    if isinstance(o, list):
        geaendert = False
        res = []
        for v in o:
            w, g = ersetze(v, alt, neu)
            res.append(w)
            geaendert = geaendert or g
        if geaendert and all(isinstance(x, ObjectId) for x in res):
            res = eindeutig(res)
        return res, geaendert
    if isinstance(o, ObjectId) and o in alt:
        return neu, True
    return o, False


def zeige(p):
    return f"{p['_id']}: {p.get('titel', '')} {p.get('vorname', '')} {p.get('name', '')} ({p.get('email1') or p.get('email', '')})".replace("  ", " ")


def main():
    parser = argparse.ArgumentParser(description="Personen in vvz.person zusammenführen.")
    parser.add_argument("--suche", help="Personen anzeigen, deren Name diesen Text enthält")
    parser.add_argument("--behalte", help="ID des Datensatzes, der erhalten bleibt")
    parser.add_argument("--entferne", nargs="+", default=[], help="IDs der Datensätze, die aufgehen")
    parser.add_argument("--ausfuehren", action="store_true", help="Änderungen wirklich schreiben")
    parser.add_argument("--db", default="vvz", help="Name der Datenbank (Standard: vvz)")
    args = parser.parse_args()

    db = MongoClient(mongo_location)[args.db]
    person = db["person"]

    if args.suche:
        for p in person.find({"name": {"$regex": args.suche, "$options": "i"}}):
            n = sum(db[c].count_documents({"$or": [{"dozent": p["_id"]}, {"assistent": p["_id"]}]})
                    for c in ["veranstaltung", "planung"])
            print(f"{zeige(p)}  -- Dozent/Assistent in {n} Dokumenten")
        return

    if not args.behalte or not args.entferne:
        parser.error("--behalte und --entferne angeben (oder --suche).")

    keep_id = ObjectId(args.behalte)
    drop_ids = [ObjectId(x) for x in args.entferne]
    if keep_id in drop_ids:
        sys.exit("Die behaltene ID darf nicht unter --entferne stehen.")

    keep = person.find_one({"_id": keep_id})
    drops = [person.find_one({"_id": i}) for i in drop_ids]
    if keep is None or None in drops:
        sys.exit("Mindestens eine ID wurde in vvz.person nicht gefunden.")

    print("Behalten:  " + zeige(keep))
    for d in drops:
        print("Entfernen: " + zeige(d))

    # 1. Felder zusammenführen
    update = {}
    for k, v in keep.items():
        if k in ("_id", "bearbeitet"):
            continue
        if isinstance(v, list):
            neu = list(v)
            for d in drops:
                neu += d.get(k) or []
            neu = eindeutig(neu)
            if neu != v:
                update[k] = neu
        elif ist_leer(v):
            for d in drops:
                if not ist_leer(d.get(k)):
                    update[k] = d[k]
                    break
    # Verweise der Person auf sich selbst (z.B. vorgesetzte) umbiegen
    for k in list(update):
        update[k], _ = ersetze(update[k], set(drop_ids), keep_id)
    if "vorgesetzte" in update or keep_id in keep.get("vorgesetzte", []):
        update["vorgesetzte"] = [x for x in update.get("vorgesetzte", keep.get("vorgesetzte", [])) if x != keep_id]

    print("\nÄnderungen am behaltenen Datensatz:")
    for k, v in update.items():
        alt = keep.get(k)
        if isinstance(v, list):
            print(f"  {k}: {len(alt)} -> {len(v)} Einträge")
        else:
            print(f"  {k}: {alt!r} -> {v!r}")
    verloren = {k: d[k] for d in drops for k in d if k not in keep and not ist_leer(d[k])}
    if verloren:
        print("Nicht übernommen (Feld gibt es im behaltenen Datensatz nicht):")
        for k, v in verloren.items():
            print(f"  {k}: {v!r}")

    # 2. Verweise in allen Collections suchen
    alt = set(drop_ids)
    aenderungen = []  # (collection, _id, {feld: neuer Wert}, altes Dokument)
    for cn in db.list_collection_names():
        for doc in db[cn].find():
            if cn == "person" and doc["_id"] in alt | {keep_id}:
                continue
            felder = {}
            for k, v in doc.items():
                if k == "_id":
                    continue
                w, g = ersetze(v, alt, keep_id)
                if g:
                    felder[k] = w
            if felder:
                aenderungen.append((cn, doc["_id"], felder, doc))

    print("\nVerweise, die umgestellt werden:")
    zaehler = {}
    for cn, _, felder, _ in aenderungen:
        for k in felder:
            zaehler[(cn, k)] = zaehler.get((cn, k), 0) + 1
    for (cn, k), n in sorted(zaehler.items()):
        print(f"  {cn}.{k}: {n} Dokumente")
    # Hinweis auf doppelte Deputats-Einträge o.ä., die nicht automatisch vereinigt werden
    for cn, i, felder, _ in aenderungen:
        for k, v in felder.items():
            if isinstance(v, list) and all(isinstance(x, dict) for x in v):
                personen = [x.get("person") for x in v if x.get("person") == keep_id]
                if len(personen) > 1:
                    print(f"  Achtung: {cn} {i}: {k} enthält die Person {len(personen)}-mal, bitte von Hand prüfen.")

    if not args.ausfuehren:
        print("\nProbelauf, nichts geändert. Mit --ausfuehren wirklich schreiben.")
        return

    # Sicherung
    zeit = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    datei = f"personen_zusammenfuehren_backup_{zeit}.json"
    sicherung = {"person": [keep] + drops,
                 "verweise": [{"collection": cn, "doc": doc} for cn, _, _, doc in aenderungen]}
    with open(datei, "w") as f:
        f.write(json_util.dumps(sicherung, indent=1))
    print(f"\nSicherung geschrieben: {datei}")

    for cn, i, felder, _ in aenderungen:
        db[cn].update_one({"_id": i}, {"$set": felder})
    stempel = f"Zusammengeführt mit {', '.join(str(x) for x in drop_ids)} am {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}."
    person.update_one({"_id": keep_id}, {"$set": update | {"bearbeitet": stempel}})
    person.delete_many({"_id": {"$in": drop_ids}})
    print(f"Fertig: {len(aenderungen)} Dokumente umgestellt, {len(drop_ids)} Datensätze gelöscht.")


if __name__ == "__main__":
    main()
