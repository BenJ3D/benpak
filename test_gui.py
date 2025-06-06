#!/usr/bin/env python3
"""
Test script to verify PyQt5 installation and basic functionality
"""

import sys
import os

try:
    from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
    from PyQt5.QtCore import Qt
    print("✅ PyQt5 imports successful")
    
    # Test basic widget creation
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("BenPak Test")
    window.setGeometry(100, 100, 300, 200)
    
    label = QLabel("BenPak installation test successful!", window)
    label.setAlignment(Qt.AlignCenter)
    window.setCentralWidget(label)
    
    print("✅ Basic Qt widgets created successfully")
    print("✅ Test completed - BenPak should work correctly!")
    
    # Don't actually show the window in headless mode
    # window.show()
    # return app.exec_()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
