#!/usr/bin/env python3
"""
Enhanced Metrics Collector for MyRVM Platform Integration
Comprehensive metrics collection and aggregation
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil
import sqlite3

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from performance_monitor import PerformanceMonitor

class MetricsCollector:
    """Enhanced metrics collection and aggregation system"""
    
    def __init__(self, config: Dict):
        """
        Initialize metrics collector
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Metrics configuration
        self.collection_interval = config.get('metrics_collection_interval', 30)
        self.retention_days = config.get('metrics_retention_days', 30)
        self.aggregation_intervals = config.get('aggregation_intervals', [300, 3600, 86400])  # 5min, 1hour, 1day
        
        # Database configuration
        self.db_path = Path(__file__).parent.parent / 'data' / 'metrics.db'
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize performance monitor
        self.performance_monitor = PerformanceMonitor(config)
        
        # Metrics collection thread
        self.collection_thread = None
        self.is_running = False
        
        # Custom metrics
        self.custom_metrics = {}
        self.business_metrics = {}
        
        # Initialize database
        self._init_database()
        
        # Load metrics configuration
        self._load_metrics_config()
        
        self.logger.info("Enhanced metrics collector initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for metrics collector"""
        logger = logging.getLogger('MetricsCollector')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'metrics_collector_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _init_database(self):
        """Initialize metrics database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_type TEXT NOT NULL,
                        tags TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create aggregated metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aggregated_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        metric_name TEXT NOT NULL,
                        aggregation_type TEXT NOT NULL,
                        aggregation_interval INTEGER NOT NULL,
                        min_value REAL,
                        max_value REAL,
                        avg_value REAL,
                        sum_value REAL,
                        count_value INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_aggregated_timestamp ON aggregated_metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_aggregated_name ON aggregated_metrics(metric_name)')
                
                conn.commit()
                
            self.logger.info("Metrics database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics database: {e}")
            raise
    
    def _load_metrics_config(self):
        """Load metrics configuration from file"""
        config_file = Path(__file__).parent / 'config' / 'metrics.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                self.custom_metrics = config_data.get('custom_metrics', {})
                self.business_metrics = config_data.get('business_metrics', {})
                
                self.logger.info("Metrics configuration loaded from file")
            except Exception as e:
                self.logger.error(f"Failed to load metrics configuration: {e}")
        else:
            # Create default configuration
            self._save_metrics_config()
    
    def _save_metrics_config(self):
        """Save metrics configuration to file"""
        try:
            config_file = Path(__file__).parent / 'config' / 'metrics.json'
            config_file.parent.mkdir(exist_ok=True)
            
            config_data = {
                'custom_metrics': self.custom_metrics,
                'business_metrics': self.business_metrics,
                'collection_interval': self.collection_interval,
                'retention_days': self.retention_days,
                'aggregation_intervals': self.aggregation_intervals
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info("Metrics configuration saved to file")
            
        except Exception as e:
            self.logger.error(f"Failed to save metrics configuration: {e}")
    
    def collect_system_metrics(self) -> Dict:
        """Collect system metrics"""
        try:
            # Get system metrics from performance monitor
            system_metrics = self.performance_monitor.get_system_metrics()
            
            # Add additional system metrics
            additional_metrics = {
                'boot_time': psutil.boot_time(),
                'users': len(psutil.users()),
                'processes': len(psutil.pids()),
                'network_connections': len(psutil.net_connections()),
                'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            }
            
            system_metrics.update(additional_metrics)
            
            return system_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return {}
    
    def collect_application_metrics(self) -> Dict:
        """Collect application-specific metrics"""
        try:
            # Get performance summary
            performance_summary = self.performance_monitor.get_performance_summary()
            
            # Extract application metrics
            app_metrics = {
                'processing_time': performance_summary.get('current', {}).get('processing_time', 0),
                'throughput': performance_summary.get('current', {}).get('throughput', 0),
                'error_rate': performance_summary.get('current', {}).get('error_rate', 0),
                'queue_size': performance_summary.get('current', {}).get('queue_size', 0),
                'active_connections': performance_summary.get('current', {}).get('active_connections', 0)
            }
            
            return app_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect application metrics: {e}")
            return {}
    
    def collect_business_metrics(self) -> Dict:
        """Collect business-specific metrics"""
        try:
            # This would be populated with actual business metrics
            # For now, return sample data
            business_metrics = {
                'images_processed_total': 1234,
                'detections_made_total': 5678,
                'accuracy_rate': 94.2,
                'processing_volume_mb': 123.45,
                'user_sessions': 89,
                'api_requests_total': 9876,
                'success_rate': 98.5
            }
            
            return business_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect business metrics: {e}")
            return {}
    
    def collect_custom_metrics(self) -> Dict:
        """Collect custom metrics"""
        try:
            custom_metrics = {}
            
            # Process custom metrics from configuration
            for metric_name, metric_config in self.custom_metrics.items():
                try:
                    # This is a simplified implementation
                    # In production, you'd have more sophisticated metric collection
                    if metric_config.get('type') == 'counter':
                        custom_metrics[metric_name] = self._get_counter_metric(metric_name)
                    elif metric_config.get('type') == 'gauge':
                        custom_metrics[metric_name] = self._get_gauge_metric(metric_name)
                    elif metric_config.get('type') == 'histogram':
                        custom_metrics[metric_name] = self._get_histogram_metric(metric_name)
                        
                except Exception as e:
                    self.logger.error(f"Failed to collect custom metric {metric_name}: {e}")
            
            return custom_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect custom metrics: {e}")
            return {}
    
    def _get_counter_metric(self, metric_name: str) -> float:
        """Get counter metric value"""
        # Simplified implementation
        return 0.0
    
    def _get_gauge_metric(self, metric_name: str) -> float:
        """Get gauge metric value"""
        # Simplified implementation
        return 0.0
    
    def _get_histogram_metric(self, metric_name: str) -> Dict:
        """Get histogram metric value"""
        # Simplified implementation
        return {'count': 0, 'sum': 0.0, 'min': 0.0, 'max': 0.0, 'avg': 0.0}
    
    def store_metrics(self, metrics: Dict, metric_type: str = 'system'):
        """Store metrics in database"""
        try:
            timestamp = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for metric_name, metric_value in metrics.items():
                    # Handle nested metrics
                    if isinstance(metric_value, dict):
                        for sub_name, sub_value in metric_value.items():
                            if isinstance(sub_value, (int, float)):
                                cursor.execute('''
                                    INSERT INTO metrics (timestamp, metric_name, metric_value, metric_type, tags)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (timestamp, f"{metric_name}.{sub_name}", sub_value, metric_type, json.dumps({})))
                    elif isinstance(metric_value, (int, float)):
                        cursor.execute('''
                            INSERT INTO metrics (timestamp, metric_name, metric_value, metric_type, tags)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (timestamp, metric_name, metric_value, metric_type, json.dumps({})))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {e}")
    
    def get_metrics_history(self, metric_name: str, hours: int = 24) -> List[Dict]:
        """Get metrics history"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, metric_value, metric_type, tags
                    FROM metrics
                    WHERE metric_name = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                ''', (metric_name, start_time))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'value': row[1],
                        'type': row[2],
                        'tags': json.loads(row[3]) if row[3] else {}
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get metrics history: {e}")
            return []
    
    def aggregate_metrics(self, interval_seconds: int):
        """Aggregate metrics for a specific interval"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=interval_seconds)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all unique metric names
                cursor.execute('''
                    SELECT DISTINCT metric_name
                    FROM metrics
                    WHERE timestamp >= ? AND timestamp < ?
                ''', (start_time, end_time))
                
                metric_names = [row[0] for row in cursor.fetchall()]
                
                for metric_name in metric_names:
                    # Calculate aggregations
                    cursor.execute('''
                        SELECT 
                            MIN(metric_value) as min_val,
                            MAX(metric_value) as max_val,
                            AVG(metric_value) as avg_val,
                            SUM(metric_value) as sum_val,
                            COUNT(*) as count_val
                        FROM metrics
                        WHERE metric_name = ? AND timestamp >= ? AND timestamp < ?
                    ''', (metric_name, start_time, end_time))
                    
                    result = cursor.fetchone()
                    if result:
                        cursor.execute('''
                            INSERT INTO aggregated_metrics 
                            (timestamp, metric_name, aggregation_type, aggregation_interval, 
                             min_value, max_value, avg_value, sum_value, count_value)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (end_time, metric_name, 'time_series', interval_seconds,
                              result[0], result[1], result[2], result[3], result[4]))
                
                conn.commit()
                
            self.logger.info(f"Metrics aggregated for interval {interval_seconds}s")
            
        except Exception as e:
            self.logger.error(f"Failed to aggregate metrics: {e}")
    
    def cleanup_old_metrics(self):
        """Cleanup old metrics based on retention policy"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete old raw metrics
                cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_time,))
                raw_deleted = cursor.rowcount
                
                # Delete old aggregated metrics
                cursor.execute('DELETE FROM aggregated_metrics WHERE timestamp < ?', (cutoff_time,))
                agg_deleted = cursor.rowcount
                
                conn.commit()
                
            self.logger.info(f"Cleaned up {raw_deleted} raw metrics and {agg_deleted} aggregated metrics")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {e}")
    
    def _collection_worker(self):
        """Metrics collection worker thread"""
        self.logger.info("Metrics collection worker started")
        
        while self.is_running:
            try:
                # Collect all types of metrics
                system_metrics = self.collect_system_metrics()
                app_metrics = self.collect_application_metrics()
                business_metrics = self.collect_business_metrics()
                custom_metrics = self.collect_custom_metrics()
                
                # Store metrics
                self.store_metrics(system_metrics, 'system')
                self.store_metrics(app_metrics, 'application')
                self.store_metrics(business_metrics, 'business')
                self.store_metrics(custom_metrics, 'custom')
                
                # Perform aggregations
                for interval in self.aggregation_intervals:
                    self.aggregate_metrics(interval)
                
                # Cleanup old metrics (once per hour)
                if datetime.now().minute == 0:
                    self.cleanup_old_metrics()
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Metrics collection worker error: {e}")
                time.sleep(5)
        
        self.logger.info("Metrics collection worker stopped")
    
    def start(self):
        """Start metrics collection"""
        if not self.is_running:
            self.is_running = True
            self.collection_thread = threading.Thread(target=self._collection_worker)
            self.collection_thread.start()
            self.logger.info("Metrics collection started")
    
    def stop(self):
        """Stop metrics collection"""
        if self.is_running:
            self.is_running = False
            if self.collection_thread:
                self.collection_thread.join(timeout=5)
            self.logger.info("Metrics collection stopped")
    
    def get_metrics_summary(self) -> Dict:
        """Get metrics collection summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total metrics count
                cursor.execute('SELECT COUNT(*) FROM metrics')
                total_metrics = cursor.fetchone()[0]
                
                # Get metrics by type
                cursor.execute('''
                    SELECT metric_type, COUNT(*) 
                    FROM metrics 
                    GROUP BY metric_type
                ''')
                metrics_by_type = dict(cursor.fetchall())
                
                # Get latest metrics timestamp
                cursor.execute('SELECT MAX(timestamp) FROM metrics')
                latest_timestamp = cursor.fetchone()[0]
                
                return {
                    'total_metrics': total_metrics,
                    'metrics_by_type': metrics_by_type,
                    'latest_timestamp': latest_timestamp,
                    'is_running': self.is_running,
                    'collection_interval': self.collection_interval,
                    'retention_days': self.retention_days,
                    'database_path': str(self.db_path)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get metrics summary: {e}")
            return {}
