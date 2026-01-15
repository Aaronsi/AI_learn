/**
 * Performance Monitor Tests
 *
 * Phase 5: Unit tests for performance monitoring
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { PerformanceMonitor } from '../services/performance';

describe('PerformanceMonitor', () => {
  let monitor: PerformanceMonitor;

  beforeEach(() => {
    monitor = new PerformanceMonitor();
    vi.useFakeTimers();
  });

  afterEach(() => {
    monitor.stop();
    vi.useRealTimers();
  });

  describe('Lifecycle', () => {
    it('should start monitoring', () => {
      monitor.start();
      const metrics = monitor.getMetrics();
      expect(metrics.timestamp).toBeGreaterThan(0);
    });

    it('should stop monitoring', () => {
      monitor.start();
      monitor.stop();
      // Should not throw after stopping
      expect(() => monitor.stop()).not.toThrow();
    });

    it('should reset metrics', () => {
      monitor.start();
      monitor.recordMessage();
      monitor.reset();
      const metrics = monitor.getMetrics();
      expect(metrics.uptime).toBe(0);
    });
  });

  describe('Message Recording', () => {
    it('should record messages sent', () => {
      monitor.start();
      monitor.recordMessage();
      monitor.recordMessage();
      monitor.recordMessage();

      // Advance time to update metrics
      vi.advanceTimersByTime(1000);

      const metrics = monitor.getMetrics();
      expect(metrics.messageRate).toBeGreaterThan(0);
    });

    it('should calculate message rate correctly', () => {
      monitor.start();

      // Record 5 messages
      for (let i = 0; i < 5; i++) {
        monitor.recordMessage();
      }

      // Advance by 1 second
      vi.advanceTimersByTime(1000);

      const metrics = monitor.getMetrics();
      expect(metrics.messageRate).toBe(5);
    });
  });

  describe('Latency Recording', () => {
    it('should record audio latency', () => {
      monitor.start();
      monitor.recordAudioLatency(100);
      const metrics = monitor.getMetrics();
      expect(metrics.audioLatency).toBeGreaterThan(0);
    });

    it('should record transcription latency', () => {
      monitor.start();
      monitor.recordTranscriptionLatency(150);
      const metrics = monitor.getMetrics();
      expect(metrics.transcriptionLatency).toBeGreaterThan(0);
    });

    it('should use exponential moving average for latency', () => {
      monitor.start();
      monitor.recordAudioLatency(100);
      monitor.recordAudioLatency(200);
      monitor.recordAudioLatency(300);

      const metrics = monitor.getMetrics();
      // EMA should smooth the values
      expect(metrics.audioLatency).toBeGreaterThan(100);
      expect(metrics.audioLatency).toBeLessThan(300);
    });
  });

  describe('Buffer Monitoring', () => {
    it('should record buffer fill level', () => {
      monitor.start();
      monitor.recordBufferFill(50);
      const metrics = monitor.getMetrics();
      expect(metrics.bufferFill).toBe(50);
    });

    it('should update buffer fill level', () => {
      monitor.start();
      monitor.recordBufferFill(30);
      monitor.recordBufferFill(70);
      const metrics = monitor.getMetrics();
      expect(metrics.bufferFill).toBe(70);
    });
  });

  describe('Reconnection Tracking', () => {
    it('should record reconnection attempts', () => {
      monitor.start();
      monitor.recordReconnection();
      const metrics = monitor.getMetrics();
      expect(metrics.reconnectionCount).toBe(1);
    });

    it('should count multiple reconnections', () => {
      monitor.start();
      monitor.recordReconnection();
      monitor.recordReconnection();
      monitor.recordReconnection();
      const metrics = monitor.getMetrics();
      expect(metrics.reconnectionCount).toBe(3);
    });
  });

  describe('System Metrics', () => {
    it('should update memory usage', () => {
      monitor.start();
      monitor.updateMemory(100);
      const metrics = monitor.getMetrics();
      expect(metrics.memory).toBe(100);
    });

    it('should update CPU usage', () => {
      monitor.start();
      monitor.updateCPU(25);
      const metrics = monitor.getMetrics();
      expect(metrics.cpu).toBe(25);
    });
  });

  describe('Metrics History', () => {
    it('should maintain metrics history', () => {
      monitor.start();

      // Advance time multiple times to create history
      for (let i = 0; i < 5; i++) {
        vi.advanceTimersByTime(1000);
      }

      const snapshot = monitor.getSnapshot();
      expect(snapshot.history.length).toBeGreaterThan(0);
    });

    it('should limit history size', () => {
      monitor.start();

      // Advance time many times
      for (let i = 0; i < 150; i++) {
        vi.advanceTimersByTime(1000);
      }

      const snapshot = monitor.getSnapshot();
      expect(snapshot.history.length).toBeLessThanOrEqual(100);
    });

    it('should calculate average metrics', () => {
      monitor.start();
      monitor.recordAudioLatency(100);
      vi.advanceTimersByTime(1000);
      monitor.recordAudioLatency(200);
      vi.advanceTimersByTime(1000);
      monitor.recordAudioLatency(300);
      vi.advanceTimersByTime(1000);

      const avg = monitor.getAverageMetrics();
      expect(avg.audioLatency).toBeGreaterThan(0);
    });
  });

  describe('Health Check', () => {
    it('should be healthy under normal conditions', () => {
      monitor.start();
      monitor.recordAudioLatency(100);
      monitor.recordTranscriptionLatency(200);
      monitor.recordBufferFill(50);
      monitor.recordMessage();

      vi.advanceTimersByTime(1000);

      expect(monitor.isHealthy()).toBe(true);
    });

    it('should detect high audio latency', () => {
      monitor.start();
      monitor.recordAudioLatency(600); // Above 500ms threshold
      expect(monitor.isHealthy()).toBe(false);
    });

    it('should detect high transcription latency', () => {
      monitor.start();
      monitor.recordTranscriptionLatency(1100); // Above 1000ms threshold
      expect(monitor.isHealthy()).toBe(false);
    });

    it('should detect buffer overflow', () => {
      monitor.start();
      monitor.recordBufferFill(95); // Above 90% threshold
      expect(monitor.isHealthy()).toBe(false);
    });

    it('should detect no message sending', () => {
      monitor.start();
      vi.advanceTimersByTime(6000); // Wait > 5 seconds without messages
      expect(monitor.isHealthy()).toBe(false);
    });
  });

  describe('Uptime Tracking', () => {
    it('should track uptime correctly', () => {
      monitor.start();
      vi.advanceTimersByTime(5000); // 5 seconds

      const metrics = monitor.getMetrics();
      expect(metrics.uptime).toBeGreaterThanOrEqual(5000);
    });

    it('should reset uptime on restart', () => {
      monitor.start();
      vi.advanceTimersByTime(5000);
      monitor.stop();
      monitor.start();

      const metrics = monitor.getMetrics();
      expect(metrics.uptime).toBeLessThan(1000);
    });
  });

  describe('Snapshot', () => {
    it('should create snapshot with current metrics', () => {
      monitor.start();
      monitor.recordAudioLatency(100);
      monitor.recordMessage();

      const snapshot = monitor.getSnapshot();
      expect(snapshot.metrics).toBeDefined();
      expect(snapshot.history).toBeDefined();
      expect(snapshot.metrics.audioLatency).toBeGreaterThan(0);
    });

    it('should not mutate original metrics', () => {
      monitor.start();
      const snapshot1 = monitor.getSnapshot();
      monitor.recordAudioLatency(100);
      const snapshot2 = monitor.getSnapshot();

      expect(snapshot1.metrics.audioLatency).not.toBe(
        snapshot2.metrics.audioLatency
      );
    });
  });
});
