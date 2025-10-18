#!/usr/bin/env python3
"""
Auto-installer and runner for PricePulse Flask application
This script will install dependencies and run the application
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    print("🚀 PricePulse Flask Application Installer")
    print("=" * 50)
    
    # Check if we're running Python 3
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Required packages
    packages = [
        "Flask==3.0.0",
        "Flask-SQLAlchemy==3.1.1", 
        "Flask-CORS==4.0.0"
    ]
    
    print("\n📦 Installing required packages...")
    
    # Install packages
    for package in packages:
        if not install_package(package):
            print(f"\n❌ Installation failed for {package}")
            print("Please install manually: pip install " + package)
            return False
    
    print("\n✅ All packages installed successfully!")
    print("\n🎉 Starting PricePulse application...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Import and run the application
    try:
        from run_app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Error importing application: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running application: {e}")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 PricePulse application stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check the error message and try again")
