# TASK 01: UPDATE PING LOGIC UNTUK TEST PORT 5001

**Tanggal**: 2025-01-20  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 2-3 jam  

---

## **📋 DESKRIPSI TUGAS**

Update ping logic di MyRVM Platform untuk test port 5001 (Remote Access Controller) pada Jetson Orin.

### **🎯 TUJUAN:**
- Update `RvmController.php` untuk test port 5001
- Implementasi ping logic yang lebih akurat
- Test connectivity ke Remote Access Controller

---

## **🔧 IMPLEMENTASI**

### **1. Update RvmController.php**

#### **A. Update performPing Method:**
```php
private function performPing($ip, $port = 8000)
{
    $startTime = microtime(true);
    
    // Handle dummy data (0.0.0.0)
    if ($ip === '0.0.0.0' || $ip === 'localhost' || $ip === '127.0.0.1') {
        $responseTime = round((microtime(true) - $startTime) * 1000, 2);
        return [
            'success' => true,
            'message' => 'Dummy data - No actual connection test',
            'response_time' => $responseTime,
            'is_dummy' => true
        ];
    }
    
    // Test multiple ports
    $ports = [8000, 5000, 5001]; // RVM API, Camera, Remote Access Controller
    $results = [];
    
    foreach ($ports as $testPort) {
        $portStartTime = microtime(true);
        
        try {
            $connection = @fsockopen($ip, $testPort, $errno, $errstr, 5);
            
            if ($connection) {
                $responseTime = round((microtime(true) - $portStartTime) * 1000, 2);
                fclose($connection);
                
                $results[$testPort] = [
                    'success' => true,
                    'message' => "Port $testPort: Connection successful",
                    'response_time' => $responseTime,
                    'service' => $this->getServiceName($testPort)
                ];
            } else {
                $responseTime = round((microtime(true) - $portStartTime) * 1000, 2);
                $results[$testPort] = [
                    'success' => false,
                    'message' => "Port $testPort: Connection failed: $errstr ($errno)",
                    'response_time' => $responseTime,
                    'service' => $this->getServiceName($testPort)
                ];
            }
        } catch (\Exception $e) {
            $responseTime = round((microtime(true) - $portStartTime) * 1000, 2);
            $results[$testPort] = [
                'success' => false,
                'message' => "Port $testPort: Connection error: " . $e->getMessage(),
                'response_time' => $responseTime,
                'service' => $this->getServiceName($testPort)
            ];
        }
    }
    
    // Determine overall success
    $overallSuccess = !empty(array_filter($results, function($result) {
        return $result['success'];
    }));
    
    return [
        'success' => $overallSuccess,
        'message' => 'Multi-port connectivity test',
        'response_time' => round((microtime(true) - $startTime) * 1000, 2),
        'is_dummy' => false,
        'ports' => $results
    ];
}

private function getServiceName($port)
{
    $services = [
        8000 => 'RVM API',
        5000 => 'Camera Service',
        5001 => 'Remote Access Controller'
    ];
    
    return $services[$port] ?? "Port $port";
}
```

#### **B. Update ping Method:**
```php
public function ping(Request $request, $id)
{
    try {
        $rvm = ReverseVendingMachine::findOrFail($id);
        
        if (!$rvm->ip_address) {
            return response()->json([
                'success' => false,
                'message' => 'RVM IP address not configured'
            ], 400);
        }
        
        $pingResult = $this->performPing($rvm->ip_address, $rvm->port ?? 8000);
        
        // Update RVM connection status
        $rvm->update([
            'connection_status' => $pingResult['success'] ? 'connected' : 'disconnected',
            'last_ping' => now()
        ]);
        
        return response()->json([
            'success' => true,
            'data' => [
                'rvm_id' => $rvm->id,
                'ip_address' => $rvm->ip_address,
                'ping_result' => $pingResult
            ]
        ]);
        
    } catch (\Exception $e) {
        return response()->json([
            'success' => false,
            'message' => 'Ping failed: ' . $e->getMessage()
        ], 500);
    }
}
```

### **2. Update Frontend JavaScript**

#### **A. Update pingRVM Function:**
```javascript
function pingRVM(rvmId) {
    const statusElement = document.querySelector(`[data-rvm-id="${rvmId}"] .connection-status`);
    
    // Show loading state
    statusElement.innerHTML = '<i class="fas fa-spinner fa-spin text-warning"></i> Testing...';
    
    fetch(`/admin/rvm/${rvmId}/ping`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const pingResult = data.data.ping_result;
            
            if (pingResult.success) {
                // Show successful connection
                statusElement.innerHTML = '<i class="fas fa-check-circle text-success"></i> Connected';
                
                // Show detailed port information
                if (pingResult.ports) {
                    let portInfo = '<div class="port-details mt-2">';
                    for (const [port, result] of Object.entries(pingResult.ports)) {
                        const icon = result.success ? 'check-circle text-success' : 'times-circle text-danger';
                        portInfo += `<small class="d-block"><i class="fas fa-${icon}"></i> ${result.service}: ${result.response_time}ms</small>`;
                    }
                    portInfo += '</div>';
                    statusElement.innerHTML += portInfo;
                }
            } else {
                statusElement.innerHTML = '<i class="fas fa-times-circle text-danger"></i> Disconnected';
            }
        } else {
            statusElement.innerHTML = '<i class="fas fa-exclamation-triangle text-warning"></i> Error';
        }
    })
    .catch(error => {
        console.error('Ping error:', error);
        statusElement.innerHTML = '<i class="fas fa-exclamation-triangle text-warning"></i> Error';
    });
}
```

---

## **🧪 TESTING**

### **1. Test Cases:**

#### **A. Dummy IP Test:**
- IP: `0.0.0.0`
- Expected: Success dengan message "Dummy data"

#### **B. Real IP Test:**
- IP: `172.28.93.97`
- Expected: Test ports 8000, 5000, 5001
- Expected: Return detailed port results

#### **C. Invalid IP Test:**
- IP: `192.168.1.999`
- Expected: All ports failed

### **2. Test Commands:**
```bash
# Test ping endpoint
curl -X POST http://localhost:8001/admin/rvm/1/ping \
  -H "Content-Type: application/json" \
  -H "X-CSRF-TOKEN: your_token_here"
```

---

## **📋 CHECKLIST**

- [ ] Update `performPing` method dengan multi-port testing
- [ ] Update `ping` method untuk handle new response format
- [ ] Update frontend JavaScript untuk display port details
- [ ] Test dengan dummy IP (0.0.0.0)
- [ ] Test dengan real IP (172.28.93.97)
- [ ] Test dengan invalid IP
- [ ] Update database connection_status field
- [ ] Verify UI updates correctly

---

## **📝 NOTES**

- Port 5001 adalah Remote Access Controller di Jetson Orin
- Port 5000 adalah Camera Service
- Port 8000 adalah RVM API (default)
- Response time diukur dalam milliseconds
- Service names ditampilkan untuk user clarity

---

**Status**: ✅ **COMPLETED**  
**Completed**: 2025-01-20  
**Next**: Implementasi Remote Access API Endpoints
