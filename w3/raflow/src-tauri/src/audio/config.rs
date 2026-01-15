/// Audio Configuration
///
/// Phase 4: Optimized audio buffer and performance settings

use serde::{Deserialize, Serialize};

/// Audio capture configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioConfig {
    /// Target sample rate for transcription (Hz)
    pub target_sample_rate: u32,

    /// Chunk duration in milliseconds
    /// Lower values = lower latency, higher CPU usage
    /// Higher values = higher latency, lower CPU usage
    /// Recommended: 100-200ms
    pub chunk_duration_ms: u32,

    /// Buffer capacity in seconds
    /// Recommended: 5-10 seconds
    pub buffer_capacity_secs: u32,

    /// Number of resampling threads
    /// More threads = better performance on multi-core
    /// Recommended: 1-2
    pub resampler_threads: usize,

    /// Enable audio level monitoring
    pub enable_level_monitoring: bool,

    /// Level monitoring interval in milliseconds
    pub level_monitoring_interval_ms: u32,
}

impl Default for AudioConfig {
    fn default() -> Self {
        Self {
            target_sample_rate: 16000,
            chunk_duration_ms: 100, // Optimized from 200ms to 100ms for lower latency
            buffer_capacity_secs: 8, // Reduced from 10s to 8s to save memory
            resampler_threads: 1,
            enable_level_monitoring: true,
            level_monitoring_interval_ms: 50,
        }
    }
}

impl AudioConfig {
    /// Create configuration optimized for low latency
    pub fn low_latency() -> Self {
        Self {
            target_sample_rate: 16000,
            chunk_duration_ms: 80,
            buffer_capacity_secs: 5,
            resampler_threads: 2,
            enable_level_monitoring: true,
            level_monitoring_interval_ms: 30,
        }
    }

    /// Create configuration optimized for low CPU usage
    pub fn low_cpu() -> Self {
        Self {
            target_sample_rate: 16000,
            chunk_duration_ms: 250,
            buffer_capacity_secs: 10,
            resampler_threads: 1,
            enable_level_monitoring: false,
            level_monitoring_interval_ms: 100,
        }
    }

    /// Create configuration balanced between latency and CPU
    pub fn balanced() -> Self {
        Self::default()
    }

    /// Get chunk size in samples
    pub fn chunk_size(&self) -> usize {
        (self.target_sample_rate * self.chunk_duration_ms / 1000) as usize
    }

    /// Get buffer capacity in samples
    pub fn buffer_capacity(&self) -> usize {
        (self.target_sample_rate * self.buffer_capacity_secs) as usize
    }

    /// Validate configuration
    pub fn validate(&self) -> Result<(), String> {
        if self.target_sample_rate < 8000 || self.target_sample_rate > 48000 {
            return Err("Target sample rate must be between 8000 and 48000 Hz".to_string());
        }

        if self.chunk_duration_ms < 10 || self.chunk_duration_ms > 1000 {
            return Err("Chunk duration must be between 10 and 1000 ms".to_string());
        }

        if self.buffer_capacity_secs < 1 || self.buffer_capacity_secs > 60 {
            return Err("Buffer capacity must be between 1 and 60 seconds".to_string());
        }

        if self.resampler_threads < 1 || self.resampler_threads > 8 {
            return Err("Resampler threads must be between 1 and 8".to_string());
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = AudioConfig::default();
        assert_eq!(config.target_sample_rate, 16000);
        assert_eq!(config.chunk_duration_ms, 100);
        assert!(config.validate().is_ok());
    }

    #[test]
    fn test_low_latency_config() {
        let config = AudioConfig::low_latency();
        assert_eq!(config.chunk_duration_ms, 80);
        assert!(config.validate().is_ok());
    }

    #[test]
    fn test_low_cpu_config() {
        let config = AudioConfig::low_cpu();
        assert_eq!(config.chunk_duration_ms, 250);
        assert!(config.validate().is_ok());
    }

    #[test]
    fn test_chunk_size_calculation() {
        let config = AudioConfig::default();
        assert_eq!(config.chunk_size(), 1600); // 16000 * 100 / 1000
    }

    #[test]
    fn test_buffer_capacity_calculation() {
        let config = AudioConfig::default();
        assert_eq!(config.buffer_capacity(), 128000); // 16000 * 8
    }

    #[test]
    fn test_invalid_sample_rate() {
        let config = AudioConfig {
            target_sample_rate: 100000, // Too high
            ..Default::default()
        };
        assert!(config.validate().is_err());
    }

    #[test]
    fn test_invalid_chunk_duration() {
        let config = AudioConfig {
            chunk_duration_ms: 5000, // Too long
            ..Default::default()
        };
        assert!(config.validate().is_err());
    }
}
