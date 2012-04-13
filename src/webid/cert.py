from datetime import datetime
import logging

import M2Crypto

from serializers import Id, PublicKey

logger = logging.getLogger()

#XXX get this from settings
RAISE_CERT_EXCEPTIONS=False


class Cert(Id):
    """
    Class for representing a x509 cert.
    Has validation methods.
    """
    def __init__(self, certstr, *args, **kwargs):
        try:
            self.x509 = M2Crypto.X509.load_cert_string(certstr)
            #XXX get a better regexp for this
            self.b64der = certstr.replace(
                        '-----BEGIN CERTIFICATE-----', '').\
                        replace(
                        '-----END CERTIFICATE-----', '').\
                        replace('\n', '')
        except:
            self.x509 = None
        self.pubkey = PublicKey(None, None)
        self.subjectAltName = None
        super(Cert, self).__init__(*args, **kwargs)

    #
    # cert processing methods
    #

    def get_subjectAltName(self):
        try:
            altName = self.x509.get_ext('subjectAltName').get_value()
            self.subjectAltName = altName
            return altName
        except:
            if RAISE_CERT_EXCEPTIONS:
                raise
            else:
                return None

    def get_pubkey(self):
        #XXX clean
        if not self.x509:
            return None
        mm = str(self.x509.get_pubkey().get_modulus().lower())
        _exp = M2Crypto.m2.rsa_get_e(self.x509.get_pubkey().get_rsa().rsa)
        ee = int(''.join(["%2.2d" % ord(x) for x in _exp[-3:]]), 16)
        self.pubkey = PublicKey(mod=mm, exp=ee)
        logger.debug('cert. mod = %s' % mm)
        logger.debug('cert. exp = %s' % ee)

    def get_exp(self):
        return self.pubkey.exp

    def get_mod(self):
        return self.pubkey.mod

    @property
    def is_pubkey_well_formed(self):
        #XXX check for isint ???
        return True if (self.get_exp() is not None and \
            self.get_mod() is not None) else False

    def check_date_Ok(self):
        if not self.x509:
            return False
        nb = self.x509.get_not_before().get_datetime()
        na = self.x509.get_not_after().get_datetime()
        tz = na.tzinfo
        now = datetime.now(tz)
        return True if ((now > nb) and (now < na)) else False

    def check_days_to_expire(self):
        if not self.x509:
            return False
        na = self.x509.get_not_after().get_datetime()
        tz = na.tzinfo
        now = datetime.now(tz)
        return (na - now).days

    def has_other_critical_extensions(self):
        if not self.x509:
            return False
        ext_count = self.x509.get_ext_count()
        for i in range(ext_count):
            ext = self.x509.get_ext_at(i)
            crit, name = ext.get_critical(), ext.get_name()
            if crit == 1 and name != "subjectAltName":
                return True
        return False
