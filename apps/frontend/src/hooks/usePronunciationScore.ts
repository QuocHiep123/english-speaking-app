"use client";

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api";

interface PronunciationScore {
  overall: number;
  accuracy: number;
  fluency: number;
  completeness: number;
}

interface PhonemeFeedback {
  phoneme: string;
  score: number;
  suggestion?: string;
}

interface PronunciationFeedback {
  phonemes: PhonemeFeedback[];
  suggestions: string[];
  vietnameseInterference?: string[];
}

interface UsePronunciationScoreReturn {
  score: PronunciationScore | null;
  feedback: PronunciationFeedback | null;
  isLoading: boolean;
  error: string | null;
  analyzeAudio: (audioBlob: Blob, referenceText: string) => Promise<void>;
}

export function usePronunciationScore(): UsePronunciationScoreReturn {
  const [score, setScore] = useState<PronunciationScore | null>(null);
  const [feedback, setFeedback] = useState<PronunciationFeedback | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeAudio = useCallback(async (audioBlob: Blob, referenceText: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      formData.append("reference_text", referenceText);

      const response = await apiClient.post("/pronunciation/analyze", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setScore(response.data.score);
      setFeedback(response.data.feedback);
    } catch (err) {
      setError("Không thể phân tích phát âm. Vui lòng thử lại.");
      console.error("Error analyzing pronunciation:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    score,
    feedback,
    isLoading,
    error,
    analyzeAudio,
  };
}
