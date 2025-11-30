#!/usr/bin/env python3
"""
Скрипт для инициализации DVC в проекте.
"""

import subprocess
import sys
from pathlib import Path

def init_dvc():
    """Инициализация DVC."""
    print("Инициализация DVC...")
    
    # Инициализация DVC
    result = subprocess.run(
        ["dvc", "init", "--no-scm"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Ошибка инициализации DVC: {result.stderr}")
        return False
    
    print("✅ DVC инициализирован")
    
    # Добавление данных в DVC
    data_file = Path("data/housing.csv")
    if data_file.exists():
        print("\nДобавление данных в DVC...")
        result = subprocess.run(
            ["dvc", "add", str(data_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Данные добавлены в DVC")
        else:
            print(f"⚠️  Предупреждение: {result.stderr}")
    
    print("\n✅ Инициализация DVC завершена!")
    print("\nСледующие шаги:")
    print("1. Настройте удаленное хранилище: dvc remote add -d <name> <url>")
    print("2. Закоммитьте .dvc файлы: git add data/housing.csv.dvc .dvc/")
    print("3. Загрузите данные: dvc push")
    
    return True

if __name__ == "__main__":
    success = init_dvc()
    sys.exit(0 if success else 1)

