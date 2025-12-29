import os
import subprocess
import boto3
from datetime import datetime
from django.conf import settings
from celery import shared_task
from .models import BackupLog

@shared_task
def backup_database():
    """�������� ��������� ����� ���� ������"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
    
    try:
        # ��������� ���������� ����������� � ��
        db_settings = settings.DATABASES['default']
        
        # ������� ��� �������� ����� PostgreSQL
        cmd = [
            'pg_dump',
            '-h', db_settings['HOST'],
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '-f', backup_file
        ]
        
        # ��������� ���������� ��������� � �������
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        # ���������� �������
        start_time = datetime.now()
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        end_time = datetime.now()
        
        if result.returncode == 0:
            # �������� �������� ������
            file_size = os.path.getsize(backup_file)
            
            # ����������� ��������� ����������
            BackupLog.objects.create(
                file_path=backup_file,
                file_size=file_size,
                status='success',
                execution_time=(end_time - start_time).seconds
            )
            
            # �������� � �������� ���������
            upload_to_cloud(backup_file)
            
            # ������� ������ ������� (��������� ��������� 30)
            cleanup_old_backups(backup_dir, keep_count=30)
            
            return f"Backup created successfully: {backup_file}"
        else:
            # ������ ��� �������� ������
            BackupLog.objects.create(
                file_path=backup_file,
                status='error',
                error_message=result.stderr
            )
            return f"Backup failed: {result.stderr}"
            
    except Exception as e:
        BackupLog.objects.create(
            file_path=backup_file,
            status='error',
            error_message=str(e)
        )
        return f"Backup failed: {str(e)}"

def upload_to_cloud(file_path):
    """�������� ����� � �������� ���������"""
    
    # ������ ��� ������.�����
    if hasattr(settings, 'YANDEX_DISK_TOKEN'):
        try:
            from yadisk import YaDisk
            yandex = YaDisk(token=settings.YANDEX_DISK_TOKEN)
            
            remote_path = f"/library_backups/{os.path.basename(file_path)}"
            yandex.upload(file_path, remote_path)
            
            return True
        except Exception as e:
            print(f"Failed to upload to Yandex.Disk: {str(e)}")
    
    # ������ ��� AWS S3
    if hasattr(settings, 'AWS_ACCESS_KEY_ID'):
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            s3_key = f"backups/{os.path.basename(file_path)}"
            
            s3_client.upload_file(file_path, bucket_name, s3_key)
            
            return True
        except Exception as e:
            print(f"Failed to upload to AWS S3: {str(e)}")
    
    return False

def cleanup_old_backups(backup_dir, keep_count=30):
    """�������� ������ ��������� �����"""
    
    try:
        # ��������� ������ ������ �������
        backup_files = []
        for file_name in os.listdir(backup_dir):
            if file_name.startswith('backup_') and file_name.endswith('.sql'):
                file_path = os.path.join(backup_dir, file_name)
                if os.path.isfile(file_path):
                    backup_files.append((file_path, os.path.getmtime(file_path)))
        
        # ���������� �� ���� ��������� (������� ������)
        backup_files.sort(key=lambda x: x[1])
        
        # �������� ������ ������
        if len(backup_files) > keep_count:
            files_to_delete = backup_files[:-keep_count]
            for file_path, _ in files_to_delete:
                os.remove(file_path)
                print(f"Deleted old backup: {file_path}")
    
    except Exception as e:
        print(f"Error cleaning up old backups: {str(e)}")

CELERY_BEAT_SCHEDULE = {
    'daily-backup': {
        'task': 'library.tasks.backup_database',
        'schedule': 86400.0,  # ������ 24 ����
    },
}