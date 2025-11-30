#!/usr/bin/env python3
"""
Главный скрипт проекта ML с DVC и CI/CD.
Демонстрирует полный workflow: валидация данных -> обучение -> оценка.
"""

import sys
from pathlib import Path

def main():
    """Главная функция для запуска полного pipeline."""
    print("=" * 60)
    print("ML Project Pipeline: Data Validation -> Training -> Evaluation")
    print("=" * 60)
    
    # Проверяем наличие необходимых скриптов
    scripts_dir = Path("scripts")
    required_scripts = [
        "validate_data.py",
        "train_model.py",
        "evaluate_model.py"
    ]
    
    for script in required_scripts:
        script_path = scripts_dir / script
        if not script_path.exists():
            print(f"❌ Ошибка: скрипт {script_path} не найден")
            sys.exit(1)
    
    print("\n✅ Все необходимые скрипты найдены")
    
    print("\n" + "=" * 60)
    print("Для запуска полного pipeline используйте:")
    print("  dvc repro")
    print("\nИли запустите этапы по отдельности:")
    print("  1. python scripts/validate_data.py")
    print("  2. python scripts/train_model.py")
    print("  3. python scripts/evaluate_model.py")
    print("=" * 60)

if __name__ == '__main__':
    main()
