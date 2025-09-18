#!/usr/bin/env python3
"""
Production Configuration Test Script
Test Stage 2 production configuration for MyRVM Platform Integration
"""

import os
import json
import time
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "config"))

from environment_config import EnvironmentConfig
from security_manager import SecurityManager
from logging_config import ProductionLoggingConfig
from service_manager import ServiceManager

def test_environment_configuration():
    """Test environment-based configuration management"""
    print("\n⚙️ Testing Environment Configuration...")
    
    try:
        # Test different environments
        environments = ['development', 'staging', 'production']
        
        for env in environments:
            print(f"   Testing {env} environment...")
            
            # Set environment variable
            os.environ['MYRVM_ENVIRONMENT'] = env
            
            # Create environment config
            env_config = EnvironmentConfig()
            
            # Test configuration loading
            config = env_config.config
            print(f"   ✅ {env} config loaded: {len(config)} keys")
            
            # Test configuration validation
            required_fields = ['environment', 'log_level', 'security']
            for field in required_fields:
                if field in config:
                    print(f"   ✅ {field}: {config[field]}")
                else:
                    print(f"   ❌ Missing field: {field}")
            
            # Test configuration methods
            test_value = env_config.get('log_level', 'UNKNOWN')
            print(f"   ✅ Get method: log_level = {test_value}")
            
            # Test environment info
            env_info = env_config.get_environment_info()
            print(f"   ✅ Environment: {env_info['environment']}")
            
            # Test configuration report
            report = env_config.get_configuration_report()
            print(f"   ✅ Configuration report generated ({len(report)} chars)")
        
        print("   ✅ Environment Configuration test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Environment Configuration test failed: {e}")
        return False

def test_security_manager():
    """Test security manager functionality"""
    print("\n🔒 Testing Security Manager...")
    
    try:
        # Create test configuration
        config = {
            'security': {
                'encrypt_credentials': True,
                'require_https': False,
                'access_control': True
            }
        }
        
        # Initialize security manager
        security_manager = SecurityManager(config)
        
        # Test credential encryption/decryption
        test_credential = "test_api_key_12345"
        encrypted = security_manager.encrypt_credential(test_credential)
        decrypted = security_manager.decrypt_credential(encrypted)
        
        if decrypted == test_credential:
            print("   ✅ Credential encryption/decryption working")
        else:
            print("   ❌ Credential encryption/decryption failed")
            return False
        
        # Test credential storage
        security_manager.store_credential('test_api_key', test_credential, {'type': 'api_key'})
        retrieved = security_manager.get_credential('test_api_key')
        
        if retrieved == test_credential:
            print("   ✅ Credential storage/retrieval working")
        else:
            print("   ❌ Credential storage/retrieval failed")
            return False
        
        # Test access token generation
        token = security_manager.generate_access_token('test_user', ['read', 'write'])
        token_data = security_manager.validate_access_token(token)
        
        if token_data and token_data['user_id'] == 'test_user':
            print("   ✅ Access token generation/validation working")
        else:
            print("   ❌ Access token generation/validation failed")
            return False
        
        # Test permission checking
        has_permission = security_manager.check_permission(token, 'read')
        if has_permission:
            print("   ✅ Permission checking working")
        else:
            print("   ❌ Permission checking failed")
            return False
        
        # Test security status
        status = security_manager.get_security_status()
        print(f"   ✅ Security status: {status.get('encryption_enabled', False)}")
        
        # Test security report
        report = security_manager.get_security_report()
        print(f"   ✅ Security report generated ({len(report)} chars)")
        
        # Cleanup
        security_manager.delete_credential('test_api_key')
        security_manager.revoke_access_token(token)
        
        print("   ✅ Security Manager test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Security Manager test failed: {e}")
        return False

def test_logging_configuration():
    """Test production logging configuration"""
    print("\n📝 Testing Production Logging Configuration...")
    
    try:
        # Create test configuration
        config = {
            'log_level': 'INFO',
            'environment': 'development'
        }
        
        # Initialize logging configuration
        logging_config = ProductionLoggingConfig(config)
        
        # Test structured logging
        logging_config.log_structured('TestLogger', 'INFO', 'Test message', 
                                    test_param='test_value', timestamp=datetime.now().isoformat())
        print("   ✅ Structured logging working")
        
        # Test error logging
        try:
            raise ValueError("Test error for logging")
        except Exception as e:
            logging_config.log_error(e, {'context': 'test_context'})
        print("   ✅ Error logging working")
        
        # Test audit logging
        logging_config.log_audit('test_action', 'test_user', {'details': 'test_details'})
        print("   ✅ Audit logging working")
        
        # Test performance logging
        logging_config.log_performance('test_operation', 1.5, {'metric1': 100, 'metric2': 200})
        print("   ✅ Performance logging working")
        
        # Test log files
        log_files = logging_config.get_log_files()
        total_files = sum(len(files) for files in log_files.values())
        print(f"   ✅ Log files: {total_files} total files")
        
        # Test logging status
        status = logging_config.get_logging_status()
        print(f"   ✅ Logging status: {status.get('log_level', 'N/A')}")
        
        # Test logging report
        report = logging_config.get_logging_report()
        print(f"   ✅ Logging report generated ({len(report)} chars)")
        
        print("   ✅ Production Logging Configuration test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Production Logging Configuration test failed: {e}")
        return False

def test_service_manager():
    """Test service manager functionality"""
    print("\n🔧 Testing Service Manager...")
    
    try:
        # Create test configuration
        config = {
            'environment': 'development',
            'service_name': 'myrvm-integration-test'
        }
        
        # Initialize service manager
        service_manager = ServiceManager(config)
        
        # Test service configuration
        service_config = service_manager.service_config
        print(f"   ✅ Service config: {service_config['service_name']}")
        
        # Test systemd service content generation
        service_content = service_manager._generate_systemd_service_content()
        if '[Unit]' in service_content and '[Service]' in service_content:
            print("   ✅ Systemd service content generation working")
        else:
            print("   ❌ Systemd service content generation failed")
            return False
        
        # Test service status (without actually installing)
        status = service_manager.get_service_status()
        print(f"   ✅ Service status check working")
        
        # Test process information
        process_info = service_manager._get_process_info()
        print(f"   ✅ Process info: {len(process_info)} fields")
        
        # Test health check endpoint creation
        if service_manager.create_health_check_endpoint():
            print("   ✅ Health check endpoint creation working")
        else:
            print("   ❌ Health check endpoint creation failed")
            return False
        
        # Test service report
        report = service_manager.get_service_report()
        print(f"   ✅ Service report generated ({len(report)} chars)")
        
        print("   ✅ Service Manager test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Service Manager test failed: {e}")
        return False

def test_configuration_integration():
    """Test integration of all configuration components"""
    print("\n🔗 Testing Configuration Integration...")
    
    try:
        # Create comprehensive configuration
        config = {
            'environment': 'development',
            'log_level': 'INFO',
            'myrvm_base_url': 'http://172.28.233.83:8001',
            'rvm_id': 1,
            'security': {
                'encrypt_credentials': True,
                'require_https': False,
                'access_control': True
            }
        }
        
        # Initialize all components
        env_config = EnvironmentConfig()
        security_manager = SecurityManager(config)
        logging_config = ProductionLoggingConfig(config)
        service_manager = ServiceManager(config)
        
        print("   ✅ All components initialized successfully")
        
        # Test configuration consistency
        env_log_level = env_config.get('log_level')
        if env_log_level == config['log_level']:
            print("   ✅ Configuration consistency verified")
        else:
            print(f"   ❌ Configuration inconsistency: {env_log_level} vs {config['log_level']}")
            return False
        
        # Test security integration
        test_credential = "integration_test_key"
        security_manager.store_credential('integration_test', test_credential)
        retrieved = security_manager.get_credential('integration_test')
        
        if retrieved == test_credential:
            print("   ✅ Security integration working")
        else:
            print("   ❌ Security integration failed")
            return False
        
        # Test logging integration
        logging_config.log_structured('IntegrationTest', 'INFO', 'Integration test message',
                                    environment=config['environment'],
                                    security_enabled=config['security']['encrypt_credentials'])
        print("   ✅ Logging integration working")
        
        # Test service integration
        service_status = service_manager.get_service_status()
        if 'service_name' in service_status:
            print("   ✅ Service integration working")
        else:
            print("   ❌ Service integration failed")
            return False
        
        # Cleanup
        security_manager.delete_credential('integration_test')
        
        print("   ✅ Configuration Integration test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration Integration test failed: {e}")
        return False

def test_production_readiness():
    """Test production readiness features"""
    print("\n🚀 Testing Production Readiness...")
    
    try:
        # Test production environment configuration
        os.environ['MYRVM_ENVIRONMENT'] = 'production'
        
        env_config = EnvironmentConfig()
        config = env_config.config
        
        # Check production-specific settings
        if config.get('environment') == 'production':
            print("   ✅ Production environment detected")
        else:
            print(f"   ❌ Environment mismatch: {config.get('environment')}")
            return False
        
        # Check security settings
        security_config = config.get('security', {})
        if security_config.get('encrypt_credentials') and security_config.get('access_control'):
            print("   ✅ Production security settings enabled")
        else:
            print("   ❌ Production security settings not enabled")
            return False
        
        # Check logging settings
        if config.get('log_level') in ['WARNING', 'ERROR']:
            print("   ✅ Production logging level appropriate")
        else:
            print(f"   ❌ Production logging level inappropriate: {config.get('log_level')}")
            return False
        
        # Check performance settings
        if config.get('batch_size', 0) > 1:
            print("   ✅ Production performance settings optimized")
        else:
            print("   ❌ Production performance settings not optimized")
            return False
        
        # Test production configuration report
        report = env_config.get_configuration_report()
        if 'Production Configuration Report' in report or 'production' in report.lower():
            print("   ✅ Production configuration report generated")
        else:
            print("   ❌ Production configuration report failed")
            return False
        
        print("   ✅ Production Readiness test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Production Readiness test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Stage 2: Production Configuration Test")
    print("=" * 60)
    
    test_results = {
        'environment_configuration': False,
        'security_manager': False,
        'logging_configuration': False,
        'service_manager': False,
        'configuration_integration': False,
        'production_readiness': False
    }
    
    # Run individual component tests
    test_results['environment_configuration'] = test_environment_configuration()
    test_results['security_manager'] = test_security_manager()
    test_results['logging_configuration'] = test_logging_configuration()
    test_results['service_manager'] = test_service_manager()
    
    # Run integration tests
    test_results['configuration_integration'] = test_configuration_integration()
    test_results['production_readiness'] = test_production_readiness()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All production configuration tests passed!")
        print("✅ Stage 2: Production Configuration - COMPLETED")
    else:
        print("⚠️  Some tests failed. Please check the logs for details.")
    
    # Save test results
    results_file = Path(__file__).parent.parent / 'logs' / f'production_configuration_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'test_results': test_results,
            'timestamp': datetime.now().isoformat(),
            'passed_tests': passed_tests,
            'total_tests': total_tests
        }, f, indent=2)
    
    print(f"📝 Test results saved to: {results_file}")

if __name__ == "__main__":
    main()
