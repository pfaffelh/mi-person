from ldap3 import Server, Connection, ALL, SUBTREE
import socket

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

try:
    ldap_server = 'ldap://home.mathematik.uni-freiburg.de'  # Beispiel für einen öffentlichen LDAP-Server

    # LDAP-Baum und Suchbasis
    search_base = 'ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de'  # Der Startpunkt für die LDAP-Suche
    search_filter = '(objectClass=*)'  # Beispielhafter Filter, um alle Personenobjekte zu suchen

    # Verbindung zum LDAP-Server ohne Authentifizierung herstellen (anonyme Bindung)
    server = Server(ldap_server, get_info=ALL)
    conn = Connection(server, auto_bind=True)  # Keine Anmeldeinformationen erforderlich
    attributes = ['cn', 'sn', 'mail', 'labeledURI', 'givenName', 'objectClass', 'eduPersonPrimaryAffiliation', 'street', 'telephoneNumber', 'roomNumber', 'personalTitle'] 
except:
    print("No connection to LDAP server")

def get_person_data(abteilung = ""):
    try:
        # URL des öffentlichen LDAP-Servers
        ldap_server = 'ldap://home.mathematik.uni-freiburg.de'  # Beispiel für einen öffentlichen LDAP-Server

        # LDAP-Baum und Suchbasis
        search_base = 'ou=People,dc=home,dc=mathematik,dc=uni-freiburg,dc=de'  # Der Startpunkt für die LDAP-Suche
        if abteilung != "":
            search_base = f"ou={abteilung}," + search_base

        search_filter = '(objectClass=*)'  # Beispielhafter Filter, um alle Personenobjekte zu suchen

        # Verbindung zum LDAP-Server ohne Authentifizierung herstellen (anonyme Bindung)
        server = Server(ldap_server, get_info=ALL)
        conn = Connection(server, auto_bind=True)  # Keine Anmeldeinformationen erforderlich
        attributes = ['cn', 'sn', 'mail', 'labeledURI', 'givenName', 'objectClass', 'eduPersonPrimaryAffiliation', 'street', 'telephoneNumber', 'roomNumber', 'personalTitle'] 

        # Suche im LDAP-Baum durchführen
        conn.search(search_base, search_filter, search_scope=SUBTREE, attributes=attributes)

        # Liste für die Ergebnisse
        res = []

        # Ergebnisse in eine Liste von Dictionaries umwandeln
        for entry in conn.entries:
            entry_dict = {attr: entry[attr].value for attr in attributes if attr in entry}
            res.append(entry_dict)

        # Verbindung beenden
        conn.unbind()

    except:
        print(ip_address)

    trans = {
        "secretary" : "Sekretariate",
        "faculty" : "Professorinnen und Professoren",
        "retired" : "Emeritierte und pensionierte Professoren",
        "staff" : "Wissenschaftlicher Dienst",
        "employee" : "Administration und Technik"
    }
    res = [item for item in res if item["eduPersonPrimaryAffiliation"] in trans.keys()]
#    res = dict(sorted(res, key=lambda x: (x["eduPersonPrimaryAffiliation"], x["cn"])))
        
    data = []
    for key, value in trans.items():
        data.append({
            "kurzname" : key,
            "name" : value,
            "person" : sorted([x for x in res if x["eduPersonPrimaryAffiliation"] == key ], key = lambda x: x['sn'][0])
        })
    return data


data = get_person_data()
print(data)