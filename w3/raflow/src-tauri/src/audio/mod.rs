/// Audio Module
///
/// Phase 2: Full audio capture implementation with cpal
/// Phase 4: Optimized configuration

mod buffer;
mod capture;
mod config;
mod resampler;

pub use buffer::AudioBuffer;
pub use capture::AudioCapture;
pub use config::AudioConfig;
pub use resampler::AudioResampler;
