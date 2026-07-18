Feature: Todo API Management

  Scenario: Create a new todo task
    Given the todo API is running
    When I create a todo task "Buy milk"
    Then the task should be created
