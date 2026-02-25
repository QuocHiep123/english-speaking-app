// Pronunciation types
export interface PronunciationScore {
  overall: number;
  accuracy: number;
  fluency: number;
  completeness: number;
}

export interface PhonemeAnalysis {
  phoneme: string;
  score: number;
  expected: string;
  actual: string;
  suggestion?: string;
}

export interface PronunciationFeedback {
  phonemes: PhonemeAnalysis[];
  suggestions: string[];
  vietnameseInterference?: string[];
}

export interface PronunciationResult {
  score: PronunciationScore;
  feedback: PronunciationFeedback;
  transcription: string;
  audioUrl?: string;
}

// API types
export interface AnalyzeRequest {
  audio: Blob;
  referenceText: string;
}

export interface AnalyzeResponse {
  success: boolean;
  data: PronunciationResult;
  error?: string;
}
