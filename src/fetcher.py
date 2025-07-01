"""
Package fetcher - Handles version detection and download URL resolution
"""

import re
import requests
from bs4 import BeautifulSoup
from packaging import version
from typing import Dict, Optional, Tuple
import json


class PackageFetcher:
    def get_gitkraken_info(self) -> Tuple[str, str]:
        """Get GitKraken latest version and direct download URL (tar.gz) by following redirection or parsing page."""
        import re
        import requests
        from bs4 import BeautifulSoup
        session = self.session
        url = "https://www.gitkraken.com/download/linux-gzip"
        # Try HEAD first (may redirect)
        resp = session.head(url, allow_redirects=True)
        if resp.status_code == 200 and resp.url != url:
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
    """Fetches latest versions and download URLs for packages"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_discord_info(self) -> Tuple[str, str]:
        """Get Discord latest version and download URL"""
        try:
            # Discord provides a direct download link that redirects to latest
            url = "https://discord.com/api/download?platform=linux&format=tar.gz"
            
            # Get redirect URL to extract version
            response = self.session.head(url, allow_redirects=False)
            if response.status_code == 302:
                redirect_url = response.headers.get('Location', '')
                # Extract version from URL like: discord-0.0.XX.tar.gz
                version_match = re.search(r'discord-(\d+\.\d+\.\d+)\.tar\.gz', redirect_url)
                if version_match:
                    return version_match.group(1), url
            
            return "latest", url
            
        except Exception as e:
            print(f"Error fetching Discord info: {e}")
            return "unknown", "https://discord.com/api/download?platform=linux&format=tar.gz"
    
    def get_vscode_info(self) -> Tuple[str, str]:
        """Get VSCode latest version and download URL"""
        try:
            # VSCode API endpoint for latest stable
            api_url = "https://update.code.visualstudio.com/api/update/linux-deb-x64/stable/latest"
            response = self.session.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                version_str = data.get('name', 'latest')
                download_url = data.get('url', 'https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64')
                return version_str, download_url
            
            return "latest", "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64"
            
        except Exception as e:
            print(f"Error fetching VSCode info: {e}")
            return "unknown", "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64"
    
    def get_postman_info(self) -> Tuple[str, str]:
        """Get Postman latest version and download URL"""
        try:
            # Postman download page
            url = "https://www.postman.com/downloads/"
            response = self.session.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for Linux download link
                linux_link = soup.find('a', href=re.compile(r'linux64.*\.tar\.gz'))
                if linux_link:
                    download_url = linux_link.get('href')
                    # Try to extract version from the URL or page
                    version_match = re.search(r'(\d+\.\d+\.\d+)', download_url)
                    version_str = version_match.group(1) if version_match else "latest"
                    return version_str, download_url
            
            # Fallback to direct download
            return "latest", "https://dl.pstmn.io/download/latest/linux64"
            
        except Exception as e:
            print(f"Error fetching Postman info: {e}")
            return "unknown", "https://dl.pstmn.io/download/latest/linux64"
    
    def get_obs_info(self) -> Tuple[str, str]:
        """Get OBS Studio latest version from GitHub"""
        try:
            # GitHub API for latest release
            api_url = "https://api.github.com/repos/obsproject/obs-studio/releases/latest"
            response = self.session.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                version_str = data.get('tag_name', 'latest').lstrip('v')
                
                # Find AppImage asset
                assets = data.get('assets', [])
                for asset in assets:
                    if 'AppImage' in asset['name'] and 'x86_64' in asset['name']:
                        return version_str, asset['browser_download_url']
            
            return "latest", "https://github.com/obsproject/obs-studio/releases/latest/download/OBS-Studio-x86_64.AppImage"
            
        except Exception as e:
            print(f"Error fetching OBS info: {e}")
            return "unknown", "https://github.com/obsproject/obs-studio/releases/latest/download/OBS-Studio-x86_64.AppImage"
    
    def get_chrome_info(self) -> Tuple[str, str]:
        """Get Chrome latest version and download URL"""
        try:
            # Chrome has a stable direct download URL
            url = "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
            
            # Try to get version from Chrome API
            api_url = "https://versionhistory.googleapis.com/v1/chrome/platforms/linux/channels/stable/versions"
            response = self.session.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                versions = data.get('versions', [])
                if versions:
                    version_str = versions[0].get('version', 'latest')
                    return version_str, url
            
            return "latest", url
            
        except Exception as e:
            print(f"Error fetching Chrome info: {e}")
            return "unknown", "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    
    def get_telegram_info(self) -> Tuple[str, str]:
        """Get Telegram latest version and download URL"""
        try:
            # Telegram download page
            url = "https://telegram.org/dl/desktop/linux"
            response = self.session.get(url, allow_redirects=True)
            
            if response.status_code == 200:
                # Extract version from redirect URL if available
                final_url = response.url
                version_match = re.search(r'(\d+\.\d+\.\d+)', final_url)
                if version_match:
                    return version_match.group(1), url
            
            return "latest", url
            
        except Exception as e:
            print(f"Error fetching Telegram info: {e}")
            return "unknown", "https://telegram.org/dl/desktop/linux"
    
    def get_spotify_info(self) -> Tuple[str, str]:
        """Get Spotify latest version and download URL"""
        try:
            # Spotify repository page
            response = self.session.get("http://repository.spotify.com/pool/non-free/s/spotify-client/")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find latest .deb package
                deb_links = soup.find_all('a', href=re.compile(r'spotify-client.*\.deb$'))
                if deb_links:
                    latest_link = deb_links[-1]  # Usually the last one is latest
                    href = latest_link.get('href')
                    version_match = re.search(r'spotify-client_(\d+\.\d+\.\d+\.\d+)', href)
                    version_str = version_match.group(1) if version_match else "latest"
                    download_url = f"http://repository.spotify.com/pool/non-free/s/spotify-client/{href}"
                    return version_str, download_url
            
            return "latest", "http://repository.spotify.com/pool/non-free/s/spotify-client/spotify-client_1.2.25.1011.g0348b4b2_amd64.deb"
            
        except Exception as e:
            print(f"Error fetching Spotify info: {e}")
            return "unknown", "http://repository.spotify.com/pool/non-free/s/spotify-client/spotify-client_1.2.25.1011.g0348b4b2_amd64.deb"
    
    def get_vlc_info(self) -> Tuple[str, str]:
        """Get VLC latest version and download URL"""
        try:
            # VLC download page
            response = self.session.get("https://www.videolan.org/vlc/download-linux.html")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for AppImage download link
                appimage_link = soup.find('a', href=re.compile(r'.*\.AppImage$'))
                if appimage_link:
                    download_url = appimage_link.get('href')
                    version_match = re.search(r'vlc-(\d+\.\d+\.\d+)', download_url)
                    version_str = version_match.group(1) if version_match else "latest"
                    return version_str, download_url
            
            return "latest", "https://download.videolan.org/pub/videolan/vlc/last/vlc-3.0.20-x86_64.AppImage"
            
        except Exception as e:
            print(f"Error fetching VLC info: {e}")
            return "unknown", "https://download.videolan.org/pub/videolan/vlc/last/vlc-3.0.20-x86_64.AppImage"
    
    def get_blender_info(self) -> Tuple[str, str]:
        """Get Blender latest version and download URL"""
        try:
            # Blender download page
            response = self.session.get("https://www.blender.org/download/")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for Linux download link
                linux_link = soup.find('a', href=re.compile(r'.*linux.*\.tar\.xz$'))
                if linux_link:
                    download_url = linux_link.get('href')
                    version_match = re.search(r'blender-(\d+\.\d+\.\d+)', download_url)
                    version_str = version_match.group(1) if version_match else "latest"
                    return version_str, download_url
            
            return "latest", "https://download.blender.org/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz"
            
        except Exception as e:
            print(f"Error fetching Blender info: {e}")
            return "unknown", "https://download.blender.org/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz"
    
    def get_jetbrains_toolbox_info(self) -> Tuple[str, str]:
        """Get JetBrains Toolbox latest version and download URL"""
        try:
            # JetBrains Toolbox download page
            response = self.session.get("https://www.jetbrains.com/toolbox-app/")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for download link
                download_link = soup.find('a', href=re.compile(r'.*toolbox.*\.tar\.gz$'))
                if download_link:
                    download_url = download_link.get('href')
                    version_match = re.search(r'toolbox-(\d+\.\d+\.\d+)', download_url)
                    version_str = version_match.group(1) if version_match else "latest"
                    return version_str, download_url
            
            return "latest", "https://download.jetbrains.com/toolbox/jetbrains-toolbox-2.2.2.20062.tar.gz"
            
        except Exception as e:
            print(f"Error fetching JetBrains Toolbox info: {e}")
            return "unknown", "https://download.jetbrains.com/toolbox/jetbrains-toolbox-2.2.2.20062.tar.gz"

    def get_github_release_info(self, repo: str) -> Tuple[str, str]:
        """Generic GitHub release fetcher"""
        try:
            api_url = f"https://api.github.com/repos/{repo}/releases/latest"
            response = self.session.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                version_str = data.get('tag_name', 'latest').lstrip('v')
                
                # Get first asset URL as download
                assets = data.get('assets', [])
                if assets:
                    return version_str, assets[0]['browser_download_url']
            
            return "latest", f"https://github.com/{repo}/releases/latest"
            
        except Exception as e:
            print(f"Error fetching {repo} info: {e}")
            return "unknown", f"https://github.com/{repo}/releases/latest"
    
    def update_package_info(self, package: Dict) -> Dict:
        """Update package with latest version info"""
        package_id = package.get('id', '')
        
        # Get version and URL based on package type
        if package_id == 'discord':
            version_str, url = self.get_discord_info()
        elif package_id == 'vscode':
            version_str, url = self.get_vscode_info()
        elif package_id == 'postman':
            version_str, url = self.get_postman_info()
        elif package_id == 'obs-studio':
            version_str, url = self.get_obs_info()
        elif package_id == 'chrome':
            version_str, url = self.get_chrome_info()
        elif package_id == 'telegram':
            version_str, url = self.get_telegram_info()
        elif package_id == 'spotify':
            version_str, url = self.get_spotify_info()
        elif package_id == 'vlc':
            version_str, url = self.get_vlc_info()
        elif package_id == 'blender':
            version_str, url = self.get_blender_info()
        elif package_id == 'jetbrains_toolbox':
            version_str, url = self.get_jetbrains_toolbox_info()
        elif package_id == 'gitkraken':
            version_str, url = self.get_gitkraken_info()
        elif 'github_repo' in package:
            version_str, url = self.get_github_release_info(package['github_repo'])
        else:
            # Use existing URL and try to detect version
            version_str = package.get('version', 'latest')
            url = package.get('url_pattern', '')
        
        # Update package info
        updated_package = package.copy()
        updated_package['latest_version'] = version_str
        updated_package['url_pattern'] = url
        
        return updated_package
    
    def check_for_updates(self, installed_packages: Dict[str, str]) -> Dict[str, bool]:
        """Check which packages have updates available"""
        updates = {}
        
        for package_id, installed_version in installed_packages.items():
            if installed_version == "unknown":
                updates[package_id] = True
                continue
                
            try:
                # Get latest version for package
                if package_id == 'discord':
                    latest_version, _ = self.get_discord_info()
                elif package_id == 'vscode':
                    latest_version, _ = self.get_vscode_info()
                elif package_id == 'postman':
                    latest_version, _ = self.get_postman_info()
                elif package_id == 'obs-studio':
                    latest_version, _ = self.get_obs_info()
                elif package_id == 'chrome':
                    latest_version, _ = self.get_chrome_info()
                elif package_id == 'telegram':
                    latest_version, _ = self.get_telegram_info()
                elif package_id == 'spotify':
                    latest_version, _ = self.get_spotify_info()
                elif package_id == 'vlc':
                    latest_version, _ = self.get_vlc_info()
                elif package_id == 'blender':
                    latest_version, _ = self.get_blender_info()
                elif package_id == 'jetbrains_toolbox':
                    latest_version, _ = self.get_jetbrains_toolbox_info()
                else:
                    continue
                
                if latest_version != "latest" and latest_version != "unknown":
                    try:
                        updates[package_id] = version.parse(latest_version) > version.parse(installed_version)
                    except:
                        updates[package_id] = latest_version != installed_version
                else:
                    updates[package_id] = False
                    
            except Exception as e:
                print(f"Error checking updates for {package_id}: {e}")
                updates[package_id] = False
        
        return updates
