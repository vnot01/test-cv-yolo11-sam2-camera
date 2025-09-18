#!/usr/bin/env python3
"""
Batch Processor for MyRVM Platform Integration
Optimized batch processing for production deployment
"""

import time
import logging
import threading
import queue
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import cv2

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "services"))

from detection_service import DetectionService
from memory_manager import MemoryManager

class BatchProcessor:
    """Optimized batch processing for AI inference"""
    
    def __init__(self, config: Dict):
        """
        Initialize batch processor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.batch_size = config.get('batch_size', 4)
        self.batch_timeout = config.get('batch_timeout', 2.0)  # 2 seconds
        self.max_queue_size = config.get('max_queue_size', 20)
        self.processing_threads = config.get('processing_threads', 2)
        
        # Processing queues
        self.input_queue = queue.Queue(maxsize=self.max_queue_size)
        self.output_queue = queue.Queue(maxsize=self.max_queue_size)
        
        # Processing state
        self.is_running = False
        self.processing_threads_list = []
        self.batch_worker_thread = None
        
        # Initialize services
        self.detection_service = DetectionService(
            models_dir=config.get('models_dir', '../models')
        )
        self.memory_manager = MemoryManager(config)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Statistics
        self.stats = {
            'batches_processed': 0,
            'images_processed': 0,
            'total_processing_time': 0,
            'average_batch_time': 0,
            'queue_overflows': 0,
            'processing_errors': 0,
            'start_time': None
        }
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for batch processor"""
        logger = logging.getLogger('BatchProcessor')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'batch_processor_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def add_image(self, image_path: str, metadata: Dict = None) -> bool:
        """Add image to processing queue"""
        try:
            if metadata is None:
                metadata = {}
            
            # Add timestamp
            metadata['added_at'] = datetime.now().isoformat()
            
            # Try to add to queue
            self.input_queue.put((image_path, metadata), timeout=1)
            
            self.logger.debug(f"Added image to queue: {image_path}")
            return True
            
        except queue.Full:
            self.stats['queue_overflows'] += 1
            self.logger.warning(f"Queue full, dropping image: {image_path}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to add image to queue: {e}")
            return False
    
    def get_result(self, timeout: float = 5.0) -> Optional[Dict]:
        """Get processing result from output queue"""
        try:
            result = self.output_queue.get(timeout=timeout)
            self.output_queue.task_done()
            return result
        except queue.Empty:
            return None
        except Exception as e:
            self.logger.error(f"Failed to get result: {e}")
            return None
    
    def _load_image_batch(self, image_paths: List[str]) -> Tuple[List[np.ndarray], List[Dict]]:
        """Load batch of images"""
        images = []
        metadata_list = []
        
        for image_path, metadata in image_paths:
            try:
                # Load image
                image = cv2.imread(image_path)
                if image is None:
                    self.logger.error(f"Failed to load image: {image_path}")
                    continue
                
                # Optimize image with memory manager
                optimized_image = self.memory_manager.optimize_image_processing(image)
                
                images.append(optimized_image)
                metadata_list.append(metadata)
                
                self.logger.debug(f"Loaded image: {image_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to load image {image_path}: {e}")
                continue
        
        return images, metadata_list
    
    def _process_batch(self, images: List[np.ndarray], metadata_list: List[Dict]) -> List[Dict]:
        """Process batch of images"""
        results = []
        
        try:
            # Process each image in the batch
            for i, (image, metadata) in enumerate(zip(images, metadata_list)):
                try:
                    # Run detection
                    detection_result = self.detection_service.detect_objects(
                        image, 
                        confidence_threshold=self.config.get('confidence_threshold', 0.5)
                    )
                    
                    # Add metadata
                    result = {
                        'image_path': metadata.get('image_path', ''),
                        'metadata': metadata,
                        'detection_result': detection_result,
                        'processed_at': datetime.now().isoformat(),
                        'processing_time': detection_result.get('processing_time', 0)
                    }
                    
                    results.append(result)
                    self.stats['images_processed'] += 1
                    
                    self.logger.debug(f"Processed image {i+1}/{len(images)}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process image {i+1}: {e}")
                    self.stats['processing_errors'] += 1
                    
                    # Add error result
                    error_result = {
                        'image_path': metadata.get('image_path', ''),
                        'metadata': metadata,
                        'error': str(e),
                        'processed_at': datetime.now().isoformat()
                    }
                    results.append(error_result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            self.stats['processing_errors'] += 1
            return []
        finally:
            # Cleanup optimized images
            for image in images:
                self.memory_manager.cleanup_optimized_image(image)
    
    def _batch_worker(self):
        """Batch processing worker thread"""
        self.logger.info("Batch worker started")
        
        while self.is_running:
            try:
                # Collect batch
                batch = []
                batch_start_time = time.time()
                
                # Collect images for batch
                while len(batch) < self.batch_size and self.is_running:
                    try:
                        # Try to get image with timeout
                        timeout = self.batch_timeout - (time.time() - batch_start_time)
                        if timeout <= 0:
                            break
                        
                        image_data = self.input_queue.get(timeout=min(timeout, 0.5))
                        batch.append(image_data)
                        
                    except queue.Empty:
                        # Timeout reached, process current batch
                        break
                
                # Process batch if we have images
                if batch:
                    self.logger.info(f"Processing batch of {len(batch)} images")
                    
                    # Load images
                    images, metadata_list = self._load_image_batch(batch)
                    
                    if images:
                        # Process batch
                        batch_start = time.time()
                        results = self._process_batch(images, metadata_list)
                        batch_time = time.time() - batch_start
                        
                        # Update statistics
                        with self.lock:
                            self.stats['batches_processed'] += 1
                            self.stats['total_processing_time'] += batch_time
                            self.stats['average_batch_time'] = (
                                self.stats['total_processing_time'] / 
                                self.stats['batches_processed']
                            )
                        
                        # Add results to output queue
                        for result in results:
                            try:
                                self.output_queue.put(result, timeout=1)
                            except queue.Full:
                                self.logger.warning("Output queue full, dropping result")
                        
                        self.logger.info(f"Batch processed in {batch_time:.2f}s, "
                                       f"avg: {self.stats['average_batch_time']:.2f}s")
                    
                    # Mark batch items as done
                    for _ in batch:
                        self.input_queue.task_done()
                
                # Small delay to prevent busy waiting
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Batch worker error: {e}")
                time.sleep(1)
        
        self.logger.info("Batch worker stopped")
    
    def start(self):
        """Start batch processor"""
        if not self.is_running:
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            # Start memory manager
            self.memory_manager.start_monitoring()
            
            # Start batch worker thread
            self.batch_worker_thread = threading.Thread(target=self._batch_worker)
            self.batch_worker_thread.start()
            
            self.logger.info("Batch processor started")
            return True
        return False
    
    def stop(self):
        """Stop batch processor"""
        if self.is_running:
            self.logger.info("Stopping batch processor...")
            
            self.is_running = False
            
            # Stop batch worker thread
            if self.batch_worker_thread:
                self.batch_worker_thread.join(timeout=5)
            
            # Stop memory manager
            self.memory_manager.stop_monitoring()
            
            self.logger.info("Batch processor stopped")
    
    def get_statistics(self) -> Dict:
        """Get batch processing statistics"""
        uptime = 0
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'uptime_seconds': uptime,
            'is_running': self.is_running,
            'queue_sizes': {
                'input_queue': self.input_queue.qsize(),
                'output_queue': self.output_queue.qsize()
            },
            'stats': self.stats.copy(),
            'memory_stats': self.memory_manager.get_memory_statistics()
        }
    
    def get_performance_report(self) -> str:
        """Generate performance report"""
        stats = self.get_statistics()
        
        # Calculate rates
        uptime = stats['uptime_seconds']
        images_per_second = stats['stats']['images_processed'] / uptime if uptime > 0 else 0
        batches_per_second = stats['stats']['batches_processed'] / uptime if uptime > 0 else 0
        
        report = f"""
Batch Processor Performance Report
==================================
Uptime: {uptime:.0f} seconds
Status: {'Running' if stats['is_running'] else 'Stopped'}

Processing Statistics:
- Images Processed: {stats['stats']['images_processed']}
- Batches Processed: {stats['stats']['batches_processed']}
- Average Batch Time: {stats['stats']['average_batch_time']:.2f}s
- Images per Second: {images_per_second:.2f}
- Batches per Second: {batches_per_second:.2f}

Queue Statistics:
- Input Queue: {stats['queue_sizes']['input_queue']}/{self.max_queue_size}
- Output Queue: {stats['queue_sizes']['output_queue']}/{self.max_queue_size}

Error Statistics:
- Queue Overflows: {stats['stats']['queue_overflows']}
- Processing Errors: {stats['stats']['processing_errors']}

Memory Statistics:
- Current Memory: {stats['memory_stats']['current_memory_mb']:.1f}MB
- Memory Percent: {stats['memory_stats']['memory_percent']:.1f}%
- Pool Hits: {stats['memory_stats']['stats']['pool_hits']}
- Pool Misses: {stats['memory_stats']['stats']['pool_misses']}
"""
        return report
