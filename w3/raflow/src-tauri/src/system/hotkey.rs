/// Global Hotkey Management
///
/// Phase 3: Cross-platform global shortcut registration

use tauri::{AppHandle, Emitter};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};
use tracing::{error, info, warn};

/// Hotkey configuration
pub struct HotkeyConfig {
    /// Main toggle recording shortcut
    pub toggle_recording: String,
}

impl Default for HotkeyConfig {
    fn default() -> Self {
        Self {
            #[cfg(target_os = "macos")]
            toggle_recording: "Command+Shift+Backslash".to_string(),
            #[cfg(not(target_os = "macos"))]
            toggle_recording: "Ctrl+Shift+Backslash".to_string(),
        }
    }
}

/// Setup global shortcuts
pub fn setup_global_shortcuts(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let config = HotkeyConfig::default();

    info!("Setting up global shortcuts");
    info!("Toggle recording: {}", config.toggle_recording);

    // Parse shortcut string
    let shortcut = config.toggle_recording.parse::<Shortcut>()
        .map_err(|e| format!("Failed to parse shortcut: {}", e))?;

    // Register the shortcut
    let app_handle = app.clone();

    app.global_shortcut().on_shortcut(shortcut, move |_app, _shortcut, event| {
        if event.state == ShortcutState::Pressed {
            info!("Hotkey pressed: toggle recording");

            // Emit event to frontend
            if let Err(e) = app_handle.emit("hotkey-toggle-recording", ()) {
                error!("Failed to emit hotkey event: {}", e);
            }
        }
    })?;

    // Actually register the shortcut
    app.global_shortcut().register(shortcut)?;

    info!("Global shortcuts registered successfully");

    Ok(())
}

/// Unregister all global shortcuts
pub fn cleanup_global_shortcuts(app: &AppHandle) {
    info!("Cleaning up global shortcuts");

    if let Err(e) = app.global_shortcut().unregister_all() {
        error!("Failed to unregister shortcuts: {}", e);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hotkey_config() {
        let config = HotkeyConfig::default();

        #[cfg(target_os = "macos")]
        assert!(config.toggle_recording.contains("Command"));

        #[cfg(not(target_os = "macos"))]
        assert!(config.toggle_recording.contains("Ctrl"));
    }
}
