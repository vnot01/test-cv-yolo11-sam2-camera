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
        from .command_executor import RemoteCommandExecutor
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

