import streamlit as st
from streamlit_extras.switch_page_button import switch_page 
from datetime import datetime
import time
import pymongo

# Seiten-Layout
st.set_page_config(page_title="VVZ", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

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
    for ck in list(util.personencodekategorie.find({}, sort = [("rang", pymongo.ASCENDING)])):
        loc = [x["_id"] for x in list(util.personencode.find({"codekategorie" : ck["_id"]}, sort = [("rang", pymongo.ASCENDING)]))]
        all_codes = all_codes + loc
        if ck["name_de"] == "Statusgruppe":
            statusgruppen = loc

    
    st.multiselect("Codes", all_codes, format_func = (lambda a: tools.repr(util.personencode, a, show_collection=False)), placeholder = "Bitte auswählen", help = "Es werden nur Personen angezeigt, die einen der genannten Codes haben.", key = "code_list")
     
    aktuell = st.toggle("Aktuelle Personen anzeigen", True)
    ehemalig = st.toggle("Ehemalige Personen anzeigen", False)

    queries = []
    if st.session_state["code_list"] != []:
        queries.append({"code" : {"$elemMatch": {"$in": st.session_state["code_list"]}}})
    if aktuell:
        queries.append({"$or": [{"ausstiegsdatum": None}, {"ausstiegsdatum": {"$gt": datetime.today()}}]})
    if ehemalig:
        queries.append({"$or": [{"ausstiegsdatum": None}, {"ausstiegsdatum": {"$lt": datetime.today()}}]})
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
