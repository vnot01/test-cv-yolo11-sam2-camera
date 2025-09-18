#!/usr/bin/env python3
"""
Advanced Alerting Engine for MyRVM Platform Integration
Real-time alerting system with multiple notification channels
"""

import os
import json
import logging
import smtplib
import requests
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict, deque
import hashlib

class AlertingEngine:
    """Advanced alerting system with multiple notification channels"""
    
    def __init__(self, config: Dict):
        """
        Initialize alerting engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.suppressed_alerts = set()
        
        # Notification channels
        self.notification_channels = {
            'email': self._send_email_alert,
            'webhook': self._send_webhook_alert,
            'log': self._send_log_alert,
            'console': self._send_console_alert
        }
        
        # Alert management
        self.alert_lock = threading.Lock()
        self.alert_callbacks = []
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Load alert rules
        self._load_alert_rules()
        
        # Initialize notification settings
        self._initialize_notification_settings()
        
        self.logger.info("Alerting engine initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for alerting engine"""
        logger = logging.getLogger('AlertingEngine')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'alerting_engine_{now().strftime("%Y%m%d")}.log'
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
    
    def _load_alert_rules(self):
        """Load alert rules from configuration"""
        try:
            # Default alert rules
            self.alert_rules = {
                'high_cpu_usage': {
                    'metric': 'system.cpu.percent',
                    'condition': '>',
                    'threshold': 80,
                    'severity': 'warning',
                    'message': 'High CPU usage detected',
                    'channels': ['log', 'console'],
                    'enabled': True,
                    'cooldown': 300  # 5 minutes
                },
                'critical_cpu_usage': {
                    'metric': 'system.cpu.percent',
                    'condition': '>',
                    'threshold': 95,
                    'severity': 'critical',
                    'message': 'Critical CPU usage detected',
                    'channels': ['log', 'console', 'email'],
                    'enabled': True,
                    'cooldown': 60  # 1 minute
                },
                'high_memory_usage': {
                    'metric': 'system.memory.percent',
                    'condition': '>',
                    'threshold': 85,
                    'severity': 'warning',
                    'message': 'High memory usage detected',
                    'channels': ['log', 'console'],
                    'enabled': True,
                    'cooldown': 300
                },
                'critical_memory_usage': {
                    'metric': 'system.memory.percent',
                    'condition': '>',
                    'threshold': 95,
                    'severity': 'critical',
                    'message': 'Critical memory usage detected',
                    'channels': ['log', 'console', 'email'],
                    'enabled': True,
                    'cooldown': 60
                },
                'high_disk_usage': {
                    'metric': 'system.disk.percent',
                    'condition': '>',
                    'threshold': 90,
                    'severity': 'warning',
                    'message': 'High disk usage detected',
                    'channels': ['log', 'console'],
                    'enabled': True,
                    'cooldown': 600  # 10 minutes
                },
                'gpu_high_usage': {
                    'metric': 'gpu.load_percent',
                    'condition': '>',
                    'threshold': 90,
                    'severity': 'info',
                    'message': 'High GPU usage detected',
                    'channels': ['log'],
                    'enabled': True,
                    'cooldown': 300
                },
                'gpu_high_temperature': {
                    'metric': 'gpu.temperature_c',
                    'condition': '>',
                    'threshold': 80,
                    'severity': 'warning',
                    'message': 'High GPU temperature detected',
                    'channels': ['log', 'console'],
                    'enabled': True,
                    'cooldown': 300
                },
                'service_down': {
                    'metric': 'application.uptime_seconds',
                    'condition': '==',
                    'threshold': 0,
                    'severity': 'critical',
                    'message': 'Service appears to be down',
                    'channels': ['log', 'console', 'email', 'webhook'],
                    'enabled': True,
                    'cooldown': 30
                },
                'high_error_rate': {
                    'metric': 'application.error_count',
                    'condition': '>',
                    'threshold': 10,
                    'severity': 'warning',
                    'message': 'High error rate detected',
                    'channels': ['log', 'console'],
                    'enabled': True,
                    'cooldown': 300
                }
            }
            
            # Load custom rules from config if available
            custom_rules = self.config.get('alert_rules', {})
            self.alert_rules.update(custom_rules)
            
            self.logger.info(f"Loaded {len(self.alert_rules)} alert rules")
            
        except Exception as e:
            self.logger.error(f"Error loading alert rules: {e}")
    
    def _initialize_notification_settings(self):
        """Initialize notification settings"""
        try:
            self.notification_settings = {
                'email': {
                    'enabled': self.config.get('email_alerts', {}).get('enabled', False),
                    'smtp_server': self.config.get('email_alerts', {}).get('smtp_server', 'localhost'),
                    'smtp_port': self.config.get('email_alerts', {}).get('smtp_port', 587),
                    'username': self.config.get('email_alerts', {}).get('username', ''),
                    'password': self.config.get('email_alerts', {}).get('password', ''),
                    'from_email': self.config.get('email_alerts', {}).get('from_email', ''),
                    'to_emails': self.config.get('email_alerts', {}).get('to_emails', [])
                },
                'webhook': {
                    'enabled': self.config.get('webhook_alerts', {}).get('enabled', False),
                    'url': self.config.get('webhook_alerts', {}).get('url', ''),
                    'headers': self.config.get('webhook_alerts', {}).get('headers', {}),
                    'timeout': self.config.get('webhook_alerts', {}).get('timeout', 10)
                },
                'log': {
                    'enabled': True,
                    'level': 'INFO'
                },
                'console': {
                    'enabled': True
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error initializing notification settings: {e}")
    
    def process_metrics(self, metrics: Dict):
        """Process metrics and check for alert conditions"""
        try:
            with self.alert_lock:
                for rule_name, rule in self.alert_rules.items():
                    if not rule.get('enabled', True):
                        continue
                    
                    # Check if alert is in cooldown
                    if self._is_alert_in_cooldown(rule_name):
                        continue
                    
                    # Check if alert is suppressed
                    if rule_name in self.suppressed_alerts:
                        continue
                    
                    # Evaluate alert condition
                    if self._evaluate_alert_condition(rule, metrics):
                        self._trigger_alert(rule_name, rule, metrics)
                    else:
                        # Clear alert if condition is no longer met
                        if rule_name in self.active_alerts:
                            self._clear_alert(rule_name, rule, metrics)
            
        except Exception as e:
            self.logger.error(f"Error processing metrics for alerts: {e}")
    
    def _evaluate_alert_condition(self, rule: Dict, metrics: Dict) -> bool:
        """Evaluate alert condition"""
        try:
            metric_path = rule['metric']
            condition = rule['condition']
            threshold = rule['threshold']
            
            # Get metric value
            value = self._get_metric_value(metrics, metric_path)
            if value is None:
                return False
            
            # Evaluate condition
            if condition == '>':
                return value > threshold
            elif condition == '>=':
                return value >= threshold
            elif condition == '<':
                return value < threshold
            elif condition == '<=':
                return value <= threshold
            elif condition == '==':
                return value == threshold
            elif condition == '!=':
                return value != threshold
            else:
                self.logger.warning(f"Unknown condition: {condition}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error evaluating alert condition: {e}")
            return False
    
    def _get_metric_value(self, metrics: Dict, metric_path: str) -> Optional[float]:
        """Get metric value from nested dictionary"""
        try:
            keys = metric_path.split('.')
            value = metrics
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            
            # Convert to float if possible
            if isinstance(value, (int, float)):
                return float(value)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting metric value: {e}")
            return None
    
    def _trigger_alert(self, rule_name: str, rule: Dict, metrics: Dict):
        """Trigger alert"""
        try:
            alert_id = self._generate_alert_id(rule_name, metrics)
            
            alert_data = {
                'id': alert_id,
                'rule_name': rule_name,
                'severity': rule['severity'],
                'message': rule['message'],
                'timestamp': now().isoformat(),
                'metric_path': rule['metric'],
                'metric_value': self._get_metric_value(metrics, rule['metric']),
                'threshold': rule['threshold'],
                'condition': rule['condition'],
                'channels': rule.get('channels', ['log']),
                'status': 'active'
            }
            
            # Store active alert
            self.active_alerts[rule_name] = alert_data
            
            # Add to history
            self.alert_history.append(alert_data)
            
            # Send notifications
            self._send_notifications(alert_data)
            
            # Notify callbacks
            self._notify_alert_callbacks(alert_data)
            
            self.logger.warning(f"Alert triggered: {rule_name} - {rule['message']}")
            
        except Exception as e:
            self.logger.error(f"Error triggering alert: {e}")
    
    def _clear_alert(self, rule_name: str, rule: Dict, metrics: Dict):
        """Clear alert"""
        try:
            if rule_name in self.active_alerts:
                alert_data = self.active_alerts[rule_name]
                alert_data['status'] = 'cleared'
                alert_data['cleared_at'] = now().isoformat()
                
                # Remove from active alerts
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
                del self.active_alerts[rule_name]
                
                # Add to history
                self.alert_history.append(alert_data)
                
                # Send clear notification
                clear_message = f"Alert cleared: {rule['message']}"
                self._send_clear_notification(rule_name, clear_message, alert_data)
                
                self.logger.info(f"Alert cleared: {rule_name}")
                
        except Exception as e:
            self.logger.error(f"Error clearing alert: {e}")
    
    def _generate_alert_id(self, rule_name: str, metrics: Dict) -> str:
        """Generate unique alert ID"""
        try:
            timestamp = now().strftime("%Y%m%d_%H%M%S")
            metric_value = self._get_metric_value(metrics, self.alert_rules[rule_name]['metric'])
            data = f"{rule_name}_{timestamp}_{metric_value}"
            return hashlib.md5(data.encode()).hexdigest()[:12]
        except Exception as e:
            self.logger.error(f"Error generating alert ID: {e}")
            return f"{rule_name}_{int(time.time())}"
    
    def _is_alert_in_cooldown(self, rule_name: str) -> bool:
        """Check if alert is in cooldown period"""
        try:
            if rule_name not in self.active_alerts:
                return False
            
            alert = self.active_alerts[rule_name]
            cooldown = self.alert_rules[rule_name].get('cooldown', 300)
            
            alert_time = datetime.fromisoformat(alert['timestamp'])
            cooldown_end = alert_time + timedelta(seconds=cooldown)
            
            return now() < cooldown_end
            
        except Exception as e:
            self.logger.error(f"Error checking alert cooldown: {e}")
            return False
    
    def _send_notifications(self, alert_data: Dict):
        """Send notifications through configured channels"""
        try:
            channels = alert_data.get('channels', ['log'])
            
            for channel in channels:
                if channel in self.notification_channels:
                    try:
                        self.notification_channels[channel](alert_data)
                    except Exception as e:
                        self.logger.error(f"Error sending notification via {channel}: {e}")
                else:
                    self.logger.warning(f"Unknown notification channel: {channel}")
                    
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")
    
    def _send_clear_notification(self, rule_name: str, message: str, alert_data: Dict):
        """Send alert clear notification"""
        try:
            clear_alert = alert_data.copy()
            clear_alert['message'] = message
            clear_alert['type'] = 'clear'
            
            # Send to log and console by default
            self._send_log_alert(clear_alert)
            self._send_console_alert(clear_alert)
            
        except Exception as e:
            self.logger.error(f"Error sending clear notification: {e}")
    
    def _send_email_alert(self, alert_data: Dict):
        """Send email alert"""
        try:
            settings = self.notification_settings['email']
            if not settings['enabled']:
                return
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = settings['from_email']
            msg['To'] = ', '.join(settings['to_emails'])
            msg['Subject'] = f"[{alert_data['severity'].upper()}] {alert_data['message']}"
            
            # Create email body
            body = f"""
Alert Details:
- Rule: {alert_data['rule_name']}
- Severity: {alert_data['severity']}
- Message: {alert_data['message']}
- Timestamp: {alert_data['timestamp']}
- Metric: {alert_data['metric_path']} = {alert_data['metric_value']}
- Threshold: {alert_data['condition']} {alert_data['threshold']}
- Alert ID: {alert_data['id']}

System: MyRVM Platform Integration
Environment: {self.config.get('environment', 'unknown')}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(settings['smtp_server'], settings['smtp_port'])
            server.starttls()
            if settings['username'] and settings['password']:
                server.login(settings['username'], settings['password'])
            
            text = msg.as_string()
            server.sendmail(settings['from_email'], settings['to_emails'], text)
            server.quit()
            
            self.logger.info(f"Email alert sent: {alert_data['rule_name']}")
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")
    
    def _send_webhook_alert(self, alert_data: Dict):
        """Send webhook alert"""
        try:
            settings = self.notification_settings['webhook']
            if not settings['enabled']:
                return
            
            # Prepare webhook payload
            payload = {
                'alert': alert_data,
                'system': 'myrvm-integration',
                'environment': self.config.get('environment', 'unknown'),
                'timestamp': now().isoformat()
            }
            
            # Send webhook
            response = requests.post(
                settings['url'],
                json=payload,
                headers=settings['headers'],
                timeout=settings['timeout']
            )
            
            if response.status_code == 200:
                self.logger.info(f"Webhook alert sent: {alert_data['rule_name']}")
            else:
                self.logger.error(f"Webhook alert failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error sending webhook alert: {e}")
    
    def _send_log_alert(self, alert_data: Dict):
        """Send log alert"""
        try:
            settings = self.notification_settings['log']
            if not settings['enabled']:
                return
            
            log_level = getattr(logging, alert_data['severity'].upper(), logging.INFO)
            self.logger.log(log_level, f"ALERT: {alert_data['message']} - {alert_data['rule_name']}")
            
        except Exception as e:
            self.logger.error(f"Error sending log alert: {e}")
    
    def _send_console_alert(self, alert_data: Dict):
        """Send console alert"""
        try:
            settings = self.notification_settings['console']
            if not settings['enabled']:
                return
            
            severity_color = {
                'info': '\033[94m',      # Blue
                'warning': '\033[93m',   # Yellow
                'critical': '\033[91m',  # Red
                'error': '\033[91m'      # Red
            }
            
            color = severity_color.get(alert_data['severity'], '\033[0m')
            reset = '\033[0m'
            
            print(f"{color}[{alert_data['severity'].upper()}] {alert_data['message']}{reset}")
            print(f"  Rule: {alert_data['rule_name']}")
            print(f"  Metric: {alert_data['metric_path']} = {alert_data['metric_value']}")
            print(f"  Threshold: {alert_data['condition']} {alert_data['threshold']}")
            print(f"  Time: {alert_data['timestamp']}")
            print()
            
        except Exception as e:
            self.logger.error(f"Error sending console alert: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback"""
        self.alert_callbacks.append(callback)
        self.logger.info(f"Added alert callback: {callback.__name__}")
    
    def remove_alert_callback(self, callback: Callable):
        """Remove alert callback"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
            self.logger.info(f"Removed alert callback: {callback.__name__}")
    
    def _notify_alert_callbacks(self, alert_data: Dict):
        """Notify alert callbacks"""
        try:
            for callback in self.alert_callbacks:
                try:
                    callback(alert_data)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
        except Exception as e:
            self.logger.error(f"Error notifying alert callbacks: {e}")
    
    def suppress_alert(self, rule_name: str, duration_minutes: int = 60):
        """Suppress alert for specified duration"""
        try:
            self.suppressed_alerts.add(rule_name)
            self.logger.info(f"Alert suppressed: {rule_name} for {duration_minutes} minutes")
            
            # Auto-remove suppression after duration
            def remove_suppression():
                time.sleep(duration_minutes * 60)
                self.suppressed_alerts.discard(rule_name)
                self.logger.info(f"Alert suppression removed: {rule_name}")
            
            threading.Thread(target=remove_suppression, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error suppressing alert: {e}")
    
    def unsuppress_alert(self, rule_name: str):
        """Remove alert suppression"""
        try:
            self.suppressed_alerts.discard(rule_name)
            self.logger.info(f"Alert suppression removed: {rule_name}")
        except Exception as e:
            self.logger.error(f"Error removing alert suppression: {e}")
    
    def get_active_alerts(self) -> Dict:
        """Get active alerts"""
        with self.alert_lock:
            return self.active_alerts.copy()
    
    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """Get alert history"""
        try:
            history = list(self.alert_history)
            return history[-limit:] if limit else history
        except Exception as e:
            self.logger.error(f"Error getting alert history: {e}")
            return []
    
    def get_alerting_status(self) -> Dict:
        """Get alerting system status"""
        try:
            return {
                'active_alerts_count': len(self.active_alerts),
                'suppressed_alerts_count': len(self.suppressed_alerts),
                'alert_rules_count': len(self.alert_rules),
                'enabled_rules_count': sum(1 for rule in self.alert_rules.values() if rule.get('enabled', True)),
                'notification_channels': list(self.notification_channels.keys()),
                'callbacks_count': len(self.alert_callbacks),
                'last_alert': self.alert_history[-1] if self.alert_history else None
            }
        except Exception as e:
            self.logger.error(f"Error getting alerting status: {e}")
            return {}
    
    def get_alerting_report(self) -> str:
        """Generate alerting report"""
        try:
            status = self.get_alerting_status()
            active_alerts = self.get_active_alerts()
            
            report = f"""
Alerting Engine Report
=====================
Active Alerts: {status.get('active_alerts_count', 0)}
Suppressed Alerts: {status.get('suppressed_alerts_count', 0)}
Total Rules: {status.get('alert_rules_count', 0)}
Enabled Rules: {status.get('enabled_rules_count', 0)}
Notification Channels: {', '.join(status.get('notification_channels', []))}
Callbacks: {status.get('callbacks_count', 0)}

Active Alerts:
"""
            
            for rule_name, alert in active_alerts.items():
                report += f"- {rule_name}: {alert['message']} ({alert['severity']})\n"
            
            if not active_alerts:
                report += "- No active alerts\n"
            
            report += f"\nLast Alert: {status.get('last_alert', {}).get('timestamp', 'None')}\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating alerting report: {e}")
            return f"Error generating alerting report: {e}"
