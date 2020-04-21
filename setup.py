from setuptools import setup, find_packages
setup(
    name = "ingres_sa_dialect",
    version = "0.1",
    author = "Anthony Simpson",
    author_email = "anthony.simpson@ingres.com",
    description = "An Ingres dialect for SQLAlchemy",

    license = "MIT",

    packages=find_packages('lib'),
    package_dir={'':'lib'},

    entry_points="""
    [sqlalchemy.dialects]
    ingres = ingres_sa_dialect:base.dialect
    """
)
