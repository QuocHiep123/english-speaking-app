import { XCircle, CheckCircle2, CheckCheck } from "lucide-react";

interface TranscriptComparisonProps {
  rawTranscript: string;
  correctedText: string | null;
}

export function TranscriptComparison({
  rawTranscript,
  correctedText,
}: TranscriptComparisonProps) {
  const isIdentical =
    correctedText !== null &&
    rawTranscript.trim().toLowerCase() === correctedText.trim().toLowerCase();

  return (
    <div className="rounded-2xl bg-white p-8 shadow-sm transition-shadow hover:shadow-md">
      <h3 className="mb-6 text-center text-lg font-bold tracking-tight text-slate-800">
        Transcript Comparison
      </h3>

      {/* No corrections needed */}
      {isIdentical ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-5">
          <div className="mb-3 flex items-center gap-2">
            <CheckCheck className="h-5 w-5 text-emerald-500" />
            <span className="text-xs font-bold uppercase tracking-widest text-emerald-600">
              Your Transcript
            </span>
            <span className="ml-auto rounded-full bg-emerald-100 px-3 py-0.5 text-[11px] font-semibold text-emerald-700">
              No corrections needed ✓
            </span>
          </div>
          <p className="leading-relaxed text-emerald-900">{rawTranscript}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {/* What you said */}
          <div className="rounded-xl border border-red-200 bg-red-50/70 p-5">
            <div className="mb-3 flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-500" />
              <span className="text-xs font-bold uppercase tracking-widest text-red-600">
                What You Said
              </span>
            </div>
            <p className="leading-relaxed text-red-900">
              {rawTranscript || (
                <span className="italic text-red-300">No transcript yet.</span>
              )}
            </p>
          </div>

          {/* What you meant */}
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-5">
            <div className="mb-3 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span className="text-xs font-bold uppercase tracking-widest text-emerald-600">
                Corrected Version
              </span>
            </div>
            <p className="leading-relaxed text-emerald-900">
              {correctedText ?? (
                <span className="italic text-emerald-300">Not available</span>
              )}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
