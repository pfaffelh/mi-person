sudo apt update
sudo apt install slapd ldap-utils

Admin-Passwort wie ubuntu


sudo dpkg-reconfigure slapd


sudo systemctl status slapd

ldapsearch -x -LLL -H ldap://localhost -b dc=mathe,dc=local

sudo dpkg-reconfigure slapd

ldapadd -x   -D "cn=admin,dc=mathe,dc=local"   -W   -f base.ldif

ldapadd -x   -D "cn=admin,dc=mathe,dc=local"   -W   -f mathe_ldap.ldif

