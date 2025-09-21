# TASK 02: REMOTE COMMAND EXECUTOR

**Tanggal**: 2025-01-20  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 2-3 hari  
**Assigned**: RVM Jetson Orin (MyRVM-Integration)

---

## **📋 DESKRIPSI TUGAS**

Implementasi Remote Command Executor di RVM Jetson Orin untuk menerima dan mengeksekusi perintah remote dari MyRVM Platform, termasuk hardware control, process management, dan system commands.

### **🎯 TUJUAN:**
- Implementasi remote command receiver via WebSocket
- Hardware control commands (buka/tutup pintu, tes motor)
- Process management commands (restart app, reboot system, shutdown)
- System control commands (maintenance mode, diagnostics)
- Command execution tracking dan status reporting

---

## **🔧 IMPLEMENTASI**

### **1. Remote Command Receiver**

#### **A. WebSocket Command Receiver:**
```python
# File: myrvm-integration/remote/command_receiver.py

import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import time

class RemoteCommandReceiver:
    def __init__(self, server_url: str, rvm_id: int, api_key: str):
        self.server_url = server_url
        self.rvm_id = rvm_id
        self.api_key = api_key
        self.websocket = None
        self.is_connected = False
        self.is_running = False
        self.reconnect_interval = 5  # seconds
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
        self.command_executor = None
        
    def start(self):
        """Start command receiver"""
        if self.is_running:
            return
        
        self.is_running = True
        self.command_executor = RemoteCommandExecutor()
        self.command_executor.start()
        
        # Start WebSocket connection in separate thread
        self.ws_thread = threading.Thread(target=self._websocket_loop, daemon=True)
        self.ws_thread.start()
        
        logging.info(f"Remote command receiver started for RVM {self.rvm_id}")
    
    def stop(self):
        """Stop command receiver"""
        self.is_running = False
        self.is_connected = False
        
        if self.websocket:
            asyncio.run(self._close_websocket())
        
        if self.command_executor:
            self.command_executor.stop()
        
        logging.info(f"Remote command receiver stopped for RVM {self.rvm_id}")
    
    def _websocket_loop(self):
        """Main WebSocket connection loop"""
        while self.is_running:
            try:
                asyncio.run(self._connect_and_listen())
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
                
            if self.is_running:
                time.sleep(self.reconnect_interval)
    
    async def _connect_and_listen(self):
        """Connect to WebSocket and listen for commands"""
        try:
            ws_url = f"ws://{self.server_url}/ws/rvm/{self.rvm_id}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'X-RVM-ID': str(self.rvm_id)
            }
            
            async with websockets.connect(ws_url, extra_headers=headers) as websocket:
                self.websocket = websocket
                self.is_connected = True
                self.reconnect_attempts = 0
                
                logging.info(f"Connected to WebSocket for RVM {self.rvm_id}")
                
                # Send heartbeat
                await self._send_heartbeat()
                
                # Listen for commands
                async for message in websocket:
                    if not self.is_running:
                        break
                    
                    try:
                        command_data = json.loads(message)
                        await self._handle_command(command_data)
                    except json.JSONDecodeError as e:
                        logging.error(f"Invalid JSON received: {e}")
                    except Exception as e:
                        logging.error(f"Error handling command: {e}")
                        
        except Exception as e:
            logging.error(f"WebSocket connection error: {e}")
            self.is_connected = False
            self.reconnect_attempts += 1
            
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logging.error("Max reconnection attempts reached")
                self.is_running = False
    
    async def _handle_command(self, command_data: Dict[str, Any]):
        """Handle incoming command"""
        try:
            command_id = command_data.get('command_id')
            command_type = command_data.get('command_type')
            command_name = command_data.get('command_name')
            command_payload = command_data.get('command_payload', {})
            
            logging.info(f"Received command: {command_name} (ID: {command_id})")
            
            # Update command status to executing
            await self._update_command_status(command_id, 'executing', 'Command received and executing')
            
            # Execute command
            result = await self._execute_command(command_type, command_name, command_payload)
            
            # Update command status
            if result['success']:
                await self._update_command_status(command_id, 'completed', 'Command executed successfully', result)
            else:
                await self._update_command_status(command_id, 'failed', result['error'], result)
                
        except Exception as e:
            logging.error(f"Error handling command: {e}")
            await self._update_command_status(command_id, 'failed', str(e))
    
    async def _execute_command(self, command_type: str, command_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute remote command"""
        try:
            if command_type == 'HARDWARE_CONTROL':
                return await self._execute_hardware_command(command_name, payload)
            elif command_type == 'PROCESS_MANAGEMENT':
                return await self._execute_process_command(command_name, payload)
            elif command_type == 'SYSTEM_CONTROL':
                return await self._execute_system_command(command_name, payload)
            elif command_type == 'DIAGNOSTICS':
                return await self._execute_diagnostics_command(command_name, payload)
            else:
                return {'success': False, 'error': f'Unknown command type: {command_type}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_hardware_command(self, command_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hardware control command"""
        try:
            if command_name == 'open_door':
                return await self.command_executor.open_door()
            elif command_name == 'close_door':
                return await self.command_executor.close_door()
            elif command_name == 'test_motor':
                return await self.command_executor.test_motor()
            elif command_name == 'test_sensors':
                return await self.command_executor.test_sensors()
            else:
                return {'success': False, 'error': f'Unknown hardware command: {command_name}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_process_command(self, command_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute process management command"""
        try:
            if command_name == 'restart_app':
                return await self.command_executor.restart_app()
            elif command_name == 'reboot_system':
                return await self.command_executor.reboot_system()
            elif command_name == 'shutdown_system':
                return await self.command_executor.shutdown_system()
            else:
                return {'success': False, 'error': f'Unknown process command: {command_name}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_system_command(self, command_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system control command"""
        try:
            if command_name == 'enter_maintenance':
                return await self.command_executor.enter_maintenance_mode()
            elif command_name == 'exit_maintenance':
                return await self.command_executor.exit_maintenance_mode()
            elif command_name == 'update_config':
                return await self.command_executor.update_config(payload)
            else:
                return {'success': False, 'error': f'Unknown system command: {command_name}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_diagnostics_command(self, command_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute diagnostics command"""
        try:
            if command_name == 'take_snapshot':
                return await self.command_executor.take_snapshot()
            elif command_name == 'get_logs':
                return await self.command_executor.get_logs()
            elif command_name == 'system_info':
                return await self.command_executor.get_system_info()
            else:
                return {'success': False, 'error': f'Unknown diagnostics command: {command_name}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _update_command_status(self, command_id: int, status: str, message: str, result: Optional[Dict] = None):
        """Update command status on server"""
        try:
            status_data = {
                'command_id': command_id,
                'status': status,
                'progress_message': message,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send via WebSocket if connected
            if self.websocket and self.is_connected:
                await self.websocket.send(json.dumps({
                    'type': 'command_status_update',
                    'data': status_data
                }))
            
            # Also send via HTTP API as backup
            await self._send_status_via_api(command_id, status, message, result)
            
        except Exception as e:
            logging.error(f"Error updating command status: {e}")
    
    async def _send_status_via_api(self, command_id: int, status: str, message: str, result: Optional[Dict] = None):
        """Send command status via HTTP API"""
        try:
            import aiohttp
            
            status_data = {
                'status': status,
                'progress_message': message,
                'result': result
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"http://{self.server_url}/admin/rvm/{self.rvm_id}/command/{command_id}/status",
                    json=status_data,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'X-RVM-ID': str(self.rvm_id)
                    }
                ) as response:
                    if response.status == 200:
                        logging.info(f"Command status updated via API: {command_id} - {status}")
                    else:
                        logging.error(f"Failed to update command status via API: {response.status}")
                        
        except Exception as e:
            logging.error(f"Error sending status via API: {e}")
    
    async def _send_heartbeat(self):
        """Send heartbeat to server"""
        try:
            if self.websocket and self.is_connected:
                heartbeat_data = {
                    'type': 'heartbeat',
                    'rvm_id': self.rvm_id,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'online'
                }
                await self.websocket.send(json.dumps(heartbeat_data))
        except Exception as e:
            logging.error(f"Error sending heartbeat: {e}")
    
    async def _close_websocket(self):
        """Close WebSocket connection"""
        try:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
        except Exception as e:
            logging.error(f"Error closing WebSocket: {e}")
```

### **2. Remote Command Executor**

#### **A. Command Executor Implementation:**
```python
# File: myrvm-integration/remote/command_executor.py

import asyncio
import subprocess
import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import time

class RemoteCommandExecutor:
    def __init__(self):
        self.is_running = False
        self.maintenance_mode = False
        self.door_status = 'closed'
        self.motor_status = 'idle'
        
    def start(self):
        """Start command executor"""
        self.is_running = True
        logging.info("Remote command executor started")
    
    def stop(self):
        """Stop command executor"""
        self.is_running = False
        logging.info("Remote command executor stopped")
    
    # Hardware Control Commands
    
    async def open_door(self) -> Dict[str, Any]:
        """Open door for testing and diagnostics"""
        try:
            logging.info("Executing: Open door")
            
            # Simulate door opening (replace with actual hardware control)
            await asyncio.sleep(1)  # Simulate operation time
            
            self.door_status = 'open'
            
            return {
                'success': True,
                'message': 'Door opened successfully',
                'door_status': self.door_status,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error opening door: {e}")
            return {'success': False, 'error': str(e)}
    
    async def close_door(self) -> Dict[str, Any]:
        """Close door"""
        try:
            logging.info("Executing: Close door")
            
            # Simulate door closing (replace with actual hardware control)
            await asyncio.sleep(1)  # Simulate operation time
            
            self.door_status = 'closed'
            
            return {
                'success': True,
                'message': 'Door closed successfully',
                'door_status': self.door_status,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error closing door: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_motor(self) -> Dict[str, Any]:
        """Test motor sorting mechanism"""
        try:
            logging.info("Executing: Test motor")
            
            # Simulate motor test (replace with actual hardware control)
            await asyncio.sleep(3)  # Simulate operation time
            
            self.motor_status = 'testing'
            
            # Simulate test results
            test_results = {
                'motor_speed': 'normal',
                'motor_temperature': 'normal',
                'motor_vibration': 'normal',
                'test_duration': 3
            }
            
            self.motor_status = 'idle'
            
            return {
                'success': True,
                'message': 'Motor test completed successfully',
                'motor_status': self.motor_status,
                'test_results': test_results,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error testing motor: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_sensors(self) -> Dict[str, Any]:
        """Test all sensors"""
        try:
            logging.info("Executing: Test sensors")
            
            # Simulate sensor test (replace with actual hardware control)
            await asyncio.sleep(2)  # Simulate operation time
            
            # Simulate sensor test results
            sensor_results = {
                'camera_sensor': 'working',
                'weight_sensor': 'working',
                'proximity_sensor': 'working',
                'door_sensor': 'working',
                'temperature_sensor': 'working'
            }
            
            return {
                'success': True,
                'message': 'Sensor test completed successfully',
                'sensor_results': sensor_results,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error testing sensors: {e}")
            return {'success': False, 'error': str(e)}
    
    # Process Management Commands
    
    async def restart_app(self) -> Dict[str, Any]:
        """Restart MyRVM application"""
        try:
            logging.info("Executing: Restart application")
            
            # Schedule restart after 5 seconds
            def restart_after_delay():
                time.sleep(5)
                os.execv(sys.executable, [sys.executable] + sys.argv)
            
            restart_thread = threading.Thread(target=restart_after_delay, daemon=True)
            restart_thread.start()
            
            return {
                'success': True,
                'message': 'Application restart scheduled in 5 seconds',
                'restart_time': (datetime.now().timestamp() + 5),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error restarting application: {e}")
            return {'success': False, 'error': str(e)}
    
    async def reboot_system(self) -> Dict[str, Any]:
        """Reboot Jetson Orin system"""
        try:
            logging.info("Executing: Reboot system")
            
            # Schedule reboot after 10 seconds
            def reboot_after_delay():
                time.sleep(10)
                subprocess.run(['sudo', 'reboot'], check=True)
            
            reboot_thread = threading.Thread(target=reboot_after_delay, daemon=True)
            reboot_thread.start()
            
            return {
                'success': True,
                'message': 'System reboot scheduled in 10 seconds',
                'reboot_time': (datetime.now().timestamp() + 10),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error rebooting system: {e}")
            return {'success': False, 'error': str(e)}
    
    async def shutdown_system(self) -> Dict[str, Any]:
        """Shutdown Jetson Orin system"""
        try:
            logging.info("Executing: Shutdown system")
            
            # Schedule shutdown after 10 seconds
            def shutdown_after_delay():
                time.sleep(10)
                subprocess.run(['sudo', 'shutdown', 'now'], check=True)
            
            shutdown_thread = threading.Thread(target=shutdown_after_delay, daemon=True)
            shutdown_thread.start()
            
            return {
                'success': True,
                'message': 'System shutdown scheduled in 10 seconds',
                'shutdown_time': (datetime.now().timestamp() + 10),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error shutting down system: {e}")
            return {'success': False, 'error': str(e)}
    
    # System Control Commands
    
    async def enter_maintenance_mode(self) -> Dict[str, Any]:
        """Enter maintenance mode"""
        try:
            logging.info("Executing: Enter maintenance mode")
            
            self.maintenance_mode = True
            
            # Update GUI to show maintenance message
            await self._update_gui_maintenance_message("System is in maintenance mode. Please wait...")
            
            return {
                'success': True,
                'message': 'Entered maintenance mode successfully',
                'maintenance_mode': self.maintenance_mode,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error entering maintenance mode: {e}")
            return {'success': False, 'error': str(e)}
    
    async def exit_maintenance_mode(self) -> Dict[str, Any]:
        """Exit maintenance mode"""
        try:
            logging.info("Executing: Exit maintenance mode")
            
            self.maintenance_mode = False
            
            # Update GUI to show normal operation
            await self._update_gui_maintenance_message("System is ready for operation")
            
            return {
                'success': True,
                'message': 'Exited maintenance mode successfully',
                'maintenance_mode': self.maintenance_mode,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error exiting maintenance mode: {e}")
            return {'success': False, 'error': str(e)}
    
    async def update_config(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration"""
        try:
            logging.info("Executing: Update configuration")
            
            config_data = payload.get('config_data', {})
            
            # Update configuration file
            config_file = os.path.join(os.getcwd(), 'config', 'config.json')
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return {
                'success': True,
                'message': 'Configuration updated successfully',
                'config_file': config_file,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error updating configuration: {e}")
            return {'success': False, 'error': str(e)}
    
    # Diagnostics Commands
    
    async def take_snapshot(self) -> Dict[str, Any]:
        """Take camera snapshot for testing"""
        try:
            logging.info("Executing: Take snapshot")
            
            # Simulate camera snapshot (replace with actual camera capture)
            await asyncio.sleep(2)  # Simulate operation time
            
            # Generate snapshot filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            snapshot_file = f"snapshot_{timestamp}.jpg"
            snapshot_path = os.path.join(os.getcwd(), 'snapshots', snapshot_file)
            
            # Create snapshots directory if it doesn't exist
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            
            # Simulate snapshot creation (replace with actual camera capture)
            with open(snapshot_path, 'w') as f:
                f.write("Simulated snapshot data")
            
            return {
                'success': True,
                'message': 'Snapshot taken successfully',
                'snapshot_file': snapshot_file,
                'snapshot_path': snapshot_path,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error taking snapshot: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_logs(self) -> Dict[str, Any]:
        """Get application logs"""
        try:
            logging.info("Executing: Get logs")
            
            # Get log files
            log_dir = os.path.join(os.getcwd(), 'logs')
            log_files = []
            
            if os.path.exists(log_dir):
                for file in os.listdir(log_dir):
                    if file.endswith('.log'):
                        file_path = os.path.join(log_dir, file)
                        stat = os.stat(file_path)
                        log_files.append({
                            'filename': file,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
            
            return {
                'success': True,
                'message': 'Logs retrieved successfully',
                'log_files': log_files,
                'log_directory': log_dir,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error getting logs: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            logging.info("Executing: Get system info")
            
            # Get system information
            system_info = {
                'hostname': os.uname().nodename,
                'system': os.uname().sysname,
                'release': os.uname().release,
                'version': os.uname().version,
                'machine': os.uname().machine,
                'python_version': sys.version,
                'working_directory': os.getcwd(),
                'environment_variables': dict(os.environ),
                'process_id': os.getpid(),
                'maintenance_mode': self.maintenance_mode,
                'door_status': self.door_status,
                'motor_status': self.motor_status
            }
            
            return {
                'success': True,
                'message': 'System info retrieved successfully',
                'system_info': system_info,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error getting system info: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _update_gui_maintenance_message(self, message: str):
        """Update GUI with maintenance message"""
        try:
            # This would integrate with your GUI system
            # For now, just log the message
            logging.info(f"GUI Maintenance Message: {message}")
        except Exception as e:
            logging.error(f"Error updating GUI maintenance message: {e}")
```

### **3. Integration with Main Application**

#### **A. Main Application Integration:**
```python
# File: myrvm-integration/main_application.py

# Add to existing imports
from remote.command_receiver import RemoteCommandReceiver

class MyRVMApplication:
    def __init__(self):
        # ... existing initialization ...
        
        # Initialize remote command receiver
        self.command_receiver = None
        
    def start_remote_commands(self, server_url: str, rvm_id: int, api_key: str):
        """Start remote command receiver"""
        try:
            self.command_receiver = RemoteCommandReceiver(server_url, rvm_id, api_key)
            self.command_receiver.start()
            print("Remote command receiver started")
        except Exception as e:
            print(f"Failed to start remote command receiver: {e}")
    
    def stop_remote_commands(self):
        """Stop remote command receiver"""
        if self.command_receiver:
            self.command_receiver.stop()
            self.command_receiver = None
            print("Remote command receiver stopped")
    
    def is_maintenance_mode(self) -> bool:
        """Check if system is in maintenance mode"""
        if self.command_receiver and self.command_receiver.command_executor:
            return self.command_receiver.command_executor.maintenance_mode
        return False
```

---

## **🧪 TESTING**

### **1. WebSocket Connection Testing:**
- Test WebSocket connection establishment
- Test command reception
- Test status updates
- Test reconnection mechanism

### **2. Command Execution Testing:**
- Test hardware control commands
- Test process management commands
- Test system control commands
- Test diagnostics commands

### **3. Error Handling Testing:**
- Test invalid command handling
- Test network disconnection
- Test command execution errors
- Test status update failures

---

## **📋 CHECKLIST**

- [ ] Implement RemoteCommandReceiver
- [ ] Implement RemoteCommandExecutor
- [ ] Integrate with main application
- [ ] Test WebSocket connection
- [ ] Test command reception
- [ ] Test command execution
- [ ] Test status updates
- [ ] Test error handling
- [ ] Test reconnection mechanism
- [ ] Test hardware control commands
- [ ] Test process management commands
- [ ] Test system control commands
- [ ] Test diagnostics commands
- [ ] Performance testing
- [ ] Documentation update

---

## **📝 NOTES**

- Commands received via WebSocket
- Real-time status updates
- Automatic reconnection on disconnection
- Comprehensive error handling
- Threading for non-blocking operation
- Integration with existing application

---

**Status**: 🔄 **IN PROGRESS**  
**Next**: Implement WebSocket command receiver
