import type { AudioFile } from "@audio/shared";

export type FileEntry = { id: string; filename: string; path: string; sizeBytes: number };
export type Meta = { durationSec: number; sampleRate?: number; channels?: number };

export function mergeFileAndMeta(file: FileEntry, meta: Meta): AudioFile {
  return {
    id: file.id,
    filename: file.filename,
    durationSec: meta.durationSec,
    sampleRate: meta.sampleRate,
    channels: meta.channels,
    sizeBytes: file.sizeBytes,
    path: undefined
  };
}

export async function buildAudioList(
  files: FileEntry[],
  readMetadata: (path: string) => Promise<Meta>
): Promise<AudioFile[]> {
  const result: AudioFile[] = [];
  for (const f of files) {
    const meta = await readMetadata(f.path);
    result.push(mergeFileAndMeta(f, meta));
  }
  return result;
}


