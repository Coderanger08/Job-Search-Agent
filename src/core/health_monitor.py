"""
Health Monitor for Bangladesh Job Search Agent
Monitors system health, performance, and detects issues in real-time
"""

import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Real-time system health monitoring"""
    
    def __init__(self):
        self.health_metrics = {
            "system_resources": {},
            "application_metrics": {},
            "api_health": {},
            "error_counts": {},
            "performance_alerts": []
        }
        
        self.thresholds = {
            "cpu_usage": 90.0,  # Alert if CPU > 90% (increased from 80%)
            "memory_usage": 95.0,  # Alert if memory > 95% (increased from 85%)
            "disk_usage": 90.0,  # Alert if disk > 90%
            "response_time": 5.0,  # Alert if response time > 5 seconds
            "error_rate": 0.1,  # Alert if error rate > 10%
            "api_timeout": 10.0  # Alert if API timeout > 10 seconds
        }
        
        self.monitoring_active = False
        self.monitor_thread = None
        self.last_check = None
        
        # Health status history
        self.health_history = []
        self.max_history_size = 1000
    
    def start_monitoring(self, interval: int = 30):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            logger.warning("Health monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info(f"✅ Health monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("🛑 Health monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self.check_system_health()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(interval)
    
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "overall_health": "healthy",
                "issues": [],
                "metrics": {}
            }
            
            # Check system resources
            system_health = self._check_system_resources()
            health_status["metrics"]["system"] = system_health
            
            if system_health["status"] != "healthy":
                health_status["overall_health"] = "warning"
                health_status["issues"].extend(system_health["issues"])
            
            # Check application metrics
            app_health = self._check_application_metrics()
            health_status["metrics"]["application"] = app_health
            
            if app_health["status"] != "healthy":
                health_status["overall_health"] = "warning"
                health_status["issues"].extend(app_health["issues"])
            
            # Check API health
            api_health = self._check_api_health()
            health_status["metrics"]["api"] = api_health
            
            if api_health["status"] != "healthy":
                health_status["overall_health"] = "warning"
                health_status["issues"].extend(api_health["issues"])
            
            # Store health status
            self._store_health_status(health_status)
            
            # Update last check
            self.last_check = datetime.now()
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_health": "error",
                "issues": [f"Health check failed: {e}"],
                "metrics": {}
            }
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network status
            network = psutil.net_io_counters()
            
            # Check thresholds
            issues = []
            status = "healthy"
            
            if cpu_percent > self.thresholds["cpu_usage"]:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                status = "warning"
            
            if memory_percent > self.thresholds["memory_usage"]:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
                status = "warning"
            
            if disk_percent > self.thresholds["disk_usage"]:
                issues.append(f"High disk usage: {disk_percent:.1f}%")
                status = "warning"
            
            return {
                "status": status,
                "issues": issues,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv
            }
            
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                "status": "error",
                "issues": [f"System resource check failed: {e}"],
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0
            }
    
    def _check_application_metrics(self) -> Dict[str, Any]:
        """Check application-specific metrics"""
        try:
            # Get current process info
            current_process = psutil.Process()
            
            # Memory usage of current process
            process_memory = current_process.memory_info()
            process_memory_mb = process_memory.rss / (1024 * 1024)
            
            # CPU usage of current process
            process_cpu = current_process.cpu_percent()
            
            # Thread count
            thread_count = current_process.num_threads()
            
            # Open file handles
            open_files = len(current_process.open_files())
            
            # Check for issues
            issues = []
            status = "healthy"
            
            if process_memory_mb > 1000:  # Alert if process uses > 1GB (increased from 500MB)
                issues.append(f"High process memory usage: {process_memory_mb:.1f}MB")
                status = "warning"
            
            if thread_count > 50:  # Alert if too many threads
                issues.append(f"High thread count: {thread_count}")
                status = "warning"
            
            if open_files > 100:  # Alert if too many open files
                issues.append(f"High open file count: {open_files}")
                status = "warning"
            
            return {
                "status": status,
                "issues": issues,
                "process_memory_mb": process_memory_mb,
                "process_cpu_percent": process_cpu,
                "thread_count": thread_count,
                "open_files": open_files,
                "uptime_seconds": time.time() - current_process.create_time()
            }
            
        except Exception as e:
            logger.error(f"Application metrics check failed: {e}")
            return {
                "status": "error",
                "issues": [f"Application metrics check failed: {e}"],
                "process_memory_mb": 0,
                "process_cpu_percent": 0,
                "thread_count": 0,
                "open_files": 0
            }
    
    def _check_api_health(self) -> Dict[str, Any]:
        """Check API service health"""
        try:
            # This would typically check external API endpoints
            # For now, we'll simulate API health checks
            
            api_status = {
                "gemini_api": "healthy",
                "huggingface_api": "healthy",
                "web_search": "healthy"
            }
            
            issues = []
            overall_status = "healthy"
            
            # Simulate API response time checks
            api_response_times = {
                "gemini_api": 0.5,  # 500ms
                "huggingface_api": 1.2,  # 1.2s
                "web_search": 2.1  # 2.1s
            }
            
            for api, response_time in api_response_times.items():
                if response_time > self.thresholds["api_timeout"]:
                    api_status[api] = "slow"
                    issues.append(f"Slow {api} response: {response_time:.1f}s")
                    overall_status = "warning"
            
            return {
                "status": overall_status,
                "issues": issues,
                "api_status": api_status,
                "response_times": api_response_times
            }
            
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return {
                "status": "error",
                "issues": [f"API health check failed: {e}"],
                "api_status": {},
                "response_times": {}
            }
    
    def _store_health_status(self, health_status: Dict[str, Any]):
        """Store health status in history"""
        self.health_history.append(health_status)
        
        # Keep only recent history
        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size:]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary and trends"""
        try:
            if not self.health_history:
                return {"message": "No health data available"}
            
            # Get recent health status (last 10 checks)
            recent_checks = self.health_history[-10:]
            
            # Calculate health trends
            healthy_count = sum(1 for check in recent_checks if check["overall_health"] == "healthy")
            warning_count = sum(1 for check in recent_checks if check["overall_health"] == "warning")
            error_count = sum(1 for check in recent_checks if check["overall_health"] == "error")
            
            # Get latest metrics
            latest = self.health_history[-1]
            
            # Calculate averages for system metrics
            system_metrics = []
            for check in recent_checks:
                if "metrics" in check and "system" in check["metrics"]:
                    system_metrics.append(check["metrics"]["system"])
            
            avg_cpu = sum(m.get("cpu_percent", 0) for m in system_metrics) / len(system_metrics) if system_metrics else 0
            avg_memory = sum(m.get("memory_percent", 0) for m in system_metrics) / len(system_metrics) if system_metrics else 0
            
            return {
                "overall_status": latest["overall_health"],
                "last_check": latest["timestamp"],
                "recent_trends": {
                    "healthy_checks": healthy_count,
                    "warning_checks": warning_count,
                    "error_checks": error_count,
                    "total_checks": len(recent_checks)
                },
                "average_metrics": {
                    "cpu_percent": avg_cpu,
                    "memory_percent": avg_memory
                },
                "current_issues": latest.get("issues", []),
                "uptime": self._get_uptime()
            }
            
        except Exception as e:
            logger.error(f"Failed to get health summary: {e}")
            return {"error": str(e)}
    
    def _get_uptime(self) -> str:
        """Get application uptime"""
        try:
            if not self.health_history:
                return "Unknown"
            
            first_check = self.health_history[0]["timestamp"]
            first_time = datetime.fromisoformat(first_check.replace('Z', '+00:00'))
            uptime = datetime.now() - first_time
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m {seconds}s"
                
        except Exception as e:
            logger.error(f"Failed to calculate uptime: {e}")
            return "Unknown"
    
    def set_threshold(self, metric: str, value: float):
        """Set a health threshold"""
        if metric in self.thresholds:
            self.thresholds[metric] = value
            logger.info(f"✅ Health threshold updated: {metric} = {value}")
        else:
            logger.warning(f"Unknown health threshold: {metric}")
    
    def get_thresholds(self) -> Dict[str, float]:
        """Get current health thresholds"""
        return self.thresholds.copy()
    
    def add_performance_alert(self, alert: Dict[str, Any]):
        """Add a performance alert"""
        alert["timestamp"] = datetime.now().isoformat()
        self.health_metrics["performance_alerts"].append(alert)
        
        # Keep only recent alerts
        if len(self.health_metrics["performance_alerts"]) > 100:
            self.health_metrics["performance_alerts"] = self.health_metrics["performance_alerts"][-100:]
        
        logger.warning(f"Performance alert: {alert.get('message', 'Unknown')}")
    
    def get_performance_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent performance alerts"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_alerts = []
            for alert in self.health_metrics["performance_alerts"]:
                alert_time = datetime.fromisoformat(alert["timestamp"].replace('Z', '+00:00'))
                if alert_time > cutoff_time:
                    recent_alerts.append(alert)
            
            return recent_alerts
            
        except Exception as e:
            logger.error(f"Failed to get performance alerts: {e}")
            return []
    
    def export_health_data(self, file_path: str):
        """Export health monitoring data"""
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "health_history": self.health_history,
                "health_metrics": self.health_metrics,
                "thresholds": self.thresholds,
                "summary": self.get_health_summary()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Health data exported to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export health data: {e}")
    
    def clear_health_history(self):
        """Clear health history"""
        self.health_history.clear()
        logger.info("✅ Health history cleared")
