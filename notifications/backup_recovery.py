import asyncio
import json
import os
import shutil
import gzip
import pickle
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sqlite3
import boto3
from botocore.exceptions import ClientError

from .logging_config import NotificationLogger
from .monitoring import SystemMonitor
from .database_optimization import DatabaseOptimizer


class BackupType(Enum):
    """Types of backups."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"
    CONTINUOUS = "continuous"


class BackupStatus(Enum):
    """Status of backup operations."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VERIFYING = "verifying"
    VERIFIED = "verified"


class RecoveryType(Enum):
    """Types of recovery operations."""
    FULL_RESTORE = "full_restore"
    PARTIAL_RESTORE = "partial_restore"
    POINT_IN_TIME = "point_in_time"
    TABLE_RESTORE = "table_restore"
    DATA_MIGRATION = "data_migration"


class StorageProvider(Enum):
    """Storage providers for backups."""
    LOCAL = "local"
    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"
    GOOGLE_CLOUD = "google_cloud"
    FTP = "ftp"
    NETWORK_SHARE = "network_share"


@dataclass
class BackupConfig:
    """Configuration for backup operations."""
    backup_type: BackupType
    storage_provider: StorageProvider
    destination_path: str
    retention_days: int = 30
    compression_enabled: bool = True
    encryption_enabled: bool = True
    encryption_key: Optional[str] = None
    max_parallel_operations: int = 4
    verify_after_backup: bool = True
    notification_on_completion: bool = True
    notification_on_failure: bool = True
    schedule_cron: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BackupRecord:
    """Record of a backup operation."""
    backup_id: str
    backup_type: BackupType
    status: BackupStatus
    source_path: str
    destination_path: str
    file_size: int = 0
    compressed_size: int = 0
    checksum: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    verification_status: Optional[bool] = None
    retention_until: Optional[datetime] = None


@dataclass
class RecoveryRecord:
    """Record of a recovery operation."""
    recovery_id: str
    recovery_type: RecoveryType
    backup_id: str
    target_path: str
    status: BackupStatus
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    recovered_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to the storage backend."""
        pass
    
    @abstractmethod
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from the storage backend."""
        pass
    
    @abstractmethod
    async def delete_file(self, remote_path: str) -> bool:
        """Delete a file from the storage backend."""
        pass
    
    @abstractmethod
    async def list_files(self, remote_path: str) -> List[str]:
        """List files in the storage backend."""
        pass
    
    @abstractmethod
    async def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in the storage backend."""
        pass
    
    @abstractmethod
    async def get_file_size(self, remote_path: str) -> int:
        """Get the size of a file in the storage backend."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger = NotificationLogger()
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Copy file to local storage."""
        try:
            dest_path = self.base_path / remote_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            await asyncio.get_event_loop().run_in_executor(
                None, shutil.copy2, local_path, str(dest_path)
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to upload file {local_path}: {e}")
            return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Copy file from local storage."""
        try:
            source_path = self.base_path / remote_path
            
            if not source_path.exists():
                return False
            
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            await asyncio.get_event_loop().run_in_executor(
                None, shutil.copy2, str(source_path), local_path
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to download file {remote_path}: {e}")
            return False
    
    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from local storage."""
        try:
            file_path = self.base_path / remote_path
            
            if file_path.exists():
                await asyncio.get_event_loop().run_in_executor(
                    None, file_path.unlink
                )
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file {remote_path}: {e}")
            return False
    
    async def list_files(self, remote_path: str) -> List[str]:
        """List files in local storage."""
        try:
            dir_path = self.base_path / remote_path
            
            if not dir_path.exists():
                return []
            
            files = []
            for item in dir_path.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(self.base_path)
                    files.append(str(relative_path))
            
            return files
        except Exception as e:
            self.logger.error(f"Failed to list files in {remote_path}: {e}")
            return []
    
    async def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in local storage."""
        file_path = self.base_path / remote_path
        return file_path.exists()
    
    async def get_file_size(self, remote_path: str) -> int:
        """Get file size in local storage."""
        try:
            file_path = self.base_path / remote_path
            return file_path.stat().st_size if file_path.exists() else 0
        except Exception:
            return 0


class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend."""
    
    def __init__(self, bucket_name: str, aws_access_key: str, aws_secret_key: str, region: str = 'us-east-1'):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        self.logger = NotificationLogger()
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to S3."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.s3_client.upload_file, local_path, self.bucket_name, remote_path
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to upload file to S3 {remote_path}: {e}")
            return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from S3."""
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            await asyncio.get_event_loop().run_in_executor(
                None, self.s3_client.download_file, self.bucket_name, remote_path, local_path
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to download file from S3 {remote_path}: {e}")
            return False
    
    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from S3."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.s3_client.delete_object, {'Bucket': self.bucket_name, 'Key': remote_path}
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file from S3 {remote_path}: {e}")
            return False
    
    async def list_files(self, remote_path: str) -> List[str]:
        """List files in S3."""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.s3_client.list_objects_v2, {'Bucket': self.bucket_name, 'Prefix': remote_path}
            )
            
            files = []
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
            
            return files
        except Exception as e:
            self.logger.error(f"Failed to list files in S3 {remote_path}: {e}")
            return []
    
    async def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in S3."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.s3_client.head_object, {'Bucket': self.bucket_name, 'Key': remote_path}
            )
            return True
        except ClientError:
            return False
        except Exception as e:
            self.logger.error(f"Error checking file existence in S3 {remote_path}: {e}")
            return False
    
    async def get_file_size(self, remote_path: str) -> int:
        """Get file size in S3."""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.s3_client.head_object, {'Bucket': self.bucket_name, 'Key': remote_path}
            )
            return response.get('ContentLength', 0)
        except Exception:
            return 0


class BackupManager:
    """Manages backup operations."""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.backup_records: Dict[str, BackupRecord] = {}
        self.logger = NotificationLogger()
        self.storage_backend = self._create_storage_backend()
        self.running = False
        self._backup_thread = None
        self._cleanup_thread = None
        self._lock = threading.Lock()
    
    def _create_storage_backend(self) -> StorageBackend:
        """Create storage backend based on configuration."""
        if self.config.storage_provider == StorageProvider.LOCAL:
            return LocalStorageBackend(self.config.destination_path)
        elif self.config.storage_provider == StorageProvider.AWS_S3:
            # Extract S3 configuration from metadata
            bucket = self.config.metadata.get('bucket_name')
            access_key = self.config.metadata.get('aws_access_key')
            secret_key = self.config.metadata.get('aws_secret_key')
            region = self.config.metadata.get('region', 'us-east-1')
            return S3StorageBackend(bucket, access_key, secret_key, region)
        else:
            raise ValueError(f"Unsupported storage provider: {self.config.storage_provider}")
    
    def start(self):
        """Start the backup manager."""
        self.running = True
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_old_backups, daemon=True)
        self._cleanup_thread.start()
        
        self.logger.info("Backup manager started")
    
    def stop(self):
        """Stop the backup manager."""
        self.running = False
        
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        self.logger.info("Backup manager stopped")
    
    async def create_backup(self, source_path: str, backup_id: Optional[str] = None) -> str:
        """Create a backup of the specified source."""
        if not backup_id:
            backup_id = f"backup_{int(time.time())}_{hashlib.md5(source_path.encode()).hexdigest()[:8]}"
        
        # Create backup record
        backup_record = BackupRecord(
            backup_id=backup_id,
            backup_type=self.config.backup_type,
            status=BackupStatus.PENDING,
            source_path=source_path,
            destination_path=f"{backup_id}.backup",
            retention_until=datetime.now() + timedelta(days=self.config.retention_days)
        )
        
        with self._lock:
            self.backup_records[backup_id] = backup_record
        
        try:
            backup_record.status = BackupStatus.RUNNING
            backup_record.started_at = datetime.now()
            
            # Create backup file
            backup_file_path = await self._create_backup_file(source_path, backup_record)
            
            if backup_file_path:
                # Upload to storage backend
                success = await self.storage_backend.upload_file(
                    backup_file_path, backup_record.destination_path
                )
                
                if success:
                    # Calculate file sizes and checksum
                    backup_record.file_size = os.path.getsize(backup_file_path)
                    backup_record.checksum = await self._calculate_checksum(backup_file_path)
                    
                    # Verify backup if enabled
                    if self.config.verify_after_backup:
                        backup_record.status = BackupStatus.VERIFYING
                        verification_result = await self._verify_backup(backup_record)
                        backup_record.verification_status = verification_result
                        backup_record.status = BackupStatus.VERIFIED if verification_result else BackupStatus.FAILED
                    else:
                        backup_record.status = BackupStatus.COMPLETED
                    
                    backup_record.completed_at = datetime.now()
                    
                    # Clean up local backup file
                    try:
                        os.remove(backup_file_path)
                    except Exception as e:
                        self.logger.warning(f"Failed to clean up local backup file: {e}")
                    
                    self.logger.info(f"Backup {backup_id} completed successfully")
                else:
                    backup_record.status = BackupStatus.FAILED
                    backup_record.error_message = "Failed to upload backup to storage backend"
                    backup_record.completed_at = datetime.now()
            else:
                backup_record.status = BackupStatus.FAILED
                backup_record.error_message = "Failed to create backup file"
                backup_record.completed_at = datetime.now()
        
        except Exception as e:
            backup_record.status = BackupStatus.FAILED
            backup_record.error_message = str(e)
            backup_record.completed_at = datetime.now()
            self.logger.error(f"Backup {backup_id} failed: {e}")
        
        return backup_id
    
    async def _create_backup_file(self, source_path: str, backup_record: BackupRecord) -> Optional[str]:
        """Create a backup file from the source."""
        try:
            temp_backup_path = f"/tmp/{backup_record.backup_id}.backup"
            
            if os.path.isfile(source_path):
                # Single file backup
                if self.config.compression_enabled:
                    await self._compress_file(source_path, temp_backup_path)
                else:
                    shutil.copy2(source_path, temp_backup_path)
            
            elif os.path.isdir(source_path):
                # Directory backup
                await self._create_archive(source_path, temp_backup_path)
            
            else:
                # Database backup (assuming SQLite for this example)
                await self._create_database_backup(source_path, temp_backup_path)
            
            # Encrypt if enabled
            if self.config.encryption_enabled:
                encrypted_path = f"{temp_backup_path}.encrypted"
                await self._encrypt_file(temp_backup_path, encrypted_path)
                os.remove(temp_backup_path)
                return encrypted_path
            
            return temp_backup_path
        
        except Exception as e:
            self.logger.error(f"Failed to create backup file: {e}")
            return None
    
    async def _compress_file(self, source_path: str, dest_path: str):
        """Compress a file using gzip."""
        def compress():
            with open(source_path, 'rb') as f_in:
                with gzip.open(dest_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        
        await asyncio.get_event_loop().run_in_executor(None, compress)
    
    async def _create_archive(self, source_dir: str, dest_path: str):
        """Create a compressed archive of a directory."""
        def create_archive():
            if self.config.compression_enabled:
                shutil.make_archive(dest_path.replace('.backup', ''), 'gztar', source_dir)
                # Rename to .backup extension
                archive_path = f"{dest_path.replace('.backup', '')}.tar.gz"
                if os.path.exists(archive_path):
                    shutil.move(archive_path, dest_path)
            else:
                shutil.make_archive(dest_path.replace('.backup', ''), 'tar', source_dir)
                archive_path = f"{dest_path.replace('.backup', '')}.tar"
                if os.path.exists(archive_path):
                    shutil.move(archive_path, dest_path)
        
        await asyncio.get_event_loop().run_in_executor(None, create_archive)
    
    async def _create_database_backup(self, db_path: str, dest_path: str):
        """Create a database backup."""
        def backup_database():
            # For SQLite databases
            if db_path.endswith('.db') or db_path.endswith('.sqlite'):
                with sqlite3.connect(db_path) as source_conn:
                    with sqlite3.connect(dest_path) as backup_conn:
                        source_conn.backup(backup_conn)
            else:
                # For other databases, use dump commands
                # This is a simplified example
                shutil.copy2(db_path, dest_path)
        
        await asyncio.get_event_loop().run_in_executor(None, backup_database)
    
    async def _encrypt_file(self, source_path: str, dest_path: str):
        """Encrypt a file (simplified implementation)."""
        # This is a simplified encryption example
        # In production, use proper encryption libraries like cryptography
        def encrypt():
            with open(source_path, 'rb') as f_in:
                with open(dest_path, 'wb') as f_out:
                    data = f_in.read()
                    # Simple XOR encryption (NOT secure for production)
                    key = self.config.encryption_key or "default_key"
                    encrypted_data = bytes(a ^ ord(key[i % len(key)]) for i, a in enumerate(data))
                    f_out.write(encrypted_data)
        
        await asyncio.get_event_loop().run_in_executor(None, encrypt)
    
    async def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of a file."""
        def calculate():
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        
        return await asyncio.get_event_loop().run_in_executor(None, calculate)
    
    async def _verify_backup(self, backup_record: BackupRecord) -> bool:
        """Verify the integrity of a backup."""
        try:
            # Download backup file temporarily
            temp_path = f"/tmp/verify_{backup_record.backup_id}.backup"
            
            success = await self.storage_backend.download_file(
                backup_record.destination_path, temp_path
            )
            
            if not success:
                return False
            
            # Verify checksum
            actual_checksum = await self._calculate_checksum(temp_path)
            checksum_valid = actual_checksum == backup_record.checksum
            
            # Clean up temporary file
            try:
                os.remove(temp_path)
            except Exception:
                pass
            
            return checksum_valid
        
        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Clean up old backups based on retention policy."""
        while self.running:
            try:
                current_time = datetime.now()
                expired_backups = []
                
                with self._lock:
                    for backup_id, record in self.backup_records.items():
                        if (record.retention_until and 
                            current_time > record.retention_until and
                            record.status == BackupStatus.COMPLETED):
                            expired_backups.append(backup_id)
                
                # Delete expired backups
                for backup_id in expired_backups:
                    asyncio.create_task(self._delete_backup(backup_id))
                
                time.sleep(3600)  # Check every hour
            
            except Exception as e:
                self.logger.error(f"Error in backup cleanup: {e}")
                time.sleep(3600)
    
    async def _delete_backup(self, backup_id: str) -> bool:
        """Delete a backup."""
        try:
            backup_record = self.backup_records.get(backup_id)
            if not backup_record:
                return False
            
            # Delete from storage backend
            success = await self.storage_backend.delete_file(backup_record.destination_path)
            
            if success:
                with self._lock:
                    del self.backup_records[backup_id]
                
                self.logger.info(f"Deleted expired backup {backup_id}")
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
    
    def get_backup_status(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a backup."""
        backup_record = self.backup_records.get(backup_id)
        if not backup_record:
            return None
        
        return {
            'backup_id': backup_record.backup_id,
            'backup_type': backup_record.backup_type.value,
            'status': backup_record.status.value,
            'source_path': backup_record.source_path,
            'destination_path': backup_record.destination_path,
            'file_size': backup_record.file_size,
            'compressed_size': backup_record.compressed_size,
            'checksum': backup_record.checksum,
            'created_at': backup_record.created_at.isoformat(),
            'started_at': backup_record.started_at.isoformat() if backup_record.started_at else None,
            'completed_at': backup_record.completed_at.isoformat() if backup_record.completed_at else None,
            'error_message': backup_record.error_message,
            'verification_status': backup_record.verification_status,
            'retention_until': backup_record.retention_until.isoformat() if backup_record.retention_until else None
        }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all backups."""
        with self._lock:
            return [self.get_backup_status(backup_id) for backup_id in self.backup_records.keys()]


class RecoveryManager:
    """Manages recovery operations."""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.recovery_records: Dict[str, RecoveryRecord] = {}
        self.logger = NotificationLogger()
        self._lock = threading.Lock()
    
    async def restore_backup(self, backup_id: str, target_path: str, 
                           recovery_type: RecoveryType = RecoveryType.FULL_RESTORE) -> str:
        """Restore a backup to the specified target path."""
        recovery_id = f"recovery_{int(time.time())}_{backup_id[:8]}"
        
        # Create recovery record
        recovery_record = RecoveryRecord(
            recovery_id=recovery_id,
            recovery_type=recovery_type,
            backup_id=backup_id,
            target_path=target_path,
            status=BackupStatus.PENDING
        )
        
        with self._lock:
            self.recovery_records[recovery_id] = recovery_record
        
        try:
            recovery_record.status = BackupStatus.RUNNING
            recovery_record.started_at = datetime.now()
            
            # Get backup record
            backup_record = self.backup_manager.backup_records.get(backup_id)
            if not backup_record:
                raise ValueError(f"Backup {backup_id} not found")
            
            if backup_record.status != BackupStatus.COMPLETED:
                raise ValueError(f"Backup {backup_id} is not in completed state")
            
            # Download backup file
            temp_backup_path = f"/tmp/restore_{recovery_id}.backup"
            
            success = await self.backup_manager.storage_backend.download_file(
                backup_record.destination_path, temp_backup_path
            )
            
            if not success:
                raise Exception("Failed to download backup file")
            
            # Decrypt if needed
            if self.backup_manager.config.encryption_enabled:
                decrypted_path = f"{temp_backup_path}.decrypted"
                await self._decrypt_file(temp_backup_path, decrypted_path)
                os.remove(temp_backup_path)
                temp_backup_path = decrypted_path
            
            # Restore based on recovery type
            if recovery_type == RecoveryType.FULL_RESTORE:
                await self._restore_full(temp_backup_path, target_path, recovery_record)
            elif recovery_type == RecoveryType.PARTIAL_RESTORE:
                await self._restore_partial(temp_backup_path, target_path, recovery_record)
            elif recovery_type == RecoveryType.TABLE_RESTORE:
                await self._restore_table(temp_backup_path, target_path, recovery_record)
            
            recovery_record.status = BackupStatus.COMPLETED
            recovery_record.completed_at = datetime.now()
            
            # Clean up temporary files
            try:
                os.remove(temp_backup_path)
            except Exception:
                pass
            
            self.logger.info(f"Recovery {recovery_id} completed successfully")
        
        except Exception as e:
            recovery_record.status = BackupStatus.FAILED
            recovery_record.error_message = str(e)
            recovery_record.completed_at = datetime.now()
            self.logger.error(f"Recovery {recovery_id} failed: {e}")
        
        return recovery_id
    
    async def _decrypt_file(self, source_path: str, dest_path: str):
        """Decrypt a file (simplified implementation)."""
        def decrypt():
            with open(source_path, 'rb') as f_in:
                with open(dest_path, 'wb') as f_out:
                    data = f_in.read()
                    # Simple XOR decryption (matches encryption)
                    key = self.backup_manager.config.encryption_key or "default_key"
                    decrypted_data = bytes(a ^ ord(key[i % len(key)]) for i, a in enumerate(data))
                    f_out.write(decrypted_data)
        
        await asyncio.get_event_loop().run_in_executor(None, decrypt)
    
    async def _restore_full(self, backup_path: str, target_path: str, recovery_record: RecoveryRecord):
        """Perform a full restore."""
        def restore():
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            if backup_path.endswith('.tar.gz') or backup_path.endswith('.tar'):
                # Extract archive
                shutil.unpack_archive(backup_path, target_path)
                recovery_record.recovered_files = [target_path]
            elif self.backup_manager.config.compression_enabled:
                # Decompress file
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(target_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                recovery_record.recovered_files = [target_path]
            else:
                # Direct copy
                shutil.copy2(backup_path, target_path)
                recovery_record.recovered_files = [target_path]
        
        await asyncio.get_event_loop().run_in_executor(None, restore)
    
    async def _restore_partial(self, backup_path: str, target_path: str, recovery_record: RecoveryRecord):
        """Perform a partial restore."""
        # This is a simplified implementation
        # In practice, this would involve more complex logic to restore specific files/tables
        await self._restore_full(backup_path, target_path, recovery_record)
    
    async def _restore_table(self, backup_path: str, target_path: str, recovery_record: RecoveryRecord):
        """Restore specific database tables."""
        # This is a simplified implementation
        # In practice, this would involve database-specific restore logic
        await self._restore_full(backup_path, target_path, recovery_record)
    
    def get_recovery_status(self, recovery_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a recovery operation."""
        recovery_record = self.recovery_records.get(recovery_id)
        if not recovery_record:
            return None
        
        return {
            'recovery_id': recovery_record.recovery_id,
            'recovery_type': recovery_record.recovery_type.value,
            'backup_id': recovery_record.backup_id,
            'target_path': recovery_record.target_path,
            'status': recovery_record.status.value,
            'created_at': recovery_record.created_at.isoformat(),
            'started_at': recovery_record.started_at.isoformat() if recovery_record.started_at else None,
            'completed_at': recovery_record.completed_at.isoformat() if recovery_record.completed_at else None,
            'error_message': recovery_record.error_message,
            'recovered_files': recovery_record.recovered_files
        }
    
    def list_recoveries(self) -> List[Dict[str, Any]]:
        """List all recovery operations."""
        with self._lock:
            return [self.get_recovery_status(recovery_id) for recovery_id in self.recovery_records.keys()]


class BackupRecoveryManager:
    """Main manager for backup and recovery operations."""
    
    def __init__(self, backup_config: BackupConfig):
        self.backup_manager = BackupManager(backup_config)
        self.recovery_manager = RecoveryManager(self.backup_manager)
        self.logger = NotificationLogger()
        self.monitor = SystemMonitor()
    
    def start(self):
        """Start the backup and recovery manager."""
        self.backup_manager.start()
        self.logger.info("Backup and recovery manager started")
    
    def stop(self):
        """Stop the backup and recovery manager."""
        self.backup_manager.stop()
        self.logger.info("Backup and recovery manager stopped")
    
    async def create_notification_backup(self) -> str:
        """Create a backup of notification system data."""
        # This would backup notification database, configuration files, etc.
        notification_data_path = "notifications/data"
        return await self.backup_manager.create_backup(notification_data_path)
    
    async def restore_notification_backup(self, backup_id: str, target_path: str = "notifications/data") -> str:
        """Restore a notification system backup."""
        return await self.recovery_manager.restore_backup(backup_id, target_path)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive backup and recovery system status."""
        return {
            'backup_manager': {
                'running': self.backup_manager.running,
                'total_backups': len(self.backup_manager.backup_records),
                'recent_backups': self.backup_manager.list_backups()[-10:]  # Last 10 backups
            },
            'recovery_manager': {
                'total_recoveries': len(self.recovery_manager.recovery_records),
                'recent_recoveries': self.recovery_manager.list_recoveries()[-10:]  # Last 10 recoveries
            },
            'storage_config': {
                'provider': self.backup_manager.config.storage_provider.value,
                'retention_days': self.backup_manager.config.retention_days,
                'compression_enabled': self.backup_manager.config.compression_enabled,
                'encryption_enabled': self.backup_manager.config.encryption_enabled
            },
            'timestamp': datetime.now().isoformat()
        }


# Utility functions for easy backup and recovery operations
async def create_database_backup(db_path: str, config: BackupConfig) -> str:
    """Create a database backup."""
    manager = BackupManager(config)
    return await manager.create_backup(db_path)


async def restore_database_backup(backup_id: str, target_path: str, config: BackupConfig) -> str:
    """Restore a database backup."""
    backup_manager = BackupManager(config)
    recovery_manager = RecoveryManager(backup_manager)
    return await recovery_manager.restore_backup(backup_id, target_path)


def create_backup_config(storage_provider: StorageProvider, destination_path: str, **kwargs) -> BackupConfig:
    """Create a backup configuration with sensible defaults."""
    return BackupConfig(
        backup_type=kwargs.get('backup_type', BackupType.FULL),
        storage_provider=storage_provider,
        destination_path=destination_path,
        retention_days=kwargs.get('retention_days', 30),
        compression_enabled=kwargs.get('compression_enabled', True),
        encryption_enabled=kwargs.get('encryption_enabled', True),
        encryption_key=kwargs.get('encryption_key'),
        max_parallel_operations=kwargs.get('max_parallel_operations', 4),
        verify_after_backup=kwargs.get('verify_after_backup', True),
        notification_on_completion=kwargs.get('notification_on_completion', True),
        notification_on_failure=kwargs.get('notification_on_failure', True),
        metadata=kwargs.get('metadata', {})
    )