import json
import logging
from pathlib import Path
from src import (
    utils,
    apkpure,
    session,
    uptodown,
    aptoide,
    apkmirror,
    github
)

def download_resource(url: str, name: str = None, retries: int = 3) -> Path:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            res = session.get(url, stream=True)
            res.raise_for_status()
            break
        except Exception as e:
            last_err = e
            if attempt < retries:
                import time
                wait = attempt * 5
                logging.warning(f"download_resource: attempt {attempt} failed ({e}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise last_err
    final_url = res.url

    if not name:
        name = utils.extract_filename(res, fallback_url=final_url)

    filepath = Path(name)
    total_size = int(res.headers.get('content-length', 0))
    downloaded_size = 0

    with filepath.open("wb") as file:
        for chunk in res.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
                downloaded_size += len(chunk)

    logging.info(
        f"URL: {final_url} [{downloaded_size}/{total_size}] -> \"{filepath}\" [1]"
    )

    return filepath

def download_required(source: str) -> tuple[list[Path], str]:
    source_path = Path("sources") / f"{source}.json"
    with source_path.open() as json_file:
        repos_info = json.load(json_file)

    if isinstance(repos_info, dict) and "bundle_url" in repos_info:
        return download_from_bundle(repos_info)
    
    name = repos_info[0]["name"]
    downloaded_files = []

    for repo_info in repos_info[1:]:
        user = repo_info['user']
        repo = repo_info['repo']
        tag = repo_info['tag']

        release = utils.detect_github_release(user, repo, tag)
        
        if repo == "morphe-patches" or repo == "morphe-cli":
            for asset in release["assets"]:
                if asset["name"].endswith(".asc"):
                    continue
                if asset["name"].endswith(".mpp") or ("morphe-cli" in asset["name"] and asset["name"].endswith(".jar")):
                    filepath = download_resource(asset["browser_download_url"])
                    downloaded_files.append(filepath)
        else:
            for asset in release["assets"]:
                if asset["name"].endswith(".asc"):
                    continue
                filepath = download_resource(asset["browser_download_url"])
                downloaded_files.append(filepath)

    return downloaded_files, name

def download_from_bundle(bundle_info: dict) -> tuple[list[Path], str]:
    bundle_url = bundle_info["bundle_url"]
    name = bundle_info.get("name", "bundle-patches")
    logging.info(f"Downloading bundle from {bundle_url}")
    with session.get(bundle_url) as res:
        res.raise_for_status()
        bundle_data = res.json()
    downloaded_files = []
    if "patches" in bundle_data:
        for patch in bundle_data.get("patches", []):
            if "url" in patch:
                filepath = download_resource(patch["url"])
                downloaded_files.append(filepath)
                logging.info(f"Downloaded patch: {patch.get('name', 'unknown')}")
        for integration in bundle_data.get("integrations", []):
            if "url" in integration:
                filepath = download_resource(integration["url"])
                downloaded_files.append(filepath)
                logging.info(f"Downloaded integration: {integration.get('name', 'unknown')}")
    try:
        cli_release = utils.detect_github_release("revanced", "revanced-cli", "latest")
        for asset in cli_release["assets"]:
            if asset["name"].endswith(".asc"):
                continue
            if asset["name"].endswith(".jar") and "cli" in asset["name"].lower():
                filepath = download_resource(asset["browser_download_url"])
                downloaded_files.append(filepath)
                logging.info("Downloaded ReVanced CLI")
                break
    except Exception as e:
        logging.warning(f"Could not download ReVanced CLI: {e}")
    return downloaded_files, name

def download_platform(app_name: str, platform: str, cli: str, patches: str, arch: str = None) -> tuple[Path | None, str | None]:
    config_path = Path("apps") / platform / f"{app_name}.json"

    # jsonがない = このプラットフォームは未設定なので静かにスキップ
    if not config_path.exists():
        logging.info(f"⏭️  {platform}: no config for {app_name}, skipping")
        return None, None

    try:
        with config_path.open() as json_file:
            config = json.load(json_file)
        
        if arch:
            config['arch'] = arch

        # Support direct_url: skip version resolution and download directly
        direct_url = config.get("direct_url")
        if direct_url:
            logging.info(f"🔗 {platform}: using direct_url for {app_name}")
            try:
                filepath = download_resource(direct_url)
                # Try to resolve version via platform module if possible
                version = config.get("version")
                if not version:
                    try:
                        platform_mod = globals().get(platform)
                        if platform_mod and hasattr(platform_mod, "get_latest_version"):
                            version = platform_mod.get_latest_version(app_name, config)
                    except Exception:
                        pass
                version = version or "latest"
                logging.info(f"✅ {platform}: downloaded {app_name} via direct_url -> {filepath.name}")
                return filepath, version
            except Exception as e:
                logging.error(f"❌ {platform}: direct_url download failed for {app_name}: {type(e).__name__}: {e}")
                return None, None

        version = config.get("version") or utils.get_supported_version(config['package'], cli, patches)
        platform_module = globals()[platform]

        if not version:
            logging.warning(f"⚠️  {platform}: CLI/patch version lookup failed for {app_name}, falling back to get_latest_version")
            try:
                version = platform_module.get_latest_version(app_name, config)
            except Exception as e:
                logging.error(f"❌ {platform}: get_latest_version failed for {app_name}: {type(e).__name__}: {e}")
                return None, None

        if not version:
            logging.error(f"❌ {platform}: could not resolve any version for {app_name}")
            return None, None

        logging.info(f"🔍 {platform}: resolved version {version} for {app_name}")

        try:
            download_link = platform_module.get_download_link(version, app_name, config)
        except Exception as e:
            logging.error(f"❌ {platform}: get_download_link failed for {app_name} v{version}: {type(e).__name__}: {e}")
            return None, None

        if not download_link:
            logging.error(f"❌ {platform}: no download link found for {app_name} v{version}")
            return None, None

        filepath = download_resource(download_link)
        logging.info(f"✅ {platform}: downloaded {app_name} v{version} -> {filepath.name}")
        return filepath, version

    except Exception as e:
        logging.error(f"❌ {platform}: unexpected error for {app_name}: {type(e).__name__}: {e}")
        return None, None

def download_github(app_name: str, cli: str, patches: str, arch: str = None) -> tuple[Path | None, str | None]:
    return download_platform(app_name, "github", cli, patches, arch)

def download_apkmirror(app_name: str, cli: str, patches: str, arch: str = None) -> tuple[Path | None, str | None]:
    return download_platform(app_name, "apkmirror", cli, patches, arch)

def download_apkpure(app_name: str, cli: str, patches: str, arch: str = None) -> tuple[Path | None, str | None]:
    return download_platform(app_name, "apkpure", cli, patches, arch)

def download_aptoide(app_name: str, cli: str, patches: str, arch: str = None) -> tuple[Path | None, str | None]:
    return download_platform(app_name, "aptoide", cli, patches, arch)

def download_uptodown(app_name: str, cli: str, patches: str, arch: str = None) -> tuple[Path | None, str | None]:
    return download_platform(app_name, "uptodown", cli, patches, arch)

def download_apkeditor() -> Path:
    release = utils.detect_github_release("REAndroid", "APKEditor", "latest")
    for asset in release["assets"]:
        if asset["name"].startswith("APKEditor") and asset["name"].endswith(".jar"):
            return download_resource(asset["browser_download_url"])
    raise RuntimeError("APKEditor .jar file not found in the latest release")
