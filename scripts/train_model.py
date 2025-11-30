#!/usr/bin/env python3
"""
Скрипт для обучения модели на данных Boston Housing.
"""

import pandas as pd
import numpy as np
import json
import pickle
import sys
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import yaml

def load_config(config_path: str) -> dict:
    """Загрузка конфигурации модели."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_data(data_path: str) -> tuple:
    """Загрузка и подготовка данных."""
    print(f"Загрузка данных из {data_path}...")
    
    # Загрузка данных
    df = pd.read_csv(data_path, sep=r'\s+', header=None)
    
    # Названия колонок
    column_names = [
        'CRIM', 'ZN', 'INDUS', 'CHAS', 'NOX', 'RM', 'AGE', 
        'DIS', 'RAD', 'TAX', 'PTRATIO', 'B', 'LSTAT', 'MEDV'
    ]
    df.columns = column_names
    
    # Разделение на признаки и целевую переменную
    X = df.drop('MEDV', axis=1)
    y = df['MEDV']
    
    return X, y

def train_model(X_train, y_train, config: dict) -> RandomForestRegressor:
    """Обучение модели."""
    print("Обучение модели...")
    
    model_params = config['model']['params']
    model = RandomForestRegressor(**model_params)
    model.fit(X_train, y_train)
    
    print("Модель обучена успешно!")
    return model

def evaluate_model(model, X_test, y_test) -> dict:
    """Оценка модели."""
    y_pred = model.predict(X_test)
    
    metrics = {
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'r2': float(r2_score(y_test, y_pred))
    }
    
    return metrics

def main():
    # Пути
    data_path = "data/housing.csv"
    config_path = "config/model_config.yaml"
    model_output_path = "models/model.pkl"
    metrics_output_path = "models/metrics.json"
    report_output_path = "reports/training_report.json"
    
    # Создание директорий
    Path(model_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(metrics_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Загрузка конфигурации
    print("Загрузка конфигурации...")
    config = load_config(config_path)
    
    # Загрузка данных
    X, y = load_data(data_path)
    
    # Разделение на train/test
    test_size = config['data']['test_size']
    random_state = config['data']['random_state']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    print(f"Размер обучающей выборки: {X_train.shape[0]}")
    print(f"Размер тестовой выборки: {X_test.shape[0]}")
    
    # Обучение модели
    model = train_model(X_train, y_train, config)
    
    # Оценка на тестовой выборке
    print("Оценка модели на тестовой выборке...")
    metrics = evaluate_model(model, X_test, y_test)
    
    print("\nМетрики модели:")
    for metric_name, metric_value in metrics.items():
        print(f"  {metric_name.upper()}: {metric_value:.4f}")
    
    # Проверка порогов качества
    thresholds = config.get('thresholds', {})
    min_r2 = thresholds.get('min_r2', 0.0)
    max_rmse = thresholds.get('max_rmse', float('inf'))
    
    quality_check = {
        'passed': metrics['r2'] >= min_r2 and metrics['rmse'] <= max_rmse,
        'r2_check': {
            'passed': metrics['r2'] >= min_r2,
            'value': metrics['r2'],
            'threshold': min_r2
        },
        'rmse_check': {
            'passed': metrics['rmse'] <= max_rmse,
            'value': metrics['rmse'],
            'threshold': max_rmse
        }
    }
    
    if not quality_check['passed']:
        print("\n⚠️  ВНИМАНИЕ: Модель не прошла проверку качества!")
        if not quality_check['r2_check']['passed']:
            print(f"  R² = {metrics['r2']:.4f} < {min_r2}")
        if not quality_check['rmse_check']['passed']:
            print(f"  RMSE = {metrics['rmse']:.4f} > {max_rmse}")
    else:
        print("\n✅ Модель прошла проверку качества!")
    
    # Сохранение модели
    print(f"\nСохранение модели в {model_output_path}...")
    with open(model_output_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Сохранение метрик
    print(f"Сохранение метрик в {metrics_output_path}...")
    with open(metrics_output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    # Создание отчета
    report = {
        'model_name': config['model']['name'],
        'model_params': config['model']['params'],
        'metrics': metrics,
        'quality_check': quality_check,
        'data_info': {
            'train_size': int(X_train.shape[0]),
            'test_size': int(X_test.shape[0]),
            'features': list(X.columns)
        }
    }
    
    with open(report_output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Отчет сохранен в {report_output_path}")
    
    # Выход с кодом ошибки, если качество неудовлетворительное
    if not quality_check['passed']:
        sys.exit(1)
    
    print("\n✅ Обучение завершено успешно!")
    sys.exit(0)

if __name__ == "__main__":
    main()

