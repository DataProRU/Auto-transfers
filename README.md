![Lint](https://github.com/your/repo/actions/workflows/lint.yml/badge.svg)
![Tests](https://github.com/your/repo/actions/workflows/test_app.yml/badge.svg)
![Deploy](https://github.com/your/repo/actions/workflows/deploy.yml/badge.svg)

Для запуска приложения

1. Склонируйте репозиторий
2. Установите pyenv
https://github.com/pyenv/pyenv
```
pyenv install 3.12.7
pyenv local 3.12.7
```
3. Создайте и запустите виртуальное окружение poetry
```
poetry env use python3.12 # или 3.12.7
eval $(poetry env activate) 
```
Документация
```
https://python-poetry.org/docs/managing-environments/#bash-csh-zsh
```
4. Установите библиотеки
```
poetry install
```
5. Разверните базу данных 
```
 docker compose up -d
```
6. Примените миграции
```
poetry run python src/manage.py migrate
```
7. Запустите приложение
```
poetry run python src/manage.py runserver
```
8. Запустите телеграмм бота
```
poetry run python src/manage.py start_bot
```
