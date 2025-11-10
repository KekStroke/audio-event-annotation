Feature: Модели данных и база данных
  Как система
  Я хочу иметь правильно настроенные модели данных
  Чтобы хранить информацию об аудио-файлах и аннотациях

  Background:
    Given база данных инициализирована
    And все таблицы созданы

  Scenario: Создание AudioFile модели
    When я создаю новый AudioFile с данными:
      | file_path          | filename      | duration | sample_rate | channels | file_size |
      | /path/to/audio.wav | audio.wav     | 120.5    | 44100       | 2        | 10485760  |
    Then AudioFile должен быть сохранён в БД
    And AudioFile должен иметь UUID id
    And AudioFile должен иметь created_at timestamp
    And AudioFile должен иметь status "pending"

  Scenario: Получение AudioFile по id
    Given в БД существует AudioFile с filename "test.wav"
    When я получаю AudioFile по его id
    Then я должен получить AudioFile с filename "test.wav"
    And все поля должны быть корректно загружены

  Scenario: Обновление AudioFile
    Given в БД существует AudioFile с status "pending"
    When я обновляю status на "loaded"
    Then AudioFile в БД должен иметь status "loaded"

  Scenario: Удаление AudioFile
    Given в БД существует AudioFile с filename "delete_me.wav"
    When я удаляю этот AudioFile
    Then AudioFile не должен существовать в БД

  Scenario: Создание Annotation модели
    Given в БД существует AudioFile с id
    When я создаю Annotation для этого AudioFile:
      | start_time | end_time | event_label | confidence | notes        |
      | 10.5       | 15.3     | speech      | 0.95       | Test comment |
    Then Annotation должна быть сохранена в БД
    And Annotation должна иметь UUID id
    And Annotation должна иметь created_at и updated_at timestamps
    And Annotation должна быть связана с AudioFile

  Scenario: Получение всех аннотаций для AudioFile
    Given в БД существует AudioFile с 3 аннотациями
    When я получаю все аннотации для этого AudioFile
    Then я должен получить список из 3 аннотаций
    And все аннотации должны быть связаны с этим AudioFile

  Scenario: Создание EventType модели
    When я создаю EventType с данными:
      | name   | color   | description      |
      | speech | #FF5733 | Speech detection |
    Then EventType должен быть сохранён в БД
    And EventType должен иметь UUID id

  Scenario: Получение всех EventType
    Given в БД существует 5 различных EventType
    When я получаю все EventType
    Then я должен получить список из 5 EventType

  Scenario: Создание Project модели
    When я создаю Project с данными:
      | name           | description         |
      | Test Project   | Project for testing |
    Then Project должен быть сохранён в БД
    And Project должен иметь UUID id
    And Project должен иметь created_at timestamp

  Scenario: Cascade удаление - удаление AudioFile удаляет все Annotation
    Given в БД существует AudioFile с 3 аннотациями
    When я удаляю этот AudioFile
    Then все связанные аннотации должны быть удалены

  Scenario: Валидация уникальности названий EventType
    Given в БД существует EventType с name "speech"
    When я пытаюсь создать ещё один EventType с name "speech"
    Then операция должна завершиться с ошибкой

