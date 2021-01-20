import os
import time
import json
from configparser import ConfigParser
from http.cookiejar import http2time
from urllib.parse import urlparse, urlunparse, urljoin

import requests

from . import ssdp

DOXIE_SSDP_SERVICE = "urn:schemas-getdoxie-com:device:Scanner:1"

# Scans are downloaded in chunks of this many bytes:
DOWNLOAD_CHUNK_SIZE = 1024*8

class DoxieScanner:
    url = None
    username = "doxie" # This is always the same according to API docs
    password = None

    # connection timeout for API requests made to the scanner
    timeout = 10

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

    def __repr__(self):
        """
        >>> doxie = DoxieScanner("http://192.168.100.1:8080/", load_attributes=False)
        >>> doxie.name = "Doxie_00AAFF"
        >>> doxie.model = "DX250"
        >>> str(doxie)
        '<DoxieScanner: Doxie model DX250 (Doxie_00AAFF) at http://192.168.100.1:8080/>'
        """
        return "<DoxieScanner: {}>".format(str(self))

    @classmethod
    def discover(cls):
        """
        Return a list of DoxieScanner instances, one per device found via
        SSDP.
        """
        doxies = []
        for response in ssdp.discover(DOXIE_SSDP_SERVICE, mx=1, retries=3):
            if DOXIE_SSDP_SERVICE not in response.usn:
                continue  # skip over non-Doxie responses
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
        return urljoin(self.url, path)

    def _api_call(self, path, return_json=True):
        """
        Makes a request to the Doxie scanner on the given path,
        authenticating if necessary.
        Assumes the result is JSON, and returns the result of parsing it.
        Call with return_json=False to skip the JSON parsing step.
        """
        url = self._api_url(path)
        response = self._get_url(url)
        return response.json() if return_json else None

    def _get_url(self, url, stream=False):
        """
        Performs a GET to a URL, including authentication
        if self.password is set.
        Checks that the response status code is 200 before
        returning the response.
        """
        response = requests.get(url, auth=self._get_auth(), stream=stream, timeout=self.timeout)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()
        return response

    def _get_auth(self):
        """
        Returns a (username, password) tuple if self.password is set, otherwise None.
        Suitable for passing to requests' 'auth' kwarg.
        """
        return (self.username, self.password) if self.password is not None else None

    def _load_hello_attributes(self):
        """
        Sets the values from the 'hello' API call as attributes
        on this DoxieScanner instance.
        If a password is required, it's loaded from the INI
        file by _load_password()
        """
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
        Load the password for this Doxie's MAC address from ~/.doxieapi.ini,
        or another path specified by the DOXIEAPI_CONFIG_PATH env variable
        """
        config_path = os.path.expanduser(os.environ.get("DOXIEAPI_CONFIG_PATH", "~/.doxieapi.ini"))
        config = ConfigParser()
        config.read(config_path)
        try:
            self.password = config[self.mac]['password']
        except KeyError as err:
            raise Exception("Couldn't find password for Doxie {} in {}".format(self.mac, config_path)) from err

    @property
    def firmware(self):
        """
        Fetches and caches the 'firmware' string from the 'hello_extra' API call.
        This call is expensive and the value isn't going to change, so
        we're fine to cache it for the lifetime of this DoxieScanner instance.
        """
        if self._firmware is None:
            self._firmware = self._api_call("/hello_extra.json")['firmware']
        return self._firmware

    @property
    def connected_to_external_power(self):
        """
        Returns True if the scanner is connected to AC power.
        This uses the 'hello_extra' API call which is expensive according to
        the docs.
        Doesn't cache the value as it might change.
        """
        attributes = self._api_call("/hello_extra.json")
        # hello_extra is an expensive call so might as well
        # cache the firmware version while we're here...
        self._firmware = attributes['firmware']
        return attributes['connectedToExternalPower']

    @property
    def scans(self):
        """
        Returns a list of scans available on the Doxie
        """
        return self._api_call("/scans.json")

    @property
    def recent(self):
        """
        Returns the path of the most recent scan available on the Doxie.
        This seems to be cached on the Doxie and may refer to a scan
        which has subsequently been deleted.
        """
        return self._api_call("/scans/recent.json")['path']

    def restart_wifi(self):
        """
        Restarts the wifi on the Doxie
        """
        self._api_call("/restart.json", return_json=False)

    def download_scan(self, path, output_dir):
        """
        Downloads a scan at the given path to the given local dir,
        preserving the filename.
        Will raise an exception if the target file already exists.
        Returns the path of the downloaded file.
        """
        if not path.startswith("/scans"):
            path = "/scans{}".format(path)
        url = self._api_url(path)
        response = self._get_url(url, stream=True)
        output_path = os.path.join(output_dir, os.path.basename(path))
        if os.path.isfile(output_path):
            raise FileExistsError(output_path)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                f.write(chunk)
        # Set file timestamp to that of the file we downloaded
        if response.headers.get('Last-Modified'):
            timestamp = http2time(response.headers.get('Last-Modified'))
            os.utime(output_path, (timestamp,)*2)

        return output_path

    def download_scans(self, output_dir):
        """
        Downloads all available scans from this Doxie to the specified dir,
        preserving the filenames from the scanner.
        Returns a list of the downloaded files.
        """
        output_files = []
        for scan in self.scans:
            output_files.append(self.download_scan(scan['name'], output_dir))
        return output_files

    def delete_scan(self, path, retries=3, timeout=5):
        """
        Deletes a scan from the Doxie.
        This method may be slow; from the API docs:
           Deleting takes several seconds because a lock on the internal storage
           must be obtained and released. Deleting may fail if the lock cannot
           be obtained (e.g., the scanner is busy), so consider retrying on
           failure conditions.
        This method will attempt the deletion multiple times with a timeout
        between attempts - controlled by the retries and timeout (seconds) params.
        Returns a boolean indicating whether the deletion was successful.
        """
        if not path.startswith("/scans"):
            path = "/scans{}".format(path)
        url = self._api_url(path)
        auth = self._get_auth()
        for attempt in range(retries):
            response = requests.delete(url, auth=auth)
            if response.status_code == requests.codes.no_content:
                return True
            if attempt < retries-1:
                time.sleep(timeout)
        return False

    def delete_scans(self, paths, retries=3, timeout=5):
        """
        Deletes multiple scans from the Doxie.
        This method may be slow; from the API docs:
           Deleting takes several seconds because a lock on the internal storage
           must be obtained and released. Deleting may fail if the lock cannot
           be obtained (e.g., the scanner is busy), so consider retrying on
           failure conditions.
        This method will attempt the deletion multiple times with a timeout
        between attempts - controlled by the retries and timeout (seconds) params.
        Returns a boolean indicating whether the deletion was successful.
        The deletion is considered successful by the Doxie if at least one scan
        was deleted, it seems.
        """
        url = self._api_url("/scans/delete.json")
        auth = self._get_auth()
        for attempt in range(retries):
            response = requests.post(url, auth=auth, data=json.dumps(paths))
            if response.status_code == requests.codes.no_content:
                return True
            if attempt < retries-1:
                time.sleep(timeout)
        return False
