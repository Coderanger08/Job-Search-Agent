"""
System Validator for Bangladesh Job Search Agent
Validates system requirements, dependencies, and configurations
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging
import json
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemValidator:
    """Validates system requirements and configurations"""
    
    def __init__(self):
        self.required_packages = [
            "streamlit",
            "pandas",
            "requests",
            "bs4",
            "selenium",
            "google.generativeai",
            "transformers",
            "torch",
            "plotly",
            "psutil"
        ]
        
        self.optional_packages = [
            "yaml",
            "openai",
            "anthropic"
        ]
        
        self.required_files = [
            "config.py",
            "src/core/rag_engine.py",
            "src/core/query_parser.py",
            "src/interface/streamlit_app.py"
        ]
        
        self.validation_results = {}
    
    def validate_system(self) -> Dict[str, Any]:
        """Perform comprehensive system validation"""
        try:
            validation_result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "checks": {},
                "errors": [],
                "warnings": []
            }
            
            # Check Python version
            python_check = self._check_python_version()
            validation_result["checks"]["python_version"] = python_check
            if not python_check["valid"]:
                validation_result["success"] = False
                validation_result["errors"].append(python_check["message"])
            
            # Check required packages
            packages_check = self._check_required_packages()
            validation_result["checks"]["required_packages"] = packages_check
            if not packages_check["valid"]:
                validation_result["success"] = False
                validation_result["errors"].extend(packages_check["errors"])
            
            # Check optional packages
            optional_check = self._check_optional_packages()
            validation_result["checks"]["optional_packages"] = optional_check
            validation_result["warnings"].extend(optional_check["warnings"])
            
            # Check required files
            files_check = self._check_required_files()
            validation_result["checks"]["required_files"] = files_check
            if not files_check["valid"]:
                validation_result["success"] = False
                validation_result["errors"].extend(files_check["errors"])
            
            # Check system resources
            resources_check = self._check_system_resources()
            validation_result["checks"]["system_resources"] = resources_check
            if not resources_check["valid"]:
                validation_result["warnings"].extend(resources_check["warnings"])
            
            # Check internet connectivity
            internet_check = self._check_internet_connectivity()
            validation_result["checks"]["internet_connectivity"] = internet_check
            if not internet_check["valid"]:
                validation_result["warnings"].append(internet_check["message"])
            
            # Check API configurations
            api_check = self._check_api_configurations()
            validation_result["checks"]["api_configurations"] = api_check
            validation_result["warnings"].extend(api_check["warnings"])
            
            # Store validation results
            self.validation_results = validation_result
            
            logger.info(f"✅ System validation completed: {'SUCCESS' if validation_result['success'] else 'FAILED'}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"System validation failed: {e}")
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "checks": {},
                "errors": [f"Validation process failed: {e}"],
                "warnings": []
            }
    
    def _check_python_version(self) -> Dict[str, Any]:
        """Check Python version compatibility"""
        try:
            version = sys.version_info
            current_version = f"{version.major}.{version.minor}.{version.micro}"
            
            # Require Python 3.8 or higher
            if version.major == 3 and version.minor >= 8:
                return {
                    "valid": True,
                    "current_version": current_version,
                    "required_version": "3.8+",
                    "message": f"Python {current_version} is compatible"
                }
            else:
                return {
                    "valid": False,
                    "current_version": current_version,
                    "required_version": "3.8+",
                    "message": f"Python {current_version} is not compatible. Required: 3.8+"
                }
                
        except Exception as e:
            return {
                "valid": False,
                "current_version": "Unknown",
                "required_version": "3.8+",
                "message": f"Failed to check Python version: {e}"
            }
    
    def _check_required_packages(self) -> Dict[str, Any]:
        """Check if required packages are installed"""
        try:
            results = {
                "valid": True,
                "installed": [],
                "missing": [],
                "errors": []
            }
            
            for package in self.required_packages:
                try:
                    # Try to import the package
                    importlib.import_module(package)
                    results["installed"].append(package)
                except ImportError:
                    results["missing"].append(package)
                    results["valid"] = False
                    results["errors"].append(f"Missing required package: {package}")
                except Exception as e:
                    results["errors"].append(f"Error checking package {package}: {e}")
            
            return results
            
        except Exception as e:
            return {
                "valid": False,
                "installed": [],
                "missing": self.required_packages,
                "errors": [f"Failed to check packages: {e}"]
            }
    
    def _check_optional_packages(self) -> Dict[str, Any]:
        """Check optional packages"""
        try:
            results = {
                "installed": [],
                "missing": [],
                "warnings": []
            }
            
            for package in self.optional_packages:
                try:
                    importlib.import_module(package)
                    results["installed"].append(package)
                except ImportError:
                    results["missing"].append(package)
                    results["warnings"].append(f"Optional package not installed: {package}")
            
            return results
            
        except Exception as e:
            return {
                "installed": [],
                "missing": self.optional_packages,
                "warnings": [f"Failed to check optional packages: {e}"]
            }
    
    def _check_required_files(self) -> Dict[str, Any]:
        """Check if required files exist"""
        try:
            results = {
                "valid": True,
                "existing": [],
                "missing": [],
                "errors": []
            }
            
            for file_path in self.required_files:
                if Path(file_path).exists():
                    results["existing"].append(file_path)
                else:
                    results["missing"].append(file_path)
                    results["valid"] = False
                    results["errors"].append(f"Missing required file: {file_path}")
            
            return results
            
        except Exception as e:
            return {
                "valid": False,
                "existing": [],
                "missing": self.required_files,
                "errors": [f"Failed to check files: {e}"]
            }
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources"""
        try:
            import psutil
            
            results = {
                "valid": True,
                "warnings": [],
                "metrics": {}
            }
            
            # Check memory
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            results["metrics"]["memory_gb"] = memory_gb
            
            if memory_gb < 4:
                results["warnings"].append(f"Low memory: {memory_gb:.1f}GB (recommended: 4GB+)")
            
            # Check disk space
            disk = psutil.disk_usage('/')
            disk_gb = disk.free / (1024**3)
            results["metrics"]["disk_free_gb"] = disk_gb
            
            if disk_gb < 1:
                results["warnings"].append(f"Low disk space: {disk_gb:.1f}GB free (recommended: 1GB+)")
            
            # Check CPU cores
            cpu_cores = psutil.cpu_count()
            results["metrics"]["cpu_cores"] = cpu_cores
            
            if cpu_cores < 2:
                results["warnings"].append(f"Low CPU cores: {cpu_cores} (recommended: 2+)")
            
            return results
            
        except Exception as e:
            return {
                "valid": False,
                "warnings": [f"Failed to check system resources: {e}"],
                "metrics": {}
            }
    
    def _check_internet_connectivity(self) -> Dict[str, Any]:
        """Check internet connectivity"""
        try:
            # Test connection to multiple services
            test_urls = [
                "https://www.google.com",
                "https://api.github.com",
                "https://httpbin.org/get"
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        return {
                            "valid": True,
                            "tested_url": url,
                            "message": "Internet connectivity confirmed"
                        }
                except:
                    continue
            
            return {
                "valid": False,
                "tested_urls": test_urls,
                "message": "No internet connectivity detected"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Failed to check internet connectivity: {e}"
            }
    
    def _check_api_configurations(self) -> Dict[str, Any]:
        """Check API configurations"""
        try:
            results = {
                "warnings": [],
                "configurations": {}
            }
            
            # Check for .env file
            env_file = Path(".env")
            if env_file.exists():
                results["configurations"]["env_file"] = "Found"
            else:
                results["warnings"].append("No .env file found (API keys may not be configured)")
                results["configurations"]["env_file"] = "Missing"
            
            # Check for config directory
            config_dir = Path.home() / ".bangladesh_job_search"
            if config_dir.exists():
                results["configurations"]["config_dir"] = "Found"
            else:
                results["warnings"].append("Configuration directory not found (will be created on first run)")
                results["configurations"]["config_dir"] = "Missing"
            
            # Check environment variables
            env_vars = ["GEMINI_API_KEY", "HUGGINGFACE_API_KEY"]
            for var in env_vars:
                if os.getenv(var):
                    results["configurations"][var] = "Set"
                else:
                    results["configurations"][var] = "Not set"
                    results["warnings"].append(f"Environment variable {var} not set")
            
            return results
            
        except Exception as e:
            return {
                "warnings": [f"Failed to check API configurations: {e}"],
                "configurations": {}
            }
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results"""
        if not self.validation_results:
            return {"message": "No validation results available"}
        
        summary = {
            "overall_status": "SUCCESS" if self.validation_results["success"] else "FAILED",
            "total_checks": len(self.validation_results["checks"]),
            "errors": len(self.validation_results["errors"]),
            "warnings": len(self.validation_results["warnings"]),
            "timestamp": self.validation_results["timestamp"]
        }
        
        # Add check summaries
        for check_name, check_result in self.validation_results["checks"].items():
            if isinstance(check_result, dict) and "valid" in check_result:
                summary[f"{check_name}_status"] = "PASS" if check_result["valid"] else "FAIL"
        
        return summary
    
    def export_validation_report(self, file_path: str):
        """Export validation results to a file"""
        try:
            report = {
                "validation_results": self.validation_results,
                "summary": self.get_validation_summary(),
                "exported_at": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Validation report exported to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export validation report: {e}")
    
    def get_installation_instructions(self) -> List[str]:
        """Get installation instructions for missing components"""
        instructions = []
        
        if not self.validation_results:
            return ["Run system validation first"]
        
        # Check for missing packages
        if "required_packages" in self.validation_results["checks"]:
            packages_check = self.validation_results["checks"]["required_packages"]
            if not packages_check["valid"]:
                instructions.append("Install missing packages:")
                for package in packages_check["missing"]:
                    instructions.append(f"  pip install {package}")
        
        # Check for missing files
        if "required_files" in self.validation_results["checks"]:
            files_check = self.validation_results["checks"]["required_files"]
            if not files_check["valid"]:
                instructions.append("Missing required files. Please ensure all source files are present.")
        
        # Check for configuration issues
        if "api_configurations" in self.validation_results["checks"]:
            api_check = self.validation_results["checks"]["api_configurations"]
            if "env_file" in api_check["configurations"] and api_check["configurations"]["env_file"] == "Missing":
                instructions.append("Create .env file with your API keys:")
                instructions.append("  GEMINI_API_KEY=your_gemini_api_key")
                instructions.append("  HUGGINGFACE_API_KEY=your_huggingface_api_key")
        
        return instructions
    
    def validate_specific_component(self, component: str) -> Dict[str, Any]:
        """Validate a specific component"""
        try:
            if component == "python_version":
                return self._check_python_version()
            elif component == "required_packages":
                return self._check_required_packages()
            elif component == "optional_packages":
                return self._check_optional_packages()
            elif component == "required_files":
                return self._check_required_files()
            elif component == "system_resources":
                return self._check_system_resources()
            elif component == "internet_connectivity":
                return self._check_internet_connectivity()
            elif component == "api_configurations":
                return self._check_api_configurations()
            else:
                return {
                    "valid": False,
                    "error": f"Unknown component: {component}"
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to validate {component}: {e}"
            }
