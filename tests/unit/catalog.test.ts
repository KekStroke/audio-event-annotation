import { describe, it, expect } from "vitest";
import { mergeFileAndMeta, buildAudioList, type FileEntry } from "../../apps/server/src/catalog";

describe("catalog utils", () => {
  it("mergeFileAndMeta produces AudioFile", () => {
    const file: FileEntry = { id: "1", filename: "a.wav", path: "/a.wav", sizeBytes: 123 };
    const meta = { durationSec: 1.23, sampleRate: 48000, channels: 2 };
    const out = mergeFileAndMeta(file, meta);
    expect(out).toEqual({
      id: "1",
      filename: "a.wav",
      durationSec: 1.23,
      sampleRate: 48000,
      channels: 2,
      sizeBytes: 123,
      path: undefined
    });
  });

  it("buildAudioList merges list and metadata via async reader", async () => {
    const files: FileEntry[] = [
      { id: "1", filename: "a.wav", path: "/a.wav", sizeBytes: 10 },
      { id: "2", filename: "b.mp3", path: "/b.mp3", sizeBytes: 20 }
    ];
    const readMetadata = async (p: string) => ({ durationSec: p.endsWith("wav") ? 2 : 3 });
    const out = await buildAudioList(files, readMetadata as any);
    expect(out.map(x => x.durationSec)).toEqual([2, 3]);
  });
});


