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

### Все тесты

Для запуска всех тестов:
```bash
pytest
```

Для запуска с подробным выводом:
```bash
pytest -v
```

### Типы тестов

**Unit тесты:**
```bash
pytest tests/test_project_initialization.py
```

**BDD тесты:**
```bash
pytest tests/test_*.py
```

**E2E интеграционные тесты:**
```bash
pytest tests/test_e2e_integration.py -v
```

**Тесты конкретного функционала:**
```bash
# Тесты API
pytest tests/test_audio_api.py tests/test_annotation_api.py

# Тесты визуализации
pytest tests/test_waveform_generation.py tests/test_spectrogram_generation.py

# Тесты UI
pytest tests/test_ui_layout.py tests/test_wavesurfer_integration.py
```

### Покрытие кода

Для запуска с покрытием кода:
```bash
pytest --cov=src --cov-report=html
```

Результаты будут в `htmlcov/index.html`

## Использование

После запуска приложения откройте браузер и перейдите по адресу `http://localhost:5000`.

### Основные функции:

1. **Загрузка аудио файла**: 
   - Используйте API endpoint `POST /api/audio/add` для добавления файла
   - Передайте `file_path` в JSON теле запроса
   - Пример:
   ```bash
   curl -X POST http://localhost:5000/api/audio/add \
     -H "Content-Type: application/json" \
     -d '{"file_path": "/path/to/audio.wav"}'
   ```

2. **Визуализация**: 
   - Waveform: `GET /api/audio/{id}/waveform`
   - Спектрограмма: `GET /api/audio/{id}/spectrogram`
   - Автоматически генерируются и кэшируются

3. **Аннотация**: 
   - Создание: `POST /api/annotations`
   - Просмотр: `GET /api/annotations?audio_file_id={id}`
   - Обновление: `PUT /api/annotations/{id}`
   - Удаление: `DELETE /api/annotations/{id}`
   - В UI: Выделяйте регионы на waveform и создавайте аннотации через модальное окно

4. **Экспорт**: 
   - `GET /api/audio/{id}/export?format=json`
   - Экспортирует все аннотации файла в JSON формате
   - В UI: Нажмите кнопку "Export" для скачивания

### API Endpoints

#### Audio
- `POST /api/audio/add` - Добавить аудио файл
- `GET /api/audio/{id}` - Получить метаданные файла
- `GET /api/audio` - Список всех файлов
- `GET /api/audio/{id}/stream` - Потоковая загрузка файла
- `GET /api/audio/{id}/waveform` - Waveform изображение
- `GET /api/audio/{id}/spectrogram` - Спектрограмма изображение
- `GET /api/audio/{id}/export?format=json` - Экспорт аннотаций

#### Annotations
- `POST /api/annotations` - Создать аннотацию
- `GET /api/annotations?audio_file_id={id}` - Список аннотаций файла
- `GET /api/annotations/{id}` - Получить аннотацию
- `PUT /api/annotations/{id}` - Обновить аннотацию
- `DELETE /api/annotations/{id}` - Удалить аннотацию

### Работа с большими файлами

Приложение поддерживает работу с файлами до 16GB. Для оптимизации:
- Waveform и спектрограммы кэшируются на диске
- Аудио файлы загружаются по частям (HTTP Range requests)
- Используется downsampling для waveform визуализации

### Примеры использования

**Полный цикл работы:**
1. Загрузить файл через API
2. Открыть файл в UI (автоматически загружается waveform)
3. Выделить регион на waveform
4. Создать аннотацию через модальное окно
5. Экспортировать все аннотации в JSON

Подробнее см. [docs/USAGE.md](docs/USAGE.md)

## Структура проекта

```
audio-event-annotation/
├── app.py                  # Главный файл Flask приложения
├── requirements.txt        # Python зависимости
├── README.md              # Этот файл
├── .gitignore             # Игнорируемые файлы для Git
├── docs/                  # Документация
│   ├── PROJECT_CONTEXT.md # Контекст и архитектура проекта
│   ├── USAGE.md           # Руководство по использованию
│   ├── USER_GUIDE.md      # Руководство пользователя
│   └── API.md             # Документация API
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

### Методология

Проект следует BDD (Behavior-Driven Development) и TDD (Test-Driven Development) методологиям:

1. **RED**: Напишите BDD сценарии (`.feature` файлы) и step definitions
2. **RED**: Запустите тесты - они должны падать (функциональность не реализована)
3. **GREEN**: Реализуйте минимальный код для прохождения тестов
4. **REFACTOR**: Улучшите код, сохраняя прохождение тестов

### Структура тестов

```
tests/
├── features/              # BDD сценарии (Gherkin)
│   ├── project_initialization.feature
│   ├── database_models.feature
│   ├── audio_api.feature
│   ├── annotation_api.feature
│   └── e2e_integration.feature
└── test_*.py             # Step definitions и тесты
```

### Правила разработки

1. **Размер файлов**: Максимум 400 строк (идеально 200-300)
2. **Тесты**: Все тесты должны проходить перед коммитом
3. **Коммиты**: Один коммит = одна задача/issue
4. **Документация**: Обновляйте README при добавлении нового функционала

### Запуск в режиме разработки

```bash
# Активировать виртуальное окружение
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Запустить Flask с автоматической перезагрузкой
python app.py

# Запустить тесты в watch режиме (требует pytest-watch)
ptw tests/
```

## Лицензия

MIT

## Автор

KekStroke

