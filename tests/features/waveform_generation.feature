Feature: Генерация waveform визуализации
  Как пользователь API
  Я хочу получать waveform изображения аудио-файлов
  Чтобы визуализировать аудио-сигнал

  Background:
    Given Flask приложение запущено
    And база данных инициализирована

  Scenario: Генерация waveform изображения
    Given в БД существует AudioFile с id
    And файл существует по пути из AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/waveform"
    Then ответ должен иметь статус 200
    And ответ должен иметь заголовок "Content-Type" равный "image/png"
    And ответ должен содержать PNG изображение
    And размер изображения должен быть больше 0 байт

  Scenario: Генерация waveform с параметрами width и height
    Given в БД существует AudioFile с id
    And файл существует по пути из AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/waveform?width=800&height=200"
    Then ответ должен иметь статус 200
    And ответ должен иметь заголовок "Content-Type" равный "image/png"
    And ответ должен содержать PNG изображение

  Scenario: Генерация waveform с параметром color
    Given в БД существует AudioFile с id
    And файл существует по пути из AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/waveform?color=FF5733"
    Then ответ должен иметь статус 200
    And ответ должен содержать PNG изображение

  Scenario: Waveform генерируется без кэширования
    Given модуль waveform.py отвечает за генерацию waveform
    When я проверяю реализацию генерации waveform
    Then код не должен использовать директории кэша
    And waveform не должен сохраняться на диск для последующего использования

  Scenario: Ошибка при генерации waveform несуществующего AudioFile
    Given в БД не существует AudioFile с id "00000000-0000-0000-0000-000000000000"
    When я отправляю GET запрос на "/api/audio/00000000-0000-0000-0000-000000000000/waveform"
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"

  Scenario: Ошибка при генерации waveform для несуществующего файла
    Given в БД существует AudioFile с id
    And файл НЕ существует по пути из AudioFile
    When я отправляю GET запрос на "/api/audio/{id}/waveform"
    Then ответ должен иметь статус 404
    And ответ должен содержать JSON с полем "error"

  Scenario: Waveform использует downsampling для больших файлов
    Given в БД существует AudioFile с id
    And файл существует по пути из AudioFile
    And размер файла больше 10MB
    When я отправляю GET запрос на "/api/audio/{id}/waveform?width=1000"
    Then ответ должен иметь статус 200
    And ответ должен содержать PNG изображение
    And генерация должна использовать downsampling




