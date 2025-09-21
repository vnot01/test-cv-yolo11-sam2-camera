# TASK 05: DYNAMIC CONFIGURATION GENERATOR

**Tanggal**: 2025-09-21  
**Versi**: 1.0.0  
**Status**: 📋 PLANNING  
**Priority**: HIGH  

---

## **🎯 OBJECTIVE**

Membuat Dynamic Configuration Generator untuk auto-detect hardware info, network info, generate unique RVM ID, dan generate production_config.json secara dinamis.

---

## **📋 REQUIREMENTS**

### **Functional Requirements:**
- **Hardware Auto-Detection** (MAC address, serial number, model, capabilities)
- **Network Auto-Detection** (IP addresses, gateway, DNS, VPN info)
- **RVM ID Generation** (unique identifier based on hardware)
- **Configuration Template Management** (default, custom, location-specific)
- **Dynamic Configuration Generation** (production_config.json)
- **Configuration Validation** dan error handling
- **Configuration Backup** dan restore
- **Real-time Configuration Updates** dari server

### **Technical Requirements:**
- **Hardware Information Collection** (system info, device info)
- **Network Information Collection** (IP, routing, DNS, VPN)
- **Unique ID Generation** (MAC-based, hash-based, timestamp-based)
- **Configuration Template System** (JSON templates, variable substitution)
- **Configuration Validation** (schema validation, dependency checking)
- **Configuration Persistence** (file storage, backup, versioning)

---

## **🔧 IMPLEMENTATION PLAN**

### **1. Dynamic Configuration Generator Structure**
```
dynamic_config_generator/
├── __init__.py
├── hardware_detector.py      # Hardware information detection
├── network_detector.py       # Network information detection
├── rvm_id_generator.py       # Unique RVM ID generation
├── config_template_manager.py # Configuration template management
├── config_generator.py       # Main configuration generator
├── config_validator.py       # Configuration validation
├── config_storage.py         # Configuration storage & backup
└── utils/
    ├── system_utils.py
    ├── crypto_utils.py
    └── validation_utils.py
```

### **2. Core Features Implementation**

#### **A. Hardware Detector**
```python
class HardwareDetector:
    def detect_system_info(self):
        # Detect system information
        
    def detect_device_info(self):
        # Detect device information
        
    def detect_capabilities(self):
        # Detect hardware capabilities
```

#### **B. Network Detector**
```python
class NetworkDetector:
    def detect_network_info(self):
        # Detect network information
        
    def detect_vpn_info(self):
        # Detect VPN information
        
    def detect_server_connectivity(self):
        # Detect server connectivity
```

#### **C. RVM ID Generator**
```python
class RVMIDGenerator:
    def generate_unique_id(self):
        # Generate unique RVM ID
        
    def validate_id_uniqueness(self):
        # Validate ID uniqueness
```

---

## **📝 DETAILED IMPLEMENTATION**

### **1. Hardware Detector Module**

#### **Hardware Information Detection:**
```python
import platform
import subprocess
import json
import hashlib
import uuid
import psutil
import socket
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class HardwareInfo:
    system_info: Dict[str, Any]
    device_info: Dict[str, Any]
    capabilities: Dict[str, Any]
    unique_identifiers: Dict[str, str]

class HardwareDetector:
    def __init__(self):
        self.hardware_info = None
        
    def detect_all_hardware(self) -> HardwareInfo:
        """Detect all hardware information"""
        hardware_info = HardwareInfo(
            system_info=self.detect_system_info(),
            device_info=self.detect_device_info(),
            capabilities=self.detect_capabilities(),
            unique_identifiers=self.detect_unique_identifiers()
        )
        
        self.hardware_info = hardware_info
        return hardware_info
    
    def detect_system_info(self) -> Dict[str, Any]:
        """Detect system information"""
        system_info = {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'hostname': platform.node(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'memory': psutil.virtual_memory()._asdict(),
            'disk': psutil.disk_usage('/')._asdict(),
            'boot_time': psutil.boot_time(),
            'uptime': time.time() - psutil.boot_time()
        }
        
        # Detect Jetson-specific info
        jetson_info = self._detect_jetson_info()
        system_info.update(jetson_info)
        
        return system_info
    
    def _detect_jetson_info(self) -> Dict[str, Any]:
        """Detect Jetson-specific information"""
        jetson_info = {
            'is_jetson': False,
            'jetson_model': None,
            'jetson_serial': None,
            'jetson_part_number': None,
            'jetson_cuda_version': None,
            'jetson_cudnn_version': None,
            'jetson_tensorrt_version': None
        }
        
        try:
            # Check if running on Jetson
            if os.path.exists('/etc/nv_tegra_release'):
                jetson_info['is_jetson'] = True
                
                # Read Jetson model info
                with open('/etc/nv_tegra_release', 'r') as f:
                    content = f.read()
                    jetson_info['jetson_model'] = content.strip()
                
                # Get Jetson serial number
                try:
                    result = subprocess.run(['cat', '/proc/device-tree/serial-number'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        jetson_info['jetson_serial'] = result.stdout.strip()
                except:
                    pass
                
                # Get Jetson part number
                try:
                    result = subprocess.run(['cat', '/proc/device-tree/model'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        jetson_info['jetson_part_number'] = result.stdout.strip()
                except:
                    pass
                
                # Check CUDA version
                try:
                    result = subprocess.run(['nvcc', '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        jetson_info['jetson_cuda_version'] = result.stdout.strip()
                except:
                    pass
                
                # Check cuDNN version
                try:
                    result = subprocess.run(['cat', '/usr/include/cudnn_version.h'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        content = result.stdout
                        if 'CUDNN_MAJOR' in content:
                            jetson_info['jetson_cudnn_version'] = 'Available'
                except:
                    pass
                
                # Check TensorRT version
                try:
                    result = subprocess.run(['dpkg', '-l', 'tensorrt'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        jetson_info['jetson_tensorrt_version'] = 'Available'
                except:
                    pass
                    
        except Exception as e:
            print(f"Error detecting Jetson info: {e}")
        
        return jetson_info
    
    def detect_device_info(self) -> Dict[str, Any]:
        """Detect device information"""
        device_info = {
            'usb_devices': self._detect_usb_devices(),
            'pci_devices': self._detect_pci_devices(),
            'network_interfaces': self._detect_network_interfaces(),
            'storage_devices': self._detect_storage_devices(),
            'audio_devices': self._detect_audio_devices(),
            'video_devices': self._detect_video_devices(),
            'gpio_devices': self._detect_gpio_devices()
        }
        
        return device_info
    
    def _detect_usb_devices(self) -> List[Dict[str, Any]]:
        """Detect USB devices"""
        usb_devices = []
        
        try:
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line:
                        parts = line.split()
                        if len(parts) >= 6:
                            device = {
                                'bus': parts[1],
                                'device': parts[3].rstrip(':'),
                                'id': parts[5],
                                'description': ' '.join(parts[6:])
                            }
                            usb_devices.append(device)
        except Exception as e:
            print(f"Error detecting USB devices: {e}")
        
        return usb_devices
    
    def _detect_pci_devices(self) -> List[Dict[str, Any]]:
        """Detect PCI devices"""
        pci_devices = []
        
        try:
            result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line:
                        parts = line.split(': ', 1)
                        if len(parts) == 2:
                            device = {
                                'pci_id': parts[0],
                                'description': parts[1]
                            }
                            pci_devices.append(device)
        except Exception as e:
            print(f"Error detecting PCI devices: {e}")
        
        return pci_devices
    
    def _detect_network_interfaces(self) -> List[Dict[str, Any]]:
        """Detect network interfaces"""
        network_interfaces = []
        
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line and 'state' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            interface_name = parts[1].strip().split()[0]
                            
                            # Get interface details
                            interface_info = {
                                'name': interface_name,
                                'mac_address': self._get_interface_mac(interface_name),
                                'ip_address': self._get_interface_ip(interface_name),
                                'state': 'up' if 'state UP' in line else 'down'
                            }
                            network_interfaces.append(interface_info)
        except Exception as e:
            print(f"Error detecting network interfaces: {e}")
        
        return network_interfaces
    
    def _get_interface_mac(self, interface_name: str) -> Optional[str]:
        """Get MAC address of network interface"""
        try:
            result = subprocess.run(['cat', f'/sys/class/net/{interface_name}/address'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def _get_interface_ip(self, interface_name: str) -> Optional[str]:
        """Get IP address of network interface"""
        try:
            result = subprocess.run(['ip', 'addr', 'show', interface_name], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'inet ' in line and not '127.0.0.1' in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith('192.168.') or part.startswith('10.') or part.startswith('172.'):
                                return part.split('/')[0]
        except:
            pass
        return None
    
    def _detect_storage_devices(self) -> List[Dict[str, Any]]:
        """Detect storage devices"""
        storage_devices = []
        
        try:
            result = subprocess.run(['lsblk', '-J'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for device in data.get('blockdevices', []):
                    device_info = {
                        'name': device.get('name'),
                        'type': device.get('type'),
                        'size': device.get('size'),
                        'mountpoint': device.get('mountpoint'),
                        'fstype': device.get('fstype')
                    }
                    storage_devices.append(device_info)
        except Exception as e:
            print(f"Error detecting storage devices: {e}")
        
        return storage_devices
    
    def _detect_audio_devices(self) -> List[Dict[str, Any]]:
        """Detect audio devices"""
        audio_devices = []
        
        try:
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'card' in line and 'device' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            device_info = {
                                'card': parts[0].split()[-1],
                                'description': parts[1].strip()
                            }
                            audio_devices.append(device_info)
        except Exception as e:
            print(f"Error detecting audio devices: {e}")
        
        return audio_devices
    
    def _detect_video_devices(self) -> List[Dict[str, Any]]:
        """Detect video devices"""
        video_devices = []
        
        try:
            result = subprocess.run(['ls', '/dev/video*'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                devices = result.stdout.strip().split('\n')
                for device in devices:
                    if device:
                        device_info = {
                            'device_path': device,
                            'device_name': device.split('/')[-1]
                        }
                        video_devices.append(device_info)
        except Exception as e:
            print(f"Error detecting video devices: {e}")
        
        return video_devices
    
    def _detect_gpio_devices(self) -> List[Dict[str, Any]]:
        """Detect GPIO devices"""
        gpio_devices = []
        
        try:
            result = subprocess.run(['ls', '/dev/gpiochip*'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                devices = result.stdout.strip().split('\n')
                for device in devices:
                    if device:
                        device_info = {
                            'device_path': device,
                            'device_name': device.split('/')[-1]
                        }
                        gpio_devices.append(device_info)
        except Exception as e:
            print(f"Error detecting GPIO devices: {e}")
        
        return gpio_devices
    
    def detect_capabilities(self) -> Dict[str, Any]:
        """Detect hardware capabilities"""
        capabilities = {
            'camera_available': self._check_camera_capability(),
            'gpio_available': self._check_gpio_capability(),
            'audio_available': self._check_audio_capability(),
            'network_available': self._check_network_capability(),
            'storage_available': self._check_storage_capability(),
            'ai_acceleration': self._check_ai_acceleration(),
            'gpu_available': self._check_gpu_capability()
        }
        
        return capabilities
    
    def _check_camera_capability(self) -> bool:
        """Check if camera is available"""
        try:
            result = subprocess.run(['ls', '/dev/video*'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and result.stdout.strip()
        except:
            return False
    
    def _check_gpio_capability(self) -> bool:
        """Check if GPIO is available"""
        try:
            result = subprocess.run(['ls', '/dev/gpiochip*'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and result.stdout.strip()
        except:
            return False
    
    def _check_audio_capability(self) -> bool:
        """Check if audio is available"""
        try:
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and result.stdout.strip()
        except:
            return False
    
    def _check_network_capability(self) -> bool:
        """Check if network is available"""
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and result.stdout.strip()
        except:
            return False
    
    def _check_storage_capability(self) -> bool:
        """Check if storage is available"""
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and result.stdout.strip()
        except:
            return False
    
    def _check_ai_acceleration(self) -> bool:
        """Check if AI acceleration is available"""
        try:
            # Check for CUDA
            result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
            
            # Check for TensorRT
            result = subprocess.run(['dpkg', '-l', 'tensorrt'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
                
            return False
        except:
            return False
    
    def _check_gpu_capability(self) -> bool:
        """Check if GPU is available"""
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def detect_unique_identifiers(self) -> Dict[str, str]:
        """Detect unique identifiers"""
        identifiers = {
            'mac_address': self._get_primary_mac_address(),
            'serial_number': self._get_serial_number(),
            'machine_id': self._get_machine_id(),
            'uuid': str(uuid.uuid4()),
            'hardware_hash': None
        }
        
        # Generate hardware hash
        hardware_data = {
            'mac_address': identifiers['mac_address'],
            'serial_number': identifiers['serial_number'],
            'machine_id': identifiers['machine_id']
        }
        
        hardware_string = json.dumps(hardware_data, sort_keys=True)
        identifiers['hardware_hash'] = hashlib.sha256(hardware_string.encode()).hexdigest()
        
        return identifiers
    
    def _get_primary_mac_address(self) -> Optional[str]:
        """Get primary MAC address"""
        try:
            # Get MAC address of the first non-loopback interface
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line and 'state UP' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            interface_name = parts[1].strip().split()[0]
                            if interface_name != 'lo':
                                mac = self._get_interface_mac(interface_name)
                                if mac:
                                    return mac
        except:
            pass
        return None
    
    def _get_serial_number(self) -> Optional[str]:
        """Get system serial number"""
        try:
            # Try Jetson serial number first
            if os.path.exists('/proc/device-tree/serial-number'):
                result = subprocess.run(['cat', '/proc/device-tree/serial-number'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return result.stdout.strip()
            
            # Try DMI serial number
            result = subprocess.run(['cat', '/sys/class/dmi/id/product_serial'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
                
        except:
            pass
        return None
    
    def _get_machine_id(self) -> Optional[str]:
        """Get machine ID"""
        try:
            result = subprocess.run(['cat', '/etc/machine-id'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
```

---

## **🧪 TESTING STRATEGY**

### **Unit Testing:**
- **Hardware detection** testing
- **Network detection** testing
- **RVM ID generation** testing
- **Configuration generation** testing

### **Integration Testing:**
- **Hardware integration** testing
- **Network integration** testing
- **Configuration validation** testing
- **Template management** testing

### **System Testing:**
- **End-to-end** configuration generation
- **Hardware compatibility** testing
- **Network connectivity** testing
- **Configuration persistence** testing

---

## **📊 SUCCESS CRITERIA**

### **Functional Success:**
- ✅ Hardware auto-detection
- ✅ Network auto-detection
- ✅ RVM ID generation
- ✅ Configuration template management
- ✅ Dynamic configuration generation
- ✅ Configuration validation
- ✅ Configuration backup/restore
- ✅ Real-time configuration updates

### **Technical Success:**
- ✅ Hardware information collection
- ✅ Network information collection
- ✅ Unique ID generation
- ✅ Configuration template system
- ✅ Configuration validation
- ✅ Configuration persistence

### **Integration Success:**
- ✅ Hardware detection integration
- ✅ Network detection integration
- ✅ Configuration management integration
- ✅ Real-time updates

---

## **⏱️ ESTIMATED TIMELINE**

### **Week 1: Core Detection Modules**
- **Day 1-2**: Hardware detector module
- **Day 3-4**: Network detector module
- **Day 5**: RVM ID generator

### **Week 2: Configuration Management**
- **Day 1-2**: Configuration template manager
- **Day 3-4**: Configuration generator
- **Day 5**: Configuration validator

### **Week 3: Storage & Integration**
- **Day 1-2**: Configuration storage
- **Day 3-4**: Integration testing
- **Day 5**: Real-time updates

### **Week 4: Testing & Documentation**
- **Day 1-2**: Unit testing
- **Day 3-4**: Integration testing
- **Day 5**: Documentation

---

## **📁 DELIVERABLES**

### **Code Files:**
- `hardware_detector.py`
- `network_detector.py`
- `rvm_id_generator.py`
- `config_template_manager.py`
- `config_generator.py`
- `config_validator.py`
- `config_storage.py`

### **Documentation:**
- API documentation
- Configuration guide
- Template guide
- Troubleshooting guide

### **Testing:**
- Unit tests
- Integration tests
- System tests
- Performance tests

---

**Status**: 📋 **READY FOR IMPLEMENTATION**  
**Estimated Time**: 4 weeks  
**Difficulty**: Advanced  
**Dependencies**: Hardware detection, Network management, Configuration templates, Web interface