#!/bin/bash

# TESTING SCRIPT FOR RVM LOCATION A
# This script runs comprehensive tests for Location A installation
# Refrence: 
# /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/docs/INSTALLATION_GUIDE_LOCATION_A.md

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
RVM_ID=5
LOCATION_NAME="Location A"
SERVER_URL="http://172.28.233.83:8001"
TEST_RESULTS_FILE="/tmp/myrvm_test_results_$(date +%Y%m%d_%H%M%S).log"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

print_test() {
    echo -e "${BLUE}[TEST] $1${NC}"
}

# Function to run test and record result
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    print_test "Running: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        print_status "✅ PASSED: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        print_error "❌ FAILED: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to test system requirements
test_system_requirements() {
    print_status "Testing system requirements..."
    
    run_test "Python 3.8+ installed" "python3 --version | grep -E 'Python 3\.(8|9|10|11|12)'"
    run_test "Virtual environment exists" "[ -d 'venv' ]"
    run_test "Git repository cloned" "[ -d '.git' ]"
    run_test "Configuration file exists" "[ -f 'config/production_config.json' ]"
    run_test "System dependencies installed" "command -v chromium-browser"
    run_test "Network connectivity" "ping -c 1 8.8.8.8"
}

# Function to test hardware components
test_hardware_components() {
    print_status "Testing hardware components..."
    
    run_test "Camera device exists" "[ -e '/dev/video0' ]"
    run_test "Display available" "xrandr --listmonitors >/dev/null"
    run_test "Touch device exists" "[ -e '/dev/input/event0' ]"
    run_test "GPIO available" "[ -e '/dev/gpiochip0' ]"
    run_test "Camera permissions" "test -r /dev/video0"
    run_test "GPIO permissions" "test -r /dev/gpiochip0"
}

# Function to test application components
test_application_components() {
    print_status "Testing application components..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    run_test "Python dependencies installed" "python3 -c 'import requests, flask, cv2, numpy, psutil'"
    run_test "Configuration manager import" "python3 -c 'from config.enhanced_config_manager import EnhancedConfigurationManager'"
    run_test "API client import" "python3 -c 'from api_client.enhanced_myrvm_api_client import EnhancedMyRVMAPIClient'"
    run_test "Hardware detector import" "python3 -c 'from hardware.hardware_detector import HardwareDetector'"
    run_test "GUI client import" "python3 -c 'from gui.gui_client import GUIClient'"
    run_test "Metrics sender import" "python3 -c 'from monitoring.metrics_sender import MetricsSender'"
}

# Function to test configuration
test_configuration() {
    print_status "Testing configuration..."
    
    run_test "Configuration file valid JSON" "python3 -c 'import json; json.load(open(\"config/production_config.json\"))'"
    run_test "RVM ID configured correctly" "python3 -c 'import json; config = json.load(open(\"config/production_config.json\")); assert config[\"remote_access\"][\"rvm_id\"] == $RVM_ID'"
    run_test "Server URL configured" "python3 -c 'import json; config = json.load(open(\"config/production_config.json\")); assert \"server_url\" in config[\"remote_access\"]'"
    run_test "Services configuration" "python3 -c 'import json; config = json.load(open(\"config/production_config.json\")); assert \"services\" in config'"
    run_test "Remote access configuration" "python3 -c 'import json; config = json.load(open(\"config/production_config.json\")); assert \"remote_access\" in config'"
}

# Function to test network connectivity
test_network_connectivity() {
    print_status "Testing network connectivity..."
    
    run_test "Server reachable" "curl -s --connect-timeout 10 $SERVER_URL/api/health-check"
    run_test "DNS resolution" "nslookup 172.28.233.83"
    run_test "Port 8001 accessible" "nc -z 172.28.233.83 8001"
    run_test "HTTP response" "curl -s -o /dev/null -w '%{http_code}' $SERVER_URL/api/health-check | grep -E '^[23][0-9][0-9]$'"
}

# Function to test systemd service
test_systemd_service() {
    print_status "Testing systemd service..."
    
    run_test "Service file exists" "[ -f '/etc/systemd/system/myrvm-application.service' ]"
    run_test "Service enabled" "sudo systemctl is-enabled myrvm-application.service"
    run_test "Service can start" "sudo systemctl start myrvm-application.service"
    run_test "Service running" "sudo systemctl is-active myrvm-application.service"
    run_test "Service can stop" "sudo systemctl stop myrvm-application.service"
}

# Function to test GUI components
test_gui_components() {
    print_status "Testing GUI components..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    run_test "GUI client can initialize" "python3 -c 'from gui.gui_client import GUIClient; client = GUIClient(rvm_id=\"test\", host=\"127.0.0.1\", port=5002); print(\"GUI client initialized\")'"
    run_test "QR code generator works" "python3 -c 'from gui.qr_code_generator import QRCodeGenerator; generator = QRCodeGenerator(); print(\"QR generator initialized\")'"
    run_test "User authentication works" "python3 -c 'from gui.user_authentication import UserAuthentication; auth = UserAuthentication(); print(\"User auth initialized\")'"
}

# Function to test monitoring components
test_monitoring_components() {
    print_status "Testing monitoring components..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    run_test "Hardware metrics collector" "python3 -c 'from monitoring.hardware_metrics_collector import HardwareMetricsCollector; collector = HardwareMetricsCollector(); print(\"Hardware collector initialized\")'"
    run_test "Application metrics collector" "python3 -c 'from monitoring.application_metrics_collector import ApplicationMetricsCollector; collector = ApplicationMetricsCollector(); print(\"App collector initialized\")'"
    run_test "Network info collector" "python3 -c 'from monitoring.network_info_collector import NetworkInfoCollector; collector = NetworkInfoCollector(); print(\"Network collector initialized\")'"
    run_test "Metrics sender" "python3 -c 'from monitoring.metrics_sender import MetricsSender; sender = MetricsSender(\"http://localhost:8001\", 1, \"test\"); print(\"Metrics sender initialized\")'"
}

# Function to test remote components
test_remote_components() {
    print_status "Testing remote components..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    run_test "Command receiver" "python3 -c 'from remote.command_receiver import RemoteCommandReceiver; receiver = RemoteCommandReceiver(\"http://localhost:8001\", 1, \"test\"); print(\"Command receiver initialized\")'"
    run_test "Command executor" "python3 -c 'from remote.command_executor import RemoteCommandExecutor; executor = RemoteCommandExecutor(); print(\"Command executor initialized\")'"
}

# Function to test integration
test_integration() {
    print_status "Testing integration..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    run_test "Main application can import" "python3 -c 'from main_application import MyRVMApplication; print(\"Main app imported\")'"
    run_test "Service integration can import" "python3 -c 'from services.service_integration import MyRVMServiceIntegration; print(\"Service integration imported\")'"
    run_test "Configuration manager can import" "python3 -c 'from config.enhanced_config_manager import EnhancedConfigurationManager; print(\"Config manager imported\")'"
}

# Function to run comprehensive test
run_comprehensive_test() {
    print_status "Running comprehensive integration test..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    if python3 test_analisis3_integration.py >/dev/null 2>&1; then
        print_status "✅ PASSED: Comprehensive integration test"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_error "❌ FAILED: Comprehensive integration test"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

# Function to generate test report
generate_test_report() {
    print_status "Generating test report..."
    
    cat > "$TEST_RESULTS_FILE" << EOF
MyRVM Integration Test Report - $LOCATION_NAME
Generated: $(date)
RVM ID: $RVM_ID

Test Summary:
- Total Tests: $TESTS_TOTAL
- Passed: $TESTS_PASSED
- Failed: $TESTS_FAILED
- Success Rate: $(( (TESTS_PASSED * 100) / TESTS_TOTAL ))%

Test Categories:
1. System Requirements
2. Hardware Components
3. Application Components
4. Configuration
5. Network Connectivity
6. Systemd Service
7. GUI Components
8. Monitoring Components
9. Remote Components
10. Integration

Detailed Results:
$(cat /tmp/myrvm_test_output.log 2>/dev/null || echo "No detailed output available")

Recommendations:
EOF
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo "- All tests passed! System is ready for production." >> "$TEST_RESULTS_FILE"
    else
        echo "- $TESTS_FAILED tests failed. Please review and fix issues before production deployment." >> "$TEST_RESULTS_FILE"
    fi
    
    print_status "Test report generated: $TEST_RESULTS_FILE"
}

# Function to display test summary
display_test_summary() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  TEST RESULTS SUMMARY${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Test Statistics:${NC}"
    echo -e "  Total Tests: $TESTS_TOTAL"
    echo -e "  Passed: $TESTS_PASSED"
    echo -e "  Failed: $TESTS_FAILED"
    echo -e "  Success Rate: $(( (TESTS_PASSED * 100) / TESTS_TOTAL ))%"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
        echo -e "${GREEN}System is ready for production deployment.${NC}"
    else
        echo -e "${RED}⚠️  $TESTS_FAILED TESTS FAILED${NC}"
        echo -e "${YELLOW}Please review failed tests and fix issues before production.${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Test Report:${NC} $TEST_RESULTS_FILE"
    echo ""
}

# Main test function
main() {
    print_status "Starting comprehensive testing for $LOCATION_NAME"
    
    # Redirect output to log file
    exec > >(tee -a /tmp/myrvm_test_output.log)
    exec 2>&1
    
    test_system_requirements
    test_hardware_components
    test_application_components
    test_configuration
    test_network_connectivity
    test_systemd_service
    test_gui_components
    test_monitoring_components
    test_remote_components
    test_integration
    run_comprehensive_test
    
    generate_test_report
    display_test_summary
    
    print_status "Testing completed!"
    
    # Exit with appropriate code
    if [ $TESTS_FAILED -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
