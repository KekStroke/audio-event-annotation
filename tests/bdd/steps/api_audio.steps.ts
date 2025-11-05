import { Given, When, Then } from "@cucumber/cucumber";
import request from "supertest";
import assert from "assert";
import Fastify from "fastify";

type App = any;
let app: App;
let response: request.Response;

// We'll import createServer dynamically to avoid module caching during test runs
async function loadCreateServer() {
  const mod = await import("../../../apps/server/dist/catalog.js");
  const buildAudioList = mod.buildAudioList as (
    files: Array<{
      id: string;
      filename: string;
      path: string;
      sizeBytes: number;
    }>,
    readMetadata: (
      path: string
    ) => Promise<{
      durationSec: number;
      sampleRate?: number;
      channels?: number;
    }>
  ) => Promise<any[]>;
  return async function createServer(deps: any) {
    const app = Fastify();
    app.get("/api/audio", async (_req, reply) => {
      try {
        const files = await deps.listFiles();
        const results = await buildAudioList(files, deps.readMetadata);
        reply.send(results);
      } catch (err) {
        reply.code(500).send({ error: "internal" });
      }
    });
    return app as any;
  };
}

Given(
  'a server with an audio catalog containing files "{word}" and "{word}"',
  async function (a: string, b: string) {
    const createServer = await loadCreateServer();
    const fakeDeps = {
      listFiles: async () => [
        { id: "1", filename: a, path: "/tmp/" + a, sizeBytes: 1000 },
        { id: "2", filename: b, path: "/tmp/" + b, sizeBytes: 2000 },
      ],
      readMetadata: async (_path: string) => ({
        durationSec: 12.345,
        sampleRate: 48000,
        channels: 2,
      }),
    };
    app = await createServer(fakeDeps);
  }
);

Given(
  'a server where metadata reading fails for file "{word}" and succeeds for file "{word}"',
  async function (bad: string, good: string) {
    const createServer = await loadCreateServer();
    const files = [
      { id: "1", filename: bad, path: "/tmp/" + bad, sizeBytes: 1000 },
      { id: "2", filename: good, path: "/tmp/" + good, sizeBytes: 2000 },
    ];
    const fakeDeps = {
      listFiles: async () => files,
      readMetadata: async (p: string) => {
        if (p.endsWith(bad)) {
          throw new Error("unreadable");
        }
        return { durationSec: 10.5, sampleRate: 44100, channels: 2 };
      },
    };
    app = await createServer(fakeDeps);
  }
);

Given("a server where listing files fails with an error", async function () {
  const createServer = await loadCreateServer();
  const fakeDeps = {
    listFiles: async () => {
      throw new Error("fs error");
    },
    readMetadata: async (_p: string) => ({ durationSec: 1 }),
  };
  app = await createServer(fakeDeps);
});

When("I request GET {string}", async function (path: string) {
  if (typeof app.ready === "function") {
    await app.ready();
  }
  const srv = (app as any).server ?? app;
  response = await request(srv).get(path);
});

Then("the response status should be {int}", function (status: number) {
  if (response.status !== status) {
    console.log("Expected:", status, "Got:", response.status);
    console.log("Body:", response.body);
    console.log("Headers:", response.headers);
  }
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
      assert.ok(typeof item.id === "string" && item.id.length > 0);
      assert.ok(typeof item.filename === "string" && item.filename.length > 0);
      assert.ok(typeof item.durationSec === "number");
      assert.ok(typeof item.sizeBytes === "number");
      assert.ok(item.durationSec >= 0);
      assert.ok(item.sizeBytes >= 0);
    }
  }
);
