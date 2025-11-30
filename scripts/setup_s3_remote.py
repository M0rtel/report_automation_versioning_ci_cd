#!/usr/bin/env python3
"""
Скрипт для автоматической настройки AWS S3 как удаленного хранилища DVC.
"""

import subprocess
import sys
import shutil
import os
import re
import configparser
import json
from pathlib import Path
from typing import Optional, Tuple

def check_aws_cli_installed() -> bool:
    """Проверка установки AWS CLI."""
    if not shutil.which("aws"):
        print("❌ Ошибка: AWS CLI не установлен")
        print("Установите AWS CLI:")
        print("  pip install awscli")
        print("  или следуйте инструкциям: https://aws.amazon.com/cli/")
        return False
    return True

def check_dvc_installed() -> bool:
    """Проверка установки DVC."""
    if not shutil.which("dvc"):
        print("❌ Ошибка: DVC не установлен")
        print("Установите DVC: pip install dvc dvc-s3")
        return False
    return True

def check_boto3_installed() -> bool:
    """Проверка установки boto3."""
    try:
        import boto3
        return True
    except ImportError:
        return False

def save_aws_credentials(access_key_id: str, secret_access_key: str, region: Optional[str] = None) -> bool:
    """Сохранение AWS credentials в ~/.aws/credentials."""
    aws_dir = Path.home() / ".aws"
    aws_dir.mkdir(exist_ok=True)
    
    credentials_file = aws_dir / "credentials"
    config_file = aws_dir / "config"
    
    # Сохраняем credentials
    config = configparser.ConfigParser()
    if credentials_file.exists():
        config.read(credentials_file)
    
    if "default" not in config:
        config.add_section("default")
    
    config.set("default", "aws_access_key_id", access_key_id)
    config.set("default", "aws_secret_access_key", secret_access_key)
    
    try:
        with open(credentials_file, 'w') as f:
            config.write(f)
        print(f"✅ Credentials сохранены в {credentials_file}")
    except Exception as e:
        print(f"❌ Ошибка при сохранении credentials: {e}")
        return False
    
    # Сохраняем регион в config
    if region:
        config_region = configparser.ConfigParser()
        if config_file.exists():
            config_region.read(config_file)
        
        if "default" not in config_region:
            config_region.add_section("default")
        
        config_region.set("default", "region", region)
        
        try:
            with open(config_file, 'w') as f:
                config_region.write(f)
        except Exception as e:
            print(f"⚠️  Предупреждение: не удалось сохранить регион: {e}")
    
    return True

def create_iam_user_and_key(user_name: str, bucket_name: str, region: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """Создание IAM пользователя и access key через AWS CLI."""
    print(f"\nСоздание IAM пользователя '{user_name}'...")
    
    # Создаем IAM пользователя
    result = subprocess.run(
        ["aws", "iam", "create-user", "--user-name", user_name],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        if "EntityAlreadyExists" in result.stderr:
            print(f"✅ IAM пользователь '{user_name}' уже существует")
        else:
            print(f"❌ Ошибка при создании IAM пользователя: {result.stderr}")
            return None
    else:
        print(f"✅ IAM пользователь '{user_name}' создан")
    
    # Создаем политику для доступа к S3 bucket
    policy_name = f"{user_name}-s3-policy"
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            }
        ]
    }
    
    policy_file = Path("/tmp") / f"{policy_name}.json"
    try:
        with open(policy_file, 'w') as f:
            json.dump(policy_doc, f)
        
        # Создаем политику
        result = subprocess.run(
            ["aws", "iam", "create-policy", 
             "--policy-name", policy_name,
             "--policy-document", f"file://{policy_file}"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            if "EntityAlreadyExists" in result.stderr:
                print(f"✅ Политика '{policy_name}' уже существует")
                # Получаем ARN существующей политики
                account_id_result = subprocess.run(
                    ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
                    capture_output=True,
                    text=True
                )
                if account_id_result.returncode == 0:
                    account_id = account_id_result.stdout.strip()
                    policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
                else:
                    # Пробуем получить через list-policies
                    list_result = subprocess.run(
                        ["aws", "iam", "list-policies", "--scope", "Local", "--query", 
                         f"Policies[?PolicyName=='{policy_name}'].Arn", "--output", "text"],
                        capture_output=True,
                        text=True
                    )
                    policy_arn = list_result.stdout.strip() if list_result.returncode == 0 else None
            else:
                print(f"⚠️  Предупреждение: не удалось создать политику: {result.stderr}")
                policy_arn = None
        else:
            policy_arn = json.loads(result.stdout)["Policy"]["Arn"]
            print(f"✅ Политика '{policy_name}' создана")
        
        # Прикрепляем политику к пользователю
        if policy_arn:
            # Если policy_arn не полный, получаем account_id и формируем полный ARN
            if not policy_arn.startswith("arn:aws:iam::"):
                account_id_result = subprocess.run(
                    ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
                    capture_output=True,
                    text=True
                )
                if account_id_result.returncode == 0:
                    account_id = account_id_result.stdout.strip()
                    policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            
            attach_result = subprocess.run(
                ["aws", "iam", "attach-user-policy", 
                 "--user-name", user_name,
                 "--policy-arn", policy_arn],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if attach_result.returncode == 0:
                print(f"✅ Политика прикреплена к пользователю")
            else:
                if "Duplicate" in attach_result.stderr or "already attached" in attach_result.stderr.lower():
                    print(f"✅ Политика уже прикреплена к пользователю")
                else:
                    print(f"⚠️  Предупреждение: не удалось прикрепить политику: {attach_result.stderr}")
    finally:
        if policy_file.exists():
            policy_file.unlink()
    
    # Создаем access key
    print(f"Создание access key для пользователя '{user_name}'...")
    result = subprocess.run(
        ["aws", "iam", "create-access-key", "--user-name", user_name],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        key_data = json.loads(result.stdout)["AccessKey"]
        access_key_id = key_data["AccessKeyId"]
        secret_access_key = key_data["SecretAccessKey"]
        print(f"✅ Access key создан")
        return access_key_id, secret_access_key
    else:
        print(f"❌ Ошибка при создании access key: {result.stderr}")
        return None

def check_aws_credentials() -> Tuple[bool, Optional[str]]:
    """Проверка настройки AWS credentials с возможностью автоматического создания."""
    # Проверяем, не являются ли credentials тестовыми
    credentials_file = Path.home() / ".aws" / "credentials"
    if credentials_file.exists():
        try:
            config = configparser.ConfigParser()
            config.read(credentials_file)
            if "default" in config:
                access_key = config.get("default", "aws_access_key_id", fallback="")
                if access_key in ["123", "test", "TEST", ""]:
                    print("⚠️  Обнаружены тестовые или пустые credentials")
                    print("Пожалуйста, используйте реальные AWS credentials")
        except Exception:
            pass
    
    try:
        print("Проверка AWS credentials...")
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            text=True,
            timeout=20
        )
        
        if result.returncode == 0:
            # Пытаемся извлечь регион из конфигурации
            region_result = subprocess.run(
                ["aws", "configure", "get", "region"],
                capture_output=True,
                text=True
            )
            region = region_result.stdout.strip() if region_result.returncode == 0 else None
            return True, region
        else:
            # Анализируем ошибку
            error_msg = result.stderr.lower()
            if "invalidclienttokenid" in error_msg or "invalid" in error_msg:
                print("❌ Ошибка: Неверные AWS credentials")
                print("Проверьте Access Key ID и Secret Access Key")
            elif "could not resolve" in error_msg or "network" in error_msg:
                print("❌ Ошибка: Проблемы с сетью/подключением к AWS")
                print("Проверьте интернет-соединение и доступность AWS")
            elif "expired" in error_msg:
                print("❌ Ошибка: AWS credentials истекли")
                print("Обновите credentials через 'aws configure'")
            else:
                print(f"❌ Ошибка при проверке credentials: {result.stderr}")
            # Credentials не настроены или неверные, предлагаем создать автоматически
            print("\n⚠️  AWS credentials не настроены или неверны")
            print("\nВарианты настройки:")
            print("  1. Автоматическое создание IAM пользователя и access key")
            print("     ⚠️  Требуются валидные AWS credentials администратора (сначала настройте через 'aws configure')")
            print("  2. Ввод существующих credentials вручную (рекомендуется для начала)")
            print("  3. Использование переменных окружения")
            print("\n💡 Совет: Если у вас еще нет AWS credentials, используйте вариант 2")
            print("   Получите Access Key ID и Secret Access Key из AWS Console:")
            print("   https://console.aws.amazon.com/iam/home#/security_credentials")
            print("\n💡 Если вы уже настроили credentials через 'aws configure', но получаете ошибку:")
            print("   - Проверьте их: aws sts get-caller-identity")
            print("   - Убедитесь, что Access Key ID и Secret Access Key корректны")
            
            choice = input("\nВыберите вариант (1/2/3) или 'q' для выхода: ").strip()
            
            if choice == '1':
                # Автоматическое создание - сначала проверяем, есть ли валидные credentials для создания IAM
                print("\n⚠️  Для автоматического создания IAM пользователя нужны валидные AWS credentials с правами администратора.")
                print("Если у вас нет настроенных credentials, сначала настройте их через 'aws configure'")
                
                # Проверяем, можем ли мы выполнить базовую операцию AWS
                test_result = subprocess.run(
                    ["aws", "sts", "get-caller-identity"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if test_result.returncode != 0:
                    print("\n❌ Не удалось проверить AWS credentials")
                    print("Для автоматического создания IAM пользователя сначала настройте базовые credentials:")
                    print("  1. aws configure")
                    print("  2. Или установите переменные окружения: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
                    print("\nПосле настройки запустите скрипт снова и выберите вариант 1")
                    print("\nИли используйте вариант 2 для ввода credentials вручную")
                    return False, None
                
                # Проверяем права на создание IAM пользователя
                print("Проверка прав доступа...")
                iam_test = subprocess.run(
                    ["aws", "iam", "list-users", "--max-items", "1"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if iam_test.returncode != 0:
                    print("❌ Недостаточно прав для работы с IAM")
                    print("Убедитесь, что ваши credentials имеют права на создание IAM пользователей")
                    print("Или используйте вариант 2 для ввода credentials вручную")
                    return False, None
                
                print("✅ Права доступа подтверждены")
                
                username = os.getenv("USER", os.getenv("USERNAME", "dvc-user"))
                user_name = input(f"\nВведите имя IAM пользователя (по умолчанию: {username}-dvc): ").strip() or f"{username}-dvc"
                
                # Нужно будет создать bucket позже, поэтому пока используем временное имя
                temp_bucket = input("Введите имя S3 bucket для создания политики (можно изменить позже): ").strip()
                if not temp_bucket:
                    temp_bucket = f"dvc-storage-{username.lower()}"
                
                region_input = input("Введите AWS регион (по умолчанию: us-east-1): ").strip() or "us-east-1"
                
                credentials = create_iam_user_and_key(user_name, temp_bucket, region_input)
                if credentials:
                    access_key_id, secret_access_key = credentials
                    if save_aws_credentials(access_key_id, secret_access_key, region_input):
                        print("\n✅ Credentials успешно созданы и сохранены!")
                        # Проверяем снова
                        return check_aws_credentials()
                    else:
                        return False, None
                else:
                    print("\n❌ Не удалось создать credentials автоматически")
                    print("Возможные причины:")
                    print("  - Недостаточно прав для создания IAM пользователей")
                    print("  - IAM пользователь с таким именем уже существует")
                    print("\nПопробуйте:")
                    print("  - Вариант 2: Ввести существующие credentials вручную")
                    print("  - Или настройте AWS credentials с правами администратора и попробуйте снова")
                    return False, None
            
            elif choice == '2':
                # Ввод вручную
                print("\n" + "=" * 60)
                print("Ввод AWS credentials вручную")
                print("=" * 60)
                print("\nПолучите credentials из AWS Console:")
                print("  https://console.aws.amazon.com/iam/home#/security_credentials")
                print("\nИли создайте нового пользователя:")
                print("  https://console.aws.amazon.com/iam/home#/users$new")
                print("\nВведите AWS credentials:")
                access_key_id = input("\nAWS Access Key ID: ").strip()
                secret_access_key = input("AWS Secret Access Key: ").strip()
                region_input = input("AWS Region (по умолчанию: us-east-1): ").strip() or "us-east-1"
                
                if access_key_id and secret_access_key:
                    print("\nСохранение credentials...")
                    if save_aws_credentials(access_key_id, secret_access_key, region_input):
                        print("Проверка credentials...")
                        # Проверяем снова
                        verify_result = subprocess.run(
                            ["aws", "sts", "get-caller-identity"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if verify_result.returncode == 0:
                            print("✅ Credentials успешно сохранены и проверены!")
                            return check_aws_credentials()
                        else:
                            print("⚠️  Credentials сохранены, но проверка не прошла")
                            print("Убедитесь, что Access Key ID и Secret Access Key корректны")
                            return False, None
                    else:
                        return False, None
                else:
                    print("❌ Access Key ID и Secret Access Key обязательны")
                    return False, None
            
            elif choice == '3':
                # Переменные окружения
                print("\nУстановите переменные окружения:")
                print("  export AWS_ACCESS_KEY_ID='your-access-key-id'")
                print("  export AWS_SECRET_ACCESS_KEY='your-secret-access-key'")
                print("  export AWS_DEFAULT_REGION='us-east-1'")
                print("\nЗатем запустите скрипт снова")
                return False, None
            
            else:
                print("Отменено")
                return False, None
            
    except subprocess.TimeoutExpired:
        print("\n❌ Ошибка: Таймаут при проверке AWS credentials")
        print("\nВозможные причины:")
        print("  - Неверные или тестовые credentials (например, '123')")
        print("  - Проблемы с интернет-соединением")
        print("  - AWS сервисы недоступны")
        print("  - Блокировка файрволом или прокси")
        print("\nПопробуйте:")
        print("  1. Проверить credentials вручную:")
        print("     aws sts get-caller-identity")
        print("  2. Если получаете ошибку 'InvalidClientTokenId' - credentials неверны")
        print("  3. Получите правильные credentials из AWS Console:")
        print("     https://console.aws.amazon.com/iam/home#/security_credentials")
        print("  4. Настройте заново: aws configure")
        print("  5. Или используйте вариант 2 в скрипте для ввода credentials вручную")
        return False, None
    except Exception as e:
        print(f"❌ Ошибка при проверке AWS credentials: {e}")
        print("\nПопробуйте проверить credentials вручную:")
        print("  aws sts get-caller-identity")
        return False, None

def validate_bucket_name(bucket_name: str) -> bool:
    """Валидация имени S3 bucket."""
    # Правила именования S3 bucket:
    # - 3-63 символа
    # - Только строчные буквы, цифры, точки и дефисы
    # - Не может начинаться/заканчиваться точкой
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        print("❌ Имя bucket должно быть от 3 до 63 символов")
        return False
    
    if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', bucket_name):
        print("❌ Имя bucket может содержать только строчные буквы, цифры, точки и дефисы")
        print("   И не может начинаться/заканчиваться точкой")
        return False
    
    return True

def bucket_exists(bucket_name: str) -> bool:
    """Проверка существования S3 bucket."""
    try:
        result = subprocess.run(
            ["aws", "s3", "ls", f"s3://{bucket_name}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False

def create_bucket(bucket_name: str, region: Optional[str] = None) -> bool:
    """Создание S3 bucket."""
    print(f"Создание S3 bucket: {bucket_name}...")
    
    try:
        if region and region != "us-east-1":
            # Для регионов кроме us-east-1 нужно указывать --region
            result = subprocess.run(
                ["aws", "s3", "mb", f"s3://{bucket_name}", "--region", region],
                capture_output=True,
                text=True,
                timeout=30
            )
        else:
            result = subprocess.run(
                ["aws", "s3", "mb", f"s3://{bucket_name}"],
                capture_output=True,
                text=True,
                timeout=30
            )
        
        if result.returncode == 0:
            print(f"✅ Bucket {bucket_name} создан успешно")
            return True
        else:
            if "BucketAlreadyExists" in result.stderr or "BucketAlreadyOwnedByYou" in result.stderr:
                print(f"✅ Bucket {bucket_name} уже существует")
                return True
            else:
                print(f"❌ Ошибка при создании bucket: {result.stderr}")
                return False
    except subprocess.TimeoutExpired:
        print("❌ Таймаут при создании bucket")
        return False
    except Exception as e:
        print(f"❌ Ошибка при создании bucket: {e}")
        return False

def setup_dvc_remote(bucket_name: str, remote_name: str = "s3remote", path: str = "dvc-storage") -> bool:
    """Настройка DVC remote для S3."""
    s3_url = f"s3://{bucket_name}/{path}"
    
    print(f"\nНастройка DVC remote '{remote_name}' -> {s3_url}...")
    
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
    
    # Настраиваем credentialpath (если используется стандартный путь)
    credentials_path = os.path.expanduser("~/.aws/credentials")
    if os.path.exists(credentials_path):
        subprocess.run(
            ["dvc", "remote", "modify", remote_name, "credentialpath", credentials_path],
            capture_output=True
        )
        print("✅ Настроен путь к AWS credentials")
    
    return True

def test_connection(bucket_name: str, path: str = "dvc-storage") -> bool:
    """Тестирование подключения к S3."""
    print(f"\nТестирование подключения к S3...")
    
    try:
        # Пытаемся создать тестовый файл
        test_key = f"{path}/.dvc-test"
        result = subprocess.run(
            ["aws", "s3", "cp", "/dev/null", f"s3://{bucket_name}/{test_key}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Удаляем тестовый файл
            subprocess.run(
                ["aws", "s3", "rm", f"s3://{bucket_name}/{test_key}"],
                capture_output=True
            )
            print("✅ Подключение к S3 работает корректно")
            return True
        else:
            print(f"⚠️  Предупреждение: не удалось протестировать подключение: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  Предупреждение: ошибка при тестировании подключения: {e}")
        return False

def main():
    """Главная функция."""
    print("=" * 60)
    print("Автоматическая настройка AWS S3 для DVC")
    print("=" * 60)
    
    # Проверки
    if not check_aws_cli_installed():
        sys.exit(1)
    
    if not check_dvc_installed():
        sys.exit(1)
    
    # Проверка DVC инициализации
    dvc_dir = Path(".dvc")
    if not dvc_dir.exists() or not (dvc_dir / "config").exists():
        print("❌ DVC не инициализирован")
        print("Сначала выполните: python3 scripts/init_dvc.py")
        sys.exit(1)
    
    # Проверка AWS credentials
    credentials_ok, region = check_aws_credentials()
    if not credentials_ok:
        sys.exit(1)
    
    print(f"✅ AWS credentials настроены")
    if region:
        print(f"✅ Регион: {region}")
    else:
        print("⚠️  Регион не указан, будет использован по умолчанию (us-east-1)")
    
    # Запрос параметров
    print("\n" + "-" * 60)
    bucket_name = input("Введите имя S3 bucket (или нажмите Enter для 'dvc-storage-<username>'): ").strip()
    
    if not bucket_name:
        # Генерируем имя bucket на основе username
        username = os.getenv("USER", os.getenv("USERNAME", "user"))
        bucket_name = f"dvc-storage-{username.lower()}"
        print(f"Используется имя bucket: {bucket_name}")
    
    if not validate_bucket_name(bucket_name):
        sys.exit(1)
    
    remote_name = input("Введите имя для DVC remote (по умолчанию: s3remote): ").strip() or "s3remote"
    path = input("Введите путь в bucket для DVC (по умолчанию: dvc-storage): ").strip() or "dvc-storage"
    
    # Создание bucket
    if not bucket_exists(bucket_name):
        if not create_bucket(bucket_name, region):
            sys.exit(1)
    else:
        print(f"✅ Bucket {bucket_name} уже существует")
    
    # Настройка DVC remote
    if not setup_dvc_remote(bucket_name, remote_name, path):
        sys.exit(1)
    
    # Тестирование подключения
    test_connection(bucket_name, path)
    
    # Итоговая информация
    print("\n" + "=" * 60)
    print("✅ Настройка AWS S3 завершена успешно!")
    print("=" * 60)
    print(f"\nНастройки:")
    print(f"  Bucket: s3://{bucket_name}")
    print(f"  Remote name: {remote_name}")
    print(f"  Path: {path}")
    print(f"\nСледующие шаги:")
    print(f"  1. Проверьте настройку: dvc remote list")
    print(f"  2. Загрузите данные: dvc push")
    print(f"  3. Закоммитьте изменения: git add .dvc/config")
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

