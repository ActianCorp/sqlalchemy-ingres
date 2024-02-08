#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import os
import sys

from setuptools import setup, find_packages


if len(sys.argv) <= 1:
    print("""
Suggested setup.py parameters:

    * build
    * install
    * sdist  --formats=zip
    * sdist  # NOTE requires tar/gzip commands

    python -m pip install -e .

PyPi:

    python -m pip install setuptools twine
    twine upload dist/*
    ./setup.py  sdist ; twine upload dist/* --verbose

""")


readme_filename = 'README.md'
if os.path.exists(readme_filename):
    f = open(readme_filename)
    long_description = f.read()
    f.close()
else:
    long_description = None

# pick up version number, __version__
exec(open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib', 'sqlalchemy_ingres', '_version.py')).read())


setup(
    name = "sqlalchemy-ingres",  # note hypen, not underscore
    version = __version__,
    author = "Chris Clark",
    author_email = "Chris.Clark@actian.com",
    url="https://github.com/ActianCorp/sqlalchemy-ingres",
    description = "SQLAlchemy dialect for Actian databases; Actian Data Platform (nee Avalanche), Actian X, Ingres, and Vector",
    long_description=long_description,
    long_description_content_type='text/markdown',
    maintainer = "Michael Habiger",
    maintainer_email = "michael.habiger@hcl-software.com",

    license = "Apache-2.0",

    packages=find_packages('lib'),  # TODO review, remove and replace with static and py_modules
    package_dir={'':'lib'},

    classifiers=[  # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Topic :: Database',
        'Programming Language :: SQL',
        ],
    platforms='any',  # or distutils.util.get_platform()
    install_requires=['sqlalchemy'],
    extras_require={
        'pyodbc' : ['pyodbc', ],
        'pypyodbc' : ['pypyodbc', ],
        'all' : ['pypyodbc', 'pyodbc', ],
    },

    entry_points = {                                                
        'sqlalchemy.dialects': [                                    
            'ingres = sqlalchemy_ingres:base.dialect',  # note underscore, not hypen
            'ingres.pyodbc = sqlalchemy_ingres.pyodbc:Ingres_pyodbc'  # note underscore, not hypen
        ]                                                           
    }                                                               
)
