# TASK 02: CONFIGURATION MANAGEMENT API

**Tanggal**: 2025-09-21  
**Versi**: 1.0.0  
**Status**: 📋 PLANNING  
**Priority**: HIGH  

---

## **🎯 OBJECTIVE**

Membuat Configuration Management API untuk mendukung dynamic configuration loading, real-time configuration updates, dan configuration templates untuk RVM-Jetson.

---

## **📋 REQUIREMENTS**

### **Functional Requirements:**
- **Dynamic Configuration Loading** dari server ke RVM-Jetson
- **Real-time Configuration Updates** tanpa restart
- **Configuration Templates** untuk berbagai jenis RVM
- **Configuration Validation** dan error handling
- **Configuration Versioning** dan rollback
- **Configuration Backup** dan restore
- **Configuration History** tracking

### **Technical Requirements:**
- **RESTful API** endpoints
- **JSON-based** configuration format
- **WebSocket support** untuk real-time updates
- **Configuration encryption** untuk sensitive data
- **Configuration caching** untuk performance
- **Configuration validation** rules

---

## **🔧 IMPLEMENTATION PLAN**

### **1. Configuration Management Endpoints**

#### **A. Get RVM Configuration**
```php
// Endpoint: GET /api/v2/rvms/{id}/config
Route::get('/rvms/{id}/config', [ConfigurationController::class, 'getRvmConfig']);
```

#### **B. Update RVM Configuration**
```php
// Endpoint: PUT /api/v2/rvms/{id}/config
Route::put('/rvms/{id}/config', [ConfigurationController::class, 'updateRvmConfig']);
```

#### **C. Get Configuration Templates**
```php
// Endpoint: GET /api/v2/config/templates
Route::get('/config/templates', [ConfigurationController::class, 'getConfigTemplates']);
```

#### **D. Apply Configuration Template**
```php
// Endpoint: POST /api/v2/rvms/{id}/config/apply-template
Route::post('/rvms/{id}/config/apply-template', [ConfigurationController::class, 'applyConfigTemplate']);
```

#### **E. Configuration History**
```php
// Endpoint: GET /api/v2/rvms/{id}/config/history
Route::get('/rvms/{id}/config/history', [ConfigurationController::class, 'getConfigHistory']);
```

#### **F. Rollback Configuration**
```php
// Endpoint: POST /api/v2/rvms/{id}/config/rollback
Route::post('/rvms/{id}/config/rollback', [ConfigurationController::class, 'rollbackConfig']);
```

---

## **📝 DETAILED IMPLEMENTATION**

### **1. ConfigurationController**

#### **Controller Setup:**
```php
<?php

namespace App\Http\Controllers\Api\V2;

use App\Http\Controllers\Controller;
use App\Models\ReverseVendingMachine;
use App\Models\RvmConfiguration;
use App\Models\ConfigurationTemplate;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Facades\Cache;

class ConfigurationController extends Controller
{
    public function __construct()
    {
        $this->middleware('auth:sanctum');
        $this->middleware('role:super-admin|admin|tenant');
    }

    /**
     * Get RVM configuration
     *
     * @param Request $request
     * @param int $rvmId
     * @return JsonResponse
     */
    public function getRvmConfig(Request $request, int $rvmId): JsonResponse
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($rvmId);
            
            // Check permissions
            if (!$this->canAccessRvm($rvm)) {
                return response()->json([
                    'success' => false,
                    'message' => 'Access denied'
                ], 403);
            }

            // Get current configuration
            $config = RvmConfiguration::where('rvm_id', $rvmId)
                ->where('is_active', true)
                ->first();

            if (!$config) {
                // Return default configuration
                $config = $this->getDefaultConfiguration($rvm);
            }

            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvmId,
                    'configuration' => json_decode($config->configuration, true),
                    'version' => $config->version,
                    'last_updated' => $config->updated_at,
                    'template_id' => $config->template_id,
                ]
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get configuration',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Update RVM configuration
     *
     * @param Request $request
     * @param int $rvmId
     * @return JsonResponse
     */
    public function updateRvmConfig(Request $request, int $rvmId): JsonResponse
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($rvmId);
            
            // Check permissions
            if (!$this->canAccessRvm($rvm)) {
                return response()->json([
                    'success' => false,
                    'message' => 'Access denied'
                ], 403);
            }

            $validator = Validator::make($request->all(), [
                'configuration' => 'required|array',
                'template_id' => 'nullable|integer|exists:configuration_templates,id',
                'version' => 'nullable|string|max:50',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Validation failed',
                    'errors' => $validator->errors()
                ], 422);
            }

            // Validate configuration
            $validationResult = $this->validateConfiguration($request->input('configuration'));
            if (!$validationResult['valid']) {
                return response()->json([
                    'success' => false,
                    'message' => 'Configuration validation failed',
                    'errors' => $validationResult['errors']
                ], 422);
            }

            DB::beginTransaction();

            try {
                // Deactivate current configuration
                RvmConfiguration::where('rvm_id', $rvmId)
                    ->where('is_active', true)
                    ->update(['is_active' => false]);

                // Create new configuration
                $newConfig = RvmConfiguration::create([
                    'rvm_id' => $rvmId,
                    'configuration' => json_encode($request->input('configuration')),
                    'version' => $request->input('version', '1.0.0'),
                    'template_id' => $request->input('template_id'),
                    'is_active' => true,
                    'created_by' => auth()->id(),
                ]);

                // Clear cache
                Cache::forget("rvm_config_{$rvmId}");

                // Send real-time update to RVM
                $this->sendConfigUpdateToRvm($rvm, $newConfig);

                DB::commit();

                return response()->json([
                    'success' => true,
                    'message' => 'Configuration updated successfully',
                    'data' => [
                        'config_id' => $newConfig->id,
                        'version' => $newConfig->version,
                        'updated_at' => $newConfig->updated_at,
                    ]
                ], 200);

            } catch (\Exception $e) {
                DB::rollback();
                throw $e;
            }

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to update configuration',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get configuration templates
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function getConfigTemplates(Request $request): JsonResponse
    {
        try {
            $templates = ConfigurationTemplate::where('is_active', true)
                ->select('id', 'name', 'description', 'template_type', 'configuration', 'created_at')
                ->get();

            $formattedTemplates = $templates->map(function ($template) {
                return [
                    'id' => $template->id,
                    'name' => $template->name,
                    'description' => $template->description,
                    'template_type' => $template->template_type,
                    'configuration' => json_decode($template->configuration, true),
                    'created_at' => $template->created_at,
                ];
            });

            return response()->json([
                'success' => true,
                'data' => $formattedTemplates
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get configuration templates',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Apply configuration template to RVM
     *
     * @param Request $request
     * @param int $rvmId
     * @return JsonResponse
     */
    public function applyConfigTemplate(Request $request, int $rvmId): JsonResponse
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($rvmId);
            
            // Check permissions
            if (!$this->canAccessRvm($rvm)) {
                return response()->json([
                    'success' => false,
                    'message' => 'Access denied'
                ], 403);
            }

            $validator = Validator::make($request->all(), [
                'template_id' => 'required|integer|exists:configuration_templates,id',
                'customizations' => 'nullable|array',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Validation failed',
                    'errors' => $validator->errors()
                ], 422);
            }

            $template = ConfigurationTemplate::findOrFail($request->input('template_id'));
            $baseConfig = json_decode($template->configuration, true);
            
            // Apply customizations if provided
            $customizations = $request->input('customizations', []);
            $finalConfig = $this->mergeConfigurations($baseConfig, $customizations);

            // Validate final configuration
            $validationResult = $this->validateConfiguration($finalConfig);
            if (!$validationResult['valid']) {
                return response()->json([
                    'success' => false,
                    'message' => 'Configuration validation failed',
                    'errors' => $validationResult['errors']
                ], 422);
            }

            DB::beginTransaction();

            try {
                // Deactivate current configuration
                RvmConfiguration::where('rvm_id', $rvmId)
                    ->where('is_active', true)
                    ->update(['is_active' => false]);

                // Create new configuration from template
                $newConfig = RvmConfiguration::create([
                    'rvm_id' => $rvmId,
                    'configuration' => json_encode($finalConfig),
                    'version' => $template->version ?? '1.0.0',
                    'template_id' => $template->id,
                    'is_active' => true,
                    'created_by' => auth()->id(),
                ]);

                // Clear cache
                Cache::forget("rvm_config_{$rvmId}");

                // Send real-time update to RVM
                $this->sendConfigUpdateToRvm($rvm, $newConfig);

                DB::commit();

                return response()->json([
                    'success' => true,
                    'message' => 'Configuration template applied successfully',
                    'data' => [
                        'config_id' => $newConfig->id,
                        'template_name' => $template->name,
                        'version' => $newConfig->version,
                        'updated_at' => $newConfig->updated_at,
                    ]
                ], 200);

            } catch (\Exception $e) {
                DB::rollback();
                throw $e;
            }

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to apply configuration template',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get configuration history for RVM
     *
     * @param Request $request
     * @param int $rvmId
     * @return JsonResponse
     */
    public function getConfigHistory(Request $request, int $rvmId): JsonResponse
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($rvmId);
            
            // Check permissions
            if (!$this->canAccessRvm($rvm)) {
                return response()->json([
                    'success' => false,
                    'message' => 'Access denied'
                ], 403);
            }

            $configs = RvmConfiguration::where('rvm_id', $rvmId)
                ->with('template')
                ->orderBy('created_at', 'desc')
                ->paginate(20);

            $formattedConfigs = $configs->map(function ($config) {
                return [
                    'id' => $config->id,
                    'version' => $config->version,
                    'is_active' => $config->is_active,
                    'template_name' => $config->template ? $config->template->name : null,
                    'created_at' => $config->created_at,
                    'created_by' => $config->created_by,
                ];
            });

            return response()->json([
                'success' => true,
                'data' => [
                    'configurations' => $formattedConfigs,
                    'pagination' => [
                        'current_page' => $configs->currentPage(),
                        'last_page' => $configs->lastPage(),
                        'per_page' => $configs->perPage(),
                        'total' => $configs->total(),
                    ]
                ]
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get configuration history',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Rollback configuration to previous version
     *
     * @param Request $request
     * @param int $rvmId
     * @return JsonResponse
     */
    public function rollbackConfig(Request $request, int $rvmId): JsonResponse
    {
        try {
            $rvm = ReverseVendingMachine::findOrFail($rvmId);
            
            // Check permissions
            if (!$this->canAccessRvm($rvm)) {
                return response()->json([
                    'success' => false,
                    'message' => 'Access denied'
                ], 403);
            }

            $validator = Validator::make($request->all(), [
                'config_id' => 'required|integer|exists:rvm_configurations,id',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Validation failed',
                    'errors' => $validator->errors()
                ], 422);
            }

            $targetConfig = RvmConfiguration::where('id', $request->input('config_id'))
                ->where('rvm_id', $rvmId)
                ->firstOrFail();

            DB::beginTransaction();

            try {
                // Deactivate current configuration
                RvmConfiguration::where('rvm_id', $rvmId)
                    ->where('is_active', true)
                    ->update(['is_active' => false]);

                // Create new configuration from target
                $newConfig = RvmConfiguration::create([
                    'rvm_id' => $rvmId,
                    'configuration' => $targetConfig->configuration,
                    'version' => $targetConfig->version . '_rollback',
                    'template_id' => $targetConfig->template_id,
                    'is_active' => true,
                    'created_by' => auth()->id(),
                ]);

                // Clear cache
                Cache::forget("rvm_config_{$rvmId}");

                // Send real-time update to RVM
                $this->sendConfigUpdateToRvm($rvm, $newConfig);

                DB::commit();

                return response()->json([
                    'success' => true,
                    'message' => 'Configuration rolled back successfully',
                    'data' => [
                        'config_id' => $newConfig->id,
                        'version' => $newConfig->version,
                        'rolled_back_from' => $targetConfig->id,
                        'updated_at' => $newConfig->updated_at,
                    ]
                ], 200);

            } catch (\Exception $e) {
                DB::rollback();
                throw $e;
            }

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to rollback configuration',
                'error' => $e->getMessage()
            ], 500);
        }
    }
}
```

---

## **🔧 HELPER METHODS**

### **1. Permission Check**
```php
/**
 * Check if user can access RVM
 *
 * @param ReverseVendingMachine $rvm
 * @return bool
 */
private function canAccessRvm(ReverseVendingMachine $rvm): bool
{
    $user = auth()->user();
    
    // Super admin can access all RVMs
    if ($user->hasRole('super-admin')) {
        return true;
    }
    
    // Admin can access RVMs in their tenant
    if ($user->hasRole('admin')) {
        return $user->tenant_id === $rvm->tenant_id;
    }
    
    // Tenant can access their own RVMs
    if ($user->hasRole('tenant')) {
        return $user->tenant_id === $rvm->tenant_id;
    }
    
    return false;
}
```

### **2. Default Configuration**
```php
/**
 * Get default configuration for RVM
 *
 * @param ReverseVendingMachine $rvm
 * @return RvmConfiguration
 */
private function getDefaultConfiguration(ReverseVendingMachine $rvm): RvmConfiguration
{
    $defaultConfig = [
        'application' => [
            'name' => 'MyRVM Application',
            'version' => '1.0.0',
            'environment' => 'production',
            'debug' => false,
            'log_level' => 'INFO'
        ],
        'services' => [
            'config_manager' => ['enabled' => true, 'priority' => 1],
            'api_client' => ['enabled' => true, 'priority' => 2],
            'service_integration' => ['enabled' => true, 'priority' => 3],
            'gui_client' => ['enabled' => true, 'priority' => 4, 'port' => 5001],
            'led_screen_interface' => ['enabled' => true, 'priority' => 5],
            'user_profile_manager' => ['enabled' => true, 'priority' => 6],
            'detection_service' => ['enabled' => true, 'priority' => 7],
            'metrics_sender' => ['enabled' => true, 'priority' => 8],
            'command_receiver' => ['enabled' => true, 'priority' => 9]
        ],
        'remote_access' => [
            'server_url' => config('app.url'),
            'api_key' => $rvm->api_key,
            'rvm_id' => $rvm->id,
            'metrics_interval' => 30,
            'command_timeout' => 30
        ]
    ];

    return new RvmConfiguration([
        'rvm_id' => $rvm->id,
        'configuration' => json_encode($defaultConfig),
        'version' => '1.0.0',
        'is_active' => true,
        'created_by' => auth()->id(),
    ]);
}
```

### **3. Configuration Validation**
```php
/**
 * Validate configuration
 *
 * @param array $configuration
 * @return array
 */
private function validateConfiguration(array $configuration): array
{
    $errors = [];
    
    // Required sections
    $requiredSections = ['application', 'services', 'remote_access'];
    foreach ($requiredSections as $section) {
        if (!isset($configuration[$section])) {
            $errors[] = "Missing required section: {$section}";
        }
    }
    
    // Validate application section
    if (isset($configuration['application'])) {
        $appConfig = $configuration['application'];
        if (!isset($appConfig['name']) || empty($appConfig['name'])) {
            $errors[] = 'Application name is required';
        }
        if (!isset($appConfig['version']) || empty($appConfig['version'])) {
            $errors[] = 'Application version is required';
        }
    }
    
    // Validate services section
    if (isset($configuration['services'])) {
        $services = $configuration['services'];
        $requiredServices = ['config_manager', 'api_client', 'service_integration'];
        foreach ($requiredServices as $service) {
            if (!isset($services[$service])) {
                $errors[] = "Required service missing: {$service}";
            }
        }
    }
    
    // Validate remote_access section
    if (isset($configuration['remote_access'])) {
        $remoteAccess = $configuration['remote_access'];
        if (!isset($remoteAccess['server_url']) || empty($remoteAccess['server_url'])) {
            $errors[] = 'Server URL is required';
        }
        if (!isset($remoteAccess['api_key']) || empty($remoteAccess['api_key'])) {
            $errors[] = 'API key is required';
        }
    }
    
    return [
        'valid' => empty($errors),
        'errors' => $errors
    ];
}
```

### **4. Configuration Merging**
```php
/**
 * Merge configurations
 *
 * @param array $baseConfig
 * @param array $customizations
 * @return array
 */
private function mergeConfigurations(array $baseConfig, array $customizations): array
{
    return array_merge_recursive($baseConfig, $customizations);
}
```

### **5. Send Real-time Update**
```php
/**
 * Send configuration update to RVM
 *
 * @param ReverseVendingMachine $rvm
 * @param RvmConfiguration $config
 * @return void
 */
private function sendConfigUpdateToRvm(ReverseVendingMachine $rvm, RvmConfiguration $config): void
{
    // This would integrate with WebSocket or push notification system
    // For now, we'll just log the update
    \Log::info("Configuration update sent to RVM {$rvm->id}", [
        'config_id' => $config->id,
        'version' => $config->version,
    ]);
}
```

---

## **🗄️ DATABASE SCHEMA**

### **1. RVM Configurations Table**
```sql
CREATE TABLE rvm_configurations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    rvm_id BIGINT UNSIGNED NOT NULL,
    configuration JSON NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    template_id BIGINT UNSIGNED NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_by BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES configuration_templates(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_rvm_active (rvm_id, is_active),
    INDEX idx_created_at (created_at)
);
```

### **2. Configuration Templates Table**
```sql
CREATE TABLE configuration_templates (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    template_type VARCHAR(100) NOT NULL,
    configuration JSON NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_template_type (template_type),
    INDEX idx_active (is_active)
);
```

---

## **🧪 TESTING STRATEGY**

### **Unit Testing:**
- **Configuration validation** testing
- **Configuration merging** testing
- **Permission checking** testing
- **Helper methods** testing

### **Integration Testing:**
- **Database integration** testing
- **API endpoint** testing
- **Authentication** testing
- **Error handling** testing

### **API Testing:**
- **Postman collection** untuk semua endpoints
- **Automated testing** dengan PHPUnit
- **Load testing** untuk configuration updates
- **Security testing** untuk access control

---

## **📊 SUCCESS CRITERIA**

### **Functional Success:**
- ✅ Dynamic configuration loading
- ✅ Real-time configuration updates
- ✅ Configuration templates
- ✅ Configuration validation
- ✅ Configuration versioning
- ✅ Configuration rollback
- ✅ Configuration history

### **Technical Success:**
- ✅ Proper validation
- ✅ Error handling
- ✅ Database transactions
- ✅ Performance optimization
- ✅ Security measures
- ✅ Caching implementation

### **Integration Success:**
- ✅ RVM-Jetson integration
- ✅ Admin dashboard integration
- ✅ WebSocket integration
- ✅ Database schema compatibility

---

## **⏱️ ESTIMATED TIMELINE**

### **Week 1: Core API Development**
- **Day 1-2**: Configuration CRUD endpoints
- **Day 3-4**: Configuration templates
- **Day 5**: Configuration validation

### **Week 2: Advanced Features**
- **Day 1-2**: Configuration history
- **Day 3-4**: Configuration rollback
- **Day 5**: Real-time updates

### **Week 3: Database & Integration**
- **Day 1-2**: Database schema
- **Day 3-4**: RVM-Jetson integration
- **Day 5**: Admin dashboard integration

### **Week 4: Testing & Documentation**
- **Day 1-2**: Unit testing
- **Day 3-4**: Integration testing
- **Day 5**: Documentation

---

## **📁 DELIVERABLES**

### **Code Files:**
- `ConfigurationController.php`
- Database migrations
- Model classes
- Helper methods

### **Documentation:**
- API documentation
- Integration guide
- Database schema
- Testing documentation

### **Testing:**
- Unit tests
- Integration tests
- API tests
- Performance tests

---

**Status**: 📋 **READY FOR IMPLEMENTATION**  
**Estimated Time**: 4 weeks  
**Difficulty**: Advanced  
**Dependencies**: Database schema, Authentication system, RVM-Jetson integration
