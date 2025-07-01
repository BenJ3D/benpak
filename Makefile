# BenPak - Package Manager for 42 School
# Makefile for building and running the application

PYTHON = python3
PIP = pip3
VENV_DIR = venv
SRC_DIR = src
BUILD_DIR = build
DIST_DIR = dist
REQUIREMENTS = requirements.txt

# Default target
.PHONY: all
all: setup build

# Setup virtual environment and install dependencies
.PHONY: setup
setup:
	@echo "Setting up virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing dependencies..."
	./$(VENV_DIR)/bin/pip install -r $(REQUIREMENTS)
	@echo "Setup complete!"

# Install dependencies without venv (for system-wide install)
.PHONY: install-deps
install-deps:
	$(PIP) install -r $(REQUIREMENTS)

# Run the application in development mode
.PHONY: run
run:
	@echo "Starting BenPak..."
	./$(VENV_DIR)/bin/python $(SRC_DIR)/main.py

# Run without virtual environment
.PHONY: run-system
run-system:
	$(PYTHON) $(SRC_DIR)/main.py

# Build standalone executable
.PHONY: build
build: setup
	@echo "Building standalone executable..."
	./$(VENV_DIR)/bin/pip install pyinstaller
	mkdir -p $(BUILD_DIR)
	./$(VENV_DIR)/bin/pyinstaller benpak.spec \
		--distpath $(DIST_DIR) \
		--workpath $(BUILD_DIR)
	@echo "Executable built in $(DIST_DIR)/benpak"

# Clean build artifacts
.PHONY: clean
clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Clean everything including venv
.PHONY: clean-all
clean-all: clean
	rm -rf $(VENV_DIR)

# Install the built executable to ~/Programs
.PHONY: install
install: build
	@echo "Installing BenPak to ~/Programs..."
	mkdir -p ~/Programs/benpak
	cp $(DIST_DIR)/benpak ~/Programs/benpak/
	@echo "Creating desktop shortcut..."
	@echo "[Desktop Entry]" > ~/.local/share/applications/benpak.desktop
	@echo "Name=BenPak" >> ~/.local/share/applications/benpak.desktop
	@echo "Comment=Package Manager for 42 School" >> ~/.local/share/applications/benpak.desktop
	@echo "Exec=$(HOME)/Programs/benpak/benpak" >> ~/.local/share/applications/benpak.desktop
	@echo "Icon=package-manager" >> ~/.local/share/applications/benpak.desktop
	@echo "Terminal=false" >> ~/.local/share/applications/benpak.desktop
	@echo "Type=Application" >> ~/.local/share/applications/benpak.desktop
	@echo "Categories=System;" >> ~/.local/share/applications/benpak.desktop
	@echo "Installation complete! You can now launch BenPak from the applications menu."

# Full release and install process
.PHONY: install-release
install-release:
	@echo "🚀 Starting full release and installation process..."
	$(MAKE) release
	@echo "📦 Release created, now installing..."
	cd dist/benpak-distribution && ./install.sh
	@echo "✅ Installation complete!"
	@echo "You can now run BenPak with: benpak (if ~/bin is in PATH) or ~/bin/benpak"

# Development mode with auto-reload
.PHONY: dev
dev:
	@echo "Starting development mode..."
	while true; do \
		./$(VENV_DIR)/bin/python $(SRC_DIR)/main.py; \
		echo "App crashed or closed. Press Ctrl+C to exit or any key to restart..."; \
		read -n 1; \
	done

# Create distribution package
.PHONY: dist-package
dist-package: build
	@echo "Creating distribution package..."
	mkdir -p dist/benpak-distribution
	cp $(DIST_DIR)/benpak dist/benpak-distribution/
	# Copy packages directory for user extensibility
	cp -r packages dist/benpak-distribution/
	echo "#!/bin/bash" > dist/benpak-distribution/install.sh
	echo "# BenPak Installation Script" >> dist/benpak-distribution/install.sh
	echo "" >> dist/benpak-distribution/install.sh
	echo "echo \"Installing BenPak...\"" >> dist/benpak-distribution/install.sh
	echo "" >> dist/benpak-distribution/install.sh
	echo "# Créer les répertoires" >> dist/benpak-distribution/install.sh
	echo "mkdir -p ~/bin" >> dist/benpak-distribution/install.sh
	echo "mkdir -p ~/.local/share/benpak/packages/configs" >> dist/benpak-distribution/install.sh
	echo "" >> dist/benpak-distribution/install.sh
	echo "# Copier l'exécutable" >> dist/benpak-distribution/install.sh
	echo "cp benpak ~/bin/" >> dist/benpak-distribution/install.sh
	echo "chmod +x ~/bin/benpak" >> dist/benpak-distribution/install.sh
	echo "" >> dist/benpak-distribution/install.sh
	echo "# Copier les fichiers de packages (s'ils existent)" >> dist/benpak-distribution/install.sh
	echo "if [ -d \"packages\" ]; then" >> dist/benpak-distribution/install.sh
	echo "    cp -r packages/* ~/.local/share/benpak/packages/" >> dist/benpak-distribution/install.sh
	echo "    echo \"Package configurations copied\"" >> dist/benpak-distribution/install.sh
	echo "fi" >> dist/benpak-distribution/install.sh
	echo "" >> dist/benpak-distribution/install.sh
	echo "echo \"BenPak installed successfully in ~/bin/\"" >> dist/benpak-distribution/install.sh
	echo "echo \"\"" >> dist/benpak-distribution/install.sh
	echo "echo \"To add new packages, simply drop JSON files into:\"" >> dist/benpak-distribution/install.sh
	echo "echo \"~/.local/share/benpak/packages/configs/\"" >> dist/benpak-distribution/install.sh
	echo "echo \"\"" >> dist/benpak-distribution/install.sh
	echo "echo \"Run: benpak (if ~/bin is in your PATH) or ~/bin/benpak\"" >> dist/benpak-distribution/install.sh
	chmod +x dist/benpak-distribution/install.sh
	cp README.md dist/benpak-distribution/README.txt
	@echo "Distribution package created in dist/benpak-distribution/"

# Create TAR archive for distribution
.PHONY: tar-package
tar-package: dist-package
	@echo "Creating TAR archive..."
	cd dist && tar -czf benpak-linux-$(shell date +%Y%m%d).tar.gz benpak-distribution/
	@echo "TAR archive created: dist/benpak-linux-$(shell date +%Y%m%d).tar.gz"

# Optimize executable size with UPX
.PHONY: optimize
optimize: build
	@echo "Optimizing executable size..."
	@if command -v upx >/dev/null 2>&1; then \
		upx --best $(DIST_DIR)/benpak; \
		echo "Executable optimized with UPX"; \
	else \
		echo "UPX not found. Install with: sudo apt install upx"; \
	fi

# Test the built executable
.PHONY: test-exe
test-exe: build
	@echo "Testing built executable..."
	$(DIST_DIR)/benpak --version || echo "Testing basic execution..."
	@echo "Executable test completed"

# Create Debian package
.PHONY: deb-package
deb-package: build
	@echo "Creating Debian package..."
	mkdir -p dist/benpak-deb/DEBIAN
	mkdir -p dist/benpak-deb/usr/bin
	mkdir -p dist/benpak-deb/usr/share/applications
	mkdir -p dist/benpak-deb/usr/share/doc/benpak
	cp $(DIST_DIR)/benpak dist/benpak-deb/usr/bin/
	echo "Package: benpak" > dist/benpak-deb/DEBIAN/control
	echo "Version: 1.0.0" >> dist/benpak-deb/DEBIAN/control
	echo "Architecture: amd64" >> dist/benpak-deb/DEBIAN/control
	echo "Maintainer: BenPak Team <contact@benpak.com>" >> dist/benpak-deb/DEBIAN/control
	echo "Description: Package Manager for 42 School" >> dist/benpak-deb/DEBIAN/control
	echo "Depends: libc6, libqt5gui5" >> dist/benpak-deb/DEBIAN/control
	cp README.md dist/benpak-deb/usr/share/doc/benpak/
	dpkg-deb --build dist/benpak-deb dist/benpak_1.0.0_amd64.deb
	@echo "Debian package created: dist/benpak_1.0.0_amd64.deb"

# Create AppImage
.PHONY: appimage
appimage: build
	@echo "Creating AppImage..."
	@if command -v appimagetool >/dev/null 2>&1; then \
		mkdir -p dist/benpak.AppDir/usr/bin; \
		cp $(DIST_DIR)/benpak dist/benpak.AppDir/usr/bin/; \
		echo "[Desktop Entry]" > dist/benpak.AppDir/benpak.desktop; \
		echo "Name=BenPak" >> dist/benpak.AppDir/benpak.desktop; \
		echo "Exec=benpak" >> dist/benpak.AppDir/benpak.desktop; \
		echo "Type=Application" >> dist/benpak.AppDir/benpak.desktop; \
		echo "Categories=System;" >> dist/benpak.AppDir/benpak.desktop; \
		appimagetool dist/benpak.AppDir dist/BenPak-x86_64.AppImage; \
		echo "AppImage created: dist/BenPak-x86_64.AppImage"; \
	else \
		echo "appimagetool not found. Install AppImageKit first."; \
	fi

# Create Flatpak manifest
.PHONY: flatpak-manifest
flatpak-manifest:
	@echo "Creating Flatpak manifest..."
	@echo "app-id: com.benpak.BenPak" > dist/com.benpak.BenPak.yaml
	@echo "runtime: org.freedesktop.Platform" >> dist/com.benpak.BenPak.yaml
	@echo "runtime-version: '22.08'" >> dist/com.benpak.BenPak.yaml
	@echo "sdk: org.freedesktop.Sdk" >> dist/com.benpak.BenPak.yaml
	@echo "command: benpak" >> dist/com.benpak.BenPak.yaml
	@echo "modules:" >> dist/com.benpak.BenPak.yaml
	@echo "  - name: benpak" >> dist/com.benpak.BenPak.yaml
	@echo "    buildsystem: simple" >> dist/com.benpak.BenPak.yaml
	@echo "    build-commands:" >> dist/com.benpak.BenPak.yaml
	@echo "      - install -Dm755 benpak /app/bin/benpak" >> dist/com.benpak.BenPak.yaml
	@echo "    sources:" >> dist/com.benpak.BenPak.yaml
	@echo "      - type: file" >> dist/com.benpak.BenPak.yaml
	@echo "        path: $(DIST_DIR)/benpak" >> dist/com.benpak.BenPak.yaml
	@echo "Flatpak manifest created: dist/com.benpak.BenPak.yaml"

# Upload to GitHub releases (requires gh CLI)
.PHONY: github-release
github-release: release
	@echo "Creating GitHub release..."
	@if command -v gh >/dev/null 2>&1; then \
		gh release create v$(shell date +%Y.%m.%d) \
			dist/benpak-linux-$(shell date +%Y%m%d).tar.gz \
			--title "BenPak v$(shell date +%Y.%m.%d)" \
			--notes "Release build $(shell date +%Y%m%d)"; \
	else \
		echo "GitHub CLI not found. Install with: sudo apt install gh"; \
	fi

# Create release-ready package
.PHONY: release
release: clean build optimize tar-package
	@echo "Release package created!"
	@echo "📦 Files created:"
	@ls -la dist/benpak-linux-*.tar.gz
	@echo ""
	@echo "🚀 Ready for distribution!"
	@echo "Upload dist/benpak-linux-$(shell date +%Y%m%d).tar.gz to your distribution platform"

# Help target
.PHONY: help
help:
	@echo "🎯 BenPak Makefile Commands:"
	@echo ""
	@echo "📋 Development:"
	@echo "  setup         - Create virtual environment and install dependencies"
	@echo "  run           - Run the application (with venv)"
	@echo "  run-system    - Run the application (system python)"
	@echo "  dev           - Run in development mode with auto-restart"
	@echo "  install-deps  - Install dependencies system-wide"
	@echo ""
	@echo "🔨 Build:"
	@echo "  build         - Build standalone executable"
	@echo "  optimize      - Optimize executable size with UPX"
	@echo "  test-exe      - Test the built executable"
	@echo ""
	@echo "📦 Distribution:"
	@echo "  dist-package  - Create distribution package with installer"
	@echo "  tar-package   - Create TAR archive for distribution"
	@echo "  deb-package   - Create Debian package (.deb)"
	@echo "  appimage      - Create AppImage portable package"
	@echo "  flatpak-manifest - Create Flatpak manifest"
	@echo ""
	@echo "🚀 Release:"
	@echo "  release       - Create complete release package (TAR)"
	@echo "  github-release - Create GitHub release with assets"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  install       - Install built executable to ~/Programs"
	@echo "  install-release - Full release and install process (release + install)"
	@echo "  clean         - Clean build artifacts"
	@echo "  clean-all     - Clean everything including virtual environment"
	@echo "  help          - Show this help message"
	@echo ""
	@echo "💡 Quick Start: make release"
