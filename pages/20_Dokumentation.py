import streamlit as st
from streamlit_extras.switch_page_button import switch_page

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
st.session_state.page = "Dokumentation"

if st.session_state.logged_in:
    st.header("Dokumentation")

    with st.expander("Allgemeines"):
        st.markdown("""
In dieser App werden die Personen des Mathematischen Instituts verwaltet: Kontaktdaten, Zugehörigkeiten (Abteilung, Statusgruppe, ...), Vertragsdaten und Beisitze. Die Daten liegen in derselben Datenbank wie das Vorlesungsverzeichnis; Personen können daher auch in der App VVZ bearbeitet werden.

**Aus diesen Daten werden Webseiten und Verzeichnisse erzeugt.** Änderungen hier sind also nach außen sichtbar:
- **Personenseiten der Homepage:** Die Mitarbeiter:innen-Listen des Instituts und der Abteilungen werden aus dieser Datenbank erzeugt, gegliedert nach Statusgruppen. Angezeigt werden Name (mit Titel und Link auf die Homepage der Person), Email, Telefon, Raum und der _Kommentar für Homepage_. Welche Personen erscheinen, steht unter _Person anlegen/editieren_.
- **Vorlesungsverzeichnis:** Die Namen der Lehrenden bei den Veranstaltungen kommen ebenfalls von hier.
- **Adressbuch (LDAP) des Instituts:** Alle Personen, die noch nicht ausgestiegen sind und eine Email-Adresse oder Telefonnummer haben, werden regelmäßig in das LDAP des Instituts übertragen, mit Name, Email, Telefon und Abteilung.

**Navigation (links):**
- _Suchen/Datenexport_: Personen nach verschiedenen Kriterien suchen und als Excel-Datei herunterladen, siehe _Daten exportieren_.
- _Warnungen_: Inkonsistenzen in der Datenbank, z.B. aktuelle Personen ohne Email-Adresse oder ohne Abteilung. Oben kann man eine Abteilung auswählen. Standardmäßig werden nur aktuelle Personen berücksichtigt, die einer Statusgruppe angehören. Schaltet man das aus, erscheinen zusätzlich die Personen ohne Statusgruppe. Die Warnungen sollten regelmäßig abgearbeitet werden, siehe _Für Abteilungssekretariate_.
- _Personen_: Liste aller Personen, gefiltert nach Codes und danach, ob die Person aktuell oder ehemalig ist. Von hier aus werden Personen angelegt und bearbeitet.
- _Codes_: Die Codekategorien (z.B. _Abteilung_, _Statusgruppe_, _Studiendekanat_) und die zugehörigen Codes (z.B. _MSt_, _Doktorand:innen_, _beisitz_), die den Personen als _Zugehörigkeiten_ zugeordnet werden.

**Speichern und gleichzeitiges Bearbeiten:** Bei jedem Speichern wird vermerkt, wer wann zuletzt bearbeitet hat. Hat jemand anderes eine Person geändert, während man sie selbst offen hatte, wird nicht gespeichert, sondern gewarnt. Die Anzeige zeigt dann den aktuellen Stand; eigene, noch nicht gespeicherte Eingaben bleiben in den Feldern stehen und können erneut gespeichert werden.
""")

    with st.expander("Ablauf"):
        st.markdown("""
Der häufigste Ablauf für eine neue Person:
1. **Studiendekanat:** Bei der Planung des kommenden Semesters wird die Person angelegt, damit sie im Vorlesungsverzeichnis eingetragen werden kann. Zu diesem Zeitpunkt fehlen meist noch viele Informationen (Email, Raum, Telefon, ...).
2. **Dekanat:** Bei der Erstellung des Arbeitsvertrages werden die Vertragsdaten eingetragen: Einstiegs- und Ausstiegsdatum, Kommentar zur Stelle, siehe _Für das Dekanat_.
3. **Abteilungssekretariat:** Bei Arbeitsbeginn wird der Rest eingetragen: Email, Telefon, Raum, Vorgesetzte, Abteilung, Statusgruppe usw., siehe _Für Abteilungssekretariate_.

Bevor man eine Person neu anlegt, sollte man unter _Personen_ nachsehen, ob es sie nicht schon gibt, etwa weil sie früher schon einmal am Institut war. Beim Anlegen einer Person, deren Name und Vorname es schon gibt, erscheint eine Warnung.
""")

    with st.expander("Person anlegen/editieren"):
        st.markdown("""
Unter _Personen_ legt man mit _Neue Person hinzufügen_ eine Person an oder klickt auf eine bestehende Person, um sie zu bearbeiten. Gespeichert wird mit einem der beiden Buttons _Speichern_ (oben oder unten); _Zurück ohne Speichern_ verwirft die Änderungen.

**Die Felder:**
- _Name (de)_, _Vorname_, _Titel_, _höchster Abschluss_. _Name (en)_ nur ausfüllen, falls er auf Englisch anders geschrieben wird. Die _Abkürzung des Vornamens_ (z.B. _P._) wird in Kurzdarstellungen verwendet, etwa im Vorlesungsverzeichnis.
- _Vorgesetzte_: eine oder mehrere Personen.
- _Gender_, _RZ-Kennung_.
- _Zugehörigkeiten_: Codes aus allen Codekategorien, insbesondere die _Abteilung_ (auch mehrere möglich) und die _Statusgruppe_.
- _Email 1/2_, _Telefonnummer 1/2_, _Gebäude 1/2_, _Raum 1/2_, _Homepage_. Leerzeichen in Email-Adressen werden beim Speichern entfernt.
- _Kommentar für Homepage_ erscheint auf den Personenseiten der Homepage neben der Person; _Kommentar (intern)_ ist nur hier sichtbar.
- Vertragsdaten (Einstiegs- und Ausstiegsdatum, Kommentar zur Stelle, Abwesenheiten) können nur vom Dekanat geändert werden, siehe _Für das Dekanat_.
- _Semester_: die Semester, in denen die Person gelehrt hat. Wird in der Regel über das Vorlesungsverzeichnis gepflegt.
- _Beisitze der letzten 365 Tage_ (ganz unten), siehe _Für das Prüfungsamt_.

**Spezialfälle:**
- **Auf Homepages sichtbar** ist standardmäßig an und wird nur ausgeschaltet, wenn eine Person ausdrücklich nicht auf der Homepage erscheinen möchte.
- **Ohne Statusgruppe** erscheint eine Person ebenfalls nicht auf den Personenseiten der Homepage, auch wenn _Auf Homepages sichtbar_ an ist, denn diese Seiten sind nach Statusgruppen gegliedert. Jede aktuelle Person sollte also eine Statusgruppe haben.
- **Ohne Abteilung** erscheint eine Person nicht auf den Personenseiten der Abteilung, sondern höchstens in der Liste des ganzen Instituts.
- **Einstiegsdatum in der Zukunft:** Die Person erscheint erst ab diesem Tag auf der Homepage. **Ausstiegsdatum in der Vergangenheit:** Die Person erscheint nicht mehr auf der Homepage und nicht mehr im Adressbuch (LDAP). Personen werden in der Regel nicht gelöscht, sondern bekommen ein Ausstiegsdatum; so bleiben z.B. frühere Lehrveranstaltungen erhalten.
- **Person löschen:** Vorher wird angezeigt, welche anderen Einträge (z.B. Veranstaltungen) davon betroffen sind. Löschen nur, wenn eine Person versehentlich oder doppelt angelegt wurde.
""")

    with st.expander("Daten exportieren"):
        st.markdown("""
Unter _Suchen/Datenexport_ werden Personen gesucht und als Tabelle angezeigt, die man als Excel-Datei herunterladen kann. Die einzelnen Einstellungen sind mit _und_ verknüpft.

- **Stichtag:** Es werden nur Personen gefunden, die am Stichtag am Institut sind, d.h. deren Einstiegsdatum (falls vorhanden) vor dem Stichtag und deren Ausstiegsdatum (falls vorhanden) nach dem Stichtag liegt.
- **Temporäre Abwesenheiten mit berücksichtigen:** Ist das an, werden zusätzlich die Personen weggelassen, die am Stichtag abwesend sind (z.B. Elternzeit).
- **Zugehörigkeiten:** Codes derselben Kategorie sind mit _oder_ verknüpft, verschiedene Kategorien mit _und_. Beispiel: _Postdocs_, _Doktorand:innen_, _MSt_ findet alle Postdocs und Doktorand:innen in der Abteilung MSt. Ohne Auswahl werden alle Personen gefunden.
- **Was soll ausgegeben werden:** die Spalten der Tabelle, in der gewählten Reihenfolge. Neben den Personendaten kann jede Codekategorie ausgewählt werden (z.B. _Abteilung_), dann erscheinen die zugeordneten Codes. _Beisitze der letzten 365 Tage_ ist die Summe der Beisitze in den letzten 365 Tagen (ab heute gerechnet). _Vertragsdauer_ gibt es nur für das Dekanat.
- **Sortierung:** nach Nachname, Vorname.

**Beisitzer suchen:** Beim Einschalten werden die Einstellungen auf die Suche nach Beisitzer:innen gesetzt, siehe _Für das Prüfungsamt_. Die Einstellungen bleiben änderbar. Solange der Schalter an ist, wird nach Abteilung, Vorgesetzten, Nachname, Vorname sortiert (ohne Abteilung bzw. Vorgesetzte am Ende). Schaltet man ihn aus, bleiben alle Einstellungen stehen und nur die Sortierung ändert sich; schaltet man ihn wieder ein, werden die Einstellungen erneut gesetzt.
""")

    with st.expander("Für Abteilungssekretariate"):
        st.markdown("""
- **Bei Arbeitsbeginn** einer neuen Person die fehlenden Daten eintragen: Email, Telefon, Gebäude und Raum, Vorgesetzte, Homepage und vor allem die _Zugehörigkeiten_ _Abteilung_ und _Statusgruppe_. Ohne Statusgruppe erscheint die Person nicht auf den Personenseiten der Homepage.
- **Regelmäßig die Warnungen ansehen** (Navigation links, _Warnungen_): Oben die eigene Abteilung auswählen und die Warnungen abarbeiten, etwa fehlende Email-Adressen. Personen, die gar keiner Abteilung zugeordnet sind, erscheinen nur bei der Auswahl _Alle_; es lohnt sich, auch dort gelegentlich nachzusehen, ob Personen der eigenen Abteilung darunter sind.
- **Änderungen** (Raumwechsel, neue Telefonnummer, ...) zeitnah eintragen, da sie auf der Homepage und im Adressbuch erscheinen.
""")

    with st.expander("Für das Prüfungsamt"):
        st.markdown("""
**Beisitzer:innen suchen:** Unter _Suchen/Datenexport_ den Schalter _Beisitzer suchen_ einschalten. Dann wird eingestellt:
- _Temporäre Abwesenheiten mit berücksichtigen_: an, d.h. wer am Stichtag abwesend ist, fehlt;
- _Zugehörigkeiten_: _Doktorand:innen_ und _Postdocs_;
- Ausgabe: _Name_, _Mail_, _Vorgesetzte_, _Abteilung_, _Studiendekanat_ und _Beisitze der letzten 365 Tage_;
- Sortierung nach Abteilung, Vorgesetzten, Nachname, Vorname.

In der Spalte _Studiendekanat_ sieht man z.B., ob jemand _deutschsprachig_ ist oder _wenig deutsch_ spricht, und ob ein Code wie _kein beisitz_ gesetzt ist. Alle Einstellungen können danach noch geändert werden, z.B. der Stichtag (etwa der Prüfungstag) oder eine Einschränkung auf eine Abteilung. Mit _Download Excel-Datei_ erhält man die Liste als Excel-Datei.

**Beisitze eintragen:** Unter _Personen_ die Person öffnen und ganz unten (direkt über _Speichern_) den Bereich _Beisitze der letzten 365 Tage_ aufklappen. Mit _Neuer Eintrag_ kommt oben eine Zeile dazu, in die man das Datum und die Anzahl der Beisitze an diesem Tag einträgt; mit _Löschen_ wird eine Zeile entfernt. Beim Speichern werden die Einträge chronologisch rückwärts sortiert. Ältere Einträge (vor mehr als 365 Tagen) werden nicht angezeigt, bleiben aber gespeichert.
""")

    with st.expander("Für das Dekanat"):
        st.markdown("""
Nur das Dekanat sieht und ändert die Vertragsdaten einer Person (unter _Personen_, beim Bearbeiten einer Person):
- _Einstiegsdatum_ und _Ausstiegsdatum_ bei Erstellung bzw. Verlängerung des Arbeitsvertrages eintragen. Sie bestimmen, ob eine Person als aktuell gilt, also auf der Homepage, im Adressbuch und in Suchen am Stichtag erscheint.
- _Kommentar zur Stelle_: interne Anmerkungen zur Stelle.
- _Abwesenheit_ (Beginn und Ende, mit Kommentar) für längere Abwesenheiten wie Elternzeit. Es müssen immer Beginn und Ende angegeben werden.

Im Datenexport gibt es für das Dekanat zusätzlich die Ausgabe _Vertragsdauer_ (Ein- und Ausstiegsdatum, Kommentar zur Stelle, Abwesenheiten).
""")

else:
    switch_page("PERSON")

st.sidebar.button("logout", on_click = tools.logout)
