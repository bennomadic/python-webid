.. python-webid documentation master file, created by
   sphinx-quickstart on Thu Jan 19 01:22:47 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to python-webid's documentation!
========================================

**python-webid** is an *early-alpha* implementation of the  `WebID <http://www.w3.org/2005/Incubator/webid/spec/>`_ 
Identification and Discovery protocol.

Currently it consists only of a validator and a (very simple, really) client.

Getting Started
===============

  git clone git://github.com/bennomadic/python-webid.git

**TBD**
(setup install, pypi...)

WebIDValidator
==============

The validator, besides checking if a given client WebID certificate matches the conditions for allowing a 
WebID authentication, returns a set of result objects that can be used to generate a spec-compliance report.

For now, the validator parses the earl vocabulary for the WebID authentication and uses some of the extracted
information to structure the series of checks that lead to the WebID validation.

Read more about the `WebID Test Suite <http://www.w3.org/2005/Incubator/webid/wiki/Test_Suite>`_

To use the validator, you have to initialize it passing a base64 encoded certificate::

  from webid.validator import WebIDValidator

  certstr = """
  -----BEGIN CERTIFICATE-----
  MIIDGjCCAoOgAwIBAgIBaDANBgkqhkiG9w0BAQUFADBjMSYwJAYDVQQDEx1Ob3Qg
  YSBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTERMA8GA1UEChMIRk9BRitTU0wxJjAk
  ...
  kgBsn3XOUUqKQXMe+uH2Q5fCYKRqYCBCC1qpLy3x
  -----END CERTIFICATE-----
  """

  webidval = WebIDValidator(certstr=certstr)
  validated, data = validator.validate() 

where *validated* is a bool indicating whether the authentication was successful or not.

Not very polished yet... but you can inspect the results for the passed checks (by execution order) in::

  webidval.testbed.tests


WebID Client
============
**TBD**

Using **python-webid** from other apps
======================================
**TBD: django app for webid auth**

TestSuite
=========
**TBD**

Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

