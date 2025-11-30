#!/bin/bash
# Скрипт для первоначальной настройки проекта

set -e

echo "=========================================="
echo "Настройка ML проекта с DVC и CI/CD"
echo "=========================================="

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
    echo "✅ Виртуальное окружение создано"
else
    echo "✅ Виртуальное окружение уже существует"
fi

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Зависимости установлены"

# Инициализация DVC
if [ ! -d ".dvc" ]; then
    echo "Инициализация DVC..."
    dvc init --no-scm
    echo "✅ DVC инициализирован"
else
    echo "✅ DVC уже инициализирован"
fi

# Создание необходимых директорий
echo "Создание директорий..."
mkdir -p models reports scripts config tests
echo "✅ Директории созданы"

# Проверка наличия данных
if [ -f "data/housing.csv" ]; then
    echo "✅ Данные найдены"
    
    # Добавление данных в DVC (если еще не добавлены)
    if [ ! -f "data/housing.csv.dvc" ]; then
        echo "Добавление данных в DVC..."
        dvc add data/housing.csv
        echo "✅ Данные добавлены в DVC"
    else
        echo "✅ Данные уже в DVC"
    fi
else
    echo "⚠️  Данные не найдены в data/housing.csv"
fi

echo ""
echo "=========================================="
echo "✅ Настройка завершена!"
echo "=========================================="
echo ""
echo "Следующие шаги:"
echo "1. Активируйте виртуальное окружение: source venv/bin/activate"
echo "2. Запустите валидацию данных: python scripts/validate_data.py"
echo "3. Обучите модель: python scripts/train_model.py"
echo "4. Или используйте DVC pipeline: dvc repro"
echo ""

