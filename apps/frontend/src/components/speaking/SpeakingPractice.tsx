"use client";

import { useCallback } from "react";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useIELTSAssessment } from "@/hooks/useIELTSAssessment";
import { useRandomPrompt } from "@/hooks/useRandomPrompt";
import { RecordButton } from "./RecordButton";
import { ScoreDisplay } from "./ScoreDisplay";
import { TranscriptComparison } from "./TranscriptComparison";
import { FeedbackPanel } from "./FeedbackPanel";
import { RefreshCw, Loader2 } from "lucide-react";

const PART_LABELS: Record<number, string> = {
  1: "Part 1 – Introduction & Interview",
  2: "Part 2 – Long Turn (Cue Card)",
  3: "Part 3 – Discussion",
};

export function SpeakingPractice() {
  const { isRecording, startRecording, stopRecording, error: micError } =
    useAudioRecorder();
  const { result, isLoading, error: assessError, assessAudio, reset } =
    useIELTSAssessment();
  const {
    prompt,
    isLoading: promptLoading,
    error: promptError,
    fetchNext,
  } = useRandomPrompt();

  const handleRecordToggle = useCallback(async () => {
    if (isRecording) {
      const blob = await stopRecording();
      if (blob) {
        assessAudio(blob, prompt?.id);
      }
    } else {
      reset();
      await startRecording();
    }
  }, [isRecording, startRecording, stopRecording, assessAudio, reset, prompt]);

  const error = micError || assessError || promptError;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-3xl space-y-8">
        {/* Prompt Card */}
        <div className="rounded-2xl bg-white p-8 text-center shadow-sm transition-shadow hover:shadow-md sm:p-10">
          {promptLoading ? (
            <div className="flex items-center justify-center gap-2 py-6 text-slate-400">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Đang tải câu hỏi…</span>
            </div>
          ) : prompt ? (
            <>
              <span className="mb-2 inline-block rounded-full bg-blue-100 px-4 py-1 text-xs font-bold uppercase tracking-widest text-blue-700">
                {PART_LABELS[prompt.part] ?? `Part ${prompt.part}`}
              </span>
              <p className="mb-4 text-xs text-slate-400">
                Topic:{" "}
                <span className="font-medium text-slate-600">{prompt.topic}</span>
              </p>
              <p className="mx-auto mb-6 max-w-2xl text-2xl font-medium leading-relaxed text-slate-800 sm:text-3xl">
                {prompt.question}
              </p>
              <button
                onClick={fetchNext}
                disabled={isRecording || isLoading}
                className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 transition-colors hover:text-blue-800 disabled:cursor-not-allowed disabled:text-slate-400"
              >
                <RefreshCw className="h-4 w-4" />
                Đổi câu hỏi
              </button>
            </>
          ) : (
            <p className="py-6 text-slate-500">
              Không tải được câu hỏi. Hãy nhấn &quot;Đổi câu hỏi&quot; để thử lại.
            </p>
          )}
        </div>

        {/* Record Button */}
        <div className="flex justify-center">
          <RecordButton
            isRecording={isRecording}
            isLoading={isLoading}
            onClick={handleRecordToggle}
          />
        </div>

        {/* Recording indicator */}
        {isRecording && (
          <p className="text-center text-sm font-medium text-red-500 animate-pulse">
            🎙️ Đang ghi âm…
          </p>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-center">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            <ScoreDisplay
              lexicalScore={result.evaluation.lexical_score}
              grammarScore={result.evaluation.grammar_score}
            />

            <TranscriptComparison
              rawTranscript={result.raw_transcript}
              correctedText={result.evaluation.corrected_text}
            />

            <FeedbackPanel
              feedback={result.evaluation.feedback}
              parseError={result.evaluation.llm_parse_error}
            />
          </div>
        )}
      </div>
    </div>
  );
}
