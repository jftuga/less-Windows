# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.28.1,<1",
#     "packaging>=25,<27",
# ]
# ///

"""Plan upstream builds, new GitHub releases, and asset-preserving promotions."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import httpx
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[2]
VERSION_PATTERN = r"[0-9]+(?:\.[0-9]+)*"


def published_releases(client: httpx.Client, repository: str, api_url: str) -> list[dict]:
    releases = []
    page = 1
    while True:
        response = client.get(
            f"{api_url.rstrip('/')}/repos/{repository}/releases",
            params={"per_page": 100, "page": page},
        )
        response.raise_for_status()
        batch = response.json()
        if not isinstance(batch, list) or any(not isinstance(item, dict) for item in batch):
            raise ValueError("Invalid GitHub releases response")
        releases.extend(batch)
        if len(batch) < 100:
            return releases
        page += 1


def build_outputs(
    upstream: list[dict],
    published: list[dict],
    event_name: str,
    ref: str,
    default_branch: str,
    force_build: bool,
) -> dict[str, str]:
    if not isinstance(upstream, list) or not upstream:
        raise ValueError("No upstream releases discovered")
    channels = {False: {}, True: {}}
    for release in upstream:
        if not isinstance(release, dict):
            raise ValueError("Invalid upstream release")
        version = release.get("version")
        if not isinstance(version, str) or not re.fullmatch(VERSION_PATTERN, version):
            raise ValueError(f"Invalid upstream version: {version}")
        notes_url = release.get("notes_url")
        if not isinstance(notes_url, str) or not notes_url or "\n" in notes_url or "\r" in notes_url:
            raise ValueError("Invalid upstream release notes URL")
        if type(release.get("beta")) is not bool:
            raise ValueError("Invalid upstream beta flag")
        channels[release["beta"]].setdefault(Version(version), release)
    stable = channels[False]
    if not stable:
        raise ValueError("No upstream production release discovered")
    latest_stable = max(stable)

    existing = {}
    for release in published:
        tag = release.get("tag_name", "")
        match = re.fullmatch(rf"(?:less-v|v)({VERSION_PATTERN})", tag) if isinstance(tag, str) else None
        if not match:
            continue
        if type(release.get("draft")) is not bool or type(release.get("prerelease")) is not bool:
            raise ValueError(f"Invalid GitHub release flags: {tag}")
        existing.setdefault(Version(match[1]), []).append(release)
    published_stable = [
        version
        for version, releases in existing.items()
        if any(not item["draft"] and not item["prerelease"] for item in releases)
    ]
    newest_published = max(published_stable, default=None)

    def metadata(release):
        version = Version(release["version"])
        return {
            "version": release["version"],
            "beta": release["beta"],
            "promote": False,
            "notes_url": release["notes_url"],
            "tag_name": f"less-v{release['version']}",
            "make_latest": str(
                not release["beta"]
                and version == latest_stable
                and (newest_published is None or version >= newest_published)
            ).lower(),
        }

    publish = (
        ref == f"refs/heads/{default_branch}"
        and event_name in {"push", "schedule", "workflow_dispatch"}
        and not force_build
    )
    validate = event_name in {"push", "pull_request"} or force_build
    releases = []
    if publish:
        for version in sorted(stable):
            matches = existing.get(version, [])
            for item in matches:
                if item["draft"] or not item["prerelease"]:
                    continue
                promotion = metadata(stable[version])
                promotion.update(
                    promote=True,
                    tag_name=item["tag_name"],
                    name=(item.get("name") or item["tag_name"]).removesuffix(" beta"),
                )
                releases.append(promotion)

    selected = [stable[latest_stable]]
    if channels[True]:
        latest_beta = max(channels[True])
        if latest_beta > latest_stable:
            selected.append(channels[True][latest_beta])
    builds = []
    for release in selected:
        version = Version(release["version"])
        matches = existing.get(version, [])
        if any(item["draft"] for item in matches):
            continue
        candidate = metadata(release)
        newer = newest_published is None or version > newest_published
        missing = not matches and newer
        if validate or missing:
            builds.append(candidate)
        if publish and missing:
            releases.append(candidate)

    return {
        name: json.dumps(items, separators=(",", ":"))
        for name, items in {
            "builds": builds,
            "releases": releases,
        }.items()
    }


def main() -> int:
    try:
        result = subprocess.run(
            ["uv", "run", "--locked", str(ROOT / "build.py"), "--discover-all"],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        upstream = json.loads(result.stdout)
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        with httpx.Client(
            headers={
                "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=60,
        ) as client:
            published = published_releases(
                client,
                os.environ["GITHUB_REPOSITORY"],
                os.environ.get("GITHUB_API_URL", "https://api.github.com"),
            )
        outputs = build_outputs(
            upstream,
            published,
            os.environ["GITHUB_EVENT_NAME"],
            os.environ["GITHUB_REF"],
            event["repository"]["default_branch"],
            os.environ.get("FORCE_BUILD") == "true",
        )
        for name, value in outputs.items():
            print(f"{name}: {value}")
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            output.writelines(f"{name}={value}\n" for name, value in outputs.items())
    except (httpx.HTTPError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
