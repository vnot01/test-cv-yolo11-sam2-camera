#!/usr/bin/env python3
"""
MyRVM Platform Integration - Update Manager
Manages automated updates, version management, and update rollback capabilities.
"""

import os
import sys
import time
import logging
import subprocess
import threading
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import requests
import zipfile
import tarfile

class UpdateManager:
    """
    Manages automated updates, version management, and rollback capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.update_dir = self.project_root / "updates"
        self.backup_dir = self.project_root / "backups" / "updates"
        self.version_file = self.project_root / "VERSION"
        self.update_config_file = self.project_root / "config" / "update_config.json"
        
        self.current_version = self._get_current_version()
        self.update_history: List[Dict] = []
        self.update_status = "idle"
        self.update_progress = 0
        
        self._setup_directories()
        self._load_update_configuration()
        self._load_update_history()
        
    def _setup_directories(self):
        """Setup necessary directories for updates."""
        self.update_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_current_version(self) -> str:
        """Get current version of the application."""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r') as f:
                    return f.read().strip()
            else:
                return "1.0.0"
        except Exception as e:
            self.logger.warning(f"Could not read version file: {e}")
            return "1.0.0"
    
    def _load_update_configuration(self):
        """Load update configuration."""
        try:
            if self.update_config_file.exists():
                with open(self.update_config_file, 'r') as f:
                    self.update_config = json.load(f)
            else:
                # Default update configuration
                self.update_config = {
                    "auto_update_enabled": False,
                    "update_check_interval": 3600,  # 1 hour
                    "update_channel": "stable",
                    "backup_before_update": True,
                    "rollback_on_failure": True,
                    "update_timeout": 1800,  # 30 minutes
                    "max_rollback_versions": 5,
                    "update_sources": {
                        "github": {
                            "enabled": True,
                            "repository": "vnot01/test-cv-yolo11-sam2-camera",
                            "branch": "main"
                        },
                        "local": {
                            "enabled": True,
                            "path": "./updates"
                        }
                    }
                }
                self._save_update_configuration()
        except Exception as e:
            self.logger.error(f"Failed to load update configuration: {e}")
            self.update_config = {}
    
    def _save_update_configuration(self):
        """Save update configuration."""
        try:
            with open(self.update_config_file, 'w') as f:
                json.dump(self.update_config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save update configuration: {e}")
    
    def _load_update_history(self):
        """Load update history."""
        try:
            history_file = self.backup_dir / "update_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    self.update_history = json.load(f)
            else:
                self.update_history = []
        except Exception as e:
            self.logger.error(f"Failed to load update history: {e}")
            self.update_history = []
    
    def _save_update_history(self):
        """Save update history."""
        try:
            history_file = self.backup_dir / "update_history.json"
            with open(history_file, 'w') as f:
                json.dump(self.update_history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save update history: {e}")
    
    def _add_update_record(self, version: str, status: str, details: str = ""):
        """Add a record to update history."""
        record = {
            "version": version,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.update_history.append(record)
        self._save_update_history()
    
    def check_for_updates(self) -> Dict[str, Any]:
        """Check for available updates."""
        try:
            self.logger.info("Checking for updates...")
            
            available_updates = []
            
            # Check GitHub for updates
            if self.update_config.get("update_sources", {}).get("github", {}).get("enabled", False):
                github_updates = self._check_github_updates()
                available_updates.extend(github_updates)
            
            # Check local updates
            if self.update_config.get("update_sources", {}).get("local", {}).get("enabled", False):
                local_updates = self._check_local_updates()
                available_updates.extend(local_updates)
            
            # Filter updates newer than current version
            newer_updates = []
            for update in available_updates:
                if self._compare_versions(update["version"], self.current_version) > 0:
                    newer_updates.append(update)
            
            return {
                "current_version": self.current_version,
                "available_updates": newer_updates,
                "update_count": len(newer_updates),
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check for updates: {e}")
            return {
                "current_version": self.current_version,
                "available_updates": [],
                "update_count": 0,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def _check_github_updates(self) -> List[Dict]:
        """Check GitHub for updates."""
        try:
            github_config = self.update_config.get("update_sources", {}).get("github", {})
            repository = github_config.get("repository", "")
            branch = github_config.get("branch", "main")
            
            if not repository:
                return []
            
            # Get latest release information
            api_url = f"https://api.github.com/repos/{repository}/releases/latest"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                version = release_data.get("tag_name", "").lstrip("v")
                
                return [{
                    "source": "github",
                    "version": version,
                    "download_url": release_data.get("zipball_url", ""),
                    "release_notes": release_data.get("body", ""),
                    "published_at": release_data.get("published_at", ""),
                    "size": 0  # Size not available from API
                }]
            
            return []
            
        except Exception as e:
            self.logger.warning(f"Failed to check GitHub updates: {e}")
            return []
    
    def _check_local_updates(self) -> List[Dict]:
        """Check local directory for updates."""
        try:
            local_config = self.update_config.get("update_sources", {}).get("local", {})
            local_path = Path(local_config.get("path", "./updates"))
            
            if not local_path.exists():
                return []
            
            updates = []
            for update_file in local_path.glob("*.zip"):
                # Extract version from filename (e.g., "update_v1.2.3.zip")
                filename = update_file.stem
                if filename.startswith("update_v"):
                    version = filename[8:]  # Remove "update_v" prefix
                    updates.append({
                        "source": "local",
                        "version": version,
                        "file_path": str(update_file),
                        "size": update_file.stat().st_size,
                        "modified_at": datetime.fromtimestamp(update_file.stat().st_mtime).isoformat()
                    })
            
            return updates
            
        except Exception as e:
            self.logger.warning(f"Failed to check local updates: {e}")
            return []
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns 1 if version1 > version2, -1 if version1 < version2, 0 if equal."""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad with zeros to make same length
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 > v2:
                    return 1
                elif v1 < v2:
                    return -1
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to compare versions {version1} and {version2}: {e}")
            return 0
    
    def download_update(self, update_info: Dict[str, Any]) -> bool:
        """Download an update."""
        try:
            self.logger.info(f"Downloading update {update_info['version']}...")
            self.update_status = "downloading"
            self.update_progress = 0
            
            source = update_info.get("source", "")
            version = update_info["version"]
            
            if source == "github":
                return self._download_github_update(update_info)
            elif source == "local":
                return self._copy_local_update(update_info)
            else:
                self.logger.error(f"Unknown update source: {source}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to download update: {e}")
            self.update_status = "failed"
            return False
    
    def _download_github_update(self, update_info: Dict[str, Any]) -> bool:
        """Download update from GitHub."""
        try:
            download_url = update_info.get("download_url", "")
            version = update_info["version"]
            
            if not download_url:
                self.logger.error("No download URL provided")
                return False
            
            # Download the update
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Save to update directory
            update_file = self.update_dir / f"update_v{version}.zip"
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            self.update_progress = int((downloaded_size / total_size) * 100)
            
            self.logger.info(f"Downloaded update to {update_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download GitHub update: {e}")
            return False
    
    def _copy_local_update(self, update_info: Dict[str, Any]) -> bool:
        """Copy local update file."""
        try:
            source_path = Path(update_info.get("file_path", ""))
            version = update_info["version"]
            
            if not source_path.exists():
                self.logger.error(f"Local update file not found: {source_path}")
                return False
            
            # Copy to update directory
            update_file = self.update_dir / f"update_v{version}.zip"
            shutil.copy2(source_path, update_file)
            
            self.logger.info(f"Copied local update to {update_file}")
            self.update_progress = 100
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy local update: {e}")
            return False
    
    def install_update(self, version: str) -> bool:
        """Install an update."""
        try:
            self.logger.info(f"Installing update {version}...")
            self.update_status = "installing"
            self.update_progress = 0
            
            # Find update file
            update_file = self.update_dir / f"update_v{version}.zip"
            if not update_file.exists():
                self.logger.error(f"Update file not found: {update_file}")
                return False
            
            # Create backup if enabled
            if self.update_config.get("backup_before_update", True):
                if not self._create_backup():
                    self.logger.error("Failed to create backup before update")
                    return False
            
            # Extract update
            if not self._extract_update(update_file):
                self.logger.error("Failed to extract update")
                return False
            
            # Install update
            if not self._install_update_files(version):
                self.logger.error("Failed to install update files")
                if self.update_config.get("rollback_on_failure", True):
                    self._rollback_update()
                return False
            
            # Update version file
            self._update_version_file(version)
            
            # Record successful update
            self._add_update_record(version, "success", "Update installed successfully")
            
            self.logger.info(f"Update {version} installed successfully")
            self.update_status = "completed"
            self.update_progress = 100
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install update: {e}")
            self.update_status = "failed"
            self._add_update_record(version, "failed", str(e))
            return False
    
    def _create_backup(self) -> bool:
        """Create backup before update."""
        try:
            self.logger.info("Creating backup before update...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"pre_update_backup_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup important directories
            important_dirs = ["config", "logs", "scripts", "services", "api-client", "main"]
            
            for dir_name in important_dirs:
                source_dir = self.project_root / dir_name
                if source_dir.exists():
                    dest_dir = backup_path / dir_name
                    shutil.copytree(source_dir, dest_dir)
            
            # Backup version file
            if self.version_file.exists():
                shutil.copy2(self.version_file, backup_path / "VERSION")
            
            self.logger.info(f"Backup created at {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def _extract_update(self, update_file: Path) -> bool:
        """Extract update archive."""
        try:
            self.logger.info(f"Extracting update from {update_file}")
            
            extract_dir = self.update_dir / "extracted"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            self.logger.info("Update extracted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to extract update: {e}")
            return False
    
    def _install_update_files(self, version: str) -> bool:
        """Install update files."""
        try:
            self.logger.info("Installing update files...")
            
            extract_dir = self.update_dir / "extracted"
            
            # Find the actual project directory in the extracted files
            project_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if not project_dirs:
                self.logger.error("No project directory found in update")
                return False
            
            # Use the first directory (GitHub releases often have a single top-level directory)
            source_dir = project_dirs[0]
            
            # Copy files to project root
            important_dirs = ["config", "scripts", "services", "api-client", "main", "monitoring", "backup"]
            
            for dir_name in important_dirs:
                source_path = source_dir / dir_name
                if source_path.exists():
                    dest_path = self.project_root / dir_name
                    
                    # Backup existing directory
                    if dest_path.exists():
                        backup_path = self.project_root / f"{dir_name}.backup"
                        if backup_path.exists():
                            shutil.rmtree(backup_path)
                        shutil.move(dest_path, backup_path)
                    
                    # Copy new directory
                    shutil.copytree(source_path, dest_path)
                    self.logger.info(f"Updated {dir_name}")
            
            # Clean up extracted files
            shutil.rmtree(extract_dir)
            
            self.logger.info("Update files installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install update files: {e}")
            return False
    
    def _update_version_file(self, version: str):
        """Update version file."""
        try:
            with open(self.version_file, 'w') as f:
                f.write(version)
            self.current_version = version
            self.logger.info(f"Version updated to {version}")
        except Exception as e:
            self.logger.error(f"Failed to update version file: {e}")
    
    def _rollback_update(self):
        """Rollback the last update."""
        try:
            self.logger.info("Rolling back update...")
            
            # Find the most recent backup
            backup_dirs = [d for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith("pre_update_backup_")]
            if not backup_dirs:
                self.logger.error("No backup found for rollback")
                return False
            
            latest_backup = max(backup_dirs, key=lambda x: x.stat().st_mtime)
            
            # Restore from backup
            important_dirs = ["config", "logs", "scripts", "services", "api-client", "main"]
            
            for dir_name in important_dirs:
                backup_path = latest_backup / dir_name
                if backup_path.exists():
                    dest_path = self.project_root / dir_name
                    
                    # Remove current directory
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    
                    # Restore from backup
                    shutil.copytree(backup_path, dest_path)
                    self.logger.info(f"Restored {dir_name}")
            
            # Restore version file
            backup_version_file = latest_backup / "VERSION"
            if backup_version_file.exists():
                shutil.copy2(backup_version_file, self.version_file)
                with open(self.version_file, 'r') as f:
                    self.current_version = f.read().strip()
            
            self.logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback update: {e}")
            return False
    
    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status."""
        return {
            "current_version": self.current_version,
            "update_status": self.update_status,
            "update_progress": self.update_progress,
            "auto_update_enabled": self.update_config.get("auto_update_enabled", False),
            "last_check": self.update_history[-1]["timestamp"] if self.update_history else None,
            "update_history": self.update_history[-10:]  # Last 10 updates
        }
    
    def get_available_rollbacks(self) -> List[Dict[str, Any]]:
        """Get list of available rollback versions."""
        try:
            rollbacks = []
            
            # Get rollbacks from update history
            for record in reversed(self.update_history):
                if record["status"] == "success":
                    rollbacks.append({
                        "version": record["version"],
                        "timestamp": record["timestamp"],
                        "details": record["details"]
                    })
            
            # Limit to max rollback versions
            max_rollbacks = self.update_config.get("max_rollback_versions", 5)
            return rollbacks[:max_rollbacks]
            
        except Exception as e:
            self.logger.error(f"Failed to get available rollbacks: {e}")
            return []

def main():
    """Main function for testing."""
    import json
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "development_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create update manager
    update_manager = UpdateManager(config)
    
    # Check for updates
    updates = update_manager.check_for_updates()
    print(f"Available updates: {updates}")
    
    # Get update status
    status = update_manager.get_update_status()
    print(f"Update status: {status}")

if __name__ == "__main__":
    main()
