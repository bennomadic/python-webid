from collections import defaultdict
from datetime import datetime
from itertools import chain
import re
import logging

import constants
from webidchecks import WebIDChecks
from serializers import Id, PublicKey, WebIDClaim
from cert import Cert
from fetcher import WebIDLoader

logger = logging.getLogger(name=__name__)


WEBID_RAISE_EXCEPTIONS = False


class TestResult(Id):
    """
    Encapsulates Result of a Test
    """
    def __init__(self, *args, **kwargs):
        self.passed = kwargs.get('passed', False)
        self.pointer = None
        self.subject = None
        self.details = None
        super(TestResult, self).__init__(*args, **kwargs)


class WebIDImplementationError(Exception):
    """
    Exception raised when some methods are missing from the spec.
    """
    pass


class WebIDAuthMatched(Exception):
    """
    stub.
    Exception raised when the first authentication match
    is found on 'firstmatch' mode.
    """
    pass


class WebIDAuthStrictFailed(Exception):
    """
    stub.
    Exception raised when no valid webid Claims
    could be found in strict mode (all pubkeys in all
    profiles should be well formed).
    """
    pass


class WebIDAuthError(Exception):
    """
    Generic WebID Authentication Error.
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class WebIDValidator(object):
    """
    Main validator object.
    Its entry point is the method "validate".
    Has pointers to the tests passed, which in turn have
    pointers to results.
    """
    #XXX we could pass also a value for the RAISE_EXCEPTIONS value
    #XXX it will be useful for testing.

    def __init__(self, *args, **kwargs):

        self.certstr = None
        self.cert = None
        self.URIS = set([])
        self.profiles = dict()

        self.webidclaims = defaultdict(set)
        self.webidkeys = defaultdict(set)

        self.validatedURI = None
        self.webid_name = None

        self.testbed = WebIDChecks()

        tb = self.testbed
        for k in tb.testsdict.keys():
            tb.testsdict[k] = self.get_spec(k)

        # And what about having a xslt transform ???
        # (for the report)
        # ^^ it's a good idea, but what does this
        # comment HERE???

        certstr = kwargs.get('certstr', None)
        if certstr:
            self.certstr = certstr

        #validation mode switch:
        #exhaustive will check _all_ the webid claims
        #in all URIs in the certificate.
        #firstmatch will stop checking after the first
        #match is found.

        self.mode = kwargs.get('mode', 'firstmatch')

    @property
    def all_profiles(self):
        return self.profiles.values()

    #@property
    #def all_webidkeys(self):
        ##XXX we could hijack here the uuid of the
        ##webidkey that matches the cert key
        #return self.webidkeys.values()

    # other idea would be:
    # property: matched_pubkey, and represent as
    # owl:sameAs

    def get_method(self, name):
        """
        returns a test method from the testbed (ordered list
        of bounded methods).
        """
        return getattr(self, "check_%s" % name, None)

    def get_spec(self, testname):
        """
        returns the spec subclass for a given test method
        """
        return getattr(self.testbed, "__%s" % testname, None)

    def check_composite(self, test, **kwargs):
        """
        if this is a composite, returns a logic AND of all
        the subpart tests.
        """
        #XXX re-check that this is a composite test
        uri = kwargs.get("uri", None)
        pubkey = kwargs.get("pubkey", None)

        #print '----------checking composite %s' % test.name

        spec = self.get_spec(test.name)
        methods = [self.get_spec(name) for name in spec.parts if \
                getattr(self.get_spec(name), 'mandatory', True)]

        #all_methods = [self.get_spec(name) for name in spec.parts]
        #print 'all_methods', all_methods

        results = []
        for m in methods:
            for r in m.results:
                if uri and pubkey:
                    #print 'uri + pubkey'
                    if r.pubkey == pubkey and r.uri == uri:
                        results.append(r)

                if uri and not pubkey:
                    #print 'uri'
                    if r.uri == uri:
                        results.append(r)

                if not uri and not pubkey:
                    #print 'nor uri nor pk'
                    results.append(r)

        if results:
            individual_tests = [r.passed for r in results]
        else:
            individual_tests = [False]
        #print individual_tests
        return all(individual_tests)

    # methods to get pointers / subjects on test results

    def get_testinfo_verification_datetime(self, **kwargs):
        """
        returns the time of the verification (now)
        """
        return datetime.now()

    def get_testinfo_cert(self, **kwargs):
        """
        returns cert.
        """
        return self.cert

    def get_testinfo_cert_pubkey(self, **kwargs):
        """
        returns the cert pubkey.
        """
        if not self.cert:
            return None
        return self.cert.pubkey

    def get_testinfo_subjectAltName(self, **kwargs):
        """
        returns the cert SAN.
        """
        if not self.cert:
            return None
        return self.cert.subjectAltName

    def get_testinfo_pubkey(self, **kwargs):
        """
        returns the public key being tested.
        """
        return kwargs.get('pubkey', None)

    def get_testinfo_webid_pubkey_serialized(self, **kwargs):
        """
        should return a serialized pubkey.
        """
        result = kwargs.get('result', None)
        pubkey = kwargs.get('pubkey', None)
        #tricky. we add an attribute sayin'
        #that this thing is serialized-xml,
        #so the pointer uuid can be corrected
        #when writing the rdf-earl-report.
        result.xmlserialized = True
        return pubkey

    def get_testinfo_profile(self, **kwargs):
        """
        we should get a dict profiles[uri], where we store
        the serialized result from getting the WebID profile.
        (and headers and so on for proper serialization using
        rdf http voc)
        """
        uri = kwargs.get('uri', None)
        #print('getting testinfo:profile for uri %s' % uri)
        widprofile = self.profiles.get(uri, None)
        if widprofile:
            return widprofile.rawprofile

    def get_testinfo_rstatus(self, **kwargs):
        uri = kwargs.get('uri', None)
        widprofile = self.profiles.get(uri, None)
        if widprofile and hasattr(widprofile, 'rstatus_code'):
            return "response status code: %s" % widprofile.rstatus_code
        else:
            return None

    def add_test_info(self, field=None, result=None, spec=None, **kwargs):
        """
        checks if the spec class has some details field,
        executes that method if it exists, and add a new
        attr to test with the returned value.
        """
        kwargs['result'] = result
        info_field = getattr(spec, field, False)
        if info_field:
            info_meth = getattr(self, "get_testinfo_%s" % info_field, None)
            if info_meth and callable(info_meth):
                info = info_meth(**kwargs)
                if info:
                    setattr(result, field, info)

        #we write uri / pubkey also in results
        #so we have it accessible for later.
        for k, v in kwargs.items():
            setattr(result, k, v)

    def get_method_name(self, test):
        """
        returns the proper method name for a given test.
        it's the same as the class spec, but replacing __
        by check prefixes.
        """
        return test._getTestMethodName().replace("__", "check_")

    def do_check(self, test, **kwargs):
        """
        performs a given check.
        """
        #print "doing check %s" % test.name
        passed = False
        uri = kwargs.get('uri', None)
        pubkey = kwargs.get('pubkey', None)

        spec = self.get_spec(test.name)
        methodname = self.get_method_name(test)

        has_parts = getattr(spec, 'parts', False)
        has_extra = getattr(spec, 'extra', False)

        if (has_parts and not has_extra):
            #A requirement test, or another testCase
            # with subparts
            #i.e., profileAllKeysWellFormed (foreach...)
            logger.debug('do_check: composite %s' % test)
            passed = self.check_composite(test, **kwargs)
        else:
            #a simple, atomic TestCase
            testmethod = self.get_method(methodname)
            if not testmethod:
                raise WebIDImplementationError(
                "Validator tried a method which is not Implemented yet: %s" % \
                    (methodname))
            passed = testmethod(**kwargs)

        #XXX need a switch for disabling test results #######
        #it takes too long!
        test_result = TestResult(passed=passed)

        # we write details on test results (collateral effect)
        # to be able to generate report

        for info_field in ("details", "subject", "pointer"):
            self.add_test_info(info_field,
                    result=test_result, spec=spec,
                    uri=uri, pubkey=pubkey)

        test.results = test.results + (test_result,)

        ######################################################

        self.post_check_passed(methodname, passed, test=test, uri=uri)
        return passed

    def post_check_passed(self, methodname, passed, test=None, uri=None):
        """
        according to configuration parameter, either log the test
        result or raise an Exception or pass silently.
        """
        if passed is True:
            logger.info("%s passed!" % methodname)
            final = getattr(test, 'final', False)
            if final and uri is not None:
                self.validatedURI = uri
            if final and self.mode == "firstmatch":
                raise WebIDAuthMatched()

        if not passed:
            logger.warning("%s failed" % methodname)
            if getattr(test, 'mandatory', False) and self.mode == "strict":
                raise WebIDAuthStrictFailed()

            #XXX this should come from settings
            #XXX or be passed when initializing the object

            if not WEBID_RAISE_EXCEPTIONS:
                pass
            else:
                msg = "WebID Error at %s step." % \
                    test.__class__.__name__.replace('__', '')
                if hasattr(test, 'error'):
                    msg = test.error
                if hasattr(test, 'description'):
                    msg = msg + ' ' + test.description
                raise WebIDAuthError(msg)

    def validate(self):
        """
        entry point for validation
        public method that calls the rest
        """
        try:
            for test in self.testbed.checks_only_cert:
                self.do_check(test)

            for uri in self.URIS:
                #only uris loop
                for test in self.testbed.checks_only_uri:
                    self.do_check(test=test, uri=uri)

                #only pks loop
                for pubkey in self.webidkeys[uri]:
                    for test in self.testbed.checks_loop_pubkey:
                        self.do_check(test=test, uri=uri, pubkey=pubkey)

                for test in self.testbed.checks_loop_profile:
                    self.do_check(test=test, uri=uri)

        except WebIDAuthMatched:
            validated = True

        except WebIDAuthStrictFailed:
            validated = False

        #XXX fix this
        #At least one of the final reqs is done...
        if not hasattr(self.testbed.tests[-1], 'results'):
            #print 'no results on last test... :('
            validated = False
        else:
            if len(self.testbed.tests[-1].results) == 0:
                validated = False
            else:
                validated = self.testbed.tests[-1].results[-1].passed

        return validated, self

    @property
    def all_webidclaims(self):
        return tuple([x for x in chain(*self.webidclaims.values())])

    @property
    def all_webidkeys(self):
        return tuple([x for x in chain(*self.webidkeys.values())])

    #
    # checks (separate methods)
    #

    def check_certificateProvided(self, **kwargs):
        if not getattr(self, 'certstr', None):
            return False
        try:
            self.cert = Cert(self.certstr)
            return True
        except Exception, e:
            #XXX inject error on test
            raise Exception(e)
            #return False

    def check_certificateProvidedSAN(self, **kwargs):
        """
        returns: bool.
        calls the Cert method for extracting Subject Alt
        Name, and stores the URIS from that string as a
        set.
        """
        #XXX are we assuming that if no URIs in SAN
        #this test must fail???
        if not self.cert:
            return False
        altName = self.cert.get_subjectAltName()
        if not altName:
            return False
        uris = set(re.findall('URI:([^, ]+)', altName))
        self.URIS = uris
        self.validatedURI = None
        # return False if no URIS???
        return True if altName else False

    def check_certificateDateOk(self, **kwargs):
        """
        returns: bool.
        """
        if not self.cert:
            return False
        return self.cert.check_date_Ok()

    def check_certificatePubkeyRecognised(self, **kwargs):
        if not self.cert:
            return False
        try:
            self.cert.get_pubkey()
            return self.cert.is_pubkey_well_formed
        except:
            raise
            #return False

    def check_certificateCriticalExtensionsOk(self, **kwargs):
        if not self.cert:
            return False
        #we pass the test if the cert has NOT other critical ext
        #it's a warning all the same
        return not self.cert.has_other_critical_extensions()

    def check_certificateOk(self, **kwargs):
        #if we have arrived here it's True :)
        logger.warning("this method should never get executed")
        #By now, this check (and all the other "hasPart" tests
        #should be AND'ing all the sub-tests results.

    def check_profileGet(self, **kwargs):
        try:
            uri = kwargs.get('uri', None)
            webidprofile = WebIDLoader(uri)
            webidprofile.get()
            self.profiles[uri] = webidprofile
            if not getattr(webidprofile, 'ok', None):
                return False
        except:
            raise  # DEBUG
            #return False
        return True

    def check_profileWellFormed(self, **kwargs):
        uri = kwargs.get('uri', None)
        #print 'checking ------ profileWellFormed'
        try:
            webidprofile = self.profiles[uri]
            if not getattr(webidprofile, 'ok', None):
                return False
            webidprofile.parse()
            self._extract_webid_credentials(webidprofile.graph, uri)
            return True
        except:
            raise
            #return False

    ############################################################
    # checks below looping over all pubkeys

    def check_pubkeyRSAModulusFunctional(self, **kwargs):
        pkey = kwargs.get('pubkey', None)
        if not pkey:
            return False
        try:
            int(pkey.mod, 16)
            return True
        except ValueError:
            return False

    def check_pubkeyRSAModulusLiteral(self, **kwargs):
        """
        checks that RSA pubkey modulus is expressed using literal type.
        we're assuming it is the case if the sparql query went ok.
        but this will need better tests in the future.
        """
        pkey = kwargs.get('pubkey', None)
        if not pkey:
            return False
        return True if isinstance(pkey.mod, str) else False

    def check_pubkeyRSAModulus(self, **kwargs):
        """auto."""
        pass

    def check_pubkeyRSAExponentFunctional(self, **kwargs):
        pkey = kwargs.get('pubkey', None)
        return True if isinstance(pkey.exp, int) else False

    def check_pubkeyRSAExponentLiteral(self, **kwargs):
        pkey = kwargs.get('pubkey', None)
        return True if isinstance(pkey.exp, int) else False

    def check_pubkeyRSAExponent(self, **kwargs):
        pkey = kwargs.get('pubkey', None)
        return True if isinstance(pkey.exp, int) else False

    def check_profileWellFormedPubkey(self, **kwargs):
        """auto."""
        pass

    def check_profileAllKeysWellFormed(self, **kwargs):
        """auto."""
        pass

    def check_profileOk(self, **kwargs):
        """auto"""
        pass

    def check_webidClaim(self, **kwargs):
        """auto"""
        pass

    def check_webidAuthentication(self, **kwargs):
        """
        this is a requirement test, and hasParts,
        but we exclude ir from the automated test dependency
        as has extra semantics that are not catched by the spec
        (the parts are needed but not sufficient)
        """
        #XXX we could raise if not webidkeys, or
        #if prev test failed...
        logger.debug('webidAuth method... SHOULD get executed')
        uri = kwargs.get('uri', None)
        try:
            passed = self._check_credentials(uri=uri)
        except:
            raise
        return passed

    ########################################
    # end test methods
    #########################################
    # begin private methods

    def _extract_webid_credentials(self, graph, uri):
        logger.info('loading webid credentials for uri %s' % uri)
        #XXX this GRAPH also should be a dict by uri
        results = graph.query(constants.WEBID_SPARQL_SIMPLE)
        for result in results:
            mod, exp = result
            #TODO refactor all replaces into
            #a single regexp
            mod_lit = unicode(mod).replace(' ', '').\
                    replace('\n', '').\
                    replace('"', '').\
                    replace('\t', '').\
                    encode('ascii', 'ignore').lower()
            exp_int = int(unicode(exp))
            pubkey = PublicKey(mod=mod_lit, exp=exp_int)
            webidClaim = WebIDClaim(uri, pubkey)

            self.webidclaims[uri].add(webidClaim)
            self.webidkeys[uri].add(pubkey)

    def _check_credentials(self, **kwargs):
        """
        AKA "The Final Check"...
        Here lies the meat of the Authentication:
        checks if the cert pubkey is contained in the
        webid pubkeys set.
        """
        uri = kwargs.get('uri', None)
        logger.debug('>>> matching credentials for uri %s' % uri)

        if not self.webidkeys:
            logger.error("no webid keys :(")
            #XXX raise???

        if self.cert.pubkey in self.webidkeys[uri]:
            return True
        else:
            return False

    def _extract_webid_name(self, uri, sparql_query=None,
            sparql_vars=None):
        """
        returns a sparql query over the profile, containing
        fields useful for building a new local profile for
        the external user.
        XXX might be moved to WebIDAuthenticator
        """
        if not uri:
            return None
        graph = self.profiles[uri].graph
        if graph:
            webid_name = {}
            if sparql_query:
                query = sparql_query
            else:
                query = constants.NAME_SPARQL
                #XXX get this vars names from
                #constants too.
                sparql_vars = ('uri', 'name', 'nick',
                        'mbox')
            res = graph.query(query)
            #XXX FIXME!!!
            #Check that THE URI IS SAME AS
            #The URIRef we're handling for our
            #person...
            for result in res:
                #uri, name, nick, mbox,\
                    #givenName, familyName = result
                for key, value in zip(sparql_vars,
                        result):
                    #XXX check for same cardinality!!!
                    #or raise ImproperlyConfigured
                    webid_name[key] = unicode(value)

                #webid_name['uri'] = unicode(uri)
                #webid_name['name'] = unicode(name)
                #webid_name['nick'] = unicode(nick)
                #webid_name['mbox'] = unicode(mbox)

                #webid_name['familyName'] = unicode(familyName)
                #webid_name['givenName'] = unicode(givenName)
            self.webid_name = webid_name
