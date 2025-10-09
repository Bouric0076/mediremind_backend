import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json
from collections import deque, defaultdict
from supabase_client import supabase
from .logging_config import notification_logger, LogCategory
from .tasks import monitor_notification_health

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class Alert:
    """System alert"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    component: str
    metric_name: str
    threshold_value: float
    current_value: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data

class MetricsCollector:
    """Collects and stores system metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.metrics_history = deque(maxlen=max_history)
        self.current_metrics = {}
        self.counters = defaultdict(float)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.timers = defaultdict(list)
        self.lock = threading.Lock()
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            self.counters[name] += value
            metric = Metric(name, self.counters[name], MetricType.COUNTER, datetime.now(), tags)
            self._store_metric(metric)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            self.gauges[name] = value
            metric = Metric(name, value, MetricType.GAUGE, datetime.now(), tags)
            self._store_metric(metric)
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        with self.lock:
            self.histograms[name].append(value)
            # Keep only last 100 values
            if len(self.histograms[name]) > 100:
                self.histograms[name] = self.histograms[name][-100:]
            
            metric = Metric(name, value, MetricType.HISTOGRAM, datetime.now(), tags)
            self._store_metric(metric)
    
    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None):
        """Record a timer value (in milliseconds)"""
        with self.lock:
            self.timers[name].append(duration)
            # Keep only last 100 values
            if len(self.timers[name]) > 100:
                self.timers[name] = self.timers[name][-100:]
            
            metric = Metric(name, duration, MetricType.TIMER, datetime.now(), tags)
            self._store_metric(metric)
    
    def _store_metric(self, metric: Metric):
        """Store metric in history and current metrics"""
        self.metrics_history.append(metric)
        self.current_metrics[metric.name] = metric
    
    def get_metric_summary(self, name: str) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        with self.lock:
            if name in self.histograms and self.histograms[name]:
                values = self.histograms[name]
                return {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'latest': values[-1]
                }
            elif name in self.timers and self.timers[name]:
                values = self.timers[name]
                return {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'latest': values[-1]
                }
            elif name in self.gauges:
                return {
                    'current': self.gauges[name]
                }
            elif name in self.counters:
                return {
                    'total': self.counters[name]
                }
            else:
                return {}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        with self.lock:
            return {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {k: self.get_metric_summary(k) for k in self.histograms},
                'timers': {k: self.get_metric_summary(k) for k in self.timers},
                'timestamp': datetime.now().isoformat()
            }

class SystemMonitor:
    """Monitors system resources and health"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 30  # seconds
    
    def start_monitoring(self):
        """Start system monitoring via Celery Beat (no internal loop)"""
        # No-op: monitoring is handled by Celery beat task monitor_notification_health
        notification_logger.info(
            LogCategory.SYSTEM,
            "System monitoring scheduled via Celery beat",
            "system_monitor"
        )
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        # No-op: Celery beat controls scheduling
        notification_logger.info(
            LogCategory.SYSTEM,
            "System monitoring stop requested (managed by Celery beat)",
            "system_monitor"
        )

class AlertManager:
    """Manages alerts based on system metrics"""
    
    def start_alert_checking(self):
        """Start alert checking (disabled, handled by Celery beat)"""
        notification_logger.info(
            LogCategory.SYSTEM,
            "Alert checking managed by Celery beat (no internal thread)",
            "alert_manager"
        )
    
    def stop_alert_checking(self):
        """Stop alert checking (no-op)"""
        notification_logger.info(
            LogCategory.SYSTEM,
            "Alert checking stop requested (managed by Celery beat)",
            "alert_manager"
        )
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alerts = {}
        self.thresholds = {
            'system.cpu.usage_percent': {'critical': 90, 'high': 80, 'medium': 70},
            'system.memory.usage_percent': {'critical': 95, 'high': 85, 'medium': 75},
            'system.disk.usage_percent': {'critical': 95, 'high': 90, 'medium': 80},
            'queue.error_rate': {'critical': 10, 'high': 5, 'medium': 2},
            'notification.failure_rate': {'critical': 20, 'high': 10, 'medium': 5},
            'api.response_time_ms': {'critical': 5000, 'high': 3000, 'medium': 1000},
            'scheduler.task_backlog': {'critical': 1000, 'high': 500, 'medium': 200}
        }
        self.check_interval = 60  # seconds
        self.checking = False
        self.check_thread = None
    
    def _check_loop(self):
        """Disabled: Celery beat handles periodic checks"""
        pass
    
    def _check_thresholds(self):
        """Check all metrics against thresholds"""
        current_metrics = self.metrics.get_all_metrics()
        
        for metric_name, thresholds in self.thresholds.items():
            current_value = self._get_metric_value(metric_name, current_metrics)
            if current_value is None:
                continue
            
            # Check each threshold level
            for severity_str, threshold in thresholds.items():
                severity = AlertSeverity(severity_str)
                alert_id = f"{metric_name}_{severity_str}"
                
                if self._should_trigger_alert(metric_name, current_value, threshold, severity):
                    self._trigger_alert(alert_id, metric_name, current_value, threshold, severity)
                elif alert_id in self.alerts and not self.alerts[alert_id].resolved:
                    self._resolve_alert(alert_id)
    
    def _get_metric_value(self, metric_name: str, metrics: Dict[str, Any]) -> Optional[float]:
        """Extract metric value from metrics dictionary"""
        parts = metric_name.split('.')
        
        if parts[0] in metrics:
            metric_data = metrics[parts[0]]
            if isinstance(metric_data, dict):
                # Navigate through nested structure
                current = metric_data
                for part in parts[1:]:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return None
                
                # Handle different metric types
                if isinstance(current, dict):
                    return current.get('current') or current.get('latest') or current.get('avg')
                else:
                    return current
        
        return None
    
    def _should_trigger_alert(self, metric_name: str, current_value: float, 
                             threshold: float, severity: AlertSeverity) -> bool:
        """Determine if an alert should be triggered"""
        # Different logic for different metrics
        if 'usage_percent' in metric_name or 'error_rate' in metric_name or 'failure_rate' in metric_name:
            return current_value >= threshold
        elif 'response_time' in metric_name or 'backlog' in metric_name:
            return current_value >= threshold
        else:
            return current_value >= threshold
    
    def _trigger_alert(self, alert_id: str, metric_name: str, current_value: float,
                      threshold: float, severity: AlertSeverity):
        """Trigger a new alert"""
        if alert_id in self.alerts and not self.alerts[alert_id].resolved:
            return  # Alert already active
        
        alert = Alert(
            id=alert_id,
            title=f"{metric_name} threshold exceeded",
            description=f"{metric_name} is {current_value}, exceeding {severity.value} threshold of {threshold}",
            severity=severity,
            component=metric_name.split('.')[0],
            metric_name=metric_name,
            threshold_value=threshold,
            current_value=current_value,
            timestamp=datetime.now()
        )
        
        self.alerts[alert_id] = alert
        
        # Log the alert
        notification_logger.warning(
            LogCategory.SYSTEM,
            f"Alert triggered: {alert.title}",
            "alert_manager",
            metadata=alert.to_dict()
        )
        
        # Store alert in database
        try:
            supabase.table('system_alerts').insert(alert.to_dict()).execute()
        except Exception as e:
            notification_logger.error(
                LogCategory.SYSTEM,
                f"Failed to store alert in database: {str(e)}",
                "alert_manager"
            )
    
    def _resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id not in self.alerts or self.alerts[alert_id].resolved:
            return
        
        alert = self.alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.now()
        
        notification_logger.info(
            LogCategory.SYSTEM,
            f"Alert resolved: {alert.title}",
            "alert_manager",
            metadata=alert.to_dict()
        )
        
        # Update alert in database
        try:
            supabase.table('system_alerts').update({
                'resolved': True,
                'resolved_at': alert.resolved_at.isoformat()
            }).eq('id', alert_id).execute()
        except Exception as e:
            notification_logger.error(
                LogCategory.SYSTEM,
                f"Failed to update alert in database: {str(e)}",
                "alert_manager"
            )
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        active_alerts = self.get_active_alerts()
        
        severity_counts = defaultdict(int)
        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
        
        return {
            'total_active': len(active_alerts),
            'by_severity': dict(severity_counts),
            'alerts': [alert.to_dict() for alert in active_alerts]
        }

class HealthChecker:
    """Performs health checks on system components"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        start_time = time.time()
        try:
            # Simple query to test connectivity
            result = supabase.table('users').select('id').limit(1).execute()
            duration = (time.time() - start_time) * 1000
            
            self.metrics.record_timer('database.health_check_ms', duration)
            
            return {
                'status': 'healthy',
                'response_time_ms': duration,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.metrics.record_timer('database.health_check_ms', duration)
            
            notification_logger.error(
                LogCategory.DATABASE,
                f"Database health check failed: {str(e)}",
                "health_checker",
                error_details=str(e)
            )
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': duration,
                'timestamp': datetime.now().isoformat()
            }
    
    def check_scheduler_health(self) -> Dict[str, Any]:
        """Check scheduler health"""
        try:
            from .scheduler import scheduler
            
            return {
                'status': 'healthy' if scheduler.is_running else 'unhealthy',
                'is_running': scheduler.is_running,
                'active_tasks': len(scheduler.scheduled_tasks),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            notification_logger.error(
                LogCategory.SCHEDULER,
                f"Scheduler health check failed: {str(e)}",
                "health_checker",
                error_details=str(e)
            )
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_queue_health(self) -> Dict[str, Any]:
        """Check queue manager health"""
        try:
            from .queue_manager import queue_manager
            
            queue_status = queue_manager.get_queue_status()
            
            return {
                'status': 'healthy' if queue_manager.is_running else 'unhealthy',
                'is_running': queue_manager.is_running,
                'queue_status': queue_status,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            notification_logger.error(
                LogCategory.QUEUE,
                f"Queue health check failed: {str(e)}",
                "health_checker",
                error_details=str(e)
            )
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def perform_full_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        checks = {
            'database': self.check_database_health(),
            'scheduler': self.check_scheduler_health(),
            'queue_manager': self.check_queue_health()
        }
        
        # Calculate overall health
        healthy_components = sum(1 for check in checks.values() if check['status'] == 'healthy')
        total_components = len(checks)
        health_percentage = (healthy_components / total_components) * 100
        
        overall_status = 'healthy' if health_percentage == 100 else \
                        'degraded' if health_percentage >= 50 else 'unhealthy'
        
        return {
            'overall_status': overall_status,
            'health_percentage': health_percentage,
            'components': checks,
            'timestamp': datetime.now().isoformat()
        }

# Global instances
metrics_collector = MetricsCollector()
system_monitor = SystemMonitor(metrics_collector)
alert_manager = AlertManager(metrics_collector)
health_checker = HealthChecker(metrics_collector)

# Convenience functions
def start_monitoring():
    """Start all monitoring services"""
    system_monitor.start_monitoring()
    alert_manager.start_alert_checking()

def stop_monitoring():
    """Stop all monitoring services"""
    system_monitor.stop_monitoring()
    alert_manager.stop_alert_checking()

def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status"""
    return {
        'health': health_checker.perform_full_health_check(),
        'metrics': metrics_collector.get_all_metrics(),
        'alerts': alert_manager.get_alert_summary(),
        'timestamp': datetime.now().isoformat()
    }

__all__ = [
    'MetricsCollector', 'SystemMonitor', 'AlertManager', 'HealthChecker',
    'metrics_collector', 'system_monitor', 'alert_manager', 'health_checker',
    'start_monitoring', 'stop_monitoring', 'get_system_status'
]