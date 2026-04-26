"""
GitHub Releases downloader for APKs.

Config format (apps/github/{app_name}.json):
{
    "user": "AdguardTeam",
    "repo": "AdguardForAndroid",
    "asset_pattern": "adguard-release-v{version}.apk",
    "package": "com.adguard.android",
    "version": ""
}

asset_pattern supports:
  - "{version}"  → replaced with the resolved version string
  - "*"          → matches any single segment (glob-style, matched in order)
  - Literal filename suffix matching (e.g. ".apk")

If version is empty, the latest release tag is used and the first matching
.apk asset is downloaded.
"""

import fnmatch
import logging
import re
from typing import Dict, Optional

from src import utils


def _resolve_release(config: Dict) -> tuple[dict, str]:
    """Return (release_raw_data, version_string)."""
    user = config["user"]
    repo = config["repo"]
    tag = config.get("tag", "latest")
    release = utils.detect_github_release(user, repo, tag)
    # Extract clean version from tag (strip leading 'v')
    tag_name = release.get("tag_name", "")
    version = re.sub(r"^v", "", tag_name)
    return release, version


def get_latest_version(app_name: str, config: Dict) -> Optional[str]:
    # direct_url configs have no user/repo — return the pinned version if set,
    # otherwise return None so the caller falls through to the next platform.
    if "direct_url" in config:
        version = config.get("version") or None
        if version:
            logging.info(f"github: direct_url version for {app_name} is {version}")
        else:
            logging.info(f"github: direct_url config for {app_name} has no version, skipping")
        return version
    try:
        _, version = _resolve_release(config)
        logging.info(f"github: latest version for {app_name} is {version}")
        return version
    except Exception as e:
        logging.error(f"github: failed to resolve version for {app_name}: {e}")
        return None


def get_download_link(version: str, app_name: str, config: Dict) -> Optional[str]:
    try:
        release, _ = _resolve_release(config)
        assets = release.get("assets", [])

        asset_pattern = config.get("asset_pattern", "*.apk")
        asset_exclude = config.get("asset_exclude", "")
        # Replace {version} placeholder
        pattern = asset_pattern.replace("{version}", version)

        def _is_excluded(name: str) -> bool:
            return bool(asset_exclude and asset_exclude in name)

        # Try exact pattern match first (fnmatch)
        for asset in assets:
            name = asset["name"]
            if fnmatch.fnmatch(name, pattern) and not _is_excluded(name):
                logging.info(f"github: matched asset '{name}' for {app_name} v{version}")
                return asset["browser_download_url"]

        # Fallback: just pick the first .apk asset (still respecting exclusions)
        for asset in assets:
            name = asset["name"]
            if name.endswith(".apk") and not _is_excluded(name):
                logging.info(
                    f"github: pattern '{pattern}' did not match; "
                    f"falling back to first .apk: {name}"
                )
                return asset["browser_download_url"]

        logging.error(f"github: no .apk asset found in release for {app_name}")
        return None

    except Exception as e:
        logging.error(f"github: failed to get download link for {app_name}: {e}")
        return None
