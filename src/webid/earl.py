import logging
import os
import requests
import StringIO

import rdflib
from rdflib import URIRef

from constants import TESTREQS, TESTCASES

WIT = "RelyingParty"
WIT_FILENAME = "%s.n3" % WIT

rdflib.plugin.register('sparql', rdflib.query.Processor,
           'rdfextras.sparql.processor', 'Processor')
rdflib.plugin.register('sparql', rdflib.query.Result,
           'rdfextras.sparql.query', 'SPARQLQueryResult')

# Namespaces declaration.
# we're no longer using them. but we can need'em again :)

#EARL = rdflib.Namespace("http://www.w3.org/ns/earl#")
#DC = rdflib.Namespace("http://purl.org/dc/terms/")
#SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")

logger = logging.getLogger()


class Parser(object):
    """
    This Class parses the Earl Vocabulary for WebID Relying Parties.
    Is used for constructing the WebIDChecks that will be used in the
    WebIDValidator class. We take title, description, notes and dependencies
    from the vocabulary, for testCases and testRequirements.
    """
    # XXX this has to be cached
    # when used from django
    # it's taking way too long in gettig init!!

    def __init__(self, *args, **kwargs):
        self._get_webid_earl(download=kwargs.get('download', False))
        self._update_namespace()
        self._get_testcases()
        self._get_testreqs()

    def parseURI(self, URI=None):
        """
        Reloads the rdf graph containing the WebID test spec
        If not URI is given, it will fetch it from
        http://www.w3.org/2005/Incubator/webid/earl/RelyingParty.n3'
        """
        #print 'parsing uri %s' % URI
        self._get_webid_earl(download=True, URI=URI)

    def _get_webid_earl(self, download=False, URI=None):
        if download:
            logger.debug('downloading spec!')
            #print('downloading spec!')
            URI = 'http://www.w3.org/2005/Incubator/webid/earl/RelyingParty.n3'
            r = requests.get(URI)
            _file = StringIO.StringIO(r.content)
        else:
            _file = open(os.path.join(
                os.path.dirname(__file__), 'data', WIT_FILENAME))
            #XXX Get Timestamp fot the fetching.
            #we need to write verificationTimestamp

        self.g = rdflib.ConjunctiveGraph()
        self.g.parse(_file, format="n3")

    def _update_namespace(self):
        # updating the namespace
        OLD = "file://" + os.path.join(
                os.path.dirname(__file__), 'data', WIT_FILENAME)
        NEW = "http://www.w3.org/2005/Incubator/webid/earl/%s#" % WIT

        for cid, _, source in self.g.triples((None, None, None)):
            if source:
                try:
                    context = self.g.get_context(cid)
                    for s, p, o in context:
                        context.remove((s, p, o))
                        if isinstance(s, URIRef) and OLD in s:
                            s = URIRef(s.replace(OLD, NEW))
                        if isinstance(s, rdflib.URIRef) and OLD in p:
                            p = URIRef(p.replace(OLD, NEW))
                        if isinstance(o, URIRef) and OLD in o:
                            o = URIRef(o.replace(OLD, NEW))
                        context.add((s, p, o))
                except Exception, e:
                    #print e
                    raise e


    def _get_testcases(self):
        testcases = self.g.query(TESTCASES)
        self.testcases = [{'test': test.partition("#")[2],
                           'title': unicode(title),
                           'description': unicode(description),
                           'note': unicode(note),
                           'haspart': unicode(part.partition("#")[2]) if\
                                   part else None} \
                        for test, title, description, note, part in testcases]

    def _get_testreqs(self):
        testreqs = self.g.query(TESTREQS)
        self.testreqs = [{'test': test.partition("#")[2],
                           'title': unicode(title),
                           'description': unicode(description),
                           'note': unicode(note),
                           "haspart": unicode(part.partition("#")[2])} \
                        for test, title, description, note, part in testreqs]
