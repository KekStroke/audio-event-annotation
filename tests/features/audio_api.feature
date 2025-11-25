Feature: API для загрузки и чтения аудио-файлов
  Как пользователь API
  Я хочу загружать аудио-файлы и получать их метаданные
  Чтобы работать с аудио-файлами через REST API

  Background:
    Given Flask приложение запущено
    And база данных инициализирована

  Scenario: Добавление аудио-файла через API
    Given существует аудио-файл "test.wav" по пути "/test/audio/test.wav"
    When я отправляю POST запрос на "/api/audio/add" с телом:
      """
      {
        "file_path": "/test/audio/test.wav"
      }
      """
    Then ответ должен иметь статус 201
    And ответ должен содержать JSON с полем "id"
    And ответ должен содержать JSON с полем "filename" равным "test.wav"
    And ответ должен содержать JSON с полем "duration"
    And ответ должен содержать JSON с полем "sample_rate"
    And ответ должен содержать JSON с полем "channels"
    And ответ должен содержать JSON с полем "file_size"
    And AudioFile должен быть сохранён в БД

  Scenario: Получение метаданных аудио-файла по ID
    Given в БД существует AudioFile с id
    When я отправляю GET запрос на "/api/audio/{id}"
    Then ответ должен иметь статус 200
    And ответ должен содержать JSON с полем "id"
    And ответ должен содержать JSON с полем "filename"
    And ответ должен содержать JSON с полем "duration"
    And ответ должен содержать JSON с полем "sample_rate"
    And ответ должен содержать JSON с полем "channels"
    And ответ должен содержать JSON с полем "file_size"
    And ответ должен содержать JSON с полем "status"

  Scenario: Получение списка всех аудио-файлов
    Given в БД существует 3 AudioFile
    When я отправляю GET запрос на "/api/audio"
    Then ответ должен иметь статус 200
    And ответ должен содержать JSON массив
    And массив должен содержать 3 элемента
    And каждый элемент должен содержать поле "id"
    And каждый элемент должен содержать поле "filename"

  Scenario: Ошибка при добавлении несуществующего файла
    Given файл "/nonexistent/audio.wav" не существует
    When я отправляю POST запрос на "/api/audio/add" с телом:
      """
      {
        "file_path": "/nonexistent/audio.wav"
      }
      """
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"
    And поле "error" должно содержать "File not found"

  Scenario: Ошибка при добавлении файла неподдерживаемого формата
    Given существует файл "test.txt" по пути "/test/audio/test.txt"
    When я отправляю POST запрос на "/api/audio/add" с телом:
      """
      {
        "file_path": "/test/audio/test.txt"
      }
      """
    Then ответ должен иметь статус 400
    And ответ должен содержать JSON с полем "error"
    And поле "error" должно содержать "Unsupported file format"

  Scenario: Ошибка при получении несуществующего файла
    Given в БД не существует AudioFile с id "00000000-0000-0000-0000-000000000000"
    When я отправляю GET запрос на "/api/audio/00000000-0000-0000-0000-000000000000"
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"
    And поле "error" должно содержать "Audio file not found"

  Scenario: Валидация обязательных полей при добавлении файла
    When я отправляю POST запрос на "/api/audio/add" с телом:
      """
      {}
      """
    Then ответ должен иметь статус 400
    And ответ должен содержать JSON с полем "error"
    And поле "error" должно содержать "file_path is required"

  Scenario: Удаление аудио-файла
    Given в БД существует AudioFile с id
    When я отправляю DELETE запрос на "/api/audio/{id}"
    Then ответ должен иметь статус 200
    And ответ должен содержать JSON с полем "message" равным "Audio file deleted successfully"
    And AudioFile не должен существовать в БД

  Scenario: Ошибка при удалении несуществующего файла
    Given в БД не существует AudioFile с id "00000000-0000-0000-0000-000000000000"
    When я отправляю DELETE запрос на "/api/audio/00000000-0000-0000-0000-000000000000"
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"
    And поле "error" должно содержать "Audio file not found"

  Scenario: Импорт аудио-файлов из директории
    Given существует директория "/test/audio_folder" с 2 аудио-файлами
    When я отправляю POST запрос на "/api/audio/import" с телом:
      """
      {
        "path": "/test/audio_folder"
      }
      """
    Then ответ должен иметь статус 200
    And ответ должен содержать JSON с полем "imported_count" равным 2
    And в БД существует 2 AudioFile

  Scenario: Ошибка при импорте из несуществующей директории
    Given директория "/nonexistent/folder" не существует
    When я отправляю POST запрос на "/api/audio/import" с телом:
      """
      {
        "path": "/nonexistent/folder"
      }
      """
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"

