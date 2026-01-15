/// Audio Buffer
///
/// Ring buffer for audio data

use crate::error::{Result, audio_device_error};
use ringbuf::traits::{Consumer, Observer, Producer, Split};
use ringbuf::HeapRb;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::debug;

/// Audio ring buffer for storing and retrieving audio chunks
/// 
/// Uses split producer/consumer pattern for thread-safe access
pub struct AudioBuffer {
    producer: Arc<Mutex<<HeapRb<f32> as Split>::Prod>>,
    consumer: Arc<Mutex<<HeapRb<f32> as Split>::Cons>>,
    chunk_size: usize,
}

impl AudioBuffer {
    /// Create new audio buffer
    ///
    /// # Arguments
    /// * `capacity` - Buffer capacity in samples (should be power of 2 for efficiency)
    /// * `chunk_size` - Size of chunks to extract
    pub fn new(capacity: usize, chunk_size: usize) -> Self {
        let rb = HeapRb::<f32>::new(capacity);
        let (producer, consumer) = rb.split();

        Self {
            producer: Arc::new(Mutex::new(producer)),
            consumer: Arc::new(Mutex::new(consumer)),
            chunk_size,
        }
    }

    /// Push samples into buffer
    ///
    /// # Arguments
    /// * `samples` - Audio samples to push
    ///
    /// # Returns
    /// Number of samples successfully pushed
    pub async fn push(&self, samples: &[f32]) -> usize {
        let mut producer = self.producer.lock().await;
        
        // Try to push all samples, Producer will handle overflow
        let written = producer.push_slice(&samples);
        
        if written < samples.len() {
            debug!("Buffer full, dropping {} samples", samples.len() - written);
        }
        
        written
    }

    /// Try to extract a chunk from buffer
    ///
    /// # Returns
    /// Some(Vec<f32>) if enough samples available, None otherwise
    pub async fn pop_chunk(&self) -> Option<Vec<f32>> {
        let mut consumer = self.consumer.lock().await;
        
        // Check if we have enough data using Observer trait
        if <_ as Observer>::occupied_len(&*consumer) >= self.chunk_size {
            let mut chunk = vec![0.0f32; self.chunk_size];
            let read = <_ as Consumer>::pop_slice(&mut *consumer, &mut chunk);
            if read == self.chunk_size {
            Some(chunk)
            } else {
                None
            }
        } else {
            None
        }
    }

    /// Get number of samples currently in buffer
    pub async fn len(&self) -> usize {
        let consumer = self.consumer.lock().await;
        <_ as Observer>::occupied_len(&*consumer)
    }

    /// Check if buffer is empty
    pub async fn is_empty(&self) -> bool {
        self.len().await == 0
    }

    /// Clear all data from buffer
    pub async fn clear(&self) {
        let mut consumer = self.consumer.lock().await;
        let occupied = <_ as Observer>::occupied_len(&*consumer);
        <_ as Consumer>::skip(&mut *consumer, occupied);
    }

    /// Get chunk size
    pub fn chunk_size(&self) -> usize {
        self.chunk_size
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_buffer_push_pop() {
        let buffer = AudioBuffer::new(1024, 256);

        // Push some data
        let samples: Vec<f32> = (0..256).map(|i| i as f32).collect();
        let pushed = buffer.push(&samples).await;
        assert_eq!(pushed, 256);

        // Pop chunk
        let chunk = buffer.pop_chunk().await;
        assert!(chunk.is_some());
        assert_eq!(chunk.unwrap().len(), 256);
    }

    #[tokio::test]
    async fn test_buffer_not_enough_data() {
        let buffer = AudioBuffer::new(1024, 256);

        // Push less data than chunk size
        let samples: Vec<f32> = vec![0.0; 100];
        buffer.push(&samples).await;

        // Should not be able to pop
        let chunk = buffer.pop_chunk().await;
        assert!(chunk.is_none());
    }

    #[tokio::test]
    async fn test_buffer_overflow() {
        let buffer = AudioBuffer::new(512, 256);

        // Try to push more data than capacity
        let samples: Vec<f32> = vec![0.0; 1000];
        let pushed = buffer.push(&samples).await;

        // Should only push what fits
        assert!(pushed <= 512);
    }

    #[tokio::test]
    async fn test_buffer_clear() {
        let buffer = AudioBuffer::new(1024, 256);

        let samples: Vec<f32> = vec![0.0; 512];
        buffer.push(&samples).await;

        assert_eq!(buffer.len().await, 512);

        buffer.clear().await;
        assert_eq!(buffer.len().await, 0);
    }
}
