#!/usr/bin/env python3
"""
Quick test script for BenPak functionality
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config():
    """Test configuration system"""
    print("Testing configuration system...")
    try:
        from config import Config
        config = Config()
        
        print(f"✅ Config loaded successfully")
        print(f"   Install directory: {config.get('install_directory')}")
        print(f"   Auto refresh: {config.get('auto_refresh_interval')} seconds")
        print(f"   Create shortcuts: {config.get('create_desktop_shortcuts')}")
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_package_manager():
    """Test package manager"""
    print("\nTesting package manager...")
    try:
        from package_manager import PackageManager
        pm = PackageManager()
        
        packages = pm.get_available_packages()
        print(f"✅ Package manager loaded successfully")
        print(f"   Found {len(packages)} packages:")
        
        for package in packages:
            installed = pm.is_package_installed(package['id'])
            version = pm.get_installed_version(package['id']) if installed else "Not installed"
            status = "✓" if installed else "✗"
            print(f"   {status} {package['name']} ({package['id']}) - {version}")
            print(f"     Latest: {package.get('latest_version', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Package manager test failed: {e}")
        return False

def test_fetcher():
    """Test package fetcher"""
    print("\nTesting package fetcher...")
    try:
        from fetcher import PackageFetcher
        fetcher = PackageFetcher()
        
        print("✅ Fetcher loaded successfully")
        
        # Test version fetching for Discord
        print("   Testing Discord version fetch...")
        version, url = fetcher.get_discord_info()
        print(f"     Discord: {version} - {url[:50]}...")
        
        # Test VSCode
        print("   Testing VSCode version fetch...")
        version, url = fetcher.get_vscode_info()
        print(f"     VSCode: {version} - {url[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Fetcher test failed: {e}")
        return False

def test_shell_detection():
    """Test shell detection and PATH configuration"""
    print("\nTesting shell detection...")
    try:
        from package_manager import PackageManager
        pm = PackageManager()
        
        shell_info = pm.get_shell_info()
        print(f"✅ Shell detection working")
        print(f"   Current shell: {shell_info['current_shell']}")
        print(f"   Preferred shell: {shell_info['preferred_shell']}")
        print(f"   Auto configure PATH: {shell_info['auto_configure_enabled']}")
        print(f"   Detected config files:")
        
        for config_path, shell_name in shell_info['detected_configs']:
            print(f"     - {config_path} ({shell_name})")
        
        return True
    except Exception as e:
        print(f"❌ Shell detection test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== BenPak Component Tests ===\n")
    
    tests = [
        test_config,
        test_package_manager,
        test_fetcher,
        test_shell_detection
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Test Results ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! BenPak should work correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
