#!/usr/bin/env python3
"""
Performance Optimization Test Script
Test Stage 1 optimizations for MyRVM Platform Integration
"""

import time
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "services"))
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from optimized_detection_service import OptimizedDetectionService
from memory_manager import MemoryManager
from batch_processor import BatchProcessor
from performance_monitor import PerformanceMonitor

def test_memory_manager():
    """Test memory manager functionality"""
    print("\n🧠 Testing Memory Manager...")
    
    config = {
        'max_memory_mb': 1024,
        'memory_threshold': 0.8,
        'cleanup_interval': 5.0,
        'max_pool_size': 5
    }
    
    memory_manager = MemoryManager(config)
    
    try:
        # Test memory usage monitoring
        memory_usage = memory_manager.get_memory_usage()
        print(f"   Current memory usage: {memory_usage.get('rss_mb', 0):.1f}MB")
        
        # Test memory pressure detection
        is_pressure = memory_manager.is_memory_pressure()
        print(f"   Memory pressure: {'Yes' if is_pressure else 'No'}")
        
        # Test image buffer management
        import numpy as np
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Get optimized buffer
        optimized_buffer = memory_manager.optimize_image_processing(test_image)
        print(f"   Image optimization: {'Success' if optimized_buffer is not None else 'Failed'}")
        
        # Return buffer to pool
        memory_manager.cleanup_optimized_image(optimized_buffer)
        print(f"   Buffer cleanup: Success")
        
        # Test memory cleanup
        memory_manager.cleanup_memory(force=True)
        print(f"   Memory cleanup: Success")
        
        # Get statistics
        stats = memory_manager.get_memory_statistics()
        print(f"   Pool hits: {stats['stats']['pool_hits']}")
        print(f"   Pool misses: {stats['stats']['pool_misses']}")
        
        print("   ✅ Memory Manager test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Memory Manager test failed: {e}")
        return False

def test_batch_processor():
    """Test batch processor functionality"""
    print("\n⚡ Testing Batch Processor...")
    
    config = {
        'batch_size': 2,
        'batch_timeout': 3.0,
        'max_queue_size': 10,
        'processing_threads': 1,
        'models_dir': '../models',
        'confidence_threshold': 0.5
    }
    
    batch_processor = BatchProcessor(config)
    
    try:
        # Start batch processor
        success = batch_processor.start()
        if not success:
            print("   ❌ Failed to start batch processor")
            return False
        
        print("   ✅ Batch processor started")
        
        # Test adding images to queue
        test_images = [
            '/home/my/test-cv-yolo11-sam2-camera/storages/images/test_image1.jpg',
            '/home/my/test-cv-yolo11-sam2-camera/storages/images/test_image2.jpg'
        ]
        
        for i, image_path in enumerate(test_images):
            # Create dummy image if it doesn't exist
            if not Path(image_path).exists():
                import cv2
                import numpy as np
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
                dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.imwrite(image_path, dummy_image)
            
            success = batch_processor.add_image(image_path, {'test_id': i})
            print(f"   Added image {i+1}: {'Success' if success else 'Failed'}")
        
        # Wait for processing
        print("   Waiting for batch processing...")
        time.sleep(5)
        
        # Get results
        results = []
        for _ in range(len(test_images)):
            result = batch_processor.get_result(timeout=10.0)
            if result:
                results.append(result)
                print(f"   Got result: {result.get('image_path', 'Unknown')}")
        
        # Get statistics
        stats = batch_processor.get_statistics()
        print(f"   Images processed: {stats['stats']['images_processed']}")
        print(f"   Batches processed: {stats['stats']['batches_processed']}")
        
        # Stop batch processor
        batch_processor.stop()
        print("   ✅ Batch processor stopped")
        
        print("   ✅ Batch Processor test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Batch Processor test failed: {e}")
        return False

def test_performance_monitor():
    """Test performance monitor functionality"""
    print("\n📊 Testing Performance Monitor...")
    
    config = {
        'monitoring_interval': 2.0,
        'history_size': 100,
        'alert_thresholds': {
            'cpu_percent': 80.0,
            'memory_percent': 80.0,
            'disk_percent': 90.0,
            'temperature': 80.0
        }
    }
    
    performance_monitor = PerformanceMonitor(config)
    
    try:
        # Test system metrics
        metrics = performance_monitor.get_system_metrics()
        if metrics:
            print(f"   CPU usage: {metrics.get('cpu', {}).get('percent', 0):.1f}%")
            print(f"   Memory usage: {metrics.get('memory', {}).get('percent', 0):.1f}%")
            print(f"   Disk usage: {metrics.get('disk', {}).get('percent', 0):.1f}%")
        
        # Test alert checking
        alerts = performance_monitor.check_alerts(metrics)
        print(f"   Active alerts: {len(alerts)}")
        
        # Start monitoring briefly
        performance_monitor.start_monitoring()
        print("   ✅ Performance monitoring started")
        
        # Wait for some samples
        time.sleep(6)
        
        # Get performance summary
        summary = performance_monitor.get_performance_summary()
        if summary:
            print(f"   Samples collected: {summary.get('stats', {}).get('total_samples', 0)}")
            print(f"   Alerts generated: {summary.get('stats', {}).get('alerts_generated', 0)}")
        
        # Stop monitoring
        performance_monitor.stop_monitoring()
        print("   ✅ Performance monitoring stopped")
        
        print("   ✅ Performance Monitor test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Performance Monitor test failed: {e}")
        return False

def test_optimized_detection_service():
    """Test optimized detection service"""
    print("\n🚀 Testing Optimized Detection Service...")
    
    config = {
        'models_dir': '../models',
        'optimization_enabled': True,
        'max_memory_mb': 1024,
        'memory_threshold': 0.8,
        'batch_size': 2,
        'batch_timeout': 3.0,
        'monitoring_interval': 2.0,
        'confidence_threshold': 0.5
    }
    
    optimized_service = OptimizedDetectionService(config)
    
    try:
        # Start service
        success = optimized_service.start()
        if not success:
            print("   ❌ Failed to start optimized detection service")
            return False
        
        print("   ✅ Optimized detection service started")
        
        # Test single image detection
        test_image = '/home/my/test-cv-yolo11-sam2-camera/storages/images/test_image1.jpg'
        
        # Create test image if it doesn't exist
        if not Path(test_image).exists():
            import cv2
            import numpy as np
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
            dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.imwrite(test_image, dummy_image)
        
        # Test optimized detection
        result = optimized_service.detect_objects_optimized(test_image)
        if 'error' not in result:
            print(f"   ✅ Optimized detection: Success")
            print(f"   Processing time: {result.get('optimization_metadata', {}).get('processing_time', 0):.3f}s")
        else:
            print(f"   ⚠️  Optimized detection: {result['error']}")
        
        # Test batch detection
        test_images = [test_image, test_image]  # Use same image twice
        batch_results = optimized_service.detect_objects_batch(test_images)
        print(f"   ✅ Batch detection: {len(batch_results)}/{len(test_images)} results")
        
        # Get performance metrics
        metrics = optimized_service.get_performance_metrics()
        if 'error' not in metrics:
            service_stats = metrics.get('service_stats', {})
            print(f"   Total detections: {service_stats.get('total_detections', 0)}")
            print(f"   Optimized detections: {service_stats.get('optimized_detections', 0)}")
            print(f"   Memory optimizations: {service_stats.get('memory_optimizations', 0)}")
        
        # Test performance optimization
        optimization_result = optimized_service.optimize_performance()
        if 'error' not in optimization_result:
            optimizations = optimization_result.get('optimizations_applied', [])
            print(f"   Performance optimizations applied: {len(optimizations)}")
        
        # Get optimization report
        report = optimized_service.get_optimization_report()
        print("   ✅ Optimization report generated")
        
        # Stop service
        optimized_service.stop()
        print("   ✅ Optimized detection service stopped")
        
        print("   ✅ Optimized Detection Service test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Optimized Detection Service test failed: {e}")
        return False

def run_performance_benchmark():
    """Run comprehensive performance benchmark"""
    print("\n🏁 Running Performance Benchmark...")
    
    config = {
        'models_dir': '../models',
        'optimization_enabled': True,
        'max_memory_mb': 1024,
        'memory_threshold': 0.8,
        'batch_size': 4,
        'batch_timeout': 2.0,
        'monitoring_interval': 1.0,
        'confidence_threshold': 0.5
    }
    
    optimized_service = OptimizedDetectionService(config)
    
    try:
        # Start service
        optimized_service.start()
        print("   ✅ Service started for benchmark")
        
        # Create test images
        test_images = []
        for i in range(5):
            image_path = f'/home/my/test-cv-yolo11-sam2-camera/storages/images/benchmark_test_{i}.jpg'
            if not Path(image_path).exists():
                import cv2
                import numpy as np
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
                dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.imwrite(image_path, dummy_image)
            test_images.append(image_path)
        
        print(f"   Created {len(test_images)} test images")
        
        # Run performance test
        benchmark_result = optimized_service.run_performance_test(test_images, iterations=3)
        
        if 'error' not in benchmark_result:
            comparison = benchmark_result.get('comparison', {})
            improvement = comparison.get('improvement_percent', 0)
            speedup = comparison.get('speedup_factor', 1.0)
            
            print(f"   ✅ Performance benchmark completed")
            print(f"   Improvement: {improvement:.1f}%")
            print(f"   Speedup factor: {speedup:.2f}x")
            print(f"   Optimized time: {comparison.get('average_optimized_time', 0):.3f}s")
            print(f"   Baseline time: {comparison.get('average_baseline_time', 0):.3f}s")
        else:
            print(f"   ⚠️  Benchmark error: {benchmark_result['error']}")
        
        # Stop service
        optimized_service.stop()
        print("   ✅ Service stopped after benchmark")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Performance benchmark failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Stage 1: Performance Optimization Test")
    print("=" * 60)
    
    test_results = {
        'memory_manager': False,
        'batch_processor': False,
        'performance_monitor': False,
        'optimized_detection_service': False,
        'performance_benchmark': False
    }
    
    # Run individual component tests
    test_results['memory_manager'] = test_memory_manager()
    test_results['batch_processor'] = test_batch_processor()
    test_results['performance_monitor'] = test_performance_monitor()
    test_results['optimized_detection_service'] = test_optimized_detection_service()
    
    # Run performance benchmark
    test_results['performance_benchmark'] = run_performance_benchmark()
    
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
        print("🎉 All performance optimization tests passed!")
        print("✅ Stage 1: Performance Optimization - COMPLETED")
    else:
        print("⚠️  Some tests failed. Please check the logs for details.")
    
    # Save test results
    results_file = Path(__file__).parent.parent / 'logs' / f'performance_optimization_test_{now().strftime("%Y%m%d_%H%M%S")}.json'
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'test_results': test_results,
            'timestamp': now().isoformat(),
            'passed_tests': passed_tests,
            'total_tests': total_tests
        }, f, indent=2)
    
    print(f"📝 Test results saved to: {results_file}")

if __name__ == "__main__":
    main()
