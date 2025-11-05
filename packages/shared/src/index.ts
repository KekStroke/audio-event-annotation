export type AudioFile = {
  id: string;
  filename: string;
  durationSec: number;
  sampleRate?: number;
  channels?: number;
  sizeBytes: number;
  path?: string;
};

export type Annotation = {
  id: string;
  audioId: string;
  startSec: number;
  endSec: number;
  labelId?: string;
  confidence?: number;
  notes?: string;
};

export type Label = {
  id: string;
  name: string;
  color: string;
};

export const defaultLabels: Label[] = [
  { id: "event", name: "Event", color: "#3b82f6" },
];
