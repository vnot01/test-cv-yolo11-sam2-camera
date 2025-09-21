#!/usr/bin/env python3
"""
User Session Manager
Manage user sessions and authentication
"""

import json
import time
import logging
import threading
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

@dataclass
class UserSession:
    """User session data structure"""
    session_id: str
    user_id: int
    user_profile: Dict
    start_time: datetime
    last_activity: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[Dict] = None
    status: str = "active"  # active, expired, terminated
    session_data: Dict = None
    permissions: List[str] = None

@dataclass
class SessionConfig:
    """Session configuration"""
    default_timeout: int = 3600  # 1 hour
    max_timeout: int = 86400  # 24 hours
    cleanup_interval: int = 300  # 5 minutes
    max_sessions_per_user: int = 5
    session_id_length: int = 32
    auto_extend: bool = True
    secure_cookies: bool = True

class UserSessionManager:
    """Manage user sessions and authentication"""
    
    def __init__(self, user_profile_manager=None, config: SessionConfig = None):
        """
        Initialize User Session Manager
        
        Args:
            user_profile_manager: User profile manager instance
            config: Session configuration
        """
        self.user_profile_manager = user_profile_manager
        self.config = config or SessionConfig()
        
        # Session storage
        self.active_sessions = {}
        self.session_history = []
        self.user_sessions = {}  # user_id -> list of session_ids
        
        # Callbacks
        self.session_callbacks = []
        self.auth_callbacks = []
        
        # Threading
        self.cleanup_thread = None
        self.shutdown_event = threading.Event()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize manager
        self._initialize_manager()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for user session manager"""
        logger = logging.getLogger('UserSessionManager')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'user_session_manager_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _initialize_manager(self):
        """Initialize user session manager"""
        try:
            self.logger.info("Initializing User Session Manager...")
            
            # Start cleanup thread
            self._start_cleanup_thread()
            
            self.logger.info("User Session Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize User Session Manager: {e}")
            raise
    
    def _start_cleanup_thread(self):
        """Start session cleanup thread"""
        try:
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True,
                name="SessionCleanupThread"
            )
            self.cleanup_thread.start()
            self.logger.info("Session cleanup thread started")
            
        except Exception as e:
            self.logger.error(f"Failed to start cleanup thread: {e}")
    
    def _cleanup_loop(self):
        """Session cleanup loop"""
        while not self.shutdown_event.is_set():
            try:
                self._cleanup_expired_sessions()
                time.sleep(self.config.cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
                time.sleep(60)
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                if current_time > session.expires_at:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self._terminate_session(session_id, "Session expired")
                self.logger.info(f"Cleaned up expired session: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
    
    # Session Management Methods
    
    def create_user_session(self, user_id: int, session_data: Dict = None, 
                          timeout: int = None, ip_address: str = None, 
                          user_agent: str = None, device_info: Dict = None) -> Optional[UserSession]:
        """
        Create user session
        
        Args:
            user_id: User ID
            session_data: Additional session data
            timeout: Session timeout in seconds
            ip_address: Client IP address
            user_agent: Client user agent
            device_info: Device information
            
        Returns:
            Created user session or None if failed
        """
        try:
            # Check if user exists
            if self.user_profile_manager:
                user_profile = self.user_profile_manager.get_user_profile(user_id)
                if not user_profile:
                    self.logger.warning(f"User {user_id} not found")
                    return None
                user_profile_dict = asdict(user_profile)
            else:
                user_profile_dict = {'user_id': user_id, 'name': 'Unknown User'}
            
            # Check session limit
            if user_id in self.user_sessions:
                if len(self.user_sessions[user_id]) >= self.config.max_sessions_per_user:
                    # Terminate oldest session
                    oldest_session_id = self.user_sessions[user_id][0]
                    self._terminate_session(oldest_session_id, "Session limit exceeded")
            
            # Generate session ID
            session_id = self._generate_session_id()
            
            # Set timeout
            if timeout is None:
                timeout = self.config.default_timeout
            timeout = min(timeout, self.config.max_timeout)
            
            # Create session
            current_time = datetime.now()
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                user_profile=user_profile_dict,
                start_time=current_time,
                last_activity=current_time,
                expires_at=current_time + timedelta(seconds=timeout),
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=device_info or {},
                status="active",
                session_data=session_data or {},
                permissions=self._get_user_permissions(user_id)
            )
            
            # Store session
            self.active_sessions[session_id] = session
            
            # Update user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)
            
            # Log session creation
            if self.user_profile_manager:
                self.user_profile_manager.log_user_activity(
                    user_id, 'session_created', {
                        'session_id': session_id,
                        'ip_address': ip_address,
                        'user_agent': user_agent
                    }
                )
            
            # Notify callbacks
            self._notify_session_callbacks(session, 'created')
            
            self.logger.info(f"Created session {session_id} for user {user_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to create user session: {e}")
            return None
    
    def get_user_session(self, session_id: str) -> Optional[UserSession]:
        """
        Get user session by session ID
        
        Args:
            session_id: Session ID
            
        Returns:
            User session or None if not found
        """
        return self.active_sessions.get(session_id)
    
    def update_user_session(self, session_id: str, updates: Dict) -> bool:
        """
        Update user session
        
        Args:
            session_id: Session ID
            updates: Updates dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                self.logger.warning(f"Session {session_id} not found")
                return False
            
            session = self.active_sessions[session_id]
            
            # Update session fields
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            # Update last activity
            session.last_activity = datetime.now()
            
            # Auto-extend session if enabled
            if self.config.auto_extend:
                session.expires_at = datetime.now() + timedelta(seconds=self.config.default_timeout)
            
            # Notify callbacks
            self._notify_session_callbacks(session, 'updated')
            
            self.logger.debug(f"Updated session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update user session: {e}")
            return False
    
    def terminate_user_session(self, session_id: str, reason: str = "User logout") -> bool:
        """
        Terminate user session
        
        Args:
            session_id: Session ID
            reason: Termination reason
            
        Returns:
            True if successful, False otherwise
        """
        return self._terminate_session(session_id, reason)
    
    def _terminate_session(self, session_id: str, reason: str):
        """Internal method to terminate session"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            session.status = "terminated"
            
            # Log session termination
            if self.user_profile_manager:
                self.user_profile_manager.log_user_activity(
                    session.user_id, 'session_terminated', {
                        'session_id': session_id,
                        'reason': reason,
                        'duration': (datetime.now() - session.start_time).total_seconds()
                    }
                )
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Remove from user sessions
            if session.user_id in self.user_sessions:
                if session_id in self.user_sessions[session.user_id]:
                    self.user_sessions[session.user_id].remove(session_id)
                if not self.user_sessions[session.user_id]:
                    del self.user_sessions[session.user_id]
            
            # Add to session history
            self.session_history.append({
                'session_id': session_id,
                'user_id': session.user_id,
                'start_time': session.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'reason': reason,
                'duration': (datetime.now() - session.start_time).total_seconds()
            })
            
            # Keep only last 1000 history entries
            if len(self.session_history) > 1000:
                self.session_history = self.session_history[-1000:]
            
            # Notify callbacks
            self._notify_session_callbacks(session, 'terminated')
            
            self.logger.info(f"Terminated session {session_id}: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to terminate session: {e}")
            return False
    
    def extend_user_session(self, session_id: str, timeout: int = None) -> bool:
        """
        Extend user session
        
        Args:
            session_id: Session ID
            timeout: New timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            if timeout is None:
                timeout = self.config.default_timeout
            
            timeout = min(timeout, self.config.max_timeout)
            session.expires_at = datetime.now() + timedelta(seconds=timeout)
            session.last_activity = datetime.now()
            
            self.logger.info(f"Extended session {session_id} by {timeout} seconds")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to extend session: {e}")
            return False
    
    def get_user_sessions(self, user_id: int) -> List[UserSession]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of user sessions
        """
        try:
            sessions = []
            if user_id in self.user_sessions:
                for session_id in self.user_sessions[user_id]:
                    if session_id in self.active_sessions:
                        sessions.append(self.active_sessions[session_id])
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to get user sessions: {e}")
            return []
    
    def get_all_active_sessions(self) -> List[UserSession]:
        """Get all active sessions"""
        return list(self.active_sessions.values())
    
    def get_session_statistics(self) -> Dict:
        """Get session statistics"""
        try:
            current_time = datetime.now()
            active_count = len(self.active_sessions)
            total_users = len(self.user_sessions)
            
            # Calculate average session duration
            total_duration = 0
            session_count = 0
            for session in self.active_sessions.values():
                duration = (current_time - session.start_time).total_seconds()
                total_duration += duration
                session_count += 1
            
            avg_duration = total_duration / session_count if session_count > 0 else 0
            
            return {
                'active_sessions': active_count,
                'total_users': total_users,
                'average_session_duration': avg_duration,
                'session_history_count': len(self.session_history),
                'cleanup_interval': self.config.cleanup_interval,
                'default_timeout': self.config.default_timeout
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get session statistics: {e}")
            return {}
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session is valid, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # Check if session is expired
            if datetime.now() > session.expires_at:
                self._terminate_session(session_id, "Session expired")
                return False
            
            # Check if session is active
            if session.status != "active":
                return False
            
            # Update last activity
            session.last_activity = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate session: {e}")
            return False
    
    def refresh_session(self, session_id: str) -> bool:
        """
        Refresh session (update last activity)
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.validate_session(session_id):
                return False
            
            session = self.active_sessions[session_id]
            session.last_activity = datetime.now()
            
            # Auto-extend if enabled
            if self.config.auto_extend:
                session.expires_at = datetime.now() + timedelta(seconds=self.config.default_timeout)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to refresh session: {e}")
            return False
    
    # Authentication Methods
    
    def authenticate_user(self, user_id: int, credentials: Dict = None) -> Optional[UserSession]:
        """
        Authenticate user and create session
        
        Args:
            user_id: User ID
            credentials: User credentials
            
        Returns:
            User session if authenticated, None otherwise
        """
        try:
            # Check if user exists
            if self.user_profile_manager:
                user_profile = self.user_profile_manager.get_user_profile(user_id)
                if not user_profile:
                    self.logger.warning(f"User {user_id} not found")
                    return None
                
                # Log authentication
                self.user_profile_manager.log_user_activity(
                    user_id, 'authentication', {
                        'method': credentials.get('method', 'unknown'),
                        'success': True
                    }
                )
            
            # Create session
            session = self.create_user_session(
                user_id=user_id,
                session_data=credentials,
                ip_address=credentials.get('ip_address'),
                user_agent=credentials.get('user_agent'),
                device_info=credentials.get('device_info')
            )
            
            if session:
                # Notify auth callbacks
                self._notify_auth_callbacks(session, 'authenticated')
            
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to authenticate user: {e}")
            return None
    
    def logout_user(self, session_id: str) -> bool:
        """
        Logout user (terminate session)
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.get_user_session(session_id)
            if not session:
                return False
            
            # Log logout
            if self.user_profile_manager:
                self.user_profile_manager.log_user_activity(
                    session.user_id, 'logout', {
                        'session_id': session_id,
                        'duration': (datetime.now() - session.start_time).total_seconds()
                    }
                )
            
            # Terminate session
            success = self.terminate_user_session(session_id, "User logout")
            
            if success:
                # Notify auth callbacks
                self._notify_auth_callbacks(session, 'logged_out')
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to logout user: {e}")
            return False
    
    # Helper Methods
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return secrets.token_urlsafe(self.config.session_id_length)
    
    def _get_user_permissions(self, user_id: int) -> List[str]:
        """Get user permissions"""
        # Default permissions
        permissions = ['read', 'write']
        
        # Add user-specific permissions based on profile
        if self.user_profile_manager:
            user_profile = self.user_profile_manager.get_user_profile(user_id)
            if user_profile:
                if user_profile.balance > 100000:  # VIP user
                    permissions.append('vip')
                if user_profile.login_count > 100:  # Frequent user
                    permissions.append('frequent')
        
        return permissions
    
    # Callback Methods
    
    def register_session_callback(self, callback: Callable[[UserSession, str], None]):
        """Register session callback"""
        self.session_callbacks.append(callback)
        self.logger.info("Session callback registered")
    
    def register_auth_callback(self, callback: Callable[[UserSession, str], None]):
        """Register authentication callback"""
        self.auth_callbacks.append(callback)
        self.logger.info("Authentication callback registered")
    
    def _notify_session_callbacks(self, session: UserSession, action: str):
        """Notify session callbacks"""
        for callback in self.session_callbacks:
            try:
                callback(session, action)
            except Exception as e:
                self.logger.error(f"Session callback error: {e}")
    
    def _notify_auth_callbacks(self, session: UserSession, action: str):
        """Notify authentication callbacks"""
        for callback in self.auth_callbacks:
            try:
                callback(session, action)
            except Exception as e:
                self.logger.error(f"Authentication callback error: {e}")
    
    # Status and Management Methods
    
    def get_manager_status(self) -> Dict:
        """Get manager status"""
        return {
            'active_sessions': len(self.active_sessions),
            'total_users': len(self.user_sessions),
            'session_history_count': len(self.session_history),
            'cleanup_thread_running': self.cleanup_thread.is_alive() if self.cleanup_thread else False,
            'config': asdict(self.config)
        }
    
    def shutdown(self):
        """Shutdown user session manager"""
        try:
            self.logger.info("Shutting down User Session Manager...")
            
            # Stop cleanup thread
            self.shutdown_event.set()
            
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5)
            
            # Terminate all active sessions
            for session_id in list(self.active_sessions.keys()):
                self._terminate_session(session_id, "System shutdown")
            
            self.logger.info("User Session Manager shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error shutting down User Session Manager: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test user session manager
    session_manager = UserSessionManager()
    
    print("User Session Manager Test:")
    print("=" * 50)
    
    # Test session creation
    print("\n1. Testing Session Creation...")
    session_data = {
        'ip_address': '192.168.1.100',
        'user_agent': 'Mozilla/5.0 (Test Browser)',
        'device_info': {'type': 'mobile', 'os': 'Android'}
    }
    
    session = session_manager.create_user_session(
        user_id=1,
        session_data=session_data,
        timeout=3600
    )
    
    if session:
        print(f"   ✅ Created session {session.session_id}")
        print(f"   User ID: {session.user_id}")
        print(f"   Start Time: {session.start_time}")
        print(f"   Expires At: {session.expires_at}")
        print(f"   IP Address: {session.ip_address}")
        print(f"   Permissions: {session.permissions}")
    else:
        print("   ❌ Failed to create session")
    
    # Test session validation
    print("\n2. Testing Session Validation...")
    if session:
        session_id = session.session_id
        
        # Validate session
        is_valid = session_manager.validate_session(session_id)
        print(f"   Session valid: {'✅ Yes' if is_valid else '❌ No'}")
        
        # Refresh session
        refreshed = session_manager.refresh_session(session_id)
        print(f"   Session refreshed: {'✅ Yes' if refreshed else '❌ No'}")
        
        # Extend session
        extended = session_manager.extend_user_session(session_id, 7200)
        print(f"   Session extended: {'✅ Yes' if extended else '❌ No'}")
    
    # Test session management
    print("\n3. Testing Session Management...")
    if session:
        session_id = session.session_id
        
        # Update session
        updates = {
            'session_data': {'last_action': 'deposit'},
            'device_info': {'battery': 85}
        }
        updated = session_manager.update_user_session(session_id, updates)
        print(f"   Session updated: {'✅ Yes' if updated else '❌ No'}")
        
        # Get session
        retrieved_session = session_manager.get_user_session(session_id)
        if retrieved_session:
            print(f"   Retrieved session: ✅ Yes")
            print(f"   Last action: {retrieved_session.session_data.get('last_action')}")
            print(f"   Battery: {retrieved_session.device_info.get('battery')}")
    
    # Test authentication
    print("\n4. Testing Authentication...")
    credentials = {
        'method': 'qr_code',
        'ip_address': '192.168.1.100',
        'user_agent': 'Mozilla/5.0 (Test Browser)'
    }
    
    auth_session = session_manager.authenticate_user(1, credentials)
    if auth_session:
        print(f"   ✅ User authenticated")
        print(f"   Session ID: {auth_session.session_id}")
    else:
        print("   ❌ Authentication failed")
    
    # Test session statistics
    print("\n5. Session Statistics:")
    stats = session_manager.get_session_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test session termination
    print("\n6. Testing Session Termination...")
    if session:
        terminated = session_manager.terminate_user_session(session.session_id, "Test termination")
        print(f"   Session terminated: {'✅ Yes' if terminated else '❌ No'}")
        
        # Check if session is gone
        is_valid = session_manager.validate_session(session.session_id)
        print(f"   Session still valid: {'❌ Yes' if is_valid else '✅ No'}")
    
    # Get manager status
    print("\n7. Manager Status:")
    status = session_manager.get_manager_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Shutdown
    print("\n8. Shutting down...")
    session_manager.shutdown()
    
    print("\n✅ User Session Manager test completed successfully!")





