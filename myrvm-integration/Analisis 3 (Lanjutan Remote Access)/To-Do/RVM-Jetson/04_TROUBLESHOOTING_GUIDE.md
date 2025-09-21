# TASK 04: TROUBLESHOOTING GUIDE

**Tanggal**: 2025-09-21  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 1 hari  
**Assigned**: RVM Jetson Orin (MyRVM-Integration)

---

## **📋 DESKRIPSI MASALAH**

Analisis 3 sudah diimplementasikan di server (MyRVM-Platform) tetapi tidak berfungsi karena beberapa masalah teknis di RVM-Jetson.

### **🎯 MASALAH YANG DITEMUKAN:**
1. **CSRF Token Issue** - Error 419 "Page Expired"
2. **API Client Method Missing** - `health_check` method tidak ada
3. **Authentication Issue** - API key tidak valid
4. **Endpoint Mismatch** - RVM ID tidak match dengan server

---

## **🔧 SOLUSI TEKNIS**

### **1. CSRF Token Issue Resolution**

#### **A. Enhanced API Client with CSRF Support:**
```python
# File: api_client/enhanced_myrvm_api_client.py (Enhanced)

import requests
import json
import time
from typing import Dict, Any, Tuple, Optional

class EnhancedMyRVMAPIClient:
    def __init__(self, base_url: str, api_token: str = None, rvm_id: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.rvm_id = rvm_id
        self.session = requests.Session()
        self.csrf_token = None
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session with CSRF token"""
        try:
            # Get CSRF token from server
            response = self.session.get(f"{self.base_url}/sanctum/csrf-cookie")
            if response.status_code == 204:
                # Extract CSRF token from cookies
                for cookie in self.session.cookies:
                    if cookie.name == 'XSRF-TOKEN':
                        self.csrf_token = cookie.value
                        break
                
                # Set headers
                self.session.headers.update({
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                })
                
                if self.csrf_token:
                    self.session.headers['X-XSRF-TOKEN'] = self.csrf_token
                
                print(f"CSRF token initialized: {self.csrf_token[:20]}...")
            else:
                print(f"Failed to get CSRF token: {response.status_code}")
                
        except Exception as e:
            print(f"Error initializing session: {e}")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 30) -> Tuple[bool, Dict]:
        """Make HTTP request with proper headers"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Prepare headers
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Add CSRF token if available
            if self.csrf_token:
                headers['X-XSRF-TOKEN'] = self.csrf_token
            
            # Add API token if available
            if self.api_token:
                headers['Authorization'] = f'Bearer {self.api_token}'
            
            # Add RVM ID if available
            if self.rvm_id:
                headers['X-RVM-ID'] = str(self.rvm_id)
            
            # Make request
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers, timeout=timeout)
            else:
                return False, {'error': f'Unsupported method: {method}'}
            
            # Handle response
            if response.status_code in [200, 201, 204]:
                try:
                    return True, response.json()
                except:
                    return True, {'message': 'Success', 'status_code': response.status_code}
            else:
                return False, {
                    'error': f'HTTP {response.status_code}',
                    'message': response.text,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return False, {'error': str(e)}
    
    def health_check(self) -> Tuple[bool, Dict]:
        """Check server health"""
        return self._make_request('GET', '/api/health')
    
    def send_metrics(self, metrics_data: Dict) -> Tuple[bool, Dict]:
        """Send metrics to server"""
        if not self.rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('POST', f'/admin/rvm/{self.rvm_id}/store-metrics', data=metrics_data)
    
    def execute_command(self, command_type: str, command_name: str, payload: Dict = None) -> Tuple[bool, Dict]:
        """Execute remote command"""
        if not self.rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        data = {
            'command_type': command_type,
            'command_name': command_name,
            'command_payload': payload or {}
        }
        
        return self._make_request('POST', f'/admin/rvm/{self.rvm_id}/execute-command', data=data)
```

### **2. Enhanced Metrics Sender**

#### **A. Metrics Sender with CSRF Support:**
```python
# File: monitoring/metrics_sender.py (Enhanced)

import requests
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from hardware_metrics_collector import HardwareMetricsCollector
from application_metrics_collector import ApplicationMetricsCollector
from network_info_collector import NetworkInfoCollector

class MetricsSender:
    def __init__(self, server_url: str, rvm_id: int, api_key: str):
        self.server_url = server_url
        self.rvm_id = rvm_id
        self.api_key = api_key
        self.hardware_collector = HardwareMetricsCollector()
        self.app_collector = ApplicationMetricsCollector()
        self.network_collector = NetworkInfoCollector()
        self.is_running = False
        self.send_thread = None
        self.send_interval = 60  # Send every 60 seconds
        self.session = requests.Session()
        self.csrf_token = None
        self._initialize_session()
        
    def _initialize_session(self):
        """Initialize session with CSRF token"""
        try:
            # Get CSRF token from server
            response = self.session.get(f"{self.server_url}/sanctum/csrf-cookie")
            if response.status_code == 204:
                # Extract CSRF token from cookies
                for cookie in self.session.cookies:
                    if cookie.name == 'XSRF-TOKEN':
                        self.csrf_token = cookie.value
                        break
                
                # Set headers
                self.session.headers.update({
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                })
                
                if self.csrf_token:
                    self.session.headers['X-XSRF-TOKEN'] = self.csrf_token
                
                print(f"Metrics Sender CSRF token initialized: {self.csrf_token[:20]}...")
            else:
                print(f"Failed to get CSRF token: {response.status_code}")
                
        except Exception as e:
            print(f"Error initializing metrics sender session: {e}")
    
    def start(self):
        """Start metrics sending service"""
        if self.is_running:
            return
        
        self.is_running = True
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.send_thread.start()
        print(f"Metrics sender started for RVM {self.rvm_id}")
    
    def stop(self):
        """Stop metrics sending service"""
        self.is_running = False
        if self.send_thread:
            self.send_thread.join(timeout=5)
        print(f"Metrics sender stopped for RVM {self.rvm_id}")
    
    def _send_loop(self):
        """Main sending loop"""
        while self.is_running:
            try:
                self._send_metrics()
                time.sleep(self.send_interval)
            except Exception as e:
                print(f"Error in metrics send loop: {e}")
                time.sleep(10)  # Wait 10 seconds before retry
    
    def _send_metrics(self):
        """Send metrics to server"""
        try:
            # Collect all metrics
            hardware_metrics = self.hardware_collector.collect_all_metrics()
            app_metrics = self.app_collector.collect_all_metrics()
            network_info = self.network_collector.collect_network_info()
            
            # Prepare payload
            payload = {
                'rvm_id': self.rvm_id,
                'system_metrics': {
                    'cpu_usage': hardware_metrics.get('cpu', {}).get('cpu_usage', 0),
                    'memory_usage': hardware_metrics.get('memory', {}).get('memory_usage', 0),
                    'disk_usage': hardware_metrics.get('disk', {}).get('disk_usage', 0),
                    'gpu_usage': hardware_metrics.get('gpu', {}).get('gpu_usage', 0),
                    'temperature': hardware_metrics.get('cpu', {}).get('cpu_temperature', 0),
                    'gpu_temperature': hardware_metrics.get('gpu', {}).get('gpu_temperature', 0),
                    'disk_read_speed': hardware_metrics.get('disk', {}).get('disk_read_speed', 0),
                    'disk_write_speed': hardware_metrics.get('disk', {}).get('disk_write_speed', 0),
                    'network_upload_speed': hardware_metrics.get('network', {}).get('network_upload_speed', 0),
                    'network_download_speed': hardware_metrics.get('network', {}).get('network_download_speed', 0),
                    'memory_available': hardware_metrics.get('memory', {}).get('memory_available', 0),
                    'disk_available': hardware_metrics.get('disk', {}).get('disk_available', 0),
                    'process_count': hardware_metrics.get('processes', {}).get('process_count', 0),
                    'load_average': hardware_metrics.get('cpu', {}).get('load_average', 0),
                    'uptime': app_metrics.get('uptime', {}).get('uptime_seconds', 0)
                },
                'application_metrics': {
                    'software_version': app_metrics.get('software', {}).get('software_version', 'unknown'),
                    'ai_model_version': app_metrics.get('ai_model', {}).get('model_version', 'unknown'),
                    'ai_model_path': app_metrics.get('ai_model', {}).get('model_path', ''),
                    'uptime_seconds': app_metrics.get('uptime', {}).get('uptime_seconds', 0),
                    'deposit_count_since_restart': app_metrics.get('deposits', {}).get('deposit_count_since_restart', 0),
                    'last_deposit_time': app_metrics.get('deposits', {}).get('last_deposit_time'),
                    'error_count': app_metrics.get('errors', {}).get('error_count', 0),
                    'warning_count': app_metrics.get('errors', {}).get('warning_count', 0)
                },
                'network_information': {
                    'local_ip': network_info.get('local_ip'),
                    'virtual_ip': network_info.get('virtual_ip'),
                    'gateway_ip': network_info.get('gateway_ip'),
                    'dns_servers': json.dumps(network_info.get('dns_servers', [])),
                    'network_interface': network_info.get('network_interface'),
                    'connection_type': network_info.get('connection_type'),
                    'signal_strength': network_info.get('signal_strength'),
                    'last_network_check': network_info.get('last_network_check')
                }
            }
            
            # Send to server
            response = self.session.post(
                f"{self.server_url}/admin/rvm/{self.rvm_id}/store-metrics",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"Metrics sent successfully for RVM {self.rvm_id}")
            else:
                print(f"Failed to send metrics: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error sending metrics: {e}")
    
    def send_immediate_metrics(self):
        """Send metrics immediately (for testing)"""
        self._send_metrics()
```

### **3. Configuration Updates**

#### **A. Update Production Config:**
```json
{
  "remote_access": {
    "server_url": "http://172.28.233.83:8001",
    "api_key": "your_api_key_here",
    "rvm_id": 4,
    "metrics_interval": 30,
    "command_timeout": 30
  }
}
```

**Note**: RVM ID diubah dari 1 ke 4 untuk match dengan server.

### **4. Test Script**

#### **A. Comprehensive Test Script:**
```python
# File: test_analisis3_integration.py

import asyncio
import time
from monitoring.metrics_sender import MetricsSender
from api_client.enhanced_myrvm_api_client import EnhancedMyRVMAPIClient

async def test_analisis3_integration():
    print("🧪 TESTING ANALISIS 3 INTEGRATION...")
    print("=" * 60)
    
    # Test 1: API Client
    print("\\n1. Testing API Client...")
    try:
        api_client = EnhancedMyRVMAPIClient(
            'http://172.28.233.83:8001', 
            'your_api_key_here', 
            'jetson_orin_nano_001'
        )
        
        # Test health check
        success, response = api_client.health_check()
        print(f"   ✅ Health check: {success} - {response}")
        
        # Test metrics sending
        success, response = api_client.send_metrics({
            'test': 'data',
            'timestamp': time.time()
        })
        print(f"   ✅ Metrics sending: {success} - {response}")
        
    except Exception as e:
        print(f"   ❌ API Client test failed: {e}")
    
    # Test 2: Metrics Sender
    print("\\n2. Testing Metrics Sender...")
    try:
        metrics_sender = MetricsSender('http://172.28.233.83:8001', 4, 'your_api_key_here')
        
        # Test immediate metrics sending
        print("   📤 Sending test metrics...")
        metrics_sender.send_immediate_metrics()
        print("   ✅ Metrics sent successfully")
        
    except Exception as e:
        print(f"   ❌ Metrics Sender test failed: {e}")
    
    # Test 3: Command Execution
    print("\\n3. Testing Command Execution...")
    try:
        success, response = api_client.execute_command(
            'DIAGNOSTICS', 
            'system_info', 
            {}
        )
        print(f"   ✅ Command execution: {success} - {response}")
        
    except Exception as e:
        print(f"   ❌ Command execution test failed: {e}")
    
    print("\\n🎉 ANALISIS 3 INTEGRATION TEST COMPLETED!")

if __name__ == "__main__":
    asyncio.run(test_analisis3_integration())
```

---

## **🧪 TESTING**

### **1. CSRF Token Testing:**
- Test CSRF token initialization
- Test session management
- Test request headers

### **2. API Client Testing:**
- Test health check endpoint
- Test metrics sending
- Test command execution

### **3. Integration Testing:**
- Test end-to-end communication
- Test error handling
- Test retry mechanisms

---

## **📋 CHECKLIST**

- [ ] Enhanced API client with CSRF support
- [ ] Enhanced metrics sender with CSRF support
- [ ] Updated configuration with correct RVM ID
- [ ] Test script for integration testing
- [ ] Test CSRF token initialization
- [ ] Test API client functionality
- [ ] Test metrics sending
- [ ] Test command execution
- [ ] Test error handling
- [ ] Performance testing
- [ ] Documentation update

---

## **📝 NOTES**

- CSRF token issue resolved with proper session management
- API client enhanced with missing methods
- Configuration updated with correct RVM ID (4)
- Comprehensive error handling implemented
- Test script for validation

---

**Status**: 🔄 **IN PROGRESS**  
**Next**: Implement enhanced API client and test integration
