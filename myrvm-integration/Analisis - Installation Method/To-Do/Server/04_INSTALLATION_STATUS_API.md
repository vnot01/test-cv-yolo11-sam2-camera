# TASK 04: INSTALLATION STATUS API

**Tanggal**: 2025-09-21  
**Versi**: 1.0.0  
**Status**: 📋 PLANNING  
**Priority**: HIGH  

---

## **🎯 OBJECTIVE**

Membuat Installation Status API untuk tracking installation progress, installation status updates, dan installation error reporting untuk RVM-Jetson.

---

## **📋 REQUIREMENTS**

### **Functional Requirements:**
- **Installation Progress Tracking** (real-time progress updates)
- **Installation Status Updates** (status changes, milestones)
- **Installation Error Reporting** (error logging, troubleshooting)
- **Installation History** (complete installation log)
- **Installation Rollback** (rollback to previous state)
- **Installation Validation** (post-installation verification)
- **Installation Notifications** (status alerts, completion notifications)

### **Technical Requirements:**
- **RESTful API** endpoints
- **Real-time Updates** (WebSocket, Server-Sent Events)
- **Installation Database** (progress tracking, status history)
- **Error Logging** (detailed error information)
- **Status Management** (state machine, status transitions)
- **Notification System** (email, webhook, dashboard alerts)

---

## **🔧 IMPLEMENTATION PLAN**

### **1. Installation Status API Endpoints**

#### **A. Installation Progress Tracking**
```php
// Endpoint: POST /api/v2/installation/progress
Route::post('/installation/progress', [InstallationStatusController::class, 'updateProgress']);
```

#### **B. Installation Status Updates**
```php
// Endpoint: PUT /api/v2/installation/status
Route::put('/installation/status', [InstallationStatusController::class, 'updateStatus']);
```

#### **C. Installation Error Reporting**
```php
// Endpoint: POST /api/v2/installation/error
Route::post('/installation/error', [InstallationStatusController::class, 'reportError']);
```

#### **D. Installation History**
```php
// Endpoint: GET /api/v2/installation/history/{rvmId}
Route::get('/installation/history/{rvmId}', [InstallationStatusController::class, 'getHistory']);
```

---

## **📝 DETAILED IMPLEMENTATION**

### **1. InstallationStatusController**

#### **Controller Setup:**
```php
<?php

namespace App\Http\Controllers\Api\V2;

use App\Http\Controllers\Controller;
use App\Models\InstallationStatus;
use App\Models\InstallationProgress;
use App\Models\InstallationError;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Facades\DB;

class InstallationStatusController extends Controller
{
    public function __construct()
    {
        $this->middleware('auth:sanctum');
        $this->middleware('role:super-admin|admin|tenant');
    }

    /**
     * Update installation progress
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function updateProgress(Request $request): JsonResponse
    {
        try {
            $validator = Validator::make($request->all(), [
                'rvm_id' => 'required|integer|exists:reverse_vending_machines,id',
                'step' => 'required|string|max:255',
                'progress' => 'required|integer|min:0|max:100',
                'message' => 'nullable|string|max:1000',
                'details' => 'nullable|array',
                'estimated_completion' => 'nullable|date',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Validation failed',
                    'errors' => $validator->errors()
                ], 422);
            }

            $data = $request->all();
            
            // Create or update installation progress
            $progress = InstallationProgress::updateOrCreate(
                [
                    'rvm_id' => $data['rvm_id'],
                    'step' => $data['step']
                ],
                [
                    'progress' => $data['progress'],
                    'message' => $data['message'] ?? null,
                    'details' => json_encode($data['details'] ?? []),
                    'estimated_completion' => $data['estimated_completion'] ?? null,
                    'updated_at' => now()
                ]
            );

            // Update overall installation status
            $this->updateOverallStatus($data['rvm_id']);

            // Send real-time update
            $this->sendRealTimeUpdate($data['rvm_id'], 'progress', $progress);

            return response()->json([
                'success' => true,
                'message' => 'Installation progress updated',
                'data' => [
                    'step' => $progress->step,
                    'progress' => $progress->progress,
                    'message' => $progress->message,
                    'updated_at' => $progress->updated_at
                ]
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to update installation progress',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Update installation status
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function updateStatus(Request $request): JsonResponse
    {
        try {
            $validator = Validator::make($request->all(), [
                'rvm_id' => 'required|integer|exists:reverse_vending_machines,id',
                'status' => 'required|in:pending,installing,completed,failed,rollback',
                'message' => 'nullable|string|max:1000',
                'details' => 'nullable|array',
                'completed_at' => 'nullable|date',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Validation failed',
                    'errors' => $validator->errors()
                ], 422);
            }

            $data = $request->all();
            
            // Update installation status
            $status = InstallationStatus::updateOrCreate(
                ['rvm_id' => $data['rvm_id']],
                [
                    'status' => $data['status'],
                    'message' => $data['message'] ?? null,
                    'details' => json_encode($data['details'] ?? []),
                    'completed_at' => $data['completed_at'] ?? null,
                    'updated_at' => now()
                ]
            );

            // Send real-time update
            $this->sendRealTimeUpdate($data['rvm_id'], 'status', $status);

            // Send notifications if needed
            $this->sendStatusNotifications($data['rvm_id'], $data['status']);

            return response()->json([
                'success' => true,
                'message' => 'Installation status updated',
                'data' => [
                    'status' => $status->status,
                    'message' => $status->message,
                    'updated_at' => $status->updated_at
                ]
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to update installation status',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Report installation error
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function reportError(Request $request): JsonResponse
    {
        try {
            $validator = Validator::make($request->all(), [
                'rvm_id' => 'required|integer|exists:reverse_vending_machines,id',
                'error_type' => 'required|string|max:100',
                'error_message' => 'required|string|max:1000',
                'error_code' => 'nullable|string|max:50',
                'step' => 'nullable|string|max:255',
                'details' => 'nullable|array',
                'stack_trace' => 'nullable|string',
                'severity' => 'required|in:low,medium,high,critical',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Validation failed',
                    'errors' => $validator->errors()
                ], 422);
            }

            $data = $request->all();
            
            // Create installation error record
            $error = InstallationError::create([
                'rvm_id' => $data['rvm_id'],
                'error_type' => $data['error_type'],
                'error_message' => $data['error_message'],
                'error_code' => $data['error_code'] ?? null,
                'step' => $data['step'] ?? null,
                'details' => json_encode($data['details'] ?? []),
                'stack_trace' => $data['stack_trace'] ?? null,
                'severity' => $data['severity'],
                'created_at' => now()
            ]);

            // Update installation status to failed if critical error
            if ($data['severity'] === 'critical') {
                $this->updateStatus(new Request([
                    'rvm_id' => $data['rvm_id'],
                    'status' => 'failed',
                    'message' => 'Installation failed due to critical error',
                    'details' => ['error_id' => $error->id]
                ]));
            }

            // Send real-time update
            $this->sendRealTimeUpdate($data['rvm_id'], 'error', $error);

            // Send error notifications
            $this->sendErrorNotifications($data['rvm_id'], $error);

            return response()->json([
                'success' => true,
                'message' => 'Installation error reported',
                'data' => [
                    'error_id' => $error->id,
                    'error_type' => $error->error_type,
                    'severity' => $error->severity,
                    'created_at' => $error->created_at
                ]
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to report installation error',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get installation history
     *
     * @param Request $request
     * @param int $rvmId
     * @return JsonResponse
     */
    public function getHistory(Request $request, int $rvmId): JsonResponse
    {
        try {
            // Get installation status
            $status = InstallationStatus::where('rvm_id', $rvmId)->first();
            
            // Get installation progress
            $progress = InstallationProgress::where('rvm_id', $rvmId)
                ->orderBy('updated_at', 'desc')
                ->get();
            
            // Get installation errors
            $errors = InstallationError::where('rvm_id', $rvmId)
                ->orderBy('created_at', 'desc')
                ->get();

            // Format progress data
            $progressData = $progress->map(function ($item) {
                return [
                    'step' => $item->step,
                    'progress' => $item->progress,
                    'message' => $item->message,
                    'details' => json_decode($item->details, true),
                    'estimated_completion' => $item->estimated_completion,
                    'updated_at' => $item->updated_at
                ];
            });

            // Format errors data
            $errorsData = $errors->map(function ($item) {
                return [
                    'id' => $item->id,
                    'error_type' => $item->error_type,
                    'error_message' => $item->error_message,
                    'error_code' => $item->error_code,
                    'step' => $item->step,
                    'severity' => $item->severity,
                    'details' => json_decode($item->details, true),
                    'created_at' => $item->created_at
                ];
            });

            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvmId,
                    'status' => $status ? [
                        'status' => $status->status,
                        'message' => $status->message,
                        'details' => json_decode($status->details, true),
                        'completed_at' => $status->completed_at,
                        'updated_at' => $status->updated_at
                    ] : null,
                    'progress' => $progressData,
                    'errors' => $errorsData,
                    'summary' => [
                        'total_steps' => $progress->count(),
                        'completed_steps' => $progress->where('progress', 100)->count(),
                        'total_errors' => $errors->count(),
                        'critical_errors' => $errors->where('severity', 'critical')->count(),
                        'last_updated' => $progress->max('updated_at')
                    ]
                ]
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get installation history',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get installation status
     *
     * @param Request $request
     * @param int $rvmId
     * @return JsonResponse
     */
    public function getStatus(Request $request, int $rvmId): JsonResponse
    {
        try {
            // Get current installation status
            $status = InstallationStatus::where('rvm_id', $rvmId)->first();
            
            // Get current progress
            $progress = InstallationProgress::where('rvm_id', $rvmId)
                ->orderBy('updated_at', 'desc')
                ->first();

            // Get recent errors
            $recentErrors = InstallationError::where('rvm_id', $rvmId)
                ->where('created_at', '>=', now()->subHours(24))
                ->orderBy('created_at', 'desc')
                ->limit(5)
                ->get();

            return response()->json([
                'success' => true,
                'data' => [
                    'rvm_id' => $rvmId,
                    'status' => $status ? [
                        'status' => $status->status,
                        'message' => $status->message,
                        'updated_at' => $status->updated_at
                    ] : null,
                    'progress' => $progress ? [
                        'step' => $progress->step,
                        'progress' => $progress->progress,
                        'message' => $progress->message,
                        'updated_at' => $progress->updated_at
                    ] : null,
                    'recent_errors' => $recentErrors->map(function ($error) {
                        return [
                            'error_type' => $error->error_type,
                            'error_message' => $error->error_message,
                            'severity' => $error->severity,
                            'created_at' => $error->created_at
                        ];
                    })
                ]
            ], 200);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to get installation status',
                'error' => $e->getMessage()
            ], 500);
        }
    }
}
```

### **2. Helper Methods**

#### **Status Management:**
```php
/**
 * Update overall installation status
 *
 * @param int $rvmId
 * @return void
 */
private function updateOverallStatus(int $rvmId): void
{
    // Get all progress steps
    $progressSteps = InstallationProgress::where('rvm_id', $rvmId)->get();
    
    if ($progressSteps->isEmpty()) {
        return;
    }
    
    // Calculate overall progress
    $totalProgress = $progressSteps->sum('progress');
    $averageProgress = $totalProgress / $progressSteps->count();
    
    // Determine overall status
    $overallStatus = 'installing';
    if ($averageProgress >= 100) {
        $overallStatus = 'completed';
    } elseif ($averageProgress <= 0) {
        $overallStatus = 'pending';
    }
    
    // Update overall status
    InstallationStatus::updateOrCreate(
        ['rvm_id' => $rvmId],
        [
            'status' => $overallStatus,
            'message' => "Overall progress: {$averageProgress}%",
            'details' => json_encode([
                'total_steps' => $progressSteps->count(),
                'average_progress' => $averageProgress,
                'last_updated' => now()
            ]),
            'updated_at' => now()
        ]
    );
}

/**
 * Send real-time update
 *
 * @param int $rvmId
 * @param string $type
 * @param mixed $data
 * @return void
 */
private function sendRealTimeUpdate(int $rvmId, string $type, $data): void
{
    // This would integrate with WebSocket or Server-Sent Events
    // For now, we'll just log the update
    \Log::info("Real-time update for RVM {$rvmId}", [
        'type' => $type,
        'data' => $data
    ]);
}

/**
 * Send status notifications
 *
 * @param int $rvmId
 * @param string $status
 * @return void
 */
private function sendStatusNotifications(int $rvmId, string $status): void
{
    // Send notifications based on status
    switch ($status) {
        case 'completed':
            $this->sendCompletionNotification($rvmId);
            break;
        case 'failed':
            $this->sendFailureNotification($rvmId);
            break;
        case 'rollback':
            $this->sendRollbackNotification($rvmId);
            break;
    }
}

/**
 * Send error notifications
 *
 * @param int $rvmId
 * @param InstallationError $error
 * @return void
 */
private function sendErrorNotifications(int $rvmId, InstallationError $error): void
{
    // Send notifications based on error severity
    switch ($error->severity) {
        case 'critical':
            $this->sendCriticalErrorNotification($rvmId, $error);
            break;
        case 'high':
            $this->sendHighErrorNotification($rvmId, $error);
            break;
        case 'medium':
            $this->sendMediumErrorNotification($rvmId, $error);
            break;
    }
}

/**
 * Send completion notification
 *
 * @param int $rvmId
 * @return void
 */
private function sendCompletionNotification(int $rvmId): void
{
    // Send email notification
    // Send webhook notification
    // Update dashboard
    \Log::info("Installation completed for RVM {$rvmId}");
}

/**
 * Send failure notification
 *
 * @param int $rvmId
 * @return void
 */
private function sendFailureNotification(int $rvmId): void
{
    // Send email notification
    // Send webhook notification
    // Update dashboard
    \Log::error("Installation failed for RVM {$rvmId}");
}

/**
 * Send rollback notification
 *
 * @param int $rvmId
 * @return void
 */
private function sendRollbackNotification(int $rvmId): void
{
    // Send email notification
    // Send webhook notification
    // Update dashboard
    \Log::warning("Installation rollback for RVM {$rvmId}");
}

/**
 * Send critical error notification
 *
 * @param int $rvmId
 * @param InstallationError $error
 * @return void
 */
private function sendCriticalErrorNotification(int $rvmId, InstallationError $error): void
{
    // Send immediate email notification
    // Send webhook notification
    // Update dashboard
    \Log::critical("Critical installation error for RVM {$rvmId}: {$error->error_message}");
}

/**
 * Send high error notification
 *
 * @param int $rvmId
 * @param InstallationError $error
 * @return void
 */
private function sendHighErrorNotification(int $rvmId, InstallationError $error): void
{
    // Send email notification
    // Update dashboard
    \Log::error("High severity installation error for RVM {$rvmId}: {$error->error_message}");
}

/**
 * Send medium error notification
 *
 * @param int $rvmId
 * @param InstallationError $error
 * @return void
 */
private function sendMediumErrorNotification(int $rvmId, InstallationError $error): void
{
    // Update dashboard
    \Log::warning("Medium severity installation error for RVM {$rvmId}: {$error->error_message}");
}
```

---

## **🗄️ DATABASE SCHEMA**

### **1. Installation Status Table**
```sql
CREATE TABLE installation_status (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    rvm_id BIGINT UNSIGNED NOT NULL,
    status ENUM('pending', 'installing', 'completed', 'failed', 'rollback') NOT NULL DEFAULT 'pending',
    message TEXT NULL,
    details JSON NULL,
    completed_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id) ON DELETE CASCADE,
    
    INDEX idx_rvm_status (rvm_id, status),
    INDEX idx_created_at (created_at)
);
```

### **2. Installation Progress Table**
```sql
CREATE TABLE installation_progress (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    rvm_id BIGINT UNSIGNED NOT NULL,
    step VARCHAR(255) NOT NULL,
    progress INT NOT NULL DEFAULT 0,
    message TEXT NULL,
    details JSON NULL,
    estimated_completion TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_rvm_step (rvm_id, step),
    INDEX idx_rvm_progress (rvm_id, progress),
    INDEX idx_updated_at (updated_at)
);
```

### **3. Installation Error Table**
```sql
CREATE TABLE installation_errors (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    rvm_id BIGINT UNSIGNED NOT NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    error_code VARCHAR(50) NULL,
    step VARCHAR(255) NULL,
    details JSON NULL,
    stack_trace TEXT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP NULL DEFAULT NULL,
    
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id) ON DELETE CASCADE,
    
    INDEX idx_rvm_severity (rvm_id, severity),
    INDEX idx_created_at (created_at),
    INDEX idx_error_type (error_type)
);
```

---

## **🧪 TESTING STRATEGY**

### **Unit Testing:**
- **Installation progress** testing
- **Installation status** testing
- **Installation error** testing
- **Notification system** testing

### **Integration Testing:**
- **API endpoint** testing
- **Database integration** testing
- **Real-time updates** testing
- **Notification delivery** testing

### **System Testing:**
- **End-to-end** installation tracking
- **Error handling** testing
- **Status transitions** testing
- **Performance** testing

---

## **📊 SUCCESS CRITERIA**

### **Functional Success:**
- ✅ Installation progress tracking
- ✅ Installation status updates
- ✅ Installation error reporting
- ✅ Installation history
- ✅ Installation rollback
- ✅ Installation validation
- ✅ Installation notifications

### **Technical Success:**
- ✅ RESTful API endpoints
- ✅ Real-time updates
- ✅ Installation database
- ✅ Error logging
- ✅ Status management
- ✅ Notification system

### **Integration Success:**
- ✅ RVM-Jetson integration
- ✅ Admin dashboard integration
- ✅ WebSocket integration
- ✅ Database integration

---

## **⏱️ ESTIMATED TIMELINE**

### **Week 1: Core API Development**
- **Day 1-2**: Installation progress API
- **Day 3-4**: Installation status API
- **Day 5**: Installation error API

### **Week 2: Advanced Features**
- **Day 1-2**: Installation history API
- **Day 3-4**: Real-time updates
- **Day 5**: Notification system

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
- `InstallationStatusController.php`
- Database migrations
- Model classes
- Notification system

### **Documentation:**
- API documentation
- Installation tracking guide
- Error handling guide
- Notification guide

### **Testing:**
- Unit tests
- Integration tests
- System tests
- Performance tests

---

**Status**: 📋 **READY FOR IMPLEMENTATION**  
**Estimated Time**: 4 weeks  
**Difficulty**: Advanced  
**Dependencies**: Database schema, Notification system, RVM-Jetson integration
