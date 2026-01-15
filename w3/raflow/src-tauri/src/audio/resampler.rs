/// Audio Resampler
///
/// Resamples audio from one sample rate to another using rubato

use crate::error::{Result, audio_device_error};
use rubato::{
    Resampler, SincFixedIn, SincInterpolationParameters, SincInterpolationType,
    WindowFunction,
};
use tracing::{debug, info};

/// Audio resampler for converting sample rates
pub struct AudioResampler {
    resampler: SincFixedIn<f32>,
    input_rate: u32,
    output_rate: u32,
}

impl AudioResampler {
    /// Create new resampler
    ///
    /// # Arguments
    /// * `input_rate` - Input sample rate (e.g., 44100 or 48000)
    /// * `output_rate` - Output sample rate (typically 16000 for Scribe v2)
    /// * `chunk_size` - Size of input chunks
    pub fn new(input_rate: u32, output_rate: u32, chunk_size: usize) -> Result<Self> {
        if input_rate == 0 || output_rate == 0 {
            return Err(audio_device_error("Sample rates must be non-zero"));
        }

        info!(
            "Creating resampler: {} Hz -> {} Hz (chunk size: {})",
            input_rate, output_rate, chunk_size
        );

        let resample_ratio = output_rate as f64 / input_rate as f64;

        let params = SincInterpolationParameters {
            sinc_len: 256,
            f_cutoff: 0.95,
            interpolation: SincInterpolationType::Linear,
            oversampling_factor: 256,
            window: WindowFunction::BlackmanHarris2,
        };

        let resampler = SincFixedIn::<f32>::new(
            resample_ratio,
            2.0, // max relative ratio deviation
            params,
            chunk_size,
            1, // mono channel
        )
        .map_err(|e| audio_device_error(format!("Failed to create resampler: {}", e)))?;

        Ok(Self {
            resampler,
            input_rate,
            output_rate,
        })
    }

    /// Process audio samples
    ///
    /// # Arguments
    /// * `input` - Input samples at input_rate
    ///
    /// # Returns
    /// Output samples at output_rate
    pub fn process(&mut self, input: &[f32]) -> Result<Vec<f32>> {
        if input.is_empty() {
            return Ok(Vec::new());
        }

        debug!("Resampling {} samples", input.len());

        let waves_in = vec![input.to_vec()];

        let waves_out = self
            .resampler
            .process(&waves_in, None)
            .map_err(|e| audio_device_error(format!("Resampling failed: {}", e)))?;

        Ok(waves_out[0].clone())
    }

    /// Get input sample rate
    pub fn input_rate(&self) -> u32 {
        self.input_rate
    }

    /// Get output sample rate
    pub fn output_rate(&self) -> u32 {
        self.output_rate
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resampler_creation() {
        let resampler = AudioResampler::new(48000, 16000, 4800);
        assert!(resampler.is_ok());
    }

    #[test]
    fn test_resampler_process() {
        let mut resampler = AudioResampler::new(48000, 16000, 4800).unwrap();

        // 0.1 second at 48kHz = 4800 samples
        let input: Vec<f32> = (0..4800).map(|i| (i as f32 / 4800.0) * 0.1).collect();

        let output = resampler.process(&input).unwrap();

        // Should produce approximately 1600 samples (0.1s at 16kHz)
        assert!(output.len() > 1500 && output.len() < 1700);
    }

    #[test]
    fn test_resampler_empty_input() {
        let mut resampler = AudioResampler::new(48000, 16000, 4800).unwrap();
        let output = resampler.process(&[]).unwrap();
        assert_eq!(output.len(), 0);
    }
}
