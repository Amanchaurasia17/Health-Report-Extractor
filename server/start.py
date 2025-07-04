#!/usr/bin/env python3
"""
Startup script for the Health Report Extractor API
"""
import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is supported"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_tesseract():
    """Check if Tesseract is installed"""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Tesseract OCR is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Tesseract OCR is not installed")
    print("Please install Tesseract OCR:")
    print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
    print("  macOS: brew install tesseract")
    print("  Linux: sudo apt-get install tesseract-ocr")
    return False

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Health Report Extractor API server...")
    try:
        subprocess.run([sys.executable, 'main.py'], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")

def main():
    """Main startup function"""
    print("🩺 Health Report Extractor API - Startup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_tesseract():
        sys.exit(1)
    
    # Install dependencies if requirements.txt exists
    if Path('requirements.txt').exists():
        if not install_dependencies():
            sys.exit(1)
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
