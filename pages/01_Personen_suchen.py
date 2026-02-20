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
    stichtag = datetime.datetime.combine(stichtag, datetime.time.min)

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
    for ck in list(util.personencodekategorie.find({}, sort = [("rang", pymongo.ASCENDING)])):
        loc = [x["_id"] for x in list(util.personencode.find({"codekategorie" : ck["_id"]}, sort = [("rang", pymongo.ASCENDING)]))]
        codes_list = codes_list + loc

    code = st.multiselect("Zugehörigkeiten", codes_list, [], format_func = (lambda a: tools.repr(util.personencode, a, False, False)), placeholder = "Bitte auswählen")

    # Erstellung der Query
    if code:
        query["code"] = {"$elemMatch": { "$in": code}}

    result = list(util.person.find(query, sort=[("name", pymongo.ASCENDING), ("vorname", pymongo.ASCENDING)]))

    st.divider()
    st.write("Folgende Felder werden ausgegeben")
    # Auswahl der Ausgabe
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        ausgabe_emails = st.checkbox("Emails", True, key = "emails1")
    with col2:
        ausgabe_tels = st.checkbox("Telefonnummern", True)
    with col3:
        ausgabe_raeume = st.checkbox("Räume", True, key = "raeume1")
    with col4:
        ausgabe_url = st.checkbox("Homepage", True, key = "url1")

    dict = {}
    dict["Nachname"] = [r["name"] for r in result]
    dict["Vorname"] = [r["vorname"] for r in result]
    if ausgabe_emails:
        dict["Email"] = [f"{r['email1']}, {r['email2']}" if r["email2"] != "" else r['email1'] for r in result]
    if ausgabe_tels:
        dict["Telefon"] = [f"{r['tel1']}, {r['tel2']}" if r["tel2"] != "" else r['tel1'] for r in result]
    if ausgabe_raeume:
        dict["Raum"] = [f"{r['raum1']} ({tools.repr(util.gebaeude, r["gebaeude1"], False, True)}), {r['raum2']} ({tools.repr(util.gebaeude, r["gebaeude2"], False, True)})" if r["raum2"] != "" else f"{r['raum1']} ({tools.repr(util.gebaeude, r["gebaeude1"], False, True)})" for r in result]
    if ausgabe_url:
        dict["Homepage"] = [r["url"] for r in result]

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
