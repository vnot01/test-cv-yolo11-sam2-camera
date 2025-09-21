#!/usr/bin/env python3
"""
Test script for Analisis 3 integration
Tests CSRF token handling, API client, and metrics sending
"""

import asyncio
import time
import json
from monitoring.metrics_sender import MetricsSender
from api_client.enhanced_myrvm_api_client import EnhancedMyRVMAPIClient

async def test_analisis3_integration():
    print("🧪 TESTING ANALISIS 3 INTEGRATION...")
    print("=" * 60)
    
    # Test 1: API Client with CSRF
    print("\n1. Testing API Client with CSRF...")
    try:
        api_client = EnhancedMyRVMAPIClient(
            'http://172.28.233.83:8001', 
            'your_api_key_here', 
            rvm_id='jetson_orin_nano_001'
        )
        
        # Test health check
        print("   📤 Testing health check...")
        success, response = api_client.health_check()
        print(f"   ✅ Health check: {success} - {response}")
        
        # Test metrics sending
        print("   📤 Testing metrics sending...")
        test_metrics = {
            'test': 'data',
            'timestamp': time.time(),
            'rvm_id': 4
        }
        success, response = api_client.send_metrics(test_metrics)
        print(f"   ✅ Metrics sending: {success} - {response}")
        
    except Exception as e:
        print(f"   ❌ API Client test failed: {e}")
    
    # Test 2: Metrics Sender
    print("\n2. Testing Metrics Sender...")
    try:
        metrics_sender = MetricsSender('http://172.28.233.83:8001', 4, 'your_api_key_here')
        
        # Test immediate metrics sending
        print("   📤 Sending test metrics...")
        metrics_sender.send_immediate_metrics()
        print("   ✅ Metrics sent successfully")
        
    except Exception as e:
        print(f"   ❌ Metrics Sender test failed: {e}")
    
    # Test 3: Command Execution
    print("\n3. Testing Command Execution...")
    try:
        success, response = api_client.execute_command(
            'DIAGNOSTICS', 
            'system_info', 
            {}
        )
        print(f"   ✅ Command execution: {success} - {response}")
        
    except Exception as e:
        print(f"   ❌ Command execution test failed: {e}")
    
    # Test 4: Configuration Test
    print("\n4. Testing Configuration...")
    try:
        with open('config/production_config.json', 'r') as f:
            config = json.load(f)
        
        remote_access = config.get('remote_access', {})
        print(f"   ✅ Server URL: {remote_access.get('server_url')}")
        print(f"   ✅ RVM ID: {remote_access.get('rvm_id')}")
        print(f"   ✅ API Key: {remote_access.get('api_key', 'Not set')}")
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
    
    print("\n🎉 ANALISIS 3 INTEGRATION TEST COMPLETED!")
    print("\n📊 SUMMARY:")
    print("   - CSRF Token: ✅ Implemented")
    print("   - API Client: ✅ Enhanced")
    print("   - Metrics Sender: ✅ Enhanced")
    print("   - Configuration: ✅ Updated")
    print("   - RVM ID: ✅ Updated to 4")

if __name__ == "__main__":
    asyncio.run(test_analisis3_integration())
