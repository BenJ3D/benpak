#!/usr/bin/env python3
"""
Test script pour vérifier la détection de version Discord
"""
import sys
import os
sys.path.insert(0, '/home/bducrocq/projets/benpak/src')

from fetcher import PackageFetcher
from package_manager import PackageManager
import json

def test_discord_version():
    print("=== Test de détection de version Discord ===")
    
    # Charger la config Discord
    discord_config_path = "/home/bducrocq/projets/benpak/packages/configs/discord.json"
    with open(discord_config_path, 'r') as f:
        discord_config = json.load(f)
    
    print(f"Discord config: {discord_config}")
    
    # Tester la détection de version
    fetcher = PackageFetcher()
    updated_package = fetcher.update_package_info(discord_config)
    
    print(f"Version détectée: {updated_package.get('latest_version')}")
    print(f"URL réelle: {updated_package.get('real_download_url')}")
    
    # Tester avec PackageManager
    print("\n=== Test avec PackageManager ===")
    pm = PackageManager()
    
    # Vérifier le répertoire d'installation
    print(f"Répertoire d'installation: {pm.install_dir}")
    
    # Vérifier si Discord est installé
    discord_installed = pm.is_package_installed('discord')
    print(f"Discord installé: {discord_installed}")
    
    if discord_installed:
        installed_version = pm.get_installed_version('discord')
        print(f"Version installée: {installed_version}")
        
        # Tester check for updates
        print("\n=== Test de check_for_updates ===")
        updates = pm.check_for_updates()
        print(f"Mises à jour disponibles: {len(updates)}")
        
        for update in updates:
            if update['package']['id'] == 'discord':
                print(f"🔥 Discord UPDATE détecté!")
                print(f"   Installé: {update['installed_version']}")
                print(f"   Disponible: {update['latest_version']}")
                print(f"   Package: {update['package']['name']}")
    else:
        print("Discord n'est pas détecté comme installé")
        
    # Test manuel du fichier .version
    print("\n=== Test manuel du fichier .version ===")
    version_file = pm.install_dir / 'discord' / '.version'
    if version_file.exists():
        content = version_file.read_text().strip()
        print(f"Contenu du fichier .version: '{content}'")
    else:
        print(f"Fichier .version introuvable: {version_file}")

if __name__ == "__main__":
    test_discord_version()
