#!/usr/bin/env python3
"""
Single Command Launcher for Bangladesh Job Search Agent
Starts both FastAPI backend and React frontend
"""

import subprocess
import sys
import os
import time
import threading
import signal
import requests
from pathlib import Path
import webbrowser

class AppLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_process = None
        self.frontend_process = None
        self.is_running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down...")
        self.is_running = False
        self.stop_services()
        sys.exit(0)
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        # Check Python dependencies
        try:
            import fastapi
            import uvicorn
            print("✅ FastAPI and Uvicorn installed")
        except ImportError:
            print("❌ FastAPI or Uvicorn not installed")
            print("💡 Run: pip install fastapi uvicorn")
            return False
        
        # Check if React dependencies are installed
        react_dir = self.project_root / "react-frontend"
        if not react_dir.exists():
            print("❌ React frontend directory not found")
            print("💡 React frontend needs to be set up")
            return False
        
        node_modules = react_dir / "node_modules"
        if not node_modules.exists():
            print("⚠️  React dependencies not installed")
            print("💡 Run: cd react-frontend && npm install")
            return False
        
        print("✅ All dependencies ready")
        return True
    
    def start_backend(self):
        """Start the FastAPI backend"""
        print("🚀 Starting FastAPI backend...")
        
        try:
            self.backend_process = subprocess.Popen([
                sys.executable, "api_backend.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for backend to start
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get("http://localhost:8000/health", timeout=2)
                    if response.status_code == 200:
                        print("✅ Backend started successfully")
                        return True
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            print("❌ Backend failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the React frontend"""
        print("🚀 Starting React frontend...")
        
        try:
            react_dir = self.project_root / "react-frontend"
            self.frontend_process = subprocess.Popen([
                "npm", "start"
            ], cwd=react_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for frontend to start
            for i in range(60):  # Wait up to 60 seconds
                try:
                    response = requests.get("http://localhost:3000", timeout=2)
                    if response.status_code == 200:
                        print("✅ Frontend started successfully")
                        return True
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            print("❌ Frontend failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting frontend: {e}")
            return False
    
    def open_browser(self):
        """Open browser to the application"""
        print("🌐 Opening browser...")
        time.sleep(2)  # Give frontend a moment to fully load
        webbrowser.open("http://localhost:3000")
    
    def monitor_services(self):
        """Monitor services and restart if needed"""
        while self.is_running:
            time.sleep(10)
            
            # Check backend
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code != 200:
                    print("⚠️  Backend health check failed")
            except:
                print("⚠️  Backend not responding")
            
            # Check frontend
            try:
                response = requests.get("http://localhost:3000", timeout=2)
                if response.status_code != 200:
                    print("⚠️  Frontend health check failed")
            except:
                print("⚠️  Frontend not responding")
    
    def stop_services(self):
        """Stop all running services"""
        print("🛑 Stopping services...")
        
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait()
            print("✅ Backend stopped")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process.wait()
            print("✅ Frontend stopped")
    
    def run(self):
        """Main launcher function"""
        print("🎉 Bangladesh Job Search Agent Launcher")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            print("\n❌ Dependencies not met. Please install required packages.")
            return
        
        print("\n🚀 Starting services...")
        
        # Start backend
        if not self.start_backend():
            print("❌ Failed to start backend")
            return
        
        # Start frontend
        if not self.start_frontend():
            print("❌ Failed to start frontend")
            self.stop_services()
            return
        
        # Open browser
        self.open_browser()
        
        print("\n🎉 Application is running!")
        print("📱 Frontend: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("\n💡 Press Ctrl+C to stop the application")
        print("=" * 50)
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
        finally:
            self.stop_services()
            print("👋 Goodbye!")

def main():
    """Main entry point"""
    launcher = AppLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
