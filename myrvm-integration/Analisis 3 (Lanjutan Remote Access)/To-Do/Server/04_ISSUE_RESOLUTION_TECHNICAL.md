# TASK 04: ISSUE RESOLUTION TECHNICAL

**Tanggal**: 2025-09-21  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 1-2 hari  
**Assigned**: MyRVM Platform (Server)

---

## **📋 DESKRIPSI TUGAS**

Resolusi teknis untuk Issue 1 (API Route 404) di server-side MyRVM Platform, implementasi endpoint yang diperlukan untuk Analisis 3 integration.

### **🎯 TUJUAN:**
- Implement API endpoints yang missing untuk RVM configuration
- Ensure seamless integration dengan RVM-Jetson components
- Provide comprehensive error handling dan validation
- Support dynamic configuration management

---

## **🔧 IMPLEMENTASI TEKNIS**

### **1. API Routes Implementation**

#### **A. RVM Configuration Routes:**
```php
// File: routes/api.php

// Add to existing API routes
Route::prefix('api/v2/rvms')->group(function () {
    // RVM Configuration Management
    Route::get('/{id}/config', [RVMConfigController::class, 'getConfig'])->name('rvm.config.get');
    Route::patch('/{id}/config', [RVMConfigController::class, 'updateConfig'])->name('rvm.config.update');
    Route::get('/{id}/config/confidence-threshold', [RVMConfigController::class, 'getConfidenceThreshold'])->name('rvm.config.confidence.get');
    Route::patch('/{id}/config/confidence-threshold', [RVMConfigController::class, 'updateConfidenceThreshold'])->name('rvm.config.confidence.update');
    
    // Enhanced Metrics Endpoints
    Route::post('/{id}/store-metrics', [EnhancedMetricsController::class, 'storeMetrics'])->name('rvm.metrics.store');
    Route::get('/{id}/enhanced-metrics', [EnhancedMetricsController::class, 'getComprehensiveMetrics'])->name('rvm.metrics.get');
    
    // Remote Commands Endpoints
    Route::get('/{id}/remote-commands', [RemoteCommandsController::class, 'index'])->name('rvm.commands.index');
    Route::post('/{id}/execute-command', [RemoteCommandsController::class, 'executeCommand'])->name('rvm.commands.execute');
    Route::get('/{id}/command/{commandId}/status', [RemoteCommandsController::class, 'getCommandStatus'])->name('rvm.commands.status');
    Route::put('/{id}/command/{commandId}/status', [RemoteCommandsController::class, 'updateCommandStatus'])->name('rvm.commands.status.update');
});
```

### **2. RVM Configuration Controller**

#### **A. RVMConfigController Implementation:**
```php
// File: app/Http/Controllers/Api/RVMConfigController.php

<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\ReverseVendingMachine;
use App\Models\RVMConfiguration;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Facades\Log;

class RVMConfigController extends Controller
{
    public function getConfig($id)
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            
            // Get current configuration
            $config = RVMConfiguration::where('rvm_id', $id)->first();
            
            if (!$config) {
                // Create default configuration if not exists
                $config = $this->createDefaultConfig($id);
            }
            
            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvm->id,
                    'rvm_name' => $rvm->name,
                    'configuration' => $config->configuration,
                    'confidence_threshold' => $config->confidence_threshold,
                    'last_updated' => $config->updated_at,
                    'version' => $config->version
                ]
            ]);
            
        } catch (\Exception $e) {
            Log::error('Failed to get RVM config', [
                'rvm_id' => $id,
                'error' => $e->getMessage()
            ]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to get RVM configuration: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function updateConfig(Request $request, $id)
    {
        $validator = Validator::make($request->all(), [
            'configuration' => 'required|array',
            'version' => 'nullable|string|max:50'
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
            
            // Get or create configuration
            $config = RVMConfiguration::where('rvm_id', $id)->first();
            
            if (!$config) {
                $config = new RVMConfiguration();
                $config->rvm_id = $id;
            }
            
            // Update configuration
            $config->configuration = $request->configuration;
            $config->version = $request->version ?? '1.0';
            $config->save();
            
            // Log configuration update
            Log::info('RVM configuration updated', [
                'rvm_id' => $id,
                'version' => $config->version,
                'updated_by' => auth()->id() ?? 'system'
            ]);
            
            return response()->json([
                'success' => true,
                'message' => 'Configuration updated successfully',
                'data' => [
                    'rvm_id' => $rvm->id,
                    'configuration' => $config->configuration,
                    'version' => $config->version,
                    'updated_at' => $config->updated_at
                ]
            ]);
            
        } catch (\Exception $e) {
            Log::error('Failed to update RVM config', [
                'rvm_id' => $id,
                'error' => $e->getMessage()
            ]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to update RVM configuration: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function getConfidenceThreshold($id)
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            
            $config = RVMConfiguration::where('rvm_id', $id)->first();
            
            if (!$config) {
                $config = $this->createDefaultConfig($id);
            }
            
            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvm->id,
                    'confidence_threshold' => $config->confidence_threshold,
                    'last_updated' => $config->updated_at
                ]
            ]);
            
        } catch (\Exception $e) {
            Log::error('Failed to get confidence threshold', [
                'rvm_id' => $id,
                'error' => $e->getMessage()
            ]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to get confidence threshold: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function updateConfidenceThreshold(Request $request, $id)
    {
        $validator = Validator::make($request->all(), [
            'confidence_threshold' => 'required|numeric|min:0|max:1'
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
            
            $config = RVMConfiguration::where('rvm_id', $id)->first();
            
            if (!$config) {
                $config = $this->createDefaultConfig($id);
            }
            
            $oldThreshold = $config->confidence_threshold;
            $config->confidence_threshold = $request->confidence_threshold;
            $config->save();
            
            // Log threshold update
            Log::info('RVM confidence threshold updated', [
                'rvm_id' => $id,
                'old_threshold' => $oldThreshold,
                'new_threshold' => $config->confidence_threshold,
                'updated_by' => auth()->id() ?? 'system'
            ]);
            
            return response()->json([
                'success' => true,
                'message' => 'Confidence threshold updated successfully',
                'data' => [
                    'rvm_id' => $rvm->id,
                    'confidence_threshold' => $config->confidence_threshold,
                    'updated_at' => $config->updated_at
                ]
            ]);
            
        } catch (\Exception $e) {
            Log::error('Failed to update confidence threshold', [
                'rvm_id' => $id,
                'error' => $e->getMessage()
            ]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to update confidence threshold: ' . $e->getMessage()
            ], 500);
        }
    }
    
    private function createDefaultConfig($rvmId)
    {
        $defaultConfig = [
            'camera_index' => 0,
            'detection_interval' => 3,
            'batch_size' => 6,
            'max_processing_queue' => 15,
            'memory_threshold' => 0.7,
            'log_level' => 'INFO',
            'auto_restart' => true,
            'maintenance_mode' => false
        ];
        
        $config = new RVMConfiguration();
        $config->rvm_id = $rvmId;
        $config->configuration = $defaultConfig;
        $config->confidence_threshold = 0.5;
        $config->version = '1.0';
        $config->save();
        
        Log::info('Default RVM configuration created', [
            'rvm_id' => $rvmId
        ]);
        
        return $config;
    }
}
```

### **3. Database Schema**

#### **A. RVM Configuration Table:**
```sql
-- File: database/migrations/xxxx_xx_xx_create_rvm_configurations_table.php

CREATE TABLE rvm_configurations (
    id SERIAL PRIMARY KEY,
    rvm_id INTEGER NOT NULL,
    configuration JSONB NOT NULL,
    confidence_threshold DECIMAL(3,2) DEFAULT 0.5,
    version VARCHAR(50) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_rvm_configurations_rvm_id ON rvm_configurations(rvm_id);
CREATE INDEX idx_rvm_configurations_version ON rvm_configurations(version);

-- Add unique constraint
ALTER TABLE rvm_configurations ADD CONSTRAINT unique_rvm_configuration UNIQUE (rvm_id);
```

#### **B. RVM Configuration Model:**
```php
// File: app/Models/RVMConfiguration.php

<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class RVMConfiguration extends Model
{
    protected $table = 'rvm_configurations';
    
    protected $fillable = [
        'rvm_id',
        'configuration',
        'confidence_threshold',
        'version'
    ];
    
    protected $casts = [
        'configuration' => 'array',
        'confidence_threshold' => 'decimal:2'
    ];
    
    public function rvm(): BelongsTo
    {
        return $this->belongsTo(ReverseVendingMachine::class, 'rvm_id');
    }
    
    public function getConfigurationAttribute($value)
    {
        return json_decode($value, true);
    }
    
    public function setConfigurationAttribute($value)
    {
        $this->attributes['configuration'] = json_encode($value);
    }
}
```

### **4. Enhanced Metrics Integration**

#### **A. Enhanced Metrics Controller Update:**
```php
// File: app/Http/Controllers/Admin/EnhancedMetricsController.php (Update)

public function storeMetrics(Request $request, $id)
{
    $validator = Validator::make($request->all(), [
        'system_metrics' => 'nullable|array',
        'application_metrics' => 'nullable|array',
        'network_information' => 'nullable|array'
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
        
        // Store system metrics
        if ($request->has('system_metrics')) {
            SystemMetric::create([
                'rvm_id' => $id,
                'cpu_usage' => $request->system_metrics['cpu_usage'] ?? null,
                'memory_usage' => $request->system_metrics['memory_usage'] ?? null,
                'disk_usage' => $request->system_metrics['disk_usage'] ?? null,
                'gpu_usage' => $request->system_metrics['gpu_usage'] ?? null,
                'temperature' => $request->system_metrics['temperature'] ?? null,
                'gpu_temperature' => $request->system_metrics['gpu_temperature'] ?? null,
                'disk_read_speed' => $request->system_metrics['disk_read_speed'] ?? null,
                'disk_write_speed' => $request->system_metrics['disk_write_speed'] ?? null,
                'network_upload_speed' => $request->system_metrics['network_upload_speed'] ?? null,
                'network_download_speed' => $request->system_metrics['network_download_speed'] ?? null,
                'memory_available' => $request->system_metrics['memory_available'] ?? null,
                'disk_available' => $request->system_metrics['disk_available'] ?? null,
                'process_count' => $request->system_metrics['process_count'] ?? null,
                'load_average' => $request->system_metrics['load_average'] ?? null,
                'network_latency' => $request->system_metrics['network_latency'] ?? null,
                'uptime' => $request->system_metrics['uptime'] ?? null,
                'recorded_at' => now()
            ]);
        }
        
        // Store application metrics
        if ($request->has('application_metrics')) {
            ApplicationMetric::create([
                'rvm_id' => $id,
                'software_version' => $request->application_metrics['software_version'] ?? null,
                'ai_model_version' => $request->application_metrics['ai_model_version'] ?? null,
                'ai_model_path' => $request->application_metrics['ai_model_path'] ?? null,
                'uptime_seconds' => $request->application_metrics['uptime_seconds'] ?? null,
                'deposit_count_since_restart' => $request->application_metrics['deposit_count_since_restart'] ?? null,
                'last_deposit_time' => $request->application_metrics['last_deposit_time'] ?? null,
                'error_count' => $request->application_metrics['error_count'] ?? 0,
                'warning_count' => $request->application_metrics['warning_count'] ?? 0,
                'recorded_at' => now()
            ]);
        }
        
        // Store network information
        if ($request->has('network_information')) {
            NetworkInformation::create([
                'rvm_id' => $id,
                'local_ip' => $request->network_information['local_ip'] ?? null,
                'virtual_ip' => $request->network_information['virtual_ip'] ?? null,
                'gateway_ip' => $request->network_information['gateway_ip'] ?? null,
                'dns_servers' => $request->network_information['dns_servers'] ?? null,
                'network_interface' => $request->network_information['network_interface'] ?? null,
                'connection_type' => $request->network_information['connection_type'] ?? null,
                'signal_strength' => $request->network_information['signal_strength'] ?? null,
                'last_network_check' => $request->network_information['last_network_check'] ?? null,
                'recorded_at' => now()
            ]);
        }
        
        return response()->json([
            'success' => true,
            'message' => 'Metrics stored successfully'
        ]);
        
    } catch (\Exception $e) {
        Log::error('Failed to store metrics', [
            'rvm_id' => $id,
            'error' => $e->getMessage()
        ]);
        
        return response()->json([
            'success' => false,
            'message' => 'Failed to store metrics: ' . $e->getMessage()
        ], 500);
    }
}
```

### **5. WebSocket Integration**

#### **A. WebSocket Routes for Real-time Communication:**
```php
// File: routes/websocket.php

use BeyondCode\LaravelWebSockets\Facades\WebSocketRouter;

WebSocketRouter::webSocket('/ws/rvm/{id}', \App\WebSockets\RVMWebSocketHandler::class);
```

#### **B. RVM WebSocket Handler:**
```php
// File: app/WebSockets/RVMWebSocketHandler.php

<?php

namespace App\WebSockets;

use BeyondCode\LaravelWebSockets\WebSockets\WebSocketHandler;
use Ratchet\ConnectionInterface;
use Ratchet\WebSocket\MessageComponentInterface;

class RVMWebSocketHandler extends WebSocketHandler implements MessageComponentInterface
{
    public function onOpen(ConnectionInterface $connection)
    {
        $connection->send(json_encode([
            'type' => 'connection_established',
            'message' => 'Connected to RVM WebSocket',
            'timestamp' => now()->toISOString()
        ]));
    }
    
    public function onMessage(ConnectionInterface $connection, $message)
    {
        $data = json_decode($message, true);
        
        if (!$data || !isset($data['type'])) {
            $connection->send(json_encode([
                'type' => 'error',
                'message' => 'Invalid message format'
            ]));
            return;
        }
        
        switch ($data['type']) {
            case 'heartbeat':
                $this->handleHeartbeat($connection, $data);
                break;
            case 'command_status_update':
                $this->handleCommandStatusUpdate($connection, $data);
                break;
            default:
                $connection->send(json_encode([
                    'type' => 'error',
                    'message' => 'Unknown message type'
                ]));
        }
    }
    
    private function handleHeartbeat(ConnectionInterface $connection, $data)
    {
        $connection->send(json_encode([
            'type' => 'heartbeat_response',
            'timestamp' => now()->toISOString(),
            'status' => 'online'
        ]));
    }
    
    private function handleCommandStatusUpdate(ConnectionInterface $connection, $data)
    {
        // Update command status in database
        // Broadcast to admin dashboard
        $this->broadcastToAdmins($data);
    }
    
    private function broadcastToAdmins($data)
    {
        // Broadcast command status update to admin dashboard
        // This would integrate with your broadcasting system
    }
}
```

---

## **🧪 TESTING**

### **1. API Endpoints Testing:**
- Test RVM configuration endpoints
- Test confidence threshold endpoints
- Test enhanced metrics endpoints
- Test remote commands endpoints

### **2. Database Testing:**
- Test RVM configuration table creation
- Test data insertion and retrieval
- Test foreign key constraints
- Test indexes and performance

### **3. WebSocket Testing:**
- Test WebSocket connection establishment
- Test real-time communication
- Test command status updates
- Test heartbeat mechanism

---

## **📋 CHECKLIST**

- [ ] Create RVM configuration table migration
- [ ] Create RVMConfiguration model
- [ ] Implement RVMConfigController
- [ ] Add API routes for RVM configuration
- [ ] Update EnhancedMetricsController
- [ ] Implement WebSocket handler
- [ ] Add WebSocket routes
- [ ] Test API endpoints
- [ ] Test database operations
- [ ] Test WebSocket functionality
- [ ] Test error handling
- [ ] Performance testing
- [ ] Documentation update

---

## **📝 NOTES**

- API endpoints resolve Issue 1 (API Route 404)
- Enhanced error handling and validation
- Real-time communication via WebSocket
- Comprehensive logging for debugging
- Performance optimized with proper indexing

---

**Status**: 🔄 **IN PROGRESS**  
**Next**: Implement database migration and controller
