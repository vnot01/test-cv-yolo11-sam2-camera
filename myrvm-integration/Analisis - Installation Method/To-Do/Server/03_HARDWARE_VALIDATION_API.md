# TASK 03: HARDWARE VALIDATION API

**Tanggal**: 2025-09-21  
**Versi**: 1.0.0  
**Status**: 📋 PLANNING  
**Priority**: HIGH  

---

## **🎯 OBJECTIVE**

Membuat Hardware Validation API untuk validasi hardware compatibility, hardware status validation, dan hardware requirements check untuk RVM-Jetson.

---

## **📋 REQUIREMENTS**

### **Functional Requirements:**
- **Hardware Compatibility Check** (Jetson model, CUDA, TensorRT, OpenCV)
- **Hardware Status Validation** (camera, GPIO, audio, network)
- **Hardware Requirements Check** (minimum specs, dependencies)
- **Hardware Performance Testing** (benchmark, stress test)
- **Hardware Configuration Validation** (settings, drivers)
- **Hardware Error Detection** (faulty components, driver issues)
- **Hardware Recommendations** (optimization, troubleshooting)

### **Technical Requirements:**
- **RESTful API** endpoints
- **Hardware Database** (compatibility matrix, requirements)
- **Validation Rules Engine** (configurable validation rules)
- **Performance Metrics** (benchmark data, thresholds)
- **Error Reporting** (detailed error messages, solutions)
- **Hardware Profiles** (predefined hardware configurations)

---

## **🔧 IMPLEMENTATION PLAN**

### **1. Hardware Validation API Endpoints**

#### **A. Hardware Compatibility Check**
```php
// Endpoint: POST /api/v2/hardware/validate-compatibility
Route::post('/hardware/validate-compatibility', [HardwareValidationController::class, 'validateCompatibility']);
```

#### **B. Hardware Status Validation**
```php
// Endpoint: POST /api/v2/hardware/validate-status
Route::post('/hardware/validate-status', [HardwareValidationController::class, 'validateStatus']);
```

#### **C. Hardware Requirements Check**
```php
// Endpoint: POST /api/v2/hardware/check-requirements
Route::post('/hardware/check-requirements', [HardwareValidationController::class, 'checkRequirements']);
```

#### **D. Hardware Performance Test**
```php
// Endpoint: POST /api/v2/hardware/performance-test
Route::post('/hardware/performance-test', [HardwareValidationController::class, 'performanceTest']);
```

---

## **📝 DETAILED IMPLEMENTATION**

### **1. HardwareValidationController**

#### **Controller Setup:**
```php
<?php

namespace App\Http\Controllers\Api\V2;

use App\Http\Controllers\Controller;
use App\Models\HardwareCompatibility;
use App\Models\HardwareRequirements;
use App\Models\HardwareProfile;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Validator;

class HardwareValidationController extends Controller
{
    public function __construct()
    {
        $this->middleware('auth:sanctum');
        $this->middleware('role:super-admin|admin|tenant');
    }

    /**
     * Validate hardware compatibility
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function validateCompatibility(Request $request): JsonResponse
    {
        try {
            $validator = Validator::make($request->all(), [
                'hardware_info' => 'required|array',
                'hardware_info.model' => 'required|string|max:255',
                'hardware_info.serial_number' => 'nullable|string|max:255',
                'hardware_info.cuda_version' => 'nullable|string|max:50',
                'hardware_info.tensorrt_version' => 'nullable|string|max:50',
                'hardware_info.opencv_version' => 'nullable|string|max:50',
                'hardware_info.driver_version' => 'nullable|string|max:50',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Validation failed',
                    'errors' => $validator->errors()
                ], 422);
            }

            $hardwareInfo = $request->input('hardware_info');
            $compatibilityResult = $this->checkHardwareCompatibility($hardwareInfo);

            return response()->json([
                'success' => true,
                'data' => $compatibilityResult
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Hardware compatibility validation failed',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Validate hardware status
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function validateStatus(Request $request): JsonResponse
    {
        try {
            $validator = Validator::make($request->all(), [
                'hardware_status' => 'required|array',
                'hardware_status.camera' => 'required|array',
                'hardware_status.gpio' => 'required|array',
                'hardware_status.audio' => 'required|array',
                'hardware_status.network' => 'required|array',
                'hardware_status.storage' => 'required|array',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Validation failed',
                    'errors' => $validator->errors()
                ], 422);
            }

            $hardwareStatus = $request->input('hardware_status');
            $statusResult = $this->validateHardwareStatus($hardwareStatus);

            return response()->json([
                'success' => true,
                'data' => $statusResult
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Hardware status validation failed',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Check hardware requirements
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function checkRequirements(Request $request): JsonResponse
    {
        try {
            $validator = Validator::make($request->all(), [
                'hardware_specs' => 'required|array',
                'hardware_specs.cpu_cores' => 'required|integer|min:1',
                'hardware_specs.memory_gb' => 'required|numeric|min:1',
                'hardware_specs.storage_gb' => 'required|numeric|min:1',
                'hardware_specs.gpu_memory_mb' => 'nullable|integer|min:0',
                'hardware_specs.network_speed_mbps' => 'nullable|numeric|min:0',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Validation failed',
                    'errors' => $validator->errors()
                ], 422);
            }

            $hardwareSpecs = $request->input('hardware_specs');
            $requirementsResult = $this->checkHardwareRequirements($hardwareSpecs);

            return response()->json([
                'success' => true,
                'data' => $requirementsResult
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Hardware requirements check failed',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Performance test
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function performanceTest(Request $request): JsonResponse
    {
        try {
            $validator = Validator::make($request->all(), [
                'test_type' => 'required|in:cpu,memory,gpu,storage,network',
                'test_duration' => 'nullable|integer|min:1|max:300',
                'test_intensity' => 'nullable|in:low,medium,high',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Validation failed',
                    'errors' => $validator->errors()
                ], 422);
            }

            $testType = $request->input('test_type');
            $testDuration = $request->input('test_duration', 60);
            $testIntensity = $request->input('test_intensity', 'medium');

            $performanceResult = $this->runPerformanceTest($testType, $testDuration, $testIntensity);

            return response()->json([
                'success' => true,
                'data' => $performanceResult
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Performance test failed',
                'error' => $e->getMessage()
            ], 500);
        }
    }
}
```

### **2. Hardware Compatibility Check**

#### **Compatibility Validation Logic:**
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
        'compatible' => true,
        'compatibility_score' => 100,
        'issues' => [],
        'recommendations' => [],
        'details' => []
    ];

    // Check Jetson model compatibility
    $modelCompatibility = $this->checkJetsonModelCompatibility($hardwareInfo['model']);
    $compatibility['details']['model'] = $modelCompatibility;
    
    if (!$modelCompatibility['compatible']) {
        $compatibility['compatible'] = false;
        $compatibility['compatibility_score'] -= 30;
        $compatibility['issues'][] = 'Unsupported Jetson model';
    }

    // Check CUDA compatibility
    if (isset($hardwareInfo['cuda_version'])) {
        $cudaCompatibility = $this->checkCudaCompatibility($hardwareInfo['cuda_version']);
        $compatibility['details']['cuda'] = $cudaCompatibility;
        
        if (!$cudaCompatibility['compatible']) {
            $compatibility['compatible'] = false;
            $compatibility['compatibility_score'] -= 20;
            $compatibility['issues'][] = 'CUDA version not supported';
        }
    }

    // Check TensorRT compatibility
    if (isset($hardwareInfo['tensorrt_version'])) {
        $tensorrtCompatibility = $this->checkTensorRTCompatibility($hardwareInfo['tensorrt_version']);
        $compatibility['details']['tensorrt'] = $tensorrtCompatibility;
        
        if (!$tensorrtCompatibility['compatible']) {
            $compatibility['compatibility_score'] -= 15;
            $compatibility['recommendations'][] = 'Update TensorRT for better performance';
        }
    }

    // Check OpenCV compatibility
    if (isset($hardwareInfo['opencv_version'])) {
        $opencvCompatibility = $this->checkOpenCVCompatibility($hardwareInfo['opencv_version']);
        $compatibility['details']['opencv'] = $opencvCompatibility;
        
        if (!$opencvCompatibility['compatible']) {
            $compatibility['compatibility_score'] -= 10;
            $compatibility['recommendations'][] = 'Update OpenCV for better camera support';
        }
    }

    // Check driver compatibility
    if (isset($hardwareInfo['driver_version'])) {
        $driverCompatibility = $this->checkDriverCompatibility($hardwareInfo['driver_version']);
        $compatibility['details']['driver'] = $driverCompatibility;
        
        if (!$driverCompatibility['compatible']) {
            $compatibility['compatible'] = false;
            $compatibility['compatibility_score'] -= 25;
            $compatibility['issues'][] = 'Driver version not supported';
        }
    }

    // Generate overall recommendations
    if ($compatibility['compatibility_score'] < 70) {
        $compatibility['recommendations'][] = 'Hardware compatibility issues detected. Please check hardware requirements.';
    } elseif ($compatibility['compatibility_score'] >= 90) {
        $compatibility['recommendations'][] = 'Hardware is fully compatible. Ready for production deployment.';
    }

    return $compatibility;
}

/**
 * Check Jetson model compatibility
 *
 * @param string $model
 * @return array
 */
private function checkJetsonModelCompatibility(string $model): array
{
    $supportedModels = [
        'Jetson Orin Nano',
        'Jetson Orin NX',
        'Jetson Xavier NX',
        'Jetson AGX Xavier',
        'Jetson AGX Orin'
    ];

    $compatibility = [
        'compatible' => false,
        'model' => $model,
        'supported' => false,
        'recommended' => false,
        'performance_tier' => 'unknown'
    ];

    foreach ($supportedModels as $supportedModel) {
        if (stripos($model, $supportedModel) !== false) {
            $compatibility['compatible'] = true;
            $compatibility['supported'] = true;
            $compatibility['performance_tier'] = $this->getPerformanceTier($supportedModel);
            
            // Check if recommended
            if (in_array($supportedModel, ['Jetson Orin Nano', 'Jetson Orin NX'])) {
                $compatibility['recommended'] = true;
            }
            break;
        }
    }

    return $compatibility;
}

/**
 * Check CUDA compatibility
 *
 * @param string $cudaVersion
 * @return array
 */
private function checkCudaCompatibility(string $cudaVersion): array
{
    $supportedVersions = ['11.4', '11.8', '12.0', '12.1', '12.2'];
    $minimumVersion = '11.4';

    $compatibility = [
        'compatible' => false,
        'version' => $cudaVersion,
        'supported' => false,
        'minimum_required' => $minimumVersion,
        'recommended' => '12.0'
    ];

    if (in_array($cudaVersion, $supportedVersions)) {
        $compatibility['compatible'] = true;
        $compatibility['supported'] = true;
    } elseif (version_compare($cudaVersion, $minimumVersion, '>=')) {
        $compatibility['compatible'] = true;
        $compatibility['supported'] = false;
    }

    return $compatibility;
}

/**
 * Check TensorRT compatibility
 *
 * @param string $tensorrtVersion
 * @return array
 */
private function checkTensorRTCompatibility(string $tensorrtVersion): array
{
    $supportedVersions = ['8.0', '8.2', '8.4', '8.5', '8.6'];
    $minimumVersion = '8.0';

    $compatibility = [
        'compatible' => false,
        'version' => $tensorrtVersion,
        'supported' => false,
        'minimum_required' => $minimumVersion,
        'recommended' => '8.5'
    ];

    if (in_array($tensorrtVersion, $supportedVersions)) {
        $compatibility['compatible'] = true;
        $compatibility['supported'] = true;
    } elseif (version_compare($tensorrtVersion, $minimumVersion, '>=')) {
        $compatibility['compatible'] = true;
        $compatibility['supported'] = false;
    }

    return $compatibility;
}

/**
 * Check OpenCV compatibility
 *
 * @param string $opencvVersion
 * @return array
 */
private function checkOpenCVCompatibility(string $opencvVersion): array
{
    $supportedVersions = ['4.5', '4.6', '4.7', '4.8', '4.9'];
    $minimumVersion = '4.5';

    $compatibility = [
        'compatible' => false,
        'version' => $opencvVersion,
        'supported' => false,
        'minimum_required' => $minimumVersion,
        'recommended' => '4.8'
    ];

    if (in_array($opencvVersion, $supportedVersions)) {
        $compatibility['compatible'] = true;
        $compatibility['supported'] = true;
    } elseif (version_compare($opencvVersion, $minimumVersion, '>=')) {
        $compatibility['compatible'] = true;
        $compatibility['supported'] = false;
    }

    return $compatibility;
}

/**
 * Check driver compatibility
 *
 * @param string $driverVersion
 * @return array
 */
private function checkDriverCompatibility(string $driverVersion): array
{
    $supportedVersions = ['515', '520', '525', '530', '535'];
    $minimumVersion = '515';

    $compatibility = [
        'compatible' => false,
        'version' => $driverVersion,
        'supported' => false,
        'minimum_required' => $minimumVersion,
        'recommended' => '530'
    ];

    if (in_array($driverVersion, $supportedVersions)) {
        $compatibility['compatible'] = true;
        $compatibility['supported'] = true;
    } elseif (version_compare($driverVersion, $minimumVersion, '>=')) {
        $compatibility['compatible'] = true;
        $compatibility['supported'] = false;
    }

    return $compatibility;
}

/**
 * Get performance tier for Jetson model
 *
 * @param string $model
 * @return string
 */
private function getPerformanceTier(string $model): string
{
    $tiers = [
        'Jetson Orin Nano' => 'entry',
        'Jetson Orin NX' => 'mid',
        'Jetson Xavier NX' => 'mid',
        'Jetson AGX Xavier' => 'high',
        'Jetson AGX Orin' => 'premium'
    ];

    return $tiers[$model] ?? 'unknown';
}
```

### **3. Hardware Status Validation**

#### **Status Validation Logic:**
```php
/**
 * Validate hardware status
 *
 * @param array $hardwareStatus
 * @return array
 */
private function validateHardwareStatus(array $hardwareStatus): array
{
    $validation = [
        'valid' => true,
        'overall_score' => 100,
        'components' => [],
        'issues' => [],
        'recommendations' => []
    ];

    // Validate camera
    $cameraValidation = $this->validateCameraStatus($hardwareStatus['camera']);
    $validation['components']['camera'] = $cameraValidation;
    if (!$cameraValidation['valid']) {
        $validation['valid'] = false;
        $validation['overall_score'] -= 20;
        $validation['issues'][] = 'Camera validation failed';
    }

    // Validate GPIO
    $gpioValidation = $this->validateGPIOStatus($hardwareStatus['gpio']);
    $validation['components']['gpio'] = $gpioValidation;
    if (!$gpioValidation['valid']) {
        $validation['valid'] = false;
        $validation['overall_score'] -= 15;
        $validation['issues'][] = 'GPIO validation failed';
    }

    // Validate audio
    $audioValidation = $this->validateAudioStatus($hardwareStatus['audio']);
    $validation['components']['audio'] = $audioValidation;
    if (!$audioValidation['valid']) {
        $validation['overall_score'] -= 10;
        $validation['recommendations'][] = 'Audio validation failed - check audio devices';
    }

    // Validate network
    $networkValidation = $this->validateNetworkStatus($hardwareStatus['network']);
    $validation['components']['network'] = $networkValidation;
    if (!$networkValidation['valid']) {
        $validation['valid'] = false;
        $validation['overall_score'] -= 25;
        $validation['issues'][] = 'Network validation failed';
    }

    // Validate storage
    $storageValidation = $this->validateStorageStatus($hardwareStatus['storage']);
    $validation['components']['storage'] = $storageValidation;
    if (!$storageValidation['valid']) {
        $validation['valid'] = false;
        $validation['overall_score'] -= 30;
        $validation['issues'][] = 'Storage validation failed';
    }

    return $validation;
}

/**
 * Validate camera status
 *
 * @param array $cameraStatus
 * @return array
 */
private function validateCameraStatus(array $cameraStatus): array
{
    $validation = [
        'valid' => true,
        'score' => 100,
        'issues' => [],
        'details' => []
    ];

    // Check camera availability
    if (!$cameraStatus['available']) {
        $validation['valid'] = false;
        $validation['score'] = 0;
        $validation['issues'][] = 'Camera not available';
        return $validation;
    }

    // Check camera resolution
    if (isset($cameraStatus['resolution'])) {
        $resolution = $cameraStatus['resolution'];
        if ($resolution['width'] < 640 || $resolution['height'] < 480) {
            $validation['score'] -= 20;
            $validation['issues'][] = 'Camera resolution too low';
        }
    }

    // Check camera FPS
    if (isset($cameraStatus['fps'])) {
        if ($cameraStatus['fps'] < 15) {
            $validation['score'] -= 15;
            $validation['issues'][] = 'Camera FPS too low';
        }
    }

    // Check camera focus
    if (isset($cameraStatus['focus_quality'])) {
        if ($cameraStatus['focus_quality'] < 50) {
            $validation['score'] -= 10;
            $validation['issues'][] = 'Camera focus quality poor';
        }
    }

    return $validation;
}

/**
 * Validate GPIO status
 *
 * @param array $gpioStatus
 * @return array
 */
private function validateGPIOStatus(array $gpioStatus): array
{
    $validation = [
        'valid' => true,
        'score' => 100,
        'issues' => [],
        'details' => []
    ];

    // Check GPIO availability
    if (!$gpioStatus['available']) {
        $validation['valid'] = false;
        $validation['score'] = 0;
        $validation['issues'][] = 'GPIO not available';
        return $validation;
    }

    // Check GPIO pins
    if (isset($gpioStatus['pins'])) {
        $requiredPins = ['step', 'dir', 'enable'];
        foreach ($requiredPins as $pin) {
            if (!isset($gpioStatus['pins'][$pin]) || !$gpioStatus['pins'][$pin]['available']) {
                $validation['valid'] = false;
                $validation['score'] -= 25;
                $validation['issues'][] = "Required GPIO pin {$pin} not available";
            }
        }
    }

    return $validation;
}

/**
 * Validate audio status
 *
 * @param array $audioStatus
 * @return array
 */
private function validateAudioStatus(array $audioStatus): array
{
    $validation = [
        'valid' => true,
        'score' => 100,
        'issues' => [],
        'details' => []
    ];

    // Check audio availability
    if (!$audioStatus['available']) {
        $validation['valid'] = false;
        $validation['score'] = 0;
        $validation['issues'][] = 'Audio not available';
        return $validation;
    }

    // Check speaker
    if (isset($audioStatus['speaker']) && !$audioStatus['speaker']['available']) {
        $validation['score'] -= 30;
        $validation['issues'][] = 'Speaker not available';
    }

    // Check microphone
    if (isset($audioStatus['microphone']) && !$audioStatus['microphone']['available']) {
        $validation['score'] -= 20;
        $validation['issues'][] = 'Microphone not available';
    }

    return $validation;
}

/**
 * Validate network status
 *
 * @param array $networkStatus
 * @return array
 */
private function validateNetworkStatus(array $networkStatus): array
{
    $validation = [
        'valid' => true,
        'score' => 100,
        'issues' => [],
        'details' => []
    ];

    // Check network connectivity
    if (!$networkStatus['connected']) {
        $validation['valid'] = false;
        $validation['score'] = 0;
        $validation['issues'][] = 'Network not connected';
        return $validation;
    }

    // Check network speed
    if (isset($networkStatus['speed_mbps'])) {
        if ($networkStatus['speed_mbps'] < 10) {
            $validation['score'] -= 20;
            $validation['issues'][] = 'Network speed too slow';
        }
    }

    // Check latency
    if (isset($networkStatus['latency_ms'])) {
        if ($networkStatus['latency_ms'] > 100) {
            $validation['score'] -= 15;
            $validation['issues'][] = 'Network latency too high';
        }
    }

    return $validation;
}

/**
 * Validate storage status
 *
 * @param array $storageStatus
 * @return array
 */
private function validateStorageStatus(array $storageStatus): array
{
    $validation = [
        'valid' => true,
        'score' => 100,
        'issues' => [],
        'details' => []
    ];

    // Check storage availability
    if (!$storageStatus['available']) {
        $validation['valid'] = false;
        $validation['score'] = 0;
        $validation['issues'][] = 'Storage not available';
        return $validation;
    }

    // Check storage space
    if (isset($storageStatus['free_space_gb'])) {
        if ($storageStatus['free_space_gb'] < 5) {
            $validation['valid'] = false;
            $validation['score'] -= 50;
            $validation['issues'][] = 'Insufficient storage space';
        } elseif ($storageStatus['free_space_gb'] < 10) {
            $validation['score'] -= 20;
            $validation['issues'][] = 'Low storage space';
        }
    }

    // Check storage speed
    if (isset($storageStatus['write_speed_mbps'])) {
        if ($storageStatus['write_speed_mbps'] < 50) {
            $validation['score'] -= 15;
            $validation['issues'][] = 'Storage write speed too slow';
        }
    }

    return $validation;
}
```

---

## **🧪 TESTING STRATEGY**

### **Unit Testing:**
- **Hardware compatibility** testing
- **Hardware status validation** testing
- **Hardware requirements** testing
- **Performance testing** testing

### **Integration Testing:**
- **API endpoint** testing
- **Database integration** testing
- **Validation logic** testing
- **Error handling** testing

### **Hardware Testing:**
- **Jetson compatibility** testing
- **CUDA compatibility** testing
- **TensorRT compatibility** testing
- **OpenCV compatibility** testing

---

## **📊 SUCCESS CRITERIA**

### **Functional Success:**
- ✅ Hardware compatibility check
- ✅ Hardware status validation
- ✅ Hardware requirements check
- ✅ Hardware performance testing
- ✅ Hardware configuration validation
- ✅ Hardware error detection
- ✅ Hardware recommendations

### **Technical Success:**
- ✅ RESTful API endpoints
- ✅ Hardware database
- ✅ Validation rules engine
- ✅ Performance metrics
- ✅ Error reporting
- ✅ Hardware profiles

### **Integration Success:**
- ✅ RVM-Jetson integration
- ✅ Admin dashboard integration
- ✅ Database integration
- ✅ API documentation

---

## **⏱️ ESTIMATED TIMELINE**

### **Week 1: Core API Development**
- **Day 1-2**: Hardware compatibility API
- **Day 3-4**: Hardware status validation API
- **Day 5**: Hardware requirements API

### **Week 2: Advanced Features**
- **Day 1-2**: Performance testing API
- **Day 3-4**: Hardware profiles
- **Day 5**: Validation rules engine

### **Week 3: Database & Integration**
- **Day 1-2**: Hardware database
- **Day 3-4**: RVM-Jetson integration
- **Day 5**: Admin dashboard integration

### **Week 4: Testing & Documentation**
- **Day 1-2**: Unit testing
- **Day 3-4**: Integration testing
- **Day 5**: Documentation

---

## **📁 DELIVERABLES**

### **Code Files:**
- `HardwareValidationController.php`
- Database migrations
- Model classes
- Validation logic

### **Documentation:**
- API documentation
- Hardware compatibility guide
- Validation rules guide
- Troubleshooting guide

### **Testing:**
- Unit tests
- Integration tests
- Hardware tests
- Performance tests

---

**Status**: 📋 **READY FOR IMPLEMENTATION**  
**Estimated Time**: 4 weeks  
**Difficulty**: Advanced  
**Dependencies**: Database schema, Hardware profiles, RVM-Jetson integration