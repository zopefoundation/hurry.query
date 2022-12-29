##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Setup

$Id$
"""
import html
import os

from setuptools import find_packages
from setuptools import setup


def read(*rnames):
    text = open(os.path.join(os.path.dirname(__file__), *rnames)).read()
    return html.escape(text)


tests_require = [
    'testfixtures',
    'zope.container',
    ]

setup(
    name="hurry.query",
    version='3.3.dev0',
    author='Infrae',
    author_email='faassen@startifact.com',
    description="Higher level query system for the zope.catalog",
    long_description=(read('README.txt') +
                      '\n\n' +
                      read('CHANGES.txt')),
    license='ZPL 2.1',
    keywords="zope zope3 catalog index query",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Framework :: Zope :: 3',
    ],
    url='http://pypi.python.org/pypi/hurry.query',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['hurry'],
    package_data={
        '': ['*.txt', '*.zcml'],
    },
    zip_safe=False,
    install_requires=[
        'BTrees',
        'six',
        'setuptools',
        'transaction',
        'zc.catalog',
        'zope.cachedescriptors',
        'zope.catalog',
        'zope.component',
        'zope.index',
        'zope.interface',
        'zope.intid',
        'zope.location',
    ],
    tests_require=tests_require,
    extras_require={'test': tests_require},
    )
