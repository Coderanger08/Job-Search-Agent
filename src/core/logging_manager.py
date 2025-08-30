"""
Logging Manager for Bangladesh Job Search Agent
Handles comprehensive logging, error tracking, and performance monitoring
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
import json
import traceback
from typing import Dict, Any, Optional
import threading
import time

class LoggingManager:
    """Centralized logging management for the application"""
    
    def __init__(self):
        self.log_dir = Path.home() / ".bangladesh_job_search" / "logs"
        self.log_file = self.log_dir / "app.log"
        self.error_log_file = self.log_dir / "errors.log"
        self.performance_log_file = self.log_dir / "performance.log"
        self.analytics_log_file = self.log_dir / "analytics.log"
        
        self.logger = None
        self.error_logger = None
        self.performance_logger = None
        self.analytics_logger = None
        
        # Performance tracking
        self.performance_metrics = {
            "search_times": [],
            "api_calls": {},
            "error_counts": {},
            "user_actions": []
        }
        
        # Thread safety
        self.lock = threading.Lock()
    
    def initialize(self, log_level: str = "INFO"):
        """Initialize the logging system"""
        try:
            # Create log directory
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Set up main logger
            self.logger = self._setup_logger(
                "bangladesh_job_search",
                self.log_file,
                log_level
            )
            
            # Set up error logger
            self.error_logger = self._setup_logger(
                "bangladesh_job_search_errors",
                self.error_log_file,
                "ERROR"
            )
            
            # Set up performance logger
            self.performance_logger = self._setup_logger(
                "bangladesh_job_search_performance",
                self.performance_log_file,
                "INFO"
            )
            
            # Set up analytics logger
            self.analytics_logger = self._setup_logger(
                "bangladesh_job_search_analytics",
                self.analytics_log_file,
                "INFO"
            )
            
            self.log_info("🚀 Logging system initialized successfully")
            self.log_info(f"📁 Log directory: {self.log_dir}")
            
        except Exception as e:
            print(f"❌ Failed to initialize logging: {e}")
            # Fallback to basic logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("bangladesh_job_search")
    
    def _setup_logger(self, name: str, log_file: Path, level: str) -> logging.Logger:
        """Set up a logger with file and console handlers"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_info(self, message: str):
        """Log an info message"""
        if self.logger:
            self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log a warning message"""
        if self.logger:
            self.logger.warning(message)
    
    def log_error(self, message: str, exception: Optional[Exception] = None):
        """Log an error message with optional exception details"""
        if self.logger:
            self.logger.error(message)
        
        if self.error_logger:
            error_details = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "exception": str(exception) if exception else None,
                "traceback": traceback.format_exc() if exception else None
            }
            self.error_logger.error(json.dumps(error_details))
    
    def log_debug(self, message: str):
        """Log a debug message"""
        if self.logger:
            self.logger.debug(message)
    
    def log_performance(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """Log performance metrics"""
        if self.performance_logger:
            performance_data = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "duration_seconds": duration,
                "details": details or {}
            }
            self.performance_logger.info(json.dumps(performance_data))
        
        # Store in memory for analytics
        with self.lock:
            self.performance_metrics["search_times"].append({
                "operation": operation,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })
    
    def log_analytics(self, event_type: str, data: Dict[str, Any]):
        """Log analytics events"""
        if self.analytics_logger:
            analytics_data = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "data": data
            }
            self.analytics_logger.info(json.dumps(analytics_data))
        
        # Store in memory
        with self.lock:
            self.performance_metrics["user_actions"].append(analytics_data)
    
    def log_api_call(self, service: str, endpoint: str, duration: float, success: bool):
        """Log API call details"""
        api_data = {
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "endpoint": endpoint,
            "duration_seconds": duration,
            "success": success
        }
        
        if self.performance_logger:
            self.performance_logger.info(f"API_CALL: {json.dumps(api_data)}")
        
        # Store in memory
        with self.lock:
            if service not in self.performance_metrics["api_calls"]:
                self.performance_metrics["api_calls"][service] = []
            self.performance_metrics["api_calls"][service].append(api_data)
    
    def log_search_query(self, query: str, results_count: int, duration: float):
        """Log search query details"""
        search_data = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "results_count": results_count,
            "duration_seconds": duration
        }
        
        self.log_analytics("search_query", search_data)
        self.log_performance("search_query", duration, {"results_count": results_count})
    
    def log_user_action(self, action: str, details: Dict[str, Any] = None):
        """Log user actions"""
        action_data = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details or {}
        }
        
        self.log_analytics("user_action", action_data)
    
    def log_system_event(self, event: str, details: Dict[str, Any] = None):
        """Log system events"""
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "details": details or {}
        }
        
        self.log_info(f"SYSTEM_EVENT: {event}")
        self.log_analytics("system_event", event_data)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        with self.lock:
            # Calculate search performance
            search_times = [item["duration"] for item in self.performance_metrics["search_times"]]
            avg_search_time = sum(search_times) / len(search_times) if search_times else 0
            
            # Calculate API performance
            api_stats = {}
            for service, calls in self.performance_metrics["api_calls"].items():
                durations = [call["duration_seconds"] for call in calls]
                success_count = sum(1 for call in calls if call["success"])
                api_stats[service] = {
                    "total_calls": len(calls),
                    "success_rate": success_count / len(calls) if calls else 0,
                    "avg_duration": sum(durations) / len(durations) if durations else 0
                }
            
            # Calculate error statistics
            error_stats = {}
            for error_type, count in self.performance_metrics["error_counts"].items():
                error_stats[error_type] = count
            
            return {
                "avg_search_time": avg_search_time,
                "total_searches": len(search_times),
                "api_statistics": api_stats,
                "error_statistics": error_stats,
                "total_user_actions": len(self.performance_metrics["user_actions"])
            }
    
    def export_logs(self, export_path: str):
        """Export all logs to a file"""
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "performance_metrics": self.performance_metrics,
                "performance_summary": self.get_performance_summary()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.log_info(f"✅ Logs exported to: {export_path}")
            
        except Exception as e:
            self.log_error(f"Failed to export logs: {e}")
    
    def clear_old_logs(self, days_to_keep: int = 30):
        """Clear old log files"""
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            
            for log_file in self.log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.log_info(f"Deleted old log file: {log_file}")
            
            self.log_info(f"✅ Old logs cleared (kept last {days_to_keep} days)")
            
        except Exception as e:
            self.log_error(f"Failed to clear old logs: {e}")
    
    def get_log_file_paths(self) -> Dict[str, str]:
        """Get paths to all log files"""
        return {
            "main_log": str(self.log_file),
            "error_log": str(self.error_log_file),
            "performance_log": str(self.performance_log_file),
            "analytics_log": str(self.analytics_log_file)
        }
    
    def log_startup(self):
        """Log application startup"""
        startup_data = {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "platform": sys.platform,
            "log_directory": str(self.log_dir)
        }
        
        self.log_system_event("application_startup", startup_data)
    
    def log_shutdown(self):
        """Log application shutdown"""
        shutdown_data = {
            "timestamp": datetime.now().isoformat(),
            "performance_summary": self.get_performance_summary()
        }
        
        self.log_system_event("application_shutdown", shutdown_data)
    
    def set_log_level(self, level: str):
        """Set the logging level"""
        try:
            log_level = getattr(logging, level.upper())
            
            if self.logger:
                self.logger.setLevel(log_level)
                for handler in self.logger.handlers:
                    handler.setLevel(log_level)
            
            self.log_info(f"✅ Log level set to: {level}")
            
        except Exception as e:
            self.log_error(f"Failed to set log level: {e}")
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get log file statistics"""
        try:
            stats = {}
            
            for log_file in self.log_dir.glob("*.log"):
                if log_file.exists():
                    stats[log_file.name] = {
                        "size_bytes": log_file.stat().st_size,
                        "size_mb": log_file.stat().st_size / (1024 * 1024),
                        "last_modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                    }
            
            return stats
            
        except Exception as e:
            self.log_error(f"Failed to get log statistics: {e}")
            return {}
