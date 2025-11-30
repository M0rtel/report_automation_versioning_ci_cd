"""
Тесты на воспроизводимость модели.
"""

import pytest
import json
import sys
from pathlib import Path
import tempfile
import shutil

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_model_reproducibility():
    """Тест воспроизводимости обучения модели."""
    import subprocess
    
    # Создаем временные директории для двух запусков
    with tempfile.TemporaryDirectory() as tmpdir1, \
         tempfile.TemporaryDirectory() as tmpdir2:
        
        # Первый запуск
        result1 = subprocess.run(
            ["python", "scripts/train_model.py"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result1.returncode == 0, f"Training failed: {result1.stderr}"
        
        # Копируем метрики
        metrics_path1 = Path(__file__).parent.parent / "models" / "metrics.json"
        assert metrics_path1.exists()
        
        with open(metrics_path1, 'r') as f:
            metrics1 = json.load(f)
        
        # Второй запуск
        result2 = subprocess.run(
            ["python", "scripts/train_model.py"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result2.returncode == 0, f"Training failed: {result2.stderr}"
        
        # Загружаем метрики второго запуска
        metrics_path2 = Path(__file__).parent.parent / "models" / "metrics.json"
        with open(metrics_path2, 'r') as f:
            metrics2 = json.load(f)
        
        # Проверяем, что метрики идентичны (благодаря фиксированному random_state)
        assert abs(metrics1['r2'] - metrics2['r2']) < 0.0001, \
            f"R² differs: {metrics1['r2']} vs {metrics2['r2']}"
        assert abs(metrics1['rmse'] - metrics2['rmse']) < 0.0001, \
            f"RMSE differs: {metrics1['rmse']} vs {metrics2['rmse']}"
        assert abs(metrics1['mae'] - metrics2['mae']) < 0.0001, \
            f"MAE differs: {metrics1['mae']} vs {metrics2['mae']}"

