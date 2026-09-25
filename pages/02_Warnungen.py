import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import datetime
import pymongo

# Seiten-Layout
st.set_page_config(page_title="PERSON", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

# check if session_state is initialized if not change to main page
if 'logged_in' not in st.session_state:
    switch_page("PERSON")

from misc.config import *
import misc.util as util
import misc.tools as tools

# Navigation in Sidebar anzeigen
tools.display_navigation()
st.session_state.page = "Warnungen"

# Regeln: Jede Regel bekommt eine Person und gibt einen Warnungstext zurück, oder None.
jetzt = datetime.datetime.now()

def ist_schon_da(p):
    return p["einstiegsdatum"] is None or p["einstiegsdatum"] <= jetzt

def keine_email(p):
    if ist_schon_da(p) and p["email1"] == "" and p["email2"] == "":
        return "hat keine Email-Adresse."

# abt_dict wird unten gesetzt
def keine_abteilung(p):
    if not any(c in abt_dict for c in p["code"]):
        return "ist keiner Abteilung zugeordnet."

regeln = [keine_email]

if st.session_state.logged_in:
    st.header("Warnungen")
    st.write("Inkonsistenzen in der Datenbank.")

    abteilung = util.personencodekategorie.find_one({"name_de": "Abteilung"})
    abteilungen = list(util.personencode.find({"codekategorie": abteilung["_id"]}, sort = [("rang", pymongo.ASCENDING)]))
    abt_dict = {a["_id"]: a for a in abteilungen}
    auswahl = st.pills("Abteilung", ["Alle"] + list(abt_dict.keys()), default = "Alle", format_func = (lambda a: a if a == "Alle" else abt_dict[a]["name"]), key = "warnungen_abteilung")
    nur_aktuell = st.toggle("Nur Warnungen von aktuellen Personen anzeigen", True, key = "warnungen_aktuell")
    nur_statusgruppe = st.toggle("Nur Warnungen von Personen anzeigen, die einer Statusgruppe angehören", True, key = "warnungen_statusgruppe")

    # Platzhalter-Einträge mit Namen "-" nicht prüfen
    query = {"name": {"$ne": "-"}}
    if nur_aktuell:
        query["$and"] = [
            {"$or": [{"einstiegsdatum": None}, {"einstiegsdatum": {"$lt": jetzt}}]},
            {"$or": [{"ausstiegsdatum": None}, {"ausstiegsdatum": {"$gt": jetzt}}]}
        ]
    if auswahl not in [None, "Alle"]:
        query["code"] = auswahl
    # Ist eine Abteilung ausgewählt, haben alle angezeigten Personen eine Abteilung.
    if auswahl in [None, "Alle"]:
        regeln.append(keine_abteilung)
    personen = list(util.person.find(query, sort = [("name", pymongo.ASCENDING), ("vorname", pymongo.ASCENDING)]))

    # Warnungen nach Statusgruppen (in der Reihenfolge ihres Rangs) sortieren;
    # bei mehreren Statusgruppen zählt die erste.
    statusgruppe = util.personencodekategorie.find_one({"name_de": "Statusgruppe"})
    gruppen = list(util.personencode.find({"codekategorie": statusgruppe["_id"]}, sort = [("rang", pymongo.ASCENDING)]))
    warnungen = {g["_id"]: [] for g in gruppen} | {None: []}
    allgemein = []
    for p in personen:
        g = next((g["_id"] for g in gruppen if g["_id"] in p["code"]), None)
        if g is None and nur_statusgruppe:
            continue
        if g is None:
            allgemein.append(f"{tools.repr(util.person, p['_id'], False)} gehört keiner Statusgruppe an.")
        for regel in regeln:
            text = regel(p)
            if text:
                warnungen[g].append(f"{tools.repr(util.person, p['_id'], False)} {text}")

    st.divider()
    if not allgemein and not any(warnungen.values()):
        st.success("Keine Warnungen.")
    if allgemein:
        st.subheader(f"Allgemeine Warnungen ({len(allgemein)})")
        st.markdown("\n".join(f"- {w}" for w in allgemein))
    for g in gruppen + [None]:
        gid = g["_id"] if g else None
        if warnungen[gid]:
            st.subheader(f"{g['name'] if g else 'Ohne Statusgruppe'} ({len(warnungen[gid])})")
            st.markdown("\n".join(f"- {w}" for w in warnungen[gid]))

else:
    switch_page("PERSON")

st.sidebar.button("logout", on_click = tools.logout)
