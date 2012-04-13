import logging
import requests
import StringIO
from xml.sax import SAXParseException

import rdflib
rdflib_major_ver = int(rdflib.__version__.split('.')[0])

if rdflib_major_ver == 3:
    # this is for rdflib branch 3.x.x
    rdflib.plugin.register('sparql', rdflib.query.Processor,
           'rdfextras.sparql.processor', 'Processor')
    rdflib.plugin.register('sparql', rdflib.query.Result,
           'rdfextras.sparql.query', 'SPARQLQueryResult')

from serializers import Profile
from constants import FORMATS

#ch = logging.StreamHandler()
#ch.setLevel(logging.DEBUG)
logger = logging.getLogger(name=__name__)
#logger.setLevel(logging.DEBUG)
#logger.addHandler(ch)


UNDERSTOOD_FORMATS = ('rdf', 'rdfa')
#TODO leaving out turtle and n3 for now
#have to see how should rdflib handle it
UNDERSTOOD_CTYPES = tuple([FORMATS[f] for f in UNDERSTOOD_FORMATS])


def get_accept_header(ftuple):
    """
    input: format tuple.
    returns a string containing the accepted formats in the
    preferred order.
    """
    return '; '.join([FORMATS[f] for f in UNDERSTOOD_FORMATS])


class WebIDLoader(object):
    """
    class that encapsulates the fetching and
    parsing of a WebID Profile
    """
    def __init__(self, uri, preferred_format=None, **kwargs):
        """
        preferred_format may be either a content-type, or
        the shortname for one of the known formats.
        """
        self.uri = uri
        if preferred_format:
            self.preferred_format = preferred_format
        # XXX TODO pass verify option
        self.verify_server_cert = False
        self.format = None

        self.graph = None
        self.rcontent = None
        self.rheaders = None
        self.rawprofile = None

        self.ctype = None
        # for multiple content tries
        self.responses = dict()
        self.tried_formats = list()

    def get(self):
        """
        de-references the uri, handling content-negotiation.
        """
        logger.debug('loading webid: %s' % self.uri)
        preffmt = getattr(self, 'preferred_format', None)
        accept_header = None
        if preffmt:
            if "/" in preffmt:
                accept_header = preffmt
            else:
                try:
                    accept_header = FORMATS[preffmt]
                except KeyError:
                    accept_header = None
        logger.debug('accept_header: %s' % accept_header)
        if accept_header:  # we got a preference on init.
            logger.debug('using preferred format %s' % preffmt)
            req = requests.get(self.uri,
                verify=self.verify_server_cert,
                headers={"accept": accept_header})
        else:  # no accept header, go with default preferred fmts.
            logger.debug('using all understood formats')
            req = requests.get(self.uri,
                verify=self.verify_server_cert,
                headers={"accept": get_accept_header(UNDERSTOOD_FORMATS)})
        if req.ok:
            logger.debug('successful URI dereference for uri %s' % self.uri)
            ctype = req.headers.get('content-type', None)
            if ctype:
                ctype = ctype.split(";")[0]
            logger.debug('content-type: %s' % ctype)
            if ctype in UNDERSTOOD_CTYPES:
                logger.debug('saving state...')
                self.save_state(req)
                # we're happy... for now.
                logger.info('successfully got content for uri %s' % self.uri)
                return True
            else:
                logger.debug('do not understand content-type of response...')
                self.ok = False
                #XXX DEBUG
                self.req = req

        else:
            logger.debug('not a valid response.')
            logger.debug('status code: %s' % req.status_code)
        logger.debug('we did not get a proper response :(')
        logger.debug('we need to know if it was 404, 500, or what')
        logger.debug('doing nothing...')
        # else: loop over rest of understood formats.
        # if we had been given a preference, try with the broader accept.
        # try to use conneg features if given.
        # XXX if response code is 406, look for which of the alternates
        # can we understand.

    def save_state(self, req):
        """
        saves the content of a successful response into this instance,
        for later use.
        """
        #XXX only for DEBUG, do not save whole req object!
        #self.r = req

        self.rcontent = req.content
        self.rheaders = req.headers
        self.rstatus_code = req.status_code
        ctype = req.headers.get('content-type', None)
        if ctype:
            ctype = ctype.split(";")[0]
        self.ctype = ctype
        self.ok = req.ok
        self.format = ctype
        # XXX redundant. but changing this mean to change also
        # the earl validation on webid-auth package.
        self.responses[ctype] = req

    def parse(self, format=None):
        """
        tries to parse the content of the request into
        an rdf graph.
        """
        self.graph = rdflib.ConjunctiveGraph()
        format = format or self.format
        try:
            _f = StringIO.StringIO(self.rcontent)
            self.graph.load(_f, format=format)
            self.rawprofile = Profile(
                    self.graph.serialize(format="pretty-xml"))
            return True
        except SAXParseException:
            #malformed rdfa
            raise
        except Exception:
            raise
            #return False
            #ConnectionError (we should put some "reason" field on the test@!!

    #XXX move here the SPARQL queries also???



#############################################################
# SOME NOTES
#############################################################

# XXX I guess that we have to go with latest rdflib in pypi:
# 3.1.0. But we can workaround for the 2.x.x series if needed

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
