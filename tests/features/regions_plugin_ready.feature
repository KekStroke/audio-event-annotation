Feature: Regions Plugin инициализация и готовность
  Как разработчик
  Я хочу убедиться, что regions plugin правильно инициализируется
  Чтобы избежать ошибок "Regions plugin не готов"

  Background:
    Given Flask приложение запущено
    And в системе есть аудио-файл

  Scenario: audio-player.js диспатчит событие wavesurferRegionsReady
    When я открываю главную страницу "/"
    Then скрипт audio-player.js должен диспатчить событие "wavesurferRegionsReady"
    And событие должно содержать regions plugin в detail

  Scenario: selection-tool.js подписывается на событие wavesurferRegionsReady
    When я открываю главную страницу "/"
    Then selection-tool.js должен подписаться на событие "wavesurferRegionsReady"
    And selection-tool.js должен получить доступ к regions plugin

  Scenario: Regions plugin доступен после загрузки аудио файла
    When я открываю главную страницу "/"
    Then regions plugin должен быть доступен после загрузки аудио
    And функция getWaveSurferRegionsPlugin должна возвращать plugin
    And получение plugin не должно зависеть от кэширования

  Scenario: Событие wavesurferRegionsReady срабатывает вовремя
    When я открываю главную страницу "/"
    Then событие wavesurferRegionsReady должно срабатывать синхронно после инициализации
    And warning "Regions plugin не готов" не должен появляться



