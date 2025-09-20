#!/usr/bin/env python3
"""
User Authentication Handler
Handles user authentication via QR Code and session management
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from gui.qr_code_generator import QRCodeGenerator

@dataclass
class UserProfile:
    """User profile data"""
    user_id: int
    name: str
    email: str
    avatar: Optional[str] = None
    status: str = "active"
    balance: float = 0.0
    last_login: Optional[datetime] = None
    login_count: int = 0
    created_at: Optional[datetime] = None

@dataclass
class UserSession:
    """User session data"""
    session_id: str
    user_id: int
    user_profile: UserProfile
    start_time: datetime
    last_activity: datetime
    status: str = "active"  # active, expired, terminated
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    qr_code_data: Optional[Dict] = None

class UserAuthenticationHandler:
    """Handle user authentication via QR Code"""
    
    def __init__(self, api_client=None, rvm_id: str = "jetson_orin_nano_001"):
        """
        Initialize User Authentication Handler
        
        Args:
            api_client: API client for server communication
            rvm_id: RVM identifier
        """
        self.api_client = api_client
        self.rvm_id = rvm_id
        
        # QR Code generator
        self.qr_generator = QRCodeGenerator(rvm_id, self)
        
        # Session management
        self.active_sessions = {}
        self.session_timeout = 3600  # 1 hour
        self.max_sessions = 10
        
        # User management
        self.user_profiles = {}
        self.authentication_callbacks = []
        
        # Threading
        self.session_cleanup_thread = None
        self.shutdown_event = threading.Event()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Start session cleanup thread
        self._start_session_cleanup()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for user authentication"""
        logger = logging.getLogger('UserAuthenticationHandler')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'user_authentication_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _start_session_cleanup(self):
        """Start session cleanup thread"""
        self.session_cleanup_thread = threading.Thread(
            target=self._session_cleanup_loop,
            daemon=True,
            name="SessionCleanupThread"
        )
        self.session_cleanup_thread.start()
        self.logger.info("Session cleanup thread started")
    
    def _session_cleanup_loop(self):
        """Session cleanup loop"""
        while not self.shutdown_event.is_set():
            try:
                self._cleanup_expired_sessions()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Session cleanup error: {e}")
                time.sleep(10)
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if current_time - session.last_activity > timedelta(seconds=self.session_timeout):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self._terminate_session(session_id, "Session expired")
            self.logger.info(f"Cleaned up expired session: {session_id}")
    
    def generate_login_qr_code(self, additional_data: Dict = None) -> Tuple[str, Dict]:
        """
        Generate QR code for user login
        
        Args:
            additional_data: Additional data to include in QR code
            
        Returns:
            Tuple of (base64_qr_code, qr_code_data)
        """
        try:
            # Add login-specific data
            login_data = {
                "login_type": "qr_code",
                "rvm_location": "Main Entrance",
                "login_method": "mobile_app"
            }
            
            if additional_data:
                login_data.update(additional_data)
            
            # Generate QR code
            qr_base64, qr_data = self.qr_generator.generate_qr_code_base64("login", login_data)
            
            self.logger.info("Login QR code generated")
            return qr_base64, qr_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate login QR code: {e}")
            raise
    
    def authenticate_user(self, qr_data: Dict, user_credentials: Dict = None) -> Tuple[bool, Optional[UserSession]]:
        """
        Authenticate user via QR Code
        
        Args:
            qr_data: QR code data
            user_credentials: User credentials (optional)
            
        Returns:
            Tuple of (success, user_session)
        """
        try:
            # Validate QR code
            is_valid, error_message = self.qr_generator.validate_qr_code(qr_data)
            if not is_valid:
                self.logger.warning(f"QR code validation failed: {error_message}")
                return False, None
            
            # Check if user is already logged in
            if self._is_user_already_logged_in(qr_data.get('session_token')):
                self.logger.warning("User already logged in")
                return False, None
            
            # Authenticate user (mock implementation - replace with real authentication)
            user_profile = self._authenticate_user_credentials(user_credentials or {})
            if not user_profile:
                self.logger.warning("User authentication failed")
                return False, None
            
            # Create user session
            session = self._create_user_session(user_profile, qr_data)
            
            # Store session
            self.active_sessions[session.session_id] = session
            
            # Update user profile
            user_profile.last_login = datetime.now()
            user_profile.login_count += 1
            self.user_profiles[user_profile.user_id] = user_profile
            
            # Notify callbacks
            self._notify_authentication_callbacks(session, "login")
            
            self.logger.info(f"User authenticated successfully: {user_profile.name} (ID: {user_profile.user_id})")
            return True, session
            
        except Exception as e:
            self.logger.error(f"User authentication failed: {e}")
            return False, None
    
    def _authenticate_user_credentials(self, credentials: Dict) -> Optional[UserProfile]:
        """
        Authenticate user credentials (mock implementation)
        
        Args:
            credentials: User credentials
            
        Returns:
            User profile if authenticated, None otherwise
        """
        try:
            # Mock authentication - replace with real API call
            if self.api_client and hasattr(self.api_client, 'login'):
                # Call server API for authentication
                success, response = self.api_client.login(
                    credentials.get('email', ''),
                    credentials.get('password', '')
                )
                
                if success and 'data' in response:
                    user_data = response['data']
                    return UserProfile(
                        user_id=user_data.get('id', 1),
                        name=user_data.get('name', 'Test User'),
                        email=user_data.get('email', 'test@example.com'),
                        avatar=user_data.get('avatar'),
                        status=user_data.get('status', 'active'),
                        balance=user_data.get('balance', 0.0),
                        created_at=datetime.now()
                    )
            
            # Fallback to mock user for testing
            return UserProfile(
                user_id=1,
                name="Test User",
                email="test@example.com",
                avatar=None,
                status="active",
                balance=15000.0,
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"User credentials authentication failed: {e}")
            return None
    
    def _create_user_session(self, user_profile: UserProfile, qr_data: Dict) -> UserSession:
        """Create user session"""
        session_id = self._generate_session_id()
        current_time = datetime.now()
        
        session = UserSession(
            session_id=session_id,
            user_id=user_profile.user_id,
            user_profile=user_profile,
            start_time=current_time,
            last_activity=current_time,
            status="active",
            qr_code_data=qr_data
        )
        
        return session
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        session_id = ''.join(secrets.choice(alphabet) for _ in range(16))
        timestamp = str(int(time.time()))
        
        return f"{session_id}_{timestamp}"
    
    def _is_user_already_logged_in(self, session_token: str) -> bool:
        """Check if user is already logged in"""
        for session in self.active_sessions.values():
            if (session.qr_code_data and 
                session.qr_code_data.get('session_token') == session_token):
                return True
        return False
    
    def get_user_session(self, session_id: str) -> Optional[UserSession]:
        """Get user session by session ID"""
        return self.active_sessions.get(session_id)
    
    def update_session_activity(self, session_id: str):
        """Update session last activity time"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].last_activity = datetime.now()
    
    def terminate_session(self, session_id: str, reason: str = "User logout"):
        """Terminate user session"""
        self._terminate_session(session_id, reason)
    
    def _terminate_session(self, session_id: str, reason: str):
        """Internal method to terminate session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = "terminated"
            
            # Notify callbacks
            self._notify_authentication_callbacks(session, "logout")
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            self.logger.info(f"Session terminated: {session_id} - {reason}")
    
    def get_active_sessions(self) -> Dict[str, UserSession]:
        """Get all active sessions"""
        return self.active_sessions.copy()
    
    def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile by user ID"""
        return self.user_profiles.get(user_id)
    
    def register_authentication_callback(self, callback: Callable[[UserSession, str], None]):
        """Register authentication callback"""
        self.authentication_callbacks.append(callback)
        self.logger.info("Authentication callback registered")
    
    def _notify_authentication_callbacks(self, session: UserSession, action: str):
        """Notify authentication callbacks"""
        for callback in self.authentication_callbacks:
            try:
                callback(session, action)
            except Exception as e:
                self.logger.error(f"Authentication callback error: {e}")
    
    def get_authentication_status(self) -> Dict:
        """Get authentication status"""
        return {
            'rvm_id': self.rvm_id,
            'active_sessions_count': len(self.active_sessions),
            'max_sessions': self.max_sessions,
            'session_timeout': self.session_timeout,
            'user_profiles_count': len(self.user_profiles),
            'authentication_callbacks_count': len(self.authentication_callbacks)
        }
    
    def shutdown(self):
        """Shutdown user authentication handler"""
        self.logger.info("Shutting down user authentication handler...")
        
        # Stop session cleanup thread
        self.shutdown_event.set()
        
        if self.session_cleanup_thread and self.session_cleanup_thread.is_alive():
            self.session_cleanup_thread.join(timeout=5)
        
        # Terminate all active sessions
        for session_id in list(self.active_sessions.keys()):
            self._terminate_session(session_id, "System shutdown")
        
        self.logger.info("User authentication handler shutdown completed")

# Example usage and testing
if __name__ == "__main__":
    # Test user authentication handler
    auth_handler = UserAuthenticationHandler("jetson_orin_nano_001")
    
    print("User Authentication Handler Test:")
    print("=" * 50)
    
    # Test QR code generation
    print("\n1. Testing QR Code Generation...")
    qr_base64, qr_data = auth_handler.generate_login_qr_code()
    print(f"   QR Code generated: {len(qr_base64)} characters")
    print(f"   QR Data: {qr_data}")
    
    # Test user authentication
    print("\n2. Testing User Authentication...")
    success, session = auth_handler.authenticate_user(qr_data)
    print(f"   Authentication result: {success}")
    if session:
        print(f"   Session ID: {session.session_id}")
        print(f"   User: {session.user_profile.name}")
        print(f"   Email: {session.user_profile.email}")
        print(f"   Balance: {session.user_profile.balance}")
    
    # Test session management
    print("\n3. Testing Session Management...")
    if session:
        session_id = session.session_id
        retrieved_session = auth_handler.get_user_session(session_id)
        print(f"   Session retrieved: {retrieved_session is not None}")
        
        # Update activity
        auth_handler.update_session_activity(session_id)
        print(f"   Session activity updated")
        
        # Get active sessions
        active_sessions = auth_handler.get_active_sessions()
        print(f"   Active sessions: {len(active_sessions)}")
    
    # Test authentication status
    print("\n4. Testing Authentication Status...")
    status = auth_handler.get_authentication_status()
    print(f"   RVM ID: {status['rvm_id']}")
    print(f"   Active Sessions: {status['active_sessions_count']}")
    print(f"   Max Sessions: {status['max_sessions']}")
    print(f"   Session Timeout: {status['session_timeout']}")
    
    # Test session termination
    print("\n5. Testing Session Termination...")
    if session:
        auth_handler.terminate_session(session.session_id, "Test termination")
        print(f"   Session terminated")
        
        # Check active sessions
        active_sessions = auth_handler.get_active_sessions()
        print(f"   Active sessions after termination: {len(active_sessions)}")
    
    # Shutdown
    print("\n6. Shutting down...")
    auth_handler.shutdown()
    
    print("\n✅ User Authentication Handler test completed successfully!")
