import logging
import requests
import StringIO
from xml.sax import SAXParseException

from serializers import Profile

import rdflib

rdflib_major_ver = int(rdflib.__version__.split('.')[0])

if rdflib_major_ver == 3:
    # this is for rdflib branch 3.x.x
    rdflib.plugin.register('sparql', rdflib.query.Processor,
           'rdfextras.sparql.processor', 'Processor')
    rdflib.plugin.register('sparql', rdflib.query.Result,
           'rdfextras.sparql.query', 'SPARQLQueryResult')

logger = logging.getLogger()


class WebIDLoader(object):
    """
    class that encapsulates the fetching and
    parsing of a WebID Profile
    """

    def __init__(self, uri, **kwargs):
        self.uri = uri
        #only rdfa by now...
        #GET formats dict from client
        self.format = "rdfa"
        self.graph = None
        self.rcontent = None
        self.rheaders = None
        self.rawprofile = None

    def get(self):
        logger.error('loading webid: %s' % self.uri)
        r = requests.get(self.uri,
                headers={"accept": "application/xhtml+xml"})
        self.rcontent = r.content
        self.rheaders = r.headers
        self.rstatus_code = r.status_code
        self.ok = r.ok

    def parse(self):
        self.graph = rdflib.ConjunctiveGraph()
        try:
            _f = StringIO.StringIO(self.rcontent)
            self.graph.load(_f, format=self.format)
            self.rawprofile = Profile(
                    self.graph.serialize(format="pretty-xml"))
        except SAXParseException as e:
            #malformed rdfa
            raise
        except Exception as e:
            raise e
            #return False
            #ConnectionError (we should put some "reason" field on the test@!!

    #XXX move here the SPARQL queries also???



#############################################################
# SOME NOTES
#############################################################

# XXX I guess that we have to go with latest rdflib in pypi:
# 3.1.0. But we can workaround for the 2.x.x series if needed

#XXX TODO add html5lib to dependencies. needed by rdfa parser...
#XXX TODO add rdfextras to dependencies (sparql is no longer in rdflib core)
#XXX TODO add requests to deps

####################################################

#what happens when >1 profiles?
#content-negotiation
#but we're pointing to xmlliteral here...
#:/
#have to report Henry/Bergi about this...
#the right thing would be to describe
#the request using the http rdf voc.

#####################################################

# XXX we have to accept kwargs to override formats
# XXX (So we can test things in different providers
#     and know that we are conforming to the spec)
# XXX deal with multi-URIs

# XXX Use content-type!!!

# Resort to parsing dtd or alternates only
# if not-acceptable (and no correct headers)
#w_id = urllib.urlopen(URI)
#is_dtd = w_id.readline()
#if RDFA_DTD in is_dtd:
#    wid_format = 'rdfa'
#else:
#    wid_format = 'xml'

#let's simplify this
#(we will need a content-negotiation logic herr)
#1) head. see vary header.
#2) if yes, do our things
#3) (we prefer rdf, right?)
#r = requests.get(URI, headers={"accept":"application/rdf+xml;
#    application/xhtml+xml; text/turtle"})
