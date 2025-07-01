import re
from typing import Tuple
import requests
from bs4 import BeautifulSoup

def get_gitkraken_info() -> Tuple[str, str]:
    """Get GitKraken latest version and direct download URL (tar.gz) by following redirection or parsing page."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    # Try HEAD first (may redirect)
    url = "https://www.gitkraken.com/download/linux-gzip"
    resp = session.head(url, allow_redirects=True)
    if resp.status_code == 200 and resp.url != url:
        # We have been redirected to the real file
        real_url = resp.url
        version_match = re.search(r'gitkraken-v?(\d+\.\d+\.\d+)', real_url)
        version_str = version_match.group(1) if version_match else "latest"
        return version_str, real_url
    # Fallback: parse the download page
    resp = session.get(url)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        link = soup.find('a', href=re.compile(r'gitkraken.*\.tar\.gz'))
        if link:
            real_url = link['href']
            version_match = re.search(r'gitkraken-v?(\d+\.\d+\.\d+)', real_url)
            version_str = version_match.group(1) if version_match else "latest"
            return version_str, real_url
    return "latest", url
