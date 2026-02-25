import { Mic } from "lucide-react";

interface RecordButtonProps {
  isRecording: boolean;
  isLoading: boolean;
  onClick: () => void;
}

export function RecordButton({ isRecording, isLoading, onClick }: RecordButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className={`recorder-button ${isRecording ? "recording" : ""}`}
      aria-label={isRecording ? "Stop recording" : "Start recording"}
    >
      <Mic className="w-8 h-8 text-white" />
    </button>
  );
}
