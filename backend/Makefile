setup-env:
	python3 -m venv venv && source venv/bin/activate
	pip install -U pip
	pip install -r requirements.txt

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

run:
	daphne compeng_gg.asgi:application

test:
	pipenv run pytest

typecheck:
	pipenv run mypy

format:
	pipenv run ruff format courses/quizzes

lint:
	pipenv run ruff check courses/quizzes --fix
