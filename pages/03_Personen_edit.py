import streamlit as st
from streamlit_extras.switch_page_button import switch_page 
import time
import pymongo
import datetime

# Seiten-Layout
st.set_page_config(page_title="VVZ", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

# check if session_state is initialized if not change to main page
if 'logged_in' not in st.session_state:
    switch_page("PERSON")

from misc.config import *
import misc.util as util
from misc.util import logger
import misc.tools as tools

# load css styles
from misc.css_styles import init_css
init_css()

date_format = '%d.%m.%Y um %H:%M:%S.'
bearbeitet = f"Zuletzt bearbeitet von {st.session_state.username} am {datetime.datetime.now().strftime(date_format)}"

# Navigation in Sidebar anzeigen
tools.display_navigation()

# Es geht hier vor allem um diese Collection:
collection = util.person
geb = list(util.gebaeude.find({"sichtbar": True}, sort=[("name_de", pymongo.ASCENDING)]))

new_entry = False
submit1 = submit2 = False

# Ab hier wird die Webseite erzeugt
if st.session_state.logged_in:

    # check if entry can be found in database
    if st.session_state.edit == "new":
        new_entry = True
        x = st.session_state.new[collection]
        x["_id"] = "new"
        st.header("Neue Person")

    else:
        x = collection.find_one({"_id": st.session_state.edit})
        st.header(tools.repr(collection, x["_id"], False))

    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    with col1:
        if st.button("Zurück ohne Speichern"):
            switch_page("Personen")
    with col2: 
        if st.button('Speichern', type = 'primary', key="submit1"):
            submit1 = True
    with col4:
        st.markdown("""<style>div[data-testid="column"] button {margin-top: 58px;}</style>""", unsafe_allow_html=True,)
        with st.popover('Person löschen'):
            if not new_entry:
                s = ("  \n".join(tools.find_dependent_items(collection, x["_id"])))
                if s:
                    st.write("Eintrag wirklich löschen?  \n" + s + "  \nwerden dadurch geändert.")
                else:
                    st.write("Eintrag wirklich löschen?  \nEs gibt keine abhängigen Items.")
                colu1, colu2, colu3 = st.columns([1,1,1])
                with colu1:
                    submit = st.button(label = "Ja", type = 'primary', key = f"delete-{x['_id']}")
                if submit: 
                    tools.delete_item_update_dependent_items(collection, x["_id"])
                with colu3: 
                    st.button(label="Nein", on_click = st.success, args=("Nicht gelöscht!",), key = f"not-deleted-{x['_id']}")

    sichtbar = True #st.checkbox("In Auswahlmenüs sichtbar", x["sichtbar"], disabled = (True if x["_id"] == util.leer[collection] else False))
    st.write(x["bearbeitet"])
    hp_sichtbar = st.checkbox("Auf Homepages sichtbar", x["hp_sichtbar"])
    ldap = st.checkbox("Ins Instituts-LDAP eintragen", x["ldap"], help = "Z.B. für Scan-to-Mail-Funktion der Drucker.")
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        name=st.text_input('Name (de)', x["name"])
    with col2:
        name_en=st.text_input('Name (en), nur falls abweichend', x["name_en"])
    with col3:
        vorname=st.text_input('Vorname', x["vorname"])
    with col4:
        name_prefix=st.text_input('Abkürzung des Vornamens', x["name_prefix"])
    with col5:
        titel=st.text_input('Titel', x["titel"])
    with col6:
        kennung=st.text_input('RZ-Kennung', x["kennung"])
    otherperson = collection.find_one({"_id" : { "$ne" : x["_id"]}, "name" : name, "vorname" : vorname})
    if otherperson:
        if otherperson["semester"] != []:
            st.warning(f"Eine Person mit demselben Namen gibt es auch in { ', '.join([tools.repr(util.semester, x, False, True) for x in otherperson['semester']])}")
        else:
            st.warning(f"Eine Person mit demselben Namen gibt bereits!")


    codes_list = []
    for ck in list(util.personencodekategorie.find({}, sort = [("rang", pymongo.ASCENDING)])):
        loc = [x["_id"] for x in list(util.personencode.find({"codekategorie" : ck["_id"]}, sort = [("rang", pymongo.ASCENDING)]))]
        codes_list = codes_list + loc

    code = st.multiselect("Zugehörigkeiten", codes_list, x["code"], format_func = (lambda a: tools.repr(util.personencode, a, False, False)), placeholder = "Bitte auswählen")
    
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    with col1:
        email1=st.text_input('Email 1', x["email1"])
    with col2:
        tel1=st.text_input('Telefonnummer 1', x["tel1"])
    with col3:
        gebaeude_sichtbar = [ x["_id"]  for x in geb ]
        if x["gebaeude1"] not in gebaeude_sichtbar:
            gebaeude_sichtbar.insert(0, x["gebaeude1"])
        index1 = [g for g in gebaeude_sichtbar].index(x["gebaeude1"])
        gebaeude1 = st.selectbox("Gebäude 1", [x for x in gebaeude_sichtbar], index = index1, format_func = (lambda a: tools.repr(util.gebaeude, a, False)))
    with col4:
        raum1 = st.text_input('Raum (Büro) 1', x["raum1"])
    with col1:
        email2=st.text_input('Email 2', x["email2"])
    with col2:
        tel2=st.text_input('Telefonnummer 2', x["tel2"])
    with col3:
        gebaeude_sichtbar = [x["_id"]  for x in geb]
        if x["gebaeude2"] not in gebaeude_sichtbar:
            gebaeude_sichtbar.insert(0, x["gebaeude2"])
        index2 = [g for g in gebaeude_sichtbar].index(x["gebaeude2"])
        gebaeude2 = st.selectbox("Gebäude 2", [x for x in gebaeude_sichtbar], index = index2, format_func = (lambda a: tools.repr(util.gebaeude, a, False)))
    with col4:
        raum2 = st.text_input('Raum (Büro) 2', x["raum2"])
    with col1:
        url=st.text_input('Homepage', x["url"])

    kommentar_html=st.text_input('Kommentar für Homepage', x["kommentar_html"])
    kommentar=st.text_input('Kommentar (intern)', x["kommentar"])

    col1, col2, col3, col4 = st.columns([1, 2, 1, 2])
    with col1:
        enable_einstieg = st.toggle("Einstiegsdatum setzen", True if x["einstiegsdatum"] is not None else False)
    with col2:
        if enable_einstieg:
            einstiegsdatum = st.date_input("Eintsiegsdatum", value = x["einstiegsdatum"], format="DD.MM.YYYY")
        else:
            einstiegsdatum = None
    if einstiegsdatum is not None:
        einstiegsdatum = datetime.datetime.combine(einstiegsdatum, datetime.time.min)
    
    with col3:
        enable_ausstieg = st.toggle("Ausstiegsdatum setzen", True if x["ausstiegsdatum"] is not None else False)
    with col4:
        if enable_ausstieg:
            ausstiegsdatum = st.date_input("Ausstiegsdatum", value = x["ausstiegsdatum"], format="DD.MM.YYYY")
        else:
            ausstiegsdatum = None
    if ausstiegsdatum is not None:
        ausstiegsdatum = datetime.datetime.combine(ausstiegsdatum, datetime.time.max)



    semester_list = st.multiselect("Semester", [x["_id"] for x in util.semester.find(sort = [("kurzname", pymongo.DESCENDING)])], x["semester"], format_func = (lambda a: tools.repr(util.semester, a, False, True)), placeholder = "Bitte auswählen")
    se = list(util.semester.find({"_id": {"$in": semester_list}}, sort=[("rang", pymongo.ASCENDING)]))
    semester_list = [s["_id"] for s in se]

    x_updated = ({"name": name, "name_en": name_en, "vorname": vorname, "name_prefix": name_prefix, "titel": titel, "kennung" : kennung, "kommentar": kommentar, "kommentar_html": kommentar_html, "tel1": tel1, "email1": email1, "raum1" : raum1, "gebaeude1" : gebaeude1, "raum2" : raum2, "gebaeude2" : gebaeude2, "url" : url, "sichtbar": sichtbar, "hp_sichtbar": hp_sichtbar, "ldap" : ldap, "einstiegsdatum" : einstiegsdatum, "ausstiegsdatum" : ausstiegsdatum, "semester": semester_list, "code" : code, "bearbeitet" : bearbeitet})
    if st.button('Speichern', type = 'primary', key="submit2"):
        submit2 = True

    if submit1 or submit2:
        if new_entry:
            tools.new(collection, ini = x_updated, switch=False)
        else: 
            tools.update_confirm(collection, x, x_updated, reset=False)
        time.sleep(1)

else: 
    switch_page("Personen")

st.sidebar.button("logout", on_click = tools.logout)
