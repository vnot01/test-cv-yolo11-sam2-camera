# TASK 01: ENHANCED MONITORING SYSTEM

**Tanggal**: 2025-01-20  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 3-4 hari  
**Assigned**: MyRVM Platform (Server)

---

## **📋 DESKRIPSI TUGAS**

Implementasi Enhanced Monitoring System untuk Remote Access Dashboard yang mencakup comprehensive hardware metrics, application metrics, dan network information.

### **🎯 TUJUAN:**
- Extend existing system metrics collection
- Add hardware-specific metrics (CPU, GPU, RAM, Disk, Temperature)
- Add application metrics (software version, AI model version, uptime)
- Add network information (local IP, virtual IP, connectivity status)
- Implement real-time metrics streaming

---

## **🔧 IMPLEMENTASI**

### **1. Database Schema Extensions**

#### **A. Enhanced System Metrics Table:**
```sql
-- Extend existing system_metrics table
ALTER TABLE system_metrics ADD COLUMN IF NOT EXISTS gpu_temperature DECIMAL(5,2);
ALTER TABLE system_metrics ADD COLUMN IF NOT EXISTS disk_read_speed INTEGER;
ALTER TABLE system_metrics ADD COLUMN IF NOT EXISTS disk_write_speed INTEGER;
ALTER TABLE system_metrics ADD COLUMN IF NOT EXISTS network_upload_speed INTEGER;
ALTER TABLE system_metrics ADD COLUMN IF NOT EXISTS network_download_speed INTEGER;
ALTER TABLE system_metrics ADD COLUMN IF NOT EXISTS memory_available BIGINT;
ALTER TABLE system_metrics ADD COLUMN IF NOT EXISTS disk_available BIGINT;
ALTER TABLE system_metrics ADD COLUMN IF NOT EXISTS process_count INTEGER;
ALTER TABLE system_metrics ADD COLUMN IF NOT EXISTS load_average DECIMAL(5,2);
```

#### **B. Application Metrics Table:**
```sql
CREATE TABLE application_metrics (
    id SERIAL PRIMARY KEY,
    rvm_id INTEGER NOT NULL,
    software_version VARCHAR(50),
    ai_model_version VARCHAR(50),
    ai_model_path VARCHAR(500),
    uptime_seconds INTEGER,
    deposit_count_since_restart INTEGER,
    last_deposit_time TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id)
);
```

#### **C. Network Information Table:**
```sql
CREATE TABLE network_information (
    id SERIAL PRIMARY KEY,
    rvm_id INTEGER NOT NULL,
    local_ip VARCHAR(45),
    virtual_ip VARCHAR(45),
    gateway_ip VARCHAR(45),
    dns_servers TEXT,
    network_interface VARCHAR(50),
    connection_type VARCHAR(20),
    signal_strength INTEGER,
    last_network_check TIMESTAMP,
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id)
);
```

### **2. Backend API Extensions**

#### **A. Enhanced Metrics Controller:**
```php
// File: app/Http/Controllers/Admin/EnhancedMetricsController.php

<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\ReverseVendingMachine;
use App\Models\SystemMetric;
use App\Models\ApplicationMetric;
use App\Models\NetworkInformation;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class EnhancedMetricsController extends Controller
{
    public function getComprehensiveMetrics($id)
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($id);
            
            // Get latest system metrics
            $systemMetrics = SystemMetric::where('rvm_id', $id)
                ->orderBy('recorded_at', 'desc')
                ->first();
            
            // Get latest application metrics
            $applicationMetrics = ApplicationMetric::where('rvm_id', $id)
                ->orderBy('recorded_at', 'desc')
                ->first();
            
            // Get latest network information
            $networkInfo = NetworkInformation::where('rvm_id', $id)
                ->orderBy('recorded_at', 'desc')
                ->first();
            
            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvm->id,
                    'rvm_name' => $rvm->name,
                    'system_metrics' => $systemMetrics,
                    'application_metrics' => $applicationMetrics,
                    'network_information' => $networkInfo,
                    'last_updated' => now()
                ]
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get comprehensive metrics: ' . $e->getMessage()
            ], 500);
        }
    }
    
    public function getMetricsHistory($id, Request $request)
    {
        $validator = Validator::make($request->all(), [
            'days' => 'nullable|integer|min:1|max:30',
            'metric_type' => 'nullable|in:system,application,network'
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
            $days = $request->days ?? 7;
            $metricType = $request->metric_type ?? 'system';
            
            $startDate = now()->subDays($days);
            
            $metrics = [];
            switch ($metricType) {
                case 'system':
                    $metrics = SystemMetric::where('rvm_id', $id)
                        ->where('recorded_at', '>=', $startDate)
                        ->orderBy('recorded_at', 'desc')
                        ->get();
                    break;
                case 'application':
                    $metrics = ApplicationMetric::where('rvm_id', $id)
                        ->where('recorded_at', '>=', $startDate)
                        ->orderBy('recorded_at', 'desc')
                        ->get();
                    break;
                case 'network':
                    $metrics = NetworkInformation::where('rvm_id', $id)
                        ->where('recorded_at', '>=', $startDate)
                        ->orderBy('recorded_at', 'desc')
                        ->get();
                    break;
            }
            
            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvm->id,
                    'metric_type' => $metricType,
                    'days' => $days,
                    'metrics' => $metrics,
                    'total_records' => $metrics->count()
                ]
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get metrics history: ' . $e->getMessage()
            ], 500);
        }
    }
    
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
            return response()->json([
                'success' => false,
                'message' => 'Failed to store metrics: ' . $e->getMessage()
            ], 500);
        }
    }
}
```

### **3. Frontend Dashboard Extensions**

#### **A. Enhanced Metrics Display:**
```javascript
// File: public/js/admin/dashboard/enhanced-metrics.js

class EnhancedMetricsManager {
    constructor(rvmId) {
        this.rvmId = rvmId;
        this.refreshInterval = null;
        this.isActive = false;
    }
    
    start() {
        this.isActive = true;
        this.loadMetrics();
        this.refreshInterval = setInterval(() => {
            if (this.isActive) {
                this.loadMetrics();
            }
        }, 30000); // Refresh every 30 seconds
    }
    
    stop() {
        this.isActive = false;
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    async loadMetrics() {
        try {
            const response = await fetch(`/admin/rvm/${this.rvmId}/enhanced-metrics`);
            const data = await response.json();
            
            if (data.success) {
                this.updateMetricsDisplay(data.data);
            }
        } catch (error) {
            console.error('Failed to load enhanced metrics:', error);
        }
    }
    
    updateMetricsDisplay(metrics) {
        // Update system metrics
        if (metrics.system_metrics) {
            this.updateSystemMetrics(metrics.system_metrics);
        }
        
        // Update application metrics
        if (metrics.application_metrics) {
            this.updateApplicationMetrics(metrics.application_metrics);
        }
        
        // Update network information
        if (metrics.network_information) {
            this.updateNetworkInformation(metrics.network_information);
        }
    }
    
    updateSystemMetrics(systemMetrics) {
        // CPU Usage
        const cpuElement = document.getElementById('cpu-usage');
        if (cpuElement) {
            cpuElement.textContent = `${systemMetrics.cpu_usage || 0}%`;
            cpuElement.className = this.getUsageClass(systemMetrics.cpu_usage);
        }
        
        // Memory Usage
        const memoryElement = document.getElementById('memory-usage');
        if (memoryElement) {
            memoryElement.textContent = `${systemMetrics.memory_usage || 0}%`;
            memoryElement.className = this.getUsageClass(systemMetrics.memory_usage);
        }
        
        // GPU Usage
        const gpuElement = document.getElementById('gpu-usage');
        if (gpuElement) {
            gpuElement.textContent = `${systemMetrics.gpu_usage || 0}%`;
            gpuElement.className = this.getUsageClass(systemMetrics.gpu_usage);
        }
        
        // Temperature
        const tempElement = document.getElementById('temperature');
        if (tempElement) {
            tempElement.textContent = `${systemMetrics.temperature || 0}°C`;
            tempElement.className = this.getTemperatureClass(systemMetrics.temperature);
        }
        
        // Disk Usage
        const diskElement = document.getElementById('disk-usage');
        if (diskElement) {
            diskElement.textContent = `${systemMetrics.disk_usage || 0}%`;
            diskElement.className = this.getUsageClass(systemMetrics.disk_usage);
        }
    }
    
    updateApplicationMetrics(appMetrics) {
        // Software Version
        const versionElement = document.getElementById('software-version');
        if (versionElement) {
            versionElement.textContent = appMetrics.software_version || 'Unknown';
        }
        
        // AI Model Version
        const modelElement = document.getElementById('ai-model-version');
        if (modelElement) {
            modelElement.textContent = appMetrics.ai_model_version || 'Unknown';
        }
        
        // Uptime
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement) {
            uptimeElement.textContent = this.formatUptime(appMetrics.uptime_seconds || 0);
        }
        
        // Deposit Count
        const depositElement = document.getElementById('deposit-count');
        if (depositElement) {
            depositElement.textContent = appMetrics.deposit_count_since_restart || 0;
        }
    }
    
    updateNetworkInformation(networkInfo) {
        // Local IP
        const localIpElement = document.getElementById('local-ip');
        if (localIpElement) {
            localIpElement.textContent = networkInfo.local_ip || 'Unknown';
        }
        
        // Virtual IP
        const virtualIpElement = document.getElementById('virtual-ip');
        if (virtualIpElement) {
            virtualIpElement.textContent = networkInfo.virtual_ip || 'Unknown';
        }
        
        // Connection Type
        const connectionElement = document.getElementById('connection-type');
        if (connectionElement) {
            connectionElement.textContent = networkInfo.connection_type || 'Unknown';
        }
        
        // Signal Strength
        const signalElement = document.getElementById('signal-strength');
        if (signalElement) {
            signalElement.textContent = networkInfo.signal_strength ? `${networkInfo.signal_strength}%` : 'Unknown';
        }
    }
    
    getUsageClass(usage) {
        if (usage >= 90) return 'text-danger';
        if (usage >= 70) return 'text-warning';
        return 'text-success';
    }
    
    getTemperatureClass(temperature) {
        if (temperature >= 80) return 'text-danger';
        if (temperature >= 60) return 'text-warning';
        return 'text-success';
    }
    
    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }
}

// Initialize enhanced metrics manager
let enhancedMetricsManager = null;

function initEnhancedMetrics(rvmId) {
    if (enhancedMetricsManager) {
        enhancedMetricsManager.stop();
    }
    enhancedMetricsManager = new EnhancedMetricsManager(rvmId);
    enhancedMetricsManager.start();
}

function stopEnhancedMetrics() {
    if (enhancedMetricsManager) {
        enhancedMetricsManager.stop();
        enhancedMetricsManager = null;
    }
}
```

### **4. Routes Configuration**

#### **A. Add Enhanced Metrics Routes:**
```php
// File: routes/web.php

// Add to existing admin/rvm route group
Route::prefix('admin/rvm')->name('admin.rvm.')->group(function () {
    // ... existing routes ...
    
    // Enhanced Metrics Routes
    Route::get('/{id}/enhanced-metrics', [EnhancedMetricsController::class, 'getComprehensiveMetrics'])->name('enhanced-metrics');
    Route::get('/{id}/metrics-history', [EnhancedMetricsController::class, 'getMetricsHistory'])->name('metrics-history');
    Route::post('/{id}/store-metrics', [EnhancedMetricsController::class, 'storeMetrics'])->name('store-metrics');
});
```

---

## **🧪 TESTING**

### **1. Database Testing:**
- Test table creation and column additions
- Test data insertion and retrieval
- Test foreign key constraints
- Test indexes and performance

### **2. API Testing:**
- Test comprehensive metrics endpoint
- Test metrics history endpoint
- Test metrics storage endpoint
- Test error handling and validation

### **3. Frontend Testing:**
- Test metrics display updates
- Test real-time refresh functionality
- Test responsive design
- Test error handling

---

## **📋 CHECKLIST**

- [ ] Create database migrations for enhanced metrics
- [ ] Create ApplicationMetric model
- [ ] Create NetworkInformation model
- [ ] Implement EnhancedMetricsController
- [ ] Add enhanced metrics routes
- [ ] Create enhanced metrics JavaScript
- [ ] Update dashboard UI for enhanced metrics
- [ ] Test database operations
- [ ] Test API endpoints
- [ ] Test frontend functionality
- [ ] Test real-time updates
- [ ] Test error handling
- [ ] Performance testing
- [ ] Documentation update

---

## **📝 NOTES**

- Enhanced metrics extend existing system metrics
- Real-time updates every 30 seconds
- Comprehensive hardware and application monitoring
- Network information tracking
- Performance optimized with proper indexing
- Error handling and validation included

---

**Status**: 🔄 **IN PROGRESS**  
**Next**: Implement database migrations and models
