# Руководство по использованию Audio Event Annotation Tool

## Оглавление

1. [Быстрый старт](#быстрый-старт)
2. [Работа с API](#работа-с-api)
3. [Работа с UI](#работа-с-ui)
4. [Примеры использования](#примеры-использования)
5. [Часто задаваемые вопросы](#часто-задаваемые-вопросы)

## Быстрый старт

### 1. Запуск приложения

```bash
# Активировать виртуальное окружение
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Запустить Flask приложение
python app.py
```

Приложение будет доступно по адресу: `http://localhost:5000`

### 2. Загрузка первого файла

#### Через API:

```bash
curl -X POST http://localhost:5000/api/audio/add \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/your/audio.wav"}'
```

#### Через UI:

1. Откройте браузер: `http://localhost:5000`
2. Используйте API для загрузки файла (прямая загрузка через UI будет добавлена в будущем)

## Работа с API

### Audio API

#### Добавить аудио файл

```bash
POST /api/audio/add
Content-Type: application/json

{
  "file_path": "/path/to/audio.wav"
}
```

**Ответ:**
```json
{
  "id": "uuid",
  "filename": "audio.wav",
  "duration": 10.5,
  "sample_rate": 44100,
  "channels": 2,
  "file_size": 1234567,
  "status": "loaded"
}
```

#### Получить метаданные файла

```bash
GET /api/audio/{id}
```

#### Получить список файлов

```bash
GET /api/audio
```

#### Потоковая загрузка файла

```bash
GET /api/audio/{id}/stream
```

Поддерживает HTTP Range requests для загрузки по частям.

#### Waveform изображение

```bash
GET /api/audio/{id}/waveform?width=1200&height=200
```

Параметры:
- `width` (опционально): Ширина изображения (по умолчанию 1200)
- `height` (опционально): Высота изображения (по умолчанию 200)
- `color` (опционально): Цвет waveform (по умолчанию "#1f77b4")

#### Спектрограмма изображение

```bash
GET /api/audio/{id}/spectrogram?start_time=0&end_time=10&width=1200&height=400
```

Параметры:
- `start_time` (опционально): Начальное время в секундах (по умолчанию 0)
- `end_time` (опционально): Конечное время в секундах (по умолчанию весь файл)
- `width` (опционально): Ширина изображения (по умолчанию 1200)
- `height` (опционально): Высота изображения (по умолчанию 400)
- `color_map` (опционально): Цветовая карта (по умолчанию "magma")

#### Экспорт аннотаций

```bash
GET /api/audio/{id}/export?format=json
```

Возвращает JSON файл со всеми аннотациями.

### Annotation API

#### Создать аннотацию

```bash
POST /api/annotations
Content-Type: application/json

{
  "audio_file_id": "uuid",
  "start_time": 1.5,
  "end_time": 3.2,
  "event_label": "Speaker 1",
  "confidence": 0.95,
  "notes": "Optional notes"
}
```

**Ответ:**
```json
{
  "id": "uuid",
  "audio_file_id": "uuid",
  "start_time": 1.5,
  "end_time": 3.2,
  "event_label": "Speaker 1",
  "confidence": 0.95,
  "notes": "Optional notes",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

#### Получить список аннотаций

```bash
GET /api/annotations?audio_file_id={id}
```

#### Получить аннотацию

```bash
GET /api/annotations/{id}
```

#### Обновить аннотацию

```bash
PUT /api/annotations/{id}
Content-Type: application/json

{
  "start_time": 2.0,
  "end_time": 4.5,
  "event_label": "Updated label",
  "confidence": 0.98
}
```

#### Удалить аннотацию

```bash
DELETE /api/annotations/{id}
```

## Работа с UI

### Интерфейс

Приложение имеет следующий интерфейс:

1. **Toolbar** - Панель инструментов вверху
2. **Sidebar** - Боковая панель с аннотациями
3. **Workspace** - Рабочая область с waveform
4. **Control Panel** - Панель управления внизу

### Основные действия

#### 1. Загрузка файла

Используйте API для загрузки файла. После загрузки файл автоматически появится в списке.

#### 2. Визуализация

После загрузки файла:
- Waveform автоматически отображается в workspace
- Можно использовать кнопки "Zoom In" и "Zoom Out" для масштабирования
- Время отображается в формате MM:SS

#### 3. Выделение региона

1. Нажмите и удерживайте левую кнопку мыши на waveform
2. Перетащите для выделения региона
3. Время региона отображается под waveform
4. Можно проиграть выделенный регион кнопкой "Play Selection"

#### 4. Создание аннотации

1. Выделите регион на waveform
2. Нажмите кнопку "Create Annotation"
3. Заполните форму:
   - Event Label (обязательно)
   - Confidence (0.0 - 1.0, опционально)
   - Notes (опционально)
4. Нажмите "Save"

#### 5. Редактирование аннотации

1. Нажмите на аннотацию в списке
2. Нажмите кнопку "Edit"
3. Измените данные
4. Нажмите "Save"

#### 6. Удаление аннотации

1. Нажмите на аннотацию в списке
2. Нажмите кнопку "Delete"
3. Подтвердите удаление

#### 7. Экспорт аннотаций

1. Нажмите кнопку "Export" в workspace
2. JSON файл автоматически скачается

### Горячие клавиши

- **Space** - Воспроизвести/остановить аудио
- **← →** - Перемотка (планируется)

## Примеры использования

### Пример 1: Полный цикл работы

```bash
# 1. Загрузить файл
curl -X POST http://localhost:5000/api/audio/add \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/audio.wav"}'

# Ответ: {"id": "uuid-123", ...}

# 2. Создать аннотацию
curl -X POST http://localhost:5000/api/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "audio_file_id": "uuid-123",
    "start_time": 1.0,
    "end_time": 2.5,
    "event_label": "Speaker 1"
  }'

# 3. Получить список аннотаций
curl http://localhost:5000/api/annotations?audio_file_id=uuid-123

# 4. Экспортировать аннотации
curl http://localhost:5000/api/audio/uuid-123/export?format=json \
  -o annotations.json
```

### Пример 2: Работа с большими файлами

```bash
# Загрузить большой файл (до 16GB)
curl -X POST http://localhost:5000/api/audio/add \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/large_audio.wav"}'

# Получить waveform (автоматически кэшируется)
curl http://localhost:5000/api/audio/{id}/waveform \
  -o waveform.png

# Получить спектрограмму для конкретного интервала
curl "http://localhost:5000/api/audio/{id}/spectrogram?start_time=0&end_time=60" \
  -o spectrogram.png
```

### Пример 3: Массовое создание аннотаций

```python
import requests

base_url = "http://localhost:5000"
audio_file_id = "uuid-123"

annotations = [
    {"start_time": 1.0, "end_time": 2.5, "event_label": "Speaker 1"},
    {"start_time": 3.0, "end_time": 4.5, "event_label": "Speaker 2"},
    {"start_time": 5.0, "end_time": 6.5, "event_label": "Noise"},
]

for ann in annotations:
    ann["audio_file_id"] = audio_file_id
    response = requests.post(f"{base_url}/api/annotations", json=ann)
    print(f"Created: {response.json()}")
```

## Часто задаваемые вопросы

### Q: Какой формат аудио файлов поддерживается?

A: Приложение поддерживает все форматы, которые поддерживает `librosa` и `soundfile`:
- WAV
- MP3
- FLAC
- OGG
- и другие

### Q: Какой максимальный размер файла?

A: Максимальный размер файла - 16GB (настраивается в `app.py`).

### Q: Куда сохраняются waveform и спектрограммы?

A: Они не сохраняются — изображения формируются заново для каждого запроса.

### Q: Как удалить все аннотации для файла?

A: Используйте API для удаления каждой аннотации или удалите файл из БД (все аннотации удалятся автоматически из-за cascade delete).

### Q: Можно ли импортировать аннотации из JSON?

A: Импорт аннотаций будет добавлен в будущих версиях. Сейчас можно использовать API для создания аннотаций из JSON.

### Q: Как работает кэширование?

A: Кэширование отключено. Это гарантирует, что каждый запрос получает актуальное изображение.

## Поддержка

Если у вас возникли проблемы или вопросы:
1. Проверьте документацию в `README.md`
2. Запустите тесты: `pytest -v`
3. Создайте issue в GitHub репозитории

## Лицензия

MIT




