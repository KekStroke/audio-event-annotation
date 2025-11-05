import Fastify, {
  type FastifyInstance,
  type FastifyReply,
  type FastifyRequest,
} from "fastify";
import type { AudioFile } from "@audio/shared";
import { buildAudioList } from "./catalog";

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
    const results: AudioFile[] = await buildAudioList(files, deps.readMetadata);
    reply.send(results);
  });

  return app;
}
