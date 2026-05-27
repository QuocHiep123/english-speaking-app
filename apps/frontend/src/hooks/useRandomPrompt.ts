"use client";

import { useState, useCallback, useEffect } from "react";
import { apiClient } from "@/lib/api";
import type { IELTSPrompt } from "@/types";

interface UseRandomPromptReturn {
  prompt: IELTSPrompt | null;
  isLoading: boolean;
  error: string | null;
  fetchNext: () => Promise<void>;
}

export function useRandomPrompt(): UseRandomPromptReturn {
  const [prompt, setPrompt] = useState<IELTSPrompt | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNext = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<IELTSPrompt>(
        "/v1/prompts/random",
      );
      setPrompt(response.data);
    } catch (err: unknown) {
      let message = "Không thể tải câu hỏi. Vui lòng thử lại.";
      if (typeof err === "object" && err !== null && "response" in err) {
        const resp = (err as { response?: { data?: { detail?: string } } })
          .response;
        if (resp?.data?.detail) {
          message = resp.data.detail;
        }
      } else if (err instanceof Error) {
        message = err.message;
      }
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNext();
  }, [fetchNext]);

  return { prompt, isLoading, error, fetchNext };
}
