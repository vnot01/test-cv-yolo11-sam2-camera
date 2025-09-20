# TASK 06: MODEL CREATION UNTUK SEMUA ENTITIES

**Tanggal**: 2025-01-20  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 1-2 jam  

---

## **📋 DESKRIPSI TUGAS**

Membuat model classes untuk semua entities yang diperlukan berdasarkan database schema.

### **🎯 TUJUAN:**
- Create model classes untuk semua entities
- Implementasi relationships dan methods
- Support untuk semua fitur yang diperlukan

---

## **🔧 IMPLEMENTASI**

### **1. Remote Access Session Model**

#### **A. Model File:**
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

    public function getFormattedDurationAttribute(): string
    {
        $duration = $this->duration;
        $hours = floor($duration / 3600);
        $minutes = floor(($duration % 3600) / 60);
        $seconds = $duration % 60;
        
        if ($hours > 0) {
            return sprintf('%dh %dm %ds', $hours, $minutes, $seconds);
        } elseif ($minutes > 0) {
            return sprintf('%dm %ds', $minutes, $seconds);
        } else {
            return sprintf('%ds', $seconds);
        }
    }

    public function scopeActive($query)
    {
        return $query->where('status', 'active')->whereNull('end_time');
    }

    public function scopeCompleted($query)
    {
        return $query->where('status', 'completed');
    }
}
```

### **2. RVM Configuration Model**

#### **A. Model File:**
```php
// File: app/Models/RvmConfiguration.php

<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class RvmConfiguration extends Model
{
    use HasFactory;

    protected $fillable = [
        'rvm_id',
        'config_key',
        'config_value',
        'description',
        'config_type',
        'is_required'
    ];

    protected $casts = [
        'is_required' => 'boolean'
    ];

    public function rvm(): BelongsTo
    {
        return $this->belongsTo(ReverseVendingMachine::class, 'rvm_id');
    }

    public function getTypedValueAttribute()
    {
        switch ($this->config_type) {
            case 'integer':
                return (int) $this->config_value;
            case 'boolean':
                return filter_var($this->config_value, FILTER_VALIDATE_BOOLEAN);
            case 'json':
                return json_decode($this->config_value, true);
            case 'float':
                return (float) $this->config_value;
            default:
                return $this->config_value;
        }
    }

    public function setTypedValue($value)
    {
        switch ($this->config_type) {
            case 'json':
                $this->config_value = json_encode($value);
                break;
            case 'boolean':
                $this->config_value = $value ? 'true' : 'false';
                break;
            default:
                $this->config_value = (string) $value;
        }
    }

    public function scopeByKey($query, $key)
    {
        return $query->where('config_key', $key);
    }

    public function scopeByType($query, $type)
    {
        return $query->where('config_type', $type);
    }

    public function scopeRequired($query)
    {
        return $query->where('is_required', true);
    }
}
```

### **3. Timezone Sync Log Model**

#### **A. Model File:**
```php
// File: app/Models/TimezoneSyncLog.php

<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class TimezoneSyncLog extends Model
{
    use HasFactory;

    protected $fillable = [
        'device_id',
        'device_type',
        'timezone',
        'country',
        'city',
        'ip_address',
        'sync_method',
        'sync_timestamp',
        'status',
        'details'
    ];

    protected $casts = [
        'sync_timestamp' => 'datetime',
        'details' => 'array'
    ];

    public function scopeByDevice($query, $deviceId, $deviceType = 'rvm')
    {
        return $query->where('device_id', $deviceId)->where('device_type', $deviceType);
    }

    public function scopeByStatus($query, $status)
    {
        return $query->where('status', $status);
    }

    public function scopeByMethod($query, $method)
    {
        return $query->where('sync_method', $method);
    }

    public function scopeRecent($query, $days = 7)
    {
        return $query->where('sync_timestamp', '>=', now()->subDays($days));
    }

    public function getFormattedTimestampAttribute(): string
    {
        return $this->sync_timestamp->format('Y-m-d H:i:s');
    }

    public function getStatusBadgeAttribute(): string
    {
        $badges = [
            'success' => 'success',
            'failed' => 'danger',
            'partial' => 'warning'
        ];

        return $badges[$this->status] ?? 'secondary';
    }
}
```

### **4. Backup Log Model**

#### **A. Model File:**
```php
// File: app/Models/BackupLog.php

<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class BackupLog extends Model
{
    use HasFactory;

    protected $fillable = [
        'rvm_id',
        'backup_type',
        'file_path',
        'file_size',
        'upload_status',
        'minio_path',
        'error_message',
        'started_at',
        'completed_at'
    ];

    protected $casts = [
        'started_at' => 'datetime',
        'completed_at' => 'datetime'
    ];

    public function rvm(): BelongsTo
    {
        return $this->belongsTo(ReverseVendingMachine::class, 'rvm_id');
    }

    public function getDurationAttribute(): ?int
    {
        if ($this->completed_at) {
            return $this->started_at->diffInSeconds($this->completed_at);
        }
        
        return null;
    }

    public function getFormattedFileSizeAttribute(): string
    {
        if (!$this->file_size) {
            return 'Unknown';
        }

        $bytes = $this->file_size;
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        
        for ($i = 0; $bytes > 1024 && $i < count($units) - 1; $i++) {
            $bytes /= 1024;
        }
        
        return round($bytes, 2) . ' ' . $units[$i];
    }

    public function getStatusBadgeAttribute(): string
    {
        $badges = [
            'pending' => 'secondary',
            'uploading' => 'warning',
            'completed' => 'success',
            'failed' => 'danger'
        ];

        return $badges[$this->upload_status] ?? 'secondary';
    }

    public function scopeByType($query, $type)
    {
        return $query->where('backup_type', $type);
    }

    public function scopeByStatus($query, $status)
    {
        return $query->where('upload_status', $status);
    }

    public function scopeRecent($query, $days = 30)
    {
        return $query->where('started_at', '>=', now()->subDays($days));
    }

    public function isCompleted(): bool
    {
        return $this->upload_status === 'completed';
    }

    public function isFailed(): bool
    {
        return $this->upload_status === 'failed';
    }

    public function isInProgress(): bool
    {
        return in_array($this->upload_status, ['pending', 'uploading']);
    }
}
```

### **5. System Metric Model**

#### **A. Model File:**
```php
// File: app/Models/SystemMetric.php

<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class SystemMetric extends Model
{
    use HasFactory;

    protected $fillable = [
        'rvm_id',
        'cpu_usage',
        'memory_usage',
        'disk_usage',
        'gpu_usage',
        'temperature',
        'network_latency',
        'uptime',
        'additional_metrics',
        'recorded_at'
    ];

    protected $casts = [
        'cpu_usage' => 'decimal:2',
        'memory_usage' => 'decimal:2',
        'disk_usage' => 'decimal:2',
        'gpu_usage' => 'decimal:2',
        'temperature' => 'decimal:2',
        'network_latency' => 'integer',
        'uptime' => 'integer',
        'additional_metrics' => 'array',
        'recorded_at' => 'datetime'
    ];

    public function rvm(): BelongsTo
    {
        return $this->belongsTo(ReverseVendingMachine::class, 'rvm_id');
    }

    public function getFormattedUptimeAttribute(): string
    {
        if (!$this->uptime) {
            return 'Unknown';
        }

        $uptime = $this->uptime;
        $days = floor($uptime / 86400);
        $hours = floor(($uptime % 86400) / 3600);
        $minutes = floor(($uptime % 3600) / 60);
        
        if ($days > 0) {
            return sprintf('%dd %dh %dm', $days, $hours, $minutes);
        } elseif ($hours > 0) {
            return sprintf('%dh %dm', $hours, $minutes);
        } else {
            return sprintf('%dm', $minutes);
        }
    }

    public function getHealthStatusAttribute(): string
    {
        $issues = [];
        
        if ($this->cpu_usage > 90) {
            $issues[] = 'High CPU';
        }
        if ($this->memory_usage > 90) {
            $issues[] = 'High Memory';
        }
        if ($this->disk_usage > 90) {
            $issues[] = 'High Disk';
        }
        if ($this->temperature > 80) {
            $issues[] = 'High Temperature';
        }
        if ($this->network_latency > 1000) {
            $issues[] = 'High Latency';
        }
        
        if (empty($issues)) {
            return 'healthy';
        } elseif (count($issues) <= 2) {
            return 'warning';
        } else {
            return 'critical';
        }
    }

    public function scopeRecent($query, $hours = 24)
    {
        return $query->where('recorded_at', '>=', now()->subHours($hours));
    }

    public function scopeByHealthStatus($query, $status)
    {
        return $query->whereRaw("
            CASE 
                WHEN cpu_usage > 90 OR memory_usage > 90 OR disk_usage > 90 OR temperature > 80 OR network_latency > 1000 THEN 'critical'
                WHEN cpu_usage > 80 OR memory_usage > 80 OR disk_usage > 80 OR temperature > 70 OR network_latency > 500 THEN 'warning'
                ELSE 'healthy'
            END = ?
        ", [$status]);
    }

    public function scopeAverageMetrics($query, $hours = 24)
    {
        return $query->recent($hours)
            ->selectRaw('
                AVG(cpu_usage) as avg_cpu,
                AVG(memory_usage) as avg_memory,
                AVG(disk_usage) as avg_disk,
                AVG(gpu_usage) as avg_gpu,
                AVG(temperature) as avg_temperature,
                AVG(network_latency) as avg_latency
            ');
    }
}
```

### **6. Update Reverse Vending Machine Model**

#### **A. Update Existing Model:**
```php
// File: app/Models/ReverseVendingMachine.php

<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class ReverseVendingMachine extends Model
{
    use HasFactory;

    protected $fillable = [
        'name',
        'location_description',
        'location',
        'address',
        'status',
        'special_status',
        'capacity',
        'api_key',
        'ip_address',
        'port',
        'timezone',
        'timezone_offset',
        'last_timezone_sync',
        'last_ping',
        'connection_status'
    ];

    protected $casts = [
        'capacity' => 'integer',
        'port' => 'integer',
        'last_timezone_sync' => 'datetime',
        'last_ping' => 'datetime'
    ];

    // Existing relationships
    public function timezoneSyncLogs(): HasMany
    {
        return $this->hasMany(TimezoneSyncLog::class, 'device_id')->where('device_type', 'rvm');
    }

    // New relationships
    public function remoteAccessSessions(): HasMany
    {
        return $this->hasMany(RemoteAccessSession::class, 'rvm_id');
    }

    public function configurations(): HasMany
    {
        return $this->hasMany(RvmConfiguration::class, 'rvm_id');
    }

    public function backupLogs(): HasMany
    {
        return $this->hasMany(BackupLog::class, 'rvm_id');
    }

    public function systemMetrics(): HasMany
    {
        return $this->hasMany(SystemMetric::class, 'rvm_id');
    }

    // New methods
    public function getActiveRemoteAccessSession()
    {
        return $this->remoteAccessSessions()->active()->first();
    }

    public function hasActiveRemoteAccess(): bool
    {
        return $this->getActiveRemoteAccessSession() !== null;
    }

    public function getLatestSystemMetrics()
    {
        return $this->systemMetrics()->latest('recorded_at')->first();
    }

    public function getConfiguration($key, $default = null)
    {
        $config = $this->configurations()->where('config_key', $key)->first();
        return $config ? $config->typed_value : $default;
    }

    public function setConfiguration($key, $value, $type = 'string', $description = null)
    {
        return $this->configurations()->updateOrCreate(
            ['config_key' => $key],
            [
                'config_value' => $value,
                'config_type' => $type,
                'description' => $description
            ]
        );
    }

    public function getLatestBackupLog($type = null)
    {
        $query = $this->backupLogs()->latest('started_at');
        if ($type) {
            $query->where('backup_type', $type);
        }
        return $query->first();
    }

    public function scopeWithActiveRemoteAccess($query)
    {
        return $query->whereHas('remoteAccessSessions', function ($q) {
            $q->active();
        });
    }

    public function scopeWithoutActiveRemoteAccess($query)
    {
        return $query->whereDoesntHave('remoteAccessSessions', function ($q) {
            $q->active();
        });
    }

    public function scopeByConnectionStatus($query, $status)
    {
        return $query->where('connection_status', $status);
    }

    public function scopeByTimezone($query, $timezone)
    {
        return $query->where('timezone', $timezone);
    }
}
```

---

## **🧪 TESTING**

### **1. Model Testing:**

#### **A. Test Model Creation:**
```php
// Test RemoteAccessSession model
$session = RemoteAccessSession::create([
    'rvm_id' => 1,
    'admin_id' => 1,
    'start_time' => now(),
    'status' => 'active',
    'ip_address' => '192.168.1.100',
    'port' => 5001
]);

// Test RvmConfiguration model
$config = RvmConfiguration::create([
    'rvm_id' => 1,
    'config_key' => 'confidence_threshold',
    'config_value' => '0.8',
    'config_type' => 'float',
    'description' => 'AI confidence threshold'
]);

// Test TimezoneSyncLog model
$log = TimezoneSyncLog::create([
    'device_id' => '1',
    'device_type' => 'rvm',
    'timezone' => 'Asia/Jakarta',
    'country' => 'Indonesia',
    'city' => 'Jakarta',
    'sync_method' => 'automatic',
    'sync_timestamp' => now(),
    'status' => 'success'
]);
```

#### **B. Test Relationships:**
```php
// Test RVM relationships
$rvm = ReverseVendingMachine::find(1);

// Test remote access sessions
$activeSession = $rvm->getActiveRemoteAccessSession();
$hasActiveAccess = $rvm->hasActiveRemoteAccess();

// Test configurations
$threshold = $rvm->getConfiguration('confidence_threshold', 0.5);
$rvm->setConfiguration('max_capacity', 100, 'integer', 'Maximum RVM capacity');

// Test system metrics
$latestMetrics = $rvm->getLatestSystemMetrics();
$healthStatus = $latestMetrics->health_status;

// Test backup logs
$latestBackup = $rvm->getLatestBackupLog('full');
```

### **2. Query Testing:**

#### **A. Test Scopes:**
```php
// Test RemoteAccessSession scopes
$activeSessions = RemoteAccessSession::active()->get();
$completedSessions = RemoteAccessSession::completed()->get();

// Test RvmConfiguration scopes
$requiredConfigs = RvmConfiguration::required()->get();
$stringConfigs = RvmConfiguration::byType('string')->get();

// Test TimezoneSyncLog scopes
$recentLogs = TimezoneSyncLog::recent(7)->get();
$successLogs = TimezoneSyncLog::byStatus('success')->get();

// Test SystemMetric scopes
$recentMetrics = SystemMetric::recent(24)->get();
$healthyMetrics = SystemMetric::byHealthStatus('healthy')->get();
$avgMetrics = SystemMetric::averageMetrics(24)->first();
```

---

## **📋 CHECKLIST**

- [ ] Create RemoteAccessSession model
- [ ] Create RvmConfiguration model
- [ ] Create TimezoneSyncLog model
- [ ] Create BackupLog model
- [ ] Create SystemMetric model
- [ ] Update ReverseVendingMachine model
- [ ] Test model creation
- [ ] Test relationships
- [ ] Test scopes
- [ ] Test methods
- [ ] Validate data types
- [ ] Check fillable fields

---

## **📝 NOTES**

- All models use proper relationships
- Scopes are implemented for common queries
- Accessor methods provide formatted data
- Proper casting for data types
- Comprehensive fillable fields

---

**Status**: ✅ **COMPLETED**  
**Completion Date**: 2025-01-20  
**Next**: Basic API Endpoints Implementation
