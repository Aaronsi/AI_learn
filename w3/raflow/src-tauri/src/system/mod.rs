/// System Module
///
/// Phase 3: Full system integration

pub mod hotkey;
pub mod injection;
pub mod tray;

pub use hotkey::{cleanup_global_shortcuts, setup_global_shortcuts, HotkeyConfig};
pub use injection::{InjectionMethod, InjectionResult, TextInjector};
pub use tray::setup_tray;
