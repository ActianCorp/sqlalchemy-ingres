from setuptools import setup, find_packages
setup(
    name = "ingres_sa_dialect",
    version = "0.2",
    author = "Chris Clark",
    author_email = "Chris.Clark@actian.com",
    description = "An Ingres dialect for SQLAlchemy",

    license = "MIT",

    packages=find_packages('lib'),
    package_dir={'':'lib'},

    entry_points="""
    [sqlalchemy.dialects]
    ingres = ingres_sa_dialect:base.dialect
    """
)
