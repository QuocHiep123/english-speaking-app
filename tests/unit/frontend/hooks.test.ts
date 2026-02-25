// =============================================================================
// Frontend Unit Tests - Custom Hooks
// =============================================================================

import { renderHook, act, waitFor } from '@testing-library/react';

// Mock MediaRecorder
const mockMediaRecorder = {
  start: jest.fn(),
  stop: jest.fn(),
  ondataavailable: null as ((event: any) => void) | null,
  onstop: null as (() => void) | null,
  stream: {
    getTracks: () => [{ stop: jest.fn() }],
  },
};

const mockGetUserMedia = jest.fn().mockResolvedValue({
  getTracks: () => [{ stop: jest.fn() }],
});

Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: mockGetUserMedia,
  },
  writable: true,
});

(global as any).MediaRecorder = jest.fn().mockImplementation(() => mockMediaRecorder);

describe('useAudioRecorder', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with correct default state', async () => {
    const { useAudioRecorder } = await import('@/hooks/useAudioRecorder');
    
    const { result } = renderHook(() => useAudioRecorder());
    
    expect(result.current.isRecording).toBe(false);
    expect(result.current.audioBlob).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('starts recording when startRecording is called', async () => {
    const { useAudioRecorder } = await import('@/hooks/useAudioRecorder');
    
    const { result } = renderHook(() => useAudioRecorder());
    
    await act(async () => {
      await result.current.startRecording();
    });
    
    expect(result.current.isRecording).toBe(true);
    expect(mockGetUserMedia).toHaveBeenCalledWith(
      expect.objectContaining({
        audio: expect.any(Object),
      })
    );
  });

  it('handles microphone permission denied', async () => {
    mockGetUserMedia.mockRejectedValueOnce(new Error('Permission denied'));
    
    const { useAudioRecorder } = await import('@/hooks/useAudioRecorder');
    
    const { result } = renderHook(() => useAudioRecorder());
    
    await act(async () => {
      await result.current.startRecording();
    });
    
    expect(result.current.isRecording).toBe(false);
    expect(result.current.error).toBeTruthy();
  });
});

describe('usePronunciationScore', () => {
  // Mock axios
  jest.mock('axios', () => ({
    create: () => ({
      post: jest.fn().mockResolvedValue({
        data: {
          score: { overall: 85, accuracy: 82, fluency: 88, completeness: 90 },
          feedback: { phonemes: [], suggestions: [], vietnameseInterference: [] },
        },
      }),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
    }),
  }));

  it('initializes with null score and feedback', async () => {
    const { usePronunciationScore } = await import('@/hooks/usePronunciationScore');
    
    const { result } = renderHook(() => usePronunciationScore());
    
    expect(result.current.score).toBeNull();
    expect(result.current.feedback).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('sets loading state during analysis', async () => {
    const { usePronunciationScore } = await import('@/hooks/usePronunciationScore');
    
    const { result } = renderHook(() => usePronunciationScore());
    
    const audioBlob = new Blob(['test'], { type: 'audio/webm' });
    
    // Note: This test would need proper async handling
    // and mock setup for the API call
  });
});

describe('API Client', () => {
  it('includes correct base URL', async () => {
    const { apiClient } = await import('@/lib/api');
    
    expect(apiClient.defaults.baseURL).toBeDefined();
  });

  it('sets timeout for audio processing', async () => {
    const { apiClient } = await import('@/lib/api');
    
    expect(apiClient.defaults.timeout).toBeGreaterThanOrEqual(30000);
  });
});
