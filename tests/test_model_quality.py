"""
Тесты качества модели.
"""

import pytest
import json
import yaml
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_model_quality_thresholds():
    """Тест соответствия модели порогам качества."""
    metrics_path = Path(__file__).parent.parent / "models" / "metrics.json"
    config_path = Path(__file__).parent.parent / "config" / "model_config.yaml"
    
    # Если модель еще не обучена, пропускаем тест
    if not metrics_path.exists():
        pytest.skip("Model not trained yet")
    
    # Загружаем метрики
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    # Загружаем конфигурацию
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    thresholds = config.get('thresholds', {})
    min_r2 = thresholds.get('min_r2', 0.0)
    max_rmse = thresholds.get('max_rmse', float('inf'))
    
    # Проверяем пороги
    assert metrics['r2'] >= min_r2, \
        f"R² ({metrics['r2']:.4f}) below threshold ({min_r2})"
    assert metrics['rmse'] <= max_rmse, \
        f"RMSE ({metrics['rmse']:.4f}) above threshold ({max_rmse})"

def test_model_metrics_exist():
    """Тест наличия всех необходимых метрик."""
    metrics_path = Path(__file__).parent.parent / "models" / "metrics.json"
    
    if not metrics_path.exists():
        pytest.skip("Model not trained yet")
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    required_metrics = ['rmse', 'mae', 'r2']
    for metric in required_metrics:
        assert metric in metrics, f"Missing metric: {metric}"
        assert isinstance(metrics[metric], (int, float)), \
            f"Metric {metric} is not a number"

