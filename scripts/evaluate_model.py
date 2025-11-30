#!/usr/bin/env python3
"""
Скрипт для детальной оценки обученной модели.
"""

import pandas as pd
import numpy as np
import json
import pickle
import sys
from pathlib import Path
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI
import matplotlib.pyplot as plt
import seaborn as sns

def load_model(model_path: str):
    """Загрузка обученной модели."""
    print(f"Загрузка модели из {model_path}...")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_data(data_path: str) -> tuple:
    """Загрузка данных."""
    print(f"Загрузка данных из {data_path}...")
    
    df = pd.read_csv(data_path, sep=r'\s+', header=None)
    column_names = [
        'CRIM', 'ZN', 'INDUS', 'CHAS', 'NOX', 'RM', 'AGE', 
        'DIS', 'RAD', 'TAX', 'PTRATIO', 'B', 'LSTAT', 'MEDV'
    ]
    df.columns = column_names
    
    X = df.drop('MEDV', axis=1)
    y = df['MEDV']
    
    return X, y

def evaluate_model(model, X, y) -> dict:
    """Детальная оценка модели."""
    print("Выполнение предсказаний...")
    y_pred = model.predict(X)
    
    # Базовые метрики
    metrics = {
        'rmse': float(np.sqrt(mean_squared_error(y, y_pred))),
        'mae': float(mean_absolute_error(y, y_pred)),
        'r2': float(r2_score(y, y_pred)),
        'mean_absolute_percentage_error': float(np.mean(np.abs((y - y_pred) / y)) * 100)
    }
    
    # Дополнительная статистика
    residuals = y - y_pred
    metrics['residuals'] = {
        'mean': float(np.mean(residuals)),
        'std': float(np.std(residuals)),
        'min': float(np.min(residuals)),
        'max': float(np.max(residuals))
    }
    
    # Важность признаков (если модель поддерживает)
    if hasattr(model, 'feature_importances_'):
        feature_importance = {
            feature: float(importance) 
            for feature, importance in zip(X.columns, model.feature_importances_)
        }
        metrics['feature_importance'] = feature_importance
    
    return metrics, y_pred, residuals

def plot_feature_importance(model, feature_names, output_path: str):
    """Визуализация важности признаков."""
    if not hasattr(model, 'feature_importances_'):
        print("Модель не поддерживает feature_importances_")
        return
    
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    plt.figure(figsize=(10, 6))
    plt.title("Важность признаков")
    plt.bar(range(len(importances)), importances[indices])
    plt.xticks(range(len(importances)), [feature_names[i] for i in indices], rotation=45, ha='right')
    plt.ylabel("Важность")
    plt.tight_layout()
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"График важности признаков сохранен в {output_path}")

def main():
    model_path = "models/model.pkl"
    data_path = "data/housing.csv"
    report_output_path = "reports/evaluation_report.json"
    feature_importance_path = "reports/feature_importance.png"
    
    # Загрузка модели и данных
    model = load_model(model_path)
    X, y = load_data(data_path)
    
    # Оценка модели
    metrics, y_pred, residuals = evaluate_model(model, X, y)
    
    print("\nМетрики модели на полном датасете:")
    for metric_name, metric_value in metrics.items():
        if isinstance(metric_value, dict):
            print(f"\n{metric_name}:")
            for key, value in metric_value.items():
                print(f"  {key}: {value:.4f}")
        else:
            print(f"  {metric_name.upper()}: {metric_value:.4f}")
    
    # Визуализация важности признаков
    plot_feature_importance(model, X.columns, feature_importance_path)
    
    # Создание отчета
    report = {
        'metrics': metrics,
        'model_info': {
            'type': type(model).__name__,
            'n_features': X.shape[1],
            'n_samples': X.shape[0]
        }
    }
    
    Path(report_output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nОтчет сохранен в {report_output_path}")
    print("✅ Оценка модели завершена!")

if __name__ == "__main__":
    main()

