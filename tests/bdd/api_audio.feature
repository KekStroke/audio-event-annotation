Feature: Audio catalog API
  As an annotator
  I want to list available audio files with metadata
  So that I can choose a file to annotate

  Scenario: List two audio files with basic metadata
    Given a server with an audio catalog containing files "a.wav" and "b.mp3"
    When I request GET "/api/audio"
    Then the response status should be 200
    And the JSON array should have length 2
    And each item should include id, filename, durationSec, sizeBytes

