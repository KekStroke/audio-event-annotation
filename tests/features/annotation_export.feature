Feature: Экспорт аннотаций в JSON
  Как пользователь приложения
  Я хочу экспортировать аннотации в JSON формат
  Чтобы сохранить данные для дальнейшего использования

  Background:
    Given Flask приложение запущено
    And база данных инициализирована

  Scenario: Экспорт аннотаций в JSON формате
    Given в БД существует AudioFile с id
    And в БД существует EventType с именем "speech"
    And в БД существует Annotation для AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/export?format=json"
    Then ответ должен иметь статус 200
    And ответ должен иметь Content-Type "application/json"
    And ответ должен иметь Content-Disposition header с именем файла
    And ответ должен содержать JSON с полем "audio_file"
    And ответ должен содержать JSON с полем "annotations"
    And ответ должен содержать JSON с полем "export_date"
    And ответ должен содержать JSON с полем "version"

  Scenario: JSON структура включает метаданные файла
    Given в БД существует AudioFile с id
    And в БД существует EventType с именем "speech"
    And в БД существует Annotation для AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/export?format=json"
    Then ответ должен содержать JSON с полем "audio_file"
    And поле "audio_file" должно содержать метаданные файла
    And поле "audio_file" должно содержать поле "id"
    And поле "audio_file" должно содержать поле "filename"
    And поле "audio_file" должно содержать поле "duration"

  Scenario: JSON структура включает все аннотации
    Given в БД существует AudioFile с id
    And в БД существует EventType с именем "speech"
    And в БД существует Annotation для AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/export?format=json"
    Then ответ должен содержать JSON с полем "annotations"
    And поле "annotations" должно быть массивом
    And массив аннотаций должен содержать хотя бы один элемент
    And каждая аннотация должна содержать поле "id"
    And каждая аннотация должна содержать поле "start_time"
    And каждая аннотация должна содержать поле "end_time"
    And каждая аннотация должна содержать поле "event_label"

  Scenario: Экспорт для файла без аннотаций
    Given в БД существует AudioFile с id
    When я отправляю GET запрос на "/api/audio/{id}/export?format=json"
    Then ответ должен иметь статус 200
    And ответ должен содержать JSON с полем "annotations"
    And поле "annotations" должно быть пустым массивом

  Scenario: Ошибка при экспорте несуществующего файла
    Given в БД не существует AudioFile с id "00000000-0000-0000-0000-000000000000"
    When я отправляю GET запрос на "/api/audio/00000000-0000-0000-0000-000000000000/export?format=json"
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"

  Scenario: Кнопка Export в UI
    When я открываю главную страницу "/"
    Then должна быть кнопка "Export"
    And кнопка должна иметь обработчик для экспорта аннотаций




