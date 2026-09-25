# Entfernt Einträge aus der Collection vvz.person, die keine Personen sind
# (Faxgeräte, Diplomandenzimmer, Druckerräume usw. aus dem LDAP-Import).
#
# Aufruf (aus dem Projektverzeichnis):
#   python misc/nichtpersonen_entfernen.py               # Probelauf
#   python misc/nichtpersonen_entfernen.py --ausfuehren  # wirklich löschen
#
# Kandidaten sind Einträge aus dem LDAP-Import (ldap = True) ohne Vornamen, die
# keinem Semester, keiner Veranstaltung und keiner Statusgruppe zugeordnet sind.
# (Einträge mit Statusgruppe, zB Prüfungsamt oder IT Systemadministration, stehen
# auf den Personenseiten der Homepage und bleiben daher erhalten.)
# Einträge, auf die irgendwo in der Datenbank noch verwiesen wird, werden nicht gelöscht.
# Vor dem Löschen werden alle Kandidaten als JSON gesichert.

import argparse
import datetime

from bson import json_util
from pymongo import MongoClient

mongo_location = "mongodb://localhost:27017"


def enthaelt(o, ids):
    """Kommt eine der ids (auch verschachtelt) in o vor?"""
    if isinstance(o, dict):
        return any(enthaelt(v, ids) for v in o.values())
    if isinstance(o, list):
        return any(enthaelt(v, ids) for v in o)
    return o in ids


def main():
    parser = argparse.ArgumentParser(description = "Entfernt Nicht-Personen (Fax, Räume, ...) aus vvz.person.")
    parser.add_argument("--db", default = "vvz")
    parser.add_argument("--ausfuehren", action = "store_true", help = "Wirklich löschen (sonst nur Probelauf).")
    args = parser.parse_args()

    db = MongoClient(mongo_location)[args.db]
    person = db["person"]

    statusgruppe = db["personencodekategorie"].find_one({"name_de": "Statusgruppe"})["_id"]
    statusgruppen = [c["_id"] for c in db["personencode"].find({"codekategorie": statusgruppe})]
    kandidaten = list(person.find({"ldap": True, "vorname": "", "semester": [], "veranstaltung": [], "code": {"$nin": statusgruppen}}, sort = [("name", 1)]))
    if not kandidaten:
        print("Keine Kandidaten gefunden.")
        return

    # Verweise in allen Collections suchen
    ids = {p["_id"] for p in kandidaten}
    verweise = {i: [] for i in ids}
    for cn in db.list_collection_names():
        for doc in db[cn].find():
            if cn == "person" and doc["_id"] in ids:
                continue
            for i in ids:
                if enthaelt({k: v for k, v in doc.items() if k != "_id"}, {i}):
                    verweise[i].append(f"{cn} {doc['_id']}")

    loeschen = [p for p in kandidaten if not verweise[p["_id"]]]
    behalten = [p for p in kandidaten if verweise[p["_id"]]]

    print("Werden gelöscht:")
    for p in loeschen:
        print(f"  {p['_id']}  {p['name']}  {p['email1']}")
    if behalten:
        print("\nWerden NICHT gelöscht, da noch Verweise existieren:")
        for p in behalten:
            print(f"  {p['_id']}  {p['name']}: {', '.join(verweise[p['_id']])}")

    if not args.ausfuehren:
        print("\nProbelauf, nichts geändert. Mit --ausfuehren wirklich löschen.")
        return
    if not loeschen:
        return

    zeit = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    datei = f"nichtpersonen_entfernen_backup_{zeit}.json"
    with open(datei, "w") as f:
        f.write(json_util.dumps(loeschen, indent = 1))
    print(f"\nSicherung geschrieben: {datei}")

    res = person.delete_many({"_id": {"$in": [p["_id"] for p in loeschen]}})
    print(f"Fertig: {res.deleted_count} Einträge gelöscht.")


if __name__ == "__main__":
    main()
