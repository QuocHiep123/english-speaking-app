"use client";

import { useState, useCallback } from "react";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { usePronunciationScore } from "@/hooks/usePronunciationScore";
import { RecordButton } from "./RecordButton";
import { ScoreDisplay } from "./ScoreDisplay";
import { FeedbackPanel } from "./FeedbackPanel";

interface PracticePhrase {
  id: string;
  text: string;
  phonemes: string;
}

const SAMPLE_PHRASES: PracticePhrase[] = [
  { id: "1", text: "Hello, how are you?", phonemes: "həˈloʊ haʊ ɑːr juː" },
  { id: "2", text: "Nice to meet you.", phonemes: "naɪs tuː miːt juː" },
  { id: "3", text: "Thank you very much.", phonemes: "θæŋk juː ˈvɛri mʌtʃ" },
];

export function SpeakingPractice() {
  const [currentPhrase, setCurrentPhrase] = useState(SAMPLE_PHRASES[0]);
  const { isRecording, startRecording, stopRecording, audioBlob } = useAudioRecorder();
  const { score, feedback, isLoading, analyzeAudio } = usePronunciationScore();

  const handleRecordToggle = useCallback(async () => {
    if (isRecording) {
      const blob = await stopRecording();
      if (blob) {
        analyzeAudio(blob, currentPhrase.text);
      }
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording, currentPhrase, analyzeAudio]);

  return (
    <div className="space-y-8">
      {/* Phrase Display */}
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        <p className="text-sm text-gray-500 mb-2">Hãy đọc câu sau:</p>
        <p className="text-2xl font-medium text-gray-800">{currentPhrase.text}</p>
        <p className="text-sm text-gray-400 mt-2 font-mono">{currentPhrase.phonemes}</p>
      </div>

      {/* Record Button */}
      <div className="flex justify-center">
        <RecordButton
          isRecording={isRecording}
          isLoading={isLoading}
          onClick={handleRecordToggle}
        />
      </div>

      {/* Score Display */}
      {score && <ScoreDisplay score={score} />}

      {/* Feedback Panel */}
      {feedback && <FeedbackPanel feedback={feedback} />}

      {/* Phrase Selector */}
      <div className="flex justify-center gap-2">
        {SAMPLE_PHRASES.map((phrase) => (
          <button
            key={phrase.id}
            onClick={() => setCurrentPhrase(phrase)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              currentPhrase.id === phrase.id
                ? "bg-blue-500 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {phrase.id}
          </button>
        ))}
      </div>
    </div>
  );
}
