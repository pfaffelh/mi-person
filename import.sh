# This is a how to set up ldap in order to fill in person data

sudo apt update
sudo apt install slapd ldap-utils

sudo dpkg-reconfigure slapd

# de
# uni-freiburg.de
# admin-Passwort: siehe netrc
# angeben

sudo systemctl status slapd
# sollte running anzeigen

ldapsearch -x -LLL -H ldap://localhost -b dc=uni-freiburg,dc=de
# ist noch leer

# sudo dpkg-reconfigure slapd

# Hier wird das base.ldif geladen
# admin-Passwort aus netrc
ldapadd -x -D "cn=admin,dc=de" -W -f base.ldif

# Der Rest passiert in python

