"""
Configuration manager for BenPak
Handles user preferences and app settings
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    def __init__(self):
        # Determine base directory based on 42 School context
        if (Path.home() / "sgoinfre").exists():
            # 42 School session - use sgoinfre
            self.base_dir = Path.home() / "sgoinfre" / ".benpak"
            default_install_dir = str(Path.home() / "sgoinfre" / ".benpak" / "programs")
        else:
            # Local environment
            self.base_dir = Path.home() / ".benpak"
            default_install_dir = str(Path.home() / ".benpak" / "programs")
        
        # Create base directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_dir = self.base_dir
        self.config_file = self.config_dir / "config.json"
        self.packages_cache_file = self.config_dir / "packages_cache.json"
        
        # Default configuration
        self.default_config = {
            "install_directory": default_install_dir,
            "create_desktop_shortcuts": True,
            "create_path_symlinks": True,
            "auto_configure_path": True,  # Automatically add ~/.local/bin to PATH
            "preferred_shell": "auto",    # auto, bash, zsh, fish
            "auto_refresh_interval": 30,
            "theme": "dark",
            "download_timeout": 30,
            "max_concurrent_downloads": 3,
            "check_updates_on_startup": True,
            "window_geometry": {
                "width": 900,
                "height": 600,
                "x": 100,
                "y": 100
            }
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for any missing keys
                    return {**self.default_config, **config}
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return self.default_config.copy()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
    
    def load_packages_cache(self) -> Dict[str, Any]:
        """Load cached package information"""
        if self.packages_cache_file.exists():
            try:
                with open(self.packages_cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def save_packages_cache(self, cache_data: Dict[str, Any]):
        """Save package cache information"""
        try:
            with open(self.packages_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Error saving packages cache: {e}")
