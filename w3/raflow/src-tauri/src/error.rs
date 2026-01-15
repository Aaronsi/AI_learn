/// RAFlow Error Types
///
/// Defines all error types for the RAFlow application

use serde::{Deserialize, Serialize};

// ============================================================================
// Error Types
// ============================================================================

/// Main error type for RAFlow
#[derive(Debug, thiserror::Error, Serialize, Deserialize)]
#[serde(tag = "type", content = "message")]
pub enum RAFlowError {
    /// Audio device error
    #[error("Audio device error: {0}")]
    AudioDevice(String),

    /// WebSocket connection error
    #[error("WebSocket connection failed: {0}")]
    WebSocketConnection(String),

    /// Transcription service error
    #[error("Transcription error: {0}")]
    Transcription(String),

    /// Permission error
    #[error("Permission denied: {0}")]
    Permission(String),

    /// Text injection error
    #[error("Text injection failed: {0}")]
    Injection(String),

    /// Configuration error
    #[error("Configuration error: {0}")]
    Config(String),

    /// IO error
    #[error("IO error: {0}")]
    Io(String),

    /// Other error
    #[error("{0}")]
    Other(String),
}

// ============================================================================
// Error Conversions
// ============================================================================

impl From<std::io::Error> for RAFlowError {
    fn from(err: std::io::Error) -> Self {
        RAFlowError::Io(err.to_string())
    }
}

impl From<serde_json::Error> for RAFlowError {
    fn from(err: serde_json::Error) -> Self {
        RAFlowError::Config(err.to_string())
    }
}

impl From<cpal::BuildStreamError> for RAFlowError {
    fn from(err: cpal::BuildStreamError) -> Self {
        RAFlowError::AudioDevice(err.to_string())
    }
}

impl From<cpal::PlayStreamError> for RAFlowError {
    fn from(err: cpal::PlayStreamError) -> Self {
        RAFlowError::AudioDevice(err.to_string())
    }
}

// ============================================================================
// Result Type
// ============================================================================

/// Type alias for Result with RAFlowError
pub type Result<T> = std::result::Result<T, RAFlowError>;

// ============================================================================
// Error Helper Functions
// ============================================================================

/// Create an audio device error
pub fn audio_device_error(msg: impl Into<String>) -> RAFlowError {
    RAFlowError::AudioDevice(msg.into())
}

/// Create a permission error
pub fn permission_error(msg: impl Into<String>) -> RAFlowError {
    RAFlowError::Permission(msg.into())
}

/// Create an injection error
pub fn injection_error(msg: impl Into<String>) -> RAFlowError {
    RAFlowError::Injection(msg.into())
}

/// Create a config error
pub fn config_error(msg: impl Into<String>) -> RAFlowError {
    RAFlowError::Config(msg.into())
}
