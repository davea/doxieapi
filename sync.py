#!/usr/bin/env python3
import os
import shutil
import tempfile
from hashlib import sha1

import click

from doxieapi import DoxieScanner

def sync_doxie_to_directory(doxie, output_dir):
    """
    Syncs all available scans on the given DoxieScanner
    to a subdirectory of output_dir named the same as the DoxieScanner.
    """
    # Create the directory that's going to hold the final files
    scans_dir = os.path.join(output_dir, doxie.name)
    if not os.path.isdir(scans_dir):
        os.makedirs(scans_dir)

    # Download the available scans to a temporary directory
    # then copy any new ones to the final scans directory
    with tempfile.TemporaryDirectory() as tmpdir:
        for file in doxie.download_scans(tmpdir):
            filehash = get_file_hash(file)
            output_file = "{}.{}".format(filehash, file.split(".")[-1].lower())
            output_path = os.path.join(scans_dir, output_file)
            if not os.path.exists(output_path):
                print("Copying file {} to {}".format(os.path.basename(file), output_path))
                shutil.copyfile(file, output_path)
            else:
                print("File already exists: {}".format(output_path))

def get_file_hash(path):
    """
    Return the SHA1 hash of the contents of the file at the specified path
    """
    with open(path, 'rb') as f:
        return sha1(f.read()).hexdigest()

@click.command()
@click.argument('output_dir', type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True))
def main(output_dir):
    """
    Finds all Doxie scanners on the network and saves all avilable scans
    to the directory given on the command line.
    Scans are arranged into subdirectories, named by
    the scanner they came from.
    """
    print(output_dir)
    for doxie in DoxieScanner.discover():
        sync_doxie_to_directory(doxie, output_dir)

if __name__ == '__main__':
    main()