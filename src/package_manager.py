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
import sys

from fetcher import PackageFetcher
import sys


class PackageManager:
    def __init__(self, install_dir: str = None):
        """Initialize package manager with installation directory"""
        self.config = Config()
        self.fetcher = PackageFetcher()
        
        install_path = install_dir or self.config.get("install_directory")
        self.install_dir = Path(install_path)
        self.install_dir.mkdir(exist_ok=True)
        
        # Chemin vers les packages JSON : priorité aux fichiers locaux, puis développement
        # 1. Cherche d'abord dans ~/Programs/benpak/packages/configs (après installation)
        local_packages_dir = Path.home() / "Programs" / "benpak" / "packages" / "configs"
        # 2. Puis dans le dossier de développement
        dev_packages_dir = Path(__file__).parent.parent / "packages" / "configs"
        
        if local_packages_dir.exists():
            self.packages_config_dir = local_packages_dir
        else:
            self.packages_config_dir = dev_packages_dir
        
    def get_available_packages(self) -> List[Dict]:
        """Get list of available packages from config files"""
        packages = []
        
        # Load packages from JSON configuration files
        if self.packages_config_dir.exists():
            for config_file in self.packages_config_dir.glob("*.json"):
                try:
                    with open(config_file, 'r') as f:
                        package_config = json.load(f)
                        updated_package = self.fetcher.update_package_info(package_config)
                        packages.append(updated_package)
                except Exception as e:
                    print(f"Error loading package config {config_file}: {e}")
        else:
            print(f"Warning: Package config directory not found: {self.packages_config_dir}")
        
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
        """Download package to temporary directory, using real filename if possible and checking file type."""
        import re
        url = package["url_pattern"]
        temp_dir = tempfile.mkdtemp()
        filename = f"{package['id']}.{package['type'].split('.')[-1]}"
        temp_file = os.path.join(temp_dir, filename)
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            # Try to get filename from Content-Disposition
            content_disp = response.headers.get('content-disposition')
            if content_disp:
                fname_match = re.search(r'filename="?([^";]+)"?', content_disp)
                if fname_match:
                    real_filename = fname_match.group(1)
                    temp_file = os.path.join(temp_dir, real_filename)
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
            # Vérification du type de fichier téléchargé (pour tar.gz)
            if package["extract_method"] == "tar_gz":
                import subprocess
                try:
                    file_output = subprocess.check_output(["file", temp_file], text=True)
                    if "gzip compressed data" not in file_output and "tar archive" not in file_output:
                        raise Exception(f"Downloaded file is not a valid tar.gz archive: {file_output}")
                except Exception as e:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    raise Exception(f"Failed to verify archive for {package['name']}: {str(e)}")
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
                
            elif package["extract_method"] == "tar_bz2":
                # Extract tar.bz2 file
                subprocess.run([
                    "tar", "-xjf", file_path, "-C", str(package_dir), "--strip-components=1"
                ], check=True)
                
            elif package["extract_method"] == "tar_xz":
                # Extract tar.xz file
                subprocess.run([
                    "tar", "-xJf", file_path, "-C", str(package_dir), "--strip-components=1"
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
                version_str = package.get('latest_version', 'unknown')
                # Pour les paquets .deb, extraire la version réelle du fichier deb
                if package["extract_method"] == "deb":
                    try:
                        deb_version = subprocess.check_output([
                            "dpkg-deb", "-f", file_path, "Version"
                        ], text=True).strip()
                        if deb_version:
                            version_str = deb_version
                    except Exception as e:
                        print(f"[WARN] Impossible d'extraire la version du .deb: {e}")
                # fallback si version inconnue
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
    
    def uninstall_package(self, package_id: str, force_kill: bool = False) -> bool:
        """Uninstall a package, with option to kill running processes"""
        package_dir = self.install_dir / package_id
        
        if not package_dir.exists():
            return False
        
        try:
            # Check if the application is running
            running_processes = self._find_running_processes(package_id)
            
            if running_processes and not force_kill:
                # Application is running, ask user what to do
                print(f"\n⚠️  {package_id} is currently running:")
                for proc in running_processes:
                    print(f"   - PID {proc['pid']}: {proc['name']} ({proc['exe']})")
                
                choice = input("\nChoose an action:\n1. Kill the application and continue uninstall\n2. Cancel uninstall\nChoice (1/2): ").strip()
                
                if choice == "1":
                    if self._kill_application_processes(running_processes):
                        print("✅ Application processes terminated successfully")
                        # Wait a moment for processes to fully terminate
                        import time
                        time.sleep(2)
                    else:
                        print("❌ Failed to terminate some processes")
                        return False
                elif choice == "2":
                    print("Uninstall cancelled by user")
                    return False
                else:
                    print("Invalid choice, cancelling uninstall")
                    return False
            
            elif running_processes and force_kill:
                # Force kill without asking
                print(f"🔄 Force killing {package_id} processes...")
                self._kill_application_processes(running_processes)
                import time
                time.sleep(2)
            
            # Proceed with uninstallation
            # Remove PATH symlink
            self.remove_path_symlink(package_id)
            
            # Remove desktop shortcut
            desktop_file = Path.home() / ".local" / "share" / "applications" / f"{package_id}-BP.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
            
            # Also check for old format desktop shortcut
            old_desktop_file = Path.home() / ".local" / "share" / "applications" / f"{package_id}.desktop"
            if old_desktop_file.exists():
                old_desktop_file.unlink()
            
            # Remove package directory
            shutil.rmtree(package_dir)
            print(f"✅ {package_id} uninstalled successfully")
            return True
            
        except PermissionError as e:
            # Check again for running processes if we get permission error
            running_processes = self._find_running_processes(package_id)
            if running_processes:
                print(f"\n❌ Permission denied - {package_id} is still running:")
                for proc in running_processes:
                    print(f"   - PID {proc['pid']}: {proc['name']}")
                print("Please close the application manually and try again, or use force_kill=True")
            raise Exception(f"Permission denied while uninstalling {package_id}: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to uninstall {package_id}: {str(e)}")
    
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
        """Add executable directory to PATH directly in shell config"""
        try:
            package_dir = self.install_dir / package["id"]
            
            # Find executable
            executable_name = package.get("executable", package["id"])
            executable_path = None
            
            # Si bin_path est défini dans le package, on l'utilise en priorité pour le PATH
            bin_path = package.get("bin_path")
            if bin_path:
                bin_path_obj = package_dir / bin_path
                executable_name = package.get("executable", package["id"])
                
                # Détecter si bin_path pointe vers un fichier (se termine par le nom de l'exécutable)
                if bin_path.endswith(executable_name):
                    # bin_path pointe vers le fichier exécutable
                    executable_dir = bin_path_obj.parent
                    executable_path = bin_path_obj
                else:
                    # bin_path pointe vers un dossier
                    executable_dir = bin_path_obj
                    # Chercher l'exécutable dans le dossier bin_path
                    potential_exec = executable_dir / executable_name
                    if potential_exec.exists() and os.access(potential_exec, os.X_OK):
                        executable_path = potential_exec
                
                # Ajouter au PATH même si le dossier n'existe pas encore
                if self.config.get("auto_configure_path", True):
                    self._add_app_to_path(package["id"], str(executable_dir))
                    print(f"Added {package['name']} to PATH: {executable_dir}")
                
                # Si bin_path est défini, on considère que c'est suffisant
                # même si l'exécutable n'existe pas encore
                return True
            
            # Priority search paths for common executable locations
            priority_paths = [
                "bin/",
                "usr/bin/", 
                "usr/share/*/bin/",
                "opt/*/bin/",
                ""  # root directory as last resort
            ]
            
            candidates = []  # Store all potential executables
            
            for priority_path in priority_paths:
                search_pattern = str(package_dir / priority_path) if priority_path else str(package_dir)
                
                for root, dirs, files in os.walk(search_pattern):
                    for file in files:
                        if (file.lower() == executable_name.lower() or 
                            file.lower().startswith(executable_name.lower())):
                            file_path = Path(root) / file
                            
                            # Skip .desktop files and other non-executable formats
                            if (file_path.suffix.lower() in ['.desktop', '.txt', '.md', '.log'] or
                                not os.access(file_path, os.X_OK)):
                                continue
                            
                            # Calculate priority score
                            score = 0
                            if file.lower() == executable_name.lower():
                                score += 100  # Exact match gets highest priority
                            if "bin" in root:
                                score += 50   # Files in bin directories get priority
                            if not any(suffix in file.lower() for suffix in ['-tunnel', '-cli', '-helper']):
                                score += 25   # Main executables over helper tools
                            
                            candidates.append((score, file_path))
            
            # Choose the best candidate
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                executable_path = candidates[0][1]
                print(f"Selected executable: {executable_path} (score: {candidates[0][0]})")
            
            if not executable_path:
                print(f"Warning: Could not find executable for {package['name']}")
                return False
            
            # Add executable directory to PATH in shell configs (if enabled)
            if self.config.get("auto_configure_path", True):
                executable_dir = executable_path.parent
                self._add_app_to_path(package["id"], str(executable_dir))
            
            return True
            
        except Exception as e:
            print(f"Failed to add to PATH: {str(e)}")
            return False

    def remove_path_symlink(self, package_id: str) -> bool:
        """Remove application path from PATH when uninstalling"""
        try:
            return self._remove_app_from_path(package_id)
        except Exception as e:
            print(f"Failed to remove from PATH: {str(e)}")
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

    def _ensure_local_bin_in_path(self):
        """Ensure ~/.local/bin is in PATH by updating appropriate shell config files"""
        try:
            bin_dir = Path.home() / ".local" / "bin"
            bin_path_export = f'export PATH="$HOME/.local/bin:$PATH"'
            
            # Detect current shell and appropriate config files
            shell_configs = self._detect_shell_configs()
            
            if not shell_configs:
                print("Warning: Could not detect shell configuration files")
                return False
            
            # Check if already in PATH
            try:
                current_path = os.environ.get('PATH', '')
                if str(bin_dir) in current_path:
                    return True
            except:
                pass
            
            # Add to each detected shell config
            updated_files = []
            for config_file, shell_name in shell_configs:
                if self._add_path_to_shell_config(config_file, bin_path_export, shell_name):
                    updated_files.append((config_file, shell_name))
            
            if updated_files:
                print(f"Added ~/.local/bin to PATH in:")
                for config_file, shell_name in updated_files:
                    print(f"  - {config_file} ({shell_name})")
                print("Please restart your terminal or run 'source <config_file>' to apply changes")
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to update PATH: {str(e)}")
            return False
    
    def _detect_shell_configs(self) -> List[Tuple[Path, str]]:
        """Detect which shell configuration files to update based on current shell and available files"""
        shell_configs = []
        home = Path.home()
        
        # Detect current shell from environment
        current_shell = self._get_current_shell()
        
        # Priority order based on current shell
        if current_shell == "zsh":
            potential_configs = [
                (home / ".zshrc", "zsh"),
                (home / ".zprofile", "zsh"),
                (home / ".profile", "general")
            ]
        elif current_shell == "bash":
            potential_configs = [
                (home / ".bashrc", "bash"),
                (home / ".bash_profile", "bash"),
                (home / ".profile", "general")
            ]
        elif current_shell == "fish":
            fish_config_dir = home / ".config" / "fish"
            potential_configs = [
                (fish_config_dir / "config.fish", "fish"),
                (home / ".profile", "general")
            ]
        else:
            # Fallback: try common configs
            potential_configs = [
                (home / ".bashrc", "bash"),
                (home / ".zshrc", "zsh"),
                (home / ".profile", "general")
            ]
        
        # Check which files exist and are writable
        for config_file, shell_name in potential_configs:
            if config_file.exists() and os.access(config_file, os.W_OK):
                shell_configs.append((config_file, shell_name))
            elif shell_name == current_shell and config_file.parent.exists():
                # Create the config file if it doesn't exist for current shell
                try:
                    config_file.touch()
                    shell_configs.append((config_file, shell_name))
                except:
                    pass
        
        return shell_configs
    
    def _get_current_shell(self) -> str:
        """Detect the currently used shell"""
        # Check user preference first
        preferred_shell = self.config.get("preferred_shell", "auto")
        if preferred_shell != "auto" and preferred_shell in ['bash', 'zsh', 'fish']:
            return preferred_shell
        
        # Method 1: Check environment variables
        if os.environ.get('ZSH_VERSION'):
            return "zsh"
        elif os.environ.get('BASH_VERSION'):
            return "bash"
        
        # Method 2: Check SHELL environment variable
        shell_path = os.environ.get('SHELL', '')
        if shell_path:
            shell_name = os.path.basename(shell_path)
            if shell_name in ['zsh', 'bash', 'fish', 'sh']:
                return shell_name
        
        # Method 3: Check parent process (fallback)
        try:
            import psutil
            parent = psutil.Process().parent()
            if parent:
                parent_name = parent.name()
                if parent_name in ['zsh', 'bash', 'fish']:
                    return parent_name
        except:
            pass
        
        # Method 4: Try to detect from /etc/passwd (ultimate fallback)
        try:
            import pwd
            user_shell = pwd.getpwuid(os.getuid()).pw_shell
            shell_name = os.path.basename(user_shell)
            if shell_name in ['zsh', 'bash', 'fish', 'sh']:
                return shell_name
        except:
            pass
        
        # Default fallback
        return "bash"
    
    def _add_path_to_shell_config(self, config_file: Path, path_export: str, shell_name: str) -> bool:
        """Add PATH export to a specific shell configuration file"""
        try:
            # Read current content
            content = ""
            if config_file.exists():
                content = config_file.read_text()
            
            # Check if PATH export already exists
            if "~/.local/bin" in content or "$HOME/.local/bin" in content:
                return False  # Already configured
            
            # Prepare the export line based on shell type
            if shell_name == "fish":
                export_line = 'set -gx PATH $HOME/.local/bin $PATH'
                comment = "# Added by BenPak for command line access"
            else:
                export_line = path_export
                comment = "# Added by BenPak for command line access"
            
            # Add the export to the file
            if content and not content.endswith('\n'):
                content += '\n'
            
            content += f'\n{comment}\n{export_line}\n'
            
            # Write back to file
            config_file.write_text(content)
            return True
            
        except Exception as e:
            print(f"Failed to update {config_file}: {str(e)}")
            return False
    
    def get_shell_info(self) -> Dict[str, any]:
        """Get information about current shell configuration"""
        current_shell = self._get_current_shell()
        shell_configs = self._detect_shell_configs()
        
        return {
            "current_shell": current_shell,
            "detected_configs": [(str(path), shell) for path, shell in shell_configs],
            "auto_configure_enabled": self.config.get("auto_configure_path", True),
            "preferred_shell": self.config.get("preferred_shell", "auto")
        }
    
    def set_shell_preference(self, shell: str, auto_configure: bool = None):
        """Set user shell preference and auto-configure option"""
        if shell in ["auto", "bash", "zsh", "fish"]:
            self.config.set("preferred_shell", shell)
        
        if auto_configure is not None:
            self.config.set("auto_configure_path", auto_configure)
    
    def manually_configure_path(self) -> bool:
        """Manually configure PATH regardless of auto_configure setting"""
        return self._ensure_local_bin_in_path()

    def _add_app_to_path(self, package_id: str, executable_dir: str) -> bool:
        """Add application executable directory to PATH in shell configuration files"""
        try:
            # Detect current shell and appropriate config files
            shell_configs = self._detect_shell_configs()
            
            if not shell_configs:
                print("Warning: Could not detect shell configuration files")
                return False
            
            # Check if already in PATH
            try:
                current_path = os.environ.get('PATH', '')
                if executable_dir in current_path:
                    return True
            except:
                pass
            
            # Add to each detected shell config
            updated_files = []
            for config_file, shell_name in shell_configs:
                if self._add_app_path_to_shell_config(config_file, package_id, executable_dir, shell_name):
                    updated_files.append((config_file, shell_name))
            
            if updated_files:
                print(f"Added {package_id} to PATH in:")
                for config_file, shell_name in updated_files:
                    print(f"  - {config_file} ({shell_name})")
                print("Please restart your terminal or run 'source <config_file>' to apply changes")
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to add {package_id} to PATH: {str(e)}")
            return False
    
    def _remove_app_from_path(self, package_id: str) -> bool:
        """Remove application paths from shell configuration files"""
        try:
            # Detect current shell and appropriate config files
            shell_configs = self._detect_shell_configs()
            
            if not shell_configs:
                print("Warning: Could not detect shell configuration files")
                return False
            
            # Remove from each detected shell config
            updated_files = []
            for config_file, shell_name in shell_configs:
                if self._remove_app_path_from_shell_config(config_file, package_id):
                    updated_files.append((config_file, shell_name))
            
            if updated_files:
                print(f"Removed {package_id} from PATH in:")
                for config_file, shell_name in updated_files:
                    print(f"  - {config_file} ({shell_name})")
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to remove {package_id} from PATH: {str(e)}")
            return False
    
    def _add_app_path_to_shell_config(self, config_file: Path, package_id: str, executable_dir: str, shell_name: str) -> bool:
        """Add application PATH export to a specific shell configuration file"""
        try:
            # Read current content
            content = ""
            if config_file.exists():
                content = config_file.read_text()
            
            # Check if this app's PATH export already exists
            benpak_marker = f"# BenPak - {package_id}"
            if benpak_marker in content:
                return False  # Already configured
            
            # Préférer le ~ pour le home dans l'export PATH
            from pathlib import Path as _Path
            home = str(_Path.home())
            # Use absolute path instead of ~ to avoid expansion issues
            exec_dir_display = executable_dir
            # Prepare the export line based on shell type
            if shell_name == "fish":
                export_line = f'set -gx PATH "{exec_dir_display}" $PATH'
                comment = f"# BenPak - {package_id}"
            else:
                export_line = f'export PATH="{exec_dir_display}:$PATH"'
                comment = f"# BenPak - {package_id}"
            
            # Add the export to the file
            if content and not content.endswith('\n'):
                content += '\n'
            
            content += f'\n{comment}\n{export_line}\n'
            
            # Write back to file
            config_file.write_text(content)
            return True
            
        except Exception as e:
            print(f"Failed to update {config_file}: {str(e)}")
            return False
    
    def _remove_app_path_from_shell_config(self, config_file: Path, package_id: str) -> bool:
        """Remove application PATH export from a specific shell configuration file"""
        try:
            if not config_file.exists():
                return False
            
            content = config_file.read_text()
            lines = content.split('\n')
            new_lines = []
            skip_next = False
            
            for line in lines:
                # Skip the comment line and the next export line for this package
                if f"# BenPak - {package_id}" in line:
                    skip_next = True
                    continue
                elif skip_next and ("export PATH=" in line or "set -gx PATH" in line):
                    skip_next = False
                    continue
                else:
                    new_lines.append(line)
            
            # Write back to file if something was removed
            new_content = '\n'.join(new_lines)
            if new_content != content:
                config_file.write_text(new_content)
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to remove from {config_file}: {str(e)}")
            return False
    
    def _find_running_processes(self, package_id: str) -> List[Dict]:
        """Find running processes related to the package (robuste, multi-cas)"""
        import psutil
        running_processes = []
        package_dir = str(self.install_dir / package_id)
        package_dir_real = os.path.realpath(package_dir)
        exe_names = set()

        # Collect all executable file names in the package dir
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.access(file_path, os.X_OK) and not file_path.endswith(('.desktop', '.txt', '.md', '.log')):
                    exe_names.add(os.path.basename(file_path).lower())

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                info = proc.info
                # 1. Check if process executable path is in our package dir (realpath)
                exe_path = info.get('exe') or ''
                if exe_path:
                    exe_path_real = os.path.realpath(exe_path)
                    if package_dir in exe_path_real or package_dir_real in exe_path_real:
                        running_processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'exe': exe_path,
                            'process': proc
                        })
                        continue
                # 2. Check if process name matches any executable in the package
                if info['name'] and info['name'].lower() in exe_names:
                    running_processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'exe': exe_path,
                        'process': proc
                    })
                    continue
                # 3. Check if command line contains the package dir
                cmdline = info.get('cmdline') or []
                if any(package_dir in arg or package_dir_real in arg for arg in cmdline):
                    running_processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'exe': exe_path,
                        'process': proc
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue
        return running_processes
    
    def _kill_application_processes(self, processes: List[Dict]) -> bool:
        """Kill the specified processes"""
        success = True
        
        for proc_info in processes:
            try:
                if proc_info['process']:
                    # Use psutil if available
                    proc = proc_info['process']
                    print(f"🔄 Terminating {proc_info['name']} (PID: {proc_info['pid']})...")
                    
                    # Try graceful termination first
                    proc.terminate()
                    
                    # Wait for process to terminate
                    try:
                        proc.wait(timeout=5)
                        print(f"✅ {proc_info['name']} terminated gracefully")
                    except:
                        # Force kill if graceful termination fails
                        print(f"🔧 Force killing {proc_info['name']}...")
                        proc.kill()
                        proc.wait(timeout=2)
                        print(f"✅ {proc_info['name']} force killed")
                else:
                    # Fallback to kill command
                    print(f"🔄 Killing process {proc_info['pid']}...")
                    subprocess.run(['kill', str(proc_info['pid'])], check=True)
                    print(f"✅ Process {proc_info['pid']} killed")
                    
            except Exception as e:
                print(f"❌ Failed to kill {proc_info['name']} (PID: {proc_info['pid']}): {str(e)}")
                success = False
        
        return success
    
    def uninstall_package_interactive(self, package_id: str) -> bool:
        """Interactive uninstall with GUI-like prompts"""
        try:
            return self.uninstall_package(package_id, force_kill=False)
        except Exception as e:
            if "Permission denied" in str(e) or "running" in str(e).lower():
                print(f"\n❌ Uninstall failed: {str(e)}")
                return False
            raise e
    
    def uninstall_package_force(self, package_id: str) -> bool:
        """Force uninstall by killing processes without asking"""
        try:
            return self.uninstall_package(package_id, force_kill=True)
        except Exception as e:
            print(f"❌ Force uninstall failed: {str(e)}")
            return False
    
    def launch_package(self, package_id: str) -> bool:
        """Launch an installed package"""
        try:
            # Get package info
            packages = self.get_available_packages()
            package = None
            for pkg in packages:
                if pkg["id"] == package_id:
                    package = pkg
                    break
            
            if not package:
                print(f"❌ Package {package_id} not found")
                return False
            
            if not self.is_package_installed(package_id):
                print(f"❌ Package {package_id} is not installed")
                return False
            
            # Find the executable
            install_path = self.install_dir / package_id
            executable_name = package.get("executable", package_id)
            
            # Si bin_path est défini, on commence la recherche par ce chemin
            bin_path = package.get("bin_path")
            possible_paths = []
            if bin_path:
                possible_paths.append(install_path / bin_path / executable_name)
            possible_paths.extend([
                install_path / executable_name,
                install_path / "bin" / executable_name,
                install_path / f"{executable_name}.AppImage",
                install_path / f"{package_id}.AppImage",
            ])
            
            # For specific packages, use known paths
            if package_id == "vscode":
                possible_paths.extend([
                    install_path / "bin" / "code",
                    install_path / "code",
                    # Ne jamais inclure /usr/bin/code pour VSCode BenPak !
                ])
            elif package_id == "discord":
                possible_paths.extend([
                    install_path / "Discord",
                    install_path / "discord",
                ])
            
            executable_path = None
            for path in possible_paths:
                if path.exists() and path.is_file():
                    # Check if it's executable
                    if os.access(path, os.X_OK):
                        executable_path = path
                        break
            
            if not executable_path:
                print(f"❌ Executable not found for {package_id}")
                print(f"   Searched in: {[str(p) for p in possible_paths]}")
                return False
            
            # Launch the application in the background
            print(f"🚀 Launching {package['name']} from {executable_path}")
            subprocess.Popen([str(executable_path)], 
                           cwd=str(install_path),
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to launch {package_id}: {str(e)}")
            return False
