// RAFlow Library
// Phase 1: Basic infrastructure setup

mod audio;
mod commands;
mod error;
mod state;
mod system;

use anyhow::Result;
use tauri::Manager;

pub use error::{RAFlowError, Result as RAFlowResult};
pub use state::AppState;

const APP_PATH: &str = "raflow";

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() -> Result<()> {
    // Initialize application data directory
    let app_path = dirs::data_local_dir().unwrap().join(APP_PATH);
    if !app_path.exists() {
        std::fs::create_dir_all(&app_path)?;
    }

    // Note: Logging is initialized by tauri-plugin-log plugin
    // Do not initialize tracing_subscriber here to avoid conflicts

    // Create application state
    let state = AppState::new();

    tauri::Builder::default()
        // Plugins
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(
            tauri_plugin_log::Builder::new()
                .target(tauri_plugin_log::Target::new(
                    tauri_plugin_log::TargetKind::Stdout,
                ))
                .target(tauri_plugin_log::Target::new(
                    tauri_plugin_log::TargetKind::LogDir {
                        file_name: Some("raflow.log".to_string()),
                    },
                ))
                // Add Webview target so logs appear in browser console
                .target(tauri_plugin_log::Target::new(
                    tauri_plugin_log::TargetKind::Webview,
                ))
                .level(log::LevelFilter::Info)
                .build(),
        )
        // Commands
        .invoke_handler(tauri::generate_handler![
            commands::start_audio_capture,
            commands::stop_audio_capture,
            commands::inject_text,
            commands::get_recording_state,
        ])
        // Setup
        .setup(|app| {
            // Manage state
            app.manage(state);

            // Phase 3: Setup system tray and global shortcuts
            let app_handle = app.handle();

            // Setup system tray
            if let Err(e) = system::setup_tray(&app_handle) {
                tracing::error!("Failed to setup system tray: {}", e);
            }

            // Setup global shortcuts
            if let Err(e) = system::setup_global_shortcuts(&app_handle) {
                tracing::error!("Failed to setup global shortcuts: {}", e);
            }

            // Open devtools in debug mode
            #[cfg(debug_assertions)]
            {
                if let Some(window) = app.get_webview_window("main") {
                    window.open_devtools();
                    tracing::info!("DevTools opened for debugging");
                }
            }

            // Configure macOS activation policy for background mode
            #[cfg(target_os = "macos")]
            {
                use tauri::ActivationPolicy;
                if let Err(e) = app.set_activation_policy(ActivationPolicy::Accessory) {
                    tracing::error!("Failed to set activation policy: {}", e);
                }
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");

    Ok(())
}
