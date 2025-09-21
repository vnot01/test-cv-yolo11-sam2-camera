import os
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, Optional

class ApplicationMetricsCollector:
    def __init__(self):
        self.start_time = time.time()
        self.deposit_count = 0
        self.error_count = 0
        self.warning_count = 0
        
    def collect_software_version(self) -> Dict[str, Any]:
        """Collect software version information"""
        try:
            # Get Git commit hash
            git_hash = self._get_git_commit_hash()
            
            # Get package versions
            package_versions = self._get_package_versions()
            
            return {
                'software_version': git_hash,
                'package_versions': package_versions,
                'build_date': self._get_build_date()
            }
        except Exception as e:
            print(f"Error collecting software version: {e}")
            return {}
    
    def collect_ai_model_info(self) -> Dict[str, Any]:
        """Collect AI model information"""
        try:
            model_path = os.path.join(os.getcwd(), 'models', 'best.pt')
            
            if os.path.exists(model_path):
                stat = os.stat(model_path)
                return {
                    'model_name': 'best.pt',
                    'model_version': self._get_model_version(model_path),
                    'model_path': model_path,
                    'model_size': stat.st_size,
                    'model_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                return {
                    'model_name': 'best.pt',
                    'model_version': 'not_found',
                    'model_path': model_path,
                    'model_size': 0,
                    'model_modified': None
                }
        except Exception as e:
            print(f"Error collecting AI model info: {e}")
            return {}
    
    def collect_uptime_metrics(self) -> Dict[str, Any]:
        """Collect application uptime metrics"""
        try:
            current_time = time.time()
            uptime_seconds = current_time - self.start_time
            
            return {
                'uptime_seconds': uptime_seconds,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'current_time': datetime.fromtimestamp(current_time).isoformat()
            }
        except Exception as e:
            print(f"Error collecting uptime metrics: {e}")
            return {}
    
    def collect_deposit_metrics(self) -> Dict[str, Any]:
        """Collect deposit-related metrics"""
        try:
            return {
                'deposit_count_since_restart': self.deposit_count,
                'last_deposit_time': self._get_last_deposit_time(),
                'deposit_rate_per_hour': self._calculate_deposit_rate()
            }
        except Exception as e:
            print(f"Error collecting deposit metrics: {e}")
            return {}
    
    def collect_error_metrics(self) -> Dict[str, Any]:
        """Collect error and warning metrics"""
        try:
            return {
                'error_count': self.error_count,
                'warning_count': self.warning_count,
                'last_error_time': self._get_last_error_time(),
                'last_warning_time': self._get_last_warning_time()
            }
        except Exception as e:
            print(f"Error collecting error metrics: {e}")
            return {}
    
    def increment_deposit_count(self):
        """Increment deposit count"""
        self.deposit_count += 1
    
    def increment_error_count(self):
        """Increment error count"""
        self.error_count += 1
    
    def increment_warning_count(self):
        """Increment warning count"""
        self.warning_count += 1
    
    def _get_git_commit_hash(self) -> Optional[str]:
        """Get current Git commit hash"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            if result.returncode == 0:
                return result.stdout.strip()[:8]  # Short hash
        except Exception:
            pass
        return None
    
    def _get_package_versions(self) -> Dict[str, str]:
        """Get installed package versions"""
        try:
            packages = ['torch', 'ultralytics', 'opencv-python', 'numpy', 'pillow']
            versions = {}
            
            for package in packages:
                try:
                    result = subprocess.run(['pip', 'show', package], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.startswith('Version:'):
                                versions[package] = line.split(':', 1)[1].strip()
                                break
                except Exception:
                    versions[package] = 'unknown'
            
            return versions
        except Exception as e:
            print(f"Error getting package versions: {e}")
            return {}
    
    def _get_build_date(self) -> Optional[str]:
        """Get build date from Git"""
        try:
            result = subprocess.run(['git', 'log', '-1', '--format=%ci'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def _get_model_version(self, model_path: str) -> str:
        """Get model version (simplified)"""
        try:
            # This would typically involve loading the model and checking metadata
            # For now, we'll use file modification time as version
            stat = os.stat(model_path)
            return datetime.fromtimestamp(stat.st_mtime).strftime('%Y%m%d_%H%M%S')
        except Exception:
            return 'unknown'
    
    def _get_last_deposit_time(self) -> Optional[str]:
        """Get last deposit time"""
        try:
            # This would read from your deposit log or database
            return None  # Placeholder
        except Exception:
            return None
    
    def _calculate_deposit_rate(self) -> float:
        """Calculate deposit rate per hour"""
        try:
            uptime_hours = (time.time() - self.start_time) / 3600
            if uptime_hours > 0:
                return self.deposit_count / uptime_hours
            return 0.0
        except Exception:
            return 0.0
    
    def _get_last_error_time(self) -> Optional[str]:
        """Get last error time"""
        try:
            # This would read from your error log
            return None  # Placeholder
        except Exception:
            return None
    
    def _get_last_warning_time(self) -> Optional[str]:
        """Get last warning time"""
        try:
            # This would read from your warning log
            return None  # Placeholder
        except Exception:
            return None
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all application metrics"""
        return {
            'software': self.collect_software_version(),
            'ai_model': self.collect_ai_model_info(),
            'uptime': self.collect_uptime_metrics(),
            'deposits': self.collect_deposit_metrics(),
            'errors': self.collect_error_metrics(),
            'timestamp': datetime.now().isoformat()
        }

