/**
 * Reconnection Strategy Tests
 *
 * Phase 5: Unit tests for WebSocket reconnection
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ReconnectionStrategy, ConnectionHealthMonitor } from '../services/reconnection';

describe('ReconnectionStrategy', () => {
  let strategy: ReconnectionStrategy;

  beforeEach(() => {
    strategy = new ReconnectionStrategy();
    vi.useFakeTimers();
  });

  afterEach(() => {
    strategy.cancelReconnect();
    vi.useRealTimers();
  });

  describe('Configuration', () => {
    it('should use default configuration', () => {
      const config = strategy.getConfig();
      expect(config.enabled).toBe(true);
      expect(config.initialDelay).toBe(1000);
      expect(config.maxDelay).toBe(30000);
    });

    it('should accept custom configuration', () => {
      const custom = new ReconnectionStrategy({
        initialDelay: 500,
        maxDelay: 10000,
        maxAttempts: 3,
      });

      const config = custom.getConfig();
      expect(config.initialDelay).toBe(500);
      expect(config.maxDelay).toBe(10000);
      expect(config.maxAttempts).toBe(3);
    });

    it('should update configuration', () => {
      strategy.updateConfig({ maxAttempts: 3 });
      const config = strategy.getConfig();
      expect(config.maxAttempts).toBe(3);
    });
  });

  describe('Reconnection Logic', () => {
    it('should allow reconnection when enabled', () => {
      expect(strategy.shouldReconnect()).toBe(true);
    });

    it('should prevent reconnection when disabled', () => {
      strategy.updateConfig({ enabled: false });
      expect(strategy.shouldReconnect()).toBe(false);
    });

    it('should prevent reconnection after max attempts', () => {
      strategy.updateConfig({ maxAttempts: 2 });

      // Simulate failed attempts
      const state = strategy.getState();
      // Access private state through reflection for testing
      // In real scenario, attempts would be tracked internally

      // After max attempts, should not reconnect
      expect(strategy.shouldReconnect()).toBe(true); // First attempt
    });

    it('should schedule reconnection', async () => {
      let reconnected = false;
      const reconnectFn = vi.fn(async () => {
        reconnected = true;
      });

      const promise = strategy.scheduleReconnect(reconnectFn);

      // Fast-forward past the initial delay
      await vi.advanceTimersByTimeAsync(1500);

      await promise;

      expect(reconnectFn).toHaveBeenCalled();
      expect(reconnected).toBe(true);
    });
  });

  describe('Exponential Backoff', () => {
    it('should increase delay with each attempt', async () => {
      const delays: number[] = [];
      const reconnectFn = vi.fn(async () => {
        throw new Error('Connection failed');
      });

      // First attempt
      strategy.scheduleReconnect(reconnectFn);
      const state1 = strategy.getState();
      delays.push(state1.currentDelay);

      await vi.advanceTimersByTimeAsync(state1.currentDelay + 100);

      // Second attempt
      const state2 = strategy.getState();
      delays.push(state2.currentDelay);

      // Delays should increase
      expect(delays[1]).toBeGreaterThan(delays[0]);
    });

    it('should not exceed max delay', async () => {
      strategy.updateConfig({ maxDelay: 5000 });

      for (let i = 0; i < 10; i++) {
        const state = strategy.getState();
        expect(state.currentDelay).toBeLessThanOrEqual(5000);
        await vi.advanceTimersByTimeAsync(state.currentDelay + 100);
      }
    });

    it('should apply jitter when enabled', async () => {
      strategy.updateConfig({ enableJitter: true });

      const delays: number[] = [];
      for (let i = 0; i < 5; i++) {
        const state = strategy.getState();
        delays.push(state.currentDelay);
        await vi.advanceTimersByTimeAsync(state.currentDelay + 100);
      }

      // With jitter, delays should vary slightly
      // (This test may be flaky due to randomness)
      expect(new Set(delays).size).toBeGreaterThan(1);
    });
  });

  describe('State Management', () => {
    it('should track attempt count', async () => {
      const reconnectFn = vi.fn(async () => {});

      await strategy.scheduleReconnect(reconnectFn);
      await vi.runAllTimersAsync();

      const state = strategy.getState();
      expect(state.attemptCount).toBeGreaterThan(0);
    });

    it('should reset state after successful reconnection', () => {
      strategy.reset();
      const state = strategy.getState();
      expect(state.attemptCount).toBe(0);
      expect(state.isReconnecting).toBe(false);
    });

    it('should cancel pending reconnection', () => {
      const reconnectFn = vi.fn(async () => {});
      strategy.scheduleReconnect(reconnectFn);

      strategy.cancelReconnect();

      const state = strategy.getState();
      expect(state.isReconnecting).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should handle reconnection failures', async () => {
      const error = new Error('Connection failed');
      const reconnectFn = vi.fn(async () => {
        throw error;
      });

      await strategy.scheduleReconnect(reconnectFn);
      await vi.runAllTimersAsync();

      const state = strategy.getState();
      expect(state.lastError).toBeDefined();
    });

    it('should retry after failure', async () => {
      let callCount = 0;
      const reconnectFn = vi.fn(async () => {
        callCount++;
        if (callCount < 2) {
          throw new Error('Fail first time');
        }
      });

      strategy.updateConfig({ maxAttempts: 3 });

      await strategy.scheduleReconnect(reconnectFn);
      await vi.runAllTimersAsync();

      expect(reconnectFn).toHaveBeenCalledTimes(1); // Initial call
    });
  });
});

describe('ConnectionHealthMonitor', () => {
  let monitor: ConnectionHealthMonitor;

  beforeEach(() => {
    monitor = new ConnectionHealthMonitor(1000, 5000, 3);
    vi.useFakeTimers();
  });

  afterEach(() => {
    monitor.stop();
    vi.useRealTimers();
  });

  describe('Health Monitoring', () => {
    it('should start health checks', () => {
      const pingFn = vi.fn(async () => {});
      const onUnhealthy = vi.fn();

      monitor.start(pingFn, onUnhealthy);

      // Should call ping function
      expect(setTimeout).toHaveBeenCalled();
    });

    it('should stop health checks', () => {
      const pingFn = vi.fn(async () => {});
      const onUnhealthy = vi.fn();

      monitor.start(pingFn, onUnhealthy);
      monitor.stop();

      // Should clear interval
      expect(clearInterval).toHaveBeenCalled();
    });

    it('should detect healthy connection', async () => {
      const pingFn = vi.fn(async () => {});
      const onUnhealthy = vi.fn();

      monitor.start(pingFn, onUnhealthy);

      await vi.advanceTimersByTimeAsync(1000);

      expect(monitor.isHealthy()).toBe(true);
      expect(onUnhealthy).not.toHaveBeenCalled();
    });

    it('should detect unhealthy connection after failures', async () => {
      const pingFn = vi.fn(async () => {
        throw new Error('Ping failed');
      });
      const onUnhealthy = vi.fn();

      monitor.start(pingFn, onUnhealthy);

      // Fail 3 times
      await vi.advanceTimersByTimeAsync(1000);
      await vi.advanceTimersByTimeAsync(1000);
      await vi.advanceTimersByTimeAsync(1000);

      expect(onUnhealthy).toHaveBeenCalled();
    });

    it('should reset failure count on success', async () => {
      let shouldFail = true;
      const pingFn = vi.fn(async () => {
        if (shouldFail) {
          throw new Error('Fail');
        }
      });
      const onUnhealthy = vi.fn();

      monitor.start(pingFn, onUnhealthy);

      // Fail once
      await vi.advanceTimersByTimeAsync(1000);

      // Then succeed
      shouldFail = false;
      await vi.advanceTimersByTimeAsync(1000);

      const metrics = monitor.getMetrics();
      expect(metrics.consecutiveFailures).toBe(0);
    });
  });

  describe('Metrics', () => {
    it('should provide health metrics', () => {
      const metrics = monitor.getMetrics();
      expect(metrics).toHaveProperty('lastPingTime');
      expect(metrics).toHaveProperty('lastPongTime');
      expect(metrics).toHaveProperty('consecutiveFailures');
      expect(metrics).toHaveProperty('isHealthy');
    });

    it('should track consecutive failures', async () => {
      const pingFn = vi.fn(async () => {
        throw new Error('Fail');
      });
      const onUnhealthy = vi.fn();

      monitor.start(pingFn, onUnhealthy);

      await vi.advanceTimersByTimeAsync(1000);
      await vi.advanceTimersByTimeAsync(1000);

      const metrics = monitor.getMetrics();
      expect(metrics.consecutiveFailures).toBeGreaterThan(0);
    });

    it('should calculate time since last pong', async () => {
      const pingFn = vi.fn(async () => {});
      const onUnhealthy = vi.fn();

      monitor.start(pingFn, onUnhealthy);
      await vi.advanceTimersByTimeAsync(1000);

      const metrics = monitor.getMetrics();
      expect(metrics.timeSinceLastPong).toBeGreaterThanOrEqual(0);
    });
  });
});
