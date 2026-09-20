#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "feedparser>=6.0.12,<7",
#     "httpx>=0.28.1,<1",
#     "packaging>=25,<27",
# ]
# ///

"""Build an official stable less release in a Visual Studio Developer shell."""

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import urlsplit

import feedparser
import httpx
from packaging.version import Version

FEED_URL = "https://greenwoodsoftware.com/less/feed/"
SIGNING_KEY_URL = "https://greenwoodsoftware.com/less/pubkey.asc"
# Mark Nudelman's release key; key rotation requires updating this trusted fingerprint.
SIGNING_KEY_FINGERPRINT = "AE27252BD6846E7D6EAE1DD6F153A7C833235259"
VERSION_PATTERN = r"[0-9]+(?:\.[0-9]+)*"


@dataclass(frozen=True)
class Release:
    version: str
    url: str
    notes_url: str
    signature_url: str


def feed_link(entry, relation: str, media_type: str) -> str:
    for link in entry.get("links", []):
        if link.get("rel") == relation and link.get("type") == media_type:
            url = link.get("href", "")
            parsed = urlsplit(url)
            if (
                parsed.scheme != "https"
                or parsed.hostname not in {"greenwoodsoftware.com", "www.greenwoodsoftware.com"}
                or not parsed.path.startswith("/less/")
                or parsed.username is not None
                or parsed.password is not None
            ):
                raise ValueError(f"Unexpected upstream URL in feed: {url}")
            return url
    raise ValueError(f"Missing {media_type} {relation} link in {entry.get('id', 'feed entry')}")


def select_release(content: bytes, requested: str | None = None) -> Release:
    feed = feedparser.parse(content)
    if feed.get("bozo") or feed.get("version") != "atom10":
        raise ValueError("Upstream returned an invalid Atom feed")
    releases = {}
    for entry in feed.entries:
        if not any(tag.get("term") == "production" for tag in entry.get("tags", [])):
            continue
        match = re.fullmatch(rf"data:less-({VERSION_PATTERN})-production", entry.get("id", ""))
        if not match:
            raise ValueError(f"Unrecognized stable release ID: {entry.get('id', '')}")
        version = match[1]
        release = Release(
            version,
            feed_link(entry, "alternate", "application/gzip"),
            feed_link(entry, "related", "text/html"),
            feed_link(entry, "related", "application/pgp-signature"),
        )
        if version in releases and releases[version] != release:
            raise ValueError(f"Conflicting feed entries for version {version}")
        releases[version] = release
    if not releases:
        raise ValueError("The Atom feed contains no stable releases")
    if requested is not None:
        if requested not in releases:
            available = ", ".join(sorted(releases, key=Version, reverse=True))
            raise ValueError(
                f"Stable version {requested!r} is not in the current feed. "
                f"Available stable versions: {available}"
            )
        return releases[requested]
    return releases[max(releases, key=Version)]


def check_prerequisites(*, verify: bool = True) -> None:
    if sys.platform != "win32":
        raise RuntimeError("Building less requires Windows and a Visual Studio Developer shell.")
    if verify and not shutil.which("gpg.exe"):
        raise RuntimeError(
            "Signature verification requires gpg.exe on PATH. Install GnuPG (for example, "
            "Gpg4win), or append Git for Windows' usr\\bin directory to PATH."
        )
    missing = [name for name in ("cl.exe", "link.exe", "nmake.exe") if not shutil.which(name)]
    missing += [name for name in ("INCLUDE", "LIB") if not os.environ.get(name)]
    help_text = (
        "Open a Visual Studio Developer Command Prompt or Developer PowerShell "
        "configured for your target architecture, then run uv run build.py again. "
        "Install the Visual Studio C++ build tools and a Windows SDK if needed."
    )
    if missing:
        raise RuntimeError(f"Missing build prerequisites: {', '.join(missing)}.\n{help_text}")
    # A compile/link probe catches an incomplete SDK or a mismatched toolchain before downloading.
    with tempfile.TemporaryDirectory(prefix="less-prerequisites-") as directory:
        probe = Path(directory) / "probe.c"
        probe.write_text("#include <windows.h>\nint main(void) { return 0; }\n", encoding="ascii")
        result = subprocess.run(
            ["cl.exe", "/nologo", "probe.c", "/link", "user32.lib", "shell32.lib"],
            cwd=directory,
            capture_output=True,
            text=True,
            errors="replace",
        )
    if result.returncode:
        raise RuntimeError(
            f"The Visual Studio compiler/SDK check failed:\n"
            f"{result.stdout}{result.stderr}\n{help_text}"
        )


def verify_archive(client: httpx.Client, release: Release, archive: Path) -> None:
    print(f"Verifying less {release.version} package signature...", flush=True)
    signature = archive.parent / "source.sig"
    key = archive.parent / "pubkey.asc"
    for url, path in ((release.signature_url, signature), (SIGNING_KEY_URL, key)):
        response = client.get(url)
        response.raise_for_status()
        path.write_bytes(response.content)

    # Git's GPG needs a relative homedir on Windows; isolate it from the user's keyring.
    with tempfile.TemporaryDirectory(prefix="less-gnupg-") as directory:
        command = [
            "gpg.exe", "--no-options", "--homedir", ".", "--batch",
            "--no-auto-key-retrieve", "--no-autostart",
        ]
        result = subprocess.run(
            [*command, "--import", str(key.resolve())],
            cwd=directory, capture_output=True, text=True, errors="replace",
        )
        if result.returncode:
            raise RuntimeError(f"Cannot import the less signing key:\n{result.stderr}")
        result = subprocess.run(
            [*command, "--status-fd", "1", "--verify", str(signature.resolve()), str(archive.resolve())],
            cwd=directory, capture_output=True, text=True, errors="replace",
        )
        valid_signer = False
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 11 and fields[:2] == ["[GNUPG:]", "VALIDSIG"]:
                # GPG includes the primary fingerprint when a signing subkey is used.
                fingerprint = fields[11] if len(fields) > 11 else fields[2]
                if fingerprint == SIGNING_KEY_FINGERPRINT:
                    valid_signer = True
        if result.returncode or not valid_signer:
            raise RuntimeError(
                f"Package signature verification failed for less {release.version}; "
                f"expected signing key {SIGNING_KEY_FINGERPRINT}.\n{result.stderr}"
            )


def build_release(
    client: httpx.Client, release: Release, destination: Path, *, verify: bool = True
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"less-{release.version}-") as directory:
        workspace = Path(directory)
        archive = workspace / "source.tar.gz"
        print(f"Downloading less {release.version}: {release.url}", flush=True)
        with client.stream("GET", release.url) as response:
            response.raise_for_status()
            with archive.open("wb") as output:
                for chunk in response.iter_bytes():
                    output.write(chunk)
        if verify:
            verify_archive(client, release, archive)
        else:
            print("Skipping package signature verification (--no-verify).", flush=True)
        source_root = workspace / "source"
        with tarfile.open(archive, "r:gz") as source:
            source.extractall(source_root, filter="data")
        source_dir = source_root / f"less-{release.version}"
        if not (source_dir / "Makefile.wnm").is_file():
            raise ValueError(f"Source archive does not contain less-{release.version}/Makefile.wnm")
        print(f"Building less {release.version}...", flush=True)
        subprocess.run(["nmake.exe", "/nologo", "/f", "Makefile.wnm"], cwd=source_dir, check=True)
        executable = source_dir / "less.exe"
        if not executable.is_file() or executable.stat().st_size == 0:
            raise RuntimeError("The build did not produce less.exe")
        shutil.copy2(executable, destination)
    print(f"Built less {release.version}: {destination}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?", help="stable version in the current feed (default: latest)")
    parser.add_argument("--discover", action="store_true", help="print release JSON without building")
    parser.add_argument(
        "--no-verify", action="store_true", help="skip package signature verification (GnuPG not required)"
    )
    args = parser.parse_args()
    if args.version is not None and not re.fullmatch(VERSION_PATTERN, args.version):
        parser.error("version must be a stable numeric version such as 710")
    try:
        if not args.discover:
            check_prerequisites(verify=not args.no_verify)
        with httpx.Client(follow_redirects=True, timeout=60) as client:
            response = client.get(FEED_URL)
            response.raise_for_status()
            release = select_release(response.content, args.version)
            if args.discover:
                print(json.dumps(asdict(release)))
            else:
                build_release(client, release, Path.cwd() / "less.exe", verify=not args.no_verify)
    except (httpx.HTTPError, OSError, ValueError, RuntimeError, tarfile.TarError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
