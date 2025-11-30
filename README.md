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
│   ├── init_dvc.py               # Инициализация DVC
│   ├── setup_s3_remote.py        # Автоматическая настройка AWS S3
│   └── setup_minio_remote.py     # Автоматическая настройка MinIO
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
├── params.yaml                    # Параметры модели для DVC (отслеживание изменений)
├── .dvcignore                    # Игнорируемые DVC файлы
├── .gitignore                    # Игнорируемые Git файлы
├── requirements.txt              # Python зависимости
├── pytest.ini                   # Конфигурация pytest
├── Makefile                      # Make команды для удобства
├── docker-compose.minio.yml      # Docker Compose для MinIO
├── setup.sh                      # Скрипт первоначальной настройки
└── main.py                       # Главный скрипт проекта
```

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

6. (Опционально) Настройте удаленное хранилище:
```bash
# Вариант 1: MinIO (рекомендуется для локальной разработки)
# Сначала запустите MinIO: docker run -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ':9001'
python3 scripts/setup_minio_remote.py

# Вариант 2: AWS S3
# Убедитесь, что AWS CLI установлен и настроен (aws configure)
python3 scripts/setup_s3_remote.py
```

## Использование

### Валидация данных

```bash
python scripts/validate_data.py
# или
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
python scripts/train_model.py
# или
python3 scripts/train_model.py
```

Обучает модель RandomForestRegressor на данных Boston Housing и сохраняет:
- Модель в `models/model.pkl`
- Метрики в `models/metrics.json`
- Отчет в `reports/training_report.json`

### Оценка модели

```bash
python scripts/evaluate_model.py
# или
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

> **Для начала работы**: Удаленное хранилище не обязательно. Можно работать с локальным хранилищем (`.dvc/cache`). Удаленное хранилище настраивается позже, когда нужно делиться данными с командой или использовать в CI/CD.

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

> **Примечание**: Удаленное хранилище опционально. Для локальной разработки можно использовать локальное хранилище (по умолчанию `.dvc/cache`). Удаленное хранилище необходимо для:
> - Совместной работы в команде
> - Резервного копирования данных и моделей
> - Использования в CI/CD пайплайне

**Параметры команды:**
- `<name>` - произвольное имя для удаленного хранилища (например: `s3remote`, `gsremote`, `azure`)
- `<url>` - URL хранилища, зависит от провайдера (см. примеры ниже)
- `-d` - флаг устанавливает это хранилище как хранилище по умолчанию

#### AWS S3

##### Автоматическая настройка (рекомендуется)

Используйте скрипт для автоматической настройки:

```bash
python3 scripts/setup_s3_remote.py
```

Скрипт автоматически:
- Проверит установку AWS CLI и DVC
- **Автоматически создаст AWS credentials** (IAM пользователь и access key) или предложит ввести существующие
- Создаст S3 bucket (или использует существующий)
- Настроит политику доступа для IAM пользователя к S3 bucket
- Настроит DVC remote
- Протестирует подключение

**Требования перед запуском:**
1. Установлен AWS CLI: `pip install awscli` или следуйте [официальным инструкциям](https://aws.amazon.com/cli/)
2. DVC инициализирован: `python3 scripts/init_dvc.py`

**Варианты настройки credentials:**

- **Ввод вручную** (вариант 2, рекомендуется для начала):
  - Получите Access Key ID и Secret Access Key из [AWS Console](https://console.aws.amazon.com/iam/home#/security_credentials)
  - Или создайте нового IAM пользователя: [AWS IAM Users](https://console.aws.amazon.com/iam/home#/users$new)
  - Скрипт сохранит их в `~/.aws/credentials`

- **Автоматическое создание** (вариант 1):
  - ⚠️ **Требуются валидные AWS credentials администратора**
  - Сначала настройте базовые credentials: `aws configure`
  - Затем скрипт создаст IAM пользователя с минимальными правами доступа к S3 bucket
  - Полезно для создания отдельного пользователя только для DVC

- **Переменные окружения** (вариант 3):
  - Установите `AWS_ACCESS_KEY_ID` и `AWS_SECRET_ACCESS_KEY`
  - Затем запустите скрипт снова

> **Примечание**: Если вы получили ошибку "InvalidClientTokenId" при выборе варианта 1, это означает, что у вас нет валидных AWS credentials. Используйте вариант 2 для ввода credentials вручную.

##### Ручная настройка

Если предпочитаете настроить вручную:

1. **Создайте S3 bucket** (через AWS Console или CLI):
   ```bash
   aws s3 mb s3://my-dvc-storage-bucket
   ```

2. **Настройте аутентификацию** (если еще не настроено):
   ```bash
   aws configure
   # Введите: Access Key ID, Secret Access Key, регион
   ```

3. **Добавьте удаленное хранилище DVC:**
   ```bash
   # name: s3remote (можете выбрать любое имя)
   # url: s3://имя-вашего-bucket/путь-для-dvc
   dvc remote add -d s3remote s3://my-dvc-storage-bucket/dvc-storage
   
   # Настройте путь к credentials (опционально, если используете стандартный путь)
   dvc remote modify s3remote credentialpath ~/.aws/credentials
   ```

4. **Проверьте настройку:**
   ```bash
   dvc remote list
   ```

5. **Загрузите данные:**
   ```bash
   dvc push
   ```

**Пример URL для S3:**
- `s3://my-bucket-name/dvc-storage` - если bucket в том же регионе
- `s3://my-bucket-name/dvc-storage --region us-east-1` - с указанием региона

#### MinIO (S3-совместимое хранилище)

MinIO - это S3-совместимое объектное хранилище, которое можно запустить локально или в собственной инфраструктуре. Идеально подходит для разработки и тестирования без необходимости настройки AWS.

##### Установка MinIO

**Через Docker Compose (рекомендуется):**
```bash
docker-compose -f docker-compose.minio.yml up -d
```

**Через Docker:**
```bash
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ':9001'
```

**Остановка MinIO:**
```bash
# Docker Compose
docker-compose -f docker-compose.minio.yml down

# Docker
docker stop minio
docker rm minio
```

**Локальная установка:**
```bash
# Linux
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server /data --console-address ':9001'
```

После запуска MinIO будет доступен:
- API: http://localhost:9000
- Console (веб-интерфейс): http://localhost:9001
- Default credentials: `minioadmin` / `minioadmin`

##### Автоматическая настройка MinIO для DVC

Используйте скрипт для автоматической настройки:

```bash
python3 scripts/setup_minio_remote.py
```

Скрипт автоматически:
- Проверит установку DVC
- Запросит параметры MinIO (endpoint, credentials, bucket)
- Создаст bucket в MinIO
- Настроит DVC remote с правильным endpoint
- Протестирует подключение

**Требования:**
- MinIO должен быть запущен перед настройкой
- DVC инициализирован: `python3 scripts/init_dvc.py`

##### Ручная настройка MinIO

1. **Создайте bucket** через MinIO Console (http://localhost:9001) или через AWS CLI:
   ```bash
   aws --endpoint-url http://localhost:9000 s3 mb s3://dvc-storage
   ```

2. **Добавьте удаленное хранилище DVC:**
   ```bash
   # Добавляем remote
   dvc remote add -d minio s3://dvc-storage/dvc-storage
   
   # Настраиваем endpoint для MinIO
   dvc remote modify minio endpointurl http://localhost:9000
   
   # Настраиваем credentials
   dvc remote modify minio access_key_id minioadmin
   dvc remote modify minio secret_access_key minioadmin
   ```

3. **Проверьте настройку:**
   ```bash
   dvc remote list
   dvc remote modify minio --list
   ```

4. **Загрузите данные:**
   ```bash
   dvc push
   ```

**Преимущества MinIO:**
- ✅ Работает локально без облачных сервисов
- ✅ S3-совместимый API (работает с DVC без изменений)
- ✅ Бесплатный и open-source
- ✅ Идеально для разработки и тестирования
- ✅ Можно использовать в production

#### Google Cloud Storage

1. **Создайте GCS bucket** (через Console или gsutil):
   ```bash
   gsutil mb gs://my-dvc-storage-bucket
   ```

2. **Настройте аутентификацию:**
   ```bash
   gcloud auth application-default login
   ```

3. **Добавьте удаленное хранилище DVC:**
   ```bash
   # name: gsremote (можете выбрать любое имя)
   # url: gs://имя-вашего-bucket/путь-для-dvc
   dvc remote add -d gsremote gs://my-dvc-storage-bucket/dvc-storage
   ```

4. **Загрузите данные:**
   ```bash
   dvc push
   ```

**Пример URL для GCS:**
- `gs://my-bucket-name/dvc-storage`

#### Azure Blob Storage

1. **Создайте Storage Account и Container** (через Portal или CLI):
   ```bash
   az storage account create --name mystorageaccount --resource-group myResourceGroup
   az storage container create --name dvc-storage --account-name mystorageaccount
   ```

2. **Настройте аутентификацию:**
   ```bash
   az login
   ```

3. **Добавьте удаленное хранилище DVC:**
   ```bash
   # name: azure (можете выбрать любое имя)
   # url: azure://имя-контейнера
   dvc remote add -d azure azure://dvc-storage
   
   # Настройте учетные данные
   dvc remote modify azure account_name mystorageaccount
   dvc remote modify azure account_key "your-account-key"
   ```

**Пример URL для Azure:**
- `azure://container-name` - после настройки account_name и account_key

#### Локальное хранилище (для разработки)

Если не нужно удаленное хранилище, можно использовать локальную файловую систему:

```bash
# Создайте директорию для хранилища
mkdir -p ~/dvc-storage

# Добавьте как удаленное хранилище
dvc remote add -d local ~/dvc-storage

# Или используйте относительный путь
dvc remote add -d local ./dvc-storage
```

#### Просмотр и управление удаленными хранилищами

```bash
# Список всех удаленных хранилищ
dvc remote list

# Просмотр настроек конкретного хранилища
dvc remote modify s3remote --list

# Удаление удаленного хранилища
dvc remote remove s3remote

# Изменение URL хранилища
dvc remote modify s3remote url s3://new-bucket/dvc-storage
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
    cmd: python scripts/validate_data.py
    deps: [data/housing.csv, scripts/validate_data.py]
    outs: [reports/data_validation_report.json]

  train_model:
    cmd: python scripts/train_model.py
    deps: [data/housing.csv, scripts/train_model.py, config/model_config.yaml]
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

1. **Облачное хранилище**: Настройка S3/GCS/Azure для DVC
2. **MLflow**: Интеграция для трекинга экспериментов
3. **Мониторинг**: Добавление мониторинга дрифта данных
4. **A/B тестирование**: Сравнение версий моделей
5. **Автоматический деплой**: Деплой лучших моделей

## Лицензия

MIT

## Авторы

Проект создан для демонстрации автоматизации ML workflow с DVC и CI/CD.
