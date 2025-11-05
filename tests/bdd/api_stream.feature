Feature: HTTP Range audio streaming
  As a client
  I want partial content responses
  So that I can seek within large audio without full download

  Scenario: Partial content from start
    Given a server with audio id "1" mapped to file "/tmp/a.wav" of size 4096 bytes
    When I request GET "/api/audio/1/stream" with header "Range: bytes=0-1023"
    Then the stream response status should be 206
    And stream header "Accept-Ranges" should be "bytes"
    And stream header "Content-Range" should match "bytes 0-1023/4096"
    And the stream response body length should be 1024

  Scenario: Invalid range returns 416
    Given a server with audio id "1" mapped to file "/tmp/a.wav" of size 4096 bytes
    When I request GET "/api/audio/1/stream" with header "Range: bytes=9999-12000"
    Then the stream response status should be 416
    And stream header "Content-Range" should be "bytes */4096"

  Scenario: Missing file returns 404
    Given a server with no file for id "999"
    When I request GET "/api/audio/999/stream" with no headers
    Then the stream response status should be 404

