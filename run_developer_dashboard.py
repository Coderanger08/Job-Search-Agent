#!/usr/bin/env python3
"""
Launcher for Developer Dashboard
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Developer Dashboard"""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    dashboard_path = project_root / "developer_dashboard.py"
    
    # Check if the dashboard file exists
    if not dashboard_path.exists():
        print("❌ Error: Developer Dashboard not found!")
        print(f"Expected path: {dashboard_path}")
        sys.exit(1)
    
    print("🔧 Launching Developer Dashboard...")
    print(f"📁 Dashboard path: {dashboard_path}")
    print("🌐 Opening in browser...")
    print("💡 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run the Developer Dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_path),
            "--server.port", "8502",  # Different port from main app
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Developer Dashboard stopped.")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
