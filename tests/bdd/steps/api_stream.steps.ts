import { Given, When, Then } from "@cucumber/cucumber";
import request from "supertest";
// We'll prefer the built server to avoid ts-node ESM resolution quirks
import assert from "assert";

type App = any;
let streamApp: App;
let streamResponse: request.Response;

async function loadCreateServer() {
  const mod = await import("../../../apps/server/dist/app.js");
  return mod.createServer as (deps: any) => Promise<any>;
}

const memoryFiles = new Map<string, { path: string; sizeBytes: number; buffer: Buffer }>();

Given(
  "a server with audio id {string} mapped to file {string} of size {int} bytes",
  async function (id: string, path: string, size: number) {
    const createServer = await loadCreateServer();
    const buf = Buffer.alloc(size, 0xaa);
    memoryFiles.set(id, { path, sizeBytes: size, buffer: buf });
    const deps = {
      listFiles: async () => Array.from(memoryFiles.entries()).map(([k, v]) => ({ id: k, filename: v.path.split("/").pop(), path: v.path, sizeBytes: v.sizeBytes })),
      readMetadata: async (_p: string) => ({ durationSec: 0 }),
      openReadStream: (id2: string, start: number, end: number) => {
        const f = memoryFiles.get(id2);
        if (!f) throw Object.assign(new Error("not found"), { code: "ENOENT" });
        return f.buffer.subarray(start, end + 1);
      },
      statById: (id2: string) => {
        const f = memoryFiles.get(id2);
        if (!f) throw Object.assign(new Error("not found"), { code: "ENOENT" });
        return { size: f.sizeBytes };
      }
    };
    streamApp = await createServer(deps);
  }
);

Given("a server with no file for id {string}", async function (id: string) {
  const createServer = await loadCreateServer();
  memoryFiles.clear();
  const deps = {
    listFiles: async () => [],
    readMetadata: async (_p: string) => ({ durationSec: 0 }),
    openReadStream: (_id: string, _s: number, _e: number) => { throw Object.assign(new Error("not found"), { code: "ENOENT" }); },
    statById: (_id: string) => { throw Object.assign(new Error("not found"), { code: "ENOENT" }); }
  };
  streamApp = await createServer(deps);
});

When("I request GET {string} with header {string}", async function (path: string, header: string) {
  if (typeof streamApp.ready === "function") await streamApp.ready();
  const [name, value] = header.split(":");
  const srv = (streamApp as any).server ?? streamApp;
  streamResponse = await request(srv).get(path).set(name.trim(), value.trim());
});

When("I request GET {string} with no headers", async function (path: string) {
  if (typeof streamApp.ready === "function") await streamApp.ready();
  const srv = (streamApp as any).server ?? streamApp;
  streamResponse = await request(srv).get(path);
});

Then("the stream response status should be {int}", function (status: number) {
  assert.strictEqual(streamResponse.status, status);
});

Then("stream header {string} should be {string}", function (name: string, expected: string) {
  assert.strictEqual(streamResponse.headers[name.toLowerCase()], expected);
});

Then("stream header {string} should match {string}", function (name: string, pattern: string) {
  const value = streamResponse.headers[name.toLowerCase()];
  assert.ok(new RegExp(pattern).test(value), `Header ${name} value ${value} does not match ${pattern}`);
});

Then("the stream response body length should be {int}", function (len: number) {
  assert.strictEqual(streamResponse.body.length, len);
});


