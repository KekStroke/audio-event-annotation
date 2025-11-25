Feature: Quick Region Creation
  As a user annotating audio
  I want to quickly create regions of specified duration
  So that I can annotate sequentially without manual dragging

  Background:
    Given the application is loaded
    And an audio file with duration 300 seconds is loaded

  Scenario: Create region with default duration
    Given the region duration input has value "10"
    When I click the "Create Region" button
    Then a new region should be created with duration 10 seconds
    And the region should start at position 0 seconds
    And the region should be automatically selected

  Scenario: Create region with custom duration
    Given I set the region duration input to "5"
    When I click the "Create Region" button
    Then a new region should be created with duration 5 seconds
    And the region should start at position 0 seconds
    And the region should be automatically selected

  Scenario: Create region after existing region
    Given a region exists from 0 to 10 seconds
    And the region duration input has value "10"
    When I click the "Create Region" button
    Then a new region should be created with duration 10 seconds
    And the region should start at position 10 seconds
    And the region should be automatically selected

  Scenario: Create region after multiple regions
    Given a region exists from 0 to 10 seconds
    And a region exists from 50 to 60 seconds
    And the region duration input has value "15"
    When I click the "Create Region" button
    Then a new region should be created with duration 15 seconds
    And the region should start at position 60 seconds
    And the region should be automatically selected

  Scenario: Cannot create region beyond audio duration
    Given a region exists from 290 to 300 seconds
    And the region duration input has value "15"
    When I click the "Create Region" button
    Then no new region should be created
    And an error message "Not enough space" should be shown

  Scenario: Validate minimum duration
    Given I set the region duration input to "0"
    When I click the "Create Region" button
    Then no new region should be created
    And an error message "Duration must be at least 0.1 seconds" should be shown

  Scenario: Validate maximum duration
    Given I set the region duration input to "400"
    When I click the "Create Region" button
    Then no new region should be created
    And an error message "Duration cannot exceed audio duration" should be shown

  Scenario: Selected region has visual highlight
    Given a region exists from 0 to 10 seconds
    When I click on the region
    Then the region should have a visual highlight
    And the highlight should be different from unselected regions

  Scenario: Locked annotation region can be visually selected
    Given an annotation exists from 0 to 10 seconds with a locked region
    When I click on the locked region
    Then the locked region should have a visual highlight
    And the highlight should be different from unselected locked regions
