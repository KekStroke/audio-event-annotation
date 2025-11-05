import type { AudioFile } from "@audio/shared";

// Placeholder to verify type import works across workspaces
const example: AudioFile = {
  id: "example",
  filename: "example.wav",
  durationSec: 0,
  sizeBytes: 0,
};

console.log("Server placeholder running with shared type:", example.id);
