import uuid
try:
    from collections import namedtuple
except ImportError:
    # python2.5 backport
    from xcollections import namedtuple
from constants import PUBKEY_RDF

"""
Several classes to represent crypto objects,
like Pubkeys or Certs, that are being used
in the validation (and reporting) process.

TODO I don't like this "serializers" name.
but have to find something better. ideas?
"""


#this could be turned into a class decorator !
class Id(object):
    """
    base class that adds an uuid identifier
    to derived objects. Used for generating the
    rdf graph for the earl results report.
    """
    def __init__(self, *args, **kwargs):
        self.uuid = uuid.uuid4()
        super(Id, self).__init__()

    def id_uuid(self):
        return u"uuid%s" % unicode(self.uuid)


PK = namedtuple('PublicKey', ['mod', 'exp'])


class PublicKey(PK, Id):
    def to_rdf(self):
        iduuid = "%(id)s-serialized-xml" % {'id': self.uuid}
        return PUBKEY_RDF % {
                'iduuid': iduuid,
                'mod': self.mod,
                'exp': self.exp}


class Profile(Id):
    """
    A Container Class for profile objects
    (dereferenced URIs contained in the WebID cert SAN).
    """
    def __init__(self, dump, *args, **kwargs):
        self.dump = dump
        super(Profile, self).__init__(*args, **kwargs)


class WebIDClaim(Id):
    """
    A Container class for WebID Claims.
    It's initialized with the claimedURI and the Public
    Key that it ties together.
    """
    def __init__(self, claimedURI, pk, *args, **kwargs):
        self.claimedURI = claimedURI
        self.pubkey = PublicKey() if pk is None else pk
        super(WebIDClaim, self).__init__(*args, **kwargs)
