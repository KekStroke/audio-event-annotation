Feature: Генерация спектрограммы аудио-файла
  Как пользователь API
  Я хочу получать спектрограмму выбранного участка аудио
  Чтобы визуализировать частотный спектр

  Background:
    Given Flask приложение запущено
    And база данных инициализирована

  Scenario: Генерация спектрограммы по умолчанию
    Given в БД существует AudioFile с id
    And файл существует по пути из AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/spectrogram"
    Then ответ должен иметь статус 200
    And ответ должен иметь заголовок "Content-Type" равный "image/png"
    And ответ должен содержать PNG изображение

  Scenario: Генерация спектрограммы с параметрами
    Given в БД существует AudioFile с id
    And файл существует по пути из AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/spectrogram?start_time=1.0&end_time=3.0&width=800&height=400&color_map=plasma"
    Then ответ должен иметь статус 200
    And ответ должен содержать PNG изображение

  Scenario: Спектрограмма кэшируется на диске
    Given в БД существует AudioFile с id
    And файл существует по пути из AudioFile
    And кэш директория для спектрограмм существует
    When я отправляю GET запрос на "/api/audio/{id}/spectrogram?start_time=0.5&end_time=2.5"
    Then файл спектрограммы должен быть сохранён в кэше
    And при повторном запросе спектрограмма должна использовать кэш

  Scenario: Ошибка при генерации спектрограммы несуществующего AudioFile
    Given в БД не существует AudioFile с id "00000000-0000-0000-0000-000000000000"
    When я отправляю GET запрос на "/api/audio/00000000-0000-0000-0000-000000000000/spectrogram"
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"

  Scenario: Ошибка при генерации спектрограммы для несуществующего файла
    Given в БД существует AudioFile с id
    And файл НЕ существует по пути из AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/spectrogram"
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"

  Scenario: Ошибка при некорректном временном интервале
    Given в БД существует AudioFile с id
    And файл существует по пути из AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/spectrogram?start_time=5&end_time=2"
    Then ответ должен иметь статус 400
    And ответ должен содержать JSON с полем "error"
