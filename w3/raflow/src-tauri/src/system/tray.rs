/// System Tray Management
///
/// Phase 3: System tray icon and menu

use tauri::{
    image::Image,
    menu::{Menu, MenuBuilder, MenuEvent, MenuItem, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, Manager, Runtime, Wry,
};
use tracing::{error, info};

/// Setup system tray
pub fn setup_tray(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    info!("Setting up system tray");

    // Build menu
    let menu = build_tray_menu(app)?;

    // Build tray icon
    let _tray = TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(handle_menu_event)
        .on_tray_icon_event(handle_tray_event)
        .build(app)?;

    info!("System tray created successfully");

    Ok(())
}

/// Build tray menu
fn build_tray_menu(app: &AppHandle) -> Result<Menu<Wry>, Box<dyn std::error::Error>> {
    let toggle_item = MenuItem::with_id(app, "toggle_recording", "开始录音", true, None::<&str>)?;

    let show_item = MenuItem::with_id(app, "show_window", "显示窗口", true, None::<&str>)?;

    let settings_item = MenuItem::with_id(app, "settings", "设置", true, None::<&str>)?;

    let separator = PredefinedMenuItem::separator(app)?;

    let about_item = MenuItem::with_id(app, "about", "关于 RAFlow", true, None::<&str>)?;

    let quit_item = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;

    let menu = MenuBuilder::new(app)
        .item(&toggle_item)
        .item(&separator)
        .item(&show_item)
        .item(&settings_item)
        .item(&separator)
        .item(&about_item)
        .item(&quit_item)
        .build()?;

    Ok(menu)
}

/// Handle menu events
fn handle_menu_event(app: &AppHandle, event: MenuEvent) {
    info!("Tray menu event: {:?}", event.id);

    match event.id.as_ref() {
        "toggle_recording" => {
            // Emit event to frontend
            if let Err(e) = app.emit("tray-toggle-recording", ()) {
                error!("Failed to emit tray event: {}", e);
            }
        }
        "show_window" => {
            if let Some(window) = app.get_webview_window("main") {
                if let Err(e) = window.show() {
                    error!("Failed to show window: {}", e);
                }
                if let Err(e) = window.set_focus() {
                    error!("Failed to focus window: {}", e);
                }
            }
        }
        "settings" => {
            // Show settings (can be implemented later)
            info!("Settings clicked (not implemented yet)");
        }
        "about" => {
            // Show about dialog
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
            }
        }
        "quit" => {
            info!("Quit requested from tray");
            app.exit(0);
        }
        _ => {
            info!("Unknown menu item: {:?}", event.id);
        }
    }
}

/// Handle tray icon events (clicks)
fn handle_tray_event(tray: &tauri::tray::TrayIcon<Wry>, event: TrayIconEvent) {
    match event {
        TrayIconEvent::Click {
            button,
            button_state,
            ..
        } => {
            if button == MouseButton::Left && button_state == MouseButtonState::Up {
                info!("Tray icon left-clicked");

                let app = tray.app_handle();

                // Toggle window visibility
                if let Some(window) = app.get_webview_window("main") {
                    match window.is_visible() {
                        Ok(true) => {
                            let _ = window.hide();
                        }
                        Ok(false) => {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                        Err(e) => {
                            error!("Failed to check window visibility: {}", e);
                        }
                    }
                }
            }
        }
        _ => {}
    }
}

/// Update tray menu item
pub fn update_tray_menu_recording_state(_app: &AppHandle, is_recording: bool) {
    // This would require keeping a reference to the menu items
    // For now, we'll rebuild the menu when needed
    info!("Recording state changed: {}", is_recording);
}
