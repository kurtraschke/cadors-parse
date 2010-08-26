from setuptools import setup, find_packages
import os

name = "cadorsfeed"
version = "0.1"


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(
    name=name,
    version=version,
    description="a hello world demo",
    long_description=read('README'),
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[],
    keywords="",
    author="Kurt Raschke",
    author_email='kurt@kurtraschke.com',
    url='',
    license='',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'Werkzeug',
        'Redis',
        'lxml',
        'mechanize',
        'html5lib',
        'pyRFC3339',
        'geolucidate',
    ],
    entry_points="""
    [console_scripts]
    flask-ctl = cadorsfeed.script:run

    [paste.app_factory]
    main = cadorsfeed.script:make_app
    debug = cadorsfeed.script:make_debug
    """,
)
