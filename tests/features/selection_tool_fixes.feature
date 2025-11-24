Feature: Selection Tool fixes
  As a user
  I want selection tools to work correctly
  So I can work with regions efficiently

  Scenario: Clear Selection deletes only current selected region
    Given selection-tool.js contains clearSelection function
    When I check clearSelection code
    Then function should call selectionToolCurrentRegion.remove()
    And function should NOT call clearRegions() to delete all regions
    And function should NOT delete all regions in a loop

  Scenario: Zoom to Region uses correct API
    Given selection-tool.js contains zoomToRegion function
    When I check zoomToRegion code
    Then function should call wavesurfer.zoom()
    And function should call wavesurfer.seekTo()
    And function should use parameters from selectionToolCurrentRegion

  Scenario: Play Selection stops at region end
    Given selection-tool.js contains playSelection function
    When I check playSelection code
    Then function should use timeupdate event handler
    And handler should check currentTime >= region.end
    And handler should call pause() when reaching end

  Scenario: Audio File ID is taken from window.currentAudioFileId
    Given selection-tool.js contains ensureAudioFileId function
    When function is called
    Then it should check window.currentAudioFileId
    And set selectionToolCurrentAudioFileId from global variable

  Scenario: Audio player получает regions plugin без кэширования
    Given audio-player.js не содержит функций кэширования
    When я проверяю реализацию getWaveSurferRegionsPlugin
    Then функция должна использовать wavesurfer.getActivePlugins()
    And код не должен обращаться к window.waveSurferRegionsPlugin

