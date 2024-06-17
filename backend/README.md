# GKSport

## Описание

проект на Django - DRF - JAZZMIN

## Установка

версия Python: 3.11

1. Установить Python 3.11 +
2. Установить Git
3. Клонировать репозиторий
4. Создать виртуальное окружение (Python 3.11)

    ```bash
    python -m venv venv
    ```

5. Активировать виртуальное окружение

   | Platform | Shell           | Command to activate virtual environment |
   |----------|-----------------|-----------------------------------------|
   | POSIX    | bash/zsh        | `source <venv>/bin/activate`            |
   |          | fish            | `source <venv>/bin/activate.fish`       |
   |          | csh/tcsh        | `source <venv>/bin/activate.csh`        |
   |          | PowerShell Core | `<venv>/bin/Activate.ps1`               |
   | Windows  | cmd.exe         | `<venv>\Scripts\activate.b`             |
   |          | PowerShell      | `<venv>\Scripts\Activate.ps1`           |

6. Установить необходимые зависимости

   ```bash
   pip install -r requirements.txt
   ```

7. Установить pre-commit хуки

   ```bash
   pre-commit install -t pre-commit -t commit-msg -t pre-push
   ```

8. Выполнить для корректной сборки и отображения админ панели

    ```bash
    python manage.py collectstatic
    ````

9. Применить миграции

    ```bash
    python manage.py migrate
    ```

11. __ТОЛЬКО ПРИ ПЕРВОМ ДЕПЛОЕ__ Создать суперпользователя
   login: +70000000000
   password: 1231231231
    ```bash
    python manage.py createsuperuser
    ```



12. Задать переменные виртуального окружения

    * Для разработки данный пункт является необязательным, так как у всех переменных, есть значения по умолчанию

    * также можно использовать `.env`

   | Platform | Shell           | Command to set variable       |
   |----------|-----------------|-------------------------------|
   | POSIX    | bash/zsh        | `export <variable>=<value>`   |
   |          | fish            | `set -x <variable> <value>`   |
   |          | csh/tcsh        | `setenv <variable> <value>`   |
   |          | PowerShell Core | `$env:<variable> = "<value>"` |
   | Windows  | cmd.exe         | `set <variable>=<value>`      |
   |          | PowerShell      | `$env:<variable> = "<value>"` |

13. Запускаем celery, celery-beat
      ```bash
      celery -A config.celery worker --detach
      celery -A config.celery beat --detach --scheduler django_celery_beat.schedulers:DatabaseScheduler
      ```


### Список переменных виртуального окружения

1. DJANGO_CONFIGURATION - Конфигурация
    - `Development` - для разработки, **не использовать на стейджинге и продакшене**
    - `Production` - использовать на стейджинге и продакшене
2. DJANGO_SECRET_KEY
    - str
3. DJANGO_CSRF_TRUSTED_ORIGINS - Список допустимых доменов CSRF, сюда обязательно вписать адрес фронта, если домен не
   совпадает с бекендом. Например http://localhost:3000
    - str with separate ","
4. DJANGO_CORS_ORIGIN_WHITELIST - Список допустимых доменов CORS, сюда обязательно вписать адрес фронта, если домен не
   совпадает с бекендом. Например http://localhost:3000
    - str with separate ","
5. DJANGO_DOMAIN - Домен без слеша в конце, например http://localhost:8000
    - str
