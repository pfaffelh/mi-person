import streamlit as st
from streamlit_extras.switch_page_button import switch_page 
import pymongo
import pandas as pd
import time
import misc.util as util
import misc.tools as tools
from bson import ObjectId
from misc.config import *
from collections import OrderedDict
import jinja2
import itertools, os

# Soll dazu führen, dass latex-Befehle korrekt behandelt werden.
def latex(s):
    # ersetzt " durch ''
    s = s.replace('"', "''")
    # führt dazu, dass nie mehr %, sondern immer \% steht
    s = s.replace("\%", "%")
    s = s.replace("%", "\%")
    return s

def get_name(person_id, lang = "de"):
    if lang == "de" or util.person.find_one({'_id': person_id})['name_en'] == "":
        res = f"{util.person.find_one({'_id': person_id})['vorname']} {util.person.find_one({'_id': person_id})['name']}"
    else:
        res = util.person.find_one({'_id': person_id})['name_en']
    return res
    
def get_names(person_ids, lang = "de"):
    return [get_name(x, lang) for x in person_ids]

def try_combine_columns(df, sep = ", "):
    column_pairs = itertools.combinations(df.columns, 2)    
    for col1, col2 in column_pairs:
        if (df[col1] == df[col2]).all():
            df.rename(columns = { col1 : sep.join([col1, col2])}, inplace = True)
            df.drop(columns = col2, inplace = True)
            break
    return df

# Combine columns in a dataframe which have the same content.
# Replace identical columns with one column with a combined name.
def combine_columns2(df, sep = ", "):
    cont = True
    while cont:
        df2 = try_combine_columns(df, sep)
        if df.shape[1] == df2.shape[1]:
            cont = False
        else:
            df = df2
    return df

# Combine columns in a dataframe which have the same content.
# Replace identical columns with one column with a combined name.
def combine_columns(df, sep = ", "):
    # Durch die Paare iterieren
    cont = True
    while cont:
        column_pairs = itertools.combinations(df.columns, 2)    
        cont = False
        for col1, col2 in column_pairs:
            # print(col1, col2)
            if (df[col1] == df[col2]).all():
                df.rename(columns = { col1 : sep.join([col1, col2])}, inplace = True)
                df.drop(columns = col2, inplace = True)
                cont = True
                break
    return df



def getraum(raum_id, lang = "de", alter = True):
    otherlang = "en" if lang == "de" else "de"
    r = util.raum.find_one({ "_id": raum_id})
    g = util.gebaeude.find_one({ "_id": r["gebaeude"]})
    name = f"name_{lang}"
    if alter and r[name] == "":
        name = f"name_{otherlang}"
    return latex(", ".join([r[name], f"\href{{{g['url']}}}{{{g[name]}}}"]))

def makemodulname(modul_id, lang = "de", alter = True):
    otherlang = "de" if "lang" == "en" else "en"
    m = util.modul.find_one({"_id": modul_id})
    mname = m[f"name_{lang}"]
    if alter and mname == "":
        mname = m[f"name_{otherlang}"]    
    s = ", ".join([x["kurzname"] for x in list(util.studiengang.find({"_id": { "$in" : m["studiengang"]}, "semester" : { "$elemMatch" : { "$eq" : st.session_state.semester_id}}}))])
    return latex(f"{mname} ({s})")

def makeanforderungname(anforderung_id, lang = "de", alter = True):
    otherlang = "de" if "lang" == "en" else "en"
    a = util.anforderung.find_one({"_id": anforderung_id})
    aname = a[f"name_{lang}"]
    if alter and aname == "":
        aname = a[f"name_{otherlang}"]
    k = util.anforderungkategorie.find_one({ "_id": a["anforderungskategorie"]})["kurzname"]
    #res = aname if k == "Kommentar" else f"{k}: {aname}"
    res = f"{k}: {aname}"
    return latex(res)

def makecode(sem_id, veranstaltung, lang = "de"):
    otherlang = "de" if "lang" == "en" else "en"
    res = ""
    codekategorie_list = [x["_id"] for x in list(util.codekategorie.find({"semester": sem_id, "komm_sichtbar": True}))]
    code_list = [util.code.find_one({"_id": c, "codekategorie": {"$in": codekategorie_list}}) for c in veranstaltung["code"]]
    code_list = [x for x in code_list if x is not None]
    #if len(code_list)>0:
    #    res = ", ".join([c["name"] for c in code_list])
    if len(code_list)>0:
        res = ", ".join([c[f"beschreibung_{lang}"] for c in code_list])
    #if veranstaltung["ects"] != "":
    #    res = ", ".join([res, f"{veranstaltung['ects']} ECTS"])
    return latex(res)

# Die Funktion fasst zB Mo, 8-10, HS Rundbau, Albertstr. 21 \n Mi, 8-10, HS Rundbau, Albertstr. 21 \n 
# zusammen in
# Mo, Mi, 8-10, HS Rundbau, Albertstr. 21 \n Mi, 8-10, HS Rundbau, Albertstr. 21
def make_raumzeit(veranstaltung, lang="de", alter = True):
    otherlang = "de" if "lang" == "en" else "en"
    res = []
    for termin in veranstaltung["woechentlicher_termin"]:
        ta = util.terminart.find_one({"_id": termin['key']})
        if ta["komm_sichtbar"]:
            n = f"name_{lang}"
            if alter and ta[n] == "":
                n = f"name_{otherlang}"
            ta = ta[n]
            if termin['wochentag'] !="":
                # key, raum, zeit, person, kommentar
                key = f"{ta}:" if ta != "" else ""
                # Raum und Gebäude mit Url, zB Hs II.
                r = util.raum.find_one({ "_id": termin["raum"]})                
                raum = getraum(r["_id"], lang, alter)
                # zB Vorlesung: Montag, 8-10 Uhr, HSII, Albertstr. 23a
                if termin['start'] is not None:
                    zeit = f"{str(termin['start'].hour)}{':'+str(termin['start'].minute) if termin['start'].minute > 0 else ''}"
                    if termin['ende'] is not None:
                        zeit = zeit + f"--{str(termin['ende'].hour)}{':'+str(termin['ende'].minute) if termin['ende'].minute > 0 else ''}"
                    zeit = zeit + (" Uhr" if lang == "de" else " h")
                else:
                    zeit = ""
                # zB Mo, 8-10
                tag = util.wochentag[termin['wochentag']][lang]
                # person braucht man, wenn wir dann die Datenbank geupdated haben.
                # person = ", ".join([f"{util.person.find_one({"_id": x})["vorname"]} {util.person.find_one({"_id": x})["name"]}"for x in termin["person"]])
                komm = f"kommentar_{lang}_latex"
                if alter and termin[komm] == "":
                    komm = f"kommentar_{otherlang}_latex"
                kommentar = rf"\newline {termin[komm]}" if termin[komm] != "" else ""
                new = [key, tag, ", ".join([zeit, raum]), kommentar]
                if key in [x[0] for x in res]:
                    new.pop(0)
                    i = [x[0] for x in res].index(key)
                    res[i] = (res[i] + new)
                    res[i].reverse()
                    res[i] = list(OrderedDict.fromkeys(res[i]))
                    res[i].reverse()
                else:
                    res.append(new)
    for termin in veranstaltung["einmaliger_termin"]:
        ta = util.terminart.find_one({"_id": termin['key']})
        if ta["hp_sichtbar"]:
            n = f"name_{lang}"
            if alter and ta[n] == "":
                n = f"name_{otherlang}"
            ta = ta[n]
            # Raum und Gebäude mit Url.
            raeume = list(util.raum.find({ "_id": { "$in": termin["raum"]}}))
            raum = ", ".join([getraum(r["_id"], lang) for r in raeume])
            # zB Vorlesung: Montag, 8-10, HSII, Albertstr. 23a
            if termin['enddatum'] is None:
                termin['enddatum'] = termin['startdatum']
            if termin['startdatum'] is not None:
                startdatum = termin['startdatum'].strftime("%d.%m.")
                if termin['startdatum'] != termin['enddatum']:
                    enddatum = termin['enddatum'].strftime("%d.%m.")
                    datum = "--".join([startdatum, enddatum]) if startdatum != enddatum else startdatum
                else:
                    datum = startdatum
            else:
                datum = ""
            if termin['startzeit'] is not None:
                zeit = termin['startzeit'].strftime("%H:%M")
                if termin['endzeit'] is not None:
                    zeit = zeit + "--" + termin['endzeit'].strftime("%H:%M")
            else:
                zeit = ""
            # person braucht man, wenn wir dann die Datenbank geupdated haben.
            # person = ", ".join([f"{util.person.find_one({"_id": x})["vorname"]} {util.person.find_one({"_id": x})["name"]}"for x in termin["person"]])
            komm = f"kommentar_{lang}_latex"
            if alter and termin[komm] == "":
                komm = f"kommentar_{otherlang}_latex"
            #kommentar = rf"\newline {termin[komm]}" if termin[komm] != "" else ""
            kommentar = rf"{termin[komm]}" if termin[komm] != "" else ""
            if datum != "" or zeit != "" or raum != "":
                kommentar = ", " + kommentar                
            new = [ta, datum, zeit, raum, kommentar]
            res.append(new)
    res = [latex(f"{x[0]} {(', '.join([z for z in x if z !='' and x.index(z)!=0]))}") for x in res]
    return res

def makedata(sem_kurzname, lang, alter):
    semester = util.semester.find_one({"kurzname": sem_kurzname})
    sem_id = semester["_id"]
    
    otherlang = "en" if lang == "de" else "de"
    rubriken = list(util.rubrik.find({"semester": sem_id, "hp_sichtbar": True}, sort=[("rang", pymongo.ASCENDING)]))
    
    data = {}

    data["vorspann"] = semester[f"vorspann_kommentare_{lang}"]
    data["wasserzeichen"] = semester[f"wasserzeichen_kommentare_{lang}"]
    
    data["rubriken"] = []

    for rubrik in rubriken:
        r_dict = {}

        r_dict["titel"] = latex(rubrik[f"titel_{lang}"])
        if alter and r_dict["titel"] == "":
            r_dict["titel"] = latex(rubrik[f"titel_{otherlang}"])

        r_dict["veranstaltung"] = []
        # Falls komm == True werden nur Veranstaltungen mit komm_sichtbar == True komm aufgenommen
        sem_id = st.session_state.semester_id
        veranstaltungen = list(util.veranstaltung.find({"rubrik": rubrik["_id"], "komm_sichtbar" : True}, sort=[("rang", pymongo.ASCENDING)]))
        
        for veranstaltung in veranstaltungen:
            v_dict = {}

            v_dict["titel"] = latex(veranstaltung[f"name_{lang}"])
            v_dict["kurzname"] = veranstaltung["kurzname"]

            if alter and v_dict["titel"] == "":
                v_dict["titel"] = latex(veranstaltung[f"name_{otherlang}"])

            v_dict["url"] = latex(veranstaltung["url"])

            v_dict["dozent"] = latex(", ".join(get_names(veranstaltung["dozent"], lang)))
            assistent = latex(", ".join(get_names(veranstaltung["assistent"], lang)))

            if assistent:
                if lang == "de":
                    v_dict["person"] = ", Assistenz: ".join([v_dict["dozent"], assistent])
                else:
                    v_dict["person"] = ", Assistant: ".join([v_dict["dozent"], assistent])
            else:
                v_dict["person"] = v_dict["dozent"]
            # raumzeit ist der Text, der unter der Veranstaltung im kommentierten VVZ steht.

            v_dict["raumzeit"] = make_raumzeit(veranstaltung, lang = lang, alter = alter)

            v_dict["inhalt"] = veranstaltung[f"inhalt_{lang}"]
            if alter and v_dict["inhalt"] == "":
                v_dict["inhalt"] = veranstaltung[f"inhalt_{otherlang}"]
            
            v_dict["literatur"] = veranstaltung[f"literatur_{lang}"]
            if alter and v_dict["literatur"] == "":
                v_dict["literatur"] = veranstaltung[f"literatur_{otherlang}"]
            
            v_dict["vorkenntnisse"] = veranstaltung[f"vorkenntnisse_{lang}"]
            if alter and v_dict["vorkenntnisse"] == "":
                v_dict["vorkenntnisse"] = veranstaltung[f"vorkenntnisse_{otherlang}"]

            v_dict["kommentar"] = veranstaltung[f"kommentar_latex_{lang}"]
            if alter and v_dict["kommentar"] == "":
                v_dict["kommentar"] = veranstaltung[f"kommentar_latex_{otherlang}"]

            v_dict["code"] = makecode(sem_id, veranstaltung, lang)
            
            # Module löschen, die in keinem Studiengang des Semesters vorkommen
            mod_verw = []
            for m in veranstaltung["verwendbarkeit_modul"]:
                m1 = util.modul.find_one({"_id": m})
                if list(util.studiengang.find({"_id": { "$in" : m1["studiengang"]}, "semester" : { "$elemMatch" : { "$eq" : st.session_state.semester_id}}})) != []:
                    mod_verw.append(m)

            v_dict["verwendbarkeit_modul"] = [{"id": str(x), "titel": makemodulname(x, lang, alter)} for x in mod_verw]
            v_dict["verwendbarkeit_anforderung"] = [{"id": str(x), "titel": makeanforderungname(x, lang, alter)} for x in veranstaltung["verwendbarkeit_anforderung"]]

            for x in veranstaltung["verwendbarkeit"]:
                x["modulname"] = makemodulname(x["modul"], lang, alter)
                x["anforderungname"] = makeanforderungname(x["anforderung"], lang, alter)
                x["modulname_ects"] = f"{x['modulname']} -- {x['ects']:.3g} ECTS"
                x["modul_index"] = veranstaltung["verwendbarkeit_modul"].index(x["modul"])
                x["modul"] = str(x["modul"])
                x["anforderung_index"] = veranstaltung["verwendbarkeit_anforderung"].index(x["anforderung"])
                x["anforderung"] = str(x["anforderung"])
                x["modulname_ects"] = f"{x['modulname']} -- {x['ects']:.3g}~ECTS"
            try:
                df = pd.DataFrame.from_records(veranstaltung["verwendbarkeit"])
                # andernfalls werden die Spalten alphabetisch sortiert.
                df["modulname_ects"] = pd.Categorical(df["modulname_ects"], categories=df["modulname_ects"].unique(), ordered=True)
                
                df.sort_values(by = ["modul_index", "ects", "anforderung_index"], inplace=True)
                df["modulname_ects"] = pd.Categorical(df["modulname_ects"], categories=df["modulname_ects"].unique(), ordered=True)
                crosstab = pd.crosstab(df["anforderungname"], df["modulname_ects"]) > 0
                anforderungname = [makeanforderungname(x, lang, alter) for x in veranstaltung["verwendbarkeit_anforderung"]]

                crosstab["reorder"] = [anforderungname.index(a) for a in crosstab.index]                
                crosstab.sort_values(by = "reorder", inplace=True)
                crosstab.drop(columns = "reorder", inplace=True)

#                v_dict["verwendbarkeit"] = crosstab
                v_dict["verwendbarkeit"] = combine_columns(crosstab, sep = " \\item ")
            except:
                v_dict["verwendbarkeit"] = pd.DataFrame()

            v_dict["verwendbarkeit_hat_kommentar"] = any([item[0:10] == "Kommentar:" for item in v_dict["verwendbarkeit"].index])
            v_dict["kommentar_verwendbarkeit"] = latex(veranstaltung[f"kommentar_verwendbarkeit_{lang}"])
            r_dict["veranstaltung"].append(v_dict)

        # Rubrik nur dann hinzufügen, wenn hier auch Veranstaltungen sind
        if veranstaltungen:
            data["rubriken"].append(r_dict)
    return data

# Für die Kommentare:
# Momentan gibt es so etwas wie: '4-stündige Vorlesung mit 2-stündiger Übung' oder 'Vorlesung mit Praktischer Übung', was jeweils direkt unter der Veranstaltung selbst steht. Ist das wichtig (dann muss es als Feld ins vvz) oder nicht?
# Ein wöchentlicher Termin wird nur dann angezeigt wenn er einen Wochentag hat. Wenn er einen Wochentag hat, wird davon ausgegangen, dass er auch eine Uhrzeit hat.
# 8:00 wird als 8 ausgegeben, aber 8:15 als 8:15. 
# Braucht einmaliger_termin noch eine true/false-Variable, je nachdem ob er in den Kommentaren auftauchen soll? 

latex_jinja_env = jinja2.Environment(
    block_start_string = '\BLOCK{',
    block_end_string = '}',
    variable_start_string = '\VAR{',
    variable_end_string = '}',
    comment_start_string = '\#{',
    comment_end_string = '}',
    line_statement_prefix = '%%',
    line_comment_prefix = '%#',
    trim_blocks = True,
    autoescape = False,
    loader = jinja2.FileSystemLoader(os.path.abspath('.'))
)
