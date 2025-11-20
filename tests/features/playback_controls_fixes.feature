Feature: Playback Controls fixes
  As a user
  I want to see and control playback speed and volume
  So I can customize audio playback

  Scenario: Playback speed control displays current value
    Given index.html contains playback speed range input
    When I check the HTML structure
    Then there should be a label or span displaying speed value
    And the display should be updated when speed changes

  Scenario: Volume control displays current value
    Given index.html contains volume range input
    When I check the HTML structure
    Then there should be a label or span displaying volume value
    And the display should be updated when volume changes

  Scenario: Playback speed control works correctly
    Given audio-player.js handles playback speed changes
    When speed input value changes
    Then wavesurfer.setPlaybackRate should be called

  Scenario: Volume control works correctly
    Given audio-player.js handles volume changes
    When volume input value changes
    Then wavesurfer.setVolume should be called

  Scenario: Play and Pause combined into one button
    Given index.html has separate play and pause buttons
    When I check the controls structure
    Then there should be a single play-pause toggle button
    And button should show play icon when paused
    And button should show pause icon when playing

