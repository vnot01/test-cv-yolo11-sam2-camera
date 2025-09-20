# MyRVM API Client Documentation

**Project:** MyRVM Platform Integration with Jetson Orin Nano  
**Date:** September 18, 2025  
**Version:** 1.0.0  

## 📋 Overview

The MyRVM API Client is a Python library designed to facilitate communication between the Jetson Orin Nano CV system and the MyRVM Platform. It provides a comprehensive interface for authentication, data management, and real-time communication.

## 🚀 Features

- **Authentication Management:** Bearer token authentication with automatic token refresh
- **Processing Engine Management:** Register and manage Jetson Orin as processing engine
- **Detection Results Upload:** Upload computer vision detection results
- **Deposit Management:** Create and process waste deposits
- **RVM Status Monitoring:** Monitor RVM status and health
- **File Upload:** Upload images and detection data
- **Error Handling:** Comprehensive error handling and retry mechanisms
- **Logging:** Detailed logging for debugging and monitoring

## 📦 Installation

### **Prerequisites**
- Python 3.10+
- Virtual environment (recommended)
- Network access to MyRVM Platform

### **Installation Steps**
```bash
# Navigate to the project directory
cd /home/my/test-cv-yolo11-sam2-camera

# Activate virtual environment
source myenv/bin/activate

# Install dependencies
pip install -r myrvm-integration/requirements.txt
```

### **Dependencies**
```
requests>=2.31.0
urllib3>=2.0.0
python-dotenv>=1.0.0
```

## 🔧 Configuration

### **Configuration File**
The API client uses configuration from `config.json`:

```json
{
  "myrvm_base_url": "http://172.28.233.83:8001",
  "myrvm_tunnel_url": "https://your-tunnel-domain.com",
  "api_token": null,
  "jetson_ip": "172.28.93.97",
  "use_tunnel": false,
  "tunnel_type": "zerotier",
  "fallback_to_local": true,
  "zerotier_network": {
    "rvm_ip": "172.28.93.97",
    "platform_ip": "172.28.233.83",
    "platform_port": 8001,
    "network_id": "9bee8941b52c05b9"
  }
}
```

### **Environment Variables**
```bash
# Optional: Override configuration with environment variables
export MYRVM_BASE_URL="http://172.28.233.83:8001"
export MYRVM_API_TOKEN="your_token_here"
export JETSON_IP="172.28.93.97"
```

## 🚀 Quick Start

### **Basic Usage**
```python
from myrvm_integration.api_client.myrvm_api_client import MyRVMAPIClient

# Initialize client
client = MyRVMAPIClient(
    base_url="http://172.28.233.83:8001",
    use_tunnel=False
)

# Login
success, response = client.login("admin@myrvm.com", "password")
if success:
    print(f"Login successful: {response['data']['token']}")
else:
    print(f"Login failed: {response['error']}")

# Register processing engine
engine_data = {
    'name': 'Jetson Orin Nano - CV System',
    'type': 'nvidia_cuda',
    'server_address': '172.28.93.97',
    'port': 5000,
    'gpu_memory_limit': 8,
    'docker_gpu_passthrough': True,
    'model_path': '/models/yolo11n.pt',
    'processing_timeout': 30,
    'auto_failover': True,
    'is_active': True
}

success, response = client.register_processing_engine(engine_data)
if success:
    print(f"Engine registered: {response['data']['id']}")
else:
    print(f"Registration failed: {response['error']}")
```

## 📚 API Reference

### **Authentication Methods**

#### **login(email, password)**
Authenticate with MyRVM Platform and obtain Bearer token.

```python
success, response = client.login("admin@myrvm.com", "password")
```

**Parameters:**
- `email` (str): User email address
- `password` (str): User password

**Returns:**
- `success` (bool): Authentication success status
- `response` (dict): Response data containing token and user info

**Example Response:**
```json
{
  "success": true,
  "data": {
    "token": "21|epxqGDMSdKgZ357EmWxlQBOuh4XtqRJD0WBzhs934cd94f41",
    "user": {
      "id": 1,
      "name": "Admin",
      "email": "admin@myrvm.com"
    }
  },
  "message": "Login successful"
}
```

### **Processing Engine Methods**

#### **register_processing_engine(engine_data)**
Register Jetson Orin as a processing engine.

```python
engine_data = {
    'name': 'Jetson Orin Nano - CV System',
    'type': 'nvidia_cuda',
    'server_address': '172.28.93.97',
    'port': 5000,
    'gpu_memory_limit': 8,
    'docker_gpu_passthrough': True,
    'model_path': '/models/yolo11n.pt',
    'processing_timeout': 30,
    'auto_failover': True,
    'is_active': True
}

success, response = client.register_processing_engine(engine_data)
```

**Parameters:**
- `engine_data` (dict): Engine configuration data

**Required Fields:**
- `name` (str): Engine name
- `type` (str): Engine type (`nvidia_cuda`, `jetson_edge`)
- `server_address` (str): IP address of the engine
- `port` (int): Port number (1-65535)

**Optional Fields:**
- `gpu_memory_limit` (int): GPU memory limit in GB
- `docker_gpu_passthrough` (bool): Enable Docker GPU passthrough
- `model_path` (str): Path to AI models
- `processing_timeout` (int): Processing timeout in seconds
- `auto_failover` (bool): Enable auto failover
- `is_active` (bool): Engine active status

**Returns:**
- `success` (bool): Registration success status
- `response` (dict): Response data containing engine info

#### **get_processing_engines()**
Get list of all processing engines.

```python
success, response = client.get_processing_engines()
```

**Returns:**
- `success` (bool): Request success status
- `response` (dict): Response data containing engines list

#### **get_processing_engine(engine_id)**
Get specific processing engine by ID.

```python
success, response = client.get_processing_engine(25)
```

**Parameters:**
- `engine_id` (int): Processing engine ID

**Returns:**
- `success` (bool): Request success status
- `response` (dict): Response data containing engine info

#### **update_processing_engine(engine_id, update_data)**
Update processing engine configuration.

```python
update_data = {
    'name': 'Updated Jetson Orin Nano - CV System',
    'is_active': False
}

success, response = client.update_processing_engine(25, update_data)
```

**Parameters:**
- `engine_id` (int): Processing engine ID
- `update_data` (dict): Update data

**Returns:**
- `success` (bool): Update success status
- `response` (dict): Response data containing updated engine info

#### **delete_processing_engine(engine_id)**
Delete processing engine.

```python
success, response = client.delete_processing_engine(25)
```

**Parameters:**
- `engine_id` (int): Processing engine ID

**Returns:**
- `success` (bool): Deletion success status
- `response` (dict): Response data

#### **ping_processing_engine(engine_id)**
Ping processing engine to check status.

```python
success, response = client.ping_processing_engine(25)
```

**Parameters:**
- `engine_id` (int): Processing engine ID

**Returns:**
- `success` (bool): Ping success status
- `response` (dict): Response data containing ping info

#### **assign_engine_to_rvm(engine_id, rvm_id, priority='secondary')**
Assign processing engine to RVM.

```python
success, response = client.assign_engine_to_rvm(25, 1, 'primary')
```

**Parameters:**
- `engine_id` (int): Processing engine ID
- `rvm_id` (int): RVM ID
- `priority` (str): Assignment priority (`primary`, `secondary`)

**Returns:**
- `success` (bool): Assignment success status
- `response` (dict): Response data

### **Detection Results Methods**

#### **upload_detection_results(detection_data)**
Upload detection results from computer vision processing.

```python
detection_data = {
    'rvm_id': 1,
    'image_path': '/storages/images/output/detection_20250918_150800.jpg',
    'detections': [
        {
            'class': 'plastic_bottle',
            'confidence': 0.95,
            'bbox': [100, 100, 200, 200],
            'segmentation_mask': 'base64_encoded_mask_data'
        }
    ],
    'status': 'processed',
    'timestamp': '2025-09-18T15:08:00.000000Z'
}

success, response = client.upload_detection_results(detection_data)
```

**Parameters:**
- `detection_data` (dict): Detection results data

**Required Fields:**
- `rvm_id` (int): RVM ID
- `image_path` (str): Path to detection image
- `detections` (list): List of detected objects

**Optional Fields:**
- `status` (str): Detection status (`pending`, `processed`, `failed`)
- `timestamp` (str): Detection timestamp

**Returns:**
- `success` (bool): Upload success status
- `response` (dict): Response data containing detection result info

#### **get_detection_results(rvm_id=None, limit=10)**
Get detection results.

```python
success, response = client.get_detection_results(rvm_id=1, limit=5)
```

**Parameters:**
- `rvm_id` (int, optional): Filter by RVM ID
- `limit` (int): Number of results to return

**Returns:**
- `success` (bool): Request success status
- `response` (dict): Response data containing detection results

### **Deposit Methods**

#### **create_deposit(deposit_data)**
Create a new waste deposit.

```python
deposit_data = {
    'rvm_id': 1,
    'user_id': 1,
    'waste_type': 'plastic',
    'quantity': 1,
    'weight': 0.5,
    'location': 'Jetson Orin Nano Test',
    'notes': 'Test deposit from API client'
}

success, response = client.create_deposit(deposit_data)
```

**Parameters:**
- `deposit_data` (dict): Deposit data

**Required Fields:**
- `rvm_id` (int): RVM ID
- `user_id` (int): User ID
- `waste_type` (str): Type of waste
- `quantity` (int): Number of items
- `weight` (float): Weight in kg

**Optional Fields:**
- `location` (str): Deposit location
- `notes` (str): Additional notes

**Returns:**
- `success` (bool): Creation success status
- `response` (dict): Response data containing deposit info

#### **get_deposits(limit=10)**
Get list of deposits.

```python
success, response = client.get_deposits(limit=20)
```

**Parameters:**
- `limit` (int): Number of deposits to return

**Returns:**
- `success` (bool): Request success status
- `response` (dict): Response data containing deposits list

#### **process_deposit(deposit_id, process_data)**
Process a deposit with AI analysis results.

```python
process_data = {
    'status': 'completed',
    'reward_amount': 100,
    'ai_analysis': 'Plastic bottle detected with 95% confidence',
    'cv_analysis': 'YOLO11 detection successful'
}

success, response = client.process_deposit(1, process_data)
```

**Parameters:**
- `deposit_id` (int): Deposit ID
- `process_data` (dict): Processing data

**Returns:**
- `success` (bool): Processing success status
- `response` (dict): Response data containing updated deposit info

### **RVM Status Methods**

#### **get_rvm_status(rvm_id)**
Get RVM status and latest detection results.

```python
success, response = client.get_rvm_status(1)
```

**Parameters:**
- `rvm_id` (int): RVM ID

**Returns:**
- `success` (bool): Request success status
- `response` (dict): Response data containing RVM status

#### **trigger_processing(rvm_id, command='run_inference')**
Trigger processing on RVM.

```python
success, response = client.trigger_processing(1, 'start_camera')
```

**Parameters:**
- `rvm_id` (int): RVM ID
- `command` (str): Processing command

**Returns:**
- `success` (bool): Trigger success status
- `response` (dict): Response data

### **File Upload Methods**

#### **upload_image_file(file_path, metadata)**
Upload image file to MyRVM Platform.

```python
metadata = {
    'rvm_id': 1,
    'detection_type': 'yolo11',
    'timestamp': '2025-09-18T15:08:00.000000Z'
}

success, response = client.upload_image_file('/path/to/image.jpg', metadata)
```

**Parameters:**
- `file_path` (str): Path to image file
- `metadata` (dict): File metadata

**Returns:**
- `success` (bool): Upload success status
- `response` (dict): Response data containing file info

### **Utility Methods**

#### **test_connectivity()**
Test connectivity to MyRVM Platform.

```python
success, response = client.test_connectivity()
```

**Returns:**
- `success` (bool): Connectivity success status
- `response` (dict): Response data

#### **switch_to_tunnel()**
Switch to tunnel URL for external access.

```python
client.switch_to_tunnel()
```

#### **switch_to_local()**
Switch to local URL for internal access.

```python
client.switch_to_local()
```

## 🔧 Advanced Usage

### **Error Handling**
```python
from myrvm_integration.api_client.myrvm_api_client import MyRVMAPIClient

client = MyRVMAPIClient(base_url="http://172.28.233.83:8001")

try:
    success, response = client.login("admin@myrvm.com", "password")
    if not success:
        print(f"Login failed: {response.get('error', 'Unknown error')}")
        return
    
    # Continue with other operations
    success, response = client.register_processing_engine(engine_data)
    if not success:
        print(f"Registration failed: {response.get('error', 'Unknown error')}")
        return
        
except Exception as e:
    print(f"Unexpected error: {e}")
```

### **Retry Mechanism**
```python
import time

def retry_operation(operation, max_retries=3, delay=2):
    for attempt in range(max_retries):
        try:
            success, response = operation()
            if success:
                return success, response
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    return False, {"error": "Max retries exceeded"}

# Usage
success, response = retry_operation(
    lambda: client.register_processing_engine(engine_data)
)
```

### **Batch Operations**
```python
def upload_multiple_detections(detection_list):
    results = []
    for detection in detection_list:
        success, response = client.upload_detection_results(detection)
        results.append({
            'detection': detection,
            'success': success,
            'response': response
        })
    return results

# Usage
detections = [
    {
        'rvm_id': 1,
        'image_path': '/path/to/image1.jpg',
        'detections': [{'class': 'plastic_bottle', 'confidence': 0.95}]
    },
    {
        'rvm_id': 1,
        'image_path': '/path/to/image2.jpg',
        'detections': [{'class': 'aluminum_can', 'confidence': 0.88}]
    }
]

results = upload_multiple_detections(detections)
```

### **Configuration Management**
```python
import json
from pathlib import Path

def load_config(config_path="config.json"):
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}

def save_config(config, config_path="config.json"):
    config_file = Path(config_path)
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

# Usage
config = load_config()
client = MyRVMAPIClient(
    base_url=config.get('myrvm_base_url'),
    use_tunnel=config.get('use_tunnel', False)
)
```

## 🧪 Testing

### **Unit Tests**
```python
import unittest
from myrvm_integration.api_client.myrvm_api_client import MyRVMAPIClient

class TestMyRVMAPIClient(unittest.TestCase):
    def setUp(self):
        self.client = MyRVMAPIClient(base_url="http://172.28.233.83:8001")
    
    def test_login(self):
        success, response = self.client.login("admin@myrvm.com", "password")
        self.assertTrue(success)
        self.assertIn('token', response.get('data', {}))
    
    def test_register_processing_engine(self):
        engine_data = {
            'name': 'Test Engine',
            'type': 'nvidia_cuda',
            'server_address': '172.28.93.97',
            'port': 5000
        }
        success, response = self.client.register_processing_engine(engine_data)
        self.assertTrue(success)
        self.assertIn('id', response.get('data', {}))

if __name__ == '__main__':
    unittest.main()
```

### **Integration Tests**
```python
def test_full_integration():
    client = MyRVMAPIClient(base_url="http://172.28.233.83:8001")
    
    # Test login
    success, response = client.login("admin@myrvm.com", "password")
    assert success, f"Login failed: {response}"
    
    # Test processing engine registration
    engine_data = {
        'name': 'Integration Test Engine',
        'type': 'nvidia_cuda',
        'server_address': '172.28.93.97',
        'port': 5000,
        'gpu_memory_limit': 8,
        'docker_gpu_passthrough': True,
        'model_path': '/models/yolo11n.pt',
        'processing_timeout': 30,
        'auto_failover': True,
        'is_active': True
    }
    
    success, response = client.register_processing_engine(engine_data)
    assert success, f"Engine registration failed: {response}"
    
    engine_id = response['data']['id']
    
    # Test detection results upload
    detection_data = {
        'rvm_id': 1,
        'image_path': '/test/detection.jpg',
        'detections': [
            {
                'class': 'plastic_bottle',
                'confidence': 0.95,
                'bbox': [100, 100, 200, 200]
            }
        ],
        'status': 'processed'
    }
    
    success, response = client.upload_detection_results(detection_data)
    assert success, f"Detection upload failed: {response}"
    
    # Test deposit creation
    deposit_data = {
        'rvm_id': 1,
        'user_id': 1,
        'waste_type': 'plastic',
        'quantity': 1,
        'weight': 0.5,
        'location': 'Integration Test',
        'notes': 'Test deposit from integration test'
    }
    
    success, response = client.create_deposit(deposit_data)
    assert success, f"Deposit creation failed: {response}"
    
    print("✅ All integration tests passed!")

if __name__ == '__main__':
    test_full_integration()
```

## 🔍 Debugging

### **Enable Debug Logging**
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Create client with debug mode
client = MyRVMAPIClient(
    base_url="http://172.28.233.83:8001",
    debug=True
)
```

### **Log Analysis**
```python
def analyze_logs(log_file="api_client.log"):
    with open(log_file, 'r') as f:
        logs = f.readlines()
    
    errors = [log for log in logs if 'ERROR' in log]
    warnings = [log for log in logs if 'WARNING' in log]
    
    print(f"Total logs: {len(logs)}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    
    if errors:
        print("\nRecent errors:")
        for error in errors[-5:]:
            print(error.strip())

# Usage
analyze_logs()
```

### **Network Diagnostics**
```python
def diagnose_network():
    import requests
    import time
    
    base_url = "http://172.28.233.83:8001"
    
    # Test basic connectivity
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        response_time = time.time() - start_time
        print(f"✅ Basic connectivity: {response.status_code} ({response_time:.2f}s)")
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
    
    # Test API endpoint
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/api/v2/processing-engines", timeout=10)
        response_time = time.time() - start_time
        print(f"✅ API endpoint: {response.status_code} ({response_time:.2f}s)")
    except Exception as e:
        print(f"❌ API endpoint failed: {e}")

# Usage
diagnose_network()
```

## 📊 Performance Monitoring

### **Response Time Monitoring**
```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper

# Usage
@monitor_performance
def register_engine():
    return client.register_processing_engine(engine_data)
```

### **Success Rate Tracking**
```python
class APIClientMonitor:
    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.response_times = []
    
    def track_request(self, success, response_time):
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        self.response_times.append(response_time)
    
    def get_stats(self):
        total = self.success_count + self.error_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'total_requests': total
        }

# Usage
monitor = APIClientMonitor()
# Track requests in your API calls
```

## 🚨 Error Handling

### **Common Error Codes**
- **400 Bad Request:** Invalid request data
- **401 Unauthorized:** Authentication failed
- **403 Forbidden:** Insufficient permissions
- **404 Not Found:** Resource not found
- **422 Validation Error:** Invalid field values
- **500 Internal Server Error:** Server-side error

### **Error Response Format**
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "type": ["The selected type is invalid."],
    "server_address": ["The server address field is required."]
  }
}
```

### **Error Handling Best Practices**
```python
def handle_api_error(response):
    if response.get('success', False):
        return True, response
    
    error_message = response.get('message', 'Unknown error')
    errors = response.get('errors', {})
    
    if errors:
        error_details = []
        for field, messages in errors.items():
            error_details.append(f"{field}: {', '.join(messages)}")
        error_message += f" - {', '.join(error_details)}"
    
    return False, {'error': error_message}

# Usage
success, response = client.register_processing_engine(engine_data)
if not success:
    success, error_info = handle_api_error(response)
    print(f"Error: {error_info['error']}")
```

## 📚 Examples

### **Complete Integration Example**
```python
#!/usr/bin/env python3
"""
Complete MyRVM Platform Integration Example
"""

from myrvm_integration.api_client.myrvm_api_client import MyRVMAPIClient
import json
import time

def main():
    # Initialize client
    client = MyRVMAPIClient(
        base_url="http://172.28.233.83:8001",
        use_tunnel=False
    )
    
    print("🚀 MyRVM Platform Integration Example")
    print("=" * 50)
    
    # Step 1: Login
    print("🔐 Logging in...")
    success, response = client.login("admin@myrvm.com", "password")
    if not success:
        print(f"❌ Login failed: {response.get('error', 'Unknown error')}")
        return
    
    print(f"✅ Login successful: {response['data']['token'][:50]}...")
    
    # Step 2: Register processing engine
    print("\n🤖 Registering processing engine...")
    engine_data = {
        'name': 'Jetson Orin Nano - CV System',
        'type': 'nvidia_cuda',
        'server_address': '172.28.93.97',
        'port': 5000,
        'gpu_memory_limit': 8,
        'docker_gpu_passthrough': True,
        'model_path': '/models/yolo11n.pt',
        'processing_timeout': 30,
        'auto_failover': True,
        'is_active': True
    }
    
    success, response = client.register_processing_engine(engine_data)
    if not success:
        print(f"❌ Engine registration failed: {response.get('error', 'Unknown error')}")
        return
    
    engine_id = response['data']['id']
    print(f"✅ Engine registered: ID {engine_id}")
    
    # Step 3: Upload detection results
    print("\n📸 Uploading detection results...")
    detection_data = {
        'rvm_id': 1,
        'image_path': '/storages/images/output/detection_20250918_150800.jpg',
        'detections': [
            {
                'class': 'plastic_bottle',
                'confidence': 0.95,
                'bbox': [100, 100, 200, 200],
                'segmentation_mask': 'base64_encoded_mask_data'
            }
        ],
        'status': 'processed',
        'timestamp': '2025-09-18T15:08:00.000000Z'
    }
    
    success, response = client.upload_detection_results(detection_data)
    if not success:
        print(f"❌ Detection upload failed: {response.get('error', 'Unknown error')}")
        return
    
    print(f"✅ Detection results uploaded: ID {response['data']['id']}")
    
    # Step 4: Create deposit
    print("\n💰 Creating deposit...")
    deposit_data = {
        'rvm_id': 1,
        'user_id': 1,
        'waste_type': 'plastic',
        'quantity': 1,
        'weight': 0.5,
        'location': 'Jetson Orin Nano Test',
        'notes': 'Test deposit from API client example'
    }
    
    success, response = client.create_deposit(deposit_data)
    if not success:
        print(f"❌ Deposit creation failed: {response.get('error', 'Unknown error')}")
        return
    
    deposit_id = response['data']['id']
    print(f"✅ Deposit created: ID {deposit_id}")
    
    # Step 5: Get RVM status
    print("\n📊 Getting RVM status...")
    success, response = client.get_rvm_status(1)
    if not success:
        print(f"❌ RVM status failed: {response.get('error', 'Unknown error')}")
        return
    
    print(f"✅ RVM status: {response['data']['current_status']}")
    
    print("\n🎉 Integration example completed successfully!")

if __name__ == '__main__':
    main()
```

## 📞 Support

### **Common Issues**
1. **Authentication Issues:** Check credentials and token format
2. **Network Connectivity:** Verify ZeroTier network status
3. **Validation Errors:** Ensure all required fields are provided
4. **Server Errors:** Check server-side logs and configuration

### **Debug Commands**
```bash
# Test basic connectivity
curl http://172.28.233.83:8001/

# Test authentication
curl -X POST http://172.28.233.83:8001/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@myrvm.com","password":"password"}'

# Test processing engines endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://172.28.233.83:8001/api/v2/processing-engines
```

### **Logs Location**
- **API Client Logs:** `myrvm-integration/logs/api_client_*.log`
- **Integration Test Logs:** `myrvm-integration/logs/integration_test_results.log`
- **Processing Engine Test Logs:** `myrvm-integration/logs/processing_engine_test_results.log`

## 📚 Related Documentation

- [Changelog](../docs/CHANGELOG.md)
- [Technical Changes](../docs/TECHNICAL_CHANGES.md)
- [Deployment Guide](../docs/DEPLOYMENT_GUIDE.md)
- [API Reference](../docs/API_REFERENCE.md)
- [Integration Test Report](../docs/INTEGRATION_TEST_REPORT.md)

---

**Last Updated:** September 18, 2025  
**Next Review:** September 25, 2025  
**Maintainer:** AI Assistant  
**Status:** ✅ Production Ready
