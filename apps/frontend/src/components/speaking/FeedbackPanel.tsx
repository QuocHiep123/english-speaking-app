interface PhonemeFeedback {
  phoneme: string;
  score: number;
  suggestion?: string;
}

interface FeedbackPanelProps {
  feedback: {
    phonemes: PhonemeFeedback[];
    suggestions: string[];
    vietnameseInterference?: string[];
  };
}

export function FeedbackPanel({ feedback }: FeedbackPanelProps) {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
      <h3 className="text-lg font-semibold text-gray-800">Góp ý chi tiết</h3>

      {/* Phoneme-level feedback */}
      {feedback.phonemes.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-2">
            Phân tích âm vị
          </h4>
          <div className="flex flex-wrap gap-2">
            {feedback.phonemes.map((p, idx) => (
              <span
                key={idx}
                className={`px-2 py-1 rounded text-sm ${
                  p.score >= 80
                    ? "bg-green-100 text-green-700"
                    : p.score >= 60
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-red-100 text-red-700"
                }`}
                title={p.suggestion}
              >
                {p.phoneme}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Vietnamese interference notes */}
      {feedback.vietnameseInterference && feedback.vietnameseInterference.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-2">
            🇻🇳 Lưu ý cho người Việt
          </h4>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
            {feedback.vietnameseInterference.map((note, idx) => (
              <li key={idx}>{note}</li>
            ))}
          </ul>
        </div>
      )}

      {/* General suggestions */}
      {feedback.suggestions.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-2">
            💡 Gợi ý cải thiện
          </h4>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
            {feedback.suggestions.map((suggestion, idx) => (
              <li key={idx}>{suggestion}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
