import { Given, When, Then } from "@cucumber/cucumber";
import assert from "assert";

let value = 0;

Given("a number {int}", function (n: number) {
  value = n;
});

When("I increment it by {int}", function (n: number) {
  value = value + n;
});

Then("the result should be {int}", function (expected: number) {
  // Intentional failing expectation for BDD-first workflow
  assert.strictEqual(value, expected);
});

