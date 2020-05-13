#!/usr/bin/env python3

r"""
builder.py
-John Taylor
May-13-2020

Download and compile GNU less with Visual Studio
less.exe and lesskey.exe are created
"""

import os
import os.path
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

LESSURL="http://greenwoodsoftware.com/less/download.html"
COMPILE=r'"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"'

version_url_re = re.compile(r"""Download <strong>BETA</strong> version (.*?) """, re.M|re.S|re.I)

def download_less_web_page() -> str:
    """Download LESSURL and save the contents to fname

    Returns:
        An in-memory version of the downloaded web page
    """

    fname = "download.html"
    try:
        urllib.request.urlretrieve(LESSURL, fname)
        time.sleep(1)
    except:
        return False

    try:
        with open(fname) as fp:
            page = fp.read()
    except:
        return False

    return page

def get_latest_version_url(page:str) -> tuple:
    """Return the URL for the "BETA version"

    Args:
        page: an HTML web page, provided in LESSURL

    Returns:
        A tuple containing: (version number, zip archive URL)
        Ex: 551, http://greenwoodsoftware.com/less/less-551.zip
    """

    match = version_url_re.findall(page)
    if not len(match):
        return (None,None)

    version = match[0]
    archive = "less-%s.zip" % (version)
    url = LESSURL.replace("download.html",archive)
    return (version, url)

def download_and_save(url:str) -> bool:
    """Download the less .zip file and save it to the current directory
    """

    # something like less-561.zip
    archive = url.split("/")[-1]
    if os.path.exists(archive):
        sz = os.stat(archive).st_size
        print("File already exists: %s with size: %d" % (archive, sz))
        return archive

    try:
        urllib.request.urlretrieve(url, archive)
    except:
        return False

    return archive

def extract_archive(archive:str) -> str:
    """Unzip the archive file, remove preexisting directory
    """

    # given "less-561.zip", return "less-561
    zip_dest = os.path.splitext(archive)[0]

    if os.path.exists(zip_dest):
        print("Removing preexisting directory: %s" % (zip_dest))
        try:
            shutil.rmtree(zip_dest)
            time.sleep(1)
        except:
            return False
    try:
        with zipfile.ZipFile(archive,"r") as z:
            z.extractall(".")
    except:
        return False

    return zip_dest

def create_compile_batchfile(archive_dest:str):
    """Create a .bat file containing environment setup
    and nmake compile commands
    """

    bat = "compile.bat"
    try:
        with open(bat, "w") as fp:
            fp.write("@echo off\n")
            fp.write("cd %s\n" % (archive_dest))
            fp.write("call %s\n" % (COMPILE))
            fp.write("nmake /f Makefile.wnm\n")
    except:
        return False

    return bat

def main():
    if not (page := download_less_web_page()):
        print("Unable to download URL: %s" % (LESSURL))
        sys.exit(10)
        return

    version, url = get_latest_version_url(page)
    if None == version:
        print("Unable to extract version from: %s" % (LESSURL), file=sys.stderr)
        sys.exit(20)
    
    if not (archive := download_and_save(url)):
        print("Unable to download file: %s" % (url), file=sys.stderr)
        sys.exit(30)

    if not (archive_dest := extract_archive(archive)):
        print("Unable to unzip archive: %s" % (archive), file=sys.stderr)
        sys.exit(40)
    
    if not ( cmd := create_compile_batchfile(archive_dest)):
        print("Unable to create batch file", file=sys.stderr)
        sys.exit(50)

    result = subprocess.run((cmd,), shell=True, capture_output=True)
    if result.returncode > 0:
        err = result.stderr.decode("utf-8")
        out = result.stdout.decode("utf-8")
        print("Compile failed:\n%s\n\n%s\n" % (out, err))
        sys.exit(60)


if "__main__" == __name__:
    main()
    
# end of script
