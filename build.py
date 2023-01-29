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
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from shared import download_less_web_page, get_latest_version_url, LESSURL


def download_and_save(url: str) -> bool:
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


def extract_archive(archive: str) -> str:
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
        with zipfile.ZipFile(archive, "r") as z:
            z.extractall(".")
    except:
        return False

    return zip_dest


def create_compile_batchfile(archive_dest: str):
    """Create a .bat file containing environment setup
    and nmake compile commands
    """

    bat = "compile.bat"
    try:
        with open(bat, "w") as fp:
            fp.write("@echo off\n")
            fp.write("cd %s\n" % (archive_dest))
            fp.write("nmake /f Makefile.wnm\n")
            fp.write("copy /y less.exe ..\n")
            fp.write("copy /y lesskey.exe ..\n")
    except:
        return False

    return bat


def main():
    if not (page := download_less_web_page()):
        print("Unable to download URL: %s" % (LESSURL))
        sys.exit(10)
        return

    version, url = get_latest_version_url(page)
    if version is None:
        print("Unable to extract version from: %s" % (LESSURL), file=sys.stderr)
        sys.exit(20)

    if not (archive := download_and_save(url)):
        print("Unable to download file: %s" % (url), file=sys.stderr)
        sys.exit(30)

    if not (archive_dest := extract_archive(archive)):
        print("Unable to unzip archive: %s" % (archive), file=sys.stderr)
        sys.exit(40)

    if not (cmd := create_compile_batchfile(archive_dest)):
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
