#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setuptools configuration script.
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.rst') as readme_file:
    README = readme_file.read()
    DESC = README.split('\n')[0]

with open('RELEASE_NOTES.rst') as history_file:
    RELEASE_NOTES = history_file.read().replace('.. :changelog:', '')

from __meta__ import __version__, __author__, __contact__

REQUIREMENTS = ['Flask==1.0.2',
		'pymongo==3.4.0',
                'mock==2.0.0',
		'pytz==2017.2']

setup(
    # -- Meta information --------------------------------------------------
    name='jass',
    version=__version__,
    description=DESC,
    long_description=README + '\n\n' + RELEASE_NOTES,
    author=__author__,
    author_email=__contact__,
    url='http://www.crim.ca',
    license="copyright CRIM 2015",
    platforms=['linux-x86_64'],
    keywords='CANARIE, Annotation Storage, Services',
    classifiers=[
        'Natural Language :: English',
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
    ],

    # -- Package structure -------------------------------------------------
    packages=['jass'],

    install_requires=REQUIREMENTS,
    zip_safe=False,

    exclude_package_data={'jass': ['.hg', '.hglf']},

    package_data={
        'jass': ['jass/*.*','static/*', 'migrations/*','templates/*.*','templates/annotation_storage/*.*'],
        }

    )

