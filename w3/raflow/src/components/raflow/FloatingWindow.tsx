/**
 * FloatingWindow Component
 *
 * Phase 2: Full integration with transcription service
 */

import React, { useEffect, useState } from 'react';
import {
  useAppStore,
  selectIsRecording,
  selectPartialText,
  selectAudioLevel,
  selectFinalText,
} from '../../stores/app-store';
import { transcriptionService } from '../../services/transcription';
import { textPostProcessor } from '../../services/post-processor';
import { RecordingState, CommitStrategy, AudioFormat } from '../../types';
import { AudioVisualizer } from './AudioVisualizer';
import { listen, isTauriEnvironment } from '../../utils/tauri';

export const FloatingWindow: React.FC = () => {
  const isRecording = useAppStore(selectIsRecording);
  const partialText = useAppStore(selectPartialText);
  const audioLevel = useAppStore(selectAudioLevel);
  const finalText = useAppStore(selectFinalText);
  const recordingState = useAppStore((state) => state.recordingState);

  const [error, setError] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState<string>('');
  const [showConfig, setShowConfig] = useState(false);

  // Listen for audio level events
  useEffect(() => {
    let unlistenFn: (() => void) | null = null;
    let mounted = true;

    async function setupListener() {
      try {
        // Check Tauri environment first
        if (!isTauriEnvironment()) {
          console.warn('⚠️ Not in Tauri environment, skipping audio level listener setup');
          console.warn('Please run the app using: cargo tauri dev');
          if (mounted) {
            setError('请在 Tauri 窗口中运行应用，而不是在浏览器中');
          }
          return;
        }

        // Setup listener - this will dynamically load Tauri APIs if needed
        unlistenFn = await listen<number>('audio-level', (event) => {
          if (mounted) {
            useAppStore.getState().setAudioLevel(event.payload);
          }
        });

        console.log('✅ Audio level listener registered');
      } catch (error) {
        console.error('Failed to setup audio level listener:', error);
        if (mounted) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          setError(`监听器设置失败: ${errorMessage}`);
        }
      }
    }

    setupListener();

    // Cleanup function must be synchronous
    return () => {
      mounted = false;
      if (unlistenFn) {
        unlistenFn();
      }
    };
  }, []);

  const getStatusColor = () => {
    switch (recordingState) {
      case RecordingState.RECORDING:
        return 'bg-red-500';
      case RecordingState.PROCESSING:
        return 'bg-blue-500';
      case RecordingState.ERROR:
        return 'bg-yellow-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = () => {
    switch (recordingState) {
      case RecordingState.RECORDING:
        return '录音中...';
      case RecordingState.PROCESSING:
        return '处理中...';
      case RecordingState.ERROR:
        return '错误';
      default:
        return '就绪';
    }
  };

  const handleStartRecording = async () => {
    if (!apiKey) {
      setError('请先配置 ElevenLabs API Key');
      setShowConfig(true);
      return;
    }

    try {
      setError(null);

      // ALWAYS ensure previous session is fully stopped before starting
      // This is critical to prevent "Audio capture already running" errors
      console.log('🔄 Ensuring previous session is stopped...');
      try {
        await transcriptionService.stop();
        // Wait a bit for cleanup
        await new Promise(resolve => setTimeout(resolve, 300));
      } catch (stopError) {
        console.warn('⚠️ Error stopping previous session (may be normal):', stopError);
      }

      // Reset state before starting
      useAppStore.getState().reset();
      useAppStore.getState().startRecording();

      await transcriptionService.start(
        {
          token: apiKey,
          modelId: 'scribe_v2_realtime',
          audioFormat: AudioFormat.PCM_16000,
          languageCode: 'zh',
          commitStrategy: CommitStrategy.VAD,
          vadSilenceThreshold: 1.5,
        },
        {
          onPartial: (transcript) => {
            useAppStore.getState().setPartialText(transcript.text);
          },
          onCommit: (transcript) => {
            console.log('✅ onCommit callback called with transcript:', transcript);
            // Transcript is already processed in the service
            // Just set it as final text (this will also set state to IDLE)
            useAppStore.getState().setFinalText(transcript.text);
            console.log('✅ Final text set in store, state should be IDLE now');

            // TODO: Inject text (Phase 3)
          },
          onError: (error) => {
            console.error('Transcription error:', error);
            const errorMessage = error instanceof Error ? error.message : String(error);
            setError(errorMessage);
            useAppStore.getState().setRecordingState(RecordingState.ERROR);
          },
        }
      );
    } catch (error) {
      console.error('Error starting recording:', error);
      const message = error instanceof Error ? error.message : String(error);
      setError(message || '启动录音失败，请检查配置和网络连接');
      useAppStore.getState().setRecordingState(RecordingState.ERROR);
    }
  };

  const handleStopRecording = async () => {
    try {
      setError(null);

      console.log('🛑 Stopping recording...');
      const partialTextBeforeStop = useAppStore.getState().partialText;
      console.log('📝 Partial text before stop:', partialTextBeforeStop);

      // Set to processing state
      useAppStore.getState().stopRecording();
      console.log('✅ State set to PROCESSING');

      // IMPORTANT: Try to commit current transcript before stopping
      // This ensures we get the final transcription result
      let finalTextReceived = false;

      // Check if WebSocket is still connected before trying to commit
      if (transcriptionService.isActive()) {
        try {
          console.log('📤 Attempting to commit transcript (WebSocket is active)...');
          await transcriptionService.commit();
          console.log('✅ Commit successful, final transcript received');

          // Check if final text was actually set
          await new Promise(resolve => setTimeout(resolve, 100));
          const finalTextAfterCommit = useAppStore.getState().finalText;
          if (finalTextAfterCommit) {
            console.log('✅ Final text confirmed:', finalTextAfterCommit);
            finalTextReceived = true;
          } else {
            console.warn('⚠️ Commit succeeded but no final text in store');
          }
        } catch (commitError) {
          console.warn('⚠️ Commit failed or timeout:', commitError);
        }
      } else {
        console.warn('⚠️ WebSocket not active, skipping commit');
      }

      // If commit didn't work, use partial text as fallback
      if (!finalTextReceived) {
        const partialText = useAppStore.getState().partialText;
        if (partialText && partialText.trim()) {
          console.log('📝 Using partial text as final text:', partialText);
          const processed = textPostProcessor.process(partialText, true, true);
          useAppStore.getState().setFinalText(processed);
          finalTextReceived = true;
        } else {
          console.warn('⚠️ No partial text available');
        }
      }

      // Stop transcription service (this will also stop audio capture)
      // Only stop after commit is processed or timeout
      console.log('🛑 Stopping transcription service...');
      await transcriptionService.stop();
      console.log('✅ Transcription service stopped');

      // Final check: if we still don't have final text, reset to IDLE
      if (!finalTextReceived) {
        console.log('🔍 Final check: No final text received...');
        setTimeout(() => {
          const currentState = useAppStore.getState().recordingState;
          const currentFinalText = useAppStore.getState().finalText;
          const currentPartialText = useAppStore.getState().partialText;

          console.log('🔍 Final check state:', {
            state: currentState,
            finalText: currentFinalText,
            partialText: currentPartialText
          });

          if (!currentFinalText && currentState === RecordingState.PROCESSING) {
            if (currentPartialText && currentPartialText.trim()) {
              console.log('📝 Fallback: Using partial text as final text');
              const processed = textPostProcessor.process(currentPartialText, true, true);
              useAppStore.getState().setFinalText(processed);
            } else {
              console.warn('⚠️ No transcript available, resetting to IDLE');
              useAppStore.getState().reset();
            }
          }
        }, 500);
      }
    } catch (error) {
      console.error('❌ Error stopping recording:', error);
      const message = error instanceof Error ? error.message : String(error);
      setError(message);

      // Try to preserve partial text if available
      const partialText = useAppStore.getState().partialText;
      if (partialText && partialText.trim()) {
        console.log('📝 Error fallback: Using partial text as final text');
        const processed = textPostProcessor.process(partialText, true, true);
        useAppStore.getState().setFinalText(processed);
      } else {
        console.warn('⚠️ No partial text available, resetting state');
        useAppStore.getState().reset();
      }
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      await handleStopRecording();
    } else {
      await handleStartRecording();
    }
  };

  return (
    <div className="w-full h-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-4 flex flex-col min-h-0">
      {/* Status Indicator */}
      <div className="flex items-center justify-between mb-2 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${getStatusColor()} ${
              isRecording ? 'animate-pulse' : ''
            }`}
          />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
            {getStatusText()}
          </span>
        </div>

        <button
          onClick={() => setShowConfig(!showConfig)}
          className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          {showConfig ? '隐藏配置' : '配置'}
        </button>
      </div>

      {/* Configuration */}
      {showConfig && (
        <div className="mb-2 p-2 bg-gray-50 dark:bg-gray-800 rounded flex-shrink-0">
          <label className="text-xs text-gray-600 dark:text-gray-400 block mb-1">
            ElevenLabs API Key:
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk_..."
            className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            获取 API Key:{' '}
            <a
              href="https://elevenlabs.io"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:underline"
            >
              elevenlabs.io
            </a>
          </p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded max-h-24 overflow-y-auto flex-shrink-0">
          <p className="text-xs text-red-600 dark:text-red-400 break-words whitespace-pre-wrap">{error}</p>
        </div>
      )}

      {/* Audio Visualizer */}
      <div className="mb-2 flex-shrink-0">
        <AudioVisualizer level={audioLevel} isActive={isRecording} />
      </div>

      {/* Partial Text Preview - Scrollable area */}
      <div className="flex-1 overflow-y-auto mb-2 min-h-0">
        {finalText ? (
          <p className="text-sm text-gray-700 dark:text-gray-200 font-medium break-words whitespace-pre-wrap">
            {finalText}
          </p>
        ) : partialText ? (
          <p className="text-sm text-gray-600 dark:text-gray-300 opacity-75 break-words whitespace-pre-wrap">
            {partialText}
          </p>
        ) : (
          <p className="text-xs text-gray-400 dark:text-gray-500 italic">
            {isRecording ? '正在聆听...' : '点击按钮开始录音'}
          </p>
        )}
      </div>

      {/* Controls - Fixed at bottom */}
      <div className="pt-2 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
        <button
          onClick={toggleRecording}
          disabled={recordingState === RecordingState.PROCESSING}
          className={`w-full py-2 px-4 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
            isRecording
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          {isRecording ? '停止录音' : '开始录音'}
        </button>
      </div>

      {/* Phase Info */}
      <div className="mt-1 text-xs text-gray-400 text-center flex-shrink-0">
        Phase 2: 音频采集与转录完成 ✅
      </div>
    </div>
  );
};

