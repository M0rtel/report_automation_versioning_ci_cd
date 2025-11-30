#!/usr/bin/env python3
"""
Скрипт для валидации данных Boston Housing.
Проверяет качество данных перед обучением модели.
"""

import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path

def convert_numpy_types(obj):
    """
    Рекурсивно конвертирует NumPy типы в нативные Python типы для JSON сериализации.
    """
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, pd.Series):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    else:
        return obj

def validate_data(data_path: str, output_path: str) -> dict:
    """
    Валидация данных Boston Housing.
    
    Args:
        data_path: Путь к файлу данных
        output_path: Путь для сохранения отчета валидации
        
    Returns:
        Словарь с результатами валидации
    """
    print(f"Загрузка данных из {data_path}...")
    
    # Загрузка данных
    try:
        # Boston Housing dataset имеет пробелы в качестве разделителей
        df = pd.read_csv(data_path, sep=r'\s+', header=None)
        
        # Названия колонок согласно документации
        column_names = [
            'CRIM', 'ZN', 'INDUS', 'CHAS', 'NOX', 'RM', 'AGE', 
            'DIS', 'RAD', 'TAX', 'PTRATIO', 'B', 'LSTAT', 'MEDV'
        ]
        df.columns = column_names
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка загрузки данных: {str(e)}"
        }
    
    validation_results = {
        "status": "success",
        "checks": {},
        "summary": {}
    }
    
    # Проверка 1: Размерность данных
    n_rows, n_cols = df.shape
    validation_results["checks"]["shape"] = {
        "passed": n_rows > 0 and n_cols == 14,
        "rows": int(n_rows),
        "columns": int(n_cols),
        "expected_columns": 14
    }
    
    # Проверка 2: Отсутствие пропусков
    missing_values = df.isnull().sum()
    has_missing = missing_values.sum() > 0
    validation_results["checks"]["missing_values"] = {
        "passed": not has_missing,
        "missing_counts": missing_values[missing_values > 0].to_dict(),
        "total_missing": int(missing_values.sum())
    }
    
    # Проверка 3: Типы данных
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    validation_results["checks"]["data_types"] = {
        "passed": len(numeric_cols) == len(df.columns),
        "numeric_columns": len(numeric_cols),
        "total_columns": len(df.columns)
    }
    
    # Проверка 4: Диапазоны значений для целевой переменной
    target_col = 'MEDV'
    if target_col in df.columns:
        medv_min = float(df[target_col].min())
        medv_max = float(df[target_col].max())
        medv_mean = float(df[target_col].mean())
        medv_std = float(df[target_col].std())
        
        validation_results["checks"]["target_range"] = {
            "passed": medv_min >= 0 and medv_max <= 50,
            "min": medv_min,
            "max": medv_max,
            "mean": medv_mean,
            "std": medv_std
        }
    
    # Проверка 5: Выбросы (outliers) - используем IQR метод
    outliers_count = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
        outliers_count[col] = int(outliers)
    
    validation_results["checks"]["outliers"] = {
        "passed": True,  # Выбросы допустимы, просто фиксируем
        "outliers_count": outliers_count,
        "total_outliers": sum(outliers_count.values())
    }
    
    # Проверка 6: Дубликаты
    duplicates = df.duplicated().sum()
    validation_results["checks"]["duplicates"] = {
        "passed": duplicates == 0,
        "duplicate_rows": int(duplicates)
    }
    
    # Проверка 7: Статистика по признакам
    validation_results["summary"]["statistics"] = {
        "mean": df.select_dtypes(include=[np.number]).mean().to_dict(),
        "std": df.select_dtypes(include=[np.number]).std().to_dict(),
        "min": df.select_dtypes(include=[np.number]).min().to_dict(),
        "max": df.select_dtypes(include=[np.number]).max().to_dict()
    }
    
    # Итоговый статус
    all_passed = all(
        check.get("passed", False) 
        for check in validation_results["checks"].values()
    )
    
    validation_results["status"] = "success" if all_passed else "warning"
    
    # Конвертируем NumPy типы в нативные Python типы для JSON сериализации
    validation_results = convert_numpy_types(validation_results)
    
    # Сохранение отчета
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)
    
    print(f"Валидация завершена. Статус: {validation_results['status']}")
    print(f"Отчет сохранен в {output_path}")
    
    return validation_results

if __name__ == "__main__":
    data_path = "data/housing.csv"
    output_path = "reports/data_validation_report.json"
    
    results = validate_data(data_path, output_path)
    
    if results["status"] == "error":
        print(f"ОШИБКА: {results.get('message', 'Неизвестная ошибка')}")
        sys.exit(1)
    
    # Проверяем критические проверки
    critical_checks = ["shape", "missing_values", "data_types"]
    failed_checks = [
        name for name in critical_checks 
        if not results["checks"].get(name, {}).get("passed", False)
    ]
    
    if failed_checks:
        print(f"КРИТИЧЕСКИЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ: {', '.join(failed_checks)}")
        sys.exit(1)
    
    print("Все критические проверки пройдены успешно!")
    sys.exit(0)

