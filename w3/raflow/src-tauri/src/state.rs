/// Application State Management
///
/// Manages the global state of the RAFlow application

use crate::audio::AudioCapture;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::info;

// ============================================================================
// Recording State
// ============================================================================

/// Recording state
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum RecordingState {
    /// Not recording
    Idle,
    /// Currently recording
    Recording,
    /// Processing recorded audio
    Processing,
    /// Error state
    Error,
}

// ============================================================================
// Application State
// ============================================================================

/// Main application state
#[derive(Clone)]
pub struct AppState {
    /// Current recording state
    pub recording_state: Arc<Mutex<RecordingState>>,

    /// Whether audio capture is active
    pub is_capturing: Arc<Mutex<bool>>,

    /// Current audio level (0.0 - 1.0)
    pub audio_level: Arc<Mutex<f32>>,

    /// Audio capture instance
    pub audio_capture: Arc<AudioCapture>,
}

impl AppState {
    /// Create new application state
    pub fn new() -> Self {
        info!("Initializing RAFlow state");
        Self {
            recording_state: Arc::new(Mutex::new(RecordingState::Idle)),
            is_capturing: Arc::new(Mutex::new(false)),
            audio_level: Arc::new(Mutex::new(0.0)),
            audio_capture: Arc::new(AudioCapture::new()),
        }
    }

    /// Get current recording state
    pub async fn get_recording_state(&self) -> RecordingState {
        *self.recording_state.lock().await
    }

    /// Set recording state
    pub async fn set_recording_state(&self, state: RecordingState) {
        *self.recording_state.lock().await = state;
    }

    /// Check if currently recording
    pub async fn is_recording(&self) -> bool {
        *self.recording_state.lock().await == RecordingState::Recording
    }

    /// Start recording
    pub async fn start_recording(&self) {
        *self.recording_state.lock().await = RecordingState::Recording;
        *self.is_capturing.lock().await = true;
    }

    /// Stop recording
    pub async fn stop_recording(&self) {
        *self.recording_state.lock().await = RecordingState::Processing;
        *self.is_capturing.lock().await = false;
    }

    /// Reset to idle state
    pub async fn reset(&self) {
        *self.recording_state.lock().await = RecordingState::Idle;
        *self.is_capturing.lock().await = false;
        *self.audio_level.lock().await = 0.0;
    }

    /// Set audio level
    pub async fn set_audio_level(&self, level: f32) {
        *self.audio_level.lock().await = level.clamp(0.0, 1.0);
    }

    /// Get audio level
    pub async fn get_audio_level(&self) -> f32 {
        *self.audio_level.lock().await
    }
}

impl Default for AppState {
    fn default() -> Self {
        Self::new()
    }
}
