Feature: Drag selection для создания регионов
  Как пользователь
  Я хочу выделять регионы мышкой через drag
  Чтобы создавать аннотации для аудио фрагментов

  Background:
    Given Flask приложение запущено
    And в системе есть аудио-файл

  Scenario: Regions plugin должен быть настроен с dragSelection
    When я открываю главную страницу "/"
    Then в конфигурации regions plugin должен быть включен dragSelection: true

  Scenario: Regions plugin инициализируется с правильными параметрами
    When я открываю главную страницу "/"
    Then buildWaveSurferPlugins создает regions plugin с dragSelection
    And regions plugin должен быть активен после инициализации

  Scenario: WaveSurfer должен иметь interact: true
    When я открываю главную страницу "/"
    Then в конфигурации WaveSurfer.create должен быть interact: true
    And это позволяет взаимодействовать с waveform

  Scenario: Regions plugin доступен сразу после инициализации WaveSurfer
    When я открываю главную страницу "/"
    Then после вызова ensureWaveSurferInitialized regions plugin должен быть сразу доступен
    And getWaveSurferRegionsPlugin должна возвращать непустой объект
    And regions plugin должен иметь метод addRegion

  Scenario: Waveform контейнер не должен быть скрыт
    When я открываю главную страницу "/"
    Then waveform контейнер должен быть видим и доступен для взаимодействия
    And waveform контейнер не должен быть перекрыт loading indicator
    And CSS стили не должны блокировать pointer-events на waveform

