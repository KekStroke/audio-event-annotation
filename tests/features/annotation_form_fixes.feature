Feature: Annotation Form fixes
  As a user
  I want to create annotations successfully
  So I can annotate audio regions

  Scenario: Create Annotation gets audioFileId from window.currentAudioFileId
    Given annotation-form.js contains submitAnnotationForm function
    When I check submitAnnotationForm code
    Then function should check window.currentAudioFileId
    And function should use currentAudioFileId if audioFileId is not set

  Scenario: Annotation form audioFileId is synchronized on file selection
    Given annotation-form.js subscribes to audioFileSelected event
    When audioFileSelected event is dispatched
    Then annotation form should update its audioFileId

