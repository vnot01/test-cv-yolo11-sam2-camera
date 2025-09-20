# TASK 02: IMPLEMENTASI REMOTE ACCESS API ENDPOINTS

**Tanggal**: 2025-01-20  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 4-5 jam  

---

## **📋 DESKRIPSI TUGAS**

Implementasi API endpoints untuk Remote Access functionality di MyRVM Platform.

### **🎯 TUJUAN:**
- Implementasi API endpoints untuk remote access
- Database schema untuk remote access sessions
- Integration dengan RVM status management

---

## **🔧 IMPLEMENTASI**

### **1. Database Migration**

#### **A. Create Remote Access Sessions Table:**
```php
// File: database/migrations/2025_01_20_000000_create_remote_access_sessions_table.php

<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up()
    {
        Schema::create('remote_access_sessions', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('rvm_id');
            $table->unsignedBigInteger('admin_id');
            $table->timestamp('start_time');
            $table->timestamp('end_time')->nullable();
            $table->string('status')->default('active'); // active, completed, terminated
            $table->string('ip_address', 45)->nullable();
            $table->integer('port')->nullable();
            $table->text('reason')->nullable(); // session completion reason
            $table->timestamps();
            
            $table->foreign('rvm_id')->references('id')->on('reverse_vending_machines')->onDelete('cascade');
            $table->foreign('admin_id')->references('id')->on('users')->onDelete('cascade');
            
            $table->index(['rvm_id', 'status']);
            $table->index(['admin_id', 'status']);
        });
    }

    public function down()
    {
        Schema::dropIfExists('remote_access_sessions');
    }
};
```

### **2. Model Creation**

#### **A. Remote Access Session Model:**
```php
// File: app/Models/RemoteAccessSession.php

<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class RemoteAccessSession extends Model
{
    use HasFactory;

    protected $fillable = [
        'rvm_id',
        'admin_id',
        'start_time',
        'end_time',
        'status',
        'ip_address',
        'port',
        'reason'
    ];

    protected $casts = [
        'start_time' => 'datetime',
        'end_time' => 'datetime'
    ];

    public function rvm(): BelongsTo
    {
        return $this->belongsTo(ReverseVendingMachine::class, 'rvm_id');
    }

    public function admin(): BelongsTo
    {
        return $this->belongsTo(User::class, 'admin_id');
    }

    public function isActive(): bool
    {
        return $this->status === 'active' && is_null($this->end_time);
    }

    public function getDurationAttribute(): ?int
    {
        if ($this->end_time) {
            return $this->start_time->diffInSeconds($this->end_time);
        }
        
        return $this->start_time->diffInSeconds(now());
    }
}
```

### **3. Controller Implementation**

#### **A. Remote Access Controller:**
```php
// File: app/Http/Controllers/Admin/RemoteAccessController.php

<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\RemoteAccessSession;
use App\Models\ReverseVendingMachine;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Facades\DB;

class RemoteAccessController extends Controller
{
    public function start(Request $request, $id)
    {
        $validator = Validator::make($request->all(), [
            'admin_id' => 'required|exists:users,id',
            'ip_address' => 'nullable|ip',
            'port' => 'nullable|integer|min:1|max:65535'
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            
            // Check if there's already an active session
            $activeSession = RemoteAccessSession::where('rvm_id', $id)
                ->where('status', 'active')
                ->whereNull('end_time')
                ->first();

            if ($activeSession) {
                return response()->json([
                    'success' => false,
                    'message' => 'Remote access session already active for this RVM'
                ], 409);
            }

            DB::beginTransaction();

            // Create new remote access session
            $session = RemoteAccessSession::create([
                'rvm_id' => $id,
                'admin_id' => $request->admin_id,
                'start_time' => now(),
                'status' => 'active',
                'ip_address' => $request->ip_address,
                'port' => $request->port ?? 5001
            ]);

            // Update RVM status to maintenance
            $rvm->update([
                'status' => 'maintenance',
                'updated_at' => now()
            ]);

            DB::commit();

            return response()->json([
                'success' => true,
                'message' => 'Remote access session started successfully',
                'data' => [
                    'session_id' => $session->id,
                    'rvm_id' => $rvm->id,
                    'rvm_name' => $rvm->name,
                    'status' => 'maintenance',
                    'start_time' => $session->start_time,
                    'admin_id' => $session->admin_id
                ]
            ]);

        } catch (\Exception $e) {
            DB::rollBack();
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to start remote access session: ' . $e->getMessage()
            ], 500);
        }
    }

    public function stop(Request $request, $id)
    {
        $validator = Validator::make($request->all(), [
            'admin_id' => 'required|exists:users,id',
            'reason' => 'nullable|string|max:255'
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            
            // Find active session
            $session = RemoteAccessSession::where('rvm_id', $id)
                ->where('admin_id', $request->admin_id)
                ->where('status', 'active')
                ->whereNull('end_time')
                ->first();

            if (!$session) {
                return response()->json([
                    'success' => false,
                    'message' => 'No active remote access session found'
                ], 404);
            }

            DB::beginTransaction();

            // End the session
            $session->update([
                'end_time' => now(),
                'status' => 'completed',
                'reason' => $request->reason ?? 'Session completed'
            ]);

            // Update RVM status back to active
            $rvm->update([
                'status' => 'active',
                'updated_at' => now()
            ]);

            DB::commit();

            return response()->json([
                'success' => true,
                'message' => 'Remote access session ended successfully',
                'data' => [
                    'session_id' => $session->id,
                    'rvm_id' => $rvm->id,
                    'rvm_name' => $rvm->name,
                    'status' => 'active',
                    'duration' => $session->duration,
                    'end_time' => $session->end_time
                ]
            ]);

        } catch (\Exception $e) {
            DB::rollBack();
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to end remote access session: ' . $e->getMessage()
            ], 500);
        }
    }

    public function status($id)
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            
            // Get active session
            $activeSession = RemoteAccessSession::where('rvm_id', $id)
                ->where('status', 'active')
                ->whereNull('end_time')
                ->with('admin')
                ->first();

            // Get recent sessions (last 10)
            $recentSessions = RemoteAccessSession::where('rvm_id', $id)
                ->with('admin')
                ->orderBy('start_time', 'desc')
                ->limit(10)
                ->get();

            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvm->id,
                    'rvm_name' => $rvm->name,
                    'current_status' => $rvm->status,
                    'active_session' => $activeSession ? [
                        'session_id' => $activeSession->id,
                        'admin_id' => $activeSession->admin_id,
                        'admin_name' => $activeSession->admin->name,
                        'start_time' => $activeSession->start_time,
                        'duration' => $activeSession->duration,
                        'ip_address' => $activeSession->ip_address,
                        'port' => $activeSession->port
                    ] : null,
                    'recent_sessions' => $recentSessions->map(function ($session) {
                        return [
                            'session_id' => $session->id,
                            'admin_name' => $session->admin->name,
                            'start_time' => $session->start_time,
                            'end_time' => $session->end_time,
                            'duration' => $session->duration,
                            'status' => $session->status,
                            'reason' => $session->reason
                        ];
                    })
                ]
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get remote access status: ' . $e->getMessage()
            ], 500);
        }
    }

    public function history($id)
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            
            $sessions = RemoteAccessSession::where('rvm_id', $id)
                ->with('admin')
                ->orderBy('start_time', 'desc')
                ->paginate(20);

            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvm->id,
                    'rvm_name' => $rvm->name,
                    'sessions' => $sessions->items(),
                    'pagination' => [
                        'current_page' => $sessions->currentPage(),
                        'last_page' => $sessions->lastPage(),
                        'per_page' => $sessions->perPage(),
                        'total' => $sessions->total()
                    ]
                ]
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get remote access history: ' . $e->getMessage()
            ], 500);
        }
    }
}
```

### **4. Routes Implementation**

#### **A. Add Routes to web.php:**
```php
// File: routes/web.php

// Add to existing admin/rvm route group
Route::prefix('admin/rvm')->name('admin.rvm.')->group(function () {
    // ... existing routes ...
    
    // Remote Access Routes
    Route::post('/{id}/remote-access/start', [RemoteAccessController::class, 'start'])->name('remote-access.start');
    Route::post('/{id}/remote-access/stop', [RemoteAccessController::class, 'stop'])->name('remote-access.stop');
    Route::get('/{id}/remote-access/status', [RemoteAccessController::class, 'status'])->name('remote-access.status');
    Route::get('/{id}/remote-access/history', [RemoteAccessController::class, 'history'])->name('remote-access.history');
});
```

### **5. Frontend JavaScript Implementation**

#### **A. Remote Access Functions:**
```javascript
// File: public/js/admin/dashboard/remote-access.js

function startRemoteAccess(rvmId) {
    const adminId = getCurrentAdminId(); // Get current admin ID
    
    if (!adminId) {
        alert('❌ Admin ID not found. Please login again.');
        return;
    }
    
    // Show confirmation dialog
    if (!confirm(`Start remote access for RVM ${rvmId}?\n\nThis will change RVM status to "maintenance".`)) {
        return;
    }
    
    // Show loading state
    const button = document.querySelector(`[data-rvm-id="${rvmId}"] .remote-access-btn`);
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
    button.disabled = true;
    
    fetch(`/admin/rvm/${rvmId}/remote-access/start`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({
            admin_id: adminId,
            ip_address: getClientIP(), // Get client IP
            port: 5001
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`✅ Remote access started successfully!\n\nSession ID: ${data.data.session_id}\nRVM Status: ${data.data.status}`);
            
            // Update UI
            updateRVMStatus(rvmId, 'maintenance');
            updateRemoteAccessButton(rvmId, 'stop');
            
            // Refresh page after 2 seconds
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            alert(`❌ Failed to start remote access:\n${data.message}`);
        }
    })
    .catch(error => {
        console.error('Remote access start error:', error);
        alert('❌ Network error: ' + error.message);
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function stopRemoteAccess(rvmId) {
    const adminId = getCurrentAdminId();
    
    if (!adminId) {
        alert('❌ Admin ID not found. Please login again.');
        return;
    }
    
    // Show confirmation dialog
    if (!confirm(`Stop remote access for RVM ${rvmId}?\n\nThis will change RVM status back to "active".`)) {
        return;
    }
    
    // Show loading state
    const button = document.querySelector(`[data-rvm-id="${rvmId}"] .remote-access-btn`);
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Stopping...';
    button.disabled = true;
    
    fetch(`/admin/rvm/${rvmId}/remote-access/stop`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({
            admin_id: adminId,
            reason: 'Manual stop from dashboard'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`✅ Remote access stopped successfully!\n\nDuration: ${data.data.duration} seconds\nRVM Status: ${data.data.status}`);
            
            // Update UI
            updateRVMStatus(rvmId, 'active');
            updateRemoteAccessButton(rvmId, 'start');
            
            // Refresh page after 2 seconds
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            alert(`❌ Failed to stop remote access:\n${data.message}`);
        }
    })
    .catch(error => {
        console.error('Remote access stop error:', error);
        alert('❌ Network error: ' + error.message);
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function getRemoteAccessStatus(rvmId) {
    fetch(`/admin/rvm/${rvmId}/remote-access/status`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const status = data.data;
                
                if (status.active_session) {
                    // Show active session info
                    showRemoteAccessModal(status);
                } else {
                    // No active session
                    console.log('No active remote access session');
                }
            }
        })
        .catch(error => {
            console.error('Remote access status error:', error);
        });
}

function updateRemoteAccessButton(rvmId, action) {
    const button = document.querySelector(`[data-rvm-id="${rvmId}"] .remote-access-btn`);
    
    if (action === 'start') {
        button.innerHTML = '<i class="fas fa-desktop"></i> Remote Access';
        button.onclick = () => startRemoteAccess(rvmId);
        button.className = 'btn btn-outline-primary btn-sm remote-access-btn';
    } else if (action === 'stop') {
        button.innerHTML = '<i class="fas fa-stop"></i> Stop Access';
        button.onclick = () => stopRemoteAccess(rvmId);
        button.className = 'btn btn-outline-danger btn-sm remote-access-btn';
    }
}

function getCurrentAdminId() {
    // Get admin ID from meta tag or user data
    const adminIdMeta = document.querySelector('meta[name="admin-id"]');
    return adminIdMeta ? adminIdMeta.getAttribute('content') : null;
}

function getClientIP() {
    // Get client IP (this would need to be implemented based on your setup)
    return '192.168.1.100'; // Placeholder
}
```

---

## **🧪 TESTING**

### **1. Test Cases:**

#### **A. Start Remote Access:**
```bash
curl -X POST http://localhost:8001/admin/rvm/1/remote-access/start \
  -H "Content-Type: application/json" \
  -H "X-CSRF-TOKEN: your_token_here" \
  -d '{
    "admin_id": 1,
    "ip_address": "192.168.1.100",
    "port": 5001
  }'
```

#### **B. Stop Remote Access:**
```bash
curl -X POST http://localhost:8001/admin/rvm/1/remote-access/stop \
  -H "Content-Type: application/json" \
  -H "X-CSRF-TOKEN: your_token_here" \
  -d '{
    "admin_id": 1,
    "reason": "Session completed"
  }'
```

#### **C. Get Status:**
```bash
curl -X GET http://localhost:8001/admin/rvm/1/remote-access/status \
  -H "X-CSRF-TOKEN: your_token_here"
```

### **2. Database Tests:**
- Verify session creation
- Verify RVM status update
- Verify session completion
- Verify RVM status restoration

---

## **📋 CHECKLIST**

- [ ] Create database migration for remote_access_sessions table
- [ ] Create RemoteAccessSession model
- [ ] Implement RemoteAccessController
- [ ] Add routes for remote access endpoints
- [ ] Implement frontend JavaScript functions
- [ ] Test start remote access functionality
- [ ] Test stop remote access functionality
- [ ] Test status checking functionality
- [ ] Test session history functionality
- [ ] Verify RVM status changes
- [ ] Test error handling
- [ ] Test concurrent session prevention

---

## **📝 NOTES**

- Remote access automatically changes RVM status to "maintenance"
- Only one active session per RVM is allowed
- Session duration is calculated automatically
- Admin ID is required for all operations
- RVM status is restored to "active" when session ends

---

**Status**: 🔄 **IN PROGRESS**  
**Next**: Update UI untuk Remote Access Functionality

