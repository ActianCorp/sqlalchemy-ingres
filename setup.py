from setuptools import setup, find_packages
setup(
    name = "sqlalchemy-ingres",  # note hypen, not underscore
    version = "0.4",  # FIXME embed/pull from code - https://github.com/ActianCorp/sqlalchemy-ingres/issues/10
    author = "Chris Clark",
    author_email = "Chris.Clark@actian.com",
    description = "SQLAlchemy dialect for Actian databases; Actian Data Platform (nee Avalanche), Actian X, Ingres, and Vector",
    maintainer = "Michael Habiger",
    maintainer_email = "michael.habiger@hcl-software.com",

    license = " Apache-2.0",
    # FIXME long description, pull from readme?

    packages=find_packages('lib'),
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

    entry_points = {                                                
        'sqlalchemy.dialects': [                                    
            'ingres = sqlalchemy_ingres:base.dialect',  # note underscore, not hypen
            'ingres.pyodbc = sqlalchemy_ingres.pyodbc:Ingres_pyodbc'  # note underscore, not hypen
        ]                                                           
    }                                                               
)
