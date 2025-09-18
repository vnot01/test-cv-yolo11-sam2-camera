#!/usr/bin/env python3
"""
Security Manager for MyRVM Platform Integration
Production-ready security and credential management
"""

import os
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class SecurityManager:
    """Advanced security and credential management system"""
    
    def __init__(self, config: Dict):
        """
        Initialize security manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.encrypt_credentials = config.get('security', {}).get('encrypt_credentials', True)
        self.require_https = config.get('security', {}).get('require_https', False)
        self.access_control = config.get('security', {}).get('access_control', False)
        
        # Security directories
        self.security_dir = Path(__file__).parent / 'security'
        self.security_dir.mkdir(exist_ok=True)
        
        self.keys_dir = self.security_dir / 'keys'
        self.keys_dir.mkdir(exist_ok=True)
        
        self.credentials_dir = self.security_dir / 'credentials'
        self.credentials_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize encryption
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Access control
        self.access_tokens = {}
        self.token_expiry = {}
        
        # Security audit log
        self.audit_log = []
        self.max_audit_entries = 1000
        
        self.logger.info("Security manager initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for security manager"""
        logger = logging.getLogger('SecurityManager')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'security_manager_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = self.keys_dir / 'encryption.key'
        
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    key = f.read()
                self.logger.info("Loaded existing encryption key")
                return key
            except Exception as e:
                self.logger.error(f"Failed to load encryption key: {e}")
        
        # Create new encryption key
        try:
            # Generate key from password if available
            password = os.getenv('MYRVM_ENCRYPTION_PASSWORD', 'default_password_change_me')
            salt = os.urandom(16)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Save key
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Save salt
            salt_file = self.keys_dir / 'encryption.salt'
            with open(salt_file, 'wb') as f:
                f.write(salt)
            
            # Set secure permissions
            key_file.chmod(0o600)
            salt_file.chmod(0o600)
            
            self.logger.info("Created new encryption key")
            return key
            
        except Exception as e:
            self.logger.error(f"Failed to create encryption key: {e}")
            raise
    
    def encrypt_credential(self, credential: str) -> str:
        """Encrypt credential"""
        if not self.encrypt_credentials:
            return credential
        
        try:
            encrypted_data = self.cipher_suite.encrypt(credential.encode())
            encrypted_b64 = base64.urlsafe_b64encode(encrypted_data).decode()
            
            self._log_security_event('credential_encrypted', {
                'credential_length': len(credential),
                'encrypted_length': len(encrypted_b64)
            })
            
            return encrypted_b64
            
        except Exception as e:
            self.logger.error(f"Failed to encrypt credential: {e}")
            raise
    
    def decrypt_credential(self, encrypted_credential: str) -> str:
        """Decrypt credential"""
        if not self.encrypt_credentials:
            return encrypted_credential
        
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_credential.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            self._log_security_event('credential_decrypted', {
                'encrypted_length': len(encrypted_credential),
                'decrypted_length': len(decrypted_data)
            })
            
            return decrypted_data.decode()
            
        except Exception as e:
            self.logger.error(f"Failed to decrypt credential: {e}")
            raise
    
    def store_credential(self, name: str, credential: str, metadata: Dict = None):
        """Store encrypted credential"""
        try:
            encrypted_credential = self.encrypt_credential(credential)
            
            credential_data = {
                'name': name,
                'encrypted_credential': encrypted_credential,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            credential_file = self.credentials_dir / f'{name}.json'
            with open(credential_file, 'w') as f:
                json.dump(credential_data, f, indent=2)
            
            # Set secure permissions
            credential_file.chmod(0o600)
            
            self._log_security_event('credential_stored', {
                'credential_name': name,
                'has_metadata': bool(metadata)
            })
            
            self.logger.info(f"Credential stored: {name}")
            
        except Exception as e:
            self.logger.error(f"Failed to store credential {name}: {e}")
            raise
    
    def get_credential(self, name: str) -> Optional[str]:
        """Get and decrypt credential"""
        try:
            credential_file = self.credentials_dir / f'{name}.json'
            
            if not credential_file.exists():
                self.logger.warning(f"Credential not found: {name}")
                return None
            
            with open(credential_file, 'r') as f:
                credential_data = json.load(f)
            
            encrypted_credential = credential_data['encrypted_credential']
            decrypted_credential = self.decrypt_credential(encrypted_credential)
            
            self._log_security_event('credential_accessed', {
                'credential_name': name,
                'created_at': credential_data.get('created_at')
            })
            
            return decrypted_credential
            
        except Exception as e:
            self.logger.error(f"Failed to get credential {name}: {e}")
            return None
    
    def delete_credential(self, name: str):
        """Delete credential"""
        try:
            credential_file = self.credentials_dir / f'{name}.json'
            
            if credential_file.exists():
                credential_file.unlink()
                
                self._log_security_event('credential_deleted', {
                    'credential_name': name
                })
                
                self.logger.info(f"Credential deleted: {name}")
            else:
                self.logger.warning(f"Credential not found for deletion: {name}")
                
        except Exception as e:
            self.logger.error(f"Failed to delete credential {name}: {e}")
            raise
    
    def list_credentials(self) -> List[str]:
        """List all stored credentials"""
        try:
            credentials = []
            for credential_file in self.credentials_dir.glob('*.json'):
                credentials.append(credential_file.stem)
            
            self._log_security_event('credentials_listed', {
                'credential_count': len(credentials)
            })
            
            return credentials
            
        except Exception as e:
            self.logger.error(f"Failed to list credentials: {e}")
            return []
    
    def generate_access_token(self, user_id: str, permissions: List[str] = None, expiry_hours: int = 24) -> str:
        """Generate access token"""
        try:
            token = secrets.token_urlsafe(32)
            expiry_time = datetime.now() + timedelta(hours=expiry_hours)
            
            self.access_tokens[token] = {
                'user_id': user_id,
                'permissions': permissions or [],
                'created_at': datetime.now().isoformat(),
                'expires_at': expiry_time.isoformat()
            }
            
            self.token_expiry[token] = expiry_time
            
            self._log_security_event('access_token_generated', {
                'user_id': user_id,
                'permissions': permissions or [],
                'expiry_hours': expiry_hours
            })
            
            self.logger.info(f"Access token generated for user: {user_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to generate access token: {e}")
            raise
    
    def validate_access_token(self, token: str) -> Optional[Dict]:
        """Validate access token"""
        try:
            if token not in self.access_tokens:
                self._log_security_event('access_token_invalid', {
                    'token': token[:8] + '...' if len(token) > 8 else token
                })
                return None
            
            # Check expiry
            if datetime.now() > self.token_expiry[token]:
                del self.access_tokens[token]
                del self.token_expiry[token]
                
                self._log_security_event('access_token_expired', {
                    'token': token[:8] + '...' if len(token) > 8 else token
                })
                return None
            
            token_data = self.access_tokens[token]
            
            self._log_security_event('access_token_validated', {
                'user_id': token_data['user_id'],
                'permissions': token_data['permissions']
            })
            
            return token_data
            
        except Exception as e:
            self.logger.error(f"Failed to validate access token: {e}")
            return None
    
    def revoke_access_token(self, token: str):
        """Revoke access token"""
        try:
            if token in self.access_tokens:
                user_id = self.access_tokens[token]['user_id']
                del self.access_tokens[token]
                del self.token_expiry[token]
                
                self._log_security_event('access_token_revoked', {
                    'user_id': user_id,
                    'token': token[:8] + '...' if len(token) > 8 else token
                })
                
                self.logger.info(f"Access token revoked for user: {user_id}")
            else:
                self.logger.warning(f"Access token not found for revocation: {token[:8]}...")
                
        except Exception as e:
            self.logger.error(f"Failed to revoke access token: {e}")
            raise
    
    def check_permission(self, token: str, required_permission: str) -> bool:
        """Check if token has required permission"""
        try:
            token_data = self.validate_access_token(token)
            if not token_data:
                return False
            
            permissions = token_data.get('permissions', [])
            has_permission = required_permission in permissions or 'admin' in permissions
            
            self._log_security_event('permission_checked', {
                'user_id': token_data['user_id'],
                'required_permission': required_permission,
                'has_permission': has_permission
            })
            
            return has_permission
            
        except Exception as e:
            self.logger.error(f"Failed to check permission: {e}")
            return False
    
    def _log_security_event(self, event_type: str, details: Dict):
        """Log security event"""
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'details': details
            }
            
            self.audit_log.append(event)
            
            # Keep only recent entries
            if len(self.audit_log) > self.max_audit_entries:
                self.audit_log = self.audit_log[-self.max_audit_entries:]
            
            # Log to file
            self.logger.info(f"Security event: {event_type} - {details}")
            
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
    
    def get_security_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get security audit log"""
        try:
            return self.audit_log[-limit:] if limit else self.audit_log
        except Exception as e:
            self.logger.error(f"Failed to get security audit log: {e}")
            return []
    
    def cleanup_expired_tokens(self):
        """Cleanup expired access tokens"""
        try:
            current_time = datetime.now()
            expired_tokens = []
            
            for token, expiry_time in self.token_expiry.items():
                if current_time > expiry_time:
                    expired_tokens.append(token)
            
            for token in expired_tokens:
                del self.access_tokens[token]
                del self.token_expiry[token]
            
            if expired_tokens:
                self._log_security_event('expired_tokens_cleaned', {
                    'expired_count': len(expired_tokens)
                })
                self.logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired tokens: {e}")
    
    def get_security_status(self) -> Dict:
        """Get security status"""
        try:
            return {
                'encryption_enabled': self.encrypt_credentials,
                'https_required': self.require_https,
                'access_control_enabled': self.access_control,
                'active_tokens': len(self.access_tokens),
                'stored_credentials': len(self.list_credentials()),
                'audit_log_entries': len(self.audit_log),
                'security_dir': str(self.security_dir),
                'keys_dir': str(self.keys_dir),
                'credentials_dir': str(self.credentials_dir)
            }
        except Exception as e:
            self.logger.error(f"Failed to get security status: {e}")
            return {}
    
    def get_security_report(self) -> str:
        """Generate security report"""
        try:
            status = self.get_security_status()
            recent_events = self.get_security_audit_log(10)
            
            report = f"""
Security Manager Report
======================
Encryption Enabled: {status.get('encryption_enabled', False)}
HTTPS Required: {status.get('https_required', False)}
Access Control Enabled: {status.get('access_control_enabled', False)}

Security Statistics:
- Active Access Tokens: {status.get('active_tokens', 0)}
- Stored Credentials: {status.get('stored_credentials', 0)}
- Audit Log Entries: {status.get('audit_log_entries', 0)}

Security Directories:
- Security Dir: {status.get('security_dir', 'N/A')}
- Keys Dir: {status.get('keys_dir', 'N/A')}
- Credentials Dir: {status.get('credentials_dir', 'N/A')}

Recent Security Events ({len(recent_events)}):
"""
            
            for event in recent_events:
                report += f"- {event['timestamp']}: {event['event_type']}\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate security report: {e}")
            return f"Error generating security report: {e}"
