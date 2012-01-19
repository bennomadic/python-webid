#!/bin/sh
# TODO This could be migrated to python
# using python-nss bindings :)

echo "#####"
echo "WARNING! You are going to export a certificate, including your private key."
echo "You better know what you're doing."
echo "#####"
echo "Usage: export_certs your_cert_name_in_browser out-name"
echo "If you want to list your certs: certutil -d sql:$HOME/.pki/nssdb -L "
echo
mkdir -p ~/.webidclient/certs
pk12util -d sql:$HOME/.pki/nssdb -n "$1" -o ~/.webidclient/certs/tmp_testcert.p12
chmod 400 ~/.webidclient/certs/tmp_testcert.p12
openssl pkcs12 -in ~/.webidclient/certs/tmp_testcert.p12  -out ~/.webidclient/certs/$2.pem  -nodes 
chmod 400 ~/.webidclient/certs/$2.pem
rm ~/.webidclient/certs/tmp_testcert.p12
