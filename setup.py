#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages
import os

execfile('./src/webid/__init__.py')
VERSION = __version__

setup_root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(setup_root, "src"))

long_description = """A python lib implementing server-side validation and client ssl authentication following the WebID spec"""

packages = find_packages('src')
setup(
    name='python-webid',
    package_dir={'': 'src'},
    packages=packages,
    #include_package_data=True,
    exclude_package_data={
        'requirements': ['%s/*.tar.gz' % VERSION],
    },
    version=VERSION,
    description='A python lib implementing server-side validation \
    and client ssl authentication following the WebID spec',
    long_description=long_description,
    author='Ben Carrillo',
    author_email='bennomadic at gmail dot com',
    download_url='https://github.com/bennomadic/python-webid.git',
    #url=...
    install_requires=['M2Crypto>=0.20.2', 'rdflib>=3.2.0-RC', 'rdfextras',
        'requests', 'html5lib'],
    #test_requires=[],
    platforms=['any'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='foaf, ssl, webid, x509, certificate, \
        client certificate, authentication',
    zip_safe=False,
)
