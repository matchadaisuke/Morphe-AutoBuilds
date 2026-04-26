import base64
import logging
from typing import Dict
from src import session

BASE_URL = "https://ws75.aptoide.com/api/7/"

def get_latest_version(app_name: str, config: Dict) -> str:
    package = config['package']
    arch = config.get('arch', 'universal')
    q = _get_q_param(arch)
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
        raise ValueError(f"aptoide: version '{version}' not found for package '{package}'")

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
