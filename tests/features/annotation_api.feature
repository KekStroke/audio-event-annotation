Feature: API для создания и управления аннотациями
  Как пользователь API
  Я хочу создавать и управлять аннотациями аудио-файлов
  Чтобы отмечать события в аудио

  Background:
    Given Flask приложение запущено
    And база данных инициализирована

  Scenario: Создание аннотации
    Given в БД существует AudioFile с id
    And в БД существует EventType с именем "speech"
    When я отправляю POST запрос на "/api/annotations" с телом:
      """
      {
        "audio_file_id": "{id}",
        "event_type_id": "{event_type_id}",
        "start_time": 1.5,
        "end_time": 3.2,
        "event_label": "Speaker 1"
      }
      """
    Then ответ должен иметь статус 201
    And ответ должен содержать JSON с полем "id"
    And ответ должен содержать JSON с полем "start_time" равным 1.5
    And ответ должен содержать JSON с полем "end_time" равным 3.2

  Scenario: Получение списка аннотаций для аудио-файла
    Given в БД существует AudioFile с id
    And в БД существует EventType с именем "speech"
    And в БД существует Annotation для AudioFile
    When я отправляю GET запрос на "/api/annotations?audio_file_id={id}"
    Then ответ должен иметь статус 200
    And ответ должен содержать JSON массив
    And массив должен содержать хотя бы один элемент
    And каждый элемент должен содержать поле "id"

  Scenario: Получение одной аннотации по ID
    Given в БД существует AudioFile с id
    And в БД существует EventType с именем "speech"
    And в БД существует Annotation для AudioFile
    When я отправляю GET запрос на "/api/annotations/{annotation_id}"
    Then ответ должен иметь статус 200
    And ответ должен содержать JSON с полем "id"
    And ответ должен содержать JSON с полем "audio_file_id"

  Scenario: Обновление аннотации
    Given в БД существует AudioFile с id
    And в БД существует EventType с именем "speech"
    And в БД существует Annotation для AudioFile
    When я отправляю PUT запрос на "/api/annotations/{annotation_id}" с телом:
      """
      {
        "start_time": 2.0,
        "end_time": 4.5,
        "event_label": "Updated label"
      }
      """
    Then ответ должен иметь статус 200
    And ответ должен содержать JSON с полем "start_time" равным 2.0
    And ответ должен содержать JSON с полем "end_time" равным 4.5
    And ответ должен содержать JSON с полем "event_label" равным "Updated label"

  Scenario: Удаление аннотации
    Given в БД существует AudioFile с id
    And в БД существует EventType с именем "speech"
    And в БД существует Annotation для AudioFile
    When я отправляю DELETE запрос на "/api/annotations/{annotation_id}"
    Then ответ должен иметь статус 200
    And при повторном запросе аннотация должна быть удалена

  Scenario: Ошибка валидации при start_time >= end_time
    Given в БД существует AudioFile с id
    And в БД существует EventType с именем "speech"
    When я отправляю POST запрос на "/api/annotations" с телом:
      """
      {
        "audio_file_id": "{id}",
        "event_type_id": "{event_type_id}",
        "start_time": 5.0,
        "end_time": 3.0,
        "event_label": "Invalid"
      }
      """
    Then ответ должен иметь статус 400
    And ответ должен содержать JSON с полем "error"

  Scenario: Ошибка валидации при пустом event_label
    Given в БД существует AudioFile с id
    And в БД существует EventType с именем "speech"
    When я отправляю POST запрос на "/api/annotations" с телом:
      """
      {
        "audio_file_id": "{id}",
        "event_type_id": "{event_type_id}",
        "start_time": 1.0,
        "end_time": 2.0,
        "event_label": ""
      }
      """
    Then ответ должен иметь статус 400
    And ответ должен содержать JSON с полем "error"

  Scenario: Ошибка при получении несуществующей аннотации
    Given в БД не существует Annotation с id "00000000-0000-0000-0000-000000000000"
    When я отправляю GET запрос на "/api/annotations/00000000-0000-0000-0000-000000000000"
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"

  Scenario: Ошибка при создании аннотации для несуществующего AudioFile
    Given в БД не существует AudioFile с id "00000000-0000-0000-0000-000000000000"
    And в БД существует EventType с именем "speech"
    When я отправляю POST запрос на "/api/annotations" с телом:
      """
      {
        "audio_file_id": "00000000-0000-0000-0000-000000000000",
        "event_type_id": "{event_type_id}",
        "start_time": 1.0,
        "end_time": 2.0,
        "event_label": "Test"
      }
      """
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"

