#!/bin/bash

# BenPak - Script de désinstallation
# Usage: ./uninstall.sh

set -e

# Choix dynamique du dossier d'installation
if [ -d "$HOME/sgoinfre" ]; then
    INSTALL_DIR="$HOME/sgoinfre/.benpak"
else
    INSTALL_DIR="$HOME/.benpak"
fi
DESKTOP_FILE="$HOME/.local/share/applications/benpak.desktop"

# Couleurs pour le terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Supprimer les fichiers d'installation
remove_files() {
    print_info "Suppression des fichiers BenPak..."
    
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        print_success "Dossier d'installation supprimé: $INSTALL_DIR"
    else
        print_warning "Dossier d'installation non trouvé: $INSTALL_DIR"
    fi
    
    if [ -f "$DESKTOP_FILE" ]; then
        rm -f "$DESKTOP_FILE"
        print_success "Raccourci bureau supprimé"
    else
        print_warning "Raccourci bureau non trouvé"
    fi
}

# Nettoyer le PATH
clean_path() {
    print_info "Nettoyage du PATH..."
    
    # Nettoyer .bashrc
    if [ -f "$HOME/.bashrc" ]; then
        if grep -q "$INSTALL_DIR" "$HOME/.bashrc"; then
            sed -i "\|$INSTALL_DIR|d" "$HOME/.bashrc"
            print_success "Référence supprimée de .bashrc"
        fi
    fi
    
    # Nettoyer .zshrc
    if [ -f "$HOME/.zshrc" ]; then
        if grep -q "$INSTALL_DIR" "$HOME/.zshrc"; then
            sed -i "\|$INSTALL_DIR|d" "$HOME/.zshrc"
            print_success "Référence supprimée de .zshrc"
        fi
    fi
}

# Nettoyer les données utilisateur (optionnel)
clean_user_data() {
    USER_CONFIG_DIR="$HOME/.benpak"
    
    if [ -d "$USER_CONFIG_DIR" ]; then
        read -p "Supprimer aussi les données utilisateur dans $USER_CONFIG_DIR ? (y/N) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$USER_CONFIG_DIR"
            print_success "Données utilisateur supprimées"
        else
            print_info "Données utilisateur conservées"
        fi
    fi
}

# Fonction principale
main() {
    echo "🗑️  Désinstallation de BenPak"
    echo "============================="
    
    # Vérifier si BenPak est installé
    if [ ! -d "$INSTALL_DIR" ] && [ ! -f "$DESKTOP_FILE" ]; then
        print_warning "BenPak ne semble pas être installé"
        exit 0
    fi
    
    print_info "BenPak sera désinstallé de: $INSTALL_DIR"
    
    # Demander confirmation
    read -p "Êtes-vous sûr de vouloir désinstaller BenPak ? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Désinstallation annulée"
        exit 0
    fi
    
    # Processus de désinstallation
    remove_files
    clean_path
    clean_user_data
    
    echo ""
    print_success "🎉 BenPak a été désinstallé avec succès !"
    print_warning "Redémarrez votre terminal pour appliquer les changements du PATH"
    echo ""
}

# Exécuter le script principal
main "$@"
