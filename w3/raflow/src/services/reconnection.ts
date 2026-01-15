/**
 * WebSocket Reconnection Strategy
 *
 * Phase 4: Optimized reconnection with exponential backoff
 */

export interface ReconnectionConfig {
  /** Enable automatic reconnection */
  enabled: boolean;

  /** Initial delay before first reconnection attempt (ms) */
  initialDelay: number;

  /** Maximum delay between reconnection attempts (ms) */
  maxDelay: number;

  /** Multiplier for exponential backoff */
  backoffMultiplier: number;

  /** Maximum number of reconnection attempts (0 = unlimited) */
  maxAttempts: number;

  /** Connection timeout in milliseconds */
  connectionTimeout: number;

  /** Enable jitter to prevent thundering herd */
  enableJitter: boolean;
}

export interface ReconnectionState {
  /** Current reconnection attempt number */
  attemptCount: number;

  /** Current delay before next attempt */
  currentDelay: number;

  /** Is currently attempting to reconnect */
  isReconnecting: boolean;

  /** Last error that triggered reconnection */
  lastError?: Error;

  /** Timestamp of last successful connection */
  lastConnectedAt?: number;
}

export class ReconnectionStrategy {
  private config: ReconnectionConfig;
  private state: ReconnectionState;
  private reconnectTimer: number | null = null;

  constructor(config?: Partial<ReconnectionConfig>) {
    this.config = {
      enabled: true,
      initialDelay: 1000, // 1 second
      maxDelay: 30000, // 30 seconds
      backoffMultiplier: 1.5,
      maxAttempts: 10,
      connectionTimeout: 10000, // 10 seconds
      enableJitter: true,
      ...config,
    };

    this.state = {
      attemptCount: 0,
      currentDelay: this.config.initialDelay,
      isReconnecting: false,
    };
  }

  /**
   * Calculate next reconnection delay with exponential backoff
   */
  private calculateNextDelay(): number {
    const baseDelay = Math.min(
      this.config.initialDelay *
        Math.pow(this.config.backoffMultiplier, this.state.attemptCount),
      this.config.maxDelay
    );

    // Add jitter to prevent thundering herd problem
    if (this.config.enableJitter) {
      const jitter = Math.random() * 0.3 * baseDelay; // +/- 15% jitter
      return baseDelay + jitter;
    }

    return baseDelay;
  }

  /**
   * Check if should attempt reconnection
   */
  shouldReconnect(): boolean {
    if (!this.config.enabled) {
      return false;
    }

    if (this.config.maxAttempts > 0 && this.state.attemptCount >= this.config.maxAttempts) {
      console.warn(
        `Max reconnection attempts (${this.config.maxAttempts}) reached`
      );
      return false;
    }

    return true;
  }

  /**
   * Schedule next reconnection attempt
   */
  async scheduleReconnect(reconnectFn: () => Promise<void>): Promise<void> {
    if (!this.shouldReconnect()) {
      return;
    }

    this.state.isReconnecting = true;
    this.state.currentDelay = this.calculateNextDelay();

    console.log(
      `Scheduling reconnection attempt ${this.state.attemptCount + 1} in ${this.state.currentDelay}ms`
    );

    return new Promise((resolve) => {
      this.reconnectTimer = window.setTimeout(async () => {
        this.state.attemptCount++;

        try {
          await reconnectFn();
          this.onReconnectSuccess();
          resolve();
        } catch (error) {
          this.onReconnectFailure(error as Error);
          // Schedule next attempt
          await this.scheduleReconnect(reconnectFn);
          resolve();
        }
      }, this.state.currentDelay);
    });
  }

  /**
   * Handle successful reconnection
   */
  private onReconnectSuccess(): void {
    console.log('Reconnection successful');
    this.reset();
    this.state.lastConnectedAt = Date.now();
  }

  /**
   * Handle failed reconnection
   */
  private onReconnectFailure(error: Error): void {
    console.error(`Reconnection attempt ${this.state.attemptCount} failed:`, error);
    this.state.lastError = error;

    if (!this.shouldReconnect()) {
      console.error('Max reconnection attempts reached, giving up');
      this.state.isReconnecting = false;
    }
  }

  /**
   * Cancel pending reconnection
   */
  cancelReconnect(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.state.isReconnecting = false;
  }

  /**
   * Reset reconnection state
   */
  reset(): void {
    this.cancelReconnect();
    this.state.attemptCount = 0;
    this.state.currentDelay = this.config.initialDelay;
    this.state.isReconnecting = false;
  }

  /**
   * Get current state
   */
  getState(): Readonly<ReconnectionState> {
    return { ...this.state };
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<ReconnectionConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get configuration
   */
  getConfig(): Readonly<ReconnectionConfig> {
    return { ...this.config };
  }
}

/**
 * Connection health monitor
 */
export class ConnectionHealthMonitor {
  private pingInterval: number | null = null;
  private lastPingTime = 0;
  private lastPongTime = 0;
  private consecutiveFailures = 0;

  constructor(
    private readonly checkInterval = 5000, // 5 seconds
    private readonly timeoutThreshold = 10000, // 10 seconds
    private readonly maxFailures = 3
  ) {}

  /**
   * Start monitoring connection health
   */
  start(pingFn: () => Promise<void>, onUnhealthy: () => void): void {
    this.stop();

    this.pingInterval = window.setInterval(async () => {
      this.lastPingTime = Date.now();

      try {
        await pingFn();
        this.lastPongTime = Date.now();
        this.consecutiveFailures = 0;
      } catch (error) {
        console.warn('Health check failed:', error);
        this.consecutiveFailures++;

        if (this.consecutiveFailures >= this.maxFailures) {
          console.error('Connection unhealthy, triggering recovery');
          onUnhealthy();
        }
      }
    }, this.checkInterval);
  }

  /**
   * Stop monitoring
   */
  stop(): void {
    if (this.pingInterval !== null) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    this.consecutiveFailures = 0;
  }

  /**
   * Record a pong (successful response from server)
   * Called when we receive a response indicating the connection is alive
   */
  recordPong(): void {
    this.lastPongTime = Date.now();
    this.consecutiveFailures = 0;
  }

  /**
   * Check if connection is healthy
   */
  isHealthy(): boolean {
    if (this.lastPingTime === 0 || this.lastPongTime === 0) {
      return true; // Not enough data yet
    }

    const timeSinceLastPong = Date.now() - this.lastPongTime;
    return timeSinceLastPong < this.timeoutThreshold;
  }

  /**
   * Get health metrics
   */
  getMetrics() {
    return {
      lastPingTime: this.lastPingTime,
      lastPongTime: this.lastPongTime,
      consecutiveFailures: this.consecutiveFailures,
      isHealthy: this.isHealthy(),
      timeSinceLastPong: this.lastPongTime > 0 ? Date.now() - this.lastPongTime : 0,
    };
  }
}
