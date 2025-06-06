#!/usr/bin/env python3
"""
BenPak - Package Manager for 42 School
Main application entry point
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("BenPak")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("42 School Tools")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Apply dark theme
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QPushButton {
            background-color: #404040;
            border: 1px solid #555555;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #4a90e2;
        }
        QPushButton:pressed {
            background-color: #357abd;
        }
        QListWidget {
            background-color: #353535;
            border: 1px solid #555555;
            border-radius: 4px;
        }
        QListWidget::item {
            padding: 10px;
            border-bottom: 1px solid #404040;
        }
        QListWidget::item:selected {
            background-color: #4a90e2;
        }
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4a90e2;
            border-radius: 3px;
        }
        QStatusBar {
            background-color: #404040;
            border-top: 1px solid #555555;
        }
    """)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
