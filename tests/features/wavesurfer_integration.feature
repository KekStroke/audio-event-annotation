Feature: Интеграция wavesurfer.js для аудио визуализации
  Как пользователь приложения
  Я хочу видеть waveform и управлять воспроизведением аудио
  Чтобы эффективно работать с аудио-файлами

  Background:
    Given Flask приложение запущено

  Scenario: wavesurfer.js подключен через CDN
    When я открываю главную страницу "/"
    Then HTML должен содержать script тег с wavesurfer.js CDN
    And wavesurfer.js должен быть загружен из CDN

  Scenario: Waveform отображается для выбранного файла
    When я открываю главную страницу "/"
    Then HTML должен содержать элемент с id "waveform"
    And должен быть подключен файл "audio-player.js"
    And функция инициализации wavesurfer должна быть определена
    And HTML должен содержать контейнер "waveform-timeline" для таймлайна
    And HTML должен содержать контейнер "waveform-minimap" для миникарты

  Scenario: Повторный выбор файла не инициирует повторную загрузку
    When я открываю главную страницу "/"
    Then скрипт audio-file-manager должен пропускать повторный выбор текущего файла

  Scenario: Regions plugin уведомляет остальные модули
    When я открываю главную страницу "/"
    Then скрипт audio-player должен диспатчить событие "wavesurferRegionsReady"
    And скрипт selection-tool должен слушать событие "wavesurferRegionsReady"
    And скрипт annotation-list должен слушать событие "wavesurferRegionsReady"

  Scenario: Плагины wavesurfer инициализируются безопасно
    When я открываю главную страницу "/"
    Then скрипт audio-player должен проверять наличие плагинов перед использованием

  Scenario: WaveSurfer создаётся только после пользовательского жеста
    When я открываю главную страницу "/"
    Then скрипт audio-player должен иметь функцию "ensureWaveSurferInitialized"
    And обработчик события "audioFileSelected" должен вызывать "ensureWaveSurferInitialized"
    And WaveSurfer должен использовать MediaElement для избежания AudioContext warning

  Scenario: Работает воспроизведение и пауза
    When я открываю главную страницу "/"
    Then должны быть кнопки Play и Pause
    And кнопки должны иметь обработчики событий для wavesurfer

  Scenario: Отображается текущее время воспроизведения
    When я открываю главную страницу "/"
    Then должен быть элемент для отображения времени
    And должен быть подключен плагин timeline

  Scenario: Работает перемотка кликом по waveform
    When я открываю главную страницу "/"
    Then wavesurfer должен быть инициализирован с опцией interact: true
    And должен быть обработчик события seek

  Scenario: Регионы для выделения интервалов
    When я открываю главную страницу "/"
    Then должен быть подключен плагин regions
    And должна быть функция для создания регионов

  Scenario: Zoom in/out для waveform
    When я открываю главную страницу "/"
    Then должны быть кнопки для zoom in и zoom out
    And должна быть функция для изменения zoom уровня




