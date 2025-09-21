# TASK 02: REMOTE CONTROL COMMANDS

**Tanggal**: 2025-01-20  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 2-3 hari  
**Assigned**: MyRVM Platform (Server)

---

## **📋 DESKRIPSI TUGAS**

Implementasi Remote Control Commands untuk mengontrol RVM dari jarak jauh melalui dashboard admin, termasuk hardware control, process management, dan system commands.

### **🎯 TUJUAN:**
- Implementasi remote control commands untuk RVM
- Hardware control (buka/tutup pintu, tes motor)
- Process management (restart app, reboot system, shutdown)
- System commands (maintenance mode, diagnostics)
- Real-time command execution dan status tracking

---

## **🔧 IMPLEMENTASI**

### **1. Database Schema**

#### **A. Remote Commands Table:**
```sql
CREATE TABLE remote_commands (
    id SERIAL PRIMARY KEY,
    rvm_id INTEGER NOT NULL,
    command_type VARCHAR(50) NOT NULL,
    command_name VARCHAR(100) NOT NULL,
    command_payload JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    executed_by INTEGER,
    executed_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id),
    FOREIGN KEY (executed_by) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX idx_remote_commands_rvm_id ON remote_commands(rvm_id);
CREATE INDEX idx_remote_commands_status ON remote_commands(status);
CREATE INDEX idx_remote_commands_created_at ON remote_commands(created_at);
```

#### **B. Command Types Enum:**
```sql
-- Command types for reference
-- HARDWARE_CONTROL: open_door, close_door, test_motor, test_sensors
-- PROCESS_MANAGEMENT: restart_app, reboot_system, shutdown_system
-- SYSTEM_CONTROL: enter_maintenance, exit_maintenance, update_config
-- DIAGNOSTICS: take_snapshot, get_logs, system_info
```

### **2. Backend Implementation**

#### **A. Remote Commands Controller:**
```php
// File: app/Http/Controllers/Admin/RemoteCommandsController.php

<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\ReverseVendingMachine;
use App\Models\RemoteCommand;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;

class RemoteCommandsController extends Controller
{
    public function index($id)
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            $commands = RemoteCommand::where('rvm_id', $id)
                ->orderBy('created_at', 'desc')
                ->limit(50)
                ->get();
            
            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvm->id,
                    'rvm_name' => $rvm->name,
                    'commands' => $commands
                ]
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get remote commands: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function executeCommand(Request $request, $id)
    {
        $validator = Validator::make($request->all(), [
            'command_type' => 'required|in:HARDWARE_CONTROL,PROCESS_MANAGEMENT,SYSTEM_CONTROL,DIAGNOSTICS',
            'command_name' => 'required|string|max:100',
            'command_payload' => 'nullable|array'
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
            $user = Auth::user();
            
            // Create command record
            $command = RemoteCommand::create([
                'rvm_id' => $id,
                'command_type' => $request->command_type,
                'command_name' => $request->command_name,
                'command_payload' => $request->command_payload ?? [],
                'status' => 'pending',
                'executed_by' => $user->id,
                'executed_at' => now()
            ]);
            
            // Send command to RVM via WebSocket
            $this->sendCommandToRVM($rvm, $command);
            
            // Log command execution
            Log::info('Remote command executed', [
                'command_id' => $command->id,
                'rvm_id' => $id,
                'command_type' => $request->command_type,
                'command_name' => $request->command_name,
                'executed_by' => $user->id
            ]);
            
            return response()->json([
                'success' => true,
                'message' => 'Command sent successfully',
                'data' => [
                    'command_id' => $command->id,
                    'status' => $command->status,
                    'executed_at' => $command->executed_at
                ]
            ]);
            
        } catch (\Exception $e) {
            Log::error('Failed to execute remote command', [
                'rvm_id' => $id,
                'error' => $e->getMessage()
            ]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to execute command: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function getCommandStatus($id, $commandId)
    {
        try {
            $command = RemoteCommand::where('rvm_id', $id)
                ->where('id', $commandId)
                ->firstOrFail();
            
            return response()->json([
                'success' => true,
                'data' => $command
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Command not found: ' . $e->getMessage()
            ], 404);
        }
    }
    
    public function updateCommandStatus(Request $request, $id, $commandId)
    {
        $validator = Validator::make($request->all(), [
            'status' => 'required|in:pending,executing,completed,failed',
            'result' => 'nullable|array',
            'error_message' => 'nullable|string'
        ]);
        
        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }
        
        try {
            $command = RemoteCommand::where('rvm_id', $id)
                ->where('id', $commandId)
                ->firstOrFail();
            
            $command->status = $request->status;
            $command->result = $request->result;
            $command->error_message = $request->error_message;
            
            if ($request->status === 'completed' || $request->status === 'failed') {
                $command->completed_at = now();
            }
            
            $command->save();
            
            return response()->json([
                'success' => true,
                'message' => 'Command status updated successfully',
                'data' => $command
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to update command status: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function getAvailableCommands($id)
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            
            $availableCommands = [
                'HARDWARE_CONTROL' => [
                    [
                        'name' => 'open_door',
                        'display_name' => 'Buka Pintu Penerimaan',
                        'description' => 'Membuka pintu penerimaan untuk testing dan diagnostik',
                        'icon' => 'fas fa-door-open',
                        'color' => 'success',
                        'requires_confirmation' => true
                    ],
                    [
                        'name' => 'close_door',
                        'display_name' => 'Tutup Pintu Penerimaan',
                        'description' => 'Menutup pintu penerimaan',
                        'icon' => 'fas fa-door-closed',
                        'color' => 'warning',
                        'requires_confirmation' => false
                    ],
                    [
                        'name' => 'test_motor',
                        'display_name' => 'Tes Motor Pemilah',
                        'description' => 'Menjalankan siklus tes motor pemilah',
                        'icon' => 'fas fa-cogs',
                        'color' => 'info',
                        'requires_confirmation' => true
                    ],
                    [
                        'name' => 'test_sensors',
                        'display_name' => 'Tes Sensor',
                        'description' => 'Menjalankan tes semua sensor',
                        'icon' => 'fas fa-microchip',
                        'color' => 'info',
                        'requires_confirmation' => false
                    ]
                ],
                'PROCESS_MANAGEMENT' => [
                    [
                        'name' => 'restart_app',
                        'display_name' => 'Restart Aplikasi',
                        'description' => 'Me-restart aplikasi MyRVM tanpa reboot sistem',
                        'icon' => 'fas fa-redo',
                        'color' => 'warning',
                        'requires_confirmation' => true
                    ],
                    [
                        'name' => 'reboot_system',
                        'display_name' => 'Reboot Sistem',
                        'description' => 'Me-reboot Jetson Orin',
                        'icon' => 'fas fa-power-off',
                        'color' => 'danger',
                        'requires_confirmation' => true
                    ],
                    [
                        'name' => 'shutdown_system',
                        'display_name' => 'Shutdown Sistem',
                        'description' => 'Mematikan Jetson Orin',
                        'icon' => 'fas fa-stop',
                        'color' => 'danger',
                        'requires_confirmation' => true
                    ]
                ],
                'SYSTEM_CONTROL' => [
                    [
                        'name' => 'enter_maintenance',
                        'display_name' => 'Masuk Mode Maintenance',
                        'description' => 'Menghentikan operasi normal dan menampilkan pesan maintenance',
                        'icon' => 'fas fa-tools',
                        'color' => 'warning',
                        'requires_confirmation' => true
                    ],
                    [
                        'name' => 'exit_maintenance',
                        'display_name' => 'Keluar Mode Maintenance',
                        'description' => 'Mengembalikan RVM ke status operasional normal',
                        'icon' => 'fas fa-check-circle',
                        'color' => 'success',
                        'requires_confirmation' => false
                    ],
                    [
                        'name' => 'update_config',
                        'display_name' => 'Update Konfigurasi',
                        'description' => 'Mengupdate konfigurasi RVM',
                        'icon' => 'fas fa-cog',
                        'color' => 'info',
                        'requires_confirmation' => true
                    ]
                ],
                'DIAGNOSTICS' => [
                    [
                        'name' => 'take_snapshot',
                        'display_name' => 'Ambil Snapshot Kamera',
                        'description' => 'Mengambil gambar dari kamera untuk testing',
                        'icon' => 'fas fa-camera',
                        'color' => 'info',
                        'requires_confirmation' => false
                    ],
                    [
                        'name' => 'get_logs',
                        'display_name' => 'Ambil Log Aplikasi',
                        'description' => 'Mengambil log aplikasi terbaru',
                        'icon' => 'fas fa-file-alt',
                        'color' => 'info',
                        'requires_confirmation' => false
                    ],
                    [
                        'name' => 'system_info',
                        'display_name' => 'Informasi Sistem',
                        'description' => 'Mengambil informasi sistem lengkap',
                        'icon' => 'fas fa-info-circle',
                        'color' => 'info',
                        'requires_confirmation' => false
                    ]
                ]
            ];
            
            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvm->id,
                    'rvm_name' => $rvm->name,
                    'available_commands' => $availableCommands
                ]
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get available commands: ' . $e->getMessage()
            ], 500);
        }
    }
    
    private function sendCommandToRVM($rvm, $command)
    {
        // This would integrate with WebSocket or message queue
        // For now, we'll simulate the command sending
        
        $commandData = [
            'command_id' => $command->id,
            'command_type' => $command->command_type,
            'command_name' => $command->command_name,
            'command_payload' => $command->command_payload,
            'timestamp' => now()->toISOString()
        ];
        
        // TODO: Implement actual WebSocket or message queue integration
        // Example: WebSocket::broadcast("rvm.{$rvm->id}", 'remote_command', $commandData);
        
        Log::info('Command sent to RVM', [
            'rvm_id' => $rvm->id,
            'command_id' => $command->id,
            'command_data' => $commandData
        ]);
    }
}
```

### **3. Frontend Implementation**

#### **A. Remote Commands UI:**
```javascript
// File: public/js/admin/dashboard/remote-commands.js

class RemoteCommandsManager {
    constructor(rvmId) {
        this.rvmId = rvmId;
        this.availableCommands = null;
        this.commandHistory = [];
        this.refreshInterval = null;
    }
    
    async init() {
        await this.loadAvailableCommands();
        await this.loadCommandHistory();
        this.startStatusRefresh();
    }
    
    async loadAvailableCommands() {
        try {
            const response = await fetch(`/admin/rvm/${this.rvmId}/available-commands`);
            const data = await response.json();
            
            if (data.success) {
                this.availableCommands = data.data.available_commands;
                this.renderCommandButtons();
            }
        } catch (error) {
            console.error('Failed to load available commands:', error);
        }
    }
    
    async loadCommandHistory() {
        try {
            const response = await fetch(`/admin/rvm/${this.rvmId}/remote-commands`);
            const data = await response.json();
            
            if (data.success) {
                this.commandHistory = data.data.commands;
                this.renderCommandHistory();
            }
        } catch (error) {
            console.error('Failed to load command history:', error);
        }
    }
    
    renderCommandButtons() {
        const container = document.getElementById('remote-commands-container');
        if (!container || !this.availableCommands) return;
        
        let html = '';
        
        Object.entries(this.availableCommands).forEach(([category, commands]) => {
            html += `
                <div class="command-category mb-4">
                    <h6 class="text-muted mb-3">${this.getCategoryDisplayName(category)}</h6>
                    <div class="row">
            `;
            
            commands.forEach(command => {
                html += `
                    <div class="col-md-6 col-lg-4 mb-3">
                        <div class="card command-card">
                            <div class="card-body text-center">
                                <i class="${command.icon} fa-2x text-${command.color} mb-2"></i>
                                <h6 class="card-title">${command.display_name}</h6>
                                <p class="card-text small text-muted">${command.description}</p>
                                <button class="btn btn-${command.color} btn-sm" 
                                        onclick="executeRemoteCommand('${category}', '${command.name}', ${command.requires_confirmation})">
                                    <i class="fas fa-play"></i> Execute
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    renderCommandHistory() {
        const container = document.getElementById('command-history-container');
        if (!container) return;
        
        let html = `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Command</th>
                            <th>Status</th>
                            <th>Executed By</th>
                            <th>Executed At</th>
                            <th>Completed At</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        this.commandHistory.forEach(command => {
            html += `
                <tr>
                    <td>
                        <strong>${command.command_name}</strong><br>
                        <small class="text-muted">${command.command_type}</small>
                    </td>
                    <td>
                        <span class="badge badge-${this.getStatusColor(command.status)}">
                            ${command.status}
                        </span>
                    </td>
                    <td>${command.executed_by || 'System'}</td>
                    <td>${this.formatDateTime(command.executed_at)}</td>
                    <td>${this.formatDateTime(command.completed_at)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-info" 
                                onclick="viewCommandDetails(${command.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    async executeCommand(commandType, commandName, requiresConfirmation = false) {
        if (requiresConfirmation) {
            const confirmed = confirm(`Are you sure you want to execute "${commandName}"?`);
            if (!confirmed) return;
        }
        
        try {
            const response = await fetch(`/admin/rvm/${this.rvmId}/execute-command`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({
                    command_type: commandType,
                    command_name: commandName,
                    command_payload: {}
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Command sent successfully', 'success');
                await this.loadCommandHistory();
            } else {
                this.showNotification('Failed to send command: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Failed to execute command:', error);
            this.showNotification('Network error: ' + error.message, 'error');
        }
    }
    
    startStatusRefresh() {
        this.refreshInterval = setInterval(() => {
            this.loadCommandHistory();
        }, 5000); // Refresh every 5 seconds
    }
    
    stopStatusRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    getCategoryDisplayName(category) {
        const names = {
            'HARDWARE_CONTROL': 'Hardware Control',
            'PROCESS_MANAGEMENT': 'Process Management',
            'SYSTEM_CONTROL': 'System Control',
            'DIAGNOSTICS': 'Diagnostics'
        };
        return names[category] || category;
    }
    
    getStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'executing': 'info',
            'completed': 'success',
            'failed': 'danger'
        };
        return colors[status] || 'secondary';
    }
    
    formatDateTime(dateTime) {
        if (!dateTime) return '-';
        return new Date(dateTime).toLocaleString();
    }
    
    showNotification(message, type) {
        // Implement notification system
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

// Global functions for button clicks
function executeRemoteCommand(commandType, commandName, requiresConfirmation) {
    if (window.remoteCommandsManager) {
        window.remoteCommandsManager.executeCommand(commandType, commandName, requiresConfirmation);
    }
}

function viewCommandDetails(commandId) {
    // Implement command details modal
    console.log('View command details:', commandId);
}

// Initialize remote commands manager
let remoteCommandsManager = null;

function initRemoteCommands(rvmId) {
    if (remoteCommandsManager) {
        remoteCommandsManager.stopStatusRefresh();
    }
    remoteCommandsManager = new RemoteCommandsManager(rvmId);
    window.remoteCommandsManager = remoteCommandsManager;
    remoteCommandsManager.init();
}

function stopRemoteCommands() {
    if (remoteCommandsManager) {
        remoteCommandsManager.stopStatusRefresh();
        remoteCommandsManager = null;
    }
}
```

### **4. Routes Configuration**

#### **A. Add Remote Commands Routes:**
```php
// File: routes/web.php

// Add to existing admin/rvm route group
Route::prefix('admin/rvm')->name('admin.rvm.')->group(function () {
    // ... existing routes ...
    
    // Remote Commands Routes
    Route::get('/{id}/remote-commands', [RemoteCommandsController::class, 'index'])->name('remote-commands');
    Route::get('/{id}/available-commands', [RemoteCommandsController::class, 'getAvailableCommands'])->name('available-commands');
    Route::post('/{id}/execute-command', [RemoteCommandsController::class, 'executeCommand'])->name('execute-command');
    Route::get('/{id}/command/{commandId}/status', [RemoteCommandsController::class, 'getCommandStatus'])->name('command-status');
    Route::put('/{id}/command/{commandId}/status', [RemoteCommandsController::class, 'updateCommandStatus'])->name('update-command-status');
});
```

---

## **🧪 TESTING**

### **1. Database Testing:**
- Test table creation and constraints
- Test command insertion and retrieval
- Test status updates
- Test foreign key relationships

### **2. API Testing:**
- Test command execution endpoint
- Test command status endpoints
- Test available commands endpoint
- Test error handling

### **3. Frontend Testing:**
- Test command button rendering
- Test command execution
- Test status updates
- Test command history display

---

## **📋 CHECKLIST**

- [ ] Create remote_commands table migration
- [ ] Create RemoteCommand model
- [ ] Implement RemoteCommandsController
- [ ] Add remote commands routes
- [ ] Create remote commands JavaScript
- [ ] Update dashboard UI for remote commands
- [ ] Test database operations
- [ ] Test API endpoints
- [ ] Test frontend functionality
- [ ] Test command execution
- [ ] Test status tracking
- [ ] Test error handling
- [ ] Performance testing
- [ ] Documentation update

---

## **📝 NOTES**

- Commands are queued and tracked in database
- Real-time status updates every 5 seconds
- Confirmation required for dangerous commands
- Comprehensive command history
- Error handling and logging included
- WebSocket integration for real-time updates

---

**Status**: 🔄 **IN PROGRESS**  
**Next**: Implement database migration and model
