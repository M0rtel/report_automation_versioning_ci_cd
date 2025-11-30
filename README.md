# ML Project with DVC and CI/CD

Проект машинного обучения с автоматическим версионированием данных и моделей через DVC и CI/CD пайплайн.

## О проекте

Проект демонстрирует полную настройку автоматического версионирования данных и моделей в CI/CD пайплайне с использованием:
- **DVC** (Data Version Control) для версионирования данных и моделей
- **GitHub Actions** для автоматизации CI/CD
- **Python** для ML pipeline

## Структура проекта

```
report_automation_versioning_ci_cd/
├── data/                          # Данные (версионируются через DVC)
│   ├── housing.csv               # Boston Housing dataset
│   ├── housing.csv.dvc           # DVC метаданные (создается после dvc add)
│   └── About_Dataset.md          # Описание датасета
├── models/                        # Обученные модели (версионируются через DVC)
│   ├── model.pkl                 # Обученная модель (создается при обучении)
│   ├── model.pkl.dvc             # DVC метаданные (создается после dvc add)
│   └── metrics.json              # Метрики модели
├── scripts/                       # Скрипты обработки
│   ├── validate_data.py          # Валидация данных
│   ├── train_model.py            # Обучение модели
│   ├── evaluate_model.py         # Оценка модели
│   └── init_dvc.py               # Инициализация DVC
├── config/                        # Конфигурация
│   └── model_config.yaml         # Параметры модели и пороги качества
├── reports/                       # Отчеты и результаты
│   ├── data_validation_report.json
│   ├── training_report.json
│   ├── evaluation_report.json
│   └── feature_importance.png
├── tests/                         # Тесты
│   ├── test_data_validation.py   # Тесты валидации данных
│   ├── test_model_reproducibility.py  # Тесты воспроизводимости
│   └── test_model_quality.py     # Тесты качества модели
├── .github/
│   └── workflows/
│       └── ci_cd.yml             # GitHub Actions CI/CD пайплайн
├── .dvc/                          # DVC конфигурация (создается при dvc init)
│   └── config                     # Конфигурация DVC
├── dvc.yaml                       # DVC pipeline определение
├── .dvcignore                    # Игнорируемые DVC файлы
├── .gitignore                    # Игнорируемые Git файлы
├── requirements.txt              # Python зависимости
├── pytest.ini                   # Конфигурация pytest
├── Makefile                      # Make команды для удобства
├── setup.sh                      # Скрипт первоначальной настройки
└── main.py                       # Главный скрипт проекта
```

## Установка

### Быстрая настройка

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd report_automation_versioning_ci_cd

# Автоматическая настройка
./setup.sh
```

### Ручная настройка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Инициализируйте DVC:
```bash
python scripts/init_dvc.py
# или вручную:
dvc init
dvc add data/housing.csv
```

## Использование

### Валидация данных

```bash
python scripts/validate_data.py
```

Проверяет качество данных перед обучением модели:
- Размерность данных (14 колонок)
- Отсутствие пропусков
- Типы данных (все числовые)
- Диапазоны значений целевой переменной
- Выбросы (IQR метод)
- Дубликаты

Создает отчет: `reports/data_validation_report.json`

### Обучение модели

```bash
python scripts/train_model.py
```

Обучает модель RandomForestRegressor на данных Boston Housing и сохраняет:
- Модель в `models/model.pkl`
- Метрики в `models/metrics.json`
- Отчет в `reports/training_report.json`

### Оценка модели

```bash
python scripts/evaluate_model.py
```

Выполняет детальную оценку модели и создает:
- Отчет оценки в `reports/evaluation_report.json`
- График важности признаков в `reports/feature_importance.png`

### Запуск DVC pipeline

```bash
dvc repro
```

Запускает весь pipeline согласно `dvc.yaml`:
1. Валидация данных
2. Обучение модели
3. Оценка модели

## CI/CD Pipeline

GitHub Actions автоматически выполняет следующие этапы при push в `main` или `develop`:

### Этапы пайплайна

1. **Validate Data**
   - Проверка качества данных
   - Создание отчета валидации
   - Блокировка при критических ошибках

2. **Train Model**
   - Обучение модели на данных
   - Проверка качества модели (R² >= 0.7, RMSE <= 5.0)
   - Сохранение артефактов модели

3. **Evaluate Model**
   - Детальная оценка модели
   - Создание визуализаций (важность признаков)

4. **Test Reproducibility**
   - Проверка воспроизводимости результатов
   - Обучение модели дважды и сравнение метрик
   - Гарантия идентичных результатов (благодаря фиксированному random_state)

5. **Performance Check**
   - Проверка производительности инференса
   - Измерение времени предсказаний
   - Проверка throughput (samples/second)

6. **Version and Commit** (только для `main` branch)
   - Автоматическое добавление данных и моделей в DVC
   - Создание версионных тегов (формат: `vYYYYMMDD-<commit-hash>`)
   - Коммит изменений

### Триггеры

- `push` в `main` или `develop`
- `pull_request` в `main` или `develop`
- `workflow_dispatch` (ручной запуск через GitHub UI)

### Локальный запуск проверок

Перед push рекомендуется проверить:

```bash
# Валидация данных
python scripts/validate_data.py

# Обучение и проверка качества
python scripts/train_model.py

# Оценка модели
python scripts/evaluate_model.py

# Тесты
pytest
```

## Версионирование с DVC

### Добавление данных в DVC

```bash
dvc add data/housing.csv
git add data/housing.csv.dvc data/.gitignore
git commit -m "Add data to DVC"
```

### Добавление модели в DVC

```bash
dvc add models/model.pkl
git add models/model.pkl.dvc
git commit -m "Add model version v1.0"
git tag v1.0
```

### Просмотр версий

```bash
dvc list data/
dvc list models/
```

### Восстановление конкретной версии

```bash
dvc checkout data/housing.csv.dvc@v1.0
dvc checkout models/model.pkl.dvc@v1.0
```

### Настройка удаленного хранилища DVC

Для продакшена рекомендуется использовать облачное хранилище:

**AWS S3:**
```bash
dvc remote add -d s3remote s3://my-bucket/dvc-storage
dvc remote modify s3remote credentialpath ~/.aws/credentials
dvc push
```

**Google Cloud Storage:**
```bash
dvc remote add -d gsremote gs://my-bucket/dvc-storage
dvc push
```

**Azure Blob Storage:**
```bash
dvc remote add -d azure remote://my-container/dvc-storage
dvc push
```

### Синхронизация

```bash
# Загрузить данные/модели
dvc pull

# Загрузить изменения
dvc push

# Просмотреть статус
dvc status
```

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Конкретный тест
pytest tests/test_data_validation.py -v
pytest tests/test_model_reproducibility.py -v
pytest tests/test_model_quality.py -v

# С покрытием
pytest --cov=scripts --cov-report=html
```

### Типы тестов

- **test_data_validation.py** - тесты валидации данных
- **test_model_reproducibility.py** - тесты воспроизводимости
- **test_model_quality.py** - тесты качества модели

## Конфигурация

### Параметры модели

Параметры модели настраиваются в `config/model_config.yaml`:

```yaml
model:
  name: "RandomForestRegressor"
  params:
    n_estimators: 100
    max_depth: 10
    random_state: 42
    min_samples_split: 2
    min_samples_leaf: 1

data:
  target_column: "MEDV"
  test_size: 0.2
  random_state: 42

metrics:
  primary: "rmse"
  secondary: ["mae", "r2"]

thresholds:
  min_r2: 0.7
  max_rmse: 5.0
```

### DVC Pipeline

Определен в `dvc.yaml`:

```yaml
stages:
  validate_data:
    cmd: python scripts/validate_data.py
    deps: [data/housing.csv, scripts/validate_data.py]
    outs: [reports/data_validation_report.json]

  train_model:
    cmd: python scripts/train_model.py
    deps: [data/housing.csv, scripts/train_model.py, config/model_config.yaml]
    params: [config/model_config.yaml]
    outs: [models/model.pkl, models/metrics.json, reports/training_report.json]

  evaluate_model:
    cmd: python scripts/evaluate_model.py
    deps: [models/model.pkl, data/housing.csv, scripts/evaluate_model.py]
    outs: [reports/evaluation_report.json, reports/feature_importance.png]
```

## Проверки качества

### Валидация данных
- ✅ Размерность: 14 колонок
- ✅ Пропуски: отсутствуют
- ✅ Типы: все числовые
- ✅ Целевая переменная: MEDV в диапазоне 0-50
- ✅ Выбросы: фиксируются (IQR метод)
- ✅ Дубликаты: проверяются

### Качество модели
- ✅ R² >= 0.7
- ✅ RMSE <= 5.0
- ✅ MAE вычисляется для информации
- ✅ Пороги настраиваются в `config/model_config.yaml`

### Воспроизводимость
- ✅ Фиксированный random_state (42)
- ✅ Идентичные метрики при повторном обучении
- ✅ Автоматический тест в CI/CD

### Производительность
- ✅ Inference time < 1.0 секунды
- ✅ Throughput измеряется
- ✅ Предупреждения при проблемах

## Workflow разработки

### Работа с данными

```bash
# Добавить новые данные
dvc add data/new_data.csv
git add data/new_data.csv.dvc
git commit -m "Add new data version"

# Просмотреть версии
dvc list data/

# Восстановить конкретную версию
dvc checkout data/housing.csv.dvc@v1.0
```

### Обучение модели

```bash
# Обучение через скрипт
python scripts/train_model.py

# Или через DVC pipeline
dvc repro train_model
```

### Pull Request процесс

1. Создайте ветку от `develop`
2. Внесите изменения
3. Убедитесь, что все тесты проходят
4. Создайте PR с описанием изменений
5. Дождитесь прохождения CI/CD проверок
6. После ревью - мердж в `develop`

### Структура коммитов

Используйте конвенциональные коммиты:

- `feat:` - новая функциональность
- `fix:` - исправление бага
- `docs:` - изменения в документации
- `refactor:` - рефакторинг
- `test:` - добавление тестов
- `chore:` - обновление версий, конфигурации

Примеры:
```
feat: add data validation script
fix: correct model metrics calculation
chore: update data and model versions [skip ci]
```

## Автоматическое версионирование

При push в `main` branch CI/CD пайплайн автоматически:
1. Валидирует данные
2. Обучает модель
3. Проверяет качество
4. Добавляет данные и модель в DVC
5. Создает версионный тег (формат: `vYYYYMMDD-<commit-hash>`)
6. Коммитит изменения

## Отладка

### Проблемы с DVC

```bash
# Очистить кеш
dvc cache dir
dvc cache clean

# Переинициализация
rm -rf .dvc
dvc init
```

### Проблемы с моделью

```bash
# Проверить метрики
cat models/metrics.json

# Проверить конфигурацию
cat config/model_config.yaml

# Запустить с отладкой
python -u scripts/train_model.py
```

## Дальнейшее развитие

1. **Облачное хранилище**: Настройка S3/GCS/Azure для DVC
2. **MLflow**: Интеграция для трекинга экспериментов
3. **Мониторинг**: Добавление мониторинга дрифта данных
4. **A/B тестирование**: Сравнение версий моделей
5. **Автоматический деплой**: Деплой лучших моделей

## Лицензия

MIT

## Авторы

Проект создан для демонстрации автоматизации ML workflow с DVC и CI/CD.
