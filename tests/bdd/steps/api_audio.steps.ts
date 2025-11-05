import { Given, When, Then } from "@cucumber/cucumber";
import request from "supertest";
import assert from "assert";

type App = any;
let app: App;
let response: request.Response;

// We'll import createServer dynamically to avoid module caching during test runs
async function loadCreateServer() {
  const mod = await import("../../../apps/server/src/app.ts");
  return mod.createServer as (deps: any) => Promise<any>;
}

Given(
  "a server with an audio catalog containing files \"{word}\" and \"{word}\"",
  async function (a: string, b: string) {
    const createServer = await loadCreateServer();
    const fakeDeps = {
      listFiles: async () => [
        { id: "1", filename: a, path: "/tmp/" + a, sizeBytes: 1000 },
        { id: "2", filename: b, path: "/tmp/" + b, sizeBytes: 2000 }
      ],
      readMetadata: async (_path: string) => ({ durationSec: 12.345, sampleRate: 48000, channels: 2 })
    };
    app = await createServer(fakeDeps);
  }
);

When("I request GET {string}", async function (path: string) {
  if (typeof app.ready === "function") {
    await app.ready();
  }
  const srv = (app as any).server ?? app;
  response = await request(srv).get(path);
});

Then("the response status should be {int}", function (status: number) {
  assert.strictEqual(response.status, status);
});

Then("the JSON array should have length {int}", function (len: number) {
  assert.ok(Array.isArray(response.body));
  assert.strictEqual(response.body.length, len);
});

Then(
  "each item should include id, filename, durationSec, sizeBytes",
  function () {
    for (const item of response.body) {
      assert.ok(item.id);
      assert.ok(item.filename);
      assert.ok(typeof item.durationSec === "number");
      assert.ok(typeof item.sizeBytes === "number");
    }
  }
);


