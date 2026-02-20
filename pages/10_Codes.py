import streamlit as st
from streamlit_extras.switch_page_button import switch_page 
import time
import pymongo
import pandas as pd

# Seiten-Layout
st.set_page_config(page_title="PERSON", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

# check if session_state is initialized if not change to main page
if 'logged_in' not in st.session_state:
    switch_page("PERSON")

from misc.config import *
import misc.util as util
import misc.tools as tools

# load css styles
from misc.css_styles import init_css
init_css()

# make all neccesary variables available to session_state
# setup_session_state()

# Navigation in Sidebar anzeigen
tools.display_navigation()

collection = util.personencode
# Ab hier wird die Webseite erzeugt
if st.session_state.logged_in:
    st.header("Grundeinstellungen der Personendatenbank")

    st.header("Codes")
    collection = util.personencode

    cken = list([x["_id"] for x in util.personencodekategorie.find({}, sort=[("rang", pymongo.ASCENDING)])])
    default = util.personencodekategorie.find_one({"name_de" : "Abteilung"})["_id"]
    ck = st.selectbox("Welche Codekategorie soll bearbeitet werden?", cken, cken.index(default), format_func = (lambda a: tools.repr(util.personencodekategorie, a, show_collection = False)))
    query = { "codekategorie": ck }

    if st.button('**Neuen Code hinzufügen**'):
        tools.new(collection, ini = {"codekategorie": ck}, switch = False)

    y = list(collection.find(query, sort=[("rang", pymongo.ASCENDING)]))
    for x in y:
        co1, co2, co3 = st.columns([1,1,23]) 
        with co1: 
            st.button('↓', key=f'down-{x["_id"]}', on_click = tools.move_down, args = (collection, x, query, ))
        with co2:
            st.button('↑', key=f'up-{x["_id"]}', on_click = tools.move_up, args = (collection, x, query, ))
        with co3:   
            with st.expander(x["name"], (True if x["_id"] == st.session_state.edit else False)):
                st.subheader(tools.repr(collection, x["_id"]))
                with st.popover('Code löschen'):
                    s = ("  \n".join(tools.find_dependent_items(collection, x["_id"])))
                    if s:
                        st.write("Eintrag wirklich löschen?  \n" + s + "  \nwerden dadurch geändert.")
                    else:
                        st.write("Eintrag wirklich löschen?  \nEs gibt keine abhängigen Items.")
                    colu1, colu2, colu3 = st.columns([1,1,1])
                    with colu1:
                        submit = st.button(label = "Ja", type = 'primary', key = f"delete-{x['_id']}")
                    if submit:
                        tools.delete_item_update_dependent_items(collection, x["_id"], False)
                        st.rerun()
                    with colu3: 
                        st.button(label="Nein", on_click = st.success, args=("Nicht gelöscht!",), key = f"not-deleted-{x['_id']}")
                with st.form(f'ID-{x["_id"]}'):
                    codekategorie_list = list(util.personencodekategorie.find({}, sort = [("rang", pymongo.ASCENDING)]))
                    codekategorie_dict = {r["_id"]: tools.repr(util.personencodekategorie, r["_id"], show_collection = False) for r in codekategorie_list}
                    index = [g["_id"] for g in codekategorie_list].index(x["codekategorie"])
                    codekategorie = st.selectbox("Codekategorie", codekategorie_dict.keys(), index, format_func = (lambda a: codekategorie_dict[a]), key = f"codekategorie_{x}")
                    name=st.text_input('Name', x["name"], key=f'name-{x["_id"]}')
                    beschreibung_de=st.text_input('Beschreibung (de)', x["beschreibung_de"], key=f'beschreibung-de-{x["_id"]}')
                    beschreibung_en=st.text_input('Beschreibung (en)', x["beschreibung_en"], key=f'beschreibung-en-{x["_id"]}')
                    kommentar_html=st.text_area('Kommentar für Webpage', x["kommentar_html"])
                    kommentar=st.text_area('Kommentar', x["kommentar"])
                    x_updated = {"codekategorie": codekategorie, "name": name, "beschreibung_de": beschreibung_de, "beschreibung_en": beschreibung_en, "kommentar": kommentar}
                    submit = st.form_submit_button('Speichern', type = 'primary')
                    if submit:
                        tools.update_confirm(collection, x, x_updated, )
                        time.sleep(2)
                        st.session_state.edit = ""
                        st.rerun()                      

    with st.expander("Codes einstellen"):
        # codekategorie = st.selectbox("Codekategorie", codekategorie_dict.keys(), index, format_func = (lambda a: codekategorie_dict[a]), key = f"codekategorie_wahl")
        y = list(util.personencode.find({"codekategorie" : ck}))
        per_list = list(util.person.find({}, sort=[("name", pymongo.ASCENDING), ("vorname", pymongo.ASCENDING)]))
        per_dict = []
        for p in per_list:
            loc = {}
            loc["_id"] = p["_id"]
            loc["Name"] = tools.repr(util.person, p["_id"], False, True),
            for x in y:
                loc[str(x["_id"])] = True if x["_id"] in p["code"] else False
            per_dict.append(loc)
        df = df_new = pd.DataFrame.from_records(per_dict)
        cc = {}
        cc["_id"] = None
        cc["Name"] = "Name"
        for x in y:
            cc[str(x["_id"])] = util.personencode.find_one({"_id": x["_id"]})["name"]
        df_new = st.data_editor(
                df, height = None, column_config = cc, disabled=["Name"], hide_index = True)
        st.button("Codes übernehmen", on_click=tools.codes_uebernehmen, args = (df_new,), type="primary")

    st.header("Codekategorien")
    st.write('Dies ist z.B. "Sprache", oder "Statusgruppe". Dann kann in den Codes dieser Codekategorie so etwas stehen wie "englisch", oder "Professor:innen". Dies kann dann einzelnen Personen zugeordnet werden.' )
    collection = util.personencodekategorie
    st.write(" ")
    if st.button('**Neue Codekategorie hinzufügen**'):
        tools.new(collection, ini = {}, switch = False)

    y = list(util.personencodekategorie.find({}, sort=[("rang", pymongo.ASCENDING)]))

    for x in y:
        co1, co2, co3 = st.columns([1,1,23]) 
        with co1: 
            st.button('↓', key=f'down-{x["_id"]}', on_click = tools.move_down, args = (collection, x, {}, ))
        with co2:
            st.button('↑', key=f'up-{x["_id"]}', on_click = tools.move_up, args = (collection, x, {}, ))
        with co3:   
            abk = f"{x['name_de'].strip()}"
            with st.expander(abk, (True if x["_id"] == st.session_state.edit else False)):
                with st.popover('Codekategorie löschen'):
                    s = ("  \n".join(tools.find_dependent_items(collection, x["_id"])))
                    if s:
                        st.write("Eintrag wirklich löschen?  \n" + s + "  \nwerden dadurch geändert.")
                    else:
                        st.write("Eintrag wirklich löschen?  \nEs gibt keine abhängigen Items.")
                    colu1, colu2, colu3 = st.columns([1,1,1])
                    with colu1:
                        submit = st.button(label = "Ja", type = 'primary', key = f"delete-{x['_id']}", disabled = True if x["_id"] == util.leer[util.codekategorie] else False)
                    if submit:
                        tools.delete_item_update_dependent_items(collection, x["_id"], False)
                        st.rerun()
                    with colu3: 
                        st.button(label="Nein", on_click = st.success, args=("Nicht gelöscht!",), key = f"not-deleted-{x['_id']}")

                with st.form(f'ID-{x["_id"]}'):
                    name_de=st.text_input('Titel (de)', x["name_de"], key=f'titel-de-{x["_id"]}', disabled = True if x["name_de"] in ["Statustgruppe", "Abteilung"] else False)
                    name_en=st.text_input('Titel (en)', x["name_en"], key=f'titel-en-{x["_id"]}')
                    beschreibung_de=st.text_input('Beschreibung (de)', x["beschreibung_de"], key=f'beschreibung-de-{x["_id"]}')
                    beschreibung_en=st.text_input('Beschreibung (en)', x["beschreibung_en"], key=f'beschreibung-en-{x["_id"]}')
                    kommentar=st.text_area('Kommentar', x["kommentar"])
                    code = []
                    x_updated = {"name_de": name_de, "name_en": name_en, "beschreibung_de": beschreibung_de, "kommentar": kommentar, "code": []}
                    submit = st.form_submit_button('Speichern', type = 'primary', disabled = True if x["_id"] == util.leer[util.codekategorie] else False)
                    if submit:
                        tools.update_confirm(collection, x, x_updated, )
                        time.sleep(2)
                        st.session_state.edit = ""
                        st.rerun()                      


else:
    switch_page("PERSON")

st.sidebar.button("logout", on_click = tools.logout)
