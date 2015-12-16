#!/usr/bin/env python3
from urllib.parse import urlparse, urlunparse
import os

import requests

from ssdp import discover as ssdp_discover

DOXIE_SSDP_SERVICE = "urn:schemas-getdoxie-com:device:Scanner:1"

class DoxieScanner:
    url = None
    uid = None
    username = "doxie"
    password = None

    def __init__(self, url, uid, password=None):
        self.url = url
        self.uid = uid
        self.password = password

    def __str__(self):
        """
        >>> str(DoxieScanner("http://192.168.100.1:8080/", "uuid:a-b-c::urn:schemas-getdoxie-com:device:Scanner:1"))
        'Doxie Scanner uuid:a-b-c::urn:schemas-getdoxie-com:device:Scanner:1 at http://192.168.100.1:8080/'
        """
        return "Doxie Scanner {} at {}".format(self.uid, self.url)

    @classmethod
    def discover(cls):
        """
        Return a list of DoxieScanner instances, one per device found via
        SSDP. Password is taken from DOXIE_PASSWORD environment var, if set.
        """
        doxies = []
        for response in ssdp_discover(DOXIE_SSDP_SERVICE):
            scheme, netloc, _, _, _, _ = urlparse(response.location)
            url = urlunparse((scheme, netloc, '/', '', '', ''))
            password = os.environ.get("DOXIE_PASSWORD")
            doxies.append(DoxieScanner(url, response.usn, password=password))
        return doxies

    def _api_url(self, path):
        """
        >>> DoxieScanner("http://192.168.100.1:8080/", "")._api_url("/scans.json")
        'http://192.168.100.1:8080/scans.json'
        >>> DoxieScanner("http://192.168.100.1:8080/", "")._api_url("/networks/available.json")
        'http://192.168.100.1:8080/networks/available.json'
        """
        scheme, netloc, _, _, _, _ = urlparse(self.url)
        return urlunparse((scheme, netloc, path, '', '', ''))

    def _api_call(self, path):
        """
        Makes a request to the Doxie scanner on the given path,
        authenticating if necessary.
        """
        url = self._api_url(path)
        auth = (self.username, self.password) if self.password is not None else None
        response = requests.get(url, auth=auth)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()
        return response.json()

    @property
    def scans(self):
        return self._api_call("/scans.json")

def main():
    for doxie in DoxieScanner.discover():
        print("Discovered {}, {} scans available.".format(doxie, len(doxie.scans)))

if __name__ == '__main__':
    main()
