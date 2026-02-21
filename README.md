# StudyFile

Система управления учебными заданиями для образовательных учреждений.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Описание

StudyFile - это веб-приложение для управления учебными заданиями, которое позволяет:

- **Администраторам**: управлять пользователями, учебными группами, предметами и назначениями
- **Преподавателям**: создавать задания, просматривать и оценивать работы студентов
- **Студентам**: просматривать задания, сдавать работы в виде файлов

## Стек технологий

- **Backend**: Django 5.2, Python 3.13
- **База данных**: PostgreSQL
- **Аутентификация**: django-allauth
- **Админ-панель**: django-smartbase-admin
- **Frontend**: Bootstrap 5, crispy-forms
- **Контейнеризация**: Docker, Docker Compose
- **Управление зависимостями**: uv

## Быстрый старт

### Требования

- Docker и Docker Compose
- just (command runner)

### Запуск проекта

```bash
# Клонировать репозиторий
git clone <repository-url>
cd studyfile

# Запустить контейнеры
just up

# Выполнить миграции (первый запуск)
just manage migrate

# Создать суперпользователя
just manage createsuperuser
```

Приложение будет доступно по адресу: http://localhost:8000

## Основные команды

### Управление контейнерами

```bash
just up          # Запустить контейнеры
just down        # Остановить контейнеры
just build       # Пересобрать образы
just logs        # Просмотр логов
```

### Django команды

```bash
just manage migrate              # Выполнить миграции
just manage makemigrations       # Создать миграции
just manage createsuperuser      # Создать суперпользователя
just manage shell                # Django shell
just manage collectstatic        # Собрать статические файлы
```

### Тестирование

```bash
just manage test                 # Запустить тесты
uv run pytest                    # Запустить тесты с pytest
uv run mypy studyfile            # Проверка типов
```

## Структура проекта

```
studyfile/
├── config/                 # Конфигурация Django
│   ├── settings/          # Настройки (base, local, production)
│   ├── urls.py            # URL маршруты
│   └── sbadmin_config.py  # Конфигурация SmartBase Admin
├── studyfile/
│   ├── users/             # Приложение пользователей
│   │   ├── models.py      # Модели: User, StudyGroup, Subject, TeacherSubject
│   │   ├── sbadmin.py     # Настройки админки
│   │   └── forms.py       # Формы регистрации
│   ├── assignments/       # Приложение заданий
│   │   ├── models.py      # Модели: Assignment, Submission
│   │   ├── views.py       # Представления
│   │   └── sbadmin.py     # Настройки админки
│   └── templates/         # HTML шаблоны
├── locale/                # Файлы локализации
├── compose/               # Docker конфигурации
└── docs/                  # Документация
```

## Роли пользователей

### Администратор
- Управление пользователями (одобрение регистрации студентов)
- Создание учебных групп и предметов
- Назначение преподавателей на предметы
- Доступ к SmartBase Admin (`/sb-admin/`)

### Преподаватель
- Создание и редактирование заданий
- Просмотр списка сданных работ
- Оценка работ студентов

### Студент
- Просмотр доступных заданий
- Загрузка файлов с решениями
- Просмотр оценок и комментариев

## Доступ к админ-панелям

- **SmartBase Admin**: http://localhost:8000/sb-admin/
- **Django Admin**: http://localhost:8000/admin/

## Локализация

Проект поддерживает русский язык. Для компиляции переводов:

```bash
just manage compilemessages --locale ru_RU
```

## Разработка

### Добавление новых зависимостей

```bash
uv add <package-name>
just build
```

### Статический анализ кода

```bash
uv run ruff check .        # Линтер
uv run ruff format .       # Форматирование
uv run mypy studyfile      # Проверка типов
```

## Развертывание

См. [документацию Cookiecutter Django](https://cookiecutter-django.readthedocs.io/en/latest/3-deployment/deployment-with-docker.html) для инструкций по развертыванию.
