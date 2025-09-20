// MyRVM GUI Client JavaScript
class MyRVMApp {
    constructor() {
        this.currentScreen = 'login';
        this.userSession = null;
        this.qrCodeInterval = null;
        this.statusInterval = null;
        this.detectionInterval = null;
        this.systemInfoInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startStatusUpdates();
        this.updateCurrentTime();
        this.loadQRCode();
        
        // Update time every second
        setInterval(() => this.updateCurrentTime(), 1000);
    }
    
    setupEventListeners() {
        // QR Code refresh
        document.getElementById('refresh-qr').addEventListener('click', () => {
            this.loadQRCode();
        });
        
        // Logout button
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.logout();
        });
        
        // Action buttons
        document.getElementById('deposit-btn').addEventListener('click', () => {
            this.showNotification('Deposit feature coming soon!', 'info');
        });
        
        document.getElementById('profile-btn').addEventListener('click', () => {
            this.changeScreen('profile');
        });
        
        document.getElementById('history-btn').addEventListener('click', () => {
            this.showNotification('History feature coming soon!', 'info');
        });
        
        document.getElementById('settings-btn').addEventListener('click', () => {
            this.changeScreen('settings');
        });
        
        // Back buttons
        document.getElementById('back-to-main').addEventListener('click', () => {
            this.changeScreen('main');
        });
        
        document.getElementById('back-to-main-settings').addEventListener('click', () => {
            this.changeScreen('main');
        });
    }
    
    async loadQRCode() {
        try {
            this.showQRCodeLoading(true);
            
            const response = await fetch('/api/qr-code');
            const data = await response.json();
            
            if (data.success) {
                const qrCodeImg = document.getElementById('qr-code-image');
                qrCodeImg.src = `data:image/png;base64,${data.qr_code}`;
                qrCodeImg.style.display = 'block';
                
                // Auto-refresh QR code every 30 seconds
                if (this.qrCodeInterval) {
                    clearInterval(this.qrCodeInterval);
                }
                this.qrCodeInterval = setInterval(() => {
                    this.loadQRCode();
                }, 30000);
                
                this.showNotification('QR Code generated successfully', 'success');
            } else {
                this.showNotification('Failed to generate QR Code', 'error');
            }
        } catch (error) {
            console.error('Error loading QR code:', error);
            this.showNotification('Error loading QR Code', 'error');
        } finally {
            this.showQRCodeLoading(false);
        }
    }
    
    showQRCodeLoading(show) {
        const loading = document.querySelector('.qr-code-loading');
        const image = document.getElementById('qr-code-image');
        
        if (show) {
            loading.classList.add('active');
            image.style.display = 'none';
        } else {
            loading.classList.remove('active');
            image.style.display = 'block';
        }
    }
    
    async authenticateUser(qrData) {
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/authenticate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ qr_data: qrData })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.userSession = data.session;
                this.updateUserInfo();
                this.changeScreen('main');
                this.showNotification('Login successful!', 'success');
            } else {
                this.showNotification(data.error || 'Authentication failed', 'error');
            }
        } catch (error) {
            console.error('Authentication error:', error);
            this.showNotification('Authentication error', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async logout() {
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.userSession = null;
                this.changeScreen('login');
                this.showNotification('Logged out successfully', 'success');
                
                // Clear intervals
                if (this.qrCodeInterval) {
                    clearInterval(this.qrCodeInterval);
                }
                if (this.detectionInterval) {
                    clearInterval(this.detectionInterval);
                }
                
                // Reload QR code
                this.loadQRCode();
            } else {
                this.showNotification(data.error || 'Logout failed', 'error');
            }
        } catch (error) {
            console.error('Logout error:', error);
            this.showNotification('Logout error', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    changeScreen(screen) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(s => {
            s.classList.remove('active');
        });
        
        // Show target screen
        document.getElementById(`${screen}-screen`).classList.add('active');
        this.currentScreen = screen;
        
        // Update screen on server
        this.updateScreenOnServer(screen);
        
        // Load screen-specific data
        if (screen === 'profile') {
            this.loadProfileData();
        } else if (screen === 'settings') {
            this.loadSystemInfo();
        } else if (screen === 'main') {
            this.startDetectionUpdates();
        }
    }
    
    async updateScreenOnServer(screen) {
        try {
            await fetch('/api/change-screen', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ screen: screen })
            });
        } catch (error) {
            console.error('Error updating screen:', error);
        }
    }
    
    updateUserInfo() {
        if (this.userSession) {
            const user = this.userSession.user;
            
            // Update main screen
            document.getElementById('user-name').textContent = user.name;
            document.getElementById('user-email').textContent = user.email;
            document.getElementById('user-balance').textContent = this.formatCurrency(user.balance);
            
            // Update profile screen
            document.getElementById('profile-name').textContent = user.name;
            document.getElementById('profile-email').textContent = user.email;
            document.getElementById('profile-balance').textContent = this.formatCurrency(user.balance);
        }
    }
    
    async loadProfileData() {
        if (this.userSession) {
            // Profile data is already loaded from user session
            this.updateUserInfo();
        }
    }
    
    async loadSystemInfo() {
        try {
            const response = await fetch('/api/system-info');
            const data = await response.json();
            
            if (data.success) {
                const systemInfo = data.system_info;
                
                document.getElementById('system-rvm-id').textContent = systemInfo.rvm_id || 'N/A';
                document.getElementById('system-status-info').textContent = systemInfo.status || 'Online';
                document.getElementById('system-uptime').textContent = systemInfo.uptime || 'N/A';
                document.getElementById('system-cpu').textContent = `${systemInfo.cpu_usage || 0}%`;
                document.getElementById('system-memory').textContent = `${systemInfo.memory_usage || 0}%`;
            }
        } catch (error) {
            console.error('Error loading system info:', error);
        }
    }
    
    startStatusUpdates() {
        this.statusInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                if (data.success) {
                    const status = data.status;
                    
                    // Update system status
                    document.getElementById('system-status').textContent = status.auth_status ? 'Online' : 'Offline';
                    document.getElementById('connection-status').textContent = 'Connected';
                    
                    // Update current screen if changed
                    if (status.current_screen !== this.currentScreen) {
                        this.changeScreen(status.current_screen);
                    }
                    
                    // Update user session if changed
                    if (status.user_session && !this.userSession) {
                        this.userSession = status.user_session;
                        this.updateUserInfo();
                    } else if (!status.user_session && this.userSession) {
                        this.userSession = null;
                        this.changeScreen('login');
                    }
                }
            } catch (error) {
                console.error('Status update error:', error);
                document.getElementById('connection-status').textContent = 'Disconnected';
            }
        }, 5000); // Update every 5 seconds
    }
    
    startDetectionUpdates() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
        }
        
        this.detectionInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/detection-results');
                const data = await response.json();
                
                if (data.success) {
                    this.updateDetectionResults(data.results);
                }
            } catch (error) {
                console.error('Detection update error:', error);
            }
        }, 2000); // Update every 2 seconds
    }
    
    updateDetectionResults(results) {
        const detectionList = document.getElementById('detection-list');
        
        if (results && results.length > 0) {
            detectionList.innerHTML = '';
            
            results.slice(-10).reverse().forEach(result => {
                const detectionItem = document.createElement('div');
                detectionItem.className = 'detection-item';
                
                detectionItem.innerHTML = `
                    <div class="detection-info">
                        <div class="detection-class">${result.class || 'Unknown'}</div>
                        <div class="detection-confidence">Confidence: ${(result.confidence * 100).toFixed(1)}%</div>
                    </div>
                    <div class="detection-time">${this.formatTime(result.timestamp)}</div>
                `;
                
                detectionList.appendChild(detectionItem);
            });
        } else {
            detectionList.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No detection results yet</p>
                </div>
            `;
        }
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (show) {
            overlay.classList.add('active');
        } else {
            overlay.classList.remove('active');
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        const messageElement = document.getElementById('notification-message');
        
        messageElement.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
    
    updateCurrentTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        document.getElementById('current-time').textContent = timeString;
    }
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0
        }).format(amount);
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MyRVMApp();
});

// Handle QR code scanning simulation (for testing)
// In real implementation, this would be handled by the mobile app
document.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && window.app.currentScreen === 'login') {
        // Simulate QR code scan for testing
        const mockQRData = {
            rvm_id: 'jetson_orin_nano_001',
            timestamp: Math.floor(Date.now() / 1000),
            action: 'login',
            session_token: 'test_token_' + Date.now(),
            expires_at: Math.floor(Date.now() / 1000) + 60,
            version: '1.0'
        };
        
        window.app.authenticateUser(mockQRData);
    }
});

