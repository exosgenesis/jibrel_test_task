# WARNING!!! FOR ALL TESTS TODAY'S DATE FIXED AT 2010.06.21
# SEE tests/utils.py FOR DETAILS

Feature: Simple tests of api and grabber cooperative work

  Scenario: Init db by grabber
    Given Api, remote, db and grabber
    And DB contain BTC currency with rates rows
      | date       | rate | volume |
    Given Remote API with data for next BTC request
      | MTS              | OPEN | CLOSE | LOW | HIGH | VOLUME |
      | 2010.06.18 04:00 |    1 |  4000 |   1 |    1 |  10000 |
      | 2010.06.19 05:00 |    1 |  4000 |   1 |    1 |  30000 |
      | 2010.06.20 06:00 |    1 |  4001 |   1 |    1 |  30000 |
      | 2010.06.20 07:00 |    1 |  4002 |   1 |    1 |  50000 |
    Then '/currencies' request return
      | id | name |
      | 1  |  BTC |
    When Grabber update data by schedule
    Then '/rate/1' request return 4002 rate and 40000 average volume


  Scenario: Update db by grabber
    Given Api, remote, db and grabber
    And DB contain BTC currency with rates rows
      | date       | rate | volume |
      | 2010.06.19 | 2500 |  20000 |
      | 2010.06.20 | 3000 |  23000 |
    Given Remote API with data for next BTC request
      | MTS              | OPEN | CLOSE | LOW | HIGH | VOLUME |
      | 2010.06.20 23:00 |    1 |  3002 |   1 |    1 |  10000 |
      | 2010.06.21 23:00 |    1 |  4002 |   1 |    1 |  30000 |
    Then '/currencies' request return
      | id | name |
      | 1  |  BTC |
    When Grabber update data by schedule
    Then '/rate/1' request return 4002 rate and 20000 average volume
    Given Remote API with data for next BTC request
      | MTS              | OPEN | CLOSE | LOW | HIGH | VOLUME |
      | 2010.06.21 23:30 |    1 |  4003 |   1 |    1 |  60000 |
    When Grabber update data by schedule
    Then '/rate/1' request return 4003 rate and 30000 average volume


  Scenario: Add new currency
    Given Api, remote, db and grabber
    And DB contain BTC currency with rates rows
      | date       | rate | volume |
      | 2010.06.19 | 2500 |  20000 |
      | 2010.06.20 | 3000 |  10000 |
    And Remote API with data for next BTC request
      | MTS              | OPEN | CLOSE | LOW | HIGH | VOLUME |
      | 2010.06.20 22:00 |    1 |  3000 |   1 |    1 |  10000 |
      | 2010.06.21 23:00 |    1 |  4000 |   1 |    1 |  30000 |
    And Remote API with data for next ETH request
      | MTS              | OPEN | CLOSE | LOW | HIGH | VOLUME |
      | 2010.06.20 23:00 |    1 |   450 |   1 |    1 |   1000 |
      | 2010.06.21 23:00 |    1 |   500 |   1 |    1 |   3000 |
    Then '/currencies' request return
      | id | name |
      | 1  |  BTC |
    And '/rate/1' request return 3000 rate and 15000 average volume
    When Add ETH currency by API request
    Then '/currencies' request return
      | id | name |
      | 1  |  BTC |
      | 2  |  ETH |
    When Grabber update data by schedule
    Then '/rate/1' request return 4000 rate and 20000 average volume
    And '/rate/2' request return 500 rate and 2000 average volume