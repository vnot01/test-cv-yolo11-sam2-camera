#!/usr/bin/env python3
"""
QR Code Generator for User Authentication
Generates QR codes for user login and session management
"""

import qrcode
import json
import time
import base64
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class QRCodeGenerator:
    """QR Code generator for user authentication"""
    
    def __init__(self, rvm_id: str, session_manager=None):
        """
        Initialize QR Code Generator
        
        Args:
            rvm_id: RVM identifier
            session_manager: Session manager instance
        """
        self.rvm_id = rvm_id
        self.session_manager = session_manager
        self.qr_code_data = {}
        self.qr_code_image = None
        self.expiration_time = 60  # 1 minute
        self.qr_code_size = (400, 400)  # Default size
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # QR Code configuration
        self.qr_config = {
            'version': 1,
            'box_size': 10,
            'border': 5,
            'fill_color': 'black',
            'back_color': 'white'
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for QR code generator"""
        logger = logging.getLogger('QRCodeGenerator')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'qr_code_generator_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def generate_qr_code(self, action: str = "login", additional_data: Dict = None) -> Tuple[bytes, Dict]:
        """
        Generate QR Code for user authentication
        
        Args:
            action: Action type (login, logout, status_check)
            additional_data: Additional data to include in QR code
            
        Returns:
            Tuple of (qr_code_image_bytes, qr_code_data)
        """
        try:
            # Generate session token
            session_token = self._generate_session_token()
            
            # Create QR code data
            qr_data = {
                "rvm_id": self.rvm_id,
                "timestamp": int(time.time()),
                "action": action,
                "session_token": session_token,
                "expires_at": int(time.time()) + self.expiration_time,
                "version": "1.0"
            }
            
            # Add additional data if provided
            if additional_data:
                qr_data.update(additional_data)
            
            # Store QR code data
            self.qr_code_data = qr_data
            
            # Generate QR code image
            qr = qrcode.QRCode(
                version=self.qr_config['version'],
                box_size=self.qr_config['box_size'],
                border=self.qr_config['border']
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(
                fill_color=self.qr_config['fill_color'],
                back_color=self.qr_config['back_color']
            )
            
            # Resize image if needed
            if self.qr_code_size != (400, 400):
                img = img.resize(self.qr_code_size)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Store image
            self.qr_code_image = img_bytes.getvalue()
            
            self.logger.info(f"QR Code generated for action: {action}")
            self.logger.debug(f"QR Code data: {qr_data}")
            
            return self.qr_code_image, qr_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate QR code: {e}")
            raise
    
    def generate_qr_code_base64(self, action: str = "login", additional_data: Dict = None) -> Tuple[str, Dict]:
        """
        Generate QR Code and return as base64 string
        
        Args:
            action: Action type (login, logout, status_check)
            additional_data: Additional data to include in QR code
            
        Returns:
            Tuple of (base64_qr_code, qr_code_data)
        """
        try:
            # Generate QR code
            qr_image_bytes, qr_data = self.generate_qr_code(action, additional_data)
            
            # Convert to base64
            qr_base64 = base64.b64encode(qr_image_bytes).decode('utf-8')
            
            self.logger.info(f"QR Code generated as base64 for action: {action}")
            
            return qr_base64, qr_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate QR code base64: {e}")
            raise
    
    def validate_qr_code(self, qr_data: Dict) -> Tuple[bool, str]:
        """
        Validate QR code data
        
        Args:
            qr_data: QR code data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check required fields
            required_fields = ['rvm_id', 'timestamp', 'action', 'session_token', 'expires_at']
            for field in required_fields:
                if field not in qr_data:
                    return False, f"Missing required field: {field}"
            
            # Check RVM ID
            if qr_data['rvm_id'] != self.rvm_id:
                return False, "Invalid RVM ID"
            
            # Check expiration
            current_time = int(time.time())
            if current_time > qr_data['expires_at']:
                return False, "QR code expired"
            
            # Check timestamp (not too old)
            if current_time - qr_data['timestamp'] > 300:  # 5 minutes
                return False, "QR code too old"
            
            # Check action
            valid_actions = ['login', 'logout', 'status_check', 'config_update']
            if qr_data['action'] not in valid_actions:
                return False, f"Invalid action: {qr_data['action']}"
            
            self.logger.info(f"QR code validation successful for action: {qr_data['action']}")
            return True, "Valid"
            
        except Exception as e:
            self.logger.error(f"QR code validation failed: {e}")
            return False, f"Validation error: {e}"
    
    def _generate_session_token(self) -> str:
        """Generate unique session token"""
        import secrets
        import string
        
        # Generate random token
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        # Add timestamp for uniqueness
        timestamp = str(int(time.time()))
        session_token = f"{token}_{timestamp}"
        
        return session_token
    
    def get_qr_code_info(self) -> Dict:
        """Get current QR code information"""
        return {
            'rvm_id': self.rvm_id,
            'qr_code_data': self.qr_code_data,
            'expiration_time': self.expiration_time,
            'qr_code_size': self.qr_code_size,
            'qr_config': self.qr_config,
            'has_image': self.qr_code_image is not None
        }
    
    def set_qr_code_size(self, width: int, height: int):
        """Set QR code image size"""
        self.qr_code_size = (width, height)
        self.logger.info(f"QR code size set to: {width}x{height}")
    
    def set_expiration_time(self, seconds: int):
        """Set QR code expiration time"""
        self.expiration_time = seconds
        self.logger.info(f"QR code expiration time set to: {seconds} seconds")
    
    def set_qr_config(self, config: Dict):
        """Set QR code configuration"""
        self.qr_config.update(config)
        self.logger.info(f"QR code configuration updated: {config}")
    
    def clear_qr_code(self):
        """Clear current QR code data and image"""
        self.qr_code_data = {}
        self.qr_code_image = None
        self.logger.info("QR code data and image cleared")

# Example usage and testing
if __name__ == "__main__":
    # Test QR code generator
    generator = QRCodeGenerator("jetson_orin_nano_001")
    
    print("QR Code Generator Test:")
    print("=" * 50)
    
    # Test QR code generation
    print("\n1. Testing QR Code Generation...")
    qr_image, qr_data = generator.generate_qr_code("login")
    print(f"   QR Code generated: {len(qr_image)} bytes")
    print(f"   QR Data: {qr_data}")
    
    # Test base64 generation
    print("\n2. Testing Base64 Generation...")
    qr_base64, qr_data = generator.generate_qr_code_base64("login")
    print(f"   Base64 length: {len(qr_base64)} characters")
    print(f"   QR Data: {qr_data}")
    
    # Test validation
    print("\n3. Testing QR Code Validation...")
    is_valid, message = generator.validate_qr_code(qr_data)
    print(f"   Validation result: {is_valid}")
    print(f"   Message: {message}")
    
    # Test invalid QR code
    print("\n4. Testing Invalid QR Code...")
    invalid_data = qr_data.copy()
    invalid_data['expires_at'] = int(time.time()) - 100  # Expired
    is_valid, message = generator.validate_qr_code(invalid_data)
    print(f"   Validation result: {is_valid}")
    print(f"   Message: {message}")
    
    # Test QR code info
    print("\n5. Testing QR Code Info...")
    info = generator.get_qr_code_info()
    print(f"   RVM ID: {info['rvm_id']}")
    print(f"   Expiration Time: {info['expiration_time']}")
    print(f"   QR Code Size: {info['qr_code_size']}")
    print(f"   Has Image: {info['has_image']}")
    
    print("\n✅ QR Code Generator test completed successfully!")

