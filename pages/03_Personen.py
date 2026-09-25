import streamlit as st
from streamlit_extras.switch_page_button import switch_page 
from datetime import datetime
import pymongo

# Seiten-Layout
st.set_page_config(page_title="PERSON", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

# check if session_state is initialized if not change to main page
if 'logged_in' not in st.session_state:
    switch_page("VVZ")

from misc.config import *
import misc.util as util
import misc.tools as tools

# make all neccesary variables available to session_state
# setup_session_state()

# Navigation in Sidebar anzeigen
tools.display_navigation()

# Es geht hier vor allem um diese Collection:
collection = util.person

# Ab hier wird die Webseite erzeugt
if st.session_state.logged_in:
    st.header("Personen")
    st.write(" ")

    if st.button('**Neue Person hinzufügen**'):
        st.session_state.edit = "new"
        switch_page("personen edit")

    all_codes = []
    kategorie_von = {}
    for ck in list(util.personencodekategorie.find({}, sort = [("rang", pymongo.ASCENDING)])):
        loc = [x["_id"] for x in list(util.personencode.find({"codekategorie" : ck["_id"]}, sort = [("rang", pymongo.ASCENDING)]))]
        all_codes = all_codes + loc
        kategorie_von = kategorie_von | {c: ck["_id"] for c in loc}

    
    # Die Einstellungen bleiben erhalten, wenn man eine Person bearbeitet und zurückkommt:
    # Streamlit löscht den Zustand von Widgets, sobald sie nicht mehr angezeigt werden. Daher
    # werden die Werte zusätzlich unter eigenen Keys gespeichert und nach einem Seitenwechsel
    # (wenn der Widget-Key fehlt) zurückkopiert.
    for k, default in [("abteilung", "Alle"), ("alle", False), ("aktuell", True), ("ehemalig", False)]:
        if f"key_personen_{k}" not in st.session_state:
            st.session_state[f"key_personen_{k}"] = st.session_state.setdefault(f"personen_{k}", default)
    if "key_code_list" not in st.session_state:
        st.session_state.key_code_list = st.session_state.code_list

    # Auswahl der Abteilung wie auf der Seite Warnungen
    abteilung = util.personencodekategorie.find_one({"name_de": "Abteilung"})
    abt_dict = {a["_id"]: a for a in util.personencode.find({"codekategorie": abteilung["_id"]}, sort = [("rang", pymongo.ASCENDING)])}
    auswahl = st.session_state.personen_abteilung = st.pills("Abteilung", ["Alle"] + list(abt_dict.keys()), format_func = (lambda a: a if a == "Alle" else abt_dict[a]["name"]), key = "key_personen_abteilung")

    st.session_state.code_list = st.multiselect("Codes", all_codes, format_func = (lambda a: tools.repr(util.personencode, a, show_collection=False)), placeholder = "Bitte auswählen", key = "key_code_list")
    st.caption("Codes derselben Kategorie sind mit 'oder' verknüpft, verschiedene Kategorien mit 'und'. Beispiel: Postdocs, Doktorand:innen, MSt zeigt alle Postdocs und Doktorand:innen in MSt.")

    alle = st.session_state.personen_alle = st.toggle("Alle Personen anzeigen", key = "key_personen_alle")
    aktuell = st.session_state.personen_aktuell = st.toggle("Aktuelle Personen anzeigen", key = "key_personen_aktuell")
    ehemalig = st.session_state.personen_ehemalig = st.toggle("Ehemalige Personen anzeigen", key = "key_personen_ehemalig")

    # pro Codekategorie mindestens einer der gewählten Codes
    queries = []
    kategorien = {}
    for c in st.session_state["code_list"]:
        kategorien.setdefault(kategorie_von.get(c), []).append(c)
    for loc in kategorien.values():
        queries.append({"code": {"$in": loc}})
    if auswahl not in [None, "Alle"]:
        queries.append({"code": auswahl})
    if alle:
        aktuell = False
        ehemalig = False
    else:
        # aktuell/ehemalig sind eine Vereinigung ($or) und werden als Ganzes
        # mit dem Code-Filter geschnitten ($and).
        date_queries = []
        if aktuell:
            date_queries.append({"$or": [{"ausstiegsdatum": None}, {"ausstiegsdatum": {"$gt": datetime.today()}}]})
        if ehemalig:
            date_queries.append({"ausstiegsdatum": {"$lt": datetime.today()}})
        if date_queries:
            queries.append({"$or": date_queries})
    # st.write(queries)
    query = {"$and" : queries} if queries != [] else {}

    y = list(collection.find(query, sort=[("name", pymongo.ASCENDING), ("vorname", pymongo.ASCENDING)]))
    for x in y:
        abk = f"{x['name'].strip()}, {x['vorname'].strip()}".strip()
        submit = st.button(abk, key=f"edit-{x['_id']}")
        if submit:
            st.session_state.edit = x["_id"]
            switch_page("personen edit")

else: 
    switch_page("PERSON")

st.sidebar.button("logout", on_click = tools.logout)
