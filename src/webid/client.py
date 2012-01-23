#!/usr/bin/env python
import ConfigParser
import httplib
import os
import urllib
import shutil

from constants import FORMATS

"""
WARNING!!!!
This is (by now) just some tinkering put together,
previous to automatize a given WebID cert against different
Relying Parties. It might OR not might work.
... but take everything with a pinch of salt.
"""

# TODO: use requests instead of urrlib

# TODO : decouple a little the certs
# from the client lib...

# TODO : ability to get certs exported from browser
# (python-nss??? :))
# by now using a small sh script :)

#################################################
# Home Dir / Config setting (move)
#################################################
# Check for 1) homedir
#           2) default config
#           3) set one, if not
_default_dir = None
path = "~/.webidclient"

if _default_dir is None:
    path = os.path.expanduser(path)
    #print 'path', path
    os.path.normpath(path)
    _default_dir = path
    #print 'default_dir', _default_dir

if not os.path.exists(_default_dir):
    os.mkdir(_default_dir)

_default_config = os.path.join(_default_dir, 'webidclient.cfg')
if not os.path.exists(_default_config):
    #FIXME get proper path to data dir!!!
    shutil.copyfile('data/sample.cfg', _default_config)

config = ConfigParser.ConfigParser()
config.read(_default_config)


################################################
# Client
################################################
# Should *only* make the connection
# Get details about:
#           - crypto implementations
#           - content-negotiation, available formats etc


def printheaders(headers):
        print
        for (k, v) in headers.items():
            print k, v
        print
        print


def do_connection(url, certfile, _format="rdf", onlyhead=False):
    #XXX assert url begins with https!
    _url = url.split('https:')[1]
    host, path = urllib.splithost(_url)
    conn = httplib.HTTPSConnection(
        host,
        key_file=certfile,
        cert_file=certfile
    )
    conn.putrequest('GET', path)

    # Refactor format into a dict
    if _format in FORMATS:
        conn.putheader("Accept", FORMATS[_format])
    conn.endheaders()
    response = conn.getresponse()

    if onlyhead:
        mime = FORMATS[_format]
        rhead = dict(tuple(response.getheaders()))
        ctype = rhead.get('content-type', None)
        if ctype and mime in ctype:
            print 'OK!'
            printheaders(rhead)
        else:
            print "format failed :("

    else:
        #response to stdout
        print response.read()

##########################################################
# Tests
##########################################################
# Let's try some things :)

sections = config.sections()
certs = filter(lambda x: x.startswith('cert-'), sections)

# Implement threads?
# move to twisted (using callbacks?)


def do_pause():
    try:
        input('next?')
    except:
        print('exception, skipping...')


def try_all_certs(validator_name, validator_uri, onlyhead=False):
    #only one cert by the moment :)
    for certsect in certs:
        cert = config.get(certsect, "cert", None)
        if cert:
            certfile = os.path.join(_default_dir, 'certs', cert)
            print(">>>>>>>")
            print("Requesting %s [%s]\nwith cert at %s" % (validator_name,
                                                            validator_uri,
                                                            certfile))
            do_connection(validator_uri, certfile, _format="rdf",
                    onlyhead=onlyhead)
            # heck! scrape html??
            do_pause()


def get_first_cert():
    certsect = certs[0]
    cert = config.get(certsect, "cert", None)
    if cert:
        certfile = os.path.join(_default_dir, 'certs', cert)
        return certfile


validators = filter(lambda x: x.startswith('validator-'), sections)


def get_validator_details(val):
        name = val.split("validator-")[1]
        uri = config.get(val, "uri", None)
        return (name, uri)


def try_all_formats():
    #XXX cycle all formats
    cert = get_first_cert()
    for validator_sect in validators:
        for _format in FORMATS:
            name, uri = get_validator_details(validator_sect)
            print(">>>>>>>")
            print("Requesting %s [%s]\nwith format %s" % (name,
                                                           uri,
                                                           _format))
            do_connection(uri, cert, _format=_format, onlyhead=True)


def try_all_validators(_format, certfile):
    for validator_sect in validators:
        name, uri = get_validator_details(validator_sect)
        do_connection(uri, certfile, _format=_format,
                onlyhead=True)
        # heck! scrape html??
        # come'on, guys, let's play earl!!!
        do_pause()

# go!
certsect = certs[0]
cert = config.get(certsect, "cert", None)

#try_all_validators(cert)
try_all_formats()
