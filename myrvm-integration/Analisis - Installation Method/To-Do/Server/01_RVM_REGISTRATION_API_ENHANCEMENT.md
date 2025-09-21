# TASK 01: RVM REGISTRATION API ENHANCEMENT

**Tanggal**: 2025-09-21  
**Versi**: 1.0.0  
**Status**: 📋 PLANNING  
**Priority**: HIGH  

---

## **🎯 OBJECTIVE**

Meningkatkan RVM Registration API untuk mendukung auto-registration dari RVM-Jetson melalui Installation Method, termasuk bulk registration, validation, dan API key generation.

---

## **📋 CURRENT STATUS ANALYSIS**

### **✅ Already Available:**
- ✅ **RVM Registration API**: `POST /api/v2/rvms` (dalam RVMController)
- ✅ **RVM Management API**: CRUD operations untuk RVM
- ✅ **API Key Generation**: Regenerate API key functionality
- ✅ **Database Schema**: ReverseVendingMachine model
- ✅ **Authentication**: Sanctum-based authentication

### **❌ Need to Enhance:**
- ❌ **Auto-registration endpoint** untuk Installation Method
- ❌ **Bulk registration** support
- ❌ **Registration validation** dan pre-checks
- ❌ **Hardware validation** integration
- ❌ **Installation status** tracking

---

## **🔧 IMPLEMENTATION PLAN**

### **1. Enhanced RVM Registration Endpoints**

#### **A. Auto-Registration Endpoint**
```php
// New endpoint: POST /api/v2/rvms/auto-register
Route::post('/rvms/auto-register', [RVMController::class, 'autoRegister']);
```

#### **B. Bulk Registration Endpoint**
```php
// New endpoint: POST /api/v2/rvms/bulk-register
Route::post('/rvms/bulk-register', [RVMController::class, 'bulkRegister']);
```

#### **C. Registration Validation Endpoint**
```php
// New endpoint: POST /api/v2/rvms/validate-registration
Route::post('/rvms/validate-registration', [RVMController::class, 'validateRegistration']);
```

### **2. Enhanced RVMController Methods**

#### **A. Auto-Registration Method**
```php
public function autoRegister(Request $request): JsonResponse
{
    // Auto-generate RVM ID
    // Auto-generate API key
    // Validate hardware info
    // Create RVM record
    // Return registration data
}
```

#### **B. Bulk Registration Method**
```php
public function bulkRegister(Request $request): JsonResponse
{
    // Process multiple RVM registrations
    // Validate each registration
    // Create batch of RVM records
    // Return bulk registration results
}
```

#### **C. Registration Validation Method**
```php
public function validateRegistration(Request $request): JsonResponse
{
    // Validate RVM data
    // Check for duplicates
    // Validate hardware compatibility
    // Return validation results
}
```

---

## **📝 DETAILED IMPLEMENTATION**

### **1. Auto-Registration Endpoint**

#### **Route Definition:**
```php
// routes/api-v2.php
Route::prefix('rvms')->group(function () {
    // Existing routes...
    Route::post('/auto-register', [RVMController::class, 'autoRegister']);
    Route::post('/bulk-register', [RVMController::class, 'bulkRegister']);
    Route::post('/validate-registration', [RVMController::class, 'validateRegistration']);
});
```

#### **Controller Method:**
```php
/**
 * Auto-register RVM from Installation Method
 *
 * @param Request $request
 * @return JsonResponse
 */
public function autoRegister(Request $request): JsonResponse
{
    try {
        $validator = Validator::make($request->all(), [
            'hardware_info' => 'required|array',
            'hardware_info.mac_address' => 'required|string|max:17',
            'hardware_info.serial_number' => 'nullable|string|max:255',
            'hardware_info.model' => 'required|string|max:255',
            'hardware_info.location' => 'required|string|max:255',
            'network_info' => 'required|array',
            'network_info.local_ip' => 'required|ip',
            'network_info.vpn_ip' => 'nullable|ip',
            'installation_info' => 'required|array',
            'installation_info.technician_id' => 'nullable|string|max:255',
            'installation_info.installation_date' => 'required|date',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }

        $data = $request->all();
        
        // Generate unique RVM ID
        $rvmId = $this->generateUniqueRvmId($data['hardware_info']);
        
        // Generate API key
        $apiKey = $this->generateApiKey();
        
        // Create RVM record
        $rvm = ReverseVendingMachine::create([
            'name' => $this->generateRvmName($data['hardware_info'], $data['hardware_info']['location']),
            'location_description' => $data['hardware_info']['location'],
            'status' => 'active',
            'api_key' => $apiKey,
            'hardware_info' => json_encode($data['hardware_info']),
            'network_info' => json_encode($data['network_info']),
            'installation_info' => json_encode($data['installation_info']),
            'created_by' => auth()->id(),
        ]);

        return response()->json([
            'success' => true,
            'message' => 'RVM registered successfully',
            'data' => [
                'rvm_id' => $rvm->id,
                'name' => $rvm->name,
                'api_key' => $apiKey,
                'status' => $rvm->status,
                'created_at' => $rvm->created_at,
            ]
        ], 201);

    } catch (\Exception $e) {
        return response()->json([
            'success' => false,
            'message' => 'Registration failed',
            'error' => $e->getMessage()
        ], 500);
    }
}
```

### **2. Bulk Registration Endpoint**

#### **Controller Method:**
```php
/**
 * Bulk register multiple RVMs
 *
 * @param Request $request
 * @return JsonResponse
 */
public function bulkRegister(Request $request): JsonResponse
{
    try {
        $validator = Validator::make($request->all(), [
            'rvms' => 'required|array|min:1|max:100',
            'rvms.*.hardware_info' => 'required|array',
            'rvms.*.hardware_info.mac_address' => 'required|string|max:17',
            'rvms.*.hardware_info.serial_number' => 'nullable|string|max:255',
            'rvms.*.hardware_info.model' => 'required|string|max:255',
            'rvms.*.hardware_info.location' => 'required|string|max:255',
            'rvms.*.network_info' => 'required|array',
            'rvms.*.network_info.local_ip' => 'required|ip',
            'rvms.*.network_info.vpn_ip' => 'nullable|ip',
            'rvms.*.installation_info' => 'required|array',
            'rvms.*.installation_info.technician_id' => 'nullable|string|max:255',
            'rvms.*.installation_info.installation_date' => 'required|date',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }

        $rvms = $request->input('rvms');
        $results = [];
        $successCount = 0;
        $errorCount = 0;

        DB::beginTransaction();

        try {
            foreach ($rvms as $index => $rvmData) {
                try {
                    // Generate unique RVM ID
                    $rvmId = $this->generateUniqueRvmId($rvmData['hardware_info']);
                    
                    // Generate API key
                    $apiKey = $this->generateApiKey();
                    
                    // Create RVM record
                    $rvm = ReverseVendingMachine::create([
                        'name' => $this->generateRvmName($rvmData['hardware_info'], $rvmData['hardware_info']['location']),
                        'location_description' => $rvmData['hardware_info']['location'],
                        'status' => 'active',
                        'api_key' => $apiKey,
                        'hardware_info' => json_encode($rvmData['hardware_info']),
                        'network_info' => json_encode($rvmData['network_info']),
                        'installation_info' => json_encode($rvmData['installation_info']),
                        'created_by' => auth()->id(),
                    ]);

                    $results[] = [
                        'index' => $index,
                        'success' => true,
                        'rvm_id' => $rvm->id,
                        'name' => $rvm->name,
                        'api_key' => $apiKey,
                    ];

                    $successCount++;

                } catch (\Exception $e) {
                    $results[] = [
                        'index' => $index,
                        'success' => false,
                        'error' => $e->getMessage(),
                    ];

                    $errorCount++;
                }
            }

            DB::commit();

            return response()->json([
                'success' => true,
                'message' => 'Bulk registration completed',
                'data' => [
                    'total' => count($rvms),
                    'success_count' => $successCount,
                    'error_count' => $errorCount,
                    'results' => $results,
                ]
            ], 201);

        } catch (\Exception $e) {
            DB::rollback();
            throw $e;
        }

    } catch (\Exception $e) {
        return response()->json([
            'success' => false,
            'message' => 'Bulk registration failed',
            'error' => $e->getMessage()
        ], 500);
    }
}
```

### **3. Registration Validation Endpoint**

#### **Controller Method:**
```php
/**
 * Validate RVM registration data
 *
 * @param Request $request
 * @return JsonResponse
 */
public function validateRegistration(Request $request): JsonResponse
{
    try {
        $validator = Validator::make($request->all(), [
            'hardware_info' => 'required|array',
            'hardware_info.mac_address' => 'required|string|max:17',
            'hardware_info.serial_number' => 'nullable|string|max:255',
            'hardware_info.model' => 'required|string|max:255',
            'hardware_info.location' => 'required|string|max:255',
            'network_info' => 'required|array',
            'network_info.local_ip' => 'required|ip',
            'network_info.vpn_ip' => 'nullable|ip',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }

        $data = $request->all();
        $validationResults = [];

        // Check for duplicate MAC address
        $existingRvm = ReverseVendingMachine::where('hardware_info->mac_address', $data['hardware_info']['mac_address'])->first();
        if ($existingRvm) {
            $validationResults['duplicate_mac'] = [
                'valid' => false,
                'message' => 'MAC address already registered',
                'existing_rvm_id' => $existingRvm->id,
            ];
        } else {
            $validationResults['duplicate_mac'] = [
                'valid' => true,
                'message' => 'MAC address is unique',
            ];
        }

        // Check for duplicate serial number (if provided)
        if (!empty($data['hardware_info']['serial_number'])) {
            $existingRvm = ReverseVendingMachine::where('hardware_info->serial_number', $data['hardware_info']['serial_number'])->first();
            if ($existingRvm) {
                $validationResults['duplicate_serial'] = [
                    'valid' => false,
                    'message' => 'Serial number already registered',
                    'existing_rvm_id' => $existingRvm->id,
                ];
            } else {
                $validationResults['duplicate_serial'] = [
                    'valid' => true,
                    'message' => 'Serial number is unique',
                ];
            }
        }

        // Check for duplicate IP address
        $existingRvm = ReverseVendingMachine::where('network_info->local_ip', $data['network_info']['local_ip'])->first();
        if ($existingRvm) {
            $validationResults['duplicate_ip'] = [
                'valid' => false,
                'message' => 'IP address already registered',
                'existing_rvm_id' => $existingRvm->id,
            ];
        } else {
            $validationResults['duplicate_ip'] = [
                'valid' => true,
                'message' => 'IP address is unique',
            ];
        }

        // Hardware compatibility check
        $hardwareCompatibility = $this->checkHardwareCompatibility($data['hardware_info']);
        $validationResults['hardware_compatibility'] = $hardwareCompatibility;

        // Overall validation result
        $allValid = collect($validationResults)->every(function ($result) {
            return $result['valid'] ?? true;
        });

        return response()->json([
            'success' => true,
            'message' => 'Validation completed',
            'data' => [
                'valid' => $allValid,
                'validation_results' => $validationResults,
                'recommendations' => $this->getValidationRecommendations($validationResults),
            ]
        ], 200);

    } catch (\Exception $e) {
        return response()->json([
            'success' => false,
            'message' => 'Validation failed',
            'error' => $e->getMessage()
        ], 500);
    }
}
```

---

## **🔧 HELPER METHODS**

### **1. Generate Unique RVM ID**
```php
/**
 * Generate unique RVM ID based on hardware info
 *
 * @param array $hardwareInfo
 * @return string
 */
private function generateUniqueRvmId(array $hardwareInfo): string
{
    $macAddress = str_replace(':', '', $hardwareInfo['mac_address']);
    $model = strtoupper(substr($hardwareInfo['model'], 0, 3));
    $timestamp = date('Ymd');
    
    $baseId = $model . $macAddress . $timestamp;
    
    // Check if ID already exists and append counter if needed
    $counter = 1;
    $rvmId = $baseId;
    
    while (ReverseVendingMachine::where('id', $rvmId)->exists()) {
        $rvmId = $baseId . sprintf('%03d', $counter);
        $counter++;
    }
    
    return $rvmId;
}
```

### **2. Generate API Key**
```php
/**
 * Generate secure API key
 *
 * @return string
 */
private function generateApiKey(): string
{
    return 'myrvm_' . Str::random(32);
}
```

### **3. Generate RVM Name**
```php
/**
 * Generate RVM name based on hardware info and location
 *
 * @param array $hardwareInfo
 * @param string $location
 * @return string
 */
private function generateRvmName(array $hardwareInfo, string $location): string
{
    $model = $hardwareInfo['model'];
    $location = strtoupper(str_replace(' ', '_', $location));
    $timestamp = date('Ymd');
    
    return "MyRVM_{$model}_{$location}_{$timestamp}";
}
```

### **4. Check Hardware Compatibility**
```php
/**
 * Check hardware compatibility
 *
 * @param array $hardwareInfo
 * @return array
 */
private function checkHardwareCompatibility(array $hardwareInfo): array
{
    $compatibility = [
        'valid' => true,
        'message' => 'Hardware is compatible',
        'details' => []
    ];

    // Check supported models
    $supportedModels = ['Jetson Orin Nano', 'Jetson Orin NX', 'Jetson Xavier NX'];
    if (!in_array($hardwareInfo['model'], $supportedModels)) {
        $compatibility['valid'] = false;
        $compatibility['message'] = 'Unsupported hardware model';
        $compatibility['details'][] = 'Model not in supported list: ' . implode(', ', $supportedModels);
    }

    // Check MAC address format
    if (!preg_match('/^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/', $hardwareInfo['mac_address'])) {
        $compatibility['valid'] = false;
        $compatibility['message'] = 'Invalid MAC address format';
        $compatibility['details'][] = 'MAC address must be in format XX:XX:XX:XX:XX:XX';
    }

    return $compatibility;
}
```

### **5. Get Validation Recommendations**
```php
/**
 * Get validation recommendations
 *
 * @param array $validationResults
 * @return array
 */
private function getValidationRecommendations(array $validationResults): array
{
    $recommendations = [];

    foreach ($validationResults as $key => $result) {
        if (!$result['valid']) {
            switch ($key) {
                case 'duplicate_mac':
                    $recommendations[] = 'Consider using a different network interface or updating hardware';
                    break;
                case 'duplicate_serial':
                    $recommendations[] = 'Verify serial number or contact hardware vendor';
                    break;
                case 'duplicate_ip':
                    $recommendations[] = 'Configure different IP address or check network configuration';
                    break;
                case 'hardware_compatibility':
                    $recommendations[] = 'Update hardware to supported model or contact support';
                    break;
            }
        }
    }

    return $recommendations;
}
```

---

## **🧪 TESTING STRATEGY**

### **Unit Testing:**
- **Auto-registration** endpoint testing
- **Bulk registration** endpoint testing
- **Validation** endpoint testing
- **Helper methods** testing

### **Integration Testing:**
- **Database integration** testing
- **Authentication** testing
- **Error handling** testing
- **Performance** testing

### **API Testing:**
- **Postman collection** untuk semua endpoints
- **Automated testing** dengan PHPUnit
- **Load testing** untuk bulk operations
- **Security testing** untuk API key generation

---

## **📊 SUCCESS CRITERIA**

### **Functional Success:**
- ✅ Auto-registration endpoint working
- ✅ Bulk registration endpoint working
- ✅ Registration validation endpoint working
- ✅ Unique RVM ID generation
- ✅ Secure API key generation
- ✅ Duplicate detection
- ✅ Hardware compatibility checking

### **Technical Success:**
- ✅ Proper validation
- ✅ Error handling
- ✅ Database transactions
- ✅ Performance optimization
- ✅ Security measures

### **Integration Success:**
- ✅ RVM-Jetson integration
- ✅ Admin dashboard integration
- ✅ Database schema compatibility
- ✅ API documentation

---

## **⏱️ ESTIMATED TIMELINE**

### **Week 1: Core API Development**
- **Day 1-2**: Auto-registration endpoint
- **Day 3-4**: Bulk registration endpoint
- **Day 5**: Registration validation endpoint

### **Week 2: Helper Methods & Testing**
- **Day 1-2**: Helper methods implementation
- **Day 3-4**: Unit testing
- **Day 5**: Integration testing

### **Week 3: Documentation & Integration**
- **Day 1-2**: API documentation
- **Day 3-4**: RVM-Jetson integration
- **Day 5**: Admin dashboard integration

### **Week 4: Testing & Deployment**
- **Day 1-2**: End-to-end testing
- **Day 3-4**: Performance testing
- **Day 5**: Production deployment

---

## **📁 DELIVERABLES**

### **Code Files:**
- Enhanced `RVMController.php`
- Updated `routes/api-v2.php`
- Helper methods
- Validation rules

### **Documentation:**
- API documentation
- Integration guide
- Testing documentation
- Deployment guide

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