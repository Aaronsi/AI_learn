/// Tauri Commands for RAFlow
///
/// Phase 3: Full system integration

use crate::audio::AudioCapture;
use crate::error::RAFlowError;
use crate::state::{AppState, RecordingState};
use crate::system::{InjectionMethod, InjectionResult, TextInjector};
use std::sync::Arc;
use tauri::{command, AppHandle, State};
use tauri_plugin_clipboard_manager::ClipboardExt;
use tokio::sync::Mutex;
use tracing::{error, info};

// Global text injector instance
lazy_static::lazy_static! {
    static ref TEXT_INJECTOR: Arc<Mutex<Option<TextInjector>>> = Arc::new(Mutex::new(None));
}

// ============================================================================
// Audio Commands
// ============================================================================

/// Start audio capture
#[command]
pub async fn start_audio_capture(
    state: State<'_, AppState>,
    app: AppHandle,
) -> Result<(), String> {
    info!("Command: start_audio_capture");

    // Set app handle for events
    state.audio_capture.set_app_handle(app).await;

    // Start audio capture
    match state.audio_capture.start().await {
        Ok(_) => {
            state.start_recording().await;
            info!("Audio capture started successfully");
            Ok(())
        }
        Err(e) => {
            error!("Failed to start audio capture: {}", e);
            state.set_recording_state(RecordingState::Error).await;
            Err(e.to_string())
        }
    }
}

/// Stop audio capture
#[command]
pub async fn stop_audio_capture(state: State<'_, AppState>) -> Result<(), String> {
    info!("Command: stop_audio_capture");

    match state.audio_capture.stop().await {
        Ok(_) => {
            state.stop_recording().await;
            // Don't auto-reset to idle - let frontend control state transition
            info!("Audio capture stopped successfully");
            Ok(())
        }
        Err(e) => {
            error!("Failed to stop audio capture: {}", e);
            Err(e.to_string())
        }
    }
}

// ============================================================================
// Text Injection Commands
// ============================================================================

/// Inject text to active application
#[command]
pub async fn inject_text(app: AppHandle, text: String) -> Result<InjectionResultDto, String> {
    info!("Command: inject_text - {} chars", text.len());

    // Initialize injector if not already done
    let mut injector_guard = TEXT_INJECTOR.lock().await;
    if injector_guard.is_none() {
        match TextInjector::new() {
            Ok(injector) => {
                *injector_guard = Some(injector);
            }
            Err(e) => {
                return Err(format!("Failed to initialize injector: {}", e));
            }
        }
    }

    let injector = injector_guard.as_mut().unwrap();

    // Try to inject
    match injector.inject(&text).await {
        Ok(result) => {
            // If clipboard method, actually write to clipboard
            if result.method == InjectionMethod::Clipboard {
                if let Err(e) = app.clipboard().write_text(&text) {
                    error!("Failed to write to clipboard: {}", e);
                    return Ok(InjectionResultDto {
                        success: false,
                        method: "clipboard".to_string(),
                        error: Some(format!("Clipboard write failed: {}", e)),
                    });
                }
            }

            Ok(InjectionResultDto {
                success: result.success,
                method: match result.method {
                    InjectionMethod::Direct => "direct".to_string(),
                    InjectionMethod::Clipboard => "clipboard".to_string(),
                },
                error: result.error,
            })
        }
        Err(e) => {
            error!("Injection failed: {}", e);
            Err(e.to_string())
        }
    }
}

// ============================================================================
// State Query Commands
// ============================================================================

/// Get current recording state
#[command]
pub async fn get_recording_state(state: State<'_, AppState>) -> Result<String, String> {
    let recording_state = state.get_recording_state().await;
    Ok(format!("{:?}", recording_state).to_lowercase())
}

// ============================================================================
// DTOs
// ============================================================================

#[derive(serde::Serialize)]
pub struct InjectionResultDto {
    pub success: bool,
    pub method: String,
    pub error: Option<String>,
}

