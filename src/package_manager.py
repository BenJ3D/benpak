"""
Package Manager - Core functionality for downloading and installing packages
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from packaging import version
import json
from config import Config
from fetcher import PackageFetcher


class PackageManager:
    def __init__(self, install_dir: str = None):
        """Initialize package manager with installation directory"""
        self.config = Config()
        self.fetcher = PackageFetcher()
        
        install_path = install_dir or self.config.get("install_directory")
        self.install_dir = Path(install_path)
        self.install_dir.mkdir(exist_ok=True)
        self.packages_config_dir = Path(__file__).parent.parent / "packages" / "configs"
        
    def get_available_packages(self) -> List[Dict]:
        """Get list of available packages from config files"""
        packages = []
        
        # Built-in packages
        builtin_packages = [
            {
                "name": "Discord",
                "id": "discord",
                "description": "Voice and text chat for gamers",
                "type": "tar.gz",
                "url_pattern": "https://discord.com/api/download?platform=linux&format=tar.gz",
                "extract_method": "tar_gz",
                "icon": "🎮",
                "executable": "Discord"
            },
            {
                "name": "Visual Studio Code",
                "id": "vscode",
                "description": "Code editor redefined and optimized for building modern applications",
                "type": "deb",
                "url_pattern": "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64",
                "extract_method": "deb",
                "icon": "💻",
                "executable": "code"
            },
            {
                "name": "Postman",
                "id": "postman",
                "description": "API development environment",
                "type": "tar.gz",
                "url_pattern": "https://dl.pstmn.io/download/latest/linux64",
                "extract_method": "tar_gz",
                "icon": "📮",
                "executable": "Postman"
            }
        ]
        
        # Update packages with latest version info
        for package in builtin_packages:
            updated_package = self.fetcher.update_package_info(package)
            packages.append(updated_package)
        
        # Load custom packages from config files
        if self.packages_config_dir.exists():
            for config_file in self.packages_config_dir.glob("*.json"):
                try:
                    with open(config_file, 'r') as f:
                        package_config = json.load(f)
                        updated_package = self.fetcher.update_package_info(package_config)
                        packages.append(updated_package)
                except Exception as e:
                    print(f"Error loading package config {config_file}: {e}")
        
        return packages
    
    def is_package_installed(self, package_id: str) -> bool:
        """Check if a package is already installed"""
        package_dir = self.install_dir / package_id
        return package_dir.exists() and any(package_dir.iterdir())
    
    def get_installed_version(self, package_id: str) -> Optional[str]:
        """Get version of installed package if available"""
        version_file = self.install_dir / package_id / ".version"
        if version_file.exists():
            try:
                return version_file.read_text().strip()
            except:
                pass
        return None
    
    def download_package(self, package: Dict, progress_callback=None) -> str:
        """Download package to temporary directory"""
        url = package["url_pattern"]
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        filename = f"{package['id']}.{package['type'].split('.')[-1]}"
        temp_file = os.path.join(temp_dir, filename)
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            progress_callback(progress)
            
            return temp_file
            
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Failed to download {package['name']}: {str(e)}")
    
    def extract_package(self, package: Dict, file_path: str, progress_callback=None) -> bool:
        """Extract package to installation directory"""
        package_dir = self.install_dir / package["id"]
        
        try:
            # Remove existing installation
            if package_dir.exists():
                shutil.rmtree(package_dir)
            
            package_dir.mkdir(parents=True, exist_ok=True)
            
            if progress_callback:
                progress_callback(10)
            
            if package["extract_method"] == "tar_gz":
                # Extract tar.gz file
                subprocess.run([
                    "tar", "-xzf", file_path, "-C", str(package_dir), "--strip-components=1"
                ], check=True)
                
            elif package["extract_method"] == "deb":
                # Extract deb file using dpkg-deb
                subprocess.run([
                    "dpkg-deb", "-x", file_path, str(package_dir)
                ], check=True)
                
            elif package["extract_method"] == "appimage":
                # Handle AppImage - just copy and make executable
                appimage_name = f"{package['id']}.AppImage"
                target_path = package_dir / appimage_name
                shutil.copy2(file_path, target_path)
                os.chmod(target_path, 0o755)
                
                # Create a wrapper script for easier execution
                wrapper_script = package_dir / package.get("executable", package["id"])
                wrapper_content = f"""#!/bin/bash
cd "{package_dir}"
exec ./{appimage_name} "$@"
"""
                wrapper_script.write_text(wrapper_content)
                os.chmod(wrapper_script, 0o755)
                
            if progress_callback:
                progress_callback(90)
            
            # Create version file
            version_file = package_dir / ".version"
            try:
                # Use latest_version if available, otherwise try to extract from filename
                version_str = package.get('latest_version', 'unknown')
                if version_str in ['latest', 'unknown']:
                    import re
                    from datetime import datetime
                    
                    version_match = re.search(r'(\d+\.\d+\.\d+)', os.path.basename(file_path))
                    if version_match:
                        version_str = version_match.group(1)
                    else:
                        version_str = datetime.now().strftime("%Y.%m.%d")
                
                version_file.write_text(version_str)
            except:
                pass
            
            if progress_callback:
                progress_callback(100)
            
            return True
            
        except Exception as e:
            # Clean up on failure
            if package_dir.exists():
                shutil.rmtree(package_dir, ignore_errors=True)
            raise Exception(f"Failed to extract {package['name']}: {str(e)}")
    
    def install_package(self, package: Dict, progress_callback=None) -> bool:
        """Download and install a package, then create desktop shortcut"""
        try:
            if progress_callback:
                progress_callback(0, "Downloading...")

            # Download package
            file_path = self.download_package(package, 
                lambda p: progress_callback(p * 0.7) if progress_callback else None)

            if progress_callback:
                progress_callback(70, "Extracting...")

            # Extract package
            success = self.extract_package(package, file_path,
                lambda p: progress_callback(70 + p * 0.3) if progress_callback else None)

            # Clean up temporary file
            os.unlink(file_path)
            os.rmdir(os.path.dirname(file_path))

            # Create desktop shortcut if enabled in config
            if self.config.get("create_desktop_shortcuts", True):
                self.create_desktop_shortcut(package)
            
            # Create PATH symlink if enabled in config  
            if self.config.get("create_path_symlinks", True):
                self.create_path_symlink(package)

            if progress_callback:
                progress_callback(100, "Completed!")

            return success

        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            raise e
    
    def uninstall_package(self, package_id: str) -> bool:
        """Uninstall a package"""
        package_dir = self.install_dir / package_id
        
        if package_dir.exists():
            try:
                # Remove PATH symlink
                self.remove_path_symlink(package_id)
                
                # Remove desktop shortcut
                desktop_file = Path.home() / ".local" / "share" / "applications" / f"{package_id}.desktop"
                if desktop_file.exists():
                    desktop_file.unlink()
                
                # Remove package directory
                shutil.rmtree(package_dir)
                return True
            except Exception as e:
                raise Exception(f"Failed to uninstall package: {str(e)}")
        
        return False
    
    def create_desktop_shortcut(self, package: Dict) -> bool:
        """Create desktop shortcut for installed package, with icon discovery"""
        try:
            desktop_dir = Path.home() / ".local" / "share" / "applications"
            desktop_dir.mkdir(parents=True, exist_ok=True)

            package_dir = self.install_dir / package["id"]

            # Find executable
            executable_name = package.get("executable", package["id"])
            executable_path = None
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    if file.lower() == executable_name.lower() or file.lower().startswith(executable_name.lower()):
                        file_path = Path(root) / file
                        if os.access(file_path, os.X_OK):
                            executable_path = file_path
                            break
                if executable_path:
                    break
            if not executable_path:
                return False

            # Try to find an icon in the package directory
            icon_path = None
            icon_candidates = [
                f"{package['id']}.png", "icon.png", "Icon.png", "logo.png", "Icon.svg", "icon.svg"
            ]
            for candidate in icon_candidates:
                candidate_path = package_dir / candidate
                if candidate_path.exists():
                    icon_path = str(candidate_path)
                    break
            # If not found, try to find any .png or .svg in the package dir
            if not icon_path:
                for file in package_dir.glob("*.png"):
                    icon_path = str(file)
                    break
            if not icon_path:
                for file in package_dir.glob("*.svg"):
                    icon_path = str(file)
                    break
            # Fallback: use the icon field (emoji or name)
            if not icon_path:
                icon_path = package.get('icon', 'application-default-icon')

            # Ajout du suffixe -BP pour le nom du raccourci et de l'icône
            desktop_file = desktop_dir / f"{package['id']}-BP.desktop"
            display_name = f"{package['name']}-BP"
            # Si c'est une icône locale, on la copie avec le suffixe -BP
            if icon_path and os.path.isfile(icon_path):
                icon_ext = os.path.splitext(icon_path)[1]
                icon_target = desktop_dir / f"{package['id']}-BP{icon_ext}"
                shutil.copy2(icon_path, icon_target)
                icon_path = str(icon_target)

            desktop_content = f"""[Desktop Entry]
Name={display_name}
Comment={package.get('description', '')}
Exec={executable_path}
Icon={icon_path}
Terminal=false
Type=Application
Categories=Development;
"""
            desktop_file.write_text(desktop_content)
            os.chmod(desktop_file, 0o755)
            return True
        except Exception as e:
            print(f"Failed to create desktop shortcut: {str(e)}")
            return False

    def create_path_symlink(self, package: Dict) -> bool:
        """Create symlink in ~/.local/bin for command line access"""
        try:
            bin_dir = Path.home() / ".local" / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            
            package_dir = self.install_dir / package["id"]
            
            # Find executable
            executable_name = package.get("executable", package["id"])
            executable_path = None
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    if file.lower() == executable_name.lower() or file.lower().startswith(executable_name.lower()):
                        file_path = Path(root) / file
                        if os.access(file_path, os.X_OK):
                            executable_path = file_path
                            break
                if executable_path:
                    break
            
            if not executable_path:
                return False
            
            # Ajout du suffixe -bp pour le symlink
            symlink_name = f"{package.get('executable', package['id']).lower()}-bp"
            symlink_path = bin_dir / symlink_name
            
            # Remove existing symlink if it exists
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()
            
            # Create new symlink
            symlink_path.symlink_to(executable_path)
            
            # Ensure ~/.local/bin is in PATH by updating shell configs
            self._ensure_local_bin_in_path()
            
            return True
            
        except Exception as e:
            print(f"Failed to create PATH symlink: {str(e)}")
            return False

    def remove_path_symlink(self, package_id: str) -> bool:
        """Remove symlink from ~/.local/bin when uninstalling"""
        try:
            bin_dir = Path.home() / ".local" / "bin"
            
            # Remove symlink with -bp suffix
            for symlink in bin_dir.glob(f"*-bp"):
                if symlink.is_symlink() and package_id.lower() in symlink.name:
                    symlink.unlink()
                    return True
            
            # Also try direct package name
            potential_symlink = bin_dir / f"{package_id.lower()}-bp"
            if potential_symlink.exists() or potential_symlink.is_symlink():
                potential_symlink.unlink()
                return True
                
            return False
            
        except Exception as e:
            print(f"Failed to remove PATH symlink: {str(e)}")
            return False

    def check_for_updates(self) -> List[Dict]:
        """Check for available updates for installed packages"""
        available_updates = []
        
        try:
            # Get all available packages with latest versions
            all_packages = self.get_available_packages()
            
            for package in all_packages:
                if self.is_package_installed(package["id"]):
                    installed_version = self.get_installed_version(package["id"])
                    latest_version = package.get("version")
                    
                    if installed_version and latest_version and installed_version != latest_version:
                        available_updates.append({
                            "package": package,
                            "installed_version": installed_version,
                            "latest_version": latest_version
                        })
        
        except Exception as e:
            print(f"Error checking for updates: {e}")
        
        return available_updates
    
    def get_installed_packages(self) -> List[Dict]:
        """Get list of all installed packages with their info"""
        installed_packages = []
        
        if not self.install_dir.exists():
            return installed_packages
        
        try:
            available_packages = self.get_available_packages()
            available_by_id = {pkg["id"]: pkg for pkg in available_packages}
            
            for package_dir in self.install_dir.iterdir():
                if package_dir.is_dir() and any(package_dir.iterdir()):
                    package_id = package_dir.name
                    version = self.get_installed_version(package_id)
                    
                    # Get package info from available packages
                    package_info = available_by_id.get(package_id, {
                        "id": package_id,
                        "name": package_id.title(),
                        "description": "Locally installed package",
                        "icon": "📦"
                    })
                    
                    installed_packages.append({
                        **package_info,
                        "installed_version": version,
                        "install_date": package_dir.stat().st_mtime
                    })
        
        except Exception as e:
            print(f"Error getting installed packages: {e}")
        
        return installed_packages
