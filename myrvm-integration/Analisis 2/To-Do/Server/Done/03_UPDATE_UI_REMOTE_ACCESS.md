# TASK 03: UPDATE UI UNTUK REMOTE ACCESS FUNCTIONALITY

**Tanggal**: 2025-01-20  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 3-4 jam  

---

## **📋 DESKRIPSI TUGAS**

Update UI di MyRVM Platform untuk mendukung Remote Access functionality.

### **🎯 TUJUAN:**
- Update RVM Management UI untuk remote access
- Update Dashboard UI untuk remote access
- Implementasi modal dan status indicators
- Integration dengan existing UI components

---

## **🔧 IMPLEMENTASI**

### **1. Update RVM Management Page (all.blade.php)**

#### **A. Update Action Buttons:**
```html
<!-- File: resources/views/admin/rvm/all.blade.php -->

<!-- Update existing action buttons section -->
<div class="btn-group" role="group">
    <button type="button" class="btn btn-outline-info btn-sm" onclick="viewRVMDetails({{ $rvm->id }})">
        <i class="fas fa-eye"></i> View
    </button>
    <button type="button" class="btn btn-outline-warning btn-sm" onclick="editRVM({{ $rvm->id }})">
        <i class="fas fa-edit"></i> Edit
    </button>
    <button type="button" class="btn btn-outline-primary btn-sm remote-access-btn" 
            data-rvm-id="{{ $rvm->id }}" 
            onclick="startRemoteAccess({{ $rvm->id }})">
        <i class="fas fa-desktop"></i> Remote Access
    </button>
    <button type="button" class="btn btn-outline-success btn-sm" onclick="syncTimezone({{ $rvm->id }})">
        <i class="fas fa-sync"></i> Sync
    </button>
    <button type="button" class="btn btn-outline-secondary btn-sm" onclick="updateStatus({{ $rvm->id }})">
        <i class="fas fa-cog"></i> Status
    </button>
    <button type="button" class="btn btn-outline-danger btn-sm" onclick="deleteRVM({{ $rvm->id }})">
        <i class="fas fa-trash"></i> Delete
    </button>
</div>
```

#### **B. Update Status Column:**
```html
<!-- Update status column to show remote access status -->
<td>
    <span class="badge bg-{{ $rvm->status === 'active' ? 'success' : ($rvm->status === 'maintenance' ? 'warning' : 'danger') }}">
        {{ ucfirst($rvm->status) }}
    </span>
    @if($rvm->status === 'maintenance')
        <br><small class="text-muted">
            <i class="fas fa-desktop"></i> Remote Access Active
        </small>
    @endif
</td>
```

#### **C. Add Remote Access Status Column:**
```html
<!-- Add new column for remote access status -->
<thead>
    <tr>
        <th>ID</th>
        <th>Name</th>
        <th>Location</th>
        <th>IP Address</th>
        <th>Status</th>
        <th>Remote Access</th>
        <th>Last Ping</th>
        <th>Actions</th>
    </tr>
</thead>

<tbody>
    @foreach($rvms as $rvm)
    <tr>
        <td>{{ $rvm->id }}</td>
        <td>{{ $rvm->name }}</td>
        <td>{{ $rvm->location }}</td>
        <td>
            {{ $rvm->ip_address }}
            <br><small class="text-muted">Port: {{ $rvm->port ?? 8000 }}</small>
        </td>
        <td>
            <span class="badge bg-{{ $rvm->status === 'active' ? 'success' : ($rvm->status === 'maintenance' ? 'warning' : 'danger') }}">
                {{ ucfirst($rvm->status) }}
            </span>
        </td>
        <td>
            <div class="remote-access-status" data-rvm-id="{{ $rvm->id }}">
                <span class="badge bg-secondary">
                    <i class="fas fa-circle"></i> Inactive
                </span>
            </div>
        </td>
        <td>
            <div class="connection-status" data-rvm-id="{{ $rvm->id }}">
                <i class="fas fa-question-circle text-muted"></i> Unknown
            </div>
        </td>
        <td>
            <!-- Action buttons as above -->
        </td>
    </tr>
    @endforeach
</tbody>
```

### **2. Update Dashboard Page (index.blade.php)**

#### **A. Update RVM Cards:**
```html
<!-- File: resources/views/admin/dashboard/index.blade.php -->

<!-- Update RVM card actions -->
<div class="card-actions">
    <button class="btn btn-outline-primary btn-sm" onclick="openRemoteAccess({{ $rvm['id'] }})">
        <i class="fas fa-desktop"></i> Remote Access
    </button>
    <button class="btn btn-outline-secondary btn-sm" onclick="openStatusModal({{ $rvm['id'] }})">
        <i class="fas fa-cog"></i> Status
    </button>
</div>
```

#### **B. Add Remote Access Status to RVM Cards:**
```html
<!-- Add remote access status to RVM card -->
<div class="rvm-card" data-rvm-id="{{ $rvm['id'] }}">
    <div class="card-header">
        <h6 class="card-title">{{ $rvm['name'] }}</h6>
        <div class="card-status">
            <span class="badge bg-{{ $rvm['calculated_status'] === 'active' ? 'success' : 'warning' }}">
                {{ ucfirst($rvm['calculated_status']) }}
            </span>
            <div class="remote-access-indicator" data-rvm-id="{{ $rvm['id'] }}">
                <i class="fas fa-circle text-muted"></i>
            </div>
        </div>
    </div>
    <!-- ... rest of card content ... -->
</div>
```

### **3. Create Remote Access Modal**

#### **A. Remote Access Modal HTML:**
```html
<!-- File: resources/views/admin/rvm/remote-access-modal.blade.php -->

<!-- Remote Access Modal -->
<div class="modal fade" id="remoteAccessModal" tabindex="-1" aria-labelledby="remoteAccessModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="remoteAccessModalLabel">
                    <i class="fas fa-desktop me-2"></i>Remote Access
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div id="remoteAccessContent">
                    <!-- Content will be loaded dynamically -->
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary" id="remoteAccessActionBtn">
                    <i class="fas fa-desktop"></i> Start Remote Access
                </button>
            </div>
        </div>
    </div>
</div>
```

#### **B. Remote Access Status Modal:**
```html
<!-- Remote Access Status Modal -->
<div class="modal fade" id="remoteAccessStatusModal" tabindex="-1" aria-labelledby="remoteAccessStatusModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="remoteAccessStatusModalLabel">
                    <i class="fas fa-info-circle me-2"></i>Remote Access Status
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div id="remoteAccessStatusContent">
                    <!-- Status content will be loaded dynamically -->
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-danger" id="stopRemoteAccessBtn" style="display: none;">
                    <i class="fas fa-stop"></i> Stop Remote Access
                </button>
            </div>
        </div>
    </div>
</div>
```

### **4. Update JavaScript Functions**

#### **A. Update rvm-cards.js:**
```javascript
// File: public/js/admin/dashboard/rvm-cards.js

// Update openRemoteAccess function
function openRemoteAccess(rvmId) {
    // Get RVM data
    const rvm = rvmData.find(r => r.id === rvmId);
    if (!rvm) {
        alert('RVM not found');
        return;
    }
    
    // Check current remote access status
    fetch(`/admin/rvm/${rvmId}/remote-access/status`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const status = data.data;
                
                if (status.active_session) {
                    // Show active session info
                    showActiveRemoteAccessModal(status);
                } else {
                    // Show start remote access modal
                    showStartRemoteAccessModal(rvm);
                }
            } else {
                alert('Failed to get remote access status: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Remote access status error:', error);
            alert('Network error: ' + error.message);
        });
}

function showStartRemoteAccessModal(rvm) {
    const modal = new bootstrap.Modal(document.getElementById('remoteAccessModal'));
    const content = document.getElementById('remoteAccessContent');
    const actionBtn = document.getElementById('remoteAccessActionBtn');
    
    content.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>RVM Information</h6>
                <table class="table table-sm">
                    <tr>
                        <td><strong>Name:</strong></td>
                        <td>${rvm.name}</td>
                    </tr>
                    <tr>
                        <td><strong>Location:</strong></td>
                        <td>${rvm.location}</td>
                    </tr>
                    <tr>
                        <td><strong>IP Address:</strong></td>
                        <td>${rvm.ip_address}</td>
                    </tr>
                    <tr>
                        <td><strong>Current Status:</strong></td>
                        <td><span class="badge bg-${rvm.calculated_status === 'active' ? 'success' : 'warning'}">${rvm.calculated_status}</span></td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>Remote Access Information</h6>
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    <strong>Note:</strong> Starting remote access will change RVM status to "maintenance" and disable normal operations.
                </div>
                <div class="form-group">
                    <label>Access Port:</label>
                    <input type="number" class="form-control" id="remoteAccessPort" value="5001" min="1" max="65535">
                </div>
                <div class="form-group">
                    <label>Client IP:</label>
                    <input type="text" class="form-control" id="clientIP" value="${getClientIP()}" readonly>
                </div>
            </div>
        </div>
    `;
    
    actionBtn.innerHTML = '<i class="fas fa-desktop"></i> Start Remote Access';
    actionBtn.className = 'btn btn-primary';
    actionBtn.onclick = () => startRemoteAccess(rvm.id);
    
    modal.show();
}

function showActiveRemoteAccessModal(status) {
    const modal = new bootstrap.Modal(document.getElementById('remoteAccessStatusModal'));
    const content = document.getElementById('remoteAccessStatusContent');
    const stopBtn = document.getElementById('stopRemoteAccessBtn');
    
    const session = status.active_session;
    const duration = formatDuration(session.duration);
    
    content.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>Active Session</h6>
                <table class="table table-sm">
                    <tr>
                        <td><strong>Session ID:</strong></td>
                        <td>${session.session_id}</td>
                    </tr>
                    <tr>
                        <td><strong>Admin:</strong></td>
                        <td>${session.admin_name}</td>
                    </tr>
                    <tr>
                        <td><strong>Start Time:</strong></td>
                        <td>${formatDateTime(session.start_time)}</td>
                    </tr>
                    <tr>
                        <td><strong>Duration:</strong></td>
                        <td>${duration}</td>
                    </tr>
                    <tr>
                        <td><strong>IP Address:</strong></td>
                        <td>${session.ip_address || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td><strong>Port:</strong></td>
                        <td>${session.port || 'N/A'}</td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>RVM Status</h6>
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Maintenance Mode:</strong> RVM is currently in maintenance mode due to active remote access session.
                </div>
                <div class="form-group">
                    <label>Stop Reason:</label>
                    <textarea class="form-control" id="stopReason" rows="3" placeholder="Optional reason for stopping remote access..."></textarea>
                </div>
            </div>
        </div>
    `;
    
    stopBtn.style.display = 'block';
    stopBtn.onclick = () => stopRemoteAccess(status.rvm_id);
    
    modal.show();
}

// Helper functions
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function getClientIP() {
    // This would need to be implemented based on your setup
    return '192.168.1.100'; // Placeholder
}
```

### **5. Update CSS Styles**

#### **A. Add Remote Access Styles:**
```css
/* File: public/css/admin/remote-access.css */

.remote-access-status {
    display: inline-block;
}

.remote-access-status .badge {
    font-size: 0.75rem;
}

.remote-access-indicator {
    display: inline-block;
    margin-left: 5px;
}

.remote-access-indicator.active {
    color: #28a745 !important;
}

.remote-access-indicator.inactive {
    color: #6c757d !important;
}

.connection-status {
    font-size: 0.875rem;
}

.connection-status .text-success {
    color: #28a745 !important;
}

.connection-status .text-danger {
    color: #dc3545 !important;
}

.connection-status .text-warning {
    color: #ffc107 !important;
}

.port-details {
    font-size: 0.75rem;
    color: #6c757d;
}

.port-details .d-block {
    margin-bottom: 2px;
}

.remote-access-btn {
    min-width: 120px;
}

.remote-access-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

/* Modal specific styles */
#remoteAccessModal .modal-body,
#remoteAccessStatusModal .modal-body {
    max-height: 70vh;
    overflow-y: auto;
}

.remote-access-info {
    background-color: #f8f9fa;
    border-radius: 0.375rem;
    padding: 1rem;
    margin-bottom: 1rem;
}

.remote-access-info h6 {
    color: #495057;
    margin-bottom: 0.5rem;
}

.remote-access-info .table {
    margin-bottom: 0;
}

.remote-access-info .table td {
    border: none;
    padding: 0.25rem 0.5rem;
}

.remote-access-info .table td:first-child {
    font-weight: 600;
    width: 40%;
}
```

### **6. Update Layout Files**

#### **A. Include Remote Access CSS:**
```html
<!-- File: resources/views/layouts/admin.blade.php -->

<!-- Add to head section -->
<link rel="stylesheet" href="{{ asset('css/admin/remote-access.css') }}">
```

#### **B. Include Remote Access JavaScript:**
```html
<!-- File: resources/views/layouts/admin.blade.php -->

<!-- Add to scripts section -->
<script src="{{ asset('js/admin/dashboard/remote-access.js') }}"></script>
```

#### **C. Include Modals:**
```html
<!-- File: resources/views/admin/rvm/all.blade.php -->

<!-- Add modals at the end of the file -->
@include('admin.rvm.remote-access-modal')
```

---

## **🧪 TESTING**

### **1. UI Testing:**

#### **A. RVM Management Page:**
- Verify remote access button appears
- Verify status column shows remote access status
- Verify connection status column shows port details
- Test button click functionality

#### **B. Dashboard Page:**
- Verify remote access button in RVM cards
- Verify remote access indicator
- Test modal opening functionality

#### **C. Modal Testing:**
- Test start remote access modal
- Test active session modal
- Test form validation
- Test button functionality

### **2. Integration Testing:**
- Test with real RVM data
- Test with different RVM statuses
- Test error handling
- Test responsive design

---

## **📋 CHECKLIST**

- [ ] Update RVM Management page action buttons
- [ ] Update status column with remote access info
- [ ] Add remote access status column
- [ ] Update Dashboard RVM cards
- [ ] Create remote access modal
- [ ] Create remote access status modal
- [ ] Update JavaScript functions
- [ ] Add CSS styles for remote access
- [ ] Include CSS and JS files in layout
- [ ] Test UI functionality
- [ ] Test modal interactions
- [ ] Test responsive design
- [ ] Test error handling
- [ ] Verify integration with existing UI

---

## **📝 NOTES**

- Remote access button changes based on session status
- Status indicators show real-time information
- Modals provide detailed session information
- CSS ensures consistent styling
- JavaScript handles all interactions
- Integration with existing UI components

---

**Status**: 🔄 **IN PROGRESS**  
**Next**: Testing dan Integration

