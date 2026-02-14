| Kürzel | Bedeutung           | Zweck                |
| ------ | ------------------- | -------------------- |
| `dc`   | Domain Component    | Baumwurzel           |
| `ou`   | Organizational Unit | Ordner               |
| `cn`   | Common Name         | Anzeigename          |
| `uid`  | User ID             | Login                |
| `sn`   | Surname             | Pflicht bei Personen |



Funktionalität der App: 

* Jede Person hat ihre Grunddaten (Name, Vorname, Namenszusatz, Titel, rz-Kennung, URL, Mail (evtl mehrere))
* Die rz-Kennung entspricht dem Identifier der Person.
* Es gibt Tag-Kategorien: Statusgruppe, Abteliung, Professur, Sprache, Mailing-Listen, Sonstiges
* Jede Person hat ein Einstiegs- und Aussstiegs-Datum, das leer sein kann.
* Für jede Tag-Kategorie kann man einer Person eine Liste von Tags geben
* Jede Person hat die Semester, in der sie/er lehrt

* Soll es Bilder für die Personen geben?
* Sollen Mailing-Listen hier abgebildet werden



Soll es die Möglichkeit geben, für jede Person ein Bild in der Datenbank zu hinterlegen?

-- Wird von jeder Person der Vorgesetzte erfasst? 

Soll Lehrdeputat erfasst werden?

Weiter stelle ich mir vor, dass es in der App dann eine "Suchfunktion" gibt. Hier könnte relevant sein:
* Sollen Funktionen der Dozent:innen hinterlegt werden? (Also z.B. Goette -> Studiendekan, Mildenberger -> Studienkommission; kann sinnvoll sein, um einen Überblick zu haben, macht aber nur Sinn, wenn diese Informationen gut gepflegt werden.)
* Soll Gender erfasst werden? (Im Prinzip nein, aber es kann pratkisch für Berichte sein, oder wenn eine Person von Gender x in der Statusgruppe y gesucht wird.)

Bool'sche Variablen für: 
* mit LDAP synchonisieren?
* auf Homepage anzeigen?
