import base64
import logging
from typing import Dict
from src import session

BASE_URL = "https://ws75.aptoide.com/api/7/"

def get_latest_version(app_name: str, config: Dict) -> str:
    package = config['package']
    arch = config.get('arch', 'universal')
    q = _get_q_param(arch)

    # If a specific store_name is configured, use getApp endpoint directly
    store_name = config.get('store_name')
    if store_name:
        url = f"{BASE_URL}getApp?package_name={package}&store_name={store_name}{q}"
        res = session.get(url)
        res.raise_for_status()
        data = res.json()
        app_data = data.get('data', {})
        version = app_data.get('file', {}).get('vername')
        if version:
            logging.info(f"aptoide: found version {version} for {package} (store: {store_name})")
            return version
        raise ValueError(f"aptoide: could not get version for '{package}' from store '{store_name}'")

    url = f"{BASE_URL}apps/search?query={package}&limit=1&trusted=true{q}"
    res = session.get(url)
    res.raise_for_status()
    data = res.json()
    items = data.get('datalist', {}).get('list', [])
    if not items:
        raise ValueError(f"aptoide: no results for package '{package}' (app may not exist on Aptoide)")
    version = items[0]['file']['vername']
    logging.info(f"aptoide: found version {version} for {package}")
    return version

def get_download_link(version: str, app_name: str, config: Dict) -> str:
    package = config['package']
    arch = config.get('arch', 'universal')
    q = _get_q_param(arch)
    store_name = config.get('store_name')

    # If a specific store_name is configured, use getApp endpoint directly
    if store_name:
        url = f"{BASE_URL}getApp?package_name={package}&store_name={store_name}{q}"
        res = session.get(url)
        res.raise_for_status()
        data = res.json()
        path = data.get('data', {}).get('file', {}).get('path')
        if path:
            return path
        raise ValueError(f"aptoide: no download path for '{package}' in store '{store_name}'")

    if version.lower() == "latest":
        url = f"{BASE_URL}apps/search?query={package}&limit=1&trusted=true{q}"
        res = session.get(url)
        res.raise_for_status()
        data = res.json()
        items = data.get('datalist', {}).get('list', [])
        if not items:
            raise ValueError(f"aptoide: no results for package '{package}'")
        return items[0]['file']['path']

    # Find vercode for specific version
    url_versions = f"{BASE_URL}listAppVersions?package_name={package}&limit=50{q}"
    res_v = session.get(url_versions)
    res_v.raise_for_status()
    versions_list = res_v.json().get('datalist', {}).get('list', [])
    vercode = None
    for app in versions_list:
        if app['file']['vername'] == version:
            vercode = app['file']['vercode']
            break
    if not vercode:
        # Version not found in listAppVersions — fall back to search API
        # (some apps report a version in search results but don't expose it
        # in the versions list; in that case grab the download path directly)
        logging.warning(
            f"aptoide: version '{version}' not in listAppVersions for '{package}', "
            f"falling back to search API"
        )
        url_search = f"{BASE_URL}apps/search?query={package}&limit=1&trusted=true{q}"
        res_s = session.get(url_search)
        res_s.raise_for_status()
        items = res_s.json().get('datalist', {}).get('list', [])
        if not items:
            raise ValueError(f"aptoide: version '{version}' not found for package '{package}'")
        path = items[0]['file'].get('path')
        if not path:
            raise ValueError(f"aptoide: no download path for package '{package}'")
        return path

    url_meta = f"{BASE_URL}getAppMeta?package_name={package}&vercode={vercode}{q}"
    res_meta = session.get(url_meta)
    res_meta.raise_for_status()
    return res_meta.json()['data']['file']['path']

def _get_q_param(arch: str) -> str:
    if arch == 'universal':
        return ''
    cpu_map = {
        'arm64-v8a': 'arm64-v8a,armeabi-v7a,armeabi',
        'armeabi-v7a': 'armeabi-v7a,armeabi',
    }
    cpu = cpu_map.get(arch, '')
    if cpu:
        q_str = f"myCPU={cpu}&leanback=0"
        return f"&q={base64.b64encode(q_str.encode('utf-8')).decode('utf-8')}"
    return ''
