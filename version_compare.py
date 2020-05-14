#!/usr/bin/env python3

r"""
version_compare.py
-John Taylor
May-14-2020

Compare local github version with less web site
"""

import json
import urllib.request
import sys
from shared import download_less_web_page, get_latest_version_url, LESSURL

LOCALURL="https://api.github.com/repos/jftuga/less-Windows/releases"

def download_local_web_page() -> str:
    """Download and return JSON from LOCALURL
    """
    try:
        with urllib.request.urlopen(LOCALURL) as f:
            page = f.read()
    except:
        return False

    page = page.decode("utf-8")
    return page

def get_latest_local_version(page:str) -> str:
    """Extract and return the lastest release version from a JSON page
       Ex: 561
    """
    try:
        j = json.loads(page)
    except:
        return False
    
    newest = j[0]
    # given less-v561.17, return 561
    release_version = newest["name"][6:9]
    return release_version

def main():
    """Return exit value 0 when a new version needs to be downloaded
    """
    if not (page := download_local_web_page()):
        print("Unable to download URL: %s" % (LOCALURL))
        sys.exit(10)

    if not (local_version := get_latest_local_version(page)):
        print("Unable to download URL: %s" % (LOCALURL))
        sys.exit(20)

    if not (page := download_less_web_page()):
        print("Unable to download URL: %s" % (LESSURL))
        sys.exit(30)
        return

    remote_version, _ = get_latest_version_url(page)
    if None == remote_version:
        print("Unable to extract version from: %s" % (LESSURL), file=sys.stderr)
        sys.exit(40)

    if remote_version == local_version:
        print(f"Versions are the same: remote_version: {remote_version}   local_version: {local_version}")
        sys.exit(100)
    
    print("Remote version is newer: remote_version: {remote_version}   local_version: {local_version}")

if "__main__" == __name__:
    main()
    