from setuptools import setup, find_packages
from distutils import log
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = "doxieapi",
    version = "0.1.2",
    packages = find_packages(),

    install_requires = ['requests'],

    author = "Dave Arter",
    author_email = "pypi@davea.me",
    description = "Library for downloading scans from a Doxie Go Wi-Fi document scanner",
    long_description = long_description,
    long_description_content_type="text/markdown",
    license = "LICENSE",
    keywords = "doxie document scanner",
    url = "https://github.com/davea/doxieapi/",
    python_requires = ">=3.4",
)
