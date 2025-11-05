import Fastify, {
  type FastifyInstance,
  type FastifyReply,
  type FastifyRequest,
} from "fastify";
import type { AudioFile } from "@audio/shared";

type FileEntry = {
  id: string;
  filename: string;
  path: string;
  sizeBytes: number;
};
type Meta = { durationSec: number; sampleRate?: number; channels?: number };
function mergeFileAndMeta(file: FileEntry, meta: Meta): AudioFile {
  return {
    id: file.id,
    filename: file.filename,
    durationSec: meta.durationSec,
    sampleRate: meta.sampleRate,
    channels: meta.channels,
    sizeBytes: file.sizeBytes,
    path: undefined,
  };
}
async function buildAudioList(
  files: FileEntry[],
  readMetadata: (path: string) => Promise<Meta>
): Promise<AudioFile[]> {
  const result: AudioFile[] = [];
  for (const f of files) {
    try {
      const meta = await readMetadata(f.path);
      result.push(mergeFileAndMeta(f, meta));
    } catch {
      continue;
    }
  }
  return result;
}

export type ServerDeps = {
  listFiles: () => Promise<
    Array<{ id: string; filename: string; path: string; sizeBytes: number }>
  >;
  readMetadata: (
    path: string
  ) => Promise<{ durationSec: number; sampleRate?: number; channels?: number }>;
  openReadStream?: (
    id: string,
    start: number,
    end: number
  ) => Buffer | NodeJS.ReadableStream;
  statById?: (id: string) => { size: number };
};

export async function createServer(deps: ServerDeps): Promise<FastifyInstance> {
  const app = Fastify();

  app.get("/api/audio", async (_req: FastifyRequest, reply: FastifyReply) => {
    const files = await deps.listFiles();
    const results: AudioFile[] = await buildAudioList(files, deps.readMetadata);
    reply.send(results);
  });

  app.get(
    "/api/audio/:id/stream",
    async (
      req: FastifyRequest<{ Params: { id: string } }>,
      reply: FastifyReply
    ) => {
      try {
        if (!deps.statById || !deps.openReadStream) {
          reply
            .code(501)
            .send({ error: "Streaming not supported in this configuration" });
          return;
        }
        const id = req.params.id;
        const range = (req.headers["range"] as string | undefined) || "";
        if (!range) {
          reply.code(404).send({ error: "Not Found" });
          return;
        }
        const stat = deps.statById(id);
        const size = stat.size;
        const m = range.match(/bytes=(\d+)-(\d+)?/);
        if (!m) {
          reply.code(416).header("Content-Range", `bytes */${size}`).send();
          return;
        }
        let start = parseInt(m[1], 10);
        let end = m[2]
          ? parseInt(m[2], 10)
          : Math.min(start + 1024 * 1024 - 1, size - 1);
        if (isNaN(start) || isNaN(end) || start > end || start >= size) {
          reply.code(416).header("Content-Range", `bytes */${size}`).send();
          return;
        }
        end = Math.min(end, size - 1);
        const chunk = deps.openReadStream(id, start, end);
        reply
          .code(206)
          .header("Accept-Ranges", "bytes")
          .header("Content-Range", `bytes ${start}-${end}/${size}`)
          .header("Content-Length", String(end - start + 1))
          .send(chunk as any);
      } catch (err: any) {
        if (err && (err.code === "ENOENT" || err.message === "not found")) {
          reply.code(404).send({ error: "Not Found" });
          return;
        }
        console.error("Stream error:", err);
        reply.code(500).send({ error: "Internal Server Error", details: err.message });
      }
    }
  );

  return app;
}
