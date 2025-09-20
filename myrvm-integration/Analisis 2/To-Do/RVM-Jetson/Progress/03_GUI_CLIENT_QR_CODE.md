# Task 03: GUI Client QR Code Authentication

**Tanggal**: 2025-01-20  
**Status**: 🔄 **IN PROGRESS**  
**Priority**: ⚡ **MEDIUM**  
**Phase**: 2 - GUI Client Development

---

## **🎯 OBJECTIVE**

Implement QR Code authentication system untuk:
1. Generate QR Code untuk user login
2. Handle QR Code scanning dan validation
3. User authentication dan session management
4. User profile display
5. Session timeout handling
6. Multi-user support
7. Security validation

---

## **📋 REQUIREMENTS**

### **QR Code Generation:**
```python
# QR Code data structure
{
    "rvm_id": "jetson_orin_nano_001",
    "timestamp": 1640995200,
    "action": "login",
    "session_token": "temp_session_token",
    "expires_at": 1640995260
}
```

### **User Authentication Flow:**
1. **QR Code Display**: Generate dan display QR Code
2. **Mobile App Scan**: User scan QR Code dengan mobile app
3. **Server Validation**: Validate QR Code di server
4. **User Login**: User login melalui mobile app
5. **Session Creation**: Create user session di RVM
6. **GUI Update**: Update GUI dengan user info

### **User Profile Display:**
```python
# User profile data
{
    "user_id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "avatar": "avatar_url",
    "status": "active",
    "balance": 15000,
    "last_login": "2025-01-20T10:30:00Z"
}
```

---

## **🔧 IMPLEMENTATION PLAN**

### **Step 1: QR Code Generation System**
```python
class QRCodeGenerator:
    """QR Code generator for user authentication"""
    
    def __init__(self, rvm_id, session_manager):
        self.rvm_id = rvm_id
        self.session_manager = session_manager
        self.qr_code_data = {}
        self.qr_code_image = None
        self.expiration_time = 60  # 1 minute
```

### **Step 2: User Authentication Handler**
```python
class UserAuthenticationHandler:
    """Handle user authentication via QR Code"""
    
    def __init__(self, api_client, session_manager):
        self.api_client = api_client
        self.session_manager = session_manager
        self.active_sessions = {}
        self.session_timeout = 3600  # 1 hour
```

### **Step 3: GUI Integration**
- Update HTML templates dengan QR Code display
- Add JavaScript untuk QR Code handling
- Implement user profile display
- Add session management UI

### **Step 4: Security Implementation**
- QR Code expiration handling
- Session validation
- User permission checking
- Security logging

---

## **📁 FILES TO CREATE/MODIFY**

### **New Files:**
- `gui/qr_code_generator.py` - QR Code generation
- `gui/user_authentication.py` - User authentication
- `gui/session_manager.py` - Session management
- `templates/qr_login.html` - QR Code login template
- `static/js/qr-authentication.js` - QR Code JavaScript
- `static/css/qr-authentication.css` - QR Code styling

### **Modified Files:**
- `templates/dashboard.html` - Add QR Code integration
- `static/js/dashboard.js` - Add QR Code functionality
- `main/enhanced_jetson_main.py` - Add GUI server
- `services/remote_gui_service.py` - Update GUI service

---

## **🧪 TESTING PLAN**

### **Unit Tests:**
- QR Code generation tests
- User authentication tests
- Session management tests
- Security validation tests

### **Integration Tests:**
- QR Code scanning tests
- User login flow tests
- Session timeout tests
- Multi-user tests

### **Test Scenarios:**
1. **Normal Login**: QR Code generation, scan, login
2. **Expired QR Code**: Handle expired QR Code
3. **Invalid QR Code**: Handle invalid QR Code
4. **Session Timeout**: Handle session expiration
5. **Multi-user**: Multiple users login/logout

---

## **📊 SUCCESS CRITERIA**

### **Functional Requirements:**
- ✅ Generate QR Code untuk user login
- ✅ Handle QR Code scanning dan validation
- ✅ User authentication dan session management
- ✅ User profile display
- ✅ Session timeout handling
- ✅ Multi-user support
- ✅ Security validation

### **Performance Requirements:**
- ✅ QR Code generation: < 1 second
- ✅ User authentication: < 2 seconds
- ✅ Session validation: < 500ms
- ✅ GUI update: < 1 second
- ✅ Memory usage: < 100MB for GUI

### **Security Requirements:**
- ✅ QR Code expiration: 1 minute
- ✅ Session timeout: 1 hour
- ✅ User validation: 100% accuracy
- ✅ Security logging: All events logged

---

## **📝 IMPLEMENTATION NOTES**

### **QR Code Generation:**
```python
def generate_qr_code(self):
    """Generate QR Code for user login"""
    qr_data = {
        "rvm_id": self.rvm_id,
        "timestamp": int(time.time()),
        "action": "login",
        "session_token": self._generate_session_token(),
        "expires_at": int(time.time()) + self.expiration_time
    }
    
    # Generate QR Code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img, qr_data
```

### **User Authentication:**
```python
def authenticate_user(self, qr_data, user_credentials):
    """Authenticate user via QR Code"""
    # Validate QR Code
    if not self._validate_qr_code(qr_data):
        return False
    
    # Authenticate user
    user_data = self.api_client.authenticate_user(user_credentials)
    if not user_data:
        return False
    
    # Create session
    session = self.session_manager.create_session(user_data)
    return session
```

### **Session Management:**
```python
class SessionManager:
    """Manage user sessions"""
    
    def __init__(self):
        self.active_sessions = {}
        self.session_timeout = 3600  # 1 hour
    
    def create_session(self, user_data):
        """Create new user session"""
        session_id = self._generate_session_id()
        session = {
            "session_id": session_id,
            "user_data": user_data,
            "created_at": time.time(),
            "last_activity": time.time(),
            "status": "active"
        }
        self.active_sessions[session_id] = session
        return session
```

---

## **🔄 PROGRESS TRACKING**

### **Completed:**
- [ ] QR Code generator implementation
- [ ] User authentication handler
- [ ] Session management system
- [ ] GUI integration
- [ ] Security implementation
- [ ] HTML templates
- [ ] JavaScript functionality
- [ ] CSS styling
- [ ] Unit tests
- [ ] Integration tests
- [ ] Documentation

### **Current Status:**
- **Progress**: 0% - Starting implementation
- **Next Step**: Create QR Code generator class
- **Estimated Completion**: 3-4 days

---

## **📚 REFERENCES**

### **Related Documents:**
- `Analisis 2/14_UPDATE_BERDASARKAN_FEEDBACK_FINAL.md` - QR Code requirements
- `Analisis 2/15_SUMMARY_FINAL_COMPLETE.md` - GUI client requirements
- `templates/dashboard.html` - Existing dashboard template

### **Dependencies:**
- `qrcode` library untuk QR Code generation
- `Pillow` library untuk image handling
- `requests` library untuk API communication
- `flask` library untuk web server

---

**Status**: 🔄 **IN PROGRESS**  
**Next Update**: After completing QR Code generator  
**Estimated Completion**: 2025-01-23
