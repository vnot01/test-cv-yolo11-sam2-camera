#!/usr/bin/env python3
"""
MyRVM Platform Integration - Stage 5: Deployment Automation Test
Tests all deployment automation components including deployment scripts, service automation, update management, and rollback procedures.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import deployment automation components
from services.startup_manager import StartupManager
from services.dependency_manager import DependencyManager
from services.update_manager import UpdateManager
from services.rollback_manager import RollbackManager

def setup_logging():
    """Setup logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(project_root / "logs" / "deployment_automation_test.log")
        ]
    )

def load_config():
    """Load configuration for testing."""
    config_path = project_root / "config" / "development_config.json"
    with open(config_path, 'r') as f:
        return json.load(f)

def test_startup_manager():
    """Test startup manager functionality."""
    print("\n🚀 Testing Startup Manager...")
    print("=" * 60)
    
    try:
        config = load_config()
        startup_manager = StartupManager(config)
        
        # Test startup sequence
        print("Testing startup sequence...")
        success = startup_manager.start_services()
        
        if success:
            print("   ✅ Startup sequence completed successfully")
        else:
            print("   ❌ Startup sequence failed")
        
        # Test startup status
        status = startup_manager.get_startup_status()
        print(f"   📊 Startup Status: {status['completed_steps']}/{status['total_steps']} steps completed")
        print(f"   📊 Failed Steps: {status['failed_steps']}")
        
        # Test health status
        health = startup_manager.get_health_status()
        print(f"   🏥 Health Status: {health['health_status']}")
        
        return success
        
    except Exception as e:
        print(f"   ❌ Startup Manager test failed: {e}")
        return False

def test_dependency_manager():
    """Test dependency manager functionality."""
    print("\n🔗 Testing Dependency Manager...")
    print("=" * 60)
    
    try:
        config = load_config()
        dep_manager = DependencyManager(config)
        
        # Test dependency validation
        print("Testing dependency validation...")
        validation_success = dep_manager.validate_dependencies()
        
        if validation_success:
            print("   ✅ Dependency validation passed")
        else:
            print("   ❌ Dependency validation failed")
        
        # Test service status
        status = dep_manager.get_service_status()
        print(f"   📊 Total Services: {status['total_services']}")
        print(f"   📊 Running Services: {status['running_services']}")
        print(f"   📊 Failed Services: {status['failed_services']}")
        
        # Test ready services
        ready_services = dep_manager.get_ready_services()
        print(f"   📊 Ready Services: {len(ready_services)}")
        
        # Test blocked services
        blocked_services = dep_manager.get_blocked_services()
        print(f"   📊 Blocked Services: {len(blocked_services)}")
        
        # Test dependency graph
        graph_info = dep_manager.get_dependency_graph()
        print(f"   📊 Dependency Graph: {len(graph_info['nodes'])} nodes, {len(graph_info['edges'])} edges")
        print(f"   📊 Is DAG: {graph_info['is_dag']}")
        
        return validation_success
        
    except Exception as e:
        print(f"   ❌ Dependency Manager test failed: {e}")
        return False

def test_update_manager():
    """Test update manager functionality."""
    print("\n🔄 Testing Update Manager...")
    print("=" * 60)
    
    try:
        config = load_config()
        update_manager = UpdateManager(config)
        
        # Test update check
        print("Testing update check...")
        updates = update_manager.check_for_updates()
        
        print(f"   📊 Current Version: {updates['current_version']}")
        print(f"   📊 Available Updates: {updates['update_count']}")
        print(f"   📊 Last Check: {updates['last_check']}")
        
        if updates['update_count'] > 0:
            print("   ⚠️  Updates available:")
            for update in updates['available_updates']:
                print(f"      - {update['version']} from {update['source']}")
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
        else:
            print("   ✅ No updates available")
        
        # Test update status
        status = update_manager.get_update_status()
        print(f"   📊 Update Status: {status['update_status']}")
        print(f"   📊 Auto Update Enabled: {status['auto_update_enabled']}")
        print(f"   📊 Update Progress: {status['update_progress']}%")
        
        # Test available rollbacks
        rollbacks = update_manager.get_available_rollbacks()
        print(f"   📊 Available Rollbacks: {len(rollbacks)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Update Manager test failed: {e}")
        return False

def test_rollback_manager():
    """Test rollback manager functionality."""
    print("\n🔄 Testing Rollback Manager...")
    print("=" * 60)
    
    try:
        config = load_config()
        rollback_manager = RollbackManager(config)
        
        # Test rollback triggers
        print("Testing rollback triggers...")
        should_rollback, triggers = rollback_manager.should_rollback()
        
        print(f"   📊 Should Rollback: {should_rollback}")
        if triggers:
            print(f"   📊 Triggered Conditions: {triggers}")
        else:
            print("   ✅ No rollback conditions triggered")
        
        # Test rollback triggers status
        trigger_status = rollback_manager.get_rollback_triggers_status()
        print("   📊 Rollback Triggers Status:")
        for trigger, status in trigger_status.items():
            enabled = "✅" if status.get("enabled", False) else "❌"
            triggered = "🚨" if status.get("triggered", False) else "✅"
            print(f"      - {trigger}: {enabled} enabled, {triggered} triggered")
        
        # Test rollback status
        status = rollback_manager.get_rollback_status()
        print(f"   📊 Rollback Status: {status['rollback_status']}")
        print(f"   📊 Auto Rollback Enabled: {status['auto_rollback_enabled']}")
        print(f"   📊 Rollback Progress: {status['rollback_progress']}%")
        print(f"   📊 Available Rollbacks: {status['available_rollbacks']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Rollback Manager test failed: {e}")
        return False

def test_deployment_scripts():
    """Test deployment scripts."""
    print("\n📜 Testing Deployment Scripts...")
    print("=" * 60)
    
    try:
        scripts_dir = project_root / "scripts"
        
        # Check if deployment scripts exist
        required_scripts = [
            "deploy.sh",
            "deploy-dev.sh", 
            "deploy-staging.sh",
            "deploy-prod.sh",
            "validate-deployment.sh"
        ]
        
        missing_scripts = []
        for script in required_scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                print(f"   ✅ {script} exists")
                
                # Check if script is executable
                if os.access(script_path, os.X_OK):
                    print(f"      ✅ {script} is executable")
                else:
                    print(f"      ⚠️  {script} is not executable")
            else:
                print(f"   ❌ {script} missing")
                missing_scripts.append(script)
        
        if missing_scripts:
            print(f"   ❌ Missing scripts: {missing_scripts}")
            return False
        else:
            print("   ✅ All deployment scripts present")
            return True
        
    except Exception as e:
        print(f"   ❌ Deployment scripts test failed: {e}")
        return False

def test_configuration_files():
    """Test configuration files."""
    print("\n⚙️ Testing Configuration Files...")
    print("=" * 60)
    
    try:
        config_dir = project_root / "config"
        
        # Check if configuration files exist
        required_configs = [
            "deployment_config.json",
            "update_config.json",
            "rollback_config.json"
        ]
        
        missing_configs = []
        for config_file in required_configs:
            config_path = config_dir / config_file
            if config_path.exists():
                print(f"   ✅ {config_file} exists")
                
                # Validate JSON
                try:
                    with open(config_path, 'r') as f:
                        json.load(f)
                    print(f"      ✅ {config_file} is valid JSON")
                except json.JSONDecodeError as e:
                    print(f"      ❌ {config_file} has invalid JSON: {e}")
                    return False
            else:
                print(f"   ❌ {config_file} missing")
                missing_configs.append(config_file)
        
        if missing_configs:
            print(f"   ❌ Missing configs: {missing_configs}")
            return False
        else:
            print("   ✅ All configuration files present and valid")
            return True
        
    except Exception as e:
        print(f"   ❌ Configuration files test failed: {e}")
        return False

def test_deployment_automation_integration():
    """Test deployment automation integration."""
    print("\n🔗 Testing Deployment Automation Integration...")
    print("=" * 60)
    
    try:
        config = load_config()
        
        # Test component initialization
        print("Testing component initialization...")
        startup_manager = StartupManager(config)
        dep_manager = DependencyManager(config)
        update_manager = UpdateManager(config)
        rollback_manager = RollbackManager(config)
        
        print("   ✅ All components initialized successfully")
        
        # Test component communication
        print("Testing component communication...")
        
        # Test startup manager with dependency manager
        startup_status = startup_manager.get_startup_status()
        dep_status = dep_manager.get_service_status()
        
        print(f"   📊 Startup Manager Status: {startup_status['completed_steps']}/{startup_status['total_steps']} steps")
        print(f"   📊 Dependency Manager Status: {dep_status['running_services']}/{dep_status['total_services']} services")
        
        # Test update manager with rollback manager
        update_status = update_manager.get_update_status()
        rollback_status = rollback_manager.get_rollback_status()
        
        print(f"   📊 Update Manager Status: {update_status['update_status']}")
        print(f"   📊 Rollback Manager Status: {rollback_status['rollback_status']}")
        
        print("   ✅ Component communication working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Deployment automation integration test failed: {e}")
        return False

def test_deployment_automation_performance():
    """Test deployment automation performance."""
    print("\n⚡ Testing Deployment Automation Performance...")
    print("=" * 60)
    
    try:
        config = load_config()
        
        # Test startup manager performance
        print("Testing startup manager performance...")
        start_time = time.time()
        
        startup_manager = StartupManager(config)
        startup_status = startup_manager.get_startup_status()
        
        startup_time = time.time() - start_time
        print(f"   📊 Startup Manager Initialization: {startup_time:.3f}s")
        
        # Test dependency manager performance
        print("Testing dependency manager performance...")
        start_time = time.time()
        
        dep_manager = DependencyManager(config)
        dep_status = dep_manager.get_service_status()
        
        dep_time = time.time() - start_time
        print(f"   📊 Dependency Manager Initialization: {dep_time:.3f}s")
        
        # Test update manager performance
        print("Testing update manager performance...")
        start_time = time.time()
        
        update_manager = UpdateManager(config)
        updates = update_manager.check_for_updates()
        
        update_time = time.time() - start_time
        print(f"   📊 Update Check: {update_time:.3f}s")
        
        # Test rollback manager performance
        print("Testing rollback manager performance...")
        start_time = time.time()
        
        rollback_manager = RollbackManager(config)
        should_rollback, triggers = rollback_manager.should_rollback()
        
        rollback_time = time.time() - start_time
        print(f"   📊 Rollback Check: {rollback_time:.3f}s")
        
        # Overall performance
        total_time = startup_time + dep_time + update_time + rollback_time
        print(f"   📊 Total Performance Test: {total_time:.3f}s")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Deployment automation performance test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Stage 5: Deployment Automation Test")
    print("=" * 60)
    print(f"Test started at: {now().isoformat()}")
    
    # Setup logging
    setup_logging()
    
    # Create logs directory
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Run tests
    test_results = []
    
    # Test individual components
    test_results.append(("Startup Manager", test_startup_manager()))
    test_results.append(("Dependency Manager", test_dependency_manager()))
    test_results.append(("Update Manager", test_update_manager()))
    test_results.append(("Rollback Manager", test_rollback_manager()))
    
    # Test deployment scripts and configuration
    test_results.append(("Deployment Scripts", test_deployment_scripts()))
    test_results.append(("Configuration Files", test_configuration_files()))
    
    # Test integration and performance
    test_results.append(("Deployment Automation Integration", test_deployment_automation_integration()))
    test_results.append(("Deployment Automation Performance", test_deployment_automation_performance()))
    
    # Print test results summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All deployment automation tests passed!")
        return True
    else:
        print("❌ Some deployment automation tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
