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
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QPen, QColor

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
    launch_requested = pyqtSignal(str)
    
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
            # Launch button
            self.launch_button = QPushButton("Lancer")
            self.launch_button.setStyleSheet("background-color: #2980b9; color: white;")
            self.launch_button.clicked.connect(self.launch_package)
            button_layout.addWidget(self.launch_button)
            # Beautiful spinner (hidden by default)
            self.spinner = SpinnerWidget()
            self.spinner.setVisible(False)
            button_layout.addWidget(self.spinner)

            self.action_button = QPushButton("Uninstall")
            self.action_button.setStyleSheet("background-color: #e74c3c;")
            self.action_button.clicked.connect(self.uninstall_package)
        else:
            self.action_button = QPushButton("Install")
            self.action_button.setStyleSheet("background-color: #27ae60;")
            self.action_button.clicked.connect(self.install_package)

        button_layout.addWidget(self.action_button)
        button_layout.addStretch()

        layout.addLayout(info_layout, 3)
        layout.addLayout(button_layout, 1)

    def set_launching(self, launching=True):
        """Set launching state for the launch button"""
        if hasattr(self, 'launch_button'):
            if launching:
                self.launch_button.setText("Lancement…")
                self.launch_button.setEnabled(False)
                self.launch_button.setStyleSheet("background-color: #7f8c8d; color: white;")  # Grayed out
                if hasattr(self, 'spinner'):
                    self.spinner.start()
            else:
                self.launch_button.setText("Lancer")
                self.launch_button.setEnabled(True)
                self.launch_button.setStyleSheet("background-color: #2980b9; color: white;")  # Back to blue
                if hasattr(self, 'spinner'):
                    self.spinner.stop()

    def launch_package(self):
        """Request to launch the application"""
        self.launch_requested.emit(self.package["id"])
    
    def install_package(self):
        """Request package installation"""
        self.install_requested.emit(self.package)
    
    def uninstall_package(self):
        """Request package uninstallation"""
        self.uninstall_requested.emit(self.package["id"])
    
    def set_installing(self, installing=True):
        """Set installing state"""
        if installing:
            self.action_button.setText("Installing...")
            self.action_button.setEnabled(False)
        else:
            self.action_button.setText("Install" if not self.is_installed else "Uninstall")
            self.action_button.setEnabled(True)


class SettingsDialog(QDialog):
    """Settings dialog for configuring BenPak"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.config = config
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # Form layout for settings
        form_layout = QFormLayout()

        # Install directory
        self.old_install_dir = self.config.get("install_directory")
        self.install_dir_edit = QLineEdit(self.old_install_dir)
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
        """Save settings and close dialog, handle install dir change"""
        new_install_dir = self.install_dir_edit.text()
        self.config.set("create_desktop_shortcuts", self.shortcuts_checkbox.isChecked())
        self.config.set("auto_refresh_interval", self.refresh_spinbox.value())
        self.config.set("download_timeout", self.timeout_spinbox.value())
        self.config.set("check_updates_on_startup", self.updates_checkbox.isChecked())

        if new_install_dir != self.old_install_dir:
            from PyQt5.QtWidgets import QMessageBox
            msg = ("Le répertoire d'installation a été modifié. Les applications non désinstallées dans l'ancien répertoire n'apparaîtront plus dans le programme.\n\n"
                   "Voulez-vous redémarrer l'application maintenant pour appliquer le changement ?")
            reply = QMessageBox.question(self, "Redémarrage nécessaire", msg, QMessageBox.Yes | QMessageBox.No)
            self.config.set("install_directory", new_install_dir)
            if reply == QMessageBox.Yes:
                self.restart_app()
            else:
                super().accept()
        else:
            self.config.set("install_directory", new_install_dir)
            super().accept()

    def restart_app(self):
        """Restart the application"""
        import sys, os
        python = sys.executable
        os.execl(python, python, *sys.argv)


class SpinnerWidget(QLabel):
    """A beautiful animated spinner widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        self.setStyleSheet("background: transparent;")
        
    def start(self):
        """Start the spinner animation"""
        self.timer.start(50)  # Update every 50ms for smooth animation
        self.show()
        
    def stop(self):
        """Stop the spinner animation"""
        self.timer.stop()
        self.hide()
        
    def rotate(self):
        """Rotate the spinner"""
        self.angle = (self.angle + 15) % 360
        self.update()
        
    def paintEvent(self, event):
        """Custom paint event for the spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw spinning dots
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        
        for i in range(8):
            painter.save()
            painter.rotate(i * 45)
            
            # Fade effect for trailing dots
            alpha = 255 - (i * 25)
            if alpha < 50:
                alpha = 50
                
            color = QColor(74, 144, 226, alpha)  # Blue color with alpha
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            
            # Draw dot
            painter.drawEllipse(6, -1, 2, 2)
            painter.restore()


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
            package_widget.launch_requested.connect(self.launch_package)
            
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
        """Uninstall a package with process detection and GUI interaction"""
        # 1. Check for running processes
        try:
            running_processes = self.package_manager._find_running_processes(package_id)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de la détection des processus : {str(e)}")
            self.log_event(f"[ERROR] Échec de la détection des processus : {str(e)}")
            return

        if running_processes:
            # Build process info string
            proc_lines = []
            for proc in running_processes:
                line = f"PID {proc.get('pid', '?')}: {proc.get('name', '?')} (cmd: {' '.join(proc.get('cmdline', []))})"
                proc_lines.append(line)
            proc_str = "\n".join(proc_lines)
            msg = (f"Des processus liés à ce package sont en cours d'exécution :\n\n"
                   f"{proc_str}\n\n"
                   "Voulez-vous forcer la fermeture de ces processus et continuer la désinstallation ?")
            reply = QMessageBox.question(self, "Processus en cours",
                                        msg,
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                self.status_bar.showMessage("Désinstallation annulée (processus en cours)")
                self.log_event("[CANCEL] Désinstallation annulée par l'utilisateur (processus en cours)")
                return
            # Forcer le kill, puis attendre un délai avant retry
            self.log_event(f"[ACTION] Killing {len(running_processes)} process(es) before uninstall...")
            self.package_manager._kill_application_processes(running_processes)
            self.status_bar.showMessage("Processus tués. Attente 4 secondes avant désinstallation...")
            self.log_event("[INFO] Attente 4s pour libération des ressources système...")
            QTimer.singleShot(4000, lambda: self._uninstall_package_final(package_id))
        else:
            # Aucun process bloquant, désinstaller directement
            self._uninstall_package_final(package_id)

    def _uninstall_package_final(self, package_id):
        """Procède à la désinstallation effective après délai éventuel"""
        # Vérifier si des processus sont encore en cours après le délai
        try:
            remaining_processes = self.package_manager._find_running_processes(package_id)
            if remaining_processes:
                proc_names = [proc.get('name', 'Unknown') for proc in remaining_processes]
                msg = f"Certains processus sont encore en cours après le kill : {', '.join(proc_names)}\n\nLa désinstallation ne peut pas continuer."
                QMessageBox.critical(self, "Processus toujours actifs", msg)
                self.status_bar.showMessage("Désinstallation annulée - processus toujours actifs")
                self.log_event(f"[ERROR] Processus toujours actifs après kill : {', '.join(proc_names)}")
                return
        except Exception as e:
            self.log_event(f"[WARNING] Impossible de vérifier les processus restants : {str(e)}")
        
        # Procéder à la désinstallation
        try:
            success = self.package_manager.uninstall_package(package_id, force_kill=True)
            if success:
                self.status_bar.showMessage("Désinstallation réussie")
                QMessageBox.information(self, "Succès", "Le package a été désinstallé avec succès.")
                self.log_event(f"[SUCCESS] {package_id} désinstallé.")
                self.refresh_packages()
            else:
                self.status_bar.showMessage("Échec de la désinstallation")
                QMessageBox.warning(self, "Échec", "La désinstallation a échoué ou le package n'était pas installé.")
                self.log_event(f"[ERROR] Échec de la désinstallation de {package_id}.")
        except Exception as e:
            self.status_bar.showMessage("Erreur lors de la désinstallation")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la désinstallation : {str(e)}")
            self.log_event(f"[ERROR] Exception lors de la désinstallation : {str(e)}")

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

    def launch_package(self, package_id):
        """Launch an installed application from the package manager, UX feedback"""
        # Find the widget and set launching state
        widget = None
        for i in range(self.packages_layout.count()):
            w = self.packages_layout.itemAt(i).widget()
            if isinstance(w, PackageWidget) and w.package["id"] == package_id:
                widget = w
                break
        if widget:
            widget.set_launching(True)
        self.status_bar.showMessage(f"Lancement de {package_id}...")
        self.log_event(f"[ACTION] Lancement de {package_id} demandé.")
        # Lancer l'appli dans un QTimer pour UX (simulateur de spinner)
        def do_launch():
            try:
                result = self.package_manager.launch_package(package_id)
                if result is True or result is None:
                    self.status_bar.showMessage(f"{package_id} lancé.")
                    self.log_event(f"[SUCCESS] {package_id} lancé.")
                else:
                    QMessageBox.warning(self, "Erreur", str(result))
                    self.log_event(f"[ERROR] Lancement échoué : {result}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors du lancement : {str(e)}")
                self.log_event(f"[ERROR] Exception lors du lancement : {str(e)}")
            finally:
                if widget:
                    widget.set_launching(False)
        # Affiche le spinner 1s minimum pour le ressenti utilisateur
        QTimer.singleShot(1000, do_launch)

    def apply_quick_filter(self, filter_type):
        """Apply quick filter to packages"""
        if filter_type == "all":
            filtered_packages = self.all_packages
        else:
            # Filter packages by category
            filtered_packages = []
            for package in self.all_packages:
                category = package.get("category", "").lower()
                if filter_type.lower() in category:
                    filtered_packages.append(package)
        
        self.display_packages(filtered_packages)
        self.status_bar.showMessage(f"Filtered by: {filter_type} ({len(filtered_packages)} packages)")
