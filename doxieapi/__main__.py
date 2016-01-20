import os

from .api import DoxieScanner

def main():
    """
    Grab all available scan images and save them to the current working directory
    """
    for doxie in DoxieScanner.discover():
        print("Discovered {}.".format(doxie))
        for scan in doxie.download_scans(os.getcwd()):
            print("Saved {}".format(scan))

if __name__ == '__main__':
    main()
