"use client";

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api";
import type { AssessmentResponse } from "@/types";

interface UseIELTSAssessmentReturn {
  result: AssessmentResponse | null;
  isLoading: boolean;
  error: string | null;
  assessAudio: (audioBlob: Blob, promptId?: number) => Promise<void>;
  reset: () => void;
}

export function useIELTSAssessment(): UseIELTSAssessmentReturn {
  const [result, setResult] = useState<AssessmentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const assessAudio = useCallback(async (audioBlob: Blob, promptId?: number) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // Guard against empty / too-small recordings (likely silent)
      const MIN_AUDIO_BYTES = 1000;
      console.log(`[Assessment] Audio blob size: ${audioBlob.size} bytes`);
      if (audioBlob.size < MIN_AUDIO_BYTES) {
        setError(
          "Bản ghi âm quá ngắn hoặc trống. Vui lòng kiểm tra microphone và thử lại.",
        );
        setIsLoading(false);
        return;
      }

      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      if (promptId !== undefined) {
        formData.append("prompt_id", String(promptId));
      }

      const response = await apiClient.post<AssessmentResponse>(
        "/v1/assess_speaking",
        formData,
        {
          // Do NOT set Content-Type manually — axios auto-detects FormData
          // and adds the required multipart boundary. Setting it manually
          // strips the boundary and corrupts the upload.
          headers: { "Content-Type": undefined },
          timeout: 180_000, // LLM can be slow
        },
      );

      setResult(response.data);
    } catch (err: unknown) {
      let message = "Đánh giá thất bại. Vui lòng thử lại.";
      if (typeof err === "object" && err !== null && "response" in err) {
        const resp = (err as { response?: { data?: { detail?: string } } }).response;
        if (resp?.data?.detail) {
          message = resp.data.detail;
        }
      } else if (err instanceof Error) {
        message = err.message;
      }
      setError(message);
      console.error("IELTS assessment error:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, isLoading, error, assessAudio, reset };
}
