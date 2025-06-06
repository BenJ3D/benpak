# BenPak - Package Manager for 42 School

Un gestionnaire de paquets avec interface graphique moderne pour faciliter l'installation de logiciels sur les sessions de l'école 42 (sans droits root).

## Fonctionnalités

- 🎮 **Interface graphique moderne** avec thème sombre
- 📦 **Installation simplifiée** de logiciels populaires (Discord, VSCode, Postman, etc.)
- 🔄 **Mise à jour automatique** - détecte les dernières versions disponibles
- 🚀 **Sans droits root** - installation dans ~/Programs
- 📱 **Raccourcis desktop** créés automatiquement
- ⚡ **Installation en arrière-plan** avec barre de progression

## Packages supportés par défaut

- **Discord** - Chat vocal et textuel pour gamers
- **Visual Studio Code** - Éditeur de code Microsoft
- **Postman** - Environnement de développement d'API
- **OBS Studio** - Logiciel de streaming et enregistrement

## Installation rapide

```bash
# Cloner le projet
git clone <repo-url> benpak
cd benpak

# Installation et lancement
make setup
make run
```

## Utilisation

### Via Makefile (recommandé)

```bash
# Configuration initiale
make setup              # Créer venv et installer dépendances

# Développement
make run               # Lancer l'application (avec venv)
make dev               # Mode développement avec auto-restart

# Build et déploiement
make build             # Créer l'exécutable standalone
make install           # Installer l'app dans ~/Programs
make clean             # Nettoyer les fichiers de build

# Autres commandes utiles
make run-system        # Lancer sans venv (Python système)
make install-deps      # Installer deps système (sans venv)
make help              # Afficher l'aide
```

### Installation système

```bash
# Pour installer l'app dans votre système
make install

# L'application sera disponible :
# - Exécutable : ~/Programs/benpak/benpak
# - Menu applications : BenPak
# - Raccourci desktop automatique
```

## Architecture du projet

```
benpak/
├── Makefile                    # Commandes de build et déploiement
├── requirements.txt            # Dépendances Python
├── src/
│   ├── main.py                # Point d'entrée principal
│   ├── package_manager.py     # Logique métier (download, install, etc.)
│   └── gui/
│       ├── __init__.py
│       └── main_window.py     # Interface graphique principale
├── packages/
│   └── configs/               # Configurations des packages custom
│       └── obs-studio.json    # Exemple de config package
├── build/                     # Fichiers de build temporaires
└── dist/                      # Exécutables générés
```

## Ajouter des packages personnalisés

Créez un fichier JSON dans `packages/configs/` :

```json
{
    "name": "Mon Application",
    "id": "mon-app",
    "description": "Description de l'application",
    "type": "tar.gz",
    "url_pattern": "https://example.com/download/latest.tar.gz",
    "extract_method": "tar_gz",
    "icon": "🚀",
    "executable": "mon-app"
}
```

### Méthodes d'extraction supportées

- `tar_gz` : Archives tar.gz (comme Discord)
- `deb` : Packages Debian (comme VSCode)
- `appimage` : AppImages (comme OBS Studio)

## Fonctionnement technique

### Installation des packages

1. **Téléchargement** : Récupération depuis l'URL officielle
2. **Extraction** : 
   - `tar.gz` → `tar -xzf package.tar.gz -C ~/Programs/app/`
   - `deb` → `dpkg-deb -x package.deb ~/Programs/app/`
3. **Configuration** : Création des raccourcis desktop
4. **Versioning** : Suivi des versions installées

### Interface utilisateur

- **PyQt5** pour l'interface graphique moderne
- **Threading** pour les installations non-bloquantes
- **Thème sombre** optimisé pour les développeurs
- **Responsive design** avec widgets personnalisés

## Dépendances

- Python 3.7+
- PyQt5 (interface graphique)
- requests (téléchargements HTTP)
- packaging (gestion des versions)
- beautifulsoup4 (parsing HTML si nécessaire)

## Développement

### Structure du code

- `main.py` : Configuration de l'app et thème UI
- `package_manager.py` : Cœur métier (téléchargement, installation)
- `gui/main_window.py` : Interface utilisateur et interactions

### Ajout de nouvelles fonctionnalités

1. **Nouveau type de package** : Modifier `extract_package()` dans `package_manager.py`
2. **Nouvelle source** : Étendre `get_available_packages()`
3. **UI améliorée** : Modifier `main_window.py`

## Troubleshooting

### Erreurs communes

```bash
# Permission denied
chmod +x ~/Programs/benpak/benpak

# Dépendances manquantes
make setup

# PyQt5 non trouvé
sudo apt install python3-pyqt5

# Interface ne s'affiche pas
export DISPLAY=:0  # Si en SSH
```

### Logs et debug

Les erreurs sont affichées dans la console et via des dialogues PyQt5.

## Licence

Projet éducatif pour l'école 42. Libre d'utilisation et modification.