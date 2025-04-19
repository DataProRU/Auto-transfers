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
5 Разверните базу данных 
```
 docker compose up -d
```

6. Запустите приложение
```
poetry run python src/manage.py runserver
```

7 Запустите телеграмм бота
```
poetry run python src/manage.py start_bot
```
