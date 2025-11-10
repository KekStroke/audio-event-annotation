# Audio Event Annotation Tool

Веб-приложение для ручной аннотации больших аудио-файлов из локальной файловой системы.

## Описание

Инструмент позволяет:
- Визуализировать аудио через waveform и спектрограмму
- Выделять временные интервалы
- Прослушивать фрагменты
- Размечать наличие интересующих событий для создания датасетов

## Технологический стек

- **Backend**: Python 3.11+ с Flask
- **Аудио-обработка**: librosa, scipy, numpy, soundfile
- **Database**: SQLite с SQLAlchemy
- **Frontend**: HTML5/CSS3/JavaScript + wavesurfer.js
- **Testing**: pytest, pytest-bdd

## Требования

- Python 3.11 или выше
- pip (менеджер пакетов Python)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/KekStroke/audio-event-annotation.git
cd audio-event-annotation
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
```

3. Активируйте виртуальное окружение:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/macOS:
```bash
source venv/bin/activate
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Запуск приложения

1. Убедитесь, что виртуальное окружение активировано

2. Запустите Flask приложение:
```bash
python app.py
```

3. Откройте браузер и перейдите по адресу:
```
http://localhost:5000
```

## Запуск тестов

Для запуска всех тестов:
```bash
pytest
```

Для запуска с покрытием кода:
```bash
pytest --cov=src --cov-report=html
```

Для запуска только BDD тестов:
```bash
pytest tests/test_project_initialization.py
```

## Структура проекта

```
audio-event-annotation/
├── app.py                  # Главный файл Flask приложения
├── requirements.txt        # Python зависимости
├── README.md              # Этот файл
├── .gitignore             # Игнорируемые файлы для Git
├── docs/                  # Документация
│   └── PROJECT_CONTEXT.md # Контекст и архитектура проекта
├── src/                   # Исходный код приложения
│   ├── models/           # Модели данных
│   ├── api/              # API endpoints
│   ├── audio/            # Обработка аудио
│   └── utils/            # Вспомогательные утилиты
├── static/               # Статические файлы (CSS, JS, изображения)
│   ├── css/
│   ├── js/
│   └── images/
└── tests/                # Тесты
    └── features/         # BDD сценарии
```

## Разработка

Проект следует BDD (Behavior-Driven Development) методологии. Перед написанием кода:
1. Создайте `.feature` файлы с Gherkin сценариями
2. Напишите step definitions
3. Реализуйте функциональность для прохождения тестов

## Лицензия

MIT

## Автор

KekStroke

