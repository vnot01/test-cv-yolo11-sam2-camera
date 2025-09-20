#!/usr/bin/env python3
"""
Memory Manager for MyRVM Platform Integration
Optimized memory management for production deployment
"""

import gc
import psutil
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np
import cv2

class MemoryManager:
    """Advanced memory management for production deployment"""
    
    def __init__(self, config: Dict):
        """
        Initialize memory manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.max_memory_mb = config.get('max_memory_mb', 1024)  # 1GB default
        self.memory_threshold = config.get('memory_threshold', 0.8)  # 80% threshold
        self.cleanup_interval = config.get('cleanup_interval', 30.0)  # 30 seconds
        
        # Memory pools
        self.image_pool = []
        self.numpy_pool = []
        self.max_pool_size = config.get('max_pool_size', 10)
        
        # Memory monitoring
        self.memory_history = []
        self.max_history_size = 100
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Statistics
        self.stats = {
            'total_allocations': 0,
            'total_deallocations': 0,
            'memory_cleanups': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'start_time': None
        }
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for memory manager"""
        logger = logging.getLogger('MemoryManager')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'memory_manager_{now().strftime("%Y%m%d")}.log'
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
    
    def get_memory_usage(self) -> Dict:
        """Get current memory usage statistics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
                'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024,
                'total_mb': psutil.virtual_memory().total / 1024 / 1024
            }
        except Exception as e:
            self.logger.error(f"Failed to get memory usage: {e}")
            return {}
    
    def is_memory_pressure(self) -> bool:
        """Check if system is under memory pressure"""
        memory_usage = self.get_memory_usage()
        if not memory_usage:
            return False
        
        # Check if memory usage exceeds threshold
        current_memory_mb = memory_usage.get('rss_mb', 0)
        return current_memory_mb > (self.max_memory_mb * self.memory_threshold)
    
    def get_image_buffer(self, width: int, height: int, channels: int = 3) -> np.ndarray:
        """Get image buffer from pool or create new one"""
        with self.lock:
            # Try to find suitable buffer in pool
            for i, buffer in enumerate(self.image_pool):
                if (buffer.shape == (height, width, channels) and 
                    buffer.dtype == np.uint8):
                    # Found suitable buffer, remove from pool
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
                    buffer = self.image_pool.pop(i)
                    self.stats['pool_hits'] += 1
                    self.logger.debug(f"Reused image buffer: {width}x{height}x{channels}")
                    return buffer
            
            # No suitable buffer found, create new one
            buffer = np.zeros((height, width, channels), dtype=np.uint8)
            self.stats['pool_misses'] += 1
            self.stats['total_allocations'] += 1
            self.logger.debug(f"Created new image buffer: {width}x{height}x{channels}")
            return buffer
    
    def return_image_buffer(self, buffer: np.ndarray):
        """Return image buffer to pool"""
        with self.lock:
            if len(self.image_pool) < self.max_pool_size:
                # Clear buffer and add to pool
                buffer.fill(0)
                self.image_pool.append(buffer)
                self.stats['total_deallocations'] += 1
                self.logger.debug(f"Returned image buffer to pool: {buffer.shape}")
            else:
                # Pool is full, let buffer be garbage collected
                del buffer
                self.stats['total_deallocations'] += 1
    
    def get_numpy_buffer(self, shape: tuple, dtype: np.dtype = np.float32) -> np.ndarray:
        """Get numpy buffer from pool or create new one"""
        with self.lock:
            # Try to find suitable buffer in pool
            for i, buffer in enumerate(self.numpy_pool):
                if buffer.shape == shape and buffer.dtype == dtype:
                    # Found suitable buffer, remove from pool
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
                    buffer = self.numpy_pool.pop(i)
                    self.stats['pool_hits'] += 1
                    self.logger.debug(f"Reused numpy buffer: {shape}, {dtype}")
                    return buffer
            
            # No suitable buffer found, create new one
            buffer = np.zeros(shape, dtype=dtype)
            self.stats['pool_misses'] += 1
            self.stats['total_allocations'] += 1
            self.logger.debug(f"Created new numpy buffer: {shape}, {dtype}")
            return buffer
    
    def return_numpy_buffer(self, buffer: np.ndarray):
        """Return numpy buffer to pool"""
        with self.lock:
            if len(self.numpy_pool) < self.max_pool_size:
                # Clear buffer and add to pool
                buffer.fill(0)
                self.numpy_pool.append(buffer)
                self.stats['total_deallocations'] += 1
                self.logger.debug(f"Returned numpy buffer to pool: {buffer.shape}")
            else:
                # Pool is full, let buffer be garbage collected
                del buffer
                self.stats['total_deallocations'] += 1
    
    def cleanup_memory(self, force: bool = False):
        """Perform memory cleanup"""
        try:
            # Check if cleanup is needed
            if not force and not self.is_memory_pressure():
                return
            
            self.logger.info("Performing memory cleanup...")
            
            # Clear memory pools
            with self.lock:
                self.image_pool.clear()
                self.numpy_pool.clear()
            
            # Force garbage collection
            collected = gc.collect()
            
            # Log cleanup results
            memory_after = self.get_memory_usage()
            self.stats['memory_cleanups'] += 1
            
            self.logger.info(f"Memory cleanup completed: {collected} objects collected, "
                           f"Memory: {memory_after.get('rss_mb', 0):.1f}MB")
            
        except Exception as e:
            self.logger.error(f"Memory cleanup failed: {e}")
    
    def monitor_memory(self):
        """Memory monitoring worker"""
        self.logger.info("Memory monitoring started")
        
        while self.is_monitoring:
            try:
                # Get current memory usage
                memory_usage = self.get_memory_usage()
                
                if memory_usage:
                    # Add to history
                    memory_usage['timestamp'] = now().isoformat()
                    self.memory_history.append(memory_usage)
                    
                    # Keep only recent history
                    if len(self.memory_history) > self.max_history_size:
                        self.memory_history = self.memory_history[-self.max_history_size:]
                    
                    # Check for memory pressure
                    if self.is_memory_pressure():
                        self.logger.warning(f"Memory pressure detected: "
                                          f"{memory_usage.get('rss_mb', 0):.1f}MB "
                                          f"({memory_usage.get('percent', 0):.1f}%)")
                        self.cleanup_memory(force=True)
                    
                    # Log memory usage periodically
                    if len(self.memory_history) % 10 == 0:
                        self.logger.info(f"Memory usage: {memory_usage.get('rss_mb', 0):.1f}MB "
                                       f"({memory_usage.get('percent', 0):.1f}%)")
                
                # Wait for next check
                time.sleep(self.cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")
                time.sleep(5)
        
        self.logger.info("Memory monitoring stopped")
    
    def start_monitoring(self):
        """Start memory monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.stats['start_time'] = now()
            self.monitor_thread = threading.Thread(target=self.monitor_memory)
            self.monitor_thread.start()
            self.logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            self.logger.info("Memory monitoring stopped")
    
    def get_memory_statistics(self) -> Dict:
        """Get memory management statistics"""
        uptime = 0
        if self.stats['start_time']:
            uptime = (now() - self.stats['start_time']).total_seconds()
        
        current_memory = self.get_memory_usage()
        
        return {
            'uptime_seconds': uptime,
            'current_memory_mb': current_memory.get('rss_mb', 0),
            'memory_percent': current_memory.get('percent', 0),
            'pool_size': {
                'image_pool': len(self.image_pool),
                'numpy_pool': len(self.numpy_pool)
            },
            'stats': self.stats.copy(),
            'memory_history': self.memory_history[-10:] if self.memory_history else []
        }
    
    def optimize_image_processing(self, image: np.ndarray) -> np.ndarray:
        """Optimize image for processing"""
        try:
            # Get optimized buffer
            height, width = image.shape[:2]
            channels = image.shape[2] if len(image.shape) == 3 else 1
            
            if len(image.shape) == 3:
                optimized_image = self.get_image_buffer(width, height, channels)
                np.copyto(optimized_image, image)
            else:
                optimized_image = self.get_image_buffer(width, height, 1)
                np.copyto(optimized_image, image.reshape(height, width, 1))
            
            return optimized_image
            
        except Exception as e:
            self.logger.error(f"Image optimization failed: {e}")
            return image
    
    def cleanup_optimized_image(self, image: np.ndarray):
        """Cleanup optimized image"""
        try:
            self.return_image_buffer(image)
        except Exception as e:
            self.logger.error(f"Image cleanup failed: {e}")
    
    def get_memory_report(self) -> str:
        """Generate memory usage report"""
        stats = self.get_memory_statistics()
        current_memory = self.get_memory_usage()
        
        report = f"""
Memory Manager Report
====================
Current Memory Usage: {current_memory.get('rss_mb', 0):.1f}MB ({current_memory.get('percent', 0):.1f}%)
Available Memory: {current_memory.get('available_mb', 0):.1f}MB
Total Memory: {current_memory.get('total_mb', 0):.1f}MB

Pool Statistics:
- Image Pool: {stats['pool_size']['image_pool']}/{self.max_pool_size}
- Numpy Pool: {stats['pool_size']['numpy_pool']}/{self.max_pool_size}

Allocation Statistics:
- Total Allocations: {stats['stats']['total_allocations']}
- Total Deallocations: {stats['stats']['total_deallocations']}
- Pool Hits: {stats['stats']['pool_hits']}
- Pool Misses: {stats['stats']['pool_misses']}
- Memory Cleanups: {stats['stats']['memory_cleanups']}

Uptime: {stats['uptime_seconds']:.0f} seconds
"""
        return report
