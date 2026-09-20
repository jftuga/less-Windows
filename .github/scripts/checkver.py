# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.28.1,<1",
#     "packaging>=25,<27",
# ]
# ///

"""Discover the upstream release and set GitHub Actions build/release outputs."""

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


def published_version(client: httpx.Client, repository: str, api_url: str) -> str | None:
    response = client.get(f"{api_url.rstrip('/')}/repos/{repository}/releases/latest")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    tag = response.json().get("tag_name", "")
    match = re.fullmatch(rf"(?:less-v|v)({VERSION_PATTERN})", tag) if isinstance(tag, str) else None
    if not match:
        raise ValueError(f"Unsupported repository release tag: {tag}")
    return match[1]


def build_outputs(
    upstream: dict,
    published: str | None,
    event_name: str,
    ref: str,
    default_branch: str,
    force_build: bool,
) -> dict[str, str]:
    version = upstream.get("version")
    if not isinstance(version, str) or not re.fullmatch(VERSION_PATTERN, version):
        raise ValueError(f"Invalid upstream version: {version}")
    notes_url = upstream.get("notes_url")
    if not isinstance(notes_url, str) or not notes_url or "\n" in notes_url or "\r" in notes_url:
        raise ValueError("Invalid upstream release notes URL")

    newer = published is None or Version(version) > Version(published)
    forced = event_name == "workflow_dispatch" and force_build
    should_build = event_name in {"pull_request", "push"} or forced or newer
    should_release = (
        newer
        and ref == f"refs/heads/{default_branch}"
        and event_name != "pull_request"
        and not forced
    )
    return {
        "version": version,
        "notes_url": notes_url,
        "should_build": str(should_build).lower(),
        "should_release": str(should_release).lower(),
    }


def main() -> int:
    try:
        result = subprocess.run(
            ["uv", "run", "--locked", str(ROOT / "build.py"), "--discover"],
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
            published = published_version(
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
        print(
            f"Upstream: {outputs['version']}; published: {published or 'none'}; "
            f"build: {outputs['should_build']}; release: {outputs['should_release']}"
        )
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            output.writelines(f"{name}={value}\n" for name, value in outputs.items())
    except (httpx.HTTPError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
