/// Audio Capture
///
/// Captures audio from microphone using cpal
/// Uses tokio::sync::mpsc channel to transfer audio data from audio thread to tokio runtime

use super::resampler::AudioResampler;
use crate::error::{Result, audio_device_error};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Sample, SampleFormat, Stream};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use tauri::{AppHandle, Emitter};
use tokio::sync::mpsc::{UnboundedReceiver, UnboundedSender};
use tokio::sync::Mutex as TokioMutex;
use tracing::{error, info, warn, debug};

const TARGET_SAMPLE_RATE: u32 = 16000; // Target for ElevenLabs
const CHUNK_DURATION_MS: u32 = 200; // 0.2 seconds - each chunk is 0.2s of audio
const CHUNK_SIZE: usize = (TARGET_SAMPLE_RATE * CHUNK_DURATION_MS / 1000) as usize; // 3200 samples

/// Audio data message sent from audio thread
/// Contains raw samples (before resampling) that will be processed in the chunk processor
struct AudioMessage {
    samples: Vec<f32>,
    rms: f32,
}

/// Audio capture manager
pub struct AudioCapture {
    stream: Arc<TokioMutex<Option<Stream>>>,
    is_running: Arc<AtomicBool>,
    app_handle: Arc<TokioMutex<Option<AppHandle>>>,
    // Channel for sending audio data from audio thread to processor
    // Using tokio unbounded channel - sender can be used from sync code
    audio_sender: Arc<TokioMutex<Option<UnboundedSender<AudioMessage>>>>,
    // Store device sample rate for resampling
    device_sample_rate: Arc<TokioMutex<u32>>,
}

impl AudioCapture {
    /// Create new audio capture
    pub fn new() -> Self {
        Self {
            stream: Arc::new(TokioMutex::new(None)),
            is_running: Arc::new(AtomicBool::new(false)),
            app_handle: Arc::new(TokioMutex::new(None)),
            audio_sender: Arc::new(TokioMutex::new(None)),
            device_sample_rate: Arc::new(TokioMutex::new(TARGET_SAMPLE_RATE)),
        }
    }

    /// Set app handle for emitting events
    pub async fn set_app_handle(&self, handle: AppHandle) {
        *self.app_handle.lock().await = Some(handle);
    }

    /// Start audio capture
    pub async fn start(&self) -> Result<()> {
        if self.is_running.load(Ordering::SeqCst) {
            return Err(audio_device_error("Audio capture already running"));
        }

        info!("Starting audio capture");

        // Get host and device
        let host = cpal::default_host();
        let device = host
            .default_input_device()
            .ok_or_else(|| audio_device_error("No input device available"))?;

        let device_name = device.name().unwrap_or_else(|_| "Unknown".to_string());
        info!("Using input device: {}", device_name);

        // Get device config
        let config = device
            .default_input_config()
            .map_err(|e| audio_device_error(format!("Failed to get default config: {}", e)))?;

        // In cpal 0.17+, sample_rate() returns u32 directly (not SampleRate struct)
        let sample_rate: u32 = config.sample_rate();
        let channels = config.channels();
        let sample_format = config.sample_format();

        info!(
            "Device config: {} Hz, {} channels, {:?}",
            sample_rate, channels, sample_format
        );

        // Store device sample rate for resampling in chunk processor
        *self.device_sample_rate.lock().await = sample_rate;

        // Create tokio unbounded channel for audio data transfer from audio thread
        // UnboundedSender::send() is NOT async, so it can be used from sync code (audio callback)
        let (tx, rx) = tokio::sync::mpsc::unbounded_channel::<AudioMessage>();
        *self.audio_sender.lock().await = Some(tx.clone());

        // Build stream - send raw samples without resampling
        // Resampling will be done in the chunk processor with accumulated data
        let stream = match sample_format {
            SampleFormat::F32 => self.build_stream_simple::<f32>(
                &device,
                &config.into(),
                tx,
                channels,
            )?,
            SampleFormat::I16 => self.build_stream_simple::<i16>(
                &device,
                &config.into(),
                tx,
                channels,
            )?,
            SampleFormat::U16 => self.build_stream_simple::<u16>(
                &device,
                &config.into(),
                tx,
                channels,
            )?,
            _ => {
                return Err(audio_device_error(format!(
                    "Unsupported sample format: {:?}",
                    sample_format
                )))
            }
        };

        stream.play().map_err(|e| {
            audio_device_error(format!("Failed to start audio stream: {}", e))
        })?;

        *self.stream.lock().await = Some(stream);
        self.is_running.store(true, Ordering::SeqCst);

        info!("Audio stream started, will resample {} Hz -> {} Hz", sample_rate, TARGET_SAMPLE_RATE);

        // Start chunk processor with resampling
        self.start_chunk_processor(rx, sample_rate).await;

        info!("Audio capture started successfully");

        Ok(())
    }

    /// Build audio stream - simplified version that sends raw samples
    /// Resampling is done in the chunk processor to handle variable input sizes
    fn build_stream_simple<T>(
        &self,
        device: &cpal::Device,
        config: &cpal::StreamConfig,
        tx: UnboundedSender<AudioMessage>,
        channels: u16,
    ) -> Result<Stream>
    where
        T: Sample + cpal::SizedSample,
        f32: cpal::FromSample<T>,
    {
        use std::sync::atomic::{AtomicU64, Ordering as AtomicOrdering};
        let callback_count = Arc::new(AtomicU64::new(0));
        let callback_count_clone = callback_count.clone();

        let stream = device
            .build_input_stream(
                config,
                move |data: &[T], _: &cpal::InputCallbackInfo| {
                    let count = callback_count_clone.fetch_add(1, AtomicOrdering::SeqCst);

                    // Convert to f32 and handle multi-channel
                    let samples: Vec<f32> = if channels == 1 {
                        data.iter().map(|&s| s.to_sample::<f32>()).collect()
                    } else {
                        // Convert stereo to mono by averaging
                        data.chunks(channels as usize)
                            .map(|chunk| {
                                let sum: f32 = chunk.iter().map(|&s| s.to_sample::<f32>()).sum();
                                sum / channels as f32
                            })
                            .collect()
                    };

                    // Calculate RMS level for the raw samples
                    let rms = calculate_rms(&samples);

                    // Log first few callbacks to confirm audio is flowing
                    if count < 5 {
                        info!("🎤 Audio callback #{}: {} samples, rms={:.4}", count, samples.len(), rms);
                    }

                    // Send raw samples to tokio channel (resampling happens in chunk processor)
                    let msg = AudioMessage {
                        samples,
                        rms,
                    };

                    if let Err(e) = tx.send(msg) {
                        // Channel closed, stop sending
                        error!("Failed to send audio data to channel: {}", e);
                    }
                },
                |err| error!("Audio stream error: {}", err),
                None,
            )
            .map_err(|e| audio_device_error(format!("Failed to build stream: {}", e)))?;

        Ok(stream)
    }

    /// Start chunk processor task with resampling support
    async fn start_chunk_processor(&self, mut rx: UnboundedReceiver<AudioMessage>, device_sample_rate: u32) {
        let app_handle = self.app_handle.clone();
        let is_running = self.is_running.clone();

        info!("🎵 Spawning chunk processor task (device rate: {} Hz, target: {} Hz)...",
            device_sample_rate, TARGET_SAMPLE_RATE);

        tokio::spawn(async move {
            info!("🎵 Chunk processor task started!");

            let mut chunk_count = 0u64;
            let mut message_count = 0u64;

            // Accumulated raw samples at device sample rate
            let mut raw_accumulated: Vec<f32> = Vec::with_capacity(device_sample_rate as usize);

            // Accumulated resampled samples at target sample rate
            let mut resampled_accumulated: Vec<f32> = Vec::with_capacity(CHUNK_SIZE * 2);

            // Create resampler if needed
            let needs_resampling = device_sample_rate != TARGET_SAMPLE_RATE;

            // Calculate chunk size at device sample rate for resampler
            // Use a reasonable chunk size that allows flexible input
            let resample_chunk_size = (device_sample_rate as usize) / 10; // 0.1 second chunks

            let mut resampler = if needs_resampling {
                info!("🔄 Creating resampler: {} Hz -> {} Hz (chunk size: {})",
                    device_sample_rate, TARGET_SAMPLE_RATE, resample_chunk_size);
                match AudioResampler::new(device_sample_rate, TARGET_SAMPLE_RATE, resample_chunk_size) {
                    Ok(r) => Some(r),
                    Err(e) => {
                        error!("❌ Failed to create resampler: {}", e);
                        None
                    }
                }
            } else {
                info!("✅ No resampling needed (device is already {} Hz)", TARGET_SAMPLE_RATE);
                None
            };

            loop {
                // Use tokio select to handle both receiving messages and checking stop flag
                tokio::select! {
                    // Try to receive audio data
                    msg = rx.recv() => {
                        match msg {
                            Some(audio_msg) => {
                                message_count += 1;

                                // Log first few messages to confirm data is flowing
                                if message_count <= 5 {
                                    info!("🎵 Received audio message #{}: {} samples, rms={:.4}",
                                        message_count, audio_msg.samples.len(), audio_msg.rms);
                                }

                                // Emit audio level event
                                if let Some(handle) = app_handle.lock().await.as_ref() {
                                    let _ = handle.emit("audio-level", audio_msg.rms);
                                }

                                if needs_resampling {
                                    // Accumulate raw samples for resampling
                                    raw_accumulated.extend(audio_msg.samples);

                                    // Process complete chunks through resampler
                                    while raw_accumulated.len() >= resample_chunk_size {
                                        let chunk: Vec<f32> = raw_accumulated.drain(..resample_chunk_size).collect();

                                        if let Some(ref mut r) = resampler {
                                            match r.process(&chunk) {
                                                Ok(resampled) => {
                                                    debug!("🔄 Resampled {} -> {} samples", chunk.len(), resampled.len());
                                                    resampled_accumulated.extend(resampled);
                                                }
                                                Err(e) => {
                                                    error!("❌ Resampling error: {}", e);
                                                }
                                            }
                                        }
                                    }
                                } else {
                                    // No resampling needed, directly accumulate
                                    resampled_accumulated.extend(audio_msg.samples);
                                }

                                // Emit complete chunks at target sample rate
                                while resampled_accumulated.len() >= CHUNK_SIZE {
                                    let chunk: Vec<f32> = resampled_accumulated.drain(..CHUNK_SIZE).collect();
                                    chunk_count += 1;
                                    emit_audio_chunk(&app_handle, &chunk, chunk_count).await;
                                }
                            }
                            None => {
                                // Channel closed
                                info!("🎵 Audio channel closed, processing remaining data");
                                // Process any remaining accumulated samples
                                while resampled_accumulated.len() >= CHUNK_SIZE {
                                    let chunk: Vec<f32> = resampled_accumulated.drain(..CHUNK_SIZE).collect();
                                    chunk_count += 1;
                                    emit_audio_chunk(&app_handle, &chunk, chunk_count).await;
                                }
                                break;
                            }
                        }
                    }
                    // Check stop flag periodically
                    _ = tokio::time::sleep(tokio::time::Duration::from_millis(100)) => {
                        if !is_running.load(Ordering::SeqCst) {
                            info!("🎵 Stop signal received, processing remaining {} resampled samples",
                                resampled_accumulated.len());
                            // Process any remaining accumulated samples before stopping
                            while resampled_accumulated.len() >= CHUNK_SIZE {
                                let chunk: Vec<f32> = resampled_accumulated.drain(..CHUNK_SIZE).collect();
                                chunk_count += 1;
                                emit_audio_chunk(&app_handle, &chunk, chunk_count).await;
                            }
                            break;
                        }
                    }
                }
            }

            info!("🎵 Chunk processor stopped: received {} messages, emitted {} chunks", message_count, chunk_count);
        });
    }

    /// Stop audio capture
    pub async fn stop(&self) -> Result<()> {
        if !self.is_running.load(Ordering::SeqCst) {
            warn!("Audio capture not running");
            return Ok(());
        }

        info!("Stopping audio capture");

        // Set is_running to false first - this signals the chunk processor to stop
        self.is_running.store(false, Ordering::SeqCst);

        // Drop the stream to stop new audio data from coming in
        *self.stream.lock().await = None;

        // Close the audio sender channel (this will cause recv() to return None)
        *self.audio_sender.lock().await = None;

        // Give chunk processor time to process remaining data
        tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;

        info!("Audio capture stopped");

        Ok(())
    }

    /// Check if currently capturing
    pub async fn is_running(&self) -> bool {
        self.is_running.load(Ordering::SeqCst)
    }
}

/// Emit audio chunk event
async fn emit_audio_chunk(
    app_handle: &Arc<TokioMutex<Option<AppHandle>>>,
    chunk: &[f32],
    chunk_count: u64,
) {
    let bytes = samples_to_bytes(chunk);

    info!(
        "🎵 Processing audio chunk #{}: {} samples -> {} bytes",
        chunk_count,
        chunk.len(),
        bytes.len()
    );

    // Emit audio chunk event
    if let Some(handle) = app_handle.lock().await.as_ref() {
        let payload = serde_json::json!({
            "data": bytes,
            "sampleRate": TARGET_SAMPLE_RATE,
            "channels": 1,
        });

        match handle.emit("audio-chunk", payload) {
            Ok(_) => {
                info!("🎵 Emitted audio-chunk event #{}", chunk_count);
            }
            Err(e) => {
                error!("❌ Failed to emit audio-chunk event: {}", e);
            }
        }
    } else {
        warn!("⚠️ No app handle available to emit event");
    }
}

/// Calculate RMS level
fn calculate_rms(samples: &[f32]) -> f32 {
    if samples.is_empty() {
        return 0.0;
    }

    let sum_squares: f32 = samples.iter().map(|&s| s * s).sum();
    (sum_squares / samples.len() as f32).sqrt()
}

/// Convert f32 samples to 16-bit PCM bytes
fn samples_to_bytes(samples: &[f32]) -> Vec<u8> {
    let mut bytes = Vec::with_capacity(samples.len() * 2);

    for &sample in samples {
        // Clamp to [-1.0, 1.0] and convert to i16
        let clamped = sample.clamp(-1.0, 1.0);
        let scaled = (clamped * 32767.0) as i16;
        bytes.extend_from_slice(&scaled.to_le_bytes());
    }

    bytes
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calculate_rms() {
        let samples = vec![0.5, -0.5, 0.5, -0.5];
        let rms = calculate_rms(&samples);
        assert!(rms > 0.0 && rms <= 1.0);
    }

    #[test]
    fn test_samples_to_bytes() {
        let samples = vec![0.0, 0.5, -0.5, 1.0, -1.0];
        let bytes = samples_to_bytes(&samples);
        assert_eq!(bytes.len(), samples.len() * 2);
    }

    #[tokio::test]
    async fn test_audio_capture_lifecycle() {
        let capture = AudioCapture::new();
        assert!(!capture.is_running().await);
    }
}
