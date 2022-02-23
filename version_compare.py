#!/usr/bin/env python3

r"""
version_compare.py
-John Taylor
May-14-2020

Compare local github version with less web site
"""

import json
import urllib.request
import re
import sys
from shared import download_less_web_page, get_latest_version_url, LESSURL, NEWFILE

LOCALURL = "https://api.github.com/repos/jftuga/less-Windows/releases"


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


def get_latest_local_version(page: str) -> str:
    """Extract and return the lastest release version from a JSON page
       Ex: 561
    """
    try:
        j = json.loads(page)
    except:
        return False

    if not len(j):
        return "500"

    newest = j[0]
    print(f'{newest["tag_name"]=}')
    # The initial version is different than future versions
    if "v560" == newest["tag_name"]:
        return "560"

    # given less-v561.17, return 561
    release_version = newest["tag_name"][6:11]
    if release_version.endswith(".0"):
        release_version = re.sub("\.0$", "", release_version)
    print(f'{release_version=}')
    return release_version


def main():
    """Write to new.txt when a new version needs to be downloaded
    """
    if not (page := download_local_web_page()):
        print("Unable to download URL: %s" % (LOCALURL))
        sys.exit(10)

    if not (local_version := get_latest_local_version(page)):
        print("Unable to extract version from URL: %s" % (LOCALURL))
        sys.exit(20)

    if not (page := download_less_web_page()):
        print("Unable to download URL: %s" % (LESSURL))
        sys.exit(30)
        return

    remote_version, _ = get_latest_version_url(page)
    if remote_version is None:
        print("Unable to extract version from: %s" % (LESSURL), file=sys.stderr)
        sys.exit(40)

    if remote_version == local_version:
        print(f"Versions are the same: remote_version: {remote_version}   local_version: {local_version}")
        return

    if float(local_version) >= float(remote_version):
        print(f"Local version is newer: local_version: {local_version}   remote_version: {remote_version}")
        sys.exit(120)

    print(f"Remote version is newer: remote_version: {remote_version}   local_version: {local_version}")
    print(f"Saving new version to file: {NEWFILE}")
    try:
        with open(NEWFILE, mode="w") as fp:
            fp.write("%s\n" % remote_version)
    except:
        print(f"Unable able to open file for writing: {NEWFILE}")
        sys.exit(50)


if "__main__" == __name__:
    main()
