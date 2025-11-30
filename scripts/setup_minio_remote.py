#!/usr/bin/env python3
"""
Скрипт для автоматической настройки MinIO как удаленного хранилища DVC.
MinIO - это S3-совместимое объектное хранилище, которое можно запустить локально.
"""

import subprocess
import sys
import shutil
import os
import re
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

def check_dvc_installed() -> bool:
    """Проверка установки DVC."""
    if not shutil.which("dvc"):
        print("❌ Ошибка: DVC не установлен")
        print("Установите DVC: pip install dvc dvc-s3")
        return False
    return True

def check_minio_client_installed() -> bool:
    """Проверка установки MinIO Client (mc)."""
    if not shutil.which("mc"):
        print("⚠️  MinIO Client (mc) не установлен")
        print("Это необязательно, но полезно для управления MinIO")
        print("Установите: https://min.io/docs/minio/linux/reference/minio-mc.html")
        return False
    return True

def validate_endpoint(endpoint: str) -> bool:
    """Валидация endpoint URL."""
    try:
        parsed = urlparse(endpoint)
        if parsed.scheme not in ['http', 'https']:
            print("❌ Endpoint должен начинаться с http:// или https://")
            return False
        if not parsed.netloc:
            print("❌ Endpoint должен содержать hostname и порт")
            return False
        return True
    except Exception as e:
        print(f"❌ Ошибка валидации endpoint: {e}")
        return False

def test_minio_connection(endpoint: str, access_key: str, secret_key: str) -> bool:
    """Тестирование подключения к MinIO."""
    print(f"\nТестирование подключения к MinIO ({endpoint})...")
    
    try:
        # Используем AWS CLI для проверки подключения
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = access_key
        env['AWS_SECRET_ACCESS_KEY'] = secret_key
        env['AWS_ENDPOINT_URL'] = endpoint
        
        # Пытаемся выполнить простую операцию
        result = subprocess.run(
            ["aws", "--endpoint-url", endpoint, "s3", "ls"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Подключение к MinIO успешно!")
            return True
        else:
            print(f"⚠️  Не удалось подключиться: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Таймаут при подключении к MinIO")
        print("Проверьте, что MinIO запущен и доступен по указанному адресу")
        return False
    except FileNotFoundError:
        print("⚠️  AWS CLI не установлен, пропускаем проверку подключения")
        print("Установите AWS CLI для проверки: pip install awscli")
        return True  # Не критично, если AWS CLI не установлен
    except Exception as e:
        print(f"⚠️  Ошибка при проверке подключения: {e}")
        return False

def create_bucket_minio(endpoint: str, bucket_name: str, access_key: str, secret_key: str) -> bool:
    """Создание bucket в MinIO."""
    print(f"\nСоздание bucket '{bucket_name}' в MinIO...")
    
    try:
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = access_key
        env['AWS_SECRET_ACCESS_KEY'] = secret_key
        env['AWS_ENDPOINT_URL'] = endpoint
        
        # Создаем bucket
        result = subprocess.run(
            ["aws", "--endpoint-url", endpoint, "s3", "mb", f"s3://{bucket_name}"],
            env=env,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            print(f"✅ Bucket '{bucket_name}' создан успешно")
            return True
        else:
            if "BucketAlreadyExists" in result.stderr or "BucketAlreadyOwnedByYou" in result.stderr:
                print(f"✅ Bucket '{bucket_name}' уже существует")
                return True
            else:
                print(f"⚠️  Не удалось создать bucket: {result.stderr}")
                print("Попробуйте создать bucket вручную через MinIO Console или mc")
                return False
    except FileNotFoundError:
        print("⚠️  AWS CLI не установлен, пропускаем создание bucket")
        print("Создайте bucket вручную через MinIO Console: http://localhost:9001")
        return True
    except Exception as e:
        print(f"⚠️  Ошибка при создании bucket: {e}")
        return False

def setup_dvc_remote_minio(endpoint: str, bucket_name: str, access_key: str, secret_key: str, 
                           remote_name: str = "minio", path: str = "dvc-storage") -> bool:
    """Настройка DVC remote для MinIO."""
    # MinIO использует специальный формат URL для S3-совместимых хранилищ
    # DVC требует указать endpoint через параметр endpointurl
    s3_url = f"s3://{bucket_name}/{path}"
    
    print(f"\nНастройка DVC remote '{remote_name}' -> {s3_url}...")
    print(f"Endpoint: {endpoint}")
    
    # Проверяем, существует ли уже remote с таким именем
    result = subprocess.run(
        ["dvc", "remote", "list"],
        capture_output=True,
        text=True
    )
    
    if remote_name in result.stdout:
        print(f"⚠️  Remote '{remote_name}' уже существует")
        response = input(f"Перезаписать remote '{remote_name}'? (y/N): ").strip().lower()
        if response != 'y':
            print("Отменено пользователем")
            return False
        
        # Удаляем существующий remote
        subprocess.run(
            ["dvc", "remote", "remove", remote_name],
            capture_output=True
        )
    
    # Добавляем remote
    result = subprocess.run(
        ["dvc", "remote", "add", "-d", remote_name, s3_url],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Ошибка при добавлении remote: {result.stderr}")
        return False
    
    print(f"✅ Remote '{remote_name}' добавлен")
    
    # Настраиваем endpoint для MinIO
    result = subprocess.run(
        ["dvc", "remote", "modify", remote_name, "endpointurl", endpoint],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"⚠️  Предупреждение: не удалось настроить endpoint: {result.stderr}")
    else:
        print(f"✅ Endpoint настроен: {endpoint}")
    
    # Настраиваем credentials
    result = subprocess.run(
        ["dvc", "remote", "modify", remote_name, "access_key_id", access_key],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Access Key ID настроен")
    else:
        print(f"⚠️  Предупреждение: не удалось настроить access_key_id")
    
    result = subprocess.run(
        ["dvc", "remote", "modify", remote_name, "secret_access_key", secret_key],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Secret Access Key настроен")
    else:
        print(f"⚠️  Предупреждение: не удалось настроить secret_access_key")
    
    return True

def test_dvc_connection(remote_name: str) -> bool:
    """Тестирование подключения DVC к MinIO."""
    print(f"\nТестирование подключения DVC к MinIO...")
    
    try:
        # Пытаемся выполнить dvc status для проверки подключения
        result = subprocess.run(
            ["dvc", "remote", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if remote_name in result.stdout:
            print("✅ DVC remote настроен корректно")
            return True
        else:
            print("⚠️  Remote не найден в списке")
            return False
    except Exception as e:
        print(f"⚠️  Ошибка при проверке: {e}")
        return False

def main():
    """Главная функция."""
    print("=" * 60)
    print("Автоматическая настройка MinIO для DVC")
    print("=" * 60)
    
    # Проверки
    if not check_dvc_installed():
        sys.exit(1)
    
    check_minio_client_installed()  # Не критично
    
    # Проверка DVC инициализации
    dvc_dir = Path(".dvc")
    if not dvc_dir.exists() or not (dvc_dir / "config").exists():
        print("❌ DVC не инициализирован")
        print("Сначала выполните: python3 scripts/init_dvc.py")
        sys.exit(1)
    
    # Запрос параметров
    print("\n" + "-" * 60)
    print("Настройка MinIO для DVC")
    print("-" * 60)
    print("\n💡 MinIO должен быть запущен перед настройкой")
    print("   Запустите MinIO: docker run -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ':9001'")
    print("   Или используйте локальную установку MinIO")
    print()
    
    endpoint = input("Введите MinIO endpoint (по умолчанию: http://localhost:9000): ").strip() or "http://localhost:9000"
    
    if not validate_endpoint(endpoint):
        sys.exit(1)
    
    access_key = input("Введите MinIO Access Key (по умолчанию: minioadmin): ").strip() or "minioadmin"
    secret_key = input("Введите MinIO Secret Key (по умолчанию: minioadmin): ").strip() or "minioadmin"
    
    username = os.getenv("USER", os.getenv("USERNAME", "user"))
    default_bucket = f"dvc-storage-{username.lower()}"
    bucket_name = input(f"Введите имя bucket (по умолчанию: {default_bucket}): ").strip() or default_bucket
    
    # Валидация имени bucket (S3 правила)
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        print("❌ Имя bucket должно быть от 3 до 63 символов")
        sys.exit(1)
    
    if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', bucket_name):
        print("❌ Имя bucket может содержать только строчные буквы, цифры, точки и дефисы")
        sys.exit(1)
    
    remote_name = input("Введите имя для DVC remote (по умолчанию: minio): ").strip() or "minio"
    path = input("Введите путь в bucket для DVC (по умолчанию: dvc-storage): ").strip() or "dvc-storage"
    
    # Тестирование подключения
    if not test_minio_connection(endpoint, access_key, secret_key):
        print("\n⚠️  Не удалось подключиться к MinIO")
        print("Убедитесь, что MinIO запущен и доступен")
        response = input("Продолжить настройку? (y/N): ").strip().lower()
        if response != 'y':
            print("Отменено")
            sys.exit(1)
    
    # Создание bucket
    create_bucket_minio(endpoint, bucket_name, access_key, secret_key)
    
    # Настройка DVC remote
    if not setup_dvc_remote_minio(endpoint, bucket_name, access_key, secret_key, remote_name, path):
        sys.exit(1)
    
    # Тестирование DVC подключения
    test_dvc_connection(remote_name)
    
    # Итоговая информация
    print("\n" + "=" * 60)
    print("✅ Настройка MinIO завершена успешно!")
    print("=" * 60)
    print(f"\nНастройки:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Bucket: {bucket_name}")
    print(f"  Remote name: {remote_name}")
    print(f"  Path: {path}")
    print(f"\nСледующие шаги:")
    print(f"  1. Проверьте настройку: dvc remote list")
    print(f"  2. Проверьте детали: dvc remote modify {remote_name} --list")
    print(f"  3. Загрузите данные: dvc push")
    print(f"  4. Закоммитьте изменения: git add .dvc/config")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)

