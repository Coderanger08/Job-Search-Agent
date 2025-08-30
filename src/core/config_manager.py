"""
Configuration Manager for Bangladesh Job Search Agent
Handles all application settings, API keys, and user preferences
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigManager:
    """Centralized configuration management for the application"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".bangladesh_job_search"
        self.config_file = self.config_dir / "config.json"
        self.user_prefs_file = self.config_dir / "user_preferences.json"
        self.api_keys_file = self.config_dir / "api_keys.json"
        
        # Default configuration
        self.default_config = {
            "version": "1.0.0",
            "app_name": "Bangladesh Job Search Agent",
            "description": "AI-Powered Job Search with Real-time Data",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            
            # Application settings
            "app_settings": {
                "debug_mode": False,
                "log_level": "INFO",
                "max_search_results": 50,
                "search_timeout": 30,
                "enable_analytics": True,
                "enable_notifications": True,
                "auto_save_results": True
            },
            
            # UI settings
            "ui_settings": {
                "theme": "light",
                "language": "en",
                "default_location": "Dhaka",
                "default_job_type": "Any",
                "show_salary_info": True,
                "compact_view": False
            },
            
            # Search settings
            "search_settings": {
                "default_sources": ["BDJobs", "LinkedIn", "Indeed", "Web Search"],
                "enable_advanced_search": True,
                "enable_fuzzy_matching": True,
                "enable_deduplication": True,
                "min_salary_filter": 0,
                "max_salary_filter": 1000000
            },
            
            # Performance settings
            "performance_settings": {
                "max_concurrent_searches": 5,
                "cache_duration": 3600,  # 1 hour
                "enable_caching": True,
                "memory_limit_mb": 512,
                "enable_compression": True
            }
        }
        
        # Default user preferences
        self.default_user_prefs = {
            "recent_searches": [],
            "saved_jobs": [],
            "favorite_companies": [],
            "search_history": [],
            "filter_presets": {},
            "notification_settings": {
                "email_notifications": False,
                "browser_notifications": True,
                "job_alerts": True
            }
        }
        
        # API configuration template
        self.api_config_template = {
            "gemini_api_key": "",
            "huggingface_api_key": "",
            "linkedin_api_key": "",
            "indeed_api_key": "",
            "serpapi_key": "",
            "duckduckgo_enabled": True,
            "google_search_enabled": True
        }
        
        self.config = {}
        self.user_prefs = {}
        self.api_keys = {}
    
    def get_version(self) -> str:
        """Get application version"""
        return self.default_config["version"]
    
    def initialize_config_directory(self):
        """Initialize configuration directory and files"""
        try:
            # Create config directory
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Create config file if it doesn't exist
            if not self.config_file.exists():
                self.save_config(self.default_config)
            
            # Create user preferences file if it doesn't exist
            if not self.user_prefs_file.exists():
                self.save_user_preferences(self.default_user_prefs)
            
            # Create API keys file if it doesn't exist
            if not self.api_keys_file.exists():
                self.save_api_keys(self.api_config_template)
            
            logger.info(f"✅ Configuration directory initialized: {self.config_dir}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize config directory: {e}")
            raise
    
    def load_config(self) -> Dict[str, Any]:
        """Load application configuration"""
        try:
            self.initialize_config_directory()
            
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("✅ Configuration loaded successfully")
            else:
                self.config = self.default_config.copy()
                self.save_config(self.config)
                logger.info("✅ Default configuration created")
            
            return self.config
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            self.config = self.default_config.copy()
            return self.config
    
    def save_config(self, config: Dict[str, Any]):
        """Save application configuration"""
        try:
            config["last_updated"] = datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.config = config
            logger.info("✅ Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")
            raise
    
    def load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences"""
        try:
            if self.user_prefs_file.exists():
                with open(self.user_prefs_file, 'r', encoding='utf-8') as f:
                    self.user_prefs = json.load(f)
                logger.info("✅ User preferences loaded")
            else:
                self.user_prefs = self.default_user_prefs.copy()
                self.save_user_preferences(self.user_prefs)
                logger.info("✅ Default user preferences created")
            
            return self.user_prefs
            
        except Exception as e:
            logger.error(f"❌ Failed to load user preferences: {e}")
            self.user_prefs = self.default_user_prefs.copy()
            return self.user_prefs
    
    def save_user_preferences(self, prefs: Dict[str, Any]):
        """Save user preferences"""
        try:
            with open(self.user_prefs_file, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
            
            self.user_prefs = prefs
            logger.info("✅ User preferences saved")
            
        except Exception as e:
            logger.error(f"❌ Failed to save user preferences: {e}")
            raise
    
    def load_api_keys(self) -> Dict[str, Any]:
        """Load API keys configuration"""
        try:
            if self.api_keys_file.exists():
                with open(self.api_keys_file, 'r', encoding='utf-8') as f:
                    self.api_keys = json.load(f)
                logger.info("✅ API keys loaded")
            else:
                self.api_keys = self.api_config_template.copy()
                self.save_api_keys(self.api_keys)
                logger.info("✅ API keys template created")
            
            return self.api_keys
            
        except Exception as e:
            logger.error(f"❌ Failed to load API keys: {e}")
            self.api_keys = self.api_config_template.copy()
            return self.api_keys
    
    def save_api_keys(self, api_keys: Dict[str, Any]):
        """Save API keys configuration"""
        try:
            with open(self.api_keys_file, 'w', encoding='utf-8') as f:
                json.dump(api_keys, f, indent=2, ensure_ascii=False)
            
            self.api_keys = api_keys
            logger.info("✅ API keys saved")
            
        except Exception as e:
            logger.error(f"❌ Failed to save API keys: {e}")
            raise
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting"""
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"❌ Failed to get setting '{key}': {e}")
            return default
    
    def set_setting(self, key: str, value: Any):
        """Set a configuration setting"""
        try:
            keys = key.split('.')
            config = self.config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            # Save the updated configuration
            self.save_config(self.config)
            
            logger.info(f"✅ Setting '{key}' updated to: {value}")
            
        except Exception as e:
            logger.error(f"❌ Failed to set setting '{key}': {e}")
            raise
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        try:
            keys = key.split('.')
            value = self.user_prefs
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"❌ Failed to get user preference '{key}': {e}")
            return default
    
    def set_user_preference(self, key: str, value: Any):
        """Set a user preference"""
        try:
            keys = key.split('.')
            prefs = self.user_prefs
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in prefs:
                    prefs[k] = {}
                prefs = prefs[k]
            
            # Set the value
            prefs[keys[-1]] = value
            
            # Save the updated preferences
            self.save_user_preferences(self.user_prefs)
            
            logger.info(f"✅ User preference '{key}' updated to: {value}")
            
        except Exception as e:
            logger.error(f"❌ Failed to set user preference '{key}': {e}")
            raise
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service"""
        try:
            return self.api_keys.get(f"{service}_api_key", "")
        except Exception as e:
            logger.error(f"❌ Failed to get API key for '{service}': {e}")
            return None
    
    def set_api_key(self, service: str, api_key: str):
        """Set API key for a specific service"""
        try:
            self.api_keys[f"{service}_api_key"] = api_key
            self.save_api_keys(self.api_keys)
            logger.info(f"✅ API key for '{service}' updated")
            
        except Exception as e:
            logger.error(f"❌ Failed to set API key for '{service}': {e}")
            raise
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate API keys configuration"""
        validation_results = {}
        
        try:
            for service in ["gemini", "huggingface", "linkedin", "indeed", "serpapi"]:
                api_key = self.get_api_key(service)
                validation_results[service] = bool(api_key and len(api_key) > 10)
            
            logger.info(f"✅ API keys validation completed: {validation_results}")
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ API keys validation failed: {e}")
            return {}
    
    def export_config(self, file_path: str):
        """Export configuration to file"""
        try:
            export_data = {
                "config": self.config,
                "user_preferences": self.user_prefs,
                "api_keys": self.api_keys,
                "exported_at": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Configuration exported to: {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to export configuration: {e}")
            raise
    
    def import_config(self, file_path: str):
        """Import configuration from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if "config" in import_data:
                self.save_config(import_data["config"])
            
            if "user_preferences" in import_data:
                self.save_user_preferences(import_data["user_preferences"])
            
            if "api_keys" in import_data:
                self.save_api_keys(import_data["api_keys"])
            
            logger.info(f"✅ Configuration imported from: {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to import configuration: {e}")
            raise
    
    def reset_to_defaults(self):
        """Reset all configuration to defaults"""
        try:
            self.save_config(self.default_config.copy())
            self.save_user_preferences(self.default_user_prefs.copy())
            self.save_api_keys(self.api_config_template.copy())
            
            logger.info("✅ Configuration reset to defaults")
            
        except Exception as e:
            logger.error(f"❌ Failed to reset configuration: {e}")
            raise
