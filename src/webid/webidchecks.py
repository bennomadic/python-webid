import uuid
import inspect
from itertools import tee, islice, chain, izip

from earl import Parser


class WebIDChecks(object):
    order = 0
    namespace = "http://www.w3.org/2005/Incubator/webid/earl/RelyingParty#"

    def __init__(self):
        self.uuid = uuid.uuid4()
        #deprecate passed?
        #self.passed = False
        self.title = None
        self.description = None
        self.notes = None
        self.results = tuple()
        self.mandatory = True
        #XXX FIXME validatedURI should be
        #set properly when done.
        self.validatedURI = None
        #change to tuple
        self.parts = list()
        self.tests = list()
        self.earltests = set([])
        #still have to be used
        #(date of voc fetched)
        self.earlvoc_fetched = None

        if self.__class__.__name__ == "WebIDChecks":
            """
            we get subclasses, only for the superclass
            """
            self.testsdict = dict()
            for subclass in WebIDChecks.__subclasses__():
                #XXX take care, all subclasses are
                #taken as tests!
                if not hasattr(subclass, 'test'):
                    setattr(subclass, 'test', True)
                    setattr(subclass, 'requirement', False)
                setattr(self, subclass.__name__, subclass())
                if hasattr(subclass, 'mandatory'):
                    #all tests are mandatory
                    #unless specified otherwise in the subclass
                    #(it will generate warnings if false)
                    setattr(getattr(self, subclass.__name__),
                            'mandatory',
                            getattr(subclass, 'mandatory'))
            self.getEarlTests()
            self.tests = self._getOrderedTests()

    def __repr__(self):
        if getattr(self, 'requirement', False):
            return "<WebIDTest: [req] %s>" % self.__class__.__name__
        return "<WebIDTest: %s>" % self.__class__.__name__

    @property
    def id_uuid(self):
        return u"uuid%s" % self.uuid

    def _getTestMethodName(self):
        return self.name

    def _getOrderedTests(self):
        return sorted(filter(lambda x: getattr(x, 'test', False),
            dict(inspect.getmembers(self)).values()),
            key=lambda x: x.order)

    @property
    def test_coverage(self):
        """
        returns the percentage of tests over
        the total tests in the spec
        that we have implemented
        """
        return float(len(self.tests)) / float(len(self.earltests))

    def get_missing_tests(self):
        """
        returns a set containing the tests that appear in the webid earl voc
        but we do not have implemented (yet)
        """
        #XXX get order???
        return self.earltests.difference(
            set([x.__class__.__name__.replace('__', '') \
                for x in self.tests]))
    # needed?

    @property
    def _iter_tests(self):
        for test in self.tests:
            yield test

    # XXX deprecate
    # Accessing prev, item, next on iter
    # http://stackoverflow.com/questions/1011938/python-
    # previous-and-next-values-inside-a-loop
    def prev_and_next(self):
        prevs, items, nexts = tee(self.tests, 3)
        prevs = chain([None], prevs)
        nexts = chain(islice(nexts, 1, None), [None])
        return izip(prevs, items, nexts)

    def getEarlTests(self):
        """
        get a EarlParser object
        that contains all the testcases in the (current) ont.
        """
        self.ont = Parser()
        # hmm we could combine the testcases and the
        # testreqs queries, it's pretty redundant
        for tcase in self.ont.testcases:
            test = tcase.get('test', None)
            title = tcase.get('title', None)
            description = tcase.get('description', None)
            notes = tcase.get('notes', None)
            part = tcase.get('haspart', None)
            attr_name = "__%s" % test
            subcls = getattr(self, attr_name, None)
            if subcls:
                setattr(subcls, 'title', title)
                setattr(subcls, 'name', test)
                setattr(subcls, 'description', description)
                setattr(subcls, 'notes', notes)
                if part:
                    getattr(subcls, 'parts').append(part)
            self.earltests.add(test)
            self.testsdict[test] = None

        for treq in self.ont.testreqs:
            test = treq.get('test', None)
            title = treq.get('title', None)
            description = treq.get('description', None)
            notes = treq.get('notes', None)
            part = treq.get('haspart', None)
            attr_name = "__%s" % test

            subcls = getattr(self, attr_name, None)
            if subcls:
                setattr(subcls, 'title', title)
                setattr(subcls, 'name', test)
                setattr(subcls, 'description', description)
                setattr(subcls, 'notes', notes)
                if part:
                    getattr(subcls, 'parts').append(part)
                #XXX this is the only diff, finally!
                setattr(subcls, 'requirement', True)
            self.earltests.add(test)
            self.testsdict[test] = None

    @property
    def checks_only_cert(self):
        """
        returns only checks that deal with certificate
        """
        return [x for x in self.tests \
            if not hasattr(x, 'foreach')]

    @property
    def checks_only_uri(self):
        """
        returns the block of checks that deal with uri
        """
        return [x for x in self.tests \
                if hasattr(x, 'foreach') \
                and 'uri' in x.foreach \
                and 'pubkey' not in x.foreach]

    @property
    def checks_loop_pubkey(self):
        """
        returns the block of checks that deal with pubkeys
        in a given uri
        """
        return [x for x in self.tests \
                if hasattr(x, 'foreach') \
                and 'pubkey' in x.foreach]

    @property
    def checks_loop_profile(self):
        """
        returns the block of checks that deal with pubkeys
        in a given uri
        """
        return [x for x in self.tests \
                if hasattr(x, 'foreach') \
                and 'profile' in x.foreach]

    def get_results(uri=None, pk=None):
        """
        stub. should return filtered results
        from the tuple
        """
        pass

# certificate tests


class __certificateProvided(WebIDChecks):
    order = 1
    error = u"We did not receive a user certificate. It could be that user has\
not sent one, or a timeout, or a server misconfiguration. Please check."
    pointer = "cert"


class __certificateProvidedSAN(WebIDChecks):
    order = 2
    subject = "cert"
    pointer = "subjectAltName"
    details = "subjectAltName"


class __certificateDateOk(WebIDChecks):
    order = 3
    subject = "cert"
    details = "verification_datetime"


class __certificatePubkeyRecognised(WebIDChecks):
    order = 4
    subject = "cert"
    pointer = "cert_pubkey"


class __certificateCriticalExtensionsOk(WebIDChecks):
    order = 5
    mandatory = False
    subject = "cert"


class __certificateOk(WebIDChecks):
    # auto (req)
    order = 6


# profile tests
class __profileGet(WebIDChecks):
    order = 7
    subject = "profile"
    details = "rstatus"
    foreach = ("uri",)


class __profileWellFormed(WebIDChecks):
    order = 8
    subject = "profile"
    foreach = ("uri",)


class __pubkeyRSAModulusFunctional(WebIDChecks):
    order = 9
    foreach = ("uri", "pubkey")
    subject = "webid_pubkey_serialized"


class __pubkeyRSAModulusOldFunctional(WebIDChecks):
    order = 10
    test = False
    foreach = ("uri", "pubkey")
    subject = "webid_pubkey_serialized"


class __pubkeyRSAModulusLiteral(WebIDChecks):
    order = 11
    foreach = "pubkey"
    foreach = ("uri", "pubkey")
    subject = "webid_pubkey_serialized"


class __pubkeyRSAModulus(WebIDChecks):
    order = 12
    foreach = ("uri", "pubkey")
    subject = "webid_pubkey_serialized"


class __pubkeyRSAExponentFunctional(WebIDChecks):
    order = 13
    foreach = ("uri", "pubkey")
    subject = "webid_pubkey_serialized"


class __pubkeyRSAExponentOldFunctional(WebIDChecks):
    order = 14
    test = False
    foreach = ("uri", "pubkey")
    subject = "webid_pubkey_serialized"


class __pubkeyRSAExponentLiteral(WebIDChecks):
    order = 15
    foreach = ("uri", "pubkey")
    subject = "webid_pubkey_serialized"


class __pubkeyRSAExponent(WebIDChecks):
    order = 16
    foreach = ("uri", "pubkey")
    subject = "webid_pubkey_serialized"


class __profileWellFormedPubkey(WebIDChecks):
    order = 17
    foreach = ("uri", "pubkey")
    subject = "webid_pubkey_serialized"


class __pubKeyOldOk(WebIDChecks):
    order = 18
    foreach = ("uri", "pubkey")
    test = False


class __profileAllKeysWellFormed(WebIDChecks):
    order = 19
    foreach = ("profile",)
    test = True
    mandatory = False


class __profileOk(WebIDChecks):
    #auto
    order = 20
    foreach = ("profile",)

# webid protocol tests


class __webidClaim(WebIDChecks):
    #auto
    order = 21
    foreach = ("profile",)


class __webidAuthentication(WebIDChecks):
    #auto
    order = 22
    extra = True
    final = True
    foreach = ("profile",)
