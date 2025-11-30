.PHONY: help install init-dvc validate train evaluate test clean dvc-repro

help:
	@echo "Доступные команды:"
	@echo "  make install      - Установить зависимости"
	@echo "  make init-dvc     - Инициализировать DVC"
	@echo "  make validate     - Валидировать данные"
	@echo "  make train        - Обучить модель"
	@echo "  make evaluate     - Оценить модель"
	@echo "  make test         - Запустить тесты"
	@echo "  make dvc-repro    - Запустить DVC pipeline"
	@echo "  make clean        - Очистить временные файлы"

install:
	pip install -r requirements.txt

init-dvc:
	python scripts/init_dvc.py

validate:
	python scripts/validate_data.py

train:
	python scripts/train_model.py

evaluate:
	python scripts/evaluate_model.py

test:
	pytest -v

dvc-repro:
	dvc repro

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov

