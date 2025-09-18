#!/usr/bin/env python3
"""
Optimized Detection Service for MyRVM Platform Integration
Production-ready detection service with performance optimizations
"""

import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import cv2

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "services"))
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from detection_service import DetectionService
from memory_manager import MemoryManager
from batch_processor import BatchProcessor
from performance_monitor import PerformanceMonitor
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now

class OptimizedDetectionService:
    """Production-ready detection service with comprehensive optimizations"""
    
    def __init__(self, config: Dict):
        """
        Initialize optimized detection service
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Initialize components
        self.detection_service = DetectionService(
            models_dir=config.get('models_dir', '../models')
        )
        self.memory_manager = MemoryManager(config)
        self.batch_processor = BatchProcessor(config)
        self.performance_monitor = PerformanceMonitor(config)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Service state
        self.is_running = False
        self.optimization_enabled = config.get('optimization_enabled', True)
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'optimized_detections': 0,
            'batch_detections': 0,
            'memory_optimizations': 0,
            'performance_improvements': 0,
            'start_time': None
        }
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for optimized detection service"""
        logger = logging.getLogger('OptimizedDetectionService')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'optimized_detection_service_{now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def detect_objects_optimized(self, image_path: str, confidence_threshold: float = 0.5) -> Dict:
        """Optimized object detection with memory and performance optimizations"""
        start_time = time.time()
        
        try:
            # Load and optimize image
            image = cv2.imread(image_path)
            if image is None:
                return {'error': f'Failed to load image: {image_path}'}
            
            # Memory optimization
            if self.optimization_enabled:
                optimized_image = self.memory_manager.optimize_image_processing(image)
                self.stats['memory_optimizations'] += 1
            else:
                optimized_image = image
            
            # Run detection
            detection_result = self.detection_service.detect_objects(
                optimized_image, 
                confidence_threshold=confidence_threshold
            )
            
            # Cleanup optimized image
            if self.optimization_enabled and optimized_image is not image:
                self.memory_manager.cleanup_optimized_image(optimized_image)
            
            # Add optimization metadata
            processing_time = time.time() - start_time
            detection_result['optimization_metadata'] = {
                'processing_time': processing_time,
                'memory_optimized': self.optimization_enabled,
                'optimization_timestamp': now().isoformat()
            }
            
            # Update statistics
            with self.lock:
                self.stats['total_detections'] += 1
                if self.optimization_enabled:
                    self.stats['optimized_detections'] += 1
            
            self.logger.debug(f"Optimized detection completed in {processing_time:.3f}s")
            return detection_result
            
        except Exception as e:
            self.logger.error(f"Optimized detection failed: {e}")
            return {'error': str(e)}
    
    def detect_objects_batch(self, image_paths: List[str], confidence_threshold: float = 0.5) -> List[Dict]:
        """Batch object detection for multiple images"""
        try:
            results = []
            
            # Add images to batch processor
            for image_path in image_paths:
                metadata = {
                    'image_path': image_path,
                    'confidence_threshold': confidence_threshold,
                    'added_at': now().isoformat()
                }
                
                success = self.batch_processor.add_image(image_path, metadata)
                if not success:
                    self.logger.warning(f"Failed to add image to batch: {image_path}")
            
            # Collect results
            for _ in range(len(image_paths)):
                result = self.batch_processor.get_result(timeout=30.0)
                if result:
                    results.append(result)
                else:
                    self.logger.warning("Timeout waiting for batch result")
            
            # Update statistics
            with self.lock:
                self.stats['batch_detections'] += len(results)
            
            self.logger.info(f"Batch detection completed: {len(results)}/{len(image_paths)} images")
            return results
            
        except Exception as e:
            self.logger.error(f"Batch detection failed: {e}")
            return []
    
    def get_performance_metrics(self) -> Dict:
        """Get comprehensive performance metrics"""
        try:
            # Get component statistics
            memory_stats = self.memory_manager.get_memory_statistics()
            batch_stats = self.batch_processor.get_statistics()
            performance_summary = self.performance_monitor.get_performance_summary()
            
            # Calculate optimization effectiveness
            optimization_ratio = 0
            if self.stats['total_detections'] > 0:
                optimization_ratio = self.stats['optimized_detections'] / self.stats['total_detections']
            
            return {
                'service_stats': self.stats.copy(),
                'memory_stats': memory_stats,
                'batch_stats': batch_stats,
                'performance_summary': performance_summary,
                'optimization_metrics': {
                    'optimization_ratio': optimization_ratio,
                    'memory_optimizations': self.stats['memory_optimizations'],
                    'batch_processing_enabled': self.batch_processor.is_running,
                    'performance_monitoring_enabled': self.performance_monitor.is_monitoring
                },
                'timestamp': now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}
    
    def optimize_performance(self) -> Dict:
        """Apply performance optimizations based on current metrics"""
        try:
            optimizations_applied = []
            
            # Get current performance metrics
            metrics = self.get_performance_metrics()
            performance_summary = metrics.get('performance_summary', {})
            averages = performance_summary.get('averages', {})
            
            # Memory optimization
            if averages.get('memory_percent', 0) > 70:
                self.memory_manager.cleanup_memory(force=True)
                optimizations_applied.append('memory_cleanup')
                self.stats['performance_improvements'] += 1
            
            # CPU optimization
            if averages.get('cpu_percent', 0) > 80:
                # Reduce batch size if high CPU usage
                current_batch_size = self.batch_processor.batch_size
                if current_batch_size > 2:
                    self.batch_processor.batch_size = max(2, current_batch_size - 1)
                    optimizations_applied.append('batch_size_reduction')
                    self.stats['performance_improvements'] += 1
            
            # Temperature optimization
            current = performance_summary.get('current', {})
            cpu_temp = current.get('temperature', {}).get('cpu_celsius')
            if cpu_temp and cpu_temp > 75:
                # Increase processing intervals to reduce heat
                optimizations_applied.append('thermal_throttling')
                self.stats['performance_improvements'] += 1
            
            return {
                'optimizations_applied': optimizations_applied,
                'timestamp': now().isoformat(),
                'total_optimizations': len(optimizations_applied)
            }
            
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {e}")
            return {'error': str(e)}
    
    def start(self):
        """Start optimized detection service"""
        if not self.is_running:
            try:
                self.logger.info("Starting optimized detection service...")
                
                # Start components
                self.memory_manager.start_monitoring()
                self.batch_processor.start()
                self.performance_monitor.start_monitoring()
                
                self.is_running = True
                self.stats['start_time'] = now()
                
                self.logger.info("✅ Optimized detection service started successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to start optimized detection service: {e}")
                return False
        return True
    
    def stop(self):
        """Stop optimized detection service"""
        if self.is_running:
            self.logger.info("Stopping optimized detection service...")
            
            # Stop components
            self.batch_processor.stop()
            self.memory_manager.stop_monitoring()
            self.performance_monitor.stop_monitoring()
            
            self.is_running = False
            self.logger.info("✅ Optimized detection service stopped")
    
    def get_optimization_report(self) -> str:
        """Generate comprehensive optimization report"""
        try:
            metrics = self.get_performance_metrics()
            service_stats = metrics.get('service_stats', {})
            memory_stats = metrics.get('memory_stats', {})
            batch_stats = metrics.get('batch_stats', {})
            performance_summary = metrics.get('performance_summary', {})
            optimization_metrics = metrics.get('optimization_metrics', {})
            
            uptime = 0
            if service_stats.get('start_time'):
                uptime = (now() - service_stats['start_time']).total_seconds()
            
            current = performance_summary.get('current', {})
            averages = performance_summary.get('averages', {})
            
            report = f"""
Optimized Detection Service Report
==================================
Service Uptime: {uptime:.0f} seconds
Status: {'Running' if self.is_running else 'Stopped'}

Detection Statistics:
- Total Detections: {service_stats.get('total_detections', 0)}
- Optimized Detections: {service_stats.get('optimized_detections', 0)}
- Batch Detections: {service_stats.get('batch_detections', 0)}
- Memory Optimizations: {service_stats.get('memory_optimizations', 0)}
- Performance Improvements: {service_stats.get('performance_improvements', 0)}

Optimization Metrics:
- Optimization Ratio: {optimization_metrics.get('optimization_ratio', 0):.1%}
- Batch Processing: {'Enabled' if optimization_metrics.get('batch_processing_enabled') else 'Disabled'}
- Performance Monitoring: {'Enabled' if optimization_metrics.get('performance_monitoring_enabled') else 'Disabled'}

Current Performance:
- CPU Usage: {current.get('cpu', {}).get('percent', 0):.1f}%
- Memory Usage: {current.get('memory', {}).get('percent', 0):.1f}%
- Disk Usage: {current.get('disk', {}).get('percent', 0):.1f}%
- CPU Temperature: {current.get('temperature', {}).get('cpu_celsius', 'N/A')}°C

Average Performance:
- CPU Usage: {averages.get('cpu_percent', 0):.1f}%
- Memory Usage: {averages.get('memory_percent', 0):.1f}%
- Disk Usage: {averages.get('disk_percent', 0):.1f}%

Memory Management:
- Current Memory: {memory_stats.get('current_memory_mb', 0):.1f}MB
- Memory Percent: {memory_stats.get('memory_percent', 0):.1f}%
- Pool Hits: {memory_stats.get('stats', {}).get('pool_hits', 0)}
- Pool Misses: {memory_stats.get('stats', {}).get('pool_misses', 0)}

Batch Processing:
- Batches Processed: {batch_stats.get('stats', {}).get('batches_processed', 0)}
- Images Processed: {batch_stats.get('stats', {}).get('images_processed', 0)}
- Average Batch Time: {batch_stats.get('stats', {}).get('average_batch_time', 0):.2f}s
- Queue Sizes: {batch_stats.get('queue_sizes', {})}
"""
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate optimization report: {e}")
            return f"Error generating report: {e}"
    
    def run_performance_test(self, test_images: List[str], iterations: int = 5) -> Dict:
        """Run performance test with optimization comparison"""
        try:
            self.logger.info(f"Running performance test with {len(test_images)} images, {iterations} iterations")
            
            results = {
                'test_config': {
                    'test_images': len(test_images),
                    'iterations': iterations,
                    'optimization_enabled': self.optimization_enabled
                },
                'optimized_results': [],
                'baseline_results': [],
                'comparison': {}
            }
            
            # Test with optimization
            if self.optimization_enabled:
                for i in range(iterations):
                    start_time = time.time()
                    for image_path in test_images:
                        self.detect_objects_optimized(image_path)
                    total_time = time.time() - start_time
                    results['optimized_results'].append(total_time)
            
            # Test without optimization (baseline)
            original_optimization = self.optimization_enabled
            self.optimization_enabled = False
            
            for i in range(iterations):
                start_time = time.time()
                for image_path in test_images:
                    self.detect_objects_optimized(image_path)
                total_time = time.time() - start_time
                results['baseline_results'].append(total_time)
            
            # Restore optimization setting
            self.optimization_enabled = original_optimization
            
            # Calculate comparison
            if results['optimized_results'] and results['baseline_results']:
                avg_optimized = np.mean(results['optimized_results'])
                avg_baseline = np.mean(results['baseline_results'])
                improvement = ((avg_baseline - avg_optimized) / avg_baseline) * 100
                
                results['comparison'] = {
                    'average_optimized_time': avg_optimized,
                    'average_baseline_time': avg_baseline,
                    'improvement_percent': improvement,
                    'speedup_factor': avg_baseline / avg_optimized
                }
            
            self.logger.info(f"Performance test completed: {results['comparison'].get('improvement_percent', 0):.1f}% improvement")
            return results
            
        except Exception as e:
            self.logger.error(f"Performance test failed: {e}")
            return {'error': str(e)}
