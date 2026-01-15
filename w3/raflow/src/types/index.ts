/**
 * RAFlow Type Definitions
 *
 * This file contains all TypeScript type definitions for the RAFlow application.
 */

// ============================================================================
// Transcription Types
// ============================================================================

/**
 * Audio format for transcription
 */
export enum AudioFormat {
  PCM_16000 = 'pcm_16000',
  PCM_22050 = 'pcm_22050',
  PCM_24000 = 'pcm_24000',
  PCM_44100 = 'pcm_44100',
}

/**
 * Commit strategy for transcription
 */
export enum CommitStrategy {
  /** Automatically commit based on Voice Activity Detection */
  VAD = 'vad',
  /** Manually commit via user action */
  MANUAL = 'manual',
}

/**
 * Transcription configuration
 */
export interface TranscriptionConfig {
  /** API token for ElevenLabs */
  token: string;
  /** Model ID to use */
  modelId: string;
  /** Audio format */
  audioFormat: AudioFormat;
  /** Language code (ISO 639) */
  languageCode?: string;
  /** Commit strategy */
  commitStrategy: CommitStrategy;
  /** VAD silence threshold in seconds */
  vadSilenceThreshold?: number;
}

/**
 * Partial transcript data
 */
export interface PartialTranscript {
  /** Transcribed text */
  text: string;
  /** Confidence score */
  confidence?: number;
  /** Timestamp */
  timestamp: number;
}

/**
 * Committed transcript data
 */
export interface CommittedTranscript {
  /** Final transcribed text */
  text: string;
  /** Word-level timestamps */
  words?: Array<{
    word: string;
    start: number;
    end: number;
  }>;
  /** Language detected */
  language?: string;
}

// ============================================================================
// Application State Types
// ============================================================================

/**
 * Recording state
 */
export enum RecordingState {
  IDLE = 'idle',
  RECORDING = 'recording',
  PROCESSING = 'processing',
  ERROR = 'error',
}

/**
 * Application configuration
 */
export interface AppConfig {
  elevenlabs: {
    apiKey: string;
    modelId: string;
    languageCode: string;
    commitStrategy: CommitStrategy;
    vadSilenceThreshold: number;
  };
  audio: {
    inputDevice: string;
    sampleRate: number;
    chunkDurationMs: number;
    noiseReduction: boolean;
  };
  injection: {
    strategy: 'auto' | 'clipboard';
    fallbackToClipboard: boolean;
    insertDelay: number;
  };
  hotkeys: {
    toggleRecording: string;
    manualCommit?: string;
  };
  ui: {
    showFloatingWindow: boolean;
    floatingWindowPosition: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
    theme: 'light' | 'dark' | 'auto';
  };
  postProcessing: {
    enableTermCorrection: boolean;
    enableCourseCorrection: boolean;
    customTerms: Record<string, string>;
  };
}

/**
 * Audio level data
 */
export interface AudioLevel {
  /** RMS level (0-1) */
  level: number;
  /** Timestamp */
  timestamp: number;
}

/**
 * Text injection result
 */
export interface InjectionResult {
  /** Whether injection was successful */
  success: boolean;
  /** Method used: 'direct' or 'clipboard' */
  method: 'direct' | 'clipboard';
  /** Error message if failed */
  error?: string;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * RAFlow error types
 */
export enum ErrorType {
  AUDIO_DEVICE = 'audio_device',
  WEBSOCKET_CONNECTION = 'websocket_connection',
  TRANSCRIPTION = 'transcription',
  PERMISSION = 'permission',
  INJECTION = 'injection',
  CONFIG = 'config',
}

/**
 * Error data
 */
export interface RAFlowError {
  /** Error type */
  type: ErrorType;
  /** Error message */
  message: string;
  /** Additional details */
  details?: unknown;
}

// ============================================================================
// Event Types
// ============================================================================

/**
 * Audio chunk event payload
 */
export interface AudioChunkPayload {
  /** Audio data as Uint8Array */
  data: Uint8Array;
  /** Sample rate */
  sampleRate: number;
  /** Number of channels */
  channels: number;
}

/**
 * Recording state change event payload
 */
export interface RecordingStatePayload {
  /** New state */
  state: RecordingState;
  /** Optional error */
  error?: RAFlowError;
}

// ============================================================================
// Tauri Command Types
// ============================================================================

/**
 * Get ElevenLabs token command result
 */
export type GetTokenResult = string;

/**
 * Start audio capture command result
 */
export type StartCaptureResult = void;

/**
 * Stop audio capture command result
 */
export type StopCaptureResult = void;

/**
 * Inject text command parameters
 */
export interface InjectTextParams {
  text: string;
}

/**
 * Inject text command result
 */
export type InjectTextResult = InjectionResult;

/**
 * Get config command result
 */
export type GetConfigResult = AppConfig;

/**
 * Save config command parameters
 */
export interface SaveConfigParams {
  config: Partial<AppConfig>;
}

/**
 * Save config command result
 */
export type SaveConfigResult = void;
