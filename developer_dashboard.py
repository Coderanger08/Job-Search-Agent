#!/usr/bin/env python3
"""
Developer Dashboard for Bangladesh Job Search Agent
Simple monitoring and debugging tools for developers
"""

import streamlit as st
import psutil
import time
import json
import sys
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path
sys.path.append(os.path.dirname(__file__))

def get_system_metrics():
    """Get basic system metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

def get_process_info():
    """Get current process information"""
    try:
        process = psutil.Process()
        return {
            "pid": process.pid,
            "memory_mb": process.memory_info().rss / (1024**2),
            "cpu_percent": process.cpu_percent(),
            "num_threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections())
        }
    except Exception as e:
        return {"error": str(e)}

def get_python_info():
    """Get Python environment information"""
    return {
        "python_version": sys.version,
        "platform": sys.platform,
        "executable": sys.executable,
        "path": sys.path[:5],  # First 5 paths
        "modules_loaded": len(sys.modules)
    }

def get_project_info():
    """Get project-specific information"""
    project_root = Path(__file__).parent
    
    # Check key files
    key_files = [
        "config.py",
        "src/core/rag_engine.py",
        "src/core/api_scraper_manager.py",
        "src/core/quality_assurance.py",
        "src/interface/streamlit_app.py"
    ]
    
    file_status = {}
    for file_path in key_files:
        full_path = project_root / file_path
        file_status[file_path] = {
            "exists": full_path.exists(),
            "size_kb": full_path.stat().st_size / 1024 if full_path.exists() else 0,
            "modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat() if full_path.exists() else None
        }
    
    return {
        "project_root": str(project_root),
        "key_files": file_status,
        "total_files": len(list(project_root.rglob("*.py")))
    }

def test_core_components():
    """Test core components and return status"""
    results = {}
    
    # Test imports
    try:
        from src.core.rag_engine import RAGEngine
        results["rag_engine_import"] = "✅ Success"
    except Exception as e:
        results["rag_engine_import"] = f"❌ Failed: {e}"
    
    try:
        from src.core.api_scraper_manager import APIScraperManager
        results["api_scraper_import"] = "✅ Success"
    except Exception as e:
        results["api_scraper_import"] = f"❌ Failed: {e}"
    
    try:
        from src.core.quality_assurance import QualityAssuranceLayer
        results["quality_assurance_import"] = "✅ Success"
    except Exception as e:
        results["quality_assurance_import"] = f"❌ Failed: {e}"
    
    try:
        from config import Config
        config = Config()
        results["config_import"] = "✅ Success"
    except Exception as e:
        results["config_import"] = f"❌ Failed: {e}"
    
    return results

def main():
    st.set_page_config(
        page_title="Developer Dashboard",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 Developer Dashboard")
    st.markdown("**Bangladesh Job Search Agent - System Monitoring & Debugging**")
    
    # Sidebar for navigation
    st.sidebar.title("📊 Dashboard Sections")
    section = st.sidebar.selectbox(
        "Choose Section:",
        ["System Overview", "Performance Metrics", "Project Status", "Component Tests", "Real-time Monitoring"]
    )
    
    if section == "System Overview":
        st.header("🖥️ System Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("💻 System Resources")
            metrics = get_system_metrics()
            
            if "error" not in metrics:
                st.metric("CPU Usage", f"{metrics['cpu_percent']:.1f}%")
                st.metric("Memory Usage", f"{metrics['memory_percent']:.1f}%")
                st.metric("Disk Usage", f"{metrics['disk_percent']:.1f}%")
                st.metric("Available Memory", f"{metrics['memory_available_gb']:.1f} GB")
            else:
                st.error(f"Error getting metrics: {metrics['error']}")
        
        with col2:
            st.subheader("🐍 Python Environment")
            python_info = get_python_info()
            
            st.text(f"Version: {python_info['python_version'].split()[0]}")
            st.text(f"Platform: {python_info['platform']}")
            st.text(f"Modules: {python_info['modules_loaded']}")
            st.text(f"Executable: {os.path.basename(python_info['executable'])}")
        
        with col3:
            st.subheader("📁 Project Info")
            project_info = get_project_info()
            
            st.text(f"Root: {os.path.basename(project_info['project_root'])}")
            st.text(f"Total Python Files: {project_info['total_files']}")
            
            # Show key files status
            st.subheader("Key Files Status")
            for file_path, status in project_info['key_files'].items():
                if status['exists']:
                    st.text(f"✅ {os.path.basename(file_path)} ({status['size_kb']:.1f} KB)")
                else:
                    st.text(f"❌ {os.path.basename(file_path)} (Missing)")
    
    elif section == "Performance Metrics":
        st.header("📈 Performance Metrics")
        
        # Real-time metrics collection
        if st.button("🔄 Refresh Metrics"):
            st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🖥️ System Performance")
            metrics = get_system_metrics()
            
            if "error" not in metrics:
                # Create gauge charts
                fig_cpu = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=metrics['cpu_percent'],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "CPU Usage (%)"},
                    gauge={'axis': {'range': [None, 100]},
                           'bar': {'color': "darkblue"},
                           'steps': [{'range': [0, 50], 'color': "lightgray"},
                                    {'range': [50, 80], 'color': "yellow"},
                                    {'range': [80, 100], 'color': "red"}]}
                ))
                st.plotly_chart(fig_cpu, use_container_width=True)
                
                fig_memory = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=metrics['memory_percent'],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Memory Usage (%)"},
                    gauge={'axis': {'range': [None, 100]},
                           'bar': {'color': "darkblue"},
                           'steps': [{'range': [0, 50], 'color': "lightgray"},
                                    {'range': [50, 80], 'color': "yellow"},
                                    {'range': [80, 100], 'color': "red"}]}
                ))
                st.plotly_chart(fig_memory, use_container_width=True)
        
        with col2:
            st.subheader("🔧 Process Information")
            process_info = get_process_info()
            
            if "error" not in process_info:
                st.metric("Process Memory", f"{process_info['memory_mb']:.1f} MB")
                st.metric("Process CPU", f"{process_info['cpu_percent']:.1f}%")
                st.metric("Threads", process_info['num_threads'])
                st.metric("Open Files", process_info['open_files'])
                st.metric("Network Connections", process_info['connections'])
            else:
                st.error(f"Error getting process info: {process_info['error']}")
    
    elif section == "Project Status":
        st.header("📁 Project Status")
        
        project_info = get_project_info()
        
        # File structure
        st.subheader("📂 Project Structure")
        
        # Create a tree-like view
        tree_data = []
        for file_path, status in project_info['key_files'].items():
            tree_data.append({
                "File": file_path,
                "Status": "✅ Exists" if status['exists'] else "❌ Missing",
                "Size (KB)": f"{status['size_kb']:.1f}" if status['exists'] else "N/A",
                "Last Modified": status['modified'] if status['modified'] else "N/A"
            })
        
        df = pd.DataFrame(tree_data)
        st.dataframe(df, use_container_width=True)
        
        # Dependencies check
        st.subheader("📦 Dependencies Check")
        
        required_packages = [
            "streamlit", "pandas", "requests", "bs4", "selenium",
            "google.generativeai", "transformers", "plotly", "psutil"
        ]
        
        dep_status = []
        for package in required_packages:
            try:
                __import__(package)
                dep_status.append({"Package": package, "Status": "✅ Installed"})
            except ImportError:
                dep_status.append({"Package": package, "Status": "❌ Missing"})
        
        dep_df = pd.DataFrame(dep_status)
        st.dataframe(dep_df, use_container_width=True)
    
    elif section == "Component Tests":
        st.header("🧪 Component Tests")
        
        if st.button("🔍 Run Component Tests"):
            with st.spinner("Running component tests..."):
                results = test_core_components()
                
                st.subheader("📋 Test Results")
                for component, result in results.items():
                    if "✅" in result:
                        st.success(f"{component}: {result}")
                    else:
                        st.error(f"{component}: {result}")
                
                # Summary
                passed = sum(1 for r in results.values() if "✅" in r)
                total = len(results)
                st.metric("Test Results", f"{passed}/{total} Passed")
    
    elif section == "Real-time Monitoring":
        st.header("⏱️ Real-time Monitoring")
        
        # Auto-refresh every 5 seconds
        if st.button("🔄 Start Auto-refresh"):
            st.info("Auto-refresh would be implemented here")
        
        # Create a placeholder for real-time data
        placeholder = st.empty()
        
        # Simulate real-time updates
        for i in range(10):
            with placeholder.container():
                metrics = get_system_metrics()
                if "error" not in metrics:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("CPU", f"{metrics['cpu_percent']:.1f}%")
                    with col2:
                        st.metric("Memory", f"{metrics['memory_percent']:.1f}%")
                    with col3:
                        st.metric("Time", datetime.now().strftime("%H:%M:%S"))
                time.sleep(1)
    
    # Footer
    st.markdown("---")
    st.markdown("*Developer Dashboard - Built for debugging and monitoring*")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

if __name__ == "__main__":
    main()
