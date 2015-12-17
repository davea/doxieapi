#!/usr/bin/env python3
import os
from configparser import ConfigParser
from urllib.parse import urlparse, urlunparse

import requests

from ssdp import discover as ssdp_discover

DOXIE_SSDP_SERVICE = "urn:schemas-getdoxie-com:device:Scanner:1"

class DoxieScanner:
    url = None
    username = "doxie"
    password = None

    # These attributes will be populated by _load_hello_attributes
    model = None
    name = None
    mac = None
    mode = None
    network = None
    firmware_wifi = None
    # This attribute comes from the 'hello_extra' API call, which is expensive
    # so it's lazily loaded and cached via a @property
    _firmware = None

    def __init__(self, url, load_attributes=True):
        self.url = url
        if load_attributes:
            self._load_hello_attributes()

    def __str__(self):
        """
        >>> doxie = DoxieScanner("http://192.168.100.1:8080/", load_attributes=False)
        >>> doxie.name = "Doxie_00AAFF"
        >>> doxie.model = "DX250"
        >>> str(doxie)
        'Doxie model DX250 (Doxie_00AAFF) at http://192.168.100.1:8080/'
        """
        return "Doxie model {} ({}) at {}".format(self.model, self.name, self.url)

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
            doxies.append(DoxieScanner(url))
        return doxies

    def _api_url(self, path):
        """
        >>> DoxieScanner("http://192.168.100.1:8080/", load_attributes=False)._api_url("/scans.json")
        'http://192.168.100.1:8080/scans.json'
        >>> DoxieScanner("http://192.168.100.1:8080/", load_attributes=False)._api_url("/networks/available.json")
        'http://192.168.100.1:8080/networks/available.json'
        """
        scheme, netloc, _, _, _, _ = urlparse(self.url)
        return urlunparse((scheme, netloc, path, '', '', ''))

    def _api_call(self, path, return_json=True):
        """
        Makes a request to the Doxie scanner on the given path,
        authenticating if necessary.
        Assumes the result is JSON, and returns the result of parsing it.
        Call with return_json=False to skip the JSON parsing step.
        """
        url = self._api_url(path)
        auth = (self.username, self.password) if self.password is not None else None
        response = requests.get(url, auth=auth)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()
        return response.json() if return_json else None

    def _load_hello_attributes(self):
        attributes = self._api_call("/hello.json")
        self.model = attributes['model']
        self.name = attributes['name']
        self.mac = attributes['MAC']
        self.mode = attributes['mode']
        self.firmware_wifi = attributes['firmwareWiFi']
        if self.mode == "Client":
            self.network = attributes['network']
        if attributes['hasPassword'] == True:
            self._load_password()

    def _load_password(self):
        """
        Load the password for this Doxie's MAC address from ~/.doxiegrabber.ini,
        or another path specified by the DOXIEGRABBER_CONFIG_PATH env variable
        """
        config_path = os.path.expanduser(os.environ.get("DOXIEGRABBER_CONFIG_PATH", "~/.doxiegrabber.ini"))
        config = ConfigParser()
        config.read(config_path)
        try:
            self.password = config[self.mac]['password']
        except KeyError:
            raise Exception("Couldn't find password for Doxie {} in {}".format(self.mac, config_path))

    @property
    def firmware(self):
        if self._firmware is None:
            self._firmware = self._api_call("/hello_extra.json")['firmware']
        return self._firmware

    @property
    def connected_to_external_power(self):
        attributes = self._api_call("/hello_extra.json")
        # hello_extra is an expensive call so might as well
        # cache the firmware version while we're here...
        self._firmware = attributes['firmware']
        return attributes['connectedToExternalPower']

    @property
    def scans(self):
        return self._api_call("/scans.json")

    def restart_wifi(self):
        self._api_call("/restart.json", return_json=False)

def main():
    for doxie in DoxieScanner.discover():
        print("Discovered {}, {} scans available.".format(doxie, len(doxie.scans)))

if __name__ == '__main__':
    main()
