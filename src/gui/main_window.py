"""
Main Window - GUI for BenPak Package Manager
"""

import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QListWidget, QListWidgetItem, QPushButton, QLabel, 
                             QProgressBar, QStatusBar, QMessageBox, QSplitter,
                             QTextEdit, QGroupBox, QScrollArea, QFrame, QMenuBar,
                             QMenu, QAction, QDialog, QFormLayout, QLineEdit,
                             QCheckBox, QSpinBox, QDialogButtonBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon

from package_manager import PackageManager
from config import Config


class PackageInstallWorker(QThread):
    """Worker thread for package installation"""
    progress_changed = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, package_manager, package):
        super().__init__()
        self.package_manager = package_manager
        self.package = package
    
    def run(self):
        try:
            def progress_callback(progress, message=""):
                self.progress_changed.emit(progress, message)
            
            success = self.package_manager.install_package(self.package, progress_callback)
            self.finished.emit(success, "Installation completed successfully!")
            
        except Exception as e:
            self.finished.emit(False, str(e))


class PackageWidget(QFrame):
    """Widget representing a single package"""

    install_requested = pyqtSignal(dict)
    uninstall_requested = pyqtSignal(str)
    open_requested = pyqtSignal(dict)
    
    def __init__(self, package, is_installed=False, version=None):
        super().__init__()
        self.package = package
        self.is_installed = is_installed
        self.version = version
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the package widget UI"""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout(self)
        
        # Package info
        info_layout = QVBoxLayout()
        
        # Name and icon
        name_layout = QHBoxLayout()
        icon_label = QLabel(self.package.get("icon", "📦"))
        icon_label.setFont(QFont("Arial", 16))
        name_label = QLabel(self.package["name"])
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        name_layout.addWidget(icon_label)
        name_layout.addWidget(name_label)
        name_layout.addStretch()
        
        # Description
        desc_label = QLabel(self.package.get("description", ""))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #cccccc; font-size: 10px;")
        
        # Status
        status_text = "Installed" if self.is_installed else "Not installed"
        if self.is_installed and self.version:
            status_text += f" (v{self.version})"
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet("color: #4a90e2; font-weight: bold;")
        
        info_layout.addLayout(name_layout)
        info_layout.addWidget(desc_label)
        info_layout.addWidget(status_label)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        if self.is_installed:
            self.open_button = QPushButton("Open")
            self.open_button.setStyleSheet("background-color: #3498db;")
            self.open_button.clicked.connect(self.open_package)

            self.action_button = QPushButton("Uninstall")
            self.action_button.setStyleSheet("background-color: #e74c3c;")
            self.action_button.clicked.connect(self.uninstall_package)

            button_layout.addWidget(self.open_button)
            button_layout.addWidget(self.action_button)
        else:
            self.action_button = QPushButton("Install")
            self.action_button.setStyleSheet("background-color: #27ae60;")
            self.action_button.clicked.connect(self.install_package)

            button_layout.addWidget(self.action_button)

        button_layout.addStretch()
        
        layout.addLayout(info_layout, 3)
        layout.addLayout(button_layout, 1)
    
    def install_package(self):
        """Request package installation"""
        self.install_requested.emit(self.package)
    
    def uninstall_package(self):
        """Request package uninstallation"""
        self.uninstall_requested.emit(self.package["id"])

    def open_package(self):
        """Request to open the installed package"""
        self.open_requested.emit(self.package)
    
    def set_installing(self, installing=True):
        """Set installing state"""
        if installing:
            self.action_button.setText("Installing...")
            self.action_button.setEnabled(False)
            if hasattr(self, "open_button"):
                self.open_button.setEnabled(False)
        else:
            self.action_button.setText("Install" if not self.is_installed else "Uninstall")
            self.action_button.setEnabled(True)
            if hasattr(self, "open_button"):
                self.open_button.setEnabled(True)


class SettingsDialog(QDialog):
    """Settings dialog for configuring BenPak"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the settings dialog UI"""
        self.setWindowTitle("BenPak Settings")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Form layout for settings
        form_layout = QFormLayout()
        
        # Install directory
        self.install_dir_edit = QLineEdit(self.config.get("install_directory"))
        form_layout.addRow("Install Directory:", self.install_dir_edit)
        
        # Create desktop shortcuts
        self.shortcuts_checkbox = QCheckBox()
        self.shortcuts_checkbox.setChecked(self.config.get("create_desktop_shortcuts"))
        form_layout.addRow("Create Desktop Shortcuts:", self.shortcuts_checkbox)
        
        # Auto refresh interval
        self.refresh_spinbox = QSpinBox()
        self.refresh_spinbox.setRange(10, 300)
        self.refresh_spinbox.setValue(self.config.get("auto_refresh_interval"))
        self.refresh_spinbox.setSuffix(" seconds")
        form_layout.addRow("Auto Refresh Interval:", self.refresh_spinbox)
        
        # Download timeout
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(10, 120)
        self.timeout_spinbox.setValue(self.config.get("download_timeout"))
        self.timeout_spinbox.setSuffix(" seconds")
        form_layout.addRow("Download Timeout:", self.timeout_spinbox)
        
        # Check updates on startup
        self.updates_checkbox = QCheckBox()
        self.updates_checkbox.setChecked(self.config.get("check_updates_on_startup"))
        form_layout.addRow("Check Updates on Startup:", self.updates_checkbox)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept(self):
        """Save settings and close dialog"""
        self.config.set("install_directory", self.install_dir_edit.text())
        self.config.set("create_desktop_shortcuts", self.shortcuts_checkbox.isChecked())
        self.config.set("auto_refresh_interval", self.refresh_spinbox.value())
        self.config.set("download_timeout", self.timeout_spinbox.value())
        self.config.set("check_updates_on_startup", self.updates_checkbox.isChecked())
        super().accept()


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.package_manager = PackageManager()
        self.install_worker = None
        self.all_packages = []  # Store all packages for filtering
        
        self.setup_ui()
        self.load_packages()
        
        # Setup timer for periodic refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_packages)
        refresh_interval = self.config.get("auto_refresh_interval", 30) * 1000
        self.refresh_timer.start(refresh_interval)
        
        # Load window geometry
        geometry = self.config.get("window_geometry", {})
        self.setGeometry(
            geometry.get("x", 100),
            geometry.get("y", 100),
            geometry.get("width", 900),
            geometry.get("height", 600)
        )
    
    def setup_ui(self):
        """Setup the main window UI"""
        self.setWindowTitle("BenPak - Package Manager for 42 School")
        self.setGeometry(100, 100, 900, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("BenPak Package Manager")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #4a90e2; margin: 10px;")
        
        # Search and filter layout
        search_filter_layout = QVBoxLayout()
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages...")
        self.search_input.textChanged.connect(self.filter_packages)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #404040;
                min-width: 200px;
            }
        """)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        # Quick filter buttons
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Quick filters:")
        filter_label.setStyleSheet("font-size: 12px; color: #888888;")
        
        all_btn = QPushButton("All")
        all_btn.setStyleSheet("QPushButton { padding: 4px 12px; font-size: 11px; }")
        all_btn.clicked.connect(lambda: self.apply_quick_filter("all"))
        
        dev_btn = QPushButton("Development")
        dev_btn.setStyleSheet("QPushButton { padding: 4px 12px; font-size: 11px; }")
        dev_btn.clicked.connect(lambda: self.apply_quick_filter("development"))
        
        comm_btn = QPushButton("Communication")
        comm_btn.setStyleSheet("QPushButton { padding: 4px 12px; font-size: 11px; }")
        comm_btn.clicked.connect(lambda: self.apply_quick_filter("communication"))
        
        media_btn = QPushButton("Media")
        media_btn.setStyleSheet("QPushButton { padding: 4px 12px; font-size: 11px; }")
        media_btn.clicked.connect(lambda: self.apply_quick_filter("media"))
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(all_btn)
        filter_layout.addWidget(dev_btn)
        filter_layout.addWidget(comm_btn)
        filter_layout.addWidget(media_btn)
        filter_layout.addStretch()
        
        search_filter_layout.addLayout(search_layout)
        search_filter_layout.addLayout(filter_layout)
        
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.clicked.connect(self.refresh_packages)
        
        settings_button = QPushButton("⚙️ Settings")
        settings_button.clicked.connect(self.open_settings)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addLayout(search_filter_layout)
        header_layout.addWidget(refresh_button)
        header_layout.addWidget(settings_button)
        
        # Packages area
        packages_group = QGroupBox("Available Packages")
        packages_layout = QVBoxLayout(packages_group)
        
        # Scroll area for packages
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.packages_widget = QWidget()
        self.packages_layout = QVBoxLayout(self.packages_widget)
        self.packages_layout.addStretch()
        
        scroll_area.setWidget(self.packages_widget)
        packages_layout.addWidget(scroll_area)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Console d'événements
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(80)
        self.console.setStyleSheet("background-color: #222; color: #8f8; font-size: 11px;")
        
        # Add to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(packages_group)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.console)
        
        # Set initial status
        self.status_bar.showMessage("Ready")

    def log_event(self, message):
        self.console.append(message)

    def load_packages(self):
        """Load and display available packages"""
        try:
            self.all_packages = self.package_manager.get_available_packages()
            # VIP: VSCode, Discord, Android Studio, WebStorm
            vip_ids = ["vscode", "discord", "android-studio", "webstorm"]
            vip_packages = [pkg for pkg in self.all_packages if pkg["id"] in vip_ids]
            other_packages = [pkg for pkg in self.all_packages if pkg["id"] not in vip_ids]
            self.display_packages(vip_packages + other_packages)
            self.status_bar.showMessage(f"Loaded {len(self.all_packages)} packages")
            self.log_event("[INFO] Package list loaded.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load packages: {str(e)}")
            self.log_event(f"[ERROR] Failed to load packages: {str(e)}")

    def display_packages(self, packages):
        """Display a list of packages in the UI"""
        # Clear existing widgets
        for i in reversed(range(self.packages_layout.count())):
            child = self.packages_layout.itemAt(i).widget()
            if child and isinstance(child, PackageWidget):
                child.setParent(None)
        
        # Add package widgets
        for package in packages:
            is_installed = self.package_manager.is_package_installed(package["id"])
            version = self.package_manager.get_installed_version(package["id"])
            
            package_widget = PackageWidget(package, is_installed, version)
            package_widget.install_requested.connect(self.install_package)
            package_widget.uninstall_requested.connect(self.uninstall_package)
            package_widget.open_requested.connect(self.open_package)
            
            # Insert before the stretch
            self.packages_layout.insertWidget(self.packages_layout.count() - 1, package_widget)
    
    def filter_packages(self, search_text):
        """Filter packages based on search text"""
        if not search_text:
            # Show all packages if search is empty
            filtered_packages = self.all_packages
        else:
            # Filter packages by name or description
            search_text = search_text.lower()
            filtered_packages = []
            for package in self.all_packages:
                if (search_text in package["name"].lower() or 
                    search_text in package.get("description", "").lower() or
                    search_text in package["id"].lower()):
                    filtered_packages.append(package)
        
        self.display_packages(filtered_packages)
        
        # Update status bar
        if search_text:
            self.status_bar.showMessage(f"Found {len(filtered_packages)} packages matching '{search_text}'")
        else:
            self.status_bar.showMessage(f"Showing all {len(filtered_packages)} packages")
    
    def refresh_packages(self):
        """Refresh package list"""
        self.log_event("[ACTION] Refreshing package list...")
        self.load_packages()
    
    def install_package(self, package):
        """Install a package"""
        if self.install_worker and self.install_worker.isRunning():
            QMessageBox.information(self, "Installation in Progress", 
                                  "Another installation is already in progress. Please wait.")
            return
        
        # Find the package widget and set it to installing state
        for i in range(self.packages_layout.count()):
            widget = self.packages_layout.itemAt(i).widget()
            if isinstance(widget, PackageWidget) and widget.package["id"] == package["id"]:
                widget.set_installing(True)
                break
        
        # Start installation
        self.install_worker = PackageInstallWorker(self.package_manager, package)
        self.install_worker.progress_changed.connect(self.update_progress)
        self.install_worker.finished.connect(self.installation_finished)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage(f"Installing {package['name']}...")
        self.log_event(f"[ACTION] Installing {package['name']}...")
        
        self.install_worker.start()
    
    def uninstall_package(self, package_id):
        """Uninstall a package"""
        reply = QMessageBox.question(self, "Confirm Uninstall", 
                                   f"Are you sure you want to uninstall this package?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                success = self.package_manager.uninstall_package(package_id)
                if success:
                    self.status_bar.showMessage("Package uninstalled successfully")
                    self.log_event(f"[ACTION] Uninstalled {package_id}.")
                    self.refresh_packages()
                else:
                    QMessageBox.warning(self, "Uninstall Failed", "Failed to uninstall package")
                    self.log_event(f"[ERROR] Failed to uninstall {package_id}.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Uninstall failed: {str(e)}")
                self.log_event(f"[ERROR] Uninstall failed: {str(e)}")

    def open_package(self, package):
        """Open an installed package"""
        try:
            success = self.package_manager.open_package(package)
            if success:
                self.status_bar.showMessage(f"Opened {package['name']}")
                self.log_event(f"[ACTION] Opened {package['name']}")
            else:
                QMessageBox.warning(self, "Open Failed", "Failed to launch the application.")
                self.log_event(f"[ERROR] Failed to open {package['id']}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open package: {str(e)}")
            self.log_event(f"[ERROR] Failed to open {package['id']}: {str(e)}")

    def update_progress(self, progress, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(progress)
        if message:
            self.status_bar.showMessage(message)
            self.log_event(f"[PROGRESS] {message}")

    def installation_finished(self, success, message):
        """Handle installation completion"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_bar.showMessage("Installation completed successfully")
            QMessageBox.information(self, "Success", message)
            self.log_event("[SUCCESS] Installation completed.")
            self.refresh_packages()
        else:
            self.status_bar.showMessage("Installation failed")
            QMessageBox.critical(self, "Installation Failed", message)
            self.log_event(f"[ERROR] Installation failed: {message}")
        
        # Reset package widget states
        for i in range(self.packages_layout.count()):
            widget = self.packages_layout.itemAt(i).widget()
            if isinstance(widget, PackageWidget):
                widget.set_installing(False)

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(Config(), self)
        dialog.exec_()
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            # Restart timer with new interval
            refresh_interval = self.config.get("auto_refresh_interval", 30) * 1000
            self.refresh_timer.stop()
            self.refresh_timer.start(refresh_interval)
    
    def check_updates(self):
        """Check for available updates"""
        self.status_bar.showMessage("Checking for updates...")
        self.log_event("[ACTION] Checking for updates...")
        try:
            installed_packages = {}
            packages = self.package_manager.get_available_packages()
            for package in packages:
                if self.package_manager.is_package_installed(package["id"]):
                    version = self.package_manager.get_installed_version(package["id"])
                    installed_packages[package["id"]] = version or "unknown"
            if not installed_packages:
                QMessageBox.information(self, "No Updates", "No packages are currently installed.")
                self.status_bar.showMessage("Ready")
                self.log_event("[INFO] No packages installed.")
                return
            updates = self.package_manager.fetcher.check_for_updates(installed_packages)
            update_count = sum(1 for has_update in updates.values() if has_update)
            if update_count > 0:
                QMessageBox.information(self, "Updates Available", 
                                      f"{update_count} package(s) have updates available. "
                                      "Use the refresh button to see the latest versions.")
                self.log_event(f"[INFO] {update_count} updates available.")
            else:
                QMessageBox.information(self, "No Updates", "All packages are up to date.")
                self.log_event("[INFO] All packages are up to date.")
            self.status_bar.showMessage("Update check completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to check for updates: {str(e)}")
            self.status_bar.showMessage("Update check failed")
            self.log_event(f"[ERROR] Update check failed: {str(e)}")
