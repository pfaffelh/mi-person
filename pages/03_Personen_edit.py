import streamlit as st
from streamlit_extras.switch_page_button import switch_page 
import time
from operator import itemgetter
import pymongo
import datetime

# Seiten-Layout
st.set_page_config(page_title="PERSON", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

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

def sort_persons(personen_list):
    loc = [util.person.find_one({"_id" : p_id}) for p_id in personen_list]
    loc = sorted(loc, key=itemgetter('name', 'vorname'))
    return [p["_id"] for p in loc]

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
    # ldap = st.checkbox("Ins Instituts-LDAP eintragen", x["ldap"], help = "Z.B. für Scan-to-Mail-Funktion der Drucker.")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        name=st.text_input('Name (de)', x["name"])
    with col2:
        name_en=st.text_input('Name (en), nur falls abweichend', x["name_en"])
    with col3:
        vorname=st.text_input('Vorname', x["vorname"])
    with col4:
        name_prefix=st.text_input('Abkürzung des Vornamens', x["name_prefix"])
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        gender = st.selectbox("Gender auswählen", ["m", "w", "d", "kA"], ["m", "w", "d", "kA"].index(x["gender"]))
    with col2:
        titel=st.text_input('Titel', x["titel"])
    with col3:
        kennung=st.text_input('RZ-Kennung', x["kennung"])
    otherperson = collection.find_one({"_id" : { "$ne" : x["_id"]}, "name" : name, "vorname" : vorname})
    if otherperson:
        if otherperson["semester"] != []:
            st.warning(f"Eine Person mit demselben Namen gibt es auch in { ', '.join([tools.repr(util.semester, x, False, True) for x in otherperson['semester']])}")
        else:
            st.warning(f"Eine Person mit demselben Namen gibt es bereits!")
    with col4: 
        query1 = {"$and": [{"$or": [{"einstiegsdatum": None}, {"einstiegsdatum": {"$lt": datetime.datetime.now()}}]}, {"$or": [{"ausstiegsdatum": None}, {"ausstiegsdatum": {"$gt": datetime.datetime.now()}}]}]}
        query2 = {"_id" : {"$in" : x["vorgesetzte"]}}
        pe = list(collection.find({"$or" : [query1, query2]}, sort=[("name", pymongo.ASCENDING), ("vorname", pymongo.ASCENDING)]))
        per_dict = {p["_id"]: tools.repr(util.person, p["_id"], False, True) for p in pe }
        vorgesetzte = st.multiselect("Vorgesetzte", per_dict.keys(), x["vorgesetzte"], format_func = (lambda a: per_dict[a]), placeholder = "Bitte auswählen")
        v = list(util.person.find({"_id": {"$in": vorgesetzte}}, sort=[("name", pymongo.ASCENDING)]))
        vorgesetzte = [d["_id"] for d in v]
    codes_list = []
    for ck in list(util.personencodekategorie.find({}, sort = [("rang", pymongo.ASCENDING)])):
        loc = [x["_id"] for x in list(util.personencode.find({"codekategorie" : ck["_id"]}, sort = [("rang", pymongo.ASCENDING)]))]
        codes_list = codes_list + loc

    code = st.multiselect("Zugehörigkeiten", codes_list, x["code"], format_func = (lambda a: tools.repr(util.personencode, a, False, False)), placeholder = "Bitte auswählen")
    
    col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
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

    st.write("Einstiegs- und Ausstiegsdatum, sowie längere Abwesenheiten können nur im Dekanat verändert werden.")
    if tools.is_dekanat(st.session_state.user):
        col1, col2, col3, col4 = st.columns([1, 2, 1, 2])    
        with col1:
            enable_einstieg = st.toggle("Einstiegsdatum setzen", True if x["einstiegsdatum"] is not None else False)
        with col2:
            if enable_einstieg:
                einstiegsdatum = st.date_input("Eintsiegsdatum", value = x["einstiegsdatum"], format="DD.MM.YYYY")
            else:
                einstiegsdatum = None
        with col3:
            enable_ausstieg = st.toggle("Ausstiegsdatum setzen", True if x["ausstiegsdatum"] is not None else False)
        with col4:
            if enable_ausstieg:
                ausstiegsdatum = st.date_input("Ausstiegsdatum", value = x["ausstiegsdatum"], format="DD.MM.YYYY")
            else:
                ausstiegsdatum = None
        col1, col2, col3, col4 = st.columns([1, 2, 1, 2])    
        with col1:
            enable_abwesend = st.toggle("Abwesenheit setzen", True if x["abwesend_start"] is not None else False)
        if enable_abwesend:
            with col2:
                abwesend_start = st.date_input("Beginn der Abwesenheit", value = x["abwesend_start"], format="DD.MM.YYYY")
            with col4:
                abwesend_ende = st.date_input("Ende der Abwesenheit", value = x["abwesend_ende"], format="DD.MM.YYYY")
        else:
            abwesend_start = None
            abwesend_ende = None

    else:
        einstiegsdatum = x["einstiegsdatum"]
        ausstiegsdatum = x["ausstiegsdatum"]
        abwesend_start = x["abwesend_start"]
        abwesend_ende = x["abwesend_ende"]

    if einstiegsdatum is not None:
        einstiegsdatum = datetime.datetime.combine(einstiegsdatum, datetime.time.min)
    if ausstiegsdatum is not None:
        ausstiegsdatum = datetime.datetime.combine(ausstiegsdatum, datetime.time.max)

    start_exists = (abwesend_start is not None)
    ende_exists = (abwesend_ende is not None)
    if start_exists:
        abwesend_start = datetime.datetime.combine(abwesend_start, datetime.time.min)
    if ende_exists:
        abwesend_ende = datetime.datetime.combine(abwesend_ende, datetime.time.max)
    if (start_exists and not ende_exists) or (ende_exists and not start_exists):
        st.warning("Abwesenheiten können nur eingetragen werden, wenn sowohl Start als auch Ende vorhanden sind.")
        abwesend_start = None
        abwesed_ende = None

    semester_list = st.multiselect("Semester", [x["_id"] for x in util.semester.find(sort = [("kurzname", pymongo.DESCENDING)])], x["semester"], format_func = (lambda a: tools.repr(util.semester, a, False, True)), placeholder = "Bitte auswählen")
    se = list(util.semester.find({"_id": {"$in": semester_list}}, sort=[("rang", pymongo.ASCENDING)]))
    semester_list = [s["_id"] for s in se]

    x_updated = ({"name": name, "name_en": name_en, "vorname": vorname, "name_prefix": name_prefix, "titel": titel, "kennung" : kennung, "gender" : gender, "vorgesetzte" : vorgesetzte, "kommentar": kommentar, "kommentar_html": kommentar_html, "tel1": tel1, "tel2": tel2, "email1": email2, "email1": email2, "raum1" : raum1, "raum2" : raum2, "gebaeude1" : gebaeude1, "gebaeude2" : gebaeude2, "url" : url, "sichtbar": sichtbar, "hp_sichtbar": hp_sichtbar, "einstiegsdatum" : einstiegsdatum, "ausstiegsdatum" : ausstiegsdatum, "abwesend_start" : abwesend_start, "abwesend_ende" : abwesend_ende, "semester": semester_list, "code" : code, "bearbeitet" : bearbeitet})
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
