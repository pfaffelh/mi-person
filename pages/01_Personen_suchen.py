import streamlit as st
from streamlit_extras.switch_page_button import switch_page 
import datetime
from io import BytesIO
import pymongo
import pandas as pd

# Transform df to xls
def to_excel(df):
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        worksheet = writer.sheets['Sheet1']

        # Automatische Anpassung der Spaltenbreite an die Inhalte
        for col in worksheet.columns:
            max_length = 0
            col_letter = col[0].column_letter  # Spaltenbuchstabe (z.B., 'A', 'B', 'C')
            for cell in col:
                try:
                    max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = max_length + 2  # +2 für Puffer
            worksheet.column_dimensions[col_letter].width = adjusted_width
    return output.getvalue()


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
st.session_state.page = "Suchen"

if st.session_state.logged_in:
    st.header("Suche nach Personen")
    st.write("...auf die folgendes zutrifft:")
    st.write("(Die einzelnen Zeilen sind mit 'und' verknüpft. Die eingegebenen Wörter im Textfeld sind mit 'oder' verknüpft.)")
    # QUERY
    # Stichtag
    stichtag = st.date_input("Stichtag", value = datetime.datetime.today(), format="DD.MM.YYYY")
    stichtag = datetime.datetime.combine(stichtag, datetime.time(12,0))
    temporaer = st.toggle("Temporäre Abwesenheiten mit berücksichtigen", False)
    if temporaer:
        query = {"$and": [
            {
                "$or": [
                    {"einstiegsdatum": None},
                    {"einstiegsdatum": {"$lt": stichtag}}
                ]
            },
            {
                "$or": [
                    {"ausstiegsdatum": None},
                    {"ausstiegsdatum": {"$gt": stichtag}}
                ]
            },
            {
                "$or": [
                    {"abwesend_start": None},
                    {"abwesend_start": {"$gt": stichtag}}
                ]
            },
            {
                "$or": [
                    {"abwesend_ende": None},
                    {"abwesend_ende": {"$lt": stichtag}}
                ]
            },
            
            ]}
    else:
        query = {"$and": [
            {
                "$or": [
                    {"einstiegsdatum": None},
                    {"einstiegsdatum": {"$lt": stichtag}}
                ]
            },
            {
                "$or": [
                    {"ausstiegsdatum": None},
                    {"ausstiegsdatum": {"$gt": stichtag}}
                ]
            }]}

    # Auswahl von Codes
    codes_list = []
    codekategorie_list = list(util.personencodekategorie.find({}, sort = [("rang", pymongo.ASCENDING)]))
    for ck in codekategorie_list:
        loc = [x["_id"] for x in list(util.personencode.find({"codekategorie" : ck["_id"]}, sort = [("rang", pymongo.ASCENDING)]))]
        codes_list = codes_list + loc

    code = st.multiselect("Zugehörigkeiten (d.h. es werden Personen gesucht, die all die angegebenen Zugehörigkeiten haben)", codes_list, [], format_func = (lambda a: tools.repr(util.personencode, a, False, False)), placeholder = "Bitte auswählen")

    # Erstellung der Query
    if code:
        query["code"] = {"$all": code}

    result = list(util.person.find(query, sort=[("name", pymongo.ASCENDING), ("vorname", pymongo.ASCENDING)]))

    st.divider()
    st.write("Folgende Felder werden ausgegeben")
    # Auswahl der Ausgabe

    ausgabe_list_all = ["Name", "Titel", "Abschluss", "RZ-Kennung", "Gender", "Telefon", "Mail", "Vorgesetzte", "Raum", "Homepage"]
    if tools.is_dekanat(st.session_state.user):
        ausgabe_list_all = ausgabe_list_all + ["Vertragsdauer"]

    codekategorie_list_all = [x["name_de"] for x in codekategorie_list]
    ausgaben = st.multiselect("Was soll ausgegebn werden?", ausgabe_list_all + codekategorie_list_all, default = ["Name", "Mail"])

    # TODO
    # für dekanat: einstiegsdatum, ausstiegsdatum, abwesend_start, abwesend_ende

    dict = {}
    if "Name" in ausgaben:
        dict["Nachname"] = [r["name"] for r in result]
        dict["Vorname"] = [r["vorname"] for r in result]
        dict["name_prefix"] = [r["name_prefix"] for r in result]
    if "Titel" in ausgaben:
        dict["Titel"] = [r["titel"] for r in result]
    if "Abschluss" in ausgaben:
        dict["Abschluss"] = [r["abschluss"] for r in result]
    if "RZ-Kennung" in ausgaben:
        dict["RZ-Kennung"] = [r["kennung"] for r in result]
    if "Gender" in ausgaben:
        dict["Gender"] = [r["gender"] for r in result]
    if "Telefon" in ausgaben:
        dict["Telefon"] = [", ".join(x for x in [r["tel1"], r["tel2"]] if x) for r in result]
    if "Mail" in ausgaben:
        dict["Mail"] = [", ".join(x for x in [r["email1"], r["email2"]] if x) for r in result]
    if "Vorgesetzte" in ausgaben:
        dict["Vorgesetzte"] = [", ".join(tools.repr(util.person, x, False, True) for x in r["vorgesetzte"]) for r in result]
    if "Raum" in ausgaben:
        dict["Raum"] = [", ".join(f"{x[0]} ({tools.repr(util.gebaeude, x[1], False, True)})" for x in zip([r["raum1"], r["raum2"]], [r["gebaeude1"], r["gebaeude2"]]) if x[0]) for r in result]
    if "Homepage" in ausgaben:
        dict["Homepage"] = [r["url"] for r in result]
    if "Vertragsdauer" in ausgaben:
        dict["Einstiegsdatum"] = ["" if r["einstiegsdatum"] is None else r["einstiegsdatum"].strftime("%d.%m.%Y") for r in result]
        dict["Ausstiegsdatum"] = ["" if r["ausstiegsdatum"] is None else r["ausstiegsdatum"].strftime("%d.%m.%Y") for r in result]
        dict["Kommentar Stelle"] = [r["kommentar_stelle"] for r in result]
        dict["Abwesenheit Start"] = ["" if r["abwesend_start"] is None else r["abwesend_start"].strftime("%d.%m.%Y") for r in result]
        dict["Abwesenheit Ende"] = ["" if r["abwesend_ende"] is None else r["abwesend_ende"].strftime("%d.%m.%Y") for r in result]
        dict["Abwesenheit Kommentar"] = [r["kommentar_abwesend"] for r in result]

    for ck in codekategorie_list:
        loc = [x["_id"] for x in list(util.personencode.find({"codekategorie" : ck["_id"]}, sort = [("rang", pymongo.ASCENDING)]))]
        if ck["name_de"] in ausgaben:
            dict[ck["name_de"]] = [", ".join(tools.repr(util.personencode, x, False, True) for x in r["code"] if x in loc) for r in result] 


    df = pd.DataFrame(dict)

    st.divider()

    st.data_editor(df, use_container_width=True, hide_index=True)   
    # xls Export
    output = BytesIO()
    excel_data = to_excel(df)
    st.download_button(
        label="Download Excel-Datei",
        data=excel_data,
        file_name="personen.xls",
        mime="application/vnd.ms-excel"
    )

else: 
    switch_page("PERSON")

st.sidebar.button("logout", on_click = tools.logout)
