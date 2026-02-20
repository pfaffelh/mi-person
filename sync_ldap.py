from __future__ import annotations
from pymongo import MongoClient
from typing import Any, Dict, Iterable, List, Optional, Union
from ldap3 import Server, Connection, SUBTREE, MODIFY_REPLACE, ALL

# This file establishes synchronize, a function to synchronize the established LDAP database with the MongoDb

cluster = MongoClient("mongodb://127.0.0.1:27017")
mongo_db = cluster["vvz"]
per = mongo_db["person"]
all_ldap = list(per.find({"ldap" : True}))

server = Server("ldap://localhost:389")
conn = Connection(server,
                  user="cn=admin,dc=de",
                  password="PASSWORT",
                  auto_bind=True)

people_dn = "ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de"



def _norm_values(v: Any) -> List[str]:
    """ldap3 expects lists for multi-valued attributes in modify operations."""
    if v is None:
        return []  # replace with [] => remove attribute
    if isinstance(v, str):
        return [v]
    if isinstance(v, (list, tuple, set)):
        return [str(x) for x in v]
    return [str(v)]

def upsert_person(
    *,
    ldap_uri: str,                       # e.g. "ldap://localhost:389" or "ldapi:///"
    bind_dn: str,                        # e.g. "cn=admin,dc=de"
    bind_password: str,
    base_dn: str,                        # e.g. "dc=de"
    people_ou_dn: str,                   # e.g. "ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
    cn: str,                             # e.g. "flum"
    attrs: Dict[str, Any],               # e.g. {"sn": "Flum", "givenName": "Jörg", ...}
    object_classes: Optional[List[str]] = None,
) -> str:
    """
    Upsert by cn:
      - search (cn=<cn>) under base_dn
      - if 1 match: modify (replace given attrs)
      - if 0 match: add under cn=<cn>,people_ou_dn with objectClasses and attrs
      - if >1 match: error

    Returns DN of the updated/created entry.
    """
    if object_classes is None:
        object_classes = [
            "top",
            "inetOrgPerson"
        ]

    server = Server(ldap_uri, get_info=ALL)
    conn = Connection(server, user=bind_dn, password=bind_password, auto_bind=True)

    # 1) SEARCH
    search_filter = f"(cn={cn})"
    conn.search(search_base=base_dn, search_filter=search_filter, search_scope=SUBTREE, attributes=None)

    if conn.result["result"] != 0:
        raise RuntimeError(f"LDAP search failed: {conn.result}")

    if len(conn.entries) > 1:
        dns = [e.entry_dn for e in conn.entries]
        raise RuntimeError(f"Mehr als ein Eintrag mit cn={cn}: {dns}")

    # Ensure required attributes exist for inetOrgPerson/person
    # (sn is usually mandatory; cn is mandatory too)
    add_attrs = dict(attrs)
    add_attrs.setdefault("cn", cn)
    add_attrs.setdefault("sn", cn)  # fallback; better set real surname

    # 2) UPDATE
    if len(conn.entries) == 1:
        dn = conn.entries[0].entry_dn
        print(f"Update {dn}")
        changes = {k: [(MODIFY_REPLACE, _norm_values(v))] for k, v in attrs.items()}

        ok = conn.modify(dn, changes)
        if not ok:
            raise RuntimeError(f"LDAP modify failed: {conn.result}")
        return dn

    # 3) INSERT
    print("Insert!")
    dn = f"cn={cn},{people_ou_dn}"

    # For add(), ldap3 accepts scalars or lists; we'll pass scalars for single values, lists for multi.
    normalized: Dict[str, Union[str, List[str]]] = {}
    for k, v in add_attrs.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple, set)):
            normalized[k] = [str(x) for x in v]
        else:
            normalized[k] = str(v)

    ok = conn.add(dn, object_classes, normalized)
    if not ok:
        raise RuntimeError(f"LDAP add failed: {conn.result}")
    return dn


for p in all_ldap:
    attrs = {
        'objectClass': ['top', 'inetOrgPerson'],
        'sn': p.get('name'),                                # Pflichtfeld
        'givenName': p.get('vorname', ''),                  # Vorname für die Suche
        'displayName': f"{p.get('name')}, {p.get('vorname')}", # Das zeigt der Drucker an
        'mail': p.get('email')                              # Ziel für Scan-to-Email
    }

    dn = upsert_person(
        ldap_uri="ldap://localhost:389",  # oder "ldapi:///" wenn lokal & konfiguriert
        bind_dn="cn=admin,dc=de",
        bind_password="lumm1nn2",
        base_dn="dc=de",
        people_ou_dn="ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de",
        cn=str(p['_id']),
        attrs=attrs,
    )
    print("OK:", dn)

def delete_unused_person(
        *,
        ldap_uri: str,                       # e.g. "ldap://localhost:389" or "ldapi:///"
        bind_dn: str,                        # e.g. "cn=admin,dc=de"
        bind_password: str,
        base_dn: str,                        # e.g. "dc=de"
        people_ou_dn: str,                   # e.g. "ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de"
        cn: str,                             # e.g. "flum"
        attrs: Dict[str, Any],               # e.g. {"sn": "Flum", "givenName": "Jörg", ...}
        object_classes: Optional[List[str]] = None):
    """
    Delete if cn not element of Upsert by cn:
      - search (cn=<cn>) under base_dn
      - if 1 match: modify (replace given attrs)
      - if 0 match: add under cn=<cn>,people_ou_dn with objectClasses and attrs
      - if >1 match: error

    Returns DN of the updated/created entry.
    """

    # Liste der erlaubten CNs (Sollzustand)
    valid_cns = [str(a["_id"]) for a in all_ldap]

    # aalle aktuellen Einträge holen
    conn.search(
        search_base=people_dn,
        search_filter="(objectClass=inetOrgPerson)",
        search_scope=SUBTREE,
        attributes=["cn"]
    )

    for entry in conn.entries:
        cn = str(entry.cn)

        if cn not in valid_cns:
            print("Deleting:", entry.entry_dn)

            conn.delete(entry.entry_dn)

            if not conn.result["description"] == "success":
                print("Delete failed:", conn.result)
