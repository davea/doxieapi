#!/usr/bin/env python3
from urllib.parse import urlparse, urlunparse

from ssdp import discover as ssdp_discover

DOXIE_SSDP_SERVICE = "urn:schemas-getdoxie-com:device:Scanner:1"

class DoxieScanner:
    url = None
    uid = None

    def __init__(self, url, uid):
        self.url = url
        self.uid = uid

    def __str__(self):
        """
        >>> str(DoxieScanner("http://192.168.100.1:8080/", "uuid:a-b-c::urn:schemas-getdoxie-com:device:Scanner:1"))
        'Doxie Scanner uuid:a-b-c::urn:schemas-getdoxie-com:device:Scanner:1 at http://192.168.100.1:8080/'
        """
        return "Doxie Scanner {} at {}".format(self.uid, self.url)

    @classmethod
    def discover(cls):
        doxies = []
        for response in ssdp_discover(DOXIE_SSDP_SERVICE):
            scheme, netloc, _, _, _, _ = urlparse(response.location)
            url = urlunparse((scheme, netloc, '/', '', '', ''))
            doxies.append(DoxieScanner(url, response.usn))
        return doxies

def main():
    for doxie in DoxieScanner.discover():
        print(doxie)

if __name__ == '__main__':
    main()