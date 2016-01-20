from setuptools import setup, find_packages
from distutils import log

try:
    import pypandoc
    pypandoc.convert("README.md", "rst", outputfile="README.rst")
except ImportError:
    log.warn("warning: Couldn't generate README.rst - is pypandoc installed?")

setup(
    name = "doxieapi",
    version = "0.0.1",
    packages = find_packages(),

    install_requires = ['requests'],

    author = "Dave Arter",
    author_email = "pypi@davea.me",
    description = "Library for downloading scans from a Doxie Go Wi-Fi document scanner",
    license = "LICENSE.txt",
    keywords = "doxie document scanner",
    url = "https://github.com/davea/doxieapi/",
)
