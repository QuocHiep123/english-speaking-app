import { Mic, Square, Loader2 } from "lucide-react";

interface RecordButtonProps {
  isRecording: boolean;
  isLoading: boolean;
  onClick: () => void;
}

export function RecordButton({ isRecording, isLoading, onClick }: RecordButtonProps) {
  if (isLoading) {
    return (
      <button
        disabled
        className="flex items-center gap-3 rounded-full bg-slate-300 px-10 py-5 text-base font-semibold text-slate-500 shadow-lg cursor-not-allowed"
      >
        <Loader2 className="w-6 h-6 animate-spin" />
        <span>AI đang chấm điểm…</span>
      </button>
    );
  }

  if (isRecording) {
    return (
      <div className="relative inline-flex items-center justify-center">
        {/* Pulsing rings */}
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-40" />
        <span className="absolute inline-flex h-[calc(100%+16px)] w-[calc(100%+16px)] animate-pulse rounded-full bg-red-300 opacity-20" />
        <button
          onClick={onClick}
          className="relative z-10 flex items-center gap-3 rounded-full bg-red-500 px-10 py-5 text-base font-semibold text-white shadow-xl transition-all hover:bg-red-600 hover:shadow-2xl active:scale-95"
        >
          <Square className="w-6 h-6" />
          <span>Dừng &amp; Chấm điểm</span>
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 px-10 py-5 text-base font-semibold text-white shadow-lg transition-all hover:from-blue-700 hover:to-indigo-700 hover:shadow-xl active:scale-95"
    >
      <Mic className="w-6 h-6" />
      <span>Bắt đầu nói</span>
    </button>
  );
}
