#!/usr/bin/env python3
"""
Alerting System for MyRVM Platform Integration
Real-time alerting with multiple notification channels
"""

import json
import smtplib
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

class AlertingSystem:
    """Real-time alerting system with multiple notification channels"""
    
    def __init__(self, config: Dict):
        """
        Initialize alerting system
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Alert configuration
        self.alert_thresholds = config.get('alert_thresholds', {
            'cpu_percent': 80.0,
            'memory_percent': 80.0,
            'disk_percent': 85.0,
            'temperature': 75.0,
            'response_time': 5.0,
            'error_rate': 0.1
        })
        
        # Notification channels
        self.notification_channels = config.get('notification_channels', {
            'email': {'enabled': False},
            'webhook': {'enabled': False},
            'slack': {'enabled': False},
            'sms': {'enabled': False}
        })
        
        # Alert management
        self.active_alerts = {}
        self.alert_history = []
        self.alert_cooldown = config.get('alert_cooldown', 300)  # 5 minutes
        self.max_history_size = config.get('max_alert_history', 1000)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Alert processing thread
        self.alert_thread = None
        self.is_running = False
        
        # Load alert configuration
        self._load_alert_config()
        
        self.logger.info("Alerting system initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for alerting system"""
        logger = logging.getLogger('AlertingSystem')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'alerting_system_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _load_alert_config(self):
        """Load alert configuration from file"""
        config_file = Path(__file__).parent / 'config' / 'alerts.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                self.alert_thresholds.update(config_data.get('thresholds', {}))
                self.notification_channels.update(config_data.get('channels', {}))
                
                self.logger.info("Alert configuration loaded from file")
            except Exception as e:
                self.logger.error(f"Failed to load alert configuration: {e}")
        else:
            # Create default configuration
            self._save_alert_config()
    
    def _save_alert_config(self):
        """Save alert configuration to file"""
        try:
            config_file = Path(__file__).parent / 'config' / 'alerts.json'
            config_file.parent.mkdir(exist_ok=True)
            
            config_data = {
                'thresholds': self.alert_thresholds,
                'channels': self.notification_channels,
                'cooldown': self.alert_cooldown,
                'max_history': self.max_history_size
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info("Alert configuration saved to file")
            
        except Exception as e:
            self.logger.error(f"Failed to save alert configuration: {e}")
    
    def check_metrics(self, metrics: Dict) -> List[Dict]:
        """Check metrics against thresholds and generate alerts"""
        alerts = []
        
        try:
            # CPU alert
            cpu_percent = metrics.get('cpu', {}).get('percent', 0)
            if cpu_percent > self.alert_thresholds['cpu_percent']:
                alerts.append({
                    'type': 'high_cpu',
                    'severity': 'critical' if cpu_percent > 90 else 'warning',
                    'message': f'High CPU usage: {cpu_percent:.1f}%',
                    'value': cpu_percent,
                    'threshold': self.alert_thresholds['cpu_percent'],
                    'timestamp': datetime.now().isoformat()
                })
            
            # Memory alert
            memory_percent = metrics.get('memory', {}).get('percent', 0)
            if memory_percent > self.alert_thresholds['memory_percent']:
                alerts.append({
                    'type': 'high_memory',
                    'severity': 'critical' if memory_percent > 90 else 'warning',
                    'message': f'High memory usage: {memory_percent:.1f}%',
                    'value': memory_percent,
                    'threshold': self.alert_thresholds['memory_percent'],
                    'timestamp': datetime.now().isoformat()
                })
            
            # Disk alert
            disk_percent = metrics.get('disk', {}).get('percent', 0)
            if disk_percent > self.alert_thresholds['disk_percent']:
                alerts.append({
                    'type': 'high_disk',
                    'severity': 'critical' if disk_percent > 95 else 'warning',
                    'message': f'High disk usage: {disk_percent:.1f}%',
                    'value': disk_percent,
                    'threshold': self.alert_thresholds['disk_percent'],
                    'timestamp': datetime.now().isoformat()
                })
            
            # Temperature alert
            cpu_temp = metrics.get('temperature', {}).get('cpu_celsius')
            if cpu_temp and cpu_temp > self.alert_thresholds['temperature']:
                alerts.append({
                    'type': 'high_temperature',
                    'severity': 'critical' if cpu_temp > 85 else 'warning',
                    'message': f'High CPU temperature: {cpu_temp:.1f}°C',
                    'value': cpu_temp,
                    'threshold': self.alert_thresholds['temperature'],
                    'timestamp': datetime.now().isoformat()
                })
            
            # Response time alert (if available)
            response_time = metrics.get('response_time', 0)
            if response_time > self.alert_thresholds['response_time']:
                alerts.append({
                    'type': 'high_response_time',
                    'severity': 'warning',
                    'message': f'High API response time: {response_time:.2f}s',
                    'value': response_time,
                    'threshold': self.alert_thresholds['response_time'],
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            self.logger.error(f"Failed to check metrics: {e}")
        
        return alerts
    
    def process_alerts(self, alerts: List[Dict]):
        """Process alerts and send notifications"""
        for alert in alerts:
            try:
                alert_key = f"{alert['type']}_{alert['severity']}"
                
                # Check if alert is in cooldown period
                if alert_key in self.active_alerts:
                    last_alert_time = self.active_alerts[alert_key]['timestamp']
                    if datetime.now() - datetime.fromisoformat(last_alert_time) < timedelta(seconds=self.alert_cooldown):
                        continue
                
                # Update active alerts
                self.active_alerts[alert_key] = alert
                
                # Add to history
                self.alert_history.append(alert)
                if len(self.alert_history) > self.max_history_size:
                    self.alert_history = self.alert_history[-self.max_history_size:]
                
                # Send notifications
                self._send_notifications(alert)
                
                self.logger.warning(f"Alert processed: {alert['type']} - {alert['message']}")
                
            except Exception as e:
                self.logger.error(f"Failed to process alert: {e}")
    
    def _send_notifications(self, alert: Dict):
        """Send notifications through configured channels"""
        try:
            # Email notification
            if self.notification_channels.get('email', {}).get('enabled', False):
                self._send_email_alert(alert)
            
            # Webhook notification
            if self.notification_channels.get('webhook', {}).get('enabled', False):
                self._send_webhook_alert(alert)
            
            # Slack notification
            if self.notification_channels.get('slack', {}).get('enabled', False):
                self._send_slack_alert(alert)
            
            # SMS notification
            if self.notification_channels.get('sms', {}).get('enabled', False):
                self._send_sms_alert(alert)
                
        except Exception as e:
            self.logger.error(f"Failed to send notifications: {e}")
    
    def _send_email_alert(self, alert: Dict):
        """Send email alert"""
        try:
            email_config = self.notification_channels['email']
            
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = f"[{alert['severity'].upper()}] MyRVM Platform Alert: {alert['type']}"
            
            body = f"""
Alert Type: {alert['type']}
Severity: {alert['severity'].upper()}
Message: {alert['message']}
Value: {alert.get('value', 'N/A')}
Threshold: {alert.get('threshold', 'N/A')}
Timestamp: {alert['timestamp']}

This is an automated alert from the MyRVM Platform monitoring system.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent: {alert['type']}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def _send_webhook_alert(self, alert: Dict):
        """Send webhook alert"""
        try:
            webhook_config = self.notification_channels['webhook']
            
            payload = {
                'alert': alert,
                'system': 'MyRVM Platform',
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                webhook_config['url'],
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Webhook alert sent: {alert['type']}")
            else:
                self.logger.error(f"Webhook alert failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
    
    def _send_slack_alert(self, alert: Dict):
        """Send Slack alert"""
        try:
            slack_config = self.notification_channels['slack']
            
            # Determine color based on severity
            color = 'danger' if alert['severity'] == 'critical' else 'warning'
            
            payload = {
                'channel': slack_config['channel'],
                'username': 'MyRVM Platform',
                'icon_emoji': ':warning:',
                'attachments': [{
                    'color': color,
                    'title': f"Alert: {alert['type'].replace('_', ' ').title()}",
                    'text': alert['message'],
                    'fields': [
                        {'title': 'Severity', 'value': alert['severity'].upper(), 'short': True},
                        {'title': 'Value', 'value': str(alert.get('value', 'N/A')), 'short': True},
                        {'title': 'Threshold', 'value': str(alert.get('threshold', 'N/A')), 'short': True},
                        {'title': 'Timestamp', 'value': alert['timestamp'], 'short': False}
                    ]
                }]
            }
            
            response = requests.post(
                slack_config['webhook_url'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Slack alert sent: {alert['type']}")
            else:
                self.logger.error(f"Slack alert failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
    
    def _send_sms_alert(self, alert: Dict):
        """Send SMS alert"""
        try:
            sms_config = self.notification_channels['sms']
            
            # This is a simplified SMS implementation
            # In production, you'd use a proper SMS service like Twilio
            message = f"[{alert['severity'].upper()}] MyRVM Alert: {alert['message']}"
            
            # For now, just log the SMS (in production, send actual SMS)
            self.logger.info(f"SMS alert (simulated): {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS alert: {e}")
    
    def clear_alert(self, alert_type: str, severity: str):
        """Clear a specific alert"""
        try:
            alert_key = f"{alert_type}_{severity}"
            if alert_key in self.active_alerts:
                del self.active_alerts[alert_key]
                self.logger.info(f"Alert cleared: {alert_type} - {severity}")
        except Exception as e:
            self.logger.error(f"Failed to clear alert: {e}")
    
    def get_active_alerts(self) -> List[Dict]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """Get alert history"""
        return self.alert_history[-limit:] if limit else self.alert_history
    
    def get_alert_statistics(self) -> Dict:
        """Get alert statistics"""
        try:
            total_alerts = len(self.alert_history)
            active_alerts = len(self.active_alerts)
            
            # Count by severity
            severity_counts = {'critical': 0, 'warning': 0, 'info': 0}
            for alert in self.alert_history:
                severity = alert.get('severity', 'info')
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            # Count by type
            type_counts = {}
            for alert in self.alert_history:
                alert_type = alert.get('type', 'unknown')
                type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
            
            return {
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'severity_counts': severity_counts,
                'type_counts': type_counts,
                'last_alert': self.alert_history[-1] if self.alert_history else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get alert statistics: {e}")
            return {}
    
    def start(self):
        """Start alerting system"""
        if not self.is_running:
            self.is_running = True
            self.alert_thread = threading.Thread(target=self._alert_worker)
            self.alert_thread.start()
            self.logger.info("Alerting system started")
    
    def stop(self):
        """Stop alerting system"""
        if self.is_running:
            self.is_running = False
            if self.alert_thread:
                self.alert_thread.join(timeout=5)
            self.logger.info("Alerting system stopped")
    
    def _alert_worker(self):
        """Alert processing worker thread"""
        self.logger.info("Alert worker started")
        
        while self.is_running:
            try:
                # This worker would typically receive metrics from the monitoring system
                # For now, it's a placeholder for future integration
                time.sleep(10)
            except Exception as e:
                self.logger.error(f"Alert worker error: {e}")
                time.sleep(5)
        
        self.logger.info("Alert worker stopped")
    
    def get_alerting_status(self) -> Dict:
        """Get alerting system status"""
        return {
            'is_running': self.is_running,
            'active_alerts': len(self.active_alerts),
            'total_history': len(self.alert_history),
            'notification_channels': {
                channel: config.get('enabled', False) 
                for channel, config in self.notification_channels.items()
            },
            'alert_thresholds': self.alert_thresholds,
            'cooldown_period': self.alert_cooldown
        }
