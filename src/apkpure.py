import logging

from src import session
from bs4 import BeautifulSoup

# Define a standard browser User-Agent to avoid 403 Forbidden errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://apkpure.net/'
}

# APKPureのリクエストタイムアウト（秒）
# デフォルト無制限だと30秒以上かかる場合があるため短縮
TIMEOUT = 15


def get_latest_version(app_name: str, config: str) -> str:
    url = f"https://apkpure.net/{config['name']}/{config['package']}/versions"

    try:
        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()

        content_size = len(response.content)
        logging.info(f"URL:{response.url} [{content_size}/{content_size}] -> \"-\" [1]")

        soup = BeautifulSoup(response.content, "html.parser")
        version_info = soup.find('div', class_='ver-top-down')

        if version_info and 'data-dt-version' in version_info.attrs:
            return version_info['data-dt-version']

    except Exception as e:
        logging.error(f"Failed to fetch latest version for {app_name}: {e}")

    return None


def get_download_link(version: str, app_name: str, config: str) -> str:
    url = f"https://apkpure.net/{config['name']}/{config['package']}/download/{version}"

    try:
        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()

        content_size = len(response.content)
        logging.info(f"URL:{response.url} [{content_size}/{content_size}] -> \"-\" [1]")

        soup = BeautifulSoup(response.content, "html.parser")

        download_link = soup.find('a', id='download_link')
        if download_link:
            return download_link['href']

    except Exception as e:
        logging.error(f"Failed to fetch download link for {app_name} v{version}: {e}")

    return None
