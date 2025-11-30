#!/usr/bin/env python3
"""
Скрипт для инициализации DVC в проекте.
"""

import subprocess
import sys
import shutil
from pathlib import Path

def check_dvc_installed():
    """Проверка установки DVC."""
    if not shutil.which("dvc"):
        print("❌ Ошибка: DVC не установлен")
        print("Установите DVC: pip install dvc")
        return False
    return True

def init_dvc():
    """Инициализация DVC."""
    if not check_dvc_installed():
        return False
    
    dvc_dir = Path(".dvc")
    
    # Проверка, не инициализирован ли уже DVC
    if dvc_dir.exists() and (dvc_dir / "config").exists():
        print("✅ DVC уже инициализирован")
    else:
        print("Инициализация DVC...")
        
        # Инициализация DVC
        result = subprocess.run(
            ["dvc", "init", "--no-scm"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Если ошибка из-за существующей директории, пробуем с флагом -f
            if ".dvc' exists" in result.stderr:
                print("⚠️  Директория .dvc существует, используем принудительную инициализацию...")
                result = subprocess.run(
                    ["dvc", "init", "--no-scm", "-f"],
                    capture_output=True,
                    text=True
                )
            
            if result.returncode != 0:
                print(f"Ошибка инициализации DVC: {result.stderr}")
                return False
        
        print("✅ DVC инициализирован")
    
    # Добавление данных в DVC
    data_file = Path("data/housing.csv")
    data_dvc_file = Path("data/housing.csv.dvc")
    
    if data_file.exists():
        if data_dvc_file.exists():
            print("\n✅ Данные уже добавлены в DVC")
        else:
            print("\nДобавление данных в DVC...")
            result = subprocess.run(
                ["dvc", "add", str(data_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Данные добавлены в DVC")
            else:
                # Если файл уже отслеживается, это не критично
                if "already tracked" in result.stderr.lower() or "already in cache" in result.stderr.lower():
                    print("✅ Данные уже отслеживаются DVC")
                else:
                    print(f"⚠️  Предупреждение: {result.stderr}")
    
    print("\n✅ Инициализация DVC завершена!")
    print("\nСледующие шаги:")
    print("1. Настройте удаленное хранилище: dvc remote add -d <name> <url>")
    print("2. Закоммитьте .dvc файлы: git add data/housing.csv.dvc .dvc/")
    print("3. Загрузите данные: dvc push")
    
    return True

if __name__ == "__main__":
    try:
        success = init_dvc()
        sys.exit(0 if success else 1)
    except FileNotFoundError as e:
        if "dvc" in str(e):
            print("❌ Ошибка: DVC не установлен")
            print("Установите DVC: pip install dvc")
        else:
            print(f"❌ Ошибка: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)

