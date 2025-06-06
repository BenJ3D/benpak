#!/bin/bash

# BenPak - Installation automatique
# Usage: curl -fsSL https://yoursite.com/install.sh | bash

set -e

# Choix dynamique du dossier d'installation
if [ -d "$HOME/sgoinfre" ]; then
    INSTALL_DIR="$HOME/sgoinfre/.benpak"
else
    INSTALL_DIR="$HOME/.benpak"
fi
BINARY_NAME="benpak"
DESKTOP_FILE="$HOME/.local/share/applications/benpak.desktop"

# Couleurs pour le terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
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

# Vérifier l'architecture
check_architecture() {
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            ARCH_SUFFIX="x64"
            ;;
        aarch64|arm64)
            ARCH_SUFFIX="arm64"
            ;;
        *)
            print_error "Architecture non supportée: $ARCH"
            exit 1
            ;;
    esac
}

# Détecter la distribution Linux
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    else
        print_warning "Impossible de détecter la distribution"
        DISTRO="unknown"
    fi
}

# Installer les dépendances
install_dependencies() {
    print_info "Installation des dépendances..."
    
    case $DISTRO in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y wget curl
            ;;
        fedora)
            sudo dnf install -y wget curl
            ;;
        arch)
            sudo pacman -S --noconfirm wget curl
            ;;
        *)
            print_warning "Distribution non reconnue, vérifiez que wget et curl sont installés"
            ;;
    esac
}

# Télécharger BenPak
download_benpak() {
    print_info "Téléchargement de BenPak..."
    
    # URL de téléchargement (à adapter selon votre hébergement)
    DOWNLOAD_URL="https://github.com/votre-compte/benpak/releases/latest/download/benpak-linux-${ARCH_SUFFIX}.tar.gz"
    
    # Créer le dossier temporaire
    TMP_DIR=$(mktemp -d)
    cd "$TMP_DIR"
    
    # Télécharger l'archive
    if ! wget -q "$DOWNLOAD_URL" -O benpak.tar.gz; then
        print_error "Échec du téléchargement depuis $DOWNLOAD_URL"
        exit 1
    fi
    
    # Extraire l'archive
    print_info "Extraction de l'archive..."
    tar -xzf benpak.tar.gz
}

# Installer BenPak
install_benpak() {
    print_info "Installation de BenPak dans $INSTALL_DIR..."
    
    # Créer le dossier d'installation
    mkdir -p "$INSTALL_DIR"
    
    # Copier l'exécutable
    if [ -f "benpak-distribution/benpak" ]; then
        cp "benpak-distribution/benpak" "$INSTALL_DIR/"
        chmod +x "$INSTALL_DIR/benpak"
    else
        print_error "Fichier benpak introuvable dans l'archive"
        exit 1
    fi
    
    # Copier la documentation
    if [ -f "benpak-distribution/README.txt" ]; then
        cp "benpak-distribution/README.txt" "$INSTALL_DIR/"
    fi
}

# Créer le raccourci bureau
create_desktop_shortcut() {
    print_info "Création du raccourci bureau..."
    
    # Créer le dossier applications s'il n'existe pas
    mkdir -p "$(dirname "$DESKTOP_FILE")"
    
    # Créer le fichier .desktop
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=BenPak
Comment=Package Manager for 42 School
GenericName=Package Manager
Exec=$INSTALL_DIR/benpak
Icon=package-manager
Terminal=false
Type=Application
Categories=System;PackageManager;
StartupNotify=true
EOF
    
    chmod +x "$DESKTOP_FILE"
}

# Ajouter au PATH (optionnel)
add_to_path() {
    print_info "Ajout de BenPak au PATH..."
    
    # Vérifier si déjà dans le PATH
    if echo "$PATH" | grep -q "$INSTALL_DIR"; then
        print_info "BenPak est déjà dans le PATH"
        return
    fi
    
    # Ajouter au .bashrc ou .zshrc
    SHELL_RC=""
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    fi
    
    if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
        echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_RC"
        print_info "Ajouté au PATH dans $SHELL_RC"
        print_warning "Redémarrez votre terminal ou exécutez: source $SHELL_RC"
    fi
}

# Nettoyer les fichiers temporaires
cleanup() {
    if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
}

# Vérifier l'installation
verify_installation() {
    print_info "Vérification de l'installation..."
    
    if [ -x "$INSTALL_DIR/benpak" ]; then
        print_success "BenPak installé avec succès !"
        print_info "Exécutable: $INSTALL_DIR/benpak"
        
        # Tester l'exécution
        if "$INSTALL_DIR/benpak" --version >/dev/null 2>&1; then
            print_success "BenPak fonctionne correctement"
        else
            print_warning "L'exécutable ne semble pas fonctionner correctement"
        fi
    else
        print_error "Échec de l'installation"
        exit 1
    fi
}

# Afficher les instructions finales
show_final_instructions() {
    echo ""
    print_success "🎉 Installation terminée !"
    echo ""
    echo "📍 BenPak est installé dans: $INSTALL_DIR"
    echo "🚀 Pour lancer BenPak:"
    echo "   • Depuis le menu des applications"
    echo "   • Ou en ligne de commande: $INSTALL_DIR/benpak"
    echo ""
    echo "📚 Documentation: $INSTALL_DIR/README.txt"
    echo ""
    echo "🔧 Pour désinstaller: rm -rf $INSTALL_DIR"
    echo ""
}

# Fonction principale
main() {
    echo "🚀 Installation de BenPak - Package Manager for 42 School"
    echo "========================================================="
    
    # Vérifications préliminaires
    check_architecture
    detect_distro
    
    print_info "Architecture: $ARCH ($ARCH_SUFFIX)"
    print_info "Distribution: $DISTRO"
    
    # Demander confirmation
    echo ""
    read -p "Continuer l'installation ? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation annulée"
        exit 0
    fi
    
    # Processus d'installation
    trap cleanup EXIT
    
    install_dependencies
    download_benpak
    install_benpak
    create_desktop_shortcut
    add_to_path
    verify_installation
    show_final_instructions
}

# Exécuter le script principal
main "$@"
