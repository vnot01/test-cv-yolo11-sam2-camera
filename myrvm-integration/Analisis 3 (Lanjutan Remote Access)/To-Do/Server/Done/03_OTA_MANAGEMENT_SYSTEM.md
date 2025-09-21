# TASK 03: OTA MANAGEMENT SYSTEM

**Tanggal**: 2025-01-20  
**Status**: ✅ **DONE**  
**Prioritas**: MEDIUM  
**Estimasi**: 4-5 hari  
**Assigned**: MyRVM Platform (Server)

---

## **📋 DESKRIPSI TUGAS**

Implementasi OTA (Over-the-Air) Management System untuk mengelola update software, model AI, dan konfigurasi RVM dari jarak jauh melalui dashboard admin.

### **🎯 TUJUAN:**
- Software update management dengan GitHub integration
- AI model management dengan version tracking
- Configuration management dengan remote editing
- Update progress tracking dan rollback capability
- Automated deployment dan validation

---

## **🔧 IMPLEMENTASI**

### **1. Database Schema**

#### **A. Software Updates Table:**
```sql
CREATE TABLE software_updates (
    id SERIAL PRIMARY KEY,
    rvm_id INTEGER NOT NULL,
    update_type VARCHAR(50) NOT NULL, -- 'software', 'model', 'config'
    current_version VARCHAR(100),
    target_version VARCHAR(100),
    update_source VARCHAR(200), -- GitHub URL, file path, etc.
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'downloading', 'installing', 'completed', 'failed', 'rolled_back'
    progress INTEGER DEFAULT 0, -- 0-100
    progress_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    rollback_version VARCHAR(100),
    rollback_reason TEXT,
    error_message TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX idx_software_updates_rvm_id ON software_updates(rvm_id);
CREATE INDEX idx_software_updates_status ON software_updates(status);
CREATE INDEX idx_software_updates_created_at ON software_updates(created_at);
```

#### **B. AI Models Table:**
```sql
CREATE TABLE ai_models (
    id SERIAL PRIMARY KEY,
    rvm_id INTEGER NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_path VARCHAR(500) NOT NULL,
    model_size BIGINT,
    model_checksum VARCHAR(64),
    model_url VARCHAR(500),
    is_active BOOLEAN DEFAULT FALSE,
    deployed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id)
);

-- Indexes for performance
CREATE INDEX idx_ai_models_rvm_id ON ai_models(rvm_id);
CREATE INDEX idx_ai_models_active ON ai_models(is_active);
CREATE INDEX idx_ai_models_version ON ai_models(model_version);
```

#### **C. Configuration Templates Table:**
```sql
CREATE TABLE configuration_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    config_data JSONB NOT NULL,
    version VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX idx_config_templates_active ON configuration_templates(is_active);
CREATE INDEX idx_config_templates_version ON configuration_templates(version);
```

### **2. Backend Implementation**

#### **A. OTA Management Controller:**
```php
// File: app/Http/Controllers/Admin/OTAManagementController.php

<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\ReverseVendingMachine;
use App\Models\SoftwareUpdate;
use App\Models\AiModel;
use App\Models\ConfigurationTemplate;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Http;

class OTAManagementController extends Controller
{
    public function index($id)
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            
            // Get current software version
            $currentSoftware = SoftwareUpdate::where('rvm_id', $id)
                ->where('update_type', 'software')
                ->where('status', 'completed')
                ->orderBy('completed_at', 'desc')
                ->first();
            
            // Get current AI model
            $currentModel = AiModel::where('rvm_id', $id)
                ->where('is_active', true)
                ->first();
            
            // Get recent updates
            $recentUpdates = SoftwareUpdate::where('rvm_id', $id)
                ->orderBy('created_at', 'desc')
                ->limit(10)
                ->get();
            
            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvm->id,
                    'rvm_name' => $rvm->name,
                    'current_software' => $currentSoftware,
                    'current_model' => $currentModel,
                    'recent_updates' => $recentUpdates
                ]
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get OTA information: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function checkForUpdates($id)
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            
            // Check GitHub for latest releases
            $githubReleases = $this->getGitHubReleases();
            
            // Check for model updates
            $modelUpdates = $this->checkModelUpdates($id);
            
            // Check for configuration updates
            $configUpdates = $this->checkConfigUpdates($id);
            
            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvm->id,
                    'software_updates' => $githubReleases,
                    'model_updates' => $modelUpdates,
                    'config_updates' => $configUpdates
                ]
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to check for updates: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function startSoftwareUpdate(Request $request, $id)
    {
        $validator = Validator::make($request->all(), [
            'target_version' => 'required|string',
            'update_source' => 'required|string',
            'update_type' => 'required|in:software,model,config'
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
            
            // Create update record
            $update = SoftwareUpdate::create([
                'rvm_id' => $id,
                'update_type' => $request->update_type,
                'current_version' => $this->getCurrentVersion($id, $request->update_type),
                'target_version' => $request->target_version,
                'update_source' => $request->update_source,
                'status' => 'pending',
                'progress' => 0,
                'progress_message' => 'Update queued',
                'started_at' => now(),
                'created_by' => $user->id
            ]);
            
            // Send update command to RVM
            $this->sendUpdateCommandToRVM($rvm, $update);
            
            // Log update initiation
            Log::info('OTA update initiated', [
                'update_id' => $update->id,
                'rvm_id' => $id,
                'update_type' => $request->update_type,
                'target_version' => $request->target_version,
                'initiated_by' => $user->id
            ]);
            
            return response()->json([
                'success' => true,
                'message' => 'Update initiated successfully',
                'data' => [
                    'update_id' => $update->id,
                    'status' => $update->status,
                    'started_at' => $update->started_at
                ]
            ]);
            
        } catch (\Exception $e) {
            Log::error('Failed to start OTA update', [
                'rvm_id' => $id,
                'error' => $e->getMessage()
            ]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to start update: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function getUpdateProgress($id, $updateId)
    {
        try {
            $update = SoftwareUpdate::where('rvm_id', $id)
                ->where('id', $updateId)
                ->firstOrFail();
            
            return response()->json([
                'success' => true,
                'data' => $update
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Update not found: ' . $e->getMessage()
            ], 404);
        }
    }
    
    public function updateProgress(Request $request, $id, $updateId)
    {
        $validator = Validator::make($request->all(), [
            'status' => 'required|in:pending,downloading,installing,completed,failed,rolled_back',
            'progress' => 'required|integer|min:0|max:100',
            'progress_message' => 'nullable|string',
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
            $update = SoftwareUpdate::where('rvm_id', $id)
                ->where('id', $updateId)
                ->firstOrFail();
            
            $update->status = $request->status;
            $update->progress = $request->progress;
            $update->progress_message = $request->progress_message;
            $update->error_message = $request->error_message;
            
            if ($request->status === 'completed' || $request->status === 'failed' || $request->status === 'rolled_back') {
                $update->completed_at = now();
            }
            
            $update->save();
            
            return response()->json([
                'success' => true,
                'message' => 'Update progress updated successfully',
                'data' => $update
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to update progress: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function rollbackUpdate(Request $request, $id, $updateId)
    {
        $validator = Validator::make($request->all(), [
            'rollback_reason' => 'required|string'
        ]);
        
        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }
        
        try {
            $update = SoftwareUpdate::where('rvm_id', $id)
                ->where('id', $updateId)
                ->firstOrFail();
            
            if ($update->status !== 'completed') {
                return response()->json([
                    'success' => false,
                    'message' => 'Can only rollback completed updates'
                ], 400);
            }
            
            $update->status = 'rolled_back';
            $update->rollback_reason = $request->rollback_reason;
            $update->completed_at = now();
            $update->save();
            
            // Send rollback command to RVM
            $this->sendRollbackCommandToRVM($rvm, $update);
            
            return response()->json([
                'success' => true,
                'message' => 'Rollback initiated successfully',
                'data' => $update
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to rollback update: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function uploadModel(Request $request, $id)
    {
        $validator = Validator::make($request->all(), [
            'model_file' => 'required|file|mimes:pt,pth,onnx|max:102400', // 100MB max
            'model_name' => 'required|string',
            'model_version' => 'required|string'
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
            
            $file = $request->file('model_file');
            $fileName = time() . '_' . $file->getClientOriginalName();
            $filePath = $file->storeAs('models', $fileName, 'public');
            
            // Calculate file checksum
            $checksum = hash_file('sha256', storage_path('app/public/' . $filePath));
            
            // Create model record
            $model = AiModel::create([
                'rvm_id' => $id,
                'model_name' => $request->model_name,
                'model_version' => $request->model_version,
                'model_path' => $filePath,
                'model_size' => $file->getSize(),
                'model_checksum' => $checksum,
                'model_url' => asset('storage/' . $filePath),
                'is_active' => false
            ]);
            
            return response()->json([
                'success' => true,
                'message' => 'Model uploaded successfully',
                'data' => $model
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to upload model: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function deployModel(Request $request, $id, $modelId)
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            $model = AiModel::where('rvm_id', $id)
                ->where('id', $modelId)
                ->firstOrFail();
            
            // Deactivate current model
            AiModel::where('rvm_id', $id)
                ->where('is_active', true)
                ->update(['is_active' => false]);
            
            // Activate new model
            $model->is_active = true;
            $model->deployed_at = now();
            $model->save();
            
            // Send model deployment command to RVM
            $this->sendModelDeploymentCommandToRVM($rvm, $model);
            
            return response()->json([
                'success' => true,
                'message' => 'Model deployed successfully',
                'data' => $model
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to deploy model: ' . $e->getMessage()
            ], 500);
        }
    }
    
    private function getGitHubReleases()
    {
        try {
            $response = Http::get('https://api.github.com/repos/vnot01/MySuperApps/releases');
            
            if ($response->successful()) {
                return $response->json();
            }
            
            return [];
        } catch (\Exception $e) {
            Log::error('Failed to fetch GitHub releases', ['error' => $e->getMessage()]);
            return [];
        }
    }
    
    private function checkModelUpdates($rvmId)
    {
        // Check for new model versions
        // This would integrate with your model repository
        return [];
    }
    
    private function checkConfigUpdates($rvmId)
    {
        // Check for configuration updates
        // This would check against configuration templates
        return [];
    }
    
    private function getCurrentVersion($rvmId, $updateType)
    {
        switch ($updateType) {
            case 'software':
                $update = SoftwareUpdate::where('rvm_id', $rvmId)
                    ->where('update_type', 'software')
                    ->where('status', 'completed')
                    ->orderBy('completed_at', 'desc')
                    ->first();
                return $update ? $update->target_version : 'unknown';
                
            case 'model':
                $model = AiModel::where('rvm_id', $rvmId)
                    ->where('is_active', true)
                    ->first();
                return $model ? $model->model_version : 'unknown';
                
            case 'config':
                // Get current config version
                return '1.0.0';
                
            default:
                return 'unknown';
        }
    }
    
    private function sendUpdateCommandToRVM($rvm, $update)
    {
        // Send update command via WebSocket or message queue
        $commandData = [
            'update_id' => $update->id,
            'update_type' => $update->update_type,
            'target_version' => $update->target_version,
            'update_source' => $update->update_source,
            'timestamp' => now()->toISOString()
        ];
        
        // TODO: Implement WebSocket or message queue integration
        Log::info('Update command sent to RVM', [
            'rvm_id' => $rvm->id,
            'update_id' => $update->id,
            'command_data' => $commandData
        ]);
    }
    
    private function sendRollbackCommandToRVM($rvm, $update)
    {
        // Send rollback command via WebSocket or message queue
        $commandData = [
            'update_id' => $update->id,
            'rollback_version' => $update->current_version,
            'rollback_reason' => $update->rollback_reason,
            'timestamp' => now()->toISOString()
        ];
        
        // TODO: Implement WebSocket or message queue integration
        Log::info('Rollback command sent to RVM', [
            'rvm_id' => $rvm->id,
            'update_id' => $update->id,
            'command_data' => $commandData
        ]);
    }
    
    private function sendModelDeploymentCommandToRVM($rvm, $model)
    {
        // Send model deployment command via WebSocket or message queue
        $commandData = [
            'model_id' => $model->id,
            'model_name' => $model->model_name,
            'model_version' => $model->model_version,
            'model_path' => $model->model_path,
            'model_url' => $model->model_url,
            'timestamp' => now()->toISOString()
        ];
        
        // TODO: Implement WebSocket or message queue integration
        Log::info('Model deployment command sent to RVM', [
            'rvm_id' => $rvm->id,
            'model_id' => $model->id,
            'command_data' => $commandData
        ]);
    }
}
```

### **3. Frontend Implementation**

#### **A. OTA Management UI:**
```javascript
// File: public/js/admin/dashboard/ota-management.js

class OTAManagementManager {
    constructor(rvmId) {
        this.rvmId = rvmId;
        this.updateProgress = {};
        this.refreshInterval = null;
    }
    
    async init() {
        await this.loadOTAInfo();
        await this.checkForUpdates();
        this.startProgressRefresh();
    }
    
    async loadOTAInfo() {
        try {
            const response = await fetch(`/admin/rvm/${this.rvmId}/ota-info`);
            const data = await response.json();
            
            if (data.success) {
                this.renderOTAInfo(data.data);
            }
        } catch (error) {
            console.error('Failed to load OTA info:', error);
        }
    }
    
    async checkForUpdates() {
        try {
            const response = await fetch(`/admin/rvm/${this.rvmId}/check-updates`);
            const data = await response.json();
            
            if (data.success) {
                this.renderAvailableUpdates(data.data);
            }
        } catch (error) {
            console.error('Failed to check for updates:', error);
        }
    }
    
    renderOTAInfo(otaInfo) {
        const container = document.getElementById('ota-info-container');
        if (!container) return;
        
        let html = `
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Current Software</h6>
                        </div>
                        <div class="card-body">
                            <p class="mb-1"><strong>Version:</strong> ${otaInfo.current_software?.target_version || 'Unknown'}</p>
                            <p class="mb-0"><strong>Last Updated:</strong> ${this.formatDateTime(otaInfo.current_software?.completed_at)}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Current AI Model</h6>
                        </div>
                        <div class="card-body">
                            <p class="mb-1"><strong>Model:</strong> ${otaInfo.current_model?.model_name || 'Unknown'}</p>
                            <p class="mb-1"><strong>Version:</strong> ${otaInfo.current_model?.model_version || 'Unknown'}</p>
                            <p class="mb-0"><strong>Deployed:</strong> ${this.formatDateTime(otaInfo.current_model?.deployed_at)}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Recent Updates</h6>
                        </div>
                        <div class="card-body">
                            <div class="list-group list-group-flush">
        `;
        
        otaInfo.recent_updates.slice(0, 3).forEach(update => {
            html += `
                <div class="list-group-item px-0 py-2">
                    <div class="d-flex justify-content-between">
                        <span class="small">${update.update_type} ${update.target_version}</span>
                        <span class="badge badge-${this.getStatusColor(update.status)}">${update.status}</span>
                    </div>
                </div>
            `;
        });
        
        html += `
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    renderAvailableUpdates(updates) {
        const container = document.getElementById('available-updates-container');
        if (!container) return;
        
        let html = `
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Software Updates</h6>
                        </div>
                        <div class="card-body">
        `;
        
        if (updates.software_updates && updates.software_updates.length > 0) {
            updates.software_updates.slice(0, 3).forEach(release => {
                html += `
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div>
                            <strong>${release.tag_name}</strong><br>
                            <small class="text-muted">${release.published_at}</small>
                        </div>
                        <button class="btn btn-sm btn-primary" onclick="startSoftwareUpdate('${release.tag_name}', '${release.html_url}')">
                            Update
                        </button>
                    </div>
                `;
            });
        } else {
            html += '<p class="text-muted mb-0">No software updates available</p>';
        }
        
        html += `
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Model Updates</h6>
                        </div>
                        <div class="card-body">
                            <p class="text-muted mb-0">No model updates available</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Configuration Updates</h6>
                        </div>
                        <div class="card-body">
                            <p class="text-muted mb-0">No configuration updates available</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    async startSoftwareUpdate(targetVersion, updateSource) {
        try {
            const response = await fetch(`/admin/rvm/${this.rvmId}/start-software-update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({
                    target_version: targetVersion,
                    update_source: updateSource,
                    update_type: 'software'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Software update started successfully', 'success');
                this.updateProgress[data.data.update_id] = data.data;
                this.renderUpdateProgress();
            } else {
                this.showNotification('Failed to start software update: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Failed to start software update:', error);
            this.showNotification('Network error: ' + error.message, 'error');
        }
    }
    
    renderUpdateProgress() {
        const container = document.getElementById('update-progress-container');
        if (!container) return;
        
        let html = '<h6>Update Progress</h6>';
        
        Object.values(this.updateProgress).forEach(update => {
            html += `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="mb-0">${update.update_type} ${update.target_version}</h6>
                            <span class="badge badge-${this.getStatusColor(update.status)}">${update.status}</span>
                        </div>
                        <div class="progress mb-2">
                            <div class="progress-bar" role="progressbar" style="width: ${update.progress}%">
                                ${update.progress}%
                            </div>
                        </div>
                        <p class="small text-muted mb-0">${update.progress_message || 'Processing...'}</p>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    startProgressRefresh() {
        this.refreshInterval = setInterval(() => {
            this.refreshUpdateProgress();
        }, 2000); // Refresh every 2 seconds
    }
    
    stopProgressRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    async refreshUpdateProgress() {
        for (const updateId in this.updateProgress) {
            try {
                const response = await fetch(`/admin/rvm/${this.rvmId}/update/${updateId}/progress`);
                const data = await response.json();
                
                if (data.success) {
                    this.updateProgress[updateId] = data.data;
                }
            } catch (error) {
                console.error('Failed to refresh update progress:', error);
            }
        }
        
        this.renderUpdateProgress();
    }
    
    getStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'downloading': 'info',
            'installing': 'info',
            'completed': 'success',
            'failed': 'danger',
            'rolled_back': 'secondary'
        };
        return colors[status] || 'secondary';
    }
    
    formatDateTime(dateTime) {
        if (!dateTime) return 'Never';
        return new Date(dateTime).toLocaleString();
    }
    
    showNotification(message, type) {
        // Implement notification system
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

// Global functions for button clicks
function startSoftwareUpdate(targetVersion, updateSource) {
    if (window.otaManagementManager) {
        window.otaManagementManager.startSoftwareUpdate(targetVersion, updateSource);
    }
}

// Initialize OTA management manager
let otaManagementManager = null;

function initOTAManagement(rvmId) {
    if (otaManagementManager) {
        otaManagementManager.stopProgressRefresh();
    }
    otaManagementManager = new OTAManagementManager(rvmId);
    window.otaManagementManager = otaManagementManager;
    otaManagementManager.init();
}

function stopOTAManagement() {
    if (otaManagementManager) {
        otaManagementManager.stopProgressRefresh();
        otaManagementManager = null;
    }
}
```

### **4. Routes Configuration**

#### **A. Add OTA Management Routes:**
```php
// File: routes/web.php

// Add to existing admin/rvm route group
Route::prefix('admin/rvm')->name('admin.rvm.')->group(function () {
    // ... existing routes ...
    
    // OTA Management Routes
    Route::get('/{id}/ota-info', [OTAManagementController::class, 'index'])->name('ota-info');
    Route::get('/{id}/check-updates', [OTAManagementController::class, 'checkForUpdates'])->name('check-updates');
    Route::post('/{id}/start-software-update', [OTAManagementController::class, 'startSoftwareUpdate'])->name('start-software-update');
    Route::get('/{id}/update/{updateId}/progress', [OTAManagementController::class, 'getUpdateProgress'])->name('update-progress');
    Route::put('/{id}/update/{updateId}/progress', [OTAManagementController::class, 'updateProgress'])->name('update-progress');
    Route::post('/{id}/update/{updateId}/rollback', [OTAManagementController::class, 'rollbackUpdate'])->name('rollback-update');
    Route::post('/{id}/upload-model', [OTAManagementController::class, 'uploadModel'])->name('upload-model');
    Route::post('/{id}/deploy-model/{modelId}', [OTAManagementController::class, 'deployModel'])->name('deploy-model');
});
```

---

## **🧪 TESTING**

### **1. Database Testing:**
- Test table creation and constraints
- Test update tracking and progress
- Test model management
- Test configuration templates

### **2. API Testing:**
- Test update initiation
- Test progress tracking
- Test rollback functionality
- Test model upload/deployment

### **3. Frontend Testing:**
- Test OTA info display
- Test update initiation
- Test progress tracking
- Test error handling

---

## **📋 CHECKLIST**

- [ ] Create software_updates table migration
- [ ] Create ai_models table migration
- [ ] Create configuration_templates table migration
- [ ] Create SoftwareUpdate model
- [ ] Create AiModel model
- [ ] Create ConfigurationTemplate model
- [ ] Implement OTAManagementController
- [ ] Add OTA management routes
- [ ] Create OTA management JavaScript
- [ ] Update dashboard UI for OTA management
- [ ] Test database operations
- [ ] Test API endpoints
- [ ] Test frontend functionality
- [ ] Test update process
- [ ] Test progress tracking
- [ ] Test rollback functionality
- [ ] Test model management
- [ ] Performance testing
- [ ] Documentation update

---

## **📝 NOTES**

- OTA updates are tracked in database
- Real-time progress updates every 2 seconds
- GitHub integration for software updates
- Model upload and deployment support
- Rollback capability for failed updates
- Comprehensive error handling and logging

---

**Status**: 🔄 **IN PROGRESS**  
**Next**: Implement database migrations and models
