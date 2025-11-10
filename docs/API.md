# API Документация Audio Event Annotation Tool

## Оглавление

1. [Введение](#введение)
2. [Базовый URL](#базовый-url)
3. [Формат данных](#формат-данных)
4. [Коды ответов](#коды-ответов)
5. [Audio API](#audio-api)
6. [Annotations API](#annotations-api)
7. [Export API](#export-api)
8. [Примеры использования](#примеры-использования)

## Введение

Audio Event Annotation Tool предоставляет REST API для работы с аудио-файлами и аннотациями. Все endpoints возвращают данные в формате JSON, кроме endpoints для получения изображений (waveform, spectrogram) и потоковой загрузки аудио.

## Базовый URL

```
http://localhost:5000
```

## Формат данных

### JSON

Все запросы и ответы используют формат JSON с кодировкой UTF-8.

### UUID

Все идентификаторы (ID) используют формат UUID v4.

### Временные метки

Временные метки представлены в формате ISO 8601 (например, `2024-01-01T12:00:00`).

### Время в секундах

Время в секундах представлено как число с плавающей точкой (например, `1.5`).

## Коды ответов

- **200 OK**: Успешный запрос
- **201 Created**: Ресурс успешно создан
- **206 Partial Content**: Частичный контент (для Range requests)
- **400 Bad Request**: Ошибка валидации данных
- **404 Not Found**: Ресурс не найден
- **500 Internal Server Error**: Внутренняя ошибка сервера

## Audio API

### POST /api/audio/add

Добавить аудио-файл в систему.

**Request:**
```http
POST /api/audio/add
Content-Type: application/json

{
  "file_path": "/path/to/audio.wav"
}
```

**Parameters:**
- `file_path` (string, required): Абсолютный путь к аудио-файлу в файловой системе

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_path": "/path/to/audio.wav",
  "filename": "audio.wav",
  "duration": 10.5,
  "sample_rate": 44100,
  "channels": 2,
  "file_size": 1234567,
  "created_at": "2024-01-01T12:00:00",
  "status": "loaded"
}
```

**Error Responses:**
- **400 Bad Request**: `file_path is required` или ошибка валидации формата
- **404 Not Found**: Файл не найден
- **500 Internal Server Error**: Ошибка чтения файла или ошибка базы данных

**Example:**
```bash
curl -X POST http://localhost:5000/api/audio/add \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/audio.wav"}'
```

---

### GET /api/audio/{id}

Получить метаданные аудио-файла по ID.

**Request:**
```http
GET /api/audio/{id}
```

**Parameters:**
- `id` (UUID, required): UUID аудио-файла

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_path": "/path/to/audio.wav",
  "filename": "audio.wav",
  "duration": 10.5,
  "sample_rate": 44100,
  "channels": 2,
  "file_size": 1234567,
  "created_at": "2024-01-01T12:00:00",
  "status": "loaded"
}
```

**Error Responses:**
- **400 Bad Request**: Неверный формат ID
- **404 Not Found**: Аудио-файл не найден

**Example:**
```bash
curl http://localhost:5000/api/audio/550e8400-e29b-41d4-a716-446655440000
```

---

### GET /api/audio

Получить список всех аудио-файлов.

**Request:**
```http
GET /api/audio?limit=10&offset=0
```

**Query Parameters:**
- `limit` (integer, optional): Максимальное количество записей
- `offset` (integer, optional): Смещение для пагинации

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "file_path": "/path/to/audio.wav",
    "filename": "audio.wav",
    "duration": 10.5,
    "sample_rate": 44100,
    "channels": 2,
    "file_size": 1234567,
    "created_at": "2024-01-01T12:00:00",
    "status": "loaded"
  }
]
```

**Example:**
```bash
curl http://localhost:5000/api/audio?limit=10&offset=0
```

---

### GET /api/audio/{id}/stream

Потоковая загрузка аудио-файла с поддержкой HTTP Range requests.

**Request:**
```http
GET /api/audio/{id}/stream
Range: bytes=0-1023
```

**Parameters:**
- `id` (UUID, required): UUID аудио-файла

**Headers:**
- `Range` (optional): Заголовок для частичной загрузки (например, `bytes=0-1023`)

**Response (200 OK или 206 Partial Content):**
- **200 OK**: Полный файл
- **206 Partial Content**: Частичный контент (если указан Range header)
- Content-Type: `audio/wav` (или соответствующий MIME type)
- Content-Length: Размер файла или части
- Accept-Ranges: `bytes`

**Error Responses:**
- **400 Bad Request**: Неверный формат ID
- **404 Not Found**: Аудио-файл не найден

**Example:**
```bash
# Полная загрузка
curl http://localhost:5000/api/audio/550e8400-e29b-41d4-a716-446655440000/stream \
  -o audio.wav

# Частичная загрузка (первые 1024 байта)
curl http://localhost:5000/api/audio/550e8400-e29b-41d4-a716-446655440000/stream \
  -H "Range: bytes=0-1023" \
  -o audio_part.wav
```

---

### GET /api/audio/{id}/waveform

Генерация waveform изображения для аудио-файла.

**Request:**
```http
GET /api/audio/{id}/waveform?width=1200&height=300&color=1f77b4
```

**Parameters:**
- `id` (UUID, required): UUID аудио-файла

**Query Parameters:**
- `width` (integer, optional): Ширина изображения в пикселях (по умолчанию 1200, максимум 5000)
- `height` (integer, optional): Высота изображения в пикселях (по умолчанию 300, максимум 2000)
- `color` (string, optional): Цвет waveform в hex формате без # (по умолчанию `1f77b4`)

**Response (200 OK):**
- Content-Type: `image/png`
- Body: PNG изображение waveform

**Error Responses:**
- **400 Bad Request**: Неверный формат ID или параметров
- **404 Not Found**: Аудио-файл не найден
- **500 Internal Server Error**: Ошибка генерации waveform

**Example:**
```bash
curl http://localhost:5000/api/audio/550e8400-e29b-41d4-a716-446655440000/waveform?width=1200&height=300 \
  -o waveform.png
```

---

### GET /api/audio/{id}/spectrogram

Генерация спектрограммы выбранного интервала аудио-файла.

**Request:**
```http
GET /api/audio/{id}/spectrogram?start_time=0&end_time=5&width=1024&height=512&color_map=viridis
```

**Parameters:**
- `id` (UUID, required): UUID аудио-файла

**Query Parameters:**
- `start_time` (float, optional): Начало интервала в секундах (по умолчанию 0)
- `end_time` (float, optional): Конец интервала в секундах (по умолчанию весь файл)
- `width` (integer, optional): Ширина изображения в пикселях (по умолчанию 1024, максимум 5000)
- `height` (integer, optional): Высота изображения в пикселях (по умолчанию 512, максимум 2000)
- `color_map` (string, optional): Название цветовой карты matplotlib (по умолчанию `viridis`)

**Response (200 OK):**
- Content-Type: `image/png`
- Body: PNG изображение спектрограммы

**Error Responses:**
- **400 Bad Request**: Неверный формат ID, параметров или временного интервала
- **404 Not Found**: Аудио-файл не найден
- **500 Internal Server Error**: Ошибка генерации спектрограммы

**Example:**
```bash
curl "http://localhost:5000/api/audio/550e8400-e29b-41d4-a716-446655440000/spectrogram?start_time=0&end_time=5&width=1024&height=512" \
  -o spectrogram.png
```

---

## Annotations API

### POST /api/annotations

Создание новой аннотации.

**Request:**
```http
POST /api/annotations
Content-Type: application/json

{
  "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_time": 1.5,
  "end_time": 3.2,
  "event_label": "Speaker 1",
  "confidence": 0.95,
  "notes": "Some notes"
}
```

**Parameters:**
- `audio_file_id` (UUID, required): UUID аудио-файла
- `start_time` (float, required): Начало интервала в секундах (≥ 0)
- `end_time` (float, required): Конец интервала в секундах (> 0, > start_time)
- `event_label` (string, required): Название события (1-100 символов)
- `confidence` (float, optional): Уровень уверенности (0.0 - 1.0)
- `notes` (string, optional): Дополнительные заметки
- `event_type_id` (UUID, optional): UUID типа события

**Response (201 Created):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_time": 1.5,
  "end_time": 3.2,
  "event_label": "Speaker 1",
  "confidence": 0.95,
  "notes": "Some notes",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

**Error Responses:**
- **400 Bad Request**: Ошибка валидации данных
- **404 Not Found**: AudioFile не найден
- **500 Internal Server Error**: Ошибка создания аннотации

**Example:**
```bash
curl -X POST http://localhost:5000/api/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_time": 1.5,
    "end_time": 3.2,
    "event_label": "Speaker 1",
    "confidence": 0.95
  }'
```

---

### GET /api/annotations

Получение списка аннотаций для аудио-файла.

**Request:**
```http
GET /api/annotations?audio_file_id={id}
```

**Query Parameters:**
- `audio_file_id` (UUID, required): UUID аудио-файла

**Response (200 OK):**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_time": 1.5,
    "end_time": 3.2,
    "event_label": "Speaker 1",
    "confidence": 0.95,
    "notes": "Some notes",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  }
]
```

**Error Responses:**
- **400 Bad Request**: Параметр `audio_file_id` обязателен или неверный формат
- **500 Internal Server Error**: Ошибка получения аннотаций

**Example:**
```bash
curl "http://localhost:5000/api/annotations?audio_file_id=550e8400-e29b-41d4-a716-446655440000"
```

---

### GET /api/annotations/{id}

Получение одной аннотации по ID.

**Request:**
```http
GET /api/annotations/{id}
```

**Parameters:**
- `id` (UUID, required): UUID аннотации

**Response (200 OK):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_time": 1.5,
  "end_time": 3.2,
  "event_label": "Speaker 1",
  "confidence": 0.95,
  "notes": "Some notes",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

**Error Responses:**
- **400 Bad Request**: Неверный формат ID
- **404 Not Found**: Аннотация не найдена

**Example:**
```bash
curl http://localhost:5000/api/annotations/660e8400-e29b-41d4-a716-446655440000
```

---

### PUT /api/annotations/{id}

Обновление аннотации.

**Request:**
```http
PUT /api/annotations/{id}
Content-Type: application/json

{
  "start_time": 2.0,
  "end_time": 4.5,
  "event_label": "Updated label",
  "confidence": 0.9,
  "notes": "Updated notes"
}
```

**Parameters:**
- `id` (UUID, required): UUID аннотации

**Body Parameters (все опциональны):**
- `start_time` (float, optional): Начало интервала в секундах (≥ 0)
- `end_time` (float, optional): Конец интервала в секундах (> 0, > start_time)
- `event_label` (string, optional): Название события (1-100 символов)
- `confidence` (float, optional): Уровень уверенности (0.0 - 1.0)
- `notes` (string, optional): Дополнительные заметки

**Response (200 OK):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_time": 2.0,
  "end_time": 4.5,
  "event_label": "Updated label",
  "confidence": 0.9,
  "notes": "Updated notes",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:30:00"
}
```

**Error Responses:**
- **400 Bad Request**: Ошибка валидации данных
- **404 Not Found**: Аннотация не найдена
- **500 Internal Server Error**: Ошибка обновления аннотации

**Example:**
```bash
curl -X PUT http://localhost:5000/api/annotations/660e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": 2.0,
    "end_time": 4.5,
    "event_label": "Updated label"
  }'
```

---

### DELETE /api/annotations/{id}

Удаление аннотации.

**Request:**
```http
DELETE /api/annotations/{id}
```

**Parameters:**
- `id` (UUID, required): UUID аннотации

**Response (200 OK):**
```json
{
  "message": "Annotation удалена"
}
```

**Error Responses:**
- **400 Bad Request**: Неверный формат ID
- **404 Not Found**: Аннотация не найдена
- **500 Internal Server Error**: Ошибка удаления аннотации

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/annotations/660e8400-e29b-41d4-a716-446655440000
```

---

## Export API

### GET /api/audio/{id}/export

Экспорт аннотаций для аудио-файла в JSON формате.

**Request:**
```http
GET /api/audio/{id}/export?format=json
```

**Parameters:**
- `id` (UUID, required): UUID аудио-файла

**Query Parameters:**
- `format` (string, optional): Формат экспорта (по умолчанию `json`)

**Response (200 OK):**
- Content-Type: `application/json`
- Content-Disposition: `attachment; filename="{filename}_annotations.json"`
- Body: JSON файл с аннотациями

```json
{
  "audio_file": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "audio.wav",
    "file_path": "/path/to/audio.wav",
    "duration": 10.5,
    "sample_rate": 44100,
    "channels": 2,
    "file_size": 1234567,
    "status": "loaded",
    "created_at": "2024-01-01T12:00:00"
  },
  "annotations": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
      "start_time": 1.5,
      "end_time": 3.2,
      "event_label": "Speaker 1",
      "confidence": 0.95,
      "notes": "Some notes",
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00"
    }
  ],
  "export_date": "2024-01-01T12:30:00Z",
  "version": "1.0"
}
```

**Error Responses:**
- **400 Bad Request**: Неверный формат ID или неподдерживаемый формат
- **404 Not Found**: AudioFile не найден
- **500 Internal Server Error**: Ошибка экспорта аннотаций

**Example:**
```bash
curl http://localhost:5000/api/audio/550e8400-e29b-41d4-a716-446655440000/export?format=json \
  -o annotations.json
```

---

## Примеры использования

### Пример 1: Полный цикл работы

```bash
# 1. Загрузить файл
curl -X POST http://localhost:5000/api/audio/add \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/audio.wav"}'

# Ответ: {"id": "550e8400-...", ...}

# 2. Получить метаданные
curl http://localhost:5000/api/audio/550e8400-e29b-41d4-a716-446655440000

# 3. Создать аннотацию
curl -X POST http://localhost:5000/api/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_time": 1.0,
    "end_time": 2.5,
    "event_label": "Speaker 1"
  }'

# 4. Получить список аннотаций
curl "http://localhost:5000/api/annotations?audio_file_id=550e8400-e29b-41d4-a716-446655440000"

# 5. Экспортировать аннотации
curl http://localhost:5000/api/audio/550e8400-e29b-41d4-a716-446655440000/export?format=json \
  -o annotations.json
```

### Пример 2: Python

```python
import requests

base_url = "http://localhost:5000"

# Загрузить файл
response = requests.post(
    f"{base_url}/api/audio/add",
    json={"file_path": "/path/to/audio.wav"}
)
audio_file = response.json()
audio_file_id = audio_file["id"]

# Создать аннотацию
annotation = requests.post(
    f"{base_url}/api/annotations",
    json={
        "audio_file_id": audio_file_id,
        "start_time": 1.0,
        "end_time": 2.5,
        "event_label": "Speaker 1",
        "confidence": 0.95
    }
)

# Получить список аннотаций
annotations = requests.get(
    f"{base_url}/api/annotations",
    params={"audio_file_id": audio_file_id}
)

# Экспортировать аннотации
export = requests.get(
    f"{base_url}/api/audio/{audio_file_id}/export",
    params={"format": "json"}
)
with open("annotations.json", "wb") as f:
    f.write(export.content)
```

### Пример 3: JavaScript (Fetch API)

```javascript
const baseUrl = "http://localhost:5000";

// Загрузить файл
const audioFile = await fetch(`${baseUrl}/api/audio/add`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ file_path: "/path/to/audio.wav" })
}).then(r => r.json());

// Создать аннотацию
const annotation = await fetch(`${baseUrl}/api/annotations`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    audio_file_id: audioFile.id,
    start_time: 1.0,
    end_time: 2.5,
    event_label: "Speaker 1",
    confidence: 0.95
  })
}).then(r => r.json());

// Получить список аннотаций
const annotations = await fetch(
  `${baseUrl}/api/annotations?audio_file_id=${audioFile.id}`
).then(r => r.json());

// Экспортировать аннотации
const exportData = await fetch(
  `${baseUrl}/api/audio/${audioFile.id}/export?format=json`
).then(r => r.blob());
```

## Ошибки

Все ошибки возвращаются в следующем формате:

```json
{
  "error": "Описание ошибки"
}
```

### Типы ошибок

- **Валидация**: Ошибки валидации входных данных (400)
- **Не найдено**: Ресурс не найден (404)
- **Внутренняя ошибка**: Ошибки сервера (500)

## Ограничения

- Максимальный размер файла: 16GB
- Максимальная ширина изображения: 5000 пикселей
- Максимальная высота изображения: 2000 пикселей
- Максимальная длина event_label: 100 символов
- Confidence должен быть между 0.0 и 1.0

## Поддержка

Если у вас возникли проблемы или вопросы:

1. Проверьте документацию в `README.md`
2. Проверьте руководство пользователя в `docs/USER_GUIDE.md`
3. Проверьте примеры использования выше
4. Создайте issue в GitHub репозитории

## Лицензия

MIT

## Автор

KekStroke

