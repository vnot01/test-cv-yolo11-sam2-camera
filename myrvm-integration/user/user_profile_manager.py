#!/usr/bin/env python3
"""
User Profile Manager
Manage user profiles and advanced features
"""

import json
import time
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

@dataclass
class UserProfile:
    """User profile data structure"""
    user_id: int
    name: str
    email: str
    avatar: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    preferences: Dict = None
    history: Dict = None
    statistics: Dict = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    status: str = "active"  # active, inactive, suspended
    balance: float = 0.0
    total_deposits: float = 0.0
    login_count: int = 0

@dataclass
class UserPreferences:
    """User preferences data structure"""
    user_id: int
    display: Dict = None
    notifications: Dict = None
    privacy: Dict = None
    accessibility: Dict = None
    language: str = "en"
    timezone: str = "UTC"
    theme: str = "light"
    auto_login: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class UserHistory:
    """User history data structure"""
    user_id: int
    activity_logs: List[Dict] = None
    login_history: List[Dict] = None
    transaction_history: List[Dict] = None
    statistics: Dict = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserProfileManager:
    """Manage user profiles and advanced features"""
    
    def __init__(self, api_client=None, database_path: str = None):
        """
        Initialize User Profile Manager
        
        Args:
            api_client: API client for server communication
            database_path: Path to local database file
        """
        self.api_client = api_client
        self.database_path = database_path or str(Path(__file__).parent.parent / 'data' / 'user_profiles.db')
        
        # User data storage
        self.user_profiles = {}
        self.user_preferences = {}
        self.user_history = {}
        self.user_sessions = {}
        
        # Callbacks
        self.profile_callbacks = []
        self.preference_callbacks = []
        self.history_callbacks = []
        
        # Threading
        self.sync_thread = None
        self.shutdown_event = threading.Event()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize manager
        self._initialize_manager()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for user profile manager"""
        logger = logging.getLogger('UserProfileManager')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'user_profile_manager_{datetime.now().strftime("%Y%m%d")}.log'
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
        """Initialize user profile manager"""
        try:
            self.logger.info("Initializing User Profile Manager...")
            
            # Create data directory
            data_dir = Path(self.database_path).parent
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing data
            self._load_user_data()
            
            # Start sync thread
            self._start_sync_thread()
            
            self.logger.info("User Profile Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize User Profile Manager: {e}")
            raise
    
    def _load_user_data(self):
        """Load user data from local storage"""
        try:
            if Path(self.database_path).exists():
                with open(self.database_path, 'r') as f:
                    data = json.load(f)
                
                # Load user profiles
                if 'user_profiles' in data:
                    for user_id, profile_data in data['user_profiles'].items():
                        profile_data['created_at'] = datetime.fromisoformat(profile_data['created_at']) if profile_data.get('created_at') else None
                        profile_data['updated_at'] = datetime.fromisoformat(profile_data['updated_at']) if profile_data.get('updated_at') else None
                        profile_data['last_login'] = datetime.fromisoformat(profile_data['last_login']) if profile_data.get('last_login') else None
                        self.user_profiles[int(user_id)] = UserProfile(**profile_data)
                
                # Load user preferences
                if 'user_preferences' in data:
                    for user_id, pref_data in data['user_preferences'].items():
                        pref_data['created_at'] = datetime.fromisoformat(pref_data['created_at']) if pref_data.get('created_at') else None
                        pref_data['updated_at'] = datetime.fromisoformat(pref_data['updated_at']) if pref_data.get('updated_at') else None
                        self.user_preferences[int(user_id)] = UserPreferences(**pref_data)
                
                # Load user history
                if 'user_history' in data:
                    for user_id, hist_data in data['user_history'].items():
                        hist_data['created_at'] = datetime.fromisoformat(hist_data['created_at']) if hist_data.get('created_at') else None
                        hist_data['updated_at'] = datetime.fromisoformat(hist_data['updated_at']) if hist_data.get('updated_at') else None
                        self.user_history[int(user_id)] = UserHistory(**hist_data)
                
                self.logger.info(f"Loaded {len(self.user_profiles)} user profiles")
            else:
                self.logger.info("No existing user data found, starting fresh")
                
        except Exception as e:
            self.logger.error(f"Failed to load user data: {e}")
    
    def _save_user_data(self):
        """Save user data to local storage"""
        try:
            data = {
                'user_profiles': {},
                'user_preferences': {},
                'user_history': {}
            }
            
            # Save user profiles
            for user_id, profile in self.user_profiles.items():
                profile_dict = asdict(profile)
                profile_dict['created_at'] = profile.created_at.isoformat() if profile.created_at else None
                profile_dict['updated_at'] = profile.updated_at.isoformat() if profile.updated_at else None
                profile_dict['last_login'] = profile.last_login.isoformat() if profile.last_login else None
                data['user_profiles'][str(user_id)] = profile_dict
            
            # Save user preferences
            for user_id, preferences in self.user_preferences.items():
                pref_dict = asdict(preferences)
                pref_dict['created_at'] = preferences.created_at.isoformat() if preferences.created_at else None
                pref_dict['updated_at'] = preferences.updated_at.isoformat() if preferences.updated_at else None
                data['user_preferences'][str(user_id)] = pref_dict
            
            # Save user history
            for user_id, history in self.user_history.items():
                hist_dict = asdict(history)
                hist_dict['created_at'] = history.created_at.isoformat() if history.created_at else None
                hist_dict['updated_at'] = history.updated_at.isoformat() if history.updated_at else None
                data['user_history'][str(user_id)] = hist_dict
            
            with open(self.database_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug("User data saved to local storage")
            
        except Exception as e:
            self.logger.error(f"Failed to save user data: {e}")
    
    def _start_sync_thread(self):
        """Start data synchronization thread"""
        try:
            self.sync_thread = threading.Thread(
                target=self._sync_loop,
                daemon=True,
                name="UserProfileSyncThread"
            )
            self.sync_thread.start()
            self.logger.info("Data sync thread started")
            
        except Exception as e:
            self.logger.error(f"Failed to start sync thread: {e}")
    
    def _sync_loop(self):
        """Data synchronization loop"""
        while not self.shutdown_event.is_set():
            try:
                # Save data to local storage
                self._save_user_data()
                
                # Sync with server if API client available
                if self.api_client:
                    self._sync_with_server()
                
                time.sleep(30)  # Sync every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Sync loop error: {e}")
                time.sleep(10)
    
    def _sync_with_server(self):
        """Sync user data with server"""
        try:
            # Sync user profiles
            for user_id, profile in self.user_profiles.items():
                if self.api_client and hasattr(self.api_client, 'update_user_profile'):
                    success, response = self.api_client.update_user_profile(user_id, asdict(profile))
                    if success:
                        self.logger.debug(f"Synced profile for user {user_id}")
                    else:
                        self.logger.warning(f"Failed to sync profile for user {user_id}")
            
            # Sync user preferences
            for user_id, preferences in self.user_preferences.items():
                if self.api_client and hasattr(self.api_client, 'update_user_preferences'):
                    success, response = self.api_client.update_user_preferences(user_id, asdict(preferences))
                    if success:
                        self.logger.debug(f"Synced preferences for user {user_id}")
                    else:
                        self.logger.warning(f"Failed to sync preferences for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to sync with server: {e}")
    
    # User Profile Management Methods
    
    def create_user_profile(self, user_data: Dict) -> Optional[UserProfile]:
        """
        Create new user profile
        
        Args:
            user_data: User data dictionary
            
        Returns:
            Created user profile or None if failed
        """
        try:
            # Generate user ID if not provided
            user_id = user_data.get('user_id')
            if not user_id:
                user_id = self._generate_user_id()
            
            # Create user profile
            profile = UserProfile(
                user_id=user_id,
                name=user_data.get('name', ''),
                email=user_data.get('email', ''),
                avatar=user_data.get('avatar'),
                phone=user_data.get('phone'),
                date_of_birth=user_data.get('date_of_birth'),
                address=user_data.get('address'),
                preferences=user_data.get('preferences', {}),
                history=user_data.get('history', {}),
                statistics=user_data.get('statistics', {}),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                balance=user_data.get('balance', 0.0),
                total_deposits=user_data.get('total_deposits', 0.0),
                status=user_data.get('status', 'active')
            )
            
            # Store profile
            self.user_profiles[user_id] = profile
            
            # Create default preferences
            self._create_default_preferences(user_id)
            
            # Create default history
            self._create_default_history(user_id)
            
            # Notify callbacks
            self._notify_profile_callbacks(profile, 'created')
            
            self.logger.info(f"Created user profile for user {user_id}")
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to create user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: int, updates: Dict) -> bool:
        """
        Update user profile
        
        Args:
            user_id: User ID
            updates: Updates dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.user_profiles:
                self.logger.warning(f"User profile {user_id} not found")
                return False
            
            profile = self.user_profiles[user_id]
            
            # Update profile fields
            for key, value in updates.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            profile.updated_at = datetime.now()
            
            # Notify callbacks
            self._notify_profile_callbacks(profile, 'updated')
            
            self.logger.info(f"Updated user profile for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update user profile: {e}")
            return False
    
    def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """
        Get user profile by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User profile or None if not found
        """
        return self.user_profiles.get(user_id)
    
    def delete_user_profile(self, user_id: int) -> bool:
        """
        Delete user profile
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.user_profiles:
                self.logger.warning(f"User profile {user_id} not found")
                return False
            
            # Get profile before deletion
            profile = self.user_profiles[user_id]
            
            # Delete profile and related data
            del self.user_profiles[user_id]
            if user_id in self.user_preferences:
                del self.user_preferences[user_id]
            if user_id in self.user_history:
                del self.user_history[user_id]
            
            # Notify callbacks
            self._notify_profile_callbacks(profile, 'deleted')
            
            self.logger.info(f"Deleted user profile for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete user profile: {e}")
            return False
    
    def get_all_user_profiles(self) -> List[UserProfile]:
        """Get all user profiles"""
        return list(self.user_profiles.values())
    
    def search_user_profiles(self, query: str) -> List[UserProfile]:
        """
        Search user profiles by name or email
        
        Args:
            query: Search query
            
        Returns:
            List of matching user profiles
        """
        try:
            results = []
            query_lower = query.lower()
            
            for profile in self.user_profiles.values():
                if (query_lower in profile.name.lower() or 
                    query_lower in profile.email.lower()):
                    results.append(profile)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search user profiles: {e}")
            return []
    
    # User Preferences Management Methods
    
    def set_user_preference(self, user_id: int, key: str, value: Any) -> bool:
        """
        Set user preference
        
        Args:
            user_id: User ID
            key: Preference key
            value: Preference value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.user_preferences:
                self._create_default_preferences(user_id)
            
            preferences = self.user_preferences[user_id]
            
            # Update preference
            if not preferences.display:
                preferences.display = {}
            if not preferences.notifications:
                preferences.notifications = {}
            if not preferences.privacy:
                preferences.privacy = {}
            if not preferences.accessibility:
                preferences.accessibility = {}
            
            # Set preference based on category
            if key.startswith('display.'):
                preferences.display[key[8:]] = value
            elif key.startswith('notifications.'):
                preferences.notifications[key[14:]] = value
            elif key.startswith('privacy.'):
                preferences.privacy[key[8:]] = value
            elif key.startswith('accessibility.'):
                preferences.accessibility[key[15:]] = value
            else:
                setattr(preferences, key, value)
            
            preferences.updated_at = datetime.now()
            
            # Notify callbacks
            self._notify_preference_callbacks(preferences, 'updated')
            
            self.logger.info(f"Set preference {key} for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set user preference: {e}")
            return False
    
    def get_user_preference(self, user_id: int, key: str) -> Any:
        """
        Get user preference
        
        Args:
            user_id: User ID
            key: Preference key
            
        Returns:
            Preference value or None if not found
        """
        try:
            if user_id not in self.user_preferences:
                return None
            
            preferences = self.user_preferences[user_id]
            
            # Get preference based on category
            if key.startswith('display.'):
                return preferences.display.get(key[8:]) if preferences.display else None
            elif key.startswith('notifications.'):
                return preferences.notifications.get(key[14:]) if preferences.notifications else None
            elif key.startswith('privacy.'):
                return preferences.privacy.get(key[8:]) if preferences.privacy else None
            elif key.startswith('accessibility.'):
                return preferences.accessibility.get(key[15:]) if preferences.accessibility else None
            else:
                return getattr(preferences, key, None)
            
        except Exception as e:
            self.logger.error(f"Failed to get user preference: {e}")
            return None
    
    def get_all_preferences(self, user_id: int) -> Optional[UserPreferences]:
        """Get all user preferences"""
        return self.user_preferences.get(user_id)
    
    def reset_preferences(self, user_id: int) -> bool:
        """
        Reset user preferences to default
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.user_preferences:
                return False
            
            # Create default preferences
            self._create_default_preferences(user_id)
            
            self.logger.info(f"Reset preferences for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset preferences: {e}")
            return False
    
    # User History Management Methods
    
    def log_user_activity(self, user_id: int, activity: str, data: Dict = None) -> bool:
        """
        Log user activity
        
        Args:
            user_id: User ID
            activity: Activity type
            data: Activity data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.user_history:
                self._create_default_history(user_id)
            
            history = self.user_history[user_id]
            
            # Create activity log entry
            activity_log = {
                'timestamp': datetime.now().isoformat(),
                'activity': activity,
                'data': data or {}
            }
            
            # Add to activity logs
            if not history.activity_logs:
                history.activity_logs = []
            history.activity_logs.append(activity_log)
            
            # Keep only last 1000 entries
            if len(history.activity_logs) > 1000:
                history.activity_logs = history.activity_logs[-1000:]
            
            history.updated_at = datetime.now()
            
            # Notify callbacks
            self._notify_history_callbacks(history, 'activity_logged')
            
            self.logger.debug(f"Logged activity {activity} for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log user activity: {e}")
            return False
    
    def get_user_history(self, user_id: int, limit: int = 100) -> List[Dict]:
        """
        Get user history
        
        Args:
            user_id: User ID
            limit: Maximum number of entries
            
        Returns:
            List of history entries
        """
        try:
            if user_id not in self.user_history:
                return []
            
            history = self.user_history[user_id]
            if not history.activity_logs:
                return []
            
            # Return last N entries
            return history.activity_logs[-limit:]
            
        except Exception as e:
            self.logger.error(f"Failed to get user history: {e}")
            return []
    
    def get_user_statistics(self, user_id: int) -> Dict:
        """
        Get user statistics
        
        Args:
            user_id: User ID
            
        Returns:
            User statistics dictionary
        """
        try:
            if user_id not in self.user_history:
                return {}
            
            history = self.user_history[user_id]
            if not history.statistics:
                return {}
            
            return history.statistics
            
        except Exception as e:
            self.logger.error(f"Failed to get user statistics: {e}")
            return {}
    
    def clear_user_history(self, user_id: int) -> bool:
        """
        Clear user history
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.user_history:
                return False
            
            history = self.user_history[user_id]
            history.activity_logs = []
            history.login_history = []
            history.transaction_history = []
            history.statistics = {}
            history.updated_at = datetime.now()
            
            self.logger.info(f"Cleared history for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear user history: {e}")
            return False
    
    # Helper Methods
    
    def _generate_user_id(self) -> int:
        """Generate unique user ID"""
        if not self.user_profiles:
            return 1
        return max(self.user_profiles.keys()) + 1
    
    def _create_default_preferences(self, user_id: int):
        """Create default preferences for user"""
        try:
            preferences = UserPreferences(
                user_id=user_id,
                display={
                    'theme': 'light',
                    'brightness': 80,
                    'contrast': 60,
                    'orientation': 'landscape'
                },
                notifications={
                    'enabled': True,
                    'sound': True,
                    'vibration': False
                },
                privacy={
                    'data_collection': True,
                    'analytics': True,
                    'crash_reports': True
                },
                accessibility={
                    'large_text': False,
                    'high_contrast': False,
                    'screen_reader': False
                },
                language='en',
                timezone='UTC',
                theme='light',
                auto_login=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.user_preferences[user_id] = preferences
            
        except Exception as e:
            self.logger.error(f"Failed to create default preferences: {e}")
    
    def _create_default_history(self, user_id: int):
        """Create default history for user"""
        try:
            history = UserHistory(
                user_id=user_id,
                activity_logs=[],
                login_history=[],
                transaction_history=[],
                statistics={
                    'total_logins': 0,
                    'total_deposits': 0,
                    'total_amount': 0.0,
                    'average_session_time': 0
                },
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.user_history[user_id] = history
            
        except Exception as e:
            self.logger.error(f"Failed to create default history: {e}")
    
    # Callback Methods
    
    def register_profile_callback(self, callback: Callable[[UserProfile, str], None]):
        """Register profile callback"""
        self.profile_callbacks.append(callback)
        self.logger.info("Profile callback registered")
    
    def register_preference_callback(self, callback: Callable[[UserPreferences, str], None]):
        """Register preference callback"""
        self.preference_callbacks.append(callback)
        self.logger.info("Preference callback registered")
    
    def register_history_callback(self, callback: Callable[[UserHistory, str], None]):
        """Register history callback"""
        self.history_callbacks.append(callback)
        self.logger.info("History callback registered")
    
    def _notify_profile_callbacks(self, profile: UserProfile, action: str):
        """Notify profile callbacks"""
        for callback in self.profile_callbacks:
            try:
                callback(profile, action)
            except Exception as e:
                self.logger.error(f"Profile callback error: {e}")
    
    def _notify_preference_callbacks(self, preferences: UserPreferences, action: str):
        """Notify preference callbacks"""
        for callback in self.preference_callbacks:
            try:
                callback(preferences, action)
            except Exception as e:
                self.logger.error(f"Preference callback error: {e}")
    
    def _notify_history_callbacks(self, history: UserHistory, action: str):
        """Notify history callbacks"""
        for callback in self.history_callbacks:
            try:
                callback(history, action)
            except Exception as e:
                self.logger.error(f"History callback error: {e}")
    
    # Status and Management Methods
    
    def get_manager_status(self) -> Dict:
        """Get manager status"""
        return {
            'total_users': len(self.user_profiles),
            'total_preferences': len(self.user_preferences),
            'total_history': len(self.user_history),
            'database_path': self.database_path,
            'sync_thread_running': self.sync_thread.is_alive() if self.sync_thread else False,
            'api_client_available': self.api_client is not None
        }
    
    def shutdown(self):
        """Shutdown user profile manager"""
        try:
            self.logger.info("Shutting down User Profile Manager...")
            
            # Stop sync thread
            self.shutdown_event.set()
            
            if self.sync_thread and self.sync_thread.is_alive():
                self.sync_thread.join(timeout=5)
            
            # Save final data
            self._save_user_data()
            
            self.logger.info("User Profile Manager shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error shutting down User Profile Manager: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test user profile manager
    manager = UserProfileManager()
    
    print("User Profile Manager Test:")
    print("=" * 50)
    
    # Test user profile creation
    print("\n1. Testing User Profile Creation...")
    user_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+1234567890',
        'balance': 15000.0
    }
    
    profile = manager.create_user_profile(user_data)
    if profile:
        print(f"   ✅ Created profile for user {profile.user_id}")
        print(f"   Name: {profile.name}")
        print(f"   Email: {profile.email}")
        print(f"   Balance: {profile.balance}")
    else:
        print("   ❌ Failed to create profile")
    
    # Test user preferences
    print("\n2. Testing User Preferences...")
    if profile:
        user_id = profile.user_id
        
        # Set preferences
        manager.set_user_preference(user_id, 'display.theme', 'dark')
        manager.set_user_preference(user_id, 'notifications.enabled', False)
        manager.set_user_preference(user_id, 'language', 'id')
        
        # Get preferences
        theme = manager.get_user_preference(user_id, 'display.theme')
        notifications = manager.get_user_preference(user_id, 'notifications.enabled')
        language = manager.get_user_preference(user_id, 'language')
        
        print(f"   Theme: {theme}")
        print(f"   Notifications: {notifications}")
        print(f"   Language: {language}")
    
    # Test user history
    print("\n3. Testing User History...")
    if profile:
        user_id = profile.user_id
        
        # Log activities
        manager.log_user_activity(user_id, 'login', {'method': 'qr_code'})
        manager.log_user_activity(user_id, 'deposit', {'amount': 5000, 'items': ['bottle']})
        manager.log_user_activity(user_id, 'logout', {'duration': 300})
        
        # Get history
        history = manager.get_user_history(user_id, 10)
        print(f"   History entries: {len(history)}")
        for entry in history:
            print(f"   - {entry['activity']}: {entry['data']}")
    
    # Test user profile management
    print("\n4. Testing User Profile Management...")
    if profile:
        user_id = profile.user_id
        
        # Update profile
        updates = {
            'name': 'John Smith',
            'balance': 20000.0
        }
        success = manager.update_user_profile(user_id, updates)
        print(f"   Profile update: {'✅ Success' if success else '❌ Failed'}")
        
        # Get updated profile
        updated_profile = manager.get_user_profile(user_id)
        if updated_profile:
            print(f"   Updated name: {updated_profile.name}")
            print(f"   Updated balance: {updated_profile.balance}")
    
    # Test search
    print("\n5. Testing User Search...")
    search_results = manager.search_user_profiles('john')
    print(f"   Search results: {len(search_results)}")
    for result in search_results:
        print(f"   - {result.name} ({result.email})")
    
    # Get manager status
    print("\n6. Manager Status:")
    status = manager.get_manager_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Shutdown
    print("\n7. Shutting down...")
    manager.shutdown()
    
    print("\n✅ User Profile Manager test completed successfully!")


