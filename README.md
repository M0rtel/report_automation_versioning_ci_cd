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
│   ├── housing.csv.dvc           # DVC метаданные (в Git)
│   └── About_Dataset.md          # Описание датасета
├── models/                        # Обученные модели (генерируются при обучении)
│   └── (model.pkl, metrics.json - игнорируются Git, версионируются через DVC)
├── scripts/                       # Скрипты обработки
│   ├── validate_data.py          # Валидация данных
│   ├── train_model.py            # Обучение модели
│   ├── evaluate_model.py         # Оценка модели
│   └── init_dvc.py               # Инициализация DVC
├── config/                        # Конфигурация
│   └── model_config.yaml         # Параметры модели и пороги качества
├── reports/                       # Отчеты и результаты (генерируются)
│   └── (все .json и .png файлы игнорируются Git)
├── tests/                         # Тесты
│   ├── test_data_validation.py   # Тесты валидации данных
│   ├── test_model_reproducibility.py  # Тесты воспроизводимости
│   └── test_model_quality.py     # Тесты качества модели
├── .github/
│   └── workflows/
│       └── ci_cd.yml             # GitHub Actions CI/CD пайплайн
├── .dvc/                          # DVC конфигурация
│   └── config                    # Конфигурация DVC (в Git)
├── dvc.yaml                       # DVC pipeline определение
├── dvc.lock                       # Lock файл для воспроизводимости
├── params.yaml                    # Параметры модели для DVC
├── .dvcignore                    # Игнорируемые DVC файлы
├── .gitignore                    # Игнорируемые Git файлы (все правила в одном файле)
├── requirements.txt              # Python зависимости
├── pytest.ini                   # Конфигурация pytest
├── Makefile                      # Make команды для удобства
├── main.py                       # Главный скрипт проекта
└── README.md                     # Документация проекта
```

**Примечание**: Файлы, которые игнорируются Git (через корневой `.gitignore`):
- `data/housing.csv` - хранится в `.dvc/cache`, версионируется через `housing.csv.dvc`
- `models/*.pkl`, `models/metrics.json` - генерируются при обучении, версионируются через DVC
- `reports/*.json`, `reports/*.png` - генерируются при выполнении pipeline
- `venv/` - виртуальное окружение (создается локально)
- `.dvc/cache/`, `.dvc/tmp/`, `.dvc/state`, `.dvc/config.local` - локальный кеш DVC

## Установка

### Требования

- Python 3.8 или выше
- pip
- Git (для версионирования)

### Системные зависимости (Linux/Debian/Ubuntu)

Перед созданием виртуального окружения установите необходимые системные пакеты:

```bash
# Для Debian/Ubuntu
sudo apt update
sudo apt install python3-venv python3-pip
```

### Шаги установки

1. Клонируйте репозиторий (если еще не сделано):
```bash
git clone <repository-url>
cd report_automation_versioning_ci_cd
```

2. Создайте виртуальное окружение:
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. Обновите pip:
```bash
pip install --upgrade pip
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Инициализируйте DVC:
```bash
python3 scripts/init_dvc.py
```

> **Примечание**: Локально данные и модели хранятся в кеше DVC (`.dvc/cache`), а в CI/CD используются также версии, сохранённые в облачном хранилище Yandex Object Storage (remote `yandex`).

## Использование

### Валидация данных

```bash
python3 scripts/validate_data.py
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
python3 scripts/train_model.py
```

Обучает модель RandomForestRegressor на данных Boston Housing и сохраняет:
- Модель в `models/model.pkl`
- Метрики в `models/metrics.json`
- Отчет в `reports/training_report.json`

### Оценка модели

```bash
python3 scripts/evaluate_model.py
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

Перед push рекомендуется проверить (убедитесь, что виртуальное окружение активировано):

```bash
# Валидация данных
python3 scripts/validate_data.py

# Обучение и проверка качества
python3 scripts/train_model.py

# Оценка модели
python3 scripts/evaluate_model.py

# Тесты
pytest
```

## Версионирование с DVC

DVC позволяет версионировать большие файлы (данные и модели) отдельно от Git. Файлы хранятся в кеше DVC, а в Git сохраняются только метаданные (`.dvc` файлы).

### Добавление данных в DVC

Если файл уже отслеживается Git, сначала удалите его из индекса Git (файл останется на диске):

```bash
# Если файл уже в Git, удалите его из индекса
git rm --cached data/housing.csv

# Добавьте файл в DVC
dvc add data/housing.csv

# Добавьте метаданные DVC в Git
git add data/housing.csv.dvc data/.gitignore
git commit -m "Add data to DVC"
```

Если файл еще не в Git, просто добавьте его в DVC:

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

### Хранилище DVC: локальный кеш + Yandex Object Storage

Проект использует комбинацию:
- **локальный кеш DVC** (`.dvc/cache`) — для работы на локальной машине;
- **облачное хранилище Yandex Object Storage** (remote `yandex`) — для обмена данными между разработчиком и CI/CD.

**Как это работает:**
- DVC автоматически создает локальный кеш при инициализации
- Все версионированные файлы (данные, модели) хранятся в `.dvc/cache`
- В Git сохраняются только метаданные (`.dvc` файлы), а не сами файлы
- Для отправки данных и моделей в облако используется `dvc push` (remote `yandex`)
- В CI/CD перед валидацией и обучением выполняется `dvc pull`, чтобы восстановить `data/housing.csv` и артефакты из Yandex Object Storage

**Проверка кеша:**
```bash
# Просмотр расположения кеша
dvc cache dir

# Просмотр размера кеша
du -sh .dvc/cache
```

**Очистка кеша (при необходимости):**
```bash
# Очистить неиспользуемые файлы из кеша
dvc cache clean

# Очистить весь кеш (осторожно!)
dvc cache clean --all
```

### Работа с версиями

```bash
# Просмотреть статус изменений
dvc status

# Воспроизвести pipeline (если изменились зависимости)
dvc repro

# Просмотреть историю изменений
dvc diff

# Отправить данные и модели в облако (Yandex Object Storage)
dvc push
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

Параметры модели настраиваются в двух файлах:

1. **`config/model_config.yaml`** - основной файл конфигурации, используется скриптами
2. **`params.yaml`** - файл для DVC, отслеживает изменения параметров для воспроизводимости

Оба файла содержат одинаковые параметры. При изменении параметров обновляйте оба файла:

**`config/model_config.yaml`** (используется скриптами):

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

> **Примечание**: DVC отслеживает изменения в `config/model_config.yaml` через зависимости (`deps`). При изменении конфигурации DVC автоматически запустит переобучение при `dvc repro`.

### DVC Pipeline

Определен в `dvc.yaml`:

```yaml
stages:
  validate_data:
    cmd: python3 scripts/validate_data.py
    deps: [data/housing.csv, scripts/validate_data.py]
    outs: [reports/data_validation_report.json]

  train_model:
    cmd: python3 scripts/train_model.py
    deps: [data/housing.csv, scripts/train_model.py, config/model_config.yaml]
    outs: [models/model.pkl, models/metrics.json, reports/training_report.json]

  evaluate_model:
    cmd: python3 scripts/evaluate_model.py
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
# Добавить новые данные в DVC
dvc add data/new_data.csv

# Если файл уже был в Git, сначала удалите его из индекса
# git rm --cached data/new_data.csv
# dvc add data/new_data.csv

# Добавить метаданные в Git
git add data/new_data.csv.dvc
git commit -m "Add new data version"

# Просмотреть версии
dvc list data/

# Восстановить конкретную версию (по Git тегу или коммиту)
dvc checkout data/housing.csv.dvc@v1.0
```

### Обучение модели

```bash
# Обучение через скрипт
python3 scripts/train_model.py

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
python3 -u scripts/train_model.py
```

## Дальнейшее развитие

1. **MLflow**: Интеграция для трекинга экспериментов и регистрации моделей
2. **Мониторинг**: Добавление мониторинга дрифта данных и деградации модели
3. **A/B тестирование**: Сравнение версий моделей в production
4. **Автоматический деплой**: Деплой лучших моделей на основе метрик качества
5. **Расширенные тесты**: E2E тесты, интеграционные тесты производительности
