#!/usr/bin/env python3
"""
Detection Service for Jetson Orin
Handles object detection and segmentation using YOLO11 and SAM2
"""

import cv2
import numpy as np
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from ultralytics import YOLO, SAM
except ImportError:
    print("❌ Ultralytics not found. Please install: pip install ultralytics")
    sys.exit(1)

class DetectionService:
    """Service for object detection and segmentation"""
    
    def __init__(self, models_dir: str = "../models"):
        """
        Initialize detection service
        
        Args:
            models_dir: Directory containing AI models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Model paths
        self.yolo_model_path = self.models_dir / "best.pt"
        self.yolo11n_path = self.models_dir / "yolo11n.pt"
        self.sam2_model_path = self.models_dir / "sam2.1_b.pt"
        
        # Initialize models
        self.yolo_model = None
        self.sam2_model = None
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Load models
        self._load_models()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for detection service"""
        logger = logging.getLogger('DetectionService')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'detection_service_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _load_models(self):
        """Load YOLO and SAM2 models"""
        try:
            # Load YOLO model (prefer custom model, fallback to yolo11n)
            if self.yolo_model_path.exists():
                self.logger.info(f"Loading YOLO model: {self.yolo_model_path}")
                self.yolo_model = YOLO(str(self.yolo_model_path))
            elif self.yolo11n_path.exists():
                self.logger.info(f"Loading YOLO11n model: {self.yolo11n_path}")
                self.yolo_model = YOLO(str(self.yolo11n_path))
            else:
                self.logger.error("No YOLO model found!")
                return
            
            # Load SAM2 model
            if self.sam2_model_path.exists():
                self.logger.info(f"Loading SAM2 model: {self.sam2_model_path}")
                self.sam2_model = SAM(str(self.sam2_model_path))
            else:
                self.logger.warning("SAM2 model not found, segmentation will be disabled")
                self.sam2_model = None
            
            self.logger.info("✅ Models loaded successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load models: {e}")
            raise
    
    def detect_objects(self, image_path: str, confidence_threshold: float = 0.5) -> Dict:
        """
        Detect objects in image using YOLO
        
        Args:
            image_path: Path to input image
            confidence_threshold: Minimum confidence for detections
            
        Returns:
            Dictionary containing detection results
        """
        if not self.yolo_model:
            return {'error': 'YOLO model not loaded'}
        
        if not Path(image_path).exists():
            return {'error': f'Image not found: {image_path}'}
        
        try:
            self.logger.info(f"Running object detection on: {image_path}")
            start_time = time.time()
            
            # Run YOLO inference
            results = self.yolo_model(image_path, conf=confidence_threshold, verbose=False)
            
            inference_time = time.time() - start_time
            
            # Process results
            detections = []
            if results[0].boxes is not None:
                boxes = results[0].boxes
                for i, box in enumerate(boxes):
                    detection = {
                        'id': i,
                        'class_id': int(box.cls[0]),
                        'class_name': self.yolo_model.names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
                        'center': box.xywh[0].tolist()  # [x_center, y_center, width, height]
                    }
                    detections.append(detection)
            
            result = {
                'success': True,
                'image_path': image_path,
                'timestamp': now().isoformat(),
                'inference_time': inference_time,
                'total_detections': len(detections),
                'detections': detections,
                'model_used': str(self.yolo_model_path if self.yolo_model_path.exists() else self.yolo11n_path)
            }
            
            self.logger.info(f"✅ Detection completed: {len(detections)} objects found in {inference_time:.2f}s")
            return result
            
        except Exception as e:
            error_msg = f"Detection failed: {str(e)}"
            self.logger.error(error_msg)
            return {'error': error_msg}
    
    def segment_objects(self, image_path: str, detections: List[Dict] = None, 
                       confidence_threshold: float = 0.5) -> Dict:
        """
        Segment objects in image using SAM2
        
        Args:
            image_path: Path to input image
            detections: List of detections from YOLO (if None, will run YOLO first)
            confidence_threshold: Minimum confidence for detections
            
        Returns:
            Dictionary containing segmentation results
        """
        if not self.sam2_model:
            return {'error': 'SAM2 model not loaded'}
        
        if not Path(image_path).exists():
            return {'error': f'Image not found: {image_path}'}
        
        try:
            self.logger.info(f"Running object segmentation on: {image_path}")
            start_time = time.time()
            
            # Get detections if not provided
            if detections is None:
                detection_result = self.detect_objects(image_path, confidence_threshold)
                if 'error' in detection_result:
                    return detection_result
                detections = detection_result['detections']
            
            if not detections:
                return {
                    'success': True,
                    'image_path': image_path,
                    'timestamp': now().isoformat(),
                    'inference_time': time.time() - start_time,
                    'total_segments': 0,
                    'segments': [],
                    'message': 'No objects detected for segmentation'
                }
            
            # Extract bounding boxes for SAM2
            bboxes = [det['bbox'] for det in detections]
            
            # Run SAM2 inference
            sam2_results = self.sam2_model(image_path, bboxes=bboxes)
            
            inference_time = time.time() - start_time
            
            # Process segmentation results
            segments = []
            for i, (detection, sam2_result) in enumerate(zip(detections, sam2_results)):
                # Get segmentation mask
                if hasattr(sam2_result, 'masks') and sam2_result.masks is not None:
                    mask = sam2_result.masks.data[0].cpu().numpy()
                    mask_binary = (mask > 0.5).astype(np.uint8) * 255
                    
                    # Encode mask as base64
                    import base64
                    _, buffer = cv2.imencode('.png', mask_binary)
                    mask_base64 = base64.b64encode(buffer).decode('utf-8')
                else:
                    mask_base64 = None
                
                segment = {
                    'id': i,
                    'detection': detection,
                    'mask_base64': mask_base64,
                    'area': int(np.sum(mask > 0.5)) if mask_base64 else 0
                }
                segments.append(segment)
            
            result = {
                'success': True,
                'image_path': image_path,
                'timestamp': now().isoformat(),
                'inference_time': inference_time,
                'total_segments': len(segments),
                'segments': segments,
                'model_used': str(self.sam2_model_path)
            }
            
            self.logger.info(f"✅ Segmentation completed: {len(segments)} segments in {inference_time:.2f}s")
            return result
            
        except Exception as e:
            error_msg = f"Segmentation failed: {str(e)}"
            self.logger.error(error_msg)
            return {'error': error_msg}
    
    def detect_and_segment(self, image_path: str, confidence_threshold: float = 0.5) -> Dict:
        """
        Run both detection and segmentation
        
        Args:
            image_path: Path to input image
            confidence_threshold: Minimum confidence for detections
            
        Returns:
            Dictionary containing both detection and segmentation results
        """
        try:
            self.logger.info(f"Running detection and segmentation on: {image_path}")
            start_time = time.time()
            
            # Run detection
            detection_result = self.detect_objects(image_path, confidence_threshold)
            if 'error' in detection_result:
                return detection_result
            
            # Run segmentation
            segmentation_result = self.segment_objects(
                image_path, 
                detection_result['detections'], 
                confidence_threshold
            )
            if 'error' in segmentation_result:
                return segmentation_result
            
            total_time = time.time() - start_time
            
            result = {
                'success': True,
                'image_path': image_path,
                'timestamp': now().isoformat(),
                'total_time': total_time,
                'detection': detection_result,
                'segmentation': segmentation_result
            }
            
            self.logger.info(f"✅ Detection and segmentation completed in {total_time:.2f}s")
            return result
            
        except Exception as e:
            error_msg = f"Detection and segmentation failed: {str(e)}"
            self.logger.error(error_msg)
            return {'error': error_msg}
    
    def save_results(self, results: Dict, output_dir: str = "../storages/images/output/myrvm-integration") -> str:
        """
        Save detection/segmentation results to file
        
        Args:
            results: Results dictionary
            output_dir: Output directory
            
        Returns:
            Path to saved results file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = now().strftime("%Y%m%d_%H%M%S")
        results_file = output_path / f"detection_results_{timestamp}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            self.logger.info(f"✅ Results saved to: {results_file}")
            return str(results_file)
            
        except Exception as e:
            error_msg = f"Failed to save results: {e}"
            self.logger.error(error_msg)
            raise
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        info = {
            'yolo_model': {
                'loaded': self.yolo_model is not None,
                'path': str(self.yolo_model_path) if self.yolo_model_path.exists() else str(self.yolo11n_path),
                'exists': self.yolo_model_path.exists() or self.yolo11n_path.exists()
            },
            'sam2_model': {
                'loaded': self.sam2_model is not None,
                'path': str(self.sam2_model_path),
                'exists': self.sam2_model_path.exists()
            }
        }
        return info

# Example usage and testing
if __name__ == "__main__":
    # Initialize detection service
    service = DetectionService()
    
    # Get model info
    print("Model Information:")
    model_info = service.get_model_info()
    print(json.dumps(model_info, indent=2))
    
    # Test with sample image (if exists)
    sample_image = "../storages/images/input/55_mineral_filled.jpg"
    if Path(sample_image).exists():
        print(f"\nTesting detection on: {sample_image}")
        
        # Test detection only
        detection_result = service.detect_objects(sample_image)
        print(f"Detection result: {detection_result.get('total_detections', 0)} objects found")
        
        # Test segmentation if SAM2 is available
        if service.sam2_model:
            segmentation_result = service.segment_objects(sample_image)
            print(f"Segmentation result: {segmentation_result.get('total_segments', 0)} segments")
        
        # Save results
        if 'error' not in detection_result:
            results_file = service.save_results(detection_result)
            print(f"Results saved to: {results_file}")
    else:
        print(f"Sample image not found: {sample_image}")
        print("Please provide a valid image path for testing")
