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

// ---------------------------------------------------------------------------
// IELTS Speaking Assessment types
// ---------------------------------------------------------------------------

export interface IELTSPrompt {
  id: number;
  part: number;
  topic: string;
  question: string;
}

export interface IELTSEvaluation {
  corrected_text: string | null;
  lexical_score: number | null;
  grammar_score: number | null;
  feedback: string | null;
  llm_parse_error?: string;
  raw_llm_response?: string;
}

export interface AssessmentResponse {
  raw_transcript: string;
  evaluation: IELTSEvaluation;
  attempt_id: number | null;
}
