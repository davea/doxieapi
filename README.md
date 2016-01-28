# `doxieapi`

A Python library for the [developer API](http://help.getdoxie.com/doxiego/advanced/wifi/api/)
of the [Doxie Go Wi-Fi](http://www.getdoxie.com/product/doxie-go/) document scanner.

## Installation

doxieapi is available on PyPI: https://pypi.python.org/pypi/doxieapi. Install with pip:

```sh
$ pip install doxieapi
```

## Usage

Doxie scanners on the network can discovered automatically using SSDP:

```python
>>> from doxieapi import DoxieScanner
>>> scanners = DoxieScanner.discover()
>>> print(scanners)
[<DoxieScanner: Doxie model DX250 (Doxie_01AFD2) at http://10.0.1.3:8080/>]
```

Recent and all scans can be listed:

```python
>>> scanner = scanners[0]
>>> scanner.recent
'/DOXIE/JPEG/IMG_0074.JPG'
>>> scanner.scans[:2]
[{'modified': '2010-05-01 00:17:28', 'name': '/DOXIE/JPEG/IMG_0001.JPG', 'size': 1365552},
{'modified': '2010-05-01 00:17:44', 'name': '/DOXIE/JPEG/IMG_0002.JPG', 'size': 1362595}]
```

Scans can be downloaded individually or all at once:

```python
>>> scanner.download_scan("/DOXIE/JPEG/IMG_0001.JPG", "/tmp")
'/tmp/IMG_0001.JPG'
>>> scanner.download_scans("/tmp")
['/tmp/IMG_0001.JPG', '/tmp/IMG_0002.JPG']
```

Scans can be deleted too:

```python
>>> scanner.delete_scan("/DOXIE/JPEG/IMG_0001.JPG")
True
>>> scanner.delete_scans([scan['name'] for scan in scanner.scans])
True
```

Other attributes from the API can be queried:

```python
>>> scanner.firmware
'0.26'
>>> scanner.network
'supersecretwifi'
>>> scanner.name
'Doxie_01AFD2'
>>> scanner.firmware_wifi
'1.29'
```

You can also run the module directly to download all available scans from all Doxies on
the network to the current directory:

```sh
$ python -m doxieapi
Discovered Doxie model DX250 (Doxie_01AFD2) at http://10.0.1.3:8080/
Saved /Users/dave/Code/doxieapi/doxieapi/IMG_0001.JPG
Saved /Users/dave/Code/doxieapi/doxieapi/IMG_0002.JPG
```

## Configuration

Connecting to password-protected Doxies is made possible by putting the password for
each scanner in `~/.doxieapi.ini`. Create sections named with the scanner's MAC address,
for example:

```ini
[00:11:22:33:44:55]
password=supersecretpassword
```


## Credits

Includes [ssdp.py](https://gist.github.com/dankrause/6000248) by [Dan Krause](https://github.com/dankrause).
