"""
Тесты для валидации данных.
"""

import pytest
import json
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.validate_data import validate_data

def test_data_validation_success(tmp_path):
    """Тест успешной валидации данных."""
    data_path = "data/housing.csv"
    output_path = str(tmp_path / "validation_report.json")
    
    result = validate_data(data_path, output_path)
    
    assert result["status"] in ["success", "warning"]
    assert "checks" in result
    assert "summary" in result
    
    # Проверяем, что отчет создан
    assert Path(output_path).exists()
    
    # Загружаем и проверяем отчет
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert report["status"] in ["success", "warning"]

def test_data_validation_checks(tmp_path):
    """Тест конкретных проверок данных."""
    data_path = "data/housing.csv"
    output_path = str(tmp_path / "validation_report.json")
    
    result = validate_data(data_path, output_path)
    
    # Проверка размерности
    assert "shape" in result["checks"]
    assert result["checks"]["shape"]["columns"] == 14
    
    # Проверка пропусков
    assert "missing_values" in result["checks"]
    
    # Проверка типов данных
    assert "data_types" in result["checks"]

