// =============================================================================
// Frontend Unit Tests - SpeakingPractice Component
// =============================================================================

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the hooks
jest.mock('@/hooks/useAudioRecorder', () => ({
  useAudioRecorder: () => ({
    isRecording: false,
    audioBlob: null,
    startRecording: jest.fn(),
    stopRecording: jest.fn().mockResolvedValue(new Blob()),
    error: null,
  }),
}));

jest.mock('@/hooks/usePronunciationScore', () => ({
  usePronunciationScore: () => ({
    score: null,
    feedback: null,
    isLoading: false,
    error: null,
    analyzeAudio: jest.fn(),
  }),
}));

// Import component after mocks
import { SpeakingPractice } from '@/components/speaking/SpeakingPractice';

describe('SpeakingPractice', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <SpeakingPractice />
      </QueryClientProvider>
    );
  };

  it('renders the practice phrase', () => {
    renderComponent();
    
    expect(screen.getByText(/Hello, how are you\?/i)).toBeInTheDocument();
  });

  it('renders the record button', () => {
    renderComponent();
    
    expect(screen.getByRole('button', { name: /start recording/i })).toBeInTheDocument();
  });

  it('renders phrase selector buttons', () => {
    renderComponent();
    
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('changes phrase when selector is clicked', () => {
    renderComponent();
    
    fireEvent.click(screen.getByText('2'));
    
    expect(screen.getByText(/Nice to meet you/i)).toBeInTheDocument();
  });
});

describe('ScoreDisplay', () => {
  it('renders score values correctly', () => {
    const { ScoreDisplay } = require('@/components/speaking/ScoreDisplay');
    
    render(
      <ScoreDisplay
        score={{
          overall: 85,
          accuracy: 82,
          fluency: 88,
          completeness: 90,
        }}
      />
    );
    
    expect(screen.getByText('85')).toBeInTheDocument();
    expect(screen.getByText('82')).toBeInTheDocument();
    expect(screen.getByText('88')).toBeInTheDocument();
    expect(screen.getByText('90')).toBeInTheDocument();
  });

  it('applies correct color classes based on score', () => {
    const { ScoreDisplay } = require('@/components/speaking/ScoreDisplay');
    
    const { container } = render(
      <ScoreDisplay
        score={{
          overall: 95,
          accuracy: 75,
          fluency: 55,
          completeness: 40,
        }}
      />
    );
    
    // Excellent (95) should have green class
    expect(container.querySelector('.score-excellent')).toBeInTheDocument();
    // Good (75) should have blue class
    expect(container.querySelector('.score-good')).toBeInTheDocument();
    // Fair (55) should have yellow class
    expect(container.querySelector('.score-fair')).toBeInTheDocument();
    // Poor (40) should have red class
    expect(container.querySelector('.score-poor')).toBeInTheDocument();
  });
});

describe('FeedbackPanel', () => {
  it('renders phoneme feedback', () => {
    const { FeedbackPanel } = require('@/components/speaking/FeedbackPanel');
    
    render(
      <FeedbackPanel
        feedback={{
          phonemes: [
            { phoneme: 'θ', score: 65 },
            { phoneme: 'r', score: 85 },
          ],
          suggestions: [],
          vietnameseInterference: [],
        }}
      />
    );
    
    expect(screen.getByText('θ')).toBeInTheDocument();
    expect(screen.getByText('r')).toBeInTheDocument();
  });

  it('renders Vietnamese interference notes', () => {
    const { FeedbackPanel } = require('@/components/speaking/FeedbackPanel');
    
    render(
      <FeedbackPanel
        feedback={{
          phonemes: [],
          suggestions: [],
          vietnameseInterference: [
            "The 'th' sound tip for Vietnamese speakers",
          ],
        }}
      />
    );
    
    expect(screen.getByText(/th.*sound/i)).toBeInTheDocument();
  });

  it('renders improvement suggestions', () => {
    const { FeedbackPanel } = require('@/components/speaking/FeedbackPanel');
    
    render(
      <FeedbackPanel
        feedback={{
          phonemes: [],
          suggestions: ['Practice more slowly'],
          vietnameseInterference: [],
        }}
      />
    );
    
    expect(screen.getByText(/Practice more slowly/i)).toBeInTheDocument();
  });
});

describe('RecordButton', () => {
  it('shows correct state when not recording', () => {
    const { RecordButton } = require('@/components/speaking/RecordButton');
    
    render(
      <RecordButton
        isRecording={false}
        isLoading={false}
        onClick={jest.fn()}
      />
    );
    
    expect(screen.getByRole('button')).not.toHaveClass('recording');
  });

  it('shows recording state when recording', () => {
    const { RecordButton } = require('@/components/speaking/RecordButton');
    
    render(
      <RecordButton
        isRecording={true}
        isLoading={false}
        onClick={jest.fn()}
      />
    );
    
    expect(screen.getByRole('button')).toHaveClass('recording');
  });

  it('is disabled when loading', () => {
    const { RecordButton } = require('@/components/speaking/RecordButton');
    
    render(
      <RecordButton
        isRecording={false}
        isLoading={true}
        onClick={jest.fn()}
      />
    );
    
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('calls onClick when clicked', () => {
    const { RecordButton } = require('@/components/speaking/RecordButton');
    const handleClick = jest.fn();
    
    render(
      <RecordButton
        isRecording={false}
        isLoading={false}
        onClick={handleClick}
      />
    );
    
    fireEvent.click(screen.getByRole('button'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
