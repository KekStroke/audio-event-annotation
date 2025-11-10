# MVP Backlog: Audio Event Annotations

**Дата создания**: 2025-11-10

Этот документ содержит структурированный список задач для реализации MVP. Каждая задача должна быть создана как отдельный Issue в GitHub с соответствующими метками.

---

## EPIC 1: Инфраструктура и Setup [epic, setup]

### Issue #1: Инициализация проекта и базовая структура
**Labels**: `setup`, `infrastructure`

**Описание**:
Создать базовую структуру проекта с необходимыми конфигурационными файлами.

**Acceptance Criteria**:
- [ ] Создана структура директорий согласно `docs/PROJECT_CONTEXT.md`
- [ ] Создан `requirements.txt` с зависимостями (Flask, SQLAlchemy, librosa, soundfile, pytest, pytest-bdd)
- [ ] Создан `config.py` с конфигурацией приложения (dev/prod режимы)
- [ ] Создан `run.py` - точка входа приложения
- [ ] Создан `.gitignore` для Python проектов
- [ ] Проект запускается без ошибок

**Definition of Done**:
- Все файлы созданы
- `python run.py` запускает Flask сервер на localhost
- Структура соответствует PROJECT_CONTEXT.md

---

### Issue #2: Настройка базы данных и моделей
**Labels**: `setup`, `database`

**Описание**:
Создать SQLAlchemy модели для всех сущностей и настроить подключение к SQLite.

**Acceptance Criteria**:
- [ ] Создана модель `AudioFile` в `app/models/audio_file.py`
- [ ] Создана модель `AudioSegment` в `app/models/audio_segment.py`
- [ ] Создана модель `Event` в `app/models/event.py`
- [ ] Создана модель `Annotation` в `app/models/annotation.py`
- [ ] Создана модель `Project` в `app/models/project.py`
- [ ] Настроена миграция БД (Flask-Migrate или Alembic)
- [ ] Создан скрипт инициализации БД
- [ ] Все модели имеют корректные relationships

**Definition of Done**:
- БД создается автоматически при первом запуске
- Все модели проходят базовые тесты (создание, чтение)
- Размер каждого файла модели < 200 строк

---

## EPIC 2: Работа с Аудиофайлами [epic, audio]

### Issue #3: Загрузка и сканирование аудиофайлов
**Labels**: `feature`, `audio`, `backend`

**Описание**:
Реализовать endpoint для загрузки аудиофайла из файловой системы и извлечения его метаданных.

**BDD Feature**:
```gherkin
Feature: Загрузка аудиофайла
  Scenario: Успешная загрузка WAV файла
    Given существует аудиофайл "test_audio.wav" в файловой системе
    When пользователь выбирает этот файл
    Then система извлекает метаданные (duration, sample_rate, channels)
    And сохраняет запись в таблицу AudioFile
    And возвращает ID файла
```

**Acceptance Criteria**:
- [ ] Создан route `POST /api/audio/load` в `app/routes/audio.py`
- [ ] Создан service `AudioFileService` в `app/services/audio_service.py`
- [ ] Поддерживаются форматы: WAV, MP3, FLAC, OGG
- [ ] Извлекаются метаданные: duration, sample_rate, channels, file_size
- [ ] Путь к файлу валидируется (файл должен существовать)
- [ ] Написан BDD тест в `tests/features/load_audio.feature`

**Definition of Done**:
- API endpoint работает и возвращает корректные данные
- BDD тесты проходят
- Обрабатываются ошибки (файл не найден, неподдерживаемый формат)

---

### Issue #4: Генерация waveform данных
**Labels**: `feature`, `audio`, `backend`

**Описание**:
Реализовать endpoint для получения downsampled waveform данных для визуализации.

**BDD Feature**:
```gherkin
Feature: Генерация waveform
  Scenario: Получение waveform для большого файла
    Given загружен аудиофайл длительностью 3600 секунд
    When запрашиваются waveform данные с разрешением 1000 точек
    Then система возвращает 1000 точек (min/max пары)
    And время ответа < 2 секунд
```

**Acceptance Criteria**:
- [ ] Создан route `GET /api/audio/<id>/waveform` с параметром `resolution`
- [ ] Реализован алгоритм downsampling в `app/utils/audio_processing.py`
- [ ] Данные кешируются для быстрого повторного доступа
- [ ] Поддержка стерео (возвращаются данные для каждого канала)
- [ ] Оптимизация для больших файлов (streaming)
- [ ] Написан BDD тест

**Definition of Done**:
- Endpoint возвращает JSON с waveform данными
- Работает для файлов размером > 1 GB
- BDD тесты проходят
- Время генерации waveform < 5 сек для 1 часа аудио

---

### Issue #5: Генерация спектрограммы для участка
**Labels**: `feature`, `audio`, `backend`

**Описание**:
Реализовать endpoint для генерации спектрограммы для выбранного временного участка.

**BDD Feature**:
```gherkin
Feature: Генерация спектрограммы
  Scenario: Получение спектрограммы для участка 5 секунд
    Given загружен аудиофайл
    When запрашивается спектрограмма для участка от 10 до 15 секунд
    Then система возвращает изображение спектрограммы в формате PNG
    And время ответа < 3 секунд
```

**Acceptance Criteria**:
- [ ] Создан route `GET /api/audio/<id>/spectrogram?start=<s>&end=<e>`
- [ ] Используется librosa для генерации mel-спектрограммы
- [ ] Возвращается PNG изображение или JSON с данными
- [ ] Параметры: окно FFT, hop_length, количество mel-bins
- [ ] Написан BDD тест

**Definition of Done**:
- Endpoint возвращает корректную спектрограмму
- BDD тесты проходят
- Поддержка участков до 60 секунд

---

### Issue #6: Streaming аудио для воспроизведения
**Labels**: `feature`, `audio`, `backend`

**Описание**:
Реализовать endpoint для потокового воспроизведения аудио.

**Acceptance Criteria**:
- [ ] Создан route `GET /api/audio/<id>/stream`
- [ ] Поддержка HTTP Range requests для перемотки
- [ ] Возможность воспроизведения участка `?start=<s>&end=<e>`
- [ ] Конвертация в MP3 для совместимости с браузерами
- [ ] Написан BDD тест

**Definition of Done**:
- Аудио воспроизводится в браузере
- Работает перемотка
- BDD тесты проходят

---

## EPIC 3: Управление Событиями [epic, events]

### Issue #7: CRUD для типов событий (Events)
**Labels**: `feature`, `backend`

**Описание**:
Реализовать API endpoints для создания, чтения, обновления и удаления типов событий.

**BDD Feature**:
```gherkin
Feature: Управление событиями
  Scenario: Создание нового типа события
    Given пользователь в системе
    When создается событие с именем "Speech" и цветом "#FF5733"
    Then событие сохраняется в БД
    And возвращается ID события
```

**Acceptance Criteria**:
- [ ] Создан route `POST /api/events` (создание)
- [ ] Создан route `GET /api/events` (список всех)
- [ ] Создан route `GET /api/events/<id>` (получение одного)
- [ ] Создан route `PUT /api/events/<id>` (обновление)
- [ ] Создан route `DELETE /api/events/<id>` (удаление)
- [ ] Валидация: имя обязательно, цвет в hex формате
- [ ] Написаны BDD тесты для всех операций

**Definition of Done**:
- Все CRUD операции работают
- BDD тесты проходят
- Обработка ошибок (дубликаты имен, несуществующий ID)

---

## EPIC 4: Аннотирование [epic, annotations]

### Issue #8: Создание аннотаций
**Labels**: `feature`, `backend`

**Описание**:
Реализовать endpoint для создания аннотаций событий на временной шкале аудио.

**BDD Feature**:
```gherkin
Feature: Создание аннотации
  Scenario: Разметка речевого события
    Given загружен аудиофайл с ID "abc-123"
    And существует тип события "Speech"
    When создается аннотация от 10.5 до 15.3 секунд с типом "Speech"
    Then аннотация сохраняется в БД
    And возвращается ID аннотации
```

**Acceptance Criteria**:
- [ ] Создан route `POST /api/annotations`
- [ ] Параметры: audio_file_id, event_id, start_time, end_time, confidence, notes
- [ ] Валидация: start_time < end_time, время в пределах длительности файла
- [ ] Проверка существования audio_file и event
- [ ] Написан BDD тест

**Definition of Done**:
- Endpoint создает аннотации
- BDD тесты проходят
- Валидация работает корректно

---

### Issue #9: Получение и редактирование аннотаций
**Labels**: `feature`, `backend`

**Описание**:
Реализовать endpoints для получения списка аннотаций и их редактирования.

**Acceptance Criteria**:
- [ ] Создан route `GET /api/audio/<id>/annotations` (все аннотации файла)
- [ ] Создан route `GET /api/annotations/<id>` (одна аннотация)
- [ ] Создан route `PUT /api/annotations/<id>` (обновление)
- [ ] Создан route `DELETE /api/annotations/<id>` (удаление)
- [ ] Фильтрация по типу события
- [ ] Сортировка по времени
- [ ] Написаны BDD тесты

**Definition of Done**:
- Все endpoints работают
- BDD тесты проходят

---

### Issue #10: Экспорт аннотаций
**Labels**: `feature`, `backend`

**Описание**:
Реализовать экспорт аннотаций в форматах JSON и CSV.

**BDD Feature**:
```gherkin
Feature: Экспорт аннотаций
  Scenario: Экспорт в JSON
    Given аудиофайл с 5 аннотациями
    When запрашивается экспорт в формате JSON
    Then возвращается файл со всеми аннотациями
    And формат соответствует схеме
```

**Acceptance Criteria**:
- [ ] Создан route `GET /api/audio/<id>/annotations/export?format=json`
- [ ] Поддержка форматов: JSON, CSV
- [ ] JSON формат: массив объектов с полями аннотации
- [ ] CSV формат: таблица с колонками
- [ ] Написан BDD тест

**Definition of Done**:
- Экспорт работает для обоих форматов
- BDD тесты проходят

---

## EPIC 5: Frontend Interface [epic, frontend]

### Issue #11: Базовый HTML интерфейс и layout
**Labels**: `feature`, `frontend`

**Описание**:
Создать базовую HTML структуру приложения с навигацией и layout.

**Acceptance Criteria**:
- [ ] Создан `templates/base.html` с базовым layout
- [ ] Создан `templates/index.html` - главная страница
- [ ] Создан `templates/audio_viewer.html` - страница просмотра аудио
- [ ] Подключен CSS фреймворк (через CDN, например Bootstrap или Tailwind)
- [ ] Responsive дизайн (работает на десктопе)
- [ ] Навигационное меню

**Definition of Done**:
- Страницы отображаются корректно
- Верстка адаптивная
- Размер каждого шаблона < 300 строк

---

### Issue #12: Интеграция Wavesurfer.js для waveform
**Labels**: `feature`, `frontend`

**Описание**:
Интегрировать библиотеку Wavesurfer.js для визуализации и взаимодействия с waveform.

**Acceptance Criteria**:
- [ ] Подключен Wavesurfer.js через CDN
- [ ] Создан `static/js/audio_player.js` с логикой плеера
- [ ] Отображение waveform загруженного файла
- [ ] Кнопки play/pause
- [ ] Перемотка кликом по waveform
- [ ] Индикатор текущего времени

**Definition of Done**:
- Waveform отображается
- Воспроизведение работает
- Интерфейс интуитивный

---

### Issue #13: Визуализация спектрограммы (Canvas)
**Labels**: `feature`, `frontend`

**Описание**:
Реализовать отображение спектрограммы с использованием Canvas API.

**Acceptance Criteria**:
- [ ] Создан компонент спектрограммы в `static/js/spectrogram.js`
- [ ] Запрос данных спектрограммы с сервера
- [ ] Отрисовка на Canvas
- [ ] Цветовая шкала (viridis или jet)
- [ ] Синхронизация со временем воспроизведения

**Definition of Done**:
- Спектрограмма отображается корректно
- Синхронизирована с waveform

---

### Issue #14: Выделение участков (regions)
**Labels**: `feature`, `frontend`

**Описание**:
Реализовать функционал выделения временных участков на waveform.

**Acceptance Criteria**:
- [ ] Использование Wavesurfer Regions plugin
- [ ] Создание региона drag-and-drop
- [ ] Редактирование границ региона
- [ ] Воспроизведение выделенного региона
- [ ] Отображение длительности региона
- [ ] Удаление региона

**Definition of Done**:
- Регионы создаются и редактируются
- UX интуитивный

---

### Issue #15: UI для создания и редактирования аннотаций
**Labels**: `feature`, `frontend`

**Описание**:
Создать интерфейс для работы с аннотациями событий.

**Acceptance Criteria**:
- [ ] Форма создания аннотации для выделенного региона
- [ ] Выбор типа события из списка
- [ ] Поле для confidence (slider 0-100%)
- [ ] Текстовое поле для заметок
- [ ] Список всех аннотаций файла (sidebar)
- [ ] Редактирование существующих аннотаций
- [ ] Удаление аннотаций
- [ ] Цветовая индикация регионов по типу события

**Definition of Done**:
- CRUD аннотаций работает через UI
- Аннотации отображаются на waveform цветными регионами

---

### Issue #16: Управление типами событий в UI
**Labels**: `feature`, `frontend`

**Описание**:
Создать интерфейс для управления типами событий.

**Acceptance Criteria**:
- [ ] Страница/модальное окно для управления событиями
- [ ] Список всех типов событий
- [ ] Форма создания нового типа (имя, цвет с color picker)
- [ ] Редактирование существующих
- [ ] Удаление (с предупреждением если есть аннотации)

**Definition of Done**:
- CRUD событий работает через UI
- Color picker работает корректно

---

### Issue #17: Загрузка файла через UI
**Labels**: `feature`, `frontend`

**Описание**:
Реализовать интерфейс для выбора аудиофайла из файловой системы.

**Acceptance Criteria**:
- [ ] Input для выбора файла (file picker)
- [ ] Отображение информации о файле (имя, размер, длительность)
- [ ] Индикатор загрузки/обработки
- [ ] Обработка ошибок (неподдерживаемый формат)
- [ ] Переход на страницу просмотра после загрузки

**Definition of Done**:
- Файл можно выбрать и загрузить
- Корректная обработка ошибок

---

## EPIC 6: Тестирование и Документация [epic, testing]

### Issue #18: Покрытие тестами всех endpoints
**Labels**: `testing`, `backend`

**Описание**:
Убедиться, что все API endpoints покрыты BDD тестами.

**Acceptance Criteria**:
- [ ] Все .feature файлы созданы и актуальны
- [ ] Все step definitions реализованы
- [ ] Покрытие кода тестами > 80%
- [ ] Все тесты проходят

**Definition of Done**:
- `pytest tests/` выполняется успешно
- Coverage report показывает > 80%

---

### Issue #19: Документация API (OpenAPI/Swagger)
**Labels**: `documentation`

**Описание**:
Создать документацию API в формате OpenAPI.

**Acceptance Criteria**:
- [ ] Создан файл `docs/API.md` или `openapi.yaml`
- [ ] Документированы все endpoints
- [ ] Примеры запросов и ответов
- [ ] Описание моделей данных

**Definition of Done**:
- Документация полная и актуальная
- Можно использовать для интеграции

---

### Issue #20: User Guide и README
**Labels**: `documentation`

**Описание**:
Создать пользовательскую документацию и README.

**Acceptance Criteria**:
- [ ] README.md с описанием проекта, установки и запуска
- [ ] Документ User Guide с инструкциями по использованию
- [ ] Скриншоты интерфейса
- [ ] Список поддерживаемых форматов

**Definition of Done**:
- Новый пользователь может запустить проект по README
- User Guide понятен и полон

---

## Приоритеты выполнения

**Фаза 1 - Foundation** (Issues #1-2):
Базовая инфраструктура и модели данных

**Фаза 2 - Backend Core** (Issues #3-10):
Вся бизнес-логика и API

**Фаза 3 - Frontend** (Issues #11-17):
Пользовательский интерфейс

**Фаза 4 - Polish** (Issues #18-20):
Тестирование и документация

---

## Метки для GitHub Issues

- `epic` - высокоуровневая функциональность
- `setup` - настройка инфраструктуры
- `feature` - новая функциональность
- `backend` - backend работа
- `frontend` - frontend работа
- `audio` - работа с аудио
- `database` - работа с БД
- `testing` - тестирование
- `documentation` - документация
- `bug` - баг (для будущего)
- `enhancement` - улучшение (для будущего)

