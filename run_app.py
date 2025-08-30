#!/usr/bin/env python3
"""
Launcher script for the Bangladesh Job Search Agent Streamlit Interface
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Streamlit application"""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    app_path = project_root / "src" / "interface" / "streamlit_app.py"
    
    # Check if the app file exists
    if not app_path.exists():
        print("❌ Error: Streamlit app not found!")
        print(f"Expected path: {app_path}")
        sys.exit(1)
    
    print("🚀 Launching Bangladesh Job Search Agent...")
    print(f"📁 App path: {app_path}")
    print("🌐 Opening in browser...")
    print("💡 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run the Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Server stopped.")
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
