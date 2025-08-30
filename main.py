#!/usr/bin/env python3
"""
Bangladesh Job Search Agent - Main Application Entry Point
Professional, production-ready application launcher
"""

import sys
import os
import time
import subprocess
import signal
import logging
from datetime import datetime
from pathlib import Path
import json
import argparse

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from src.core.config_manager import ConfigManager
from src.core.logging_manager import LoggingManager
from src.core.health_monitor import HealthMonitor
from src.core.system_validator import SystemValidator

class BangladeshJobSearchAgent:
    """Main application class for Bangladesh Job Search Agent"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.logging_manager = LoggingManager()
        self.health_monitor = HealthMonitor()
        self.system_validator = SystemValidator()
        self.streamlit_process = None
        
    def display_welcome(self):
        """Display welcome screen and application info"""
        print("="*70)
        print("🚀 BANGLADESH JOB SEARCH AGENT")
        print("="*70)
        print("AI-Powered Job Search with Real-time Data from Multiple Sources")
        print("Built with Advanced RAG (Retrieval Augmented Generation) Technology")
        print("="*70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Version: {self.config_manager.get_version()}")
        print("="*70)
    
    def initialize_system(self):
        """Initialize the complete system"""
        print("\n🔧 Initializing Bangladesh Job Search Agent...")
        
        try:
            # Initialize logging
            self.logging_manager.initialize()
            self.logging_manager.log_info("🚀 Starting Bangladesh Job Search Agent")
            
            # Load configuration
            self.config_manager.load_config()
            self.logging_manager.log_info("✅ Configuration loaded successfully")
            
            # Validate system
            validation_result = self.system_validator.validate_system()
            if not validation_result['success']:
                errors = validation_result.get('errors', ['Unknown error'])
                print(f"❌ System validation failed: {errors[0] if errors else 'Unknown error'}")
                return False
            
            self.logging_manager.log_info("✅ System validation passed")
            print("✅ System initialized successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            self.logging_manager.log_error(f"System initialization failed: {e}")
            return False
    
    def run_health_checks(self):
        """Run system health checks"""
        print("\n🏥 Running system health checks...")
        
        # Skip health checks in development mode
        if hasattr(self, 'debug_mode') and self.debug_mode:
            print("⚠️ Health checks skipped in debug mode")
            return True
        
        try:
            health_status = self.health_monitor.check_system_health()
            
            if health_status['overall_health'] == 'healthy':
                print("✅ All health checks passed")
                self.logging_manager.log_info("✅ Health checks passed")
                return True
            else:
                print(f"⚠️ Health check issues: {health_status['issues']}")
                self.logging_manager.log_warning(f"Health check issues: {health_status['issues']}")
                return True  # Continue anyway, just warn
                
        except Exception as e:
            print(f"❌ Health checks failed: {e}")
            self.logging_manager.log_error(f"Health checks failed: {e}")
            return False
    
    def launch_streamlit(self):
        """Launch the Streamlit interface"""
        print("\n🎨 Launching Streamlit Interface...")
        
        try:
            # Get Streamlit app path
            app_path = Path(__file__).parent / "src" / "interface" / "streamlit_app.py"
            
            if not app_path.exists():
                raise FileNotFoundError(f"Streamlit app not found: {app_path}")
            
            # Launch Streamlit
            self.streamlit_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run",
                str(app_path),
                "--server.port", "8501",
                "--server.address", "localhost",
                "--browser.gatherUsageStats", "false"
            ])
            
            print("✅ Streamlit interface launched successfully")
            print("🌐 Opening in browser: http://localhost:8501")
            print("💡 Press Ctrl+C to stop the application")
            
            self.logging_manager.log_info("✅ Streamlit interface launched")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to launch Streamlit: {e}")
            self.logging_manager.log_error(f"Failed to launch Streamlit: {e}")
            return False
    
    def monitor_application(self):
        """Monitor the running application"""
        print("\n📊 Application monitoring started...")
        
        try:
            while self.streamlit_process and self.streamlit_process.poll() is None:
                # Monitor system health
                health_status = self.health_monitor.check_system_health()
                
                # Log periodic status
                if health_status['overall_health'] != 'healthy':
                    self.logging_manager.log_warning(f"Health issues detected: {health_status['issues']}")
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Shutdown signal received...")
            self.graceful_shutdown()
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            self.logging_manager.log_error(f"Monitoring error: {e}")
            self.graceful_shutdown()
    
    def graceful_shutdown(self):
        """Gracefully shutdown the application"""
        print("\n🔄 Shutting down gracefully...")
        
        try:
            # Stop Streamlit process
            if self.streamlit_process:
                self.streamlit_process.terminate()
                self.streamlit_process.wait(timeout=10)
                print("✅ Streamlit process stopped")
            
            # Final logging
            self.logging_manager.log_info("🔄 Application shutdown completed")
            
            print("✅ Shutdown completed successfully")
            print("👋 Thank you for using Bangladesh Job Search Agent!")
            
        except Exception as e:
            print(f"❌ Shutdown error: {e}")
            self.logging_manager.log_error(f"Shutdown error: {e}")
    
    def run(self, args):
        """Main application runner"""
        try:
            # Display welcome
            self.display_welcome()
            
            # Initialize system
            if not self.initialize_system():
                return False
            
            # Run health checks
            if not self.run_health_checks():
                return False
            
            # Launch Streamlit
            if not self.launch_streamlit():
                return False
            
            # Monitor application
            self.monitor_application()
            
            return True
            
        except Exception as e:
            print(f"❌ Application error: {e}")
            self.logging_manager.log_error(f"Application error: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Bangladesh Job Search Agent")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--port", type=int, default=8501, help="Streamlit port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create and run application
    app = BangladeshJobSearchAgent()
    success = app.run(args)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
