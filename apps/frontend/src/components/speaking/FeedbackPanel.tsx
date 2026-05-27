import { Lightbulb, AlertTriangle } from "lucide-react";

interface FeedbackPanelProps {
  feedback: string | null;
  parseError?: string;
}

export function FeedbackPanel({ feedback, parseError }: FeedbackPanelProps) {
  return (
    <div className="space-y-4">
      {/* Parse error warning */}
      {parseError && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="mt-0.5 rounded-full bg-amber-100 p-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
            </div>
            <div>
              <h4 className="mb-1 text-sm font-bold uppercase tracking-wider text-amber-700">
                Processing Note
              </h4>
              <p className="text-sm leading-relaxed text-amber-800">{parseError}</p>
            </div>
          </div>
        </div>
      )}

      {/* Main feedback */}
      {feedback ? (
        <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-indigo-50 p-6 shadow-sm transition-shadow hover:shadow-md">
          <div className="flex items-start gap-4">
            <div className="mt-0.5 rounded-full bg-blue-100 p-2">
              <Lightbulb className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <h4 className="mb-2 text-sm font-bold uppercase tracking-wider text-blue-700">
                Examiner Feedback
              </h4>
              <p className="text-[15px] leading-relaxed text-slate-700 whitespace-pre-line">
                {feedback}
              </p>
            </div>
          </div>
        </div>
      ) : (
        !parseError && (
          <p className="text-center text-sm italic text-gray-400">
            No feedback available.
          </p>
        )
      )}
    </div>
  );
}
