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
	./$(VENV_DIR)/bin/pyinstaller --onefile --windowed \
		--name benpak \
		--distpath $(DIST_DIR) \
		--workpath $(BUILD_DIR) \
		$(SRC_DIR)/main.py
	@echo "Executable built in $(DIST_DIR)/benpak"

# Clean build artifacts
.PHONY: clean
clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR) *.spec
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

# Development mode with auto-reload
.PHONY: dev
dev:
	@echo "Starting development mode..."
	while true; do \
		./$(VENV_DIR)/bin/python $(SRC_DIR)/main.py; \
		echo "App crashed or closed. Press Ctrl+C to exit or any key to restart..."; \
		read -n 1; \
	done

# Help target
.PHONY: help
help:
	@echo "BenPak Makefile Commands:"
	@echo "  all          - Setup environment and build (default)"
	@echo "  setup        - Create virtual environment and install dependencies"
	@echo "  install-deps - Install dependencies system-wide"
	@echo "  run          - Run the application (with venv)"
	@echo "  run-system   - Run the application (system python)"
	@echo "  build        - Build standalone executable"
	@echo "  install      - Install built executable to ~/Programs"
	@echo "  dev          - Run in development mode with auto-restart"
	@echo "  clean        - Clean build artifacts"
	@echo "  clean-all    - Clean everything including virtual environment"
	@echo "  help         - Show this help message"
