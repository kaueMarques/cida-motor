package com.example.todo;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class TodoStepDefinitions {

    @Autowired
    private TestRestTemplate restTemplate;

    private Todo createdTodo;

    @Given("the todo API is running")
    public void the_todo_api_is_running() {
        // Context setup
    }

    @When("I create a todo task {string}")
    public void i_create_a_todo_task(String task) {
        Todo todo = new Todo(task);
        createdTodo = restTemplate.postForObject("/todos", todo, Todo.class);
    }

    @Then("the task should be created")
    public void the_task_should_be_created() {
        assertThat(createdTodo).isNotNull();
        assertThat(createdTodo.getTask()).isEqualTo("Buy milk");
    }
}
