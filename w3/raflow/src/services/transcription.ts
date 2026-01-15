/**
 * Transcription Service
 *
 * Phase 2: Full implementation with ElevenLabs Scribe v2
 * Manages WebSocket connection and real-time transcription
 */

import {
  TranscriptionConfig,
  PartialTranscript,
  CommittedTranscript,
  AudioChunkPayload,
} from '../types';
import { textPostProcessor } from './post-processor';
import { ReconnectionStrategy, ConnectionHealthMonitor } from './reconnection';
import { performanceMonitor } from './performance';
import { invoke, listen } from '../utils/tauri';

// Note: @elevenlabs/client SDK is designed for Node.js
// For browser/Tauri, we'll use WebSocket API directly

// ============================================================================
// Service Interface
// ============================================================================

export interface TranscriptionCallbacks {
  onPartial: (transcript: PartialTranscript) => void;
  onCommit: (transcript: CommittedTranscript) => void;
  onError: (error: Error) => void;
}

// ============================================================================
// Transcription Service Class
// ============================================================================

export class TranscriptionService {
  private ws: WebSocket | null = null;
  private isConnected = false;
  private callbacks: TranscriptionCallbacks | null = null;
  private audioChunkUnlisten: (() => void) | null = null;
  private audioLevelUnlisten: (() => void) | null = null;
  private enablePostProcessing = true;
  private config: TranscriptionConfig | null = null;
  private reconnectionStrategy: ReconnectionStrategy;
  private healthMonitor: ConnectionHealthMonitor;

  constructor() {
    this.reconnectionStrategy = new ReconnectionStrategy({
      enabled: true,
      initialDelay: 1000,
      maxDelay: 30000,
      maxAttempts: 5,
    });

    this.healthMonitor = new ConnectionHealthMonitor(5000, 10000, 3);
  }

  /**
   * Initialize and start transcription
   */
  async start(
    config: TranscriptionConfig,
    callbacks: TranscriptionCallbacks
  ): Promise<void> {
    if (this.isConnected) {
      throw new Error('Transcription service already started');
    }

    this.callbacks = callbacks;
    this.config = config;

    try {
      console.log('Starting transcription service...');

      // Start performance monitoring
      performanceMonitor.start();

      // IMPORTANT: Set up event listeners FIRST before starting audio capture
      // This ensures we don't miss any audio chunks
      console.log('Setting up event listeners...');

      // Listen for audio chunks from Rust (Tauri v2 - direct import)
      this.audioChunkUnlisten = await listen<AudioChunkPayload>(
        'audio-chunk',
        (event) => {
          console.log('📡 Received audio-chunk event from Rust!');
          this.handleAudioChunk(event.payload);
        }
      );

      // Listen for audio level updates
      this.audioLevelUnlisten = await listen<number>('audio-level', (event) => {
        // This is handled by the app store
        console.debug('Audio level:', event.payload);
      });

      console.log('Event listeners registered');

      // Connect to ElevenLabs WebSocket
      console.log('Connecting to ElevenLabs WebSocket...');
      await this.connectWebSocket(config);

      // Start audio capture in Rust backend (LAST)
      // This ensures WebSocket is connected and listeners are ready
      console.log('Starting audio capture...');
      await invoke('start_audio_capture');

      console.log('Transcription service started successfully');
    } catch (error) {
      console.error('Failed to start transcription service:', error);
      this.callbacks?.onError(error as Error);
      throw error;
    }
  }

  /**
   * Generate single-use token from API key
   * ElevenLabs requires a single-use token for WebSocket auth, not the API key directly
   * Token expires after 15 minutes
   */
  private async generateSingleUseToken(apiKey: string): Promise<string> {
    console.log('🔑 Generating single-use token from API key...');
    console.log('🔑 API Key prefix:', apiKey.substring(0, 8) + '...');

    try {
      // Use the correct endpoint: POST /v1/single-use-token/realtime_scribe
      const url = 'https://api.elevenlabs.io/v1/single-use-token/realtime_scribe';
      console.log('🌐 Token endpoint:', url);

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'xi-api-key': apiKey,
          'Content-Type': 'application/json',
        },
      });

      console.log('📡 Token response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Failed to generate token:', response.status, errorText);

        // Provide user-friendly error messages based on status code
        if (response.status === 401) {
          throw new Error('API Key 无效或已过期。请检查您的 ElevenLabs API Key 是否正确。');
        } else if (response.status === 403) {
          throw new Error('API Key 权限不足。请确保您的 ElevenLabs 账户已启用 Speech-to-Text 功能。');
        } else if (response.status === 404) {
          throw new Error('Token 端点不存在。ElevenLabs API 可能已更新。');
        } else if (response.status === 429) {
          throw new Error('请求过于频繁，请稍后再试。');
        } else {
          throw new Error(`生成认证令牌失败 (${response.status}): ${errorText}`);
        }
      }

      const data = await response.json();
      console.log('📦 Token response data keys:', Object.keys(data));

      // Check for token in different possible field names
      const token = data.token || data.access_token || data.jwt;

      if (!token) {
        console.error('❌ No token found in response:', JSON.stringify(data));
        throw new Error('服务器返回的响应中没有 token 字段');
      }

      console.log('✅ Single-use token generated successfully');
      console.log('🔑 Token length:', token.length);
      console.log('🔑 Token preview:', token.substring(0, 20) + '...');

      return token;
    } catch (error) {
      console.error('❌ Token generation error:', error);
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('网络连接失败。请检查您的网络连接。');
      }
      throw error;
    }
  }

  /**
   * Connect to ElevenLabs WebSocket
   */
  private async connectWebSocket(config: TranscriptionConfig): Promise<void> {
    // First, generate a single-use token from the API key
    // ElevenLabs requires a single-use token for WebSocket auth, not the API key directly
    console.log('🔑 Step 1: Generating single-use token...');
    const singleUseToken = await this.generateSingleUseToken(config.token);
    console.log('✅ Step 1 complete: Token generated (length:', singleUseToken?.length, ')');

    const params = new URLSearchParams({
      model_id: config.modelId || 'scribe_v2_realtime',
      audio_format: config.audioFormat || 'pcm_16000',
    });

    if (config.languageCode) {
      params.append('language_code', config.languageCode);
    }

    if (config.commitStrategy) {
      params.append('commit_strategy', config.commitStrategy);
    }

    if (config.vadSilenceThreshold) {
      params.append(
        'vad_silence_threshold',
        config.vadSilenceThreshold.toString()
      );
    }

    // Use the single-use token, not the API key
    const wsUrl = `wss://api.elevenlabs.io/v1/speech-to-text/realtime?${params}&token=${singleUseToken}`;
    console.log('🔌 Step 2: Connecting to WebSocket...');
    console.log('📋 WebSocket URL params:', params.toString());

    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ Step 2 complete: WebSocket connected successfully!');
        this.isConnected = true;
        this.reconnectionStrategy.reset();

        // Start health monitoring
        // Note: ElevenLabs Scribe v2 doesn't have a custom ping message type
        // We use session_started response as health indicator instead
        this.healthMonitor.start(
          async () => {
            // Don't send custom ping messages - ElevenLabs doesn't support it
            // The connection health is monitored via successful message exchanges
            // Just check if WebSocket is still open
            if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
              console.warn('WebSocket not open, triggering health check failure');
              throw new Error('WebSocket not open');
            }
          },
          () => {
            // Connection unhealthy, attempt reconnection
            console.warn('Connection unhealthy, attempting reconnection');
            this.handleConnectionLoss();
          }
        );

        resolve();
      };

      this.ws.onmessage = (event) => {
        this.handleWebSocketMessage(event.data);
      };

      this.ws.onerror = (event) => {
        // WebSocket onerror provides an Event object, not an Error object
        // We need to create a meaningful error message
        console.error('WebSocket error event:', event);
        const errorMessage = 'WebSocket 连接失败。请检查：\n1. API Key 是否有效\n2. 网络连接是否正常\n3. ElevenLabs 服务是否可用';
        const error = new Error(errorMessage);
        this.callbacks?.onError(error);
        reject(error);
      };

      this.ws.onclose = (event) => {
        console.log(`❌ WebSocket closed: code=${event.code}, reason=${event.reason || '(no reason provided)'}, wasClean=${event.wasClean}`);
        this.isConnected = false;
        this.healthMonitor.stop();

        // Provide more context based on close code
        // Common WebSocket close codes:
        // 1000 - Normal closure
        // 1001 - Going away
        // 1006 - Abnormal closure (no close frame received)
        // 1008 - Policy violation
        // 1011 - Server error
        if (event.code === 1006) {
          console.error('⚠️ WebSocket closed abnormally (code 1006). This usually means the connection was rejected or failed.');
        } else if (event.code === 1008) {
          console.error('⚠️ WebSocket closed due to policy violation (code 1008). Check authentication.');
        }

        // Attempt reconnection if not a clean close
        if (!event.wasClean && this.config) {
          this.handleConnectionLoss();
        }
      };
    });
  }

  /**
   * Handle connection loss and attempt reconnection
   */
  private async handleConnectionLoss(): Promise<void> {
    if (!this.config) {
      console.error('Cannot reconnect: no configuration available');
      return;
    }

    console.log('Connection lost, attempting to reconnect...');

    // Record reconnection attempt
    performanceMonitor.recordReconnection();

    await this.reconnectionStrategy.scheduleReconnect(async () => {
      if (this.config) {
        await this.connectWebSocket(this.config);
      }
    });
  }

  /**
   * Handle WebSocket message
   * ElevenLabs Scribe v2 uses 'message_type' field (not 'type')
   */
  private handleWebSocketMessage(data: string): void {
    try {
      const message = JSON.parse(data);
      // ElevenLabs uses 'message_type' field
      const messageType = message.message_type || message.type;
      console.log('WebSocket message received:', messageType, message);

      if (messageType === 'partial_transcript') {
        const rawText = message.text || '';
        console.log('Partial transcript (raw):', rawText);
        // Apply post-processing to partial transcript
        const processedText = this.enablePostProcessing
          ? textPostProcessor.process(rawText)
          : rawText;

        // Record transcription latency
        if (message.timestamp) {
          const latency = Date.now() - message.timestamp;
          performanceMonitor.recordTranscriptionLatency(latency);
        }

        const partial: PartialTranscript = {
          text: processedText,
          confidence: message.confidence,
          timestamp: Date.now(),
        };
        this.callbacks?.onPartial(partial);
      } else if (
        messageType === 'final_transcript' ||
        messageType === 'committed_transcript' ||
        messageType === 'committed_transcript_with_timestamps'
      ) {
        // ElevenLabs Scribe v2 committed transcript messages
        const rawText = message.text || '';
        console.log('✅ Committed transcript received:', messageType);
        console.log('✅ Raw text:', rawText);
        console.log('✅ Full message:', JSON.stringify(message, null, 2));

        // Apply post-processing to committed transcript
        const processedText = this.enablePostProcessing
          ? textPostProcessor.process(rawText, true, true)
          : rawText;

        console.log('✅ Processed text:', processedText);

        // Record transcription latency
        if (message.timestamp) {
          const latency = Date.now() - message.timestamp;
          performanceMonitor.recordTranscriptionLatency(latency);
        }

        const committed: CommittedTranscript = {
          text: processedText,
          words: message.words,
          language: message.language || message.detected_language,
        };

        // Call callback if available
        if (this.callbacks?.onCommit) {
          console.log('✅ Calling onCommit callback with:', committed);
          this.callbacks.onCommit(committed);
        } else {
          console.warn('⚠️ No onCommit callback available, transcript lost:', committed);
        }
      } else if (messageType === 'session_started') {
        console.log('✅ ElevenLabs session started!');
        console.log('📋 Session ID:', message.session_id);
        console.log('📋 Config:', JSON.stringify(message.config, null, 2));
        // Health monitor - record successful connection
        this.healthMonitor.recordPong();
      } else if (messageType === 'commit_throttled') {
        // This happens when we try to commit but there's not enough audio
        // ElevenLabs requires at least 0.3s of uncommitted audio
        console.warn('⚠️ Commit throttled:', message.error);
        console.warn('📊 This usually means no audio was sent or audio was too short');
        // Don't treat this as a fatal error - it just means there's nothing to transcribe
      } else if (messageType === 'error' || messageType === 'auth_error' || messageType === 'quota_exceeded') {
        console.error('❌ ElevenLabs error:', messageType, message);
        const errorMsg = message.error || message.message || message.detail || `Unknown error: ${messageType}`;
        this.callbacks?.onError(new Error(errorMsg));
      } else {
        // Log all other message types for debugging
        console.log('📨 Other message type:', messageType);
        console.log('📨 Full message:', JSON.stringify(message, null, 2));
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error, 'Raw data:', data);
    }
  }

  /**
   * Handle audio chunk from backend
   */
  private handleAudioChunk(payload: AudioChunkPayload): void {
    console.log('🎵 handleAudioChunk called! Payload size:', payload?.data?.length || 0);

    if (!this.ws) {
      console.warn('⚠️ WebSocket is null, dropping audio chunk');
      return;
    }

    if (this.ws.readyState !== WebSocket.OPEN) {
      console.warn('⚠️ WebSocket not ready, dropping audio chunk. State:', this.ws.readyState, '(OPEN=1)');
      return;
    }

    try {
      // Convert payload.data (array of numbers) to Uint8Array
      const audioData = new Uint8Array(payload.data);
      console.log('🎵 Audio data Uint8Array length:', audioData.length);

      // Convert to base64 - ElevenLabs requires base64-encoded audio in JSON
      // Use chunk approach to avoid call stack issues with large arrays
      let binaryString = '';
      const chunkSize = 8192;
      for (let i = 0; i < audioData.length; i += chunkSize) {
        const chunk = audioData.slice(i, Math.min(i + chunkSize, audioData.length));
        binaryString += String.fromCharCode.apply(null, Array.from(chunk));
      }
      const base64Audio = btoa(binaryString);

      // Send as JSON with message_type and audio_base_64 fields (as per ElevenLabs Scribe v2 API docs)
      // IMPORTANT: message_type: "input_audio_chunk" is REQUIRED
      // See: https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime
      const message = JSON.stringify({
        message_type: 'input_audio_chunk',
        audio_base_64: base64Audio,
      });

      this.ws.send(message);

      // Record message sent
      performanceMonitor.recordMessage();

      console.log(`🎵 Sent audio chunk: ${audioData.length} bytes -> ${base64Audio.length} base64 chars`);
    } catch (error) {
      console.error('Error sending audio chunk:', error);
    }
  }

  /**
   * Stop transcription
   */
  async stop(): Promise<void> {
    console.log('🛑 Stopping transcription service...');

    try {
      // Stop health monitoring first
      this.healthMonitor.stop();
      this.reconnectionStrategy.cancelReconnect();

      // ALWAYS try to stop audio capture in Rust backend
      // This is critical - even if WebSocket is closed, audio capture might still be running
      try {
        console.log('🎤 Stopping audio capture...');
        await invoke('stop_audio_capture');
        console.log('✅ Audio capture stopped');
      } catch (audioError) {
        // Log but don't throw - audio might not be running
        console.warn('⚠️ Audio capture stop warning:', audioError);
      }

      // Wait a short time before closing WebSocket to allow final messages
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      // Close WebSocket connection if open
      if (this.ws) {
        if (this.ws.readyState === WebSocket.OPEN) {
          this.ws.close(1000, 'User requested stop');
        }
        this.ws = null;
      }
      this.isConnected = false;

      // Remove event listeners
      if (this.audioChunkUnlisten) {
        this.audioChunkUnlisten();
        this.audioChunkUnlisten = null;
      }
      if (this.audioLevelUnlisten) {
        this.audioLevelUnlisten();
        this.audioLevelUnlisten = null;
      }

      // Reset state
      this.callbacks = null;
      this.config = null;

      // Stop performance monitoring
      performanceMonitor.stop();

      console.log('✅ Transcription service stopped successfully');
    } catch (error) {
      console.error('❌ Error stopping transcription service:', error);
      // Don't throw - we want to ensure cleanup happens
      // throw error;
    }
  }

  /**
   * Manually commit the current transcript
   * Sends a commit message to force the API to return the current transcript
   * This works with both VAD and manual commit strategies
   */
  async commit(): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    if (!this.callbacks) {
      throw new Error('No callbacks registered');
    }

    // Send a commit message to force the API to return the current transcript
    // According to ElevenLabs API docs, we can send input_audio_chunk with commit: true
    // to force commit the current transcript segment
    console.log('📤 Sending commit message to force transcript commit...');

    try {
      // Send an empty audio chunk with commit: true to trigger transcript commit
      // This tells the API to commit whatever has been transcribed so far
      const commitMessage = JSON.stringify({
        message_type: 'input_audio_chunk',
        audio_base_64: '',  // Empty audio data
        commit: true,
      });

      this.ws.send(commitMessage);
      console.log('✅ Commit message sent');
    } catch (sendError) {
      console.error('❌ Failed to send commit message:', sendError);
      throw sendError;
    }

    // Store original onCommit callback BEFORE creating Promise
    const originalOnCommit = this.callbacks.onCommit;
    if (!originalOnCommit) {
      throw new Error('Original onCommit callback is not available');
    }

    // Wait for committed transcript with timeout
    return new Promise<void>((resolve, reject) => {
      let resolved = false;
      let timeoutId: NodeJS.Timeout | null = null;

      // Set up timeout - give more time since we're forcing commit
      timeoutId = setTimeout(() => {
        if (resolved) return;

        // Restore original callback before rejecting
        if (this.callbacks) {
          this.callbacks.onCommit = originalOnCommit;
        }
        console.warn('⏱️ Commit timeout: No committed transcript received within 5 seconds');
        reject(new Error('Commit timeout: No committed transcript received within 5 seconds'));
      }, 5000);

      // Override onCommit to resolve promise when transcript arrives
      this.callbacks.onCommit = (transcript) => {
        if (resolved) {
          // Already resolved, just call original callback
          originalOnCommit(transcript);
          return;
        }

        resolved = true;
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = null;
        }

        console.log('✅ Commit promise resolved with transcript:', transcript.text);

        // Call original callback first (this will update the UI)
        try {
          originalOnCommit(transcript);
        } catch (error) {
          console.error('Error in onCommit callback:', error);
        }

        // Restore original callback
        if (this.callbacks) {
          this.callbacks.onCommit = originalOnCommit;
        }

        // Then resolve promise
        resolve();
      };
    });
  }

  /**
   * Get connection status
   */
  isActive(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Enable or disable post-processing
   */
  setPostProcessing(enabled: boolean): void {
    this.enablePostProcessing = enabled;
  }

  /**
   * Add custom term mapping
   */
  addCustomTerm(wrong: string, correct: string): void {
    textPostProcessor.addTermMapping(wrong, correct);
  }

  /**
   * Remove custom term mapping
   */
  removeCustomTerm(wrong: string): void {
    textPostProcessor.removeTermMapping(wrong);
  }

  /**
   * Update multiple custom terms at once
   */
  updateCustomTerms(terms: Record<string, string>): void {
    textPostProcessor.updateCustomTerms(terms);
  }

  /**
   * Get all term mappings
   */
  getTermMappings(): Map<string, string> {
    return textPostProcessor.getTermMappings();
  }

  /**
   * Get current performance metrics
   */
  getPerformanceMetrics() {
    return performanceMonitor.getMetrics();
  }

  /**
   * Get performance snapshot with history
   */
  getPerformanceSnapshot() {
    return performanceMonitor.getSnapshot();
  }

  /**
   * Check if performance is healthy
   */
  isPerformanceHealthy(): boolean {
    return performanceMonitor.isHealthy();
  }

  /**
   * Get reconnection state
   */
  getReconnectionState() {
    return this.reconnectionStrategy.getState();
  }

  /**
   * Get connection health metrics
   */
  getHealthMetrics() {
    return this.healthMonitor.getMetrics();
  }
}

// ============================================================================
// Export singleton instance
// ============================================================================

export const transcriptionService = new TranscriptionService();





