import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import pymongo
import ldap
import misc.util as util
from bson import ObjectId
from misc.config import *
from datetime import datetime

# st.toast() direkt vor st.rerun() (oder am Ende eines on_click-Callbacks) wird
# oft nur als Flash gezeigt: der Rerun beginnt, bevor das Frontend den Toast
# voll dargestellt hat. flash() parkt die Nachricht in session_state;
# show_pending_toasts() (im display_navigation aufgerufen) zeigt sie auf dem
# nächsten Run mit voller Standard-Dauer an.
def flash(msg):
    st.session_state.setdefault("_pending_toasts", []).append(msg)

def show_pending_toasts():
    for msg in st.session_state.pop("_pending_toasts", []):
        st.toast(msg)

# Dedupliziert find_one-Lookups innerhalb eines Reruns (und über kurze
# Rerun-Folgen via TTL). Streamlits Hasher kennt bson.ObjectId nicht, daher
# zwingend hash_funcs={ObjectId: str}; ein führender Underscore wäre falsch
# (würde alle IDs auf denselben Cache-Slot mappen).
@st.cache_data(ttl=5, hash_funcs={ObjectId: str})
def _doc(coll_name, doc_id):
    coll = util._vvz_db[coll_name]
    return coll.find_one({"_id": doc_id})

def move_up(collection, x, query = {}):
    query["rang"] = {"$lt": x["rang"]}
    target = collection.find_one(query, sort = [("rang",pymongo.DESCENDING)])
    if target:
        n= target["rang"]
        collection.update_one({"_id": target["_id"]}, {"$set": {"rang": x["rang"]}})
        collection.update_one({"_id": x["_id"]}, {"$set": {"rang": n}})
        _doc.clear()

def move_down(collection, x, query = {}):
    query["rang"] = {"$gt": x["rang"]}
    target = collection.find_one(query, sort = [("rang", pymongo.ASCENDING)])
    if target:
        n= target["rang"]
        collection.update_one({"_id": target["_id"]}, {"$set": {"rang": x["rang"]}})
        collection.update_one({"_id": x["_id"]}, {"$set": {"rang": n}})
        _doc.clear()

def move_up_list(collection, id, field, element):
    list = collection.find_one({"_id": id})[field]
    i = list.index(element)
    if i > 0:
        x = list[i-1]
        list[i-1] = element
        list[i] = x
    collection.update_one({"_id": id}, { "$set": {field: list}})
    _doc.clear()

def move_down_list(collection, id, field, element):
    list = collection.find_one({"_id": id})[field]
    i = list.index(element)
    if i+1 < len(list):
        x = list[i+1]
        list[i+1] = element
        list[i] = x
    collection.update_one({"_id": id}, { "$set": {field: list}})
    _doc.clear()

def remove_from_list(collection, id, field, element):
    collection.update_one({"_id": id}, {"$pull": {field: element}})
    _doc.clear()

def update_confirm(collection, x, x_updated, reset = True):
    util.logger.info(f"User {st.session_state.user} hat in {st.session_state.collection_name[collection]} Item {repr(collection, x['_id'])} geändert.")
    collection.update_one({"_id" : x["_id"]}, {"$set": x_updated })
    _doc.clear()
    if reset:
        reset_vars("")
    flash("🎉 Erfolgreich geändert!")

def new(collection, ini = {}, switch = True):
    if list(collection.find({ "rang" : { "$exists": True }})) != []:
        z = list(collection.find(sort = [("rang", pymongo.ASCENDING)]))
        rang = z[0]["rang"]-1
        st.session_state.new[collection]["rang"] = rang
    for key, value in ini.items():
        st.session_state.new[collection][key] = value
    st.session_state.new[collection].pop("_id", None)
    x = collection.insert_one(st.session_state.new[collection])
    _doc.clear()
    st.session_state.edit=x.inserted_id
    util.logger.info(f"User {st.session_state.user} hat in {st.session_state.collection_name[collection]} ein neues Item angelegt.")
    if switch:
        switch_page(f"{st.session_state.collection_name[collection].lower()} edit")


# Finde in collection.field die id, und gebe im Datensatz return_field zurück. Falls list=True,
# dann ist collection.field ein array.
def references(collection, field, list = False):
    res = {}
    for x in st.session_state.abhaengigkeit[collection]:
        res = res | { collection: references(x["collection"], x["field"], x["list"]) }
    if list:
        z = list(collection.find({field: {"$elemMatch": {"$eq": id}}}))
    else:
        z = list(collection.find({field: id}))
        res = {collection: [t["_id"] for t in z]}
    return res

# Finde in collection.field die id, und gebe im Datensatz return_field zurück. Falls list=True,
# dann ist collection.field ein array.
def find_dependent_items(collection, id):
    res = []
    for x in st.session_state.abhaengigkeit[collection]:
        if x["list"]:
            for y in list(x["collection"].find({x["field"].replace(".$",""): { "$elemMatch": { "$eq": id }}})):
                res.append(repr(x["collection"], y["_id"]))
        else:
            for y in list(x["collection"].find({x["field"]: id})):
                res.append(repr(x["collection"], y["_id"]))
    return res

def delete_item_update_dependent_items(collection, id, switch = True):
    if collection in st.session_state.leer.keys() and id == st.session_state.leer[collection]:
            flash("Fehler! Dieses Item kann nicht gelöscht werden!")
            reset_vars("")
    else:
        for x in st.session_state.abhaengigkeit[collection]:
            if x["list"]:
                x["collection"].update_many({x["field"].replace(".$",""): { "$elemMatch": { "$eq": id }}}, {"$pull": { x["field"] : id}})
            else:
                st.write(st.session_state.collection_name[x["collection"]])
                x["collection"].update_many({x["field"]: id}, { "$set": { x["field"].replace(".", ".$."): st.session_state.leer[collection]}})
        s = ("  \n".join(find_dependent_items(collection, id)))
        if s:
            s = f"\n{s}  \ngeändert."
        util.logger.info(f"User {st.session_state.user} hat in {st.session_state.collection_name[collection]} item {repr(collection, id)} gelöscht, und abhängige Felder geändert.")
        collection.delete_one({"_id": id})
        _doc.clear()
        reset_vars("")
        flash(f"🎉 Erfolgreich gelöscht!  {s}")
        if switch:
            switch_page(st.session_state.collection_name[collection].lower())

# Zum Einstellen der Codes für das gesamte Semester
def codes_uebernehmen(df):
    for p in df.to_dict(orient='records'):
        pid = ObjectId(p["_id"])
        del p["_id"]
        del p["Name"]
        code_all = [ObjectId(key) for key in p.keys()]
        co = [ObjectId(key) for key, value in p.items() if value]
        util.person.update_one({"_id" : pid}, {"$pull" : {"code" : { "$in" : code_all}}})
        util.person.update_one({"_id" : pid}, {"$push" : {"code" : { "$each" : co}}})
    _doc.clear()

# Die Authentifizierung gegen den Uni-LDAP-Server
def authenticate(username, password):
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, 2.0)
    user_dn = "uid={},{}".format(username, base_dn)
    try:
        l = ldap.initialize(server)
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(user_dn, password)
        return True
    except ldap.INVALID_CREDENTIALS:
        return False
    except ldap.LDAPError as error:
        util.logger.warning(f"LDAP-Error: {error}")
        return False

def can_edit(username):
    u = st.session_state.users.find_one({"rz": username})
    id = st.session_state.group.find_one({"name": app_name})["_id"]
    return (True if id in u["groups"] else False)

def is_dekanat(username):
    u = st.session_state.users.find_one({"rz": username})
    id = st.session_state.group.find_one({"name": "dekanat"})["_id"]
    return (True if id in u["groups"] else False)
    #return (True if username in dekanat else False)

def logout():
    st.session_state.logged_in = False
    util.logger.info(f"User {st.session_state.user} hat sich ausgeloggt.")

def reset_vars(text=""):
    st.session_state.edit = ""
    if text != "":
        flash(text)

def display_navigation():
    show_pending_toasts()
    st.markdown("<style>.st-emotion-cache-16txtl3 { padding: 2rem 2rem; }</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.image("static/ufr.png", use_container_width=True)
    st.sidebar.write("<hr style='height:1px;margin:0px;;border:none;color:#333;background-color:#333;' /> ", unsafe_allow_html=True)
    st.sidebar.page_link("pages/01_Personen_suchen.py", label="Suchen/Datenexport")
    st.sidebar.write("<hr style='height:1px;margin:0px;;border:none;color:#333;background-color:#333;' /> ", unsafe_allow_html=True)
    st.sidebar.page_link("pages/03_Personen.py", label="Personen")
    st.sidebar.page_link("pages/10_Codes.py", label="Codes")

# short Version ohne abhängige Variablen
def repr(collection, id, show_collection = True, short = False):
    x = _doc(collection.name, id)
    if collection == util.gebaeude:
        res = x['name_de']
    elif collection == util.raum:
        res = x['name_de']
    elif collection == util.semester:
        res = x['kurzname'] if short else x["name_de"]
    elif collection == util.rubrik:
        sem = _doc("semester", x["semester"])["kurzname"]
        res = x['titel_de'] if short else f"{x['titel_de']} ({sem})"
    elif collection == util.person:
        res = f"{x['name']}, {x['name_prefix']}" if short else f"{x['name']}, {x['vorname']}"
    elif collection == util.personencode:
        kat = _doc("personencodekategorie", x["codekategorie"])["name_de"]
        res = x['name'] if short else f"{kat}: {x['name']}"
    elif collection == util.personencodekategorie:
        res = x['name_de']
    elif collection == util.studiengang:
        res = f"{x['name']}"
    elif collection == util.modul:
        res = []
        for id1 in x["studiengang"]:
            stu = util.studiengang.find_one({"_id" : id1, "semester" : { "$elemMatch" : { "$eq" : st.session_state.semester_id}}})
            if stu:
                res.append(stu["kurzname"])
        s = ", ".join(res)
        res = x['name_de'] if short else f"{x['name_de']} ({s})"
    elif collection == util.anforderung:
        an = _doc("anforderungkategorie", x["anforderungskategorie"])["kurzname"]
        if an.strip() == "Kommentar":
            res = f"{x['name_de'].strip()}"
        else:
            res = f"{an.strip()}: {x['name_de'].strip()}"
    elif collection == util.anforderungkategorie:
        res = x['name_de']
    elif collection == util.codekategorie:
        res = x['name_de']
    elif collection == util.veranstaltung:
        s = ", ".join([_doc("person", id1)["name"] for id1 in x["dozent"]])
        sem = _doc("semester", x["semester"])["kurzname"]
        res = x['name_de'] if short else f"{x['name_de']} ({s}, {sem})"
    elif collection == st.session_state.terminart:
        res = f"{x['name_de']}"
    elif collection == st.session_state.dictionary:
        res = f"{x['de']}: {x['en']}"
    elif collection == util.planungveranstaltung:
        res = f"{x['name']}"
    elif collection == util.planung:
        res = f"{', '.join([repr(util.person, y, False, True) for y in x['dozent']])}"
    if show_collection:
        res = f"{st.session_state.collection_name[collection]}: {res}"
    return res

def hour_of_datetime(dt):
    return "" if dt is None else str(dt.hour)

def next_semester_kurzname(kurzname):
    a = int(kurzname[:4])
    b = kurzname[4:]
    return f"{a+1}SS" if b == "WS" else f"{a}WS"

def last_semester_kurzname(kurzname):
    a = int(kurzname[:4])
    b = kurzname[4:]
    return f"{a}SS" if b == "WS" else f"{a-1}WS"

def semester_name_de(kurzname):
    a = int(kurzname[:4])
    b = kurzname[4:]
    c = f"/{a+1}" if b == "WS" else ""
    return f"{'Wintersemester' if b == 'WS' else 'Sommersemester'} {a}{c}"

def semester_name_en(kurzname):
    a = int(kurzname[:4])
    b = kurzname[4:]
    c = f"/{a+1}" if b == "WS" else ""
    return f"{'Winter term' if b == 'WS' else 'Summer term'} {a}{c}"

def new_semester_dict():
    most_current_semester = util.semester.find_one({}, sort = [("rang", pymongo.DESCENDING)])
    kurzname = next_semester_kurzname(most_current_semester["kurzname"])
    name_de = semester_name_de(kurzname)
    name_en = semester_name_en(kurzname)
    return {"kurzname": kurzname, "name_de": name_de, "name_en": name_en, "rubrik":[], "code": [], "veranstaltung": [], "hp_sichtbar": True, "rang": most_current_semester["rang"]+1}
