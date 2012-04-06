WEBID_SPARQL_SIMPLE = """
PREFIX cert: <http://www.w3.org/ns/auth/cert#>
PREFIX rsa: <http://www.w3.org/ns/auth/rsa#>
SELECT ?mod ?exp
WHERE { [] cert:key [
        cert:modulus ?mod;
        cert:exponent ?exp;
        ] .
}
"""

NAME_SPARQL = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?uri ?name ?nick ?mbox ?givenName ?familyName
WHERE {
   OPTIONAL {
      ?uri foaf:name ?name .
      ?uri foaf:nick ?nick .
      ?uri foaf:mbox ?mbox .
      ?uri foaf:givenName ?givenName .
      ?uri foaf:familyName ?familyName .
   }
}
"""
###################################################
# WebID TestSuite TESTCASES

TESTCASES = """
PREFIX earl: <http://www.w3.org/ns/earl#>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX wit: <http://www.w3.org/2005/Incubator/webid/earl/RelyingParty#>

SELECT ?test ?title ?description ?note ?part
WHERE { ?test rdf:type earl:TestCase .
        OPTIONAL {?test dc:title ?title .}
        OPTIONAL {?test dc:description ?description .}
        OPTIONAL {?test skos:note ?note .}
        OPTIONAL {?test dc:hasPart ?part .}
}
"""

# WebID TestSuite TESTEREQS

TESTREQS = """
PREFIX earl: <http://www.w3.org/ns/earl#>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX wit: <http://www.w3.org/2005/Incubator/webid/earl/RelyingParty#>

SELECT ?test ?title ?description ?note ?part
WHERE { ?test rdf:type earl:TestRequirement .
        OPTIONAL {?test dc:title ?title .}
        OPTIONAL {?test dc:description ?description .}
        OPTIONAL {?test skos:note ?note .}
        OPTIONAL {?test dc:hasPart ?part .}
        }
}
"""

PUBKEY_RDF = """
<rdf:Description rdf:nodeID="%(iduuid)s">
  <rdf:type rdf:resource="http://www.w3.org/ns/auth/rsa#RSAPublicKey"/>
  <rsa:modulus rdf:datatype="http://www.w3.org/ns/auth/cert#hex">
    %(mod)s</rsa:modulus>
  <rsa:public_exponent
    rdf:datatype="http://www.w3.org/ns/auth/cert#int">%(exp)s
    </rsa:public_exponent>
 </rdf:Description>
"""


FORMATS = {
        'rdf':  'application/rdf+xml',
        'rdfa': 'application/xhtml+xml',
        'turtle': 'text/turtle',
        'n3': 'text/rdf+n3',
        #'html': 'text/html',
}


################################################
# TODO check ASK support in rdflib

SPARQL_WEBID_ASK = """
PREFIX : <http://www.w3.org/ns/auth/cert#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
ASK {
  ?webid :key [
    :modulus ?mod;
    :exponent ?exp;
    ] .
}
"""

################################################
# Deprecated, old spec version
# left here for comparison
# (and we might use it for the testsuite, it can
# be useful to tell the user/implementor that she's
# using the old format.

WEBID_SPARQL_OLD = """
PREFIX cert: <http://www.w3.org/ns/auth/cert#>
PREFIX rsa: <http://www.w3.org/ns/auth/rsa#>
SELECT ?modulus ?exp
WHERE {
   ?key cert:identity ?entity;
       rsa:modulus [ cert:hex ?modulus; ];
       rsa:public_exponent [ cert:decimal ?exp ] .
}
"""

# Also, deprecated
WEBID_SPARQL_SIMPLE_OLD = """
PREFIX cert: <http://www.w3.org/ns/auth/cert#>
PREFIX rsa: <http://www.w3.org/ns/auth/rsa#>
SELECT ?m ?e
WHERE {
   [] cert:identity ?webid ;
        rsa:modulus ?m ;
        rsa:public_exponent ?e .
}
"""

SPARQL_WEBID_ASK_OLD = """
PREFIX cert: <http://www.w3.org/ns/auth/cert#>
PREFIX rsa: <http://www.w3.org/ns/auth/rsa#>
ASK {
   [] cert:identity <http://example.org/webid#public>;
    rsa:modulus  "%(mod)s"^^cert:hex;
    rsa:public_exponent "%(exp)s"^^cert:int .
}
"""

RDFA_DTD = "http://www.w3.org/MarkUp/DTD/xhtml-rdfa-1.dtd"
