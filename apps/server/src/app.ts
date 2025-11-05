import Fastify, {
  type FastifyInstance,
  type FastifyReply,
  type FastifyRequest,
} from "fastify";
import type { AudioFile } from "@audio/shared";

export type ServerDeps = {
  listFiles: () => Promise<
    Array<{ id: string; filename: string; path: string; sizeBytes: number }>
  >;
  readMetadata: (
    path: string
  ) => Promise<{ durationSec: number; sampleRate?: number; channels?: number }>;
};

export async function createServer(deps: ServerDeps): Promise<FastifyInstance> {
  const app = Fastify();

  app.get("/api/audio", async (_req: FastifyRequest, reply: FastifyReply) => {
    const files = await deps.listFiles();
    const results: AudioFile[] = [];
    for (const f of files) {
      const meta = await deps.readMetadata(f.path);
      results.push({
        id: f.id,
        filename: f.filename,
        durationSec: meta.durationSec,
        sampleRate: meta.sampleRate,
        channels: meta.channels,
        sizeBytes: f.sizeBytes,
        path: undefined,
      });
    }
    reply.send(results);
  });

  return app;
}
