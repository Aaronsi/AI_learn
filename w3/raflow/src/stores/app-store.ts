/**
 * RAFlow Application Store
 *
 * Global state management using Zustand
 */

import { create } from 'zustand';
import {
  RecordingState,
  AppConfig,
  AudioLevel,
  RAFlowError,
  CommitStrategy,
  AudioFormat,
} from '../types';

// ============================================================================
// Store Interface
// ============================================================================

interface AppState {
  // Recording state
  recordingState: RecordingState;
  isRecording: boolean;

  // Transcription data
  partialText: string;
  finalText: string;

  // Audio data
  audioLevel: number;

  // Error state
  error: RAFlowError | null;

  // Configuration
  config: AppConfig;

  // Actions
  setRecordingState: (state: RecordingState) => void;
  startRecording: () => void;
  stopRecording: () => void;
  setPartialText: (text: string) => void;
  setFinalText: (text: string) => void;
  setAudioLevel: (level: number) => void;
  setError: (error: RAFlowError | null) => void;
  updateConfig: (config: Partial<AppConfig>) => void;
  reset: () => void;
}

// ============================================================================
// Default Configuration
// ============================================================================

const defaultConfig: AppConfig = {
  elevenlabs: {
    apiKey: '',
    modelId: 'scribe_v2_realtime',
    languageCode: 'zh',
    commitStrategy: CommitStrategy.VAD,
    vadSilenceThreshold: 1.5,
  },
  audio: {
    inputDevice: 'default',
    sampleRate: 16000,
    chunkDurationMs: 200,
    noiseReduction: false,
  },
  injection: {
    strategy: 'auto',
    fallbackToClipboard: true,
    insertDelay: 100,
  },
  hotkeys: {
    toggleRecording: 'CommandOrControl+Shift+Backslash',
  },
  ui: {
    showFloatingWindow: true,
    floatingWindowPosition: 'bottom-right',
    theme: 'auto',
  },
  postProcessing: {
    enableTermCorrection: true,
    enableCourseCorrection: true,
    customTerms: {
      'view cell': 'Vercel',
      'super base': 'Supabase',
      'react js': 'React.js',
      'type script': 'TypeScript',
      'next js': 'Next.js',
    },
  },
};

// ============================================================================
// Store Creation
// ============================================================================

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  recordingState: RecordingState.IDLE,
  isRecording: false,
  partialText: '',
  finalText: '',
  audioLevel: 0,
  error: null,
  config: defaultConfig,

  // Actions
  setRecordingState: (state: RecordingState) =>
    set({
      recordingState: state,
      isRecording: state === RecordingState.RECORDING,
    }),

  startRecording: () =>
    set({
      recordingState: RecordingState.RECORDING,
      isRecording: true,
      partialText: '',
      finalText: '',
      error: null,
    }),

  stopRecording: () =>
    set({
      recordingState: RecordingState.PROCESSING,
      isRecording: false,
    }),

  setPartialText: (text: string) =>
    set({ partialText: text }),

  setFinalText: (text: string) =>
    set({
      finalText: text,
      recordingState: RecordingState.IDLE,
    }),

  setAudioLevel: (level: number) =>
    set({ audioLevel: level }),

  setError: (error: RAFlowError | null) =>
    set({
      error,
      recordingState: error ? RecordingState.ERROR : RecordingState.IDLE,
    }),

  updateConfig: (config: Partial<AppConfig>) =>
    set((state) => ({
      config: { ...state.config, ...config },
    })),

  reset: () =>
    set({
      recordingState: RecordingState.IDLE,
      isRecording: false,
      partialText: '',
      finalText: '',
      audioLevel: 0,
      error: null,
    }),
}));

// ============================================================================
// Selectors
// ============================================================================

/**
 * Select recording state
 */
export const selectIsRecording = (state: AppState) => state.isRecording;

/**
 * Select partial text
 */
export const selectPartialText = (state: AppState) => state.partialText;

/**
 * Select final text
 */
export const selectFinalText = (state: AppState) => state.finalText;

/**
 * Select audio level
 */
export const selectAudioLevel = (state: AppState) => state.audioLevel;

/**
 * Select error
 */
export const selectError = (state: AppState) => state.error;

/**
 * Select config
 */
export const selectConfig = (state: AppState) => state.config;
