#!/usr/bin/env python3
"""
Setup script for React frontend
Automatically installs React dependencies and sets up the frontend
"""

import subprocess
import sys
import os
from pathlib import Path
import shutil

def run_command(command, cwd=None, check=True):
    """Run a command and handle errors"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_node_npm():
    """Check if Node.js and npm are installed"""
    print("🔍 Checking Node.js and npm...")
    
    # Check Node.js
    success, stdout, stderr = run_command("node --version", check=False)
    if not success:
        print("❌ Node.js not found")
        print("💡 Please install Node.js from https://nodejs.org/")
        return False
    
    node_version = stdout.strip()
    print(f"✅ Node.js {node_version} found")
    
    # Check npm
    success, stdout, stderr = run_command("npm --version", check=False)
    if not success:
        print("❌ npm not found")
        print("💡 Please install npm (usually comes with Node.js)")
        return False
    
    npm_version = stdout.strip()
    print(f"✅ npm {npm_version} found")
    
    return True

def create_react_app():
    """Create React app if it doesn't exist"""
    project_root = Path(__file__).parent
    react_dir = project_root / "react-frontend"
    
    if react_dir.exists():
        print("✅ React frontend directory already exists")
        return True
    
    print("🚀 Creating React app...")
    
    # Create React app
    success, stdout, stderr = run_command(
        "npx create-react-app react-frontend --yes",
        cwd=project_root
    )
    
    if not success:
        print(f"❌ Failed to create React app: {stderr}")
        return False
    
    print("✅ React app created successfully")
    return True

def install_dependencies():
    """Install React dependencies"""
    project_root = Path(__file__).parent
    react_dir = project_root / "react-frontend"
    
    print("📦 Installing React dependencies...")
    
    # Install dependencies
    success, stdout, stderr = run_command(
        "npm install",
        cwd=react_dir
    )
    
    if not success:
        print(f"❌ Failed to install dependencies: {stderr}")
        return False
    
    print("✅ Dependencies installed successfully")
    return True

def install_additional_packages():
    """Install additional packages for the chat interface"""
    project_root = Path(__file__).parent
    react_dir = project_root / "react-frontend"
    
    print("📦 Installing additional packages...")
    
    packages = [
        "@mui/material",
        "@emotion/react",
        "@emotion/styled",
        "@mui/icons-material",
        "framer-motion",
        "react-spring",
        "axios",
        "socket.io-client"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        success, stdout, stderr = run_command(
            f"npm install {package}",
            cwd=react_dir
        )
        
        if not success:
            print(f"❌ Failed to install {package}: {stderr}")
            return False
    
    print("✅ Additional packages installed successfully")
    return True

def copy_components():
    """Copy React components to the app"""
    project_root = Path(__file__).parent
    react_dir = project_root / "react-frontend"
    
    print("📁 Setting up React components...")
    
    # Create components directory
    components_dir = react_dir / "src" / "components"
    components_dir.mkdir(exist_ok=True)
    
    # Copy component files (these will be created by the user)
    print("✅ Components directory created")
    print("💡 You'll need to create the component files manually")
    
    return True

def main():
    """Main setup function"""
    print("🎉 React Frontend Setup")
    print("=" * 40)
    
    # Check Node.js and npm
    if not check_node_npm():
        return False
    
    # Create React app
    if not create_react_app():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Install additional packages
    if not install_additional_packages():
        return False
    
    # Copy components
    if not copy_components():
        return False
    
    print("\n🎉 React frontend setup completed!")
    print("=" * 40)
    print("📁 React app location: ./react-frontend")
    print("🚀 To start development: cd react-frontend && npm start")
    print("🔧 To build for production: cd react-frontend && npm run build")
    print("\n💡 Next steps:")
    print("   1. Create the React component files")
    print("   2. Run 'python start_app.py' to start the full application")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
