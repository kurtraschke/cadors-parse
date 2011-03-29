from setuptools import setup, find_packages
import os

name = "cadorsfeed"
version = "0.1"


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(
    name=name,
    version=version,
    description="Produce an Atom feed from the CADORS National Report",
    long_description=read('README'),
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[],
    keywords="",
    author="Kurt Raschke",
    author_email='kurt@kurtraschke.com',
    url='http://github.com/kurtraschke/cadors-parse',
    license='MIT',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'Flask',
        'Flask-SQLAlchemy',
        'psycopg2',
        'GeoAlchemy',
        'lxml',
        'mechanize',
        'html5lib',
        'SPARQLWrapper',
        'Flask-Script',
        'pyRFC3339',
        'geolucidate',
    ],
    entry_points="""
    [console_scripts]
    manage = cadorsfeed.manage:run
    """,
)
