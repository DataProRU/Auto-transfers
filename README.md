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
https://python-poetry.org/docs/managing-environments/#bash-csh-zsh
4. Установите библиотеки
```
poetry install
```
5. Запустите приложение
```
python manage.py runserver #  или poetry run python manage.py runserver
```