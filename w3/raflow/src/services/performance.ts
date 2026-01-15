/**
 * Performance Monitor
 *
 * Phase 4: Real-time performance metrics and monitoring
 */

export interface PerformanceMetrics {
  /** CPU usage percentage (0-100) */
  cpu: number;

  /** Memory usage in MB */
  memory: number;

  /** Audio processing latency in milliseconds */
  audioLatency: number;

  /** Transcription latency in milliseconds */
  transcriptionLatency: number;

  /** WebSocket messages sent per second */
  messageRate: number;

  /** Audio buffer fill percentage (0-100) */
  bufferFill: number;

  /** Connection uptime in milliseconds */
  uptime: number;

  /** Number of reconnection attempts */
  reconnectionCount: number;

  /** Last updated timestamp */
  timestamp: number;
}

export interface PerformanceSnapshot {
  metrics: PerformanceMetrics;
  history: PerformanceMetrics[];
}

export class PerformanceMonitor {
  private metrics: PerformanceMetrics;
  private history: PerformanceMetrics[] = [];
  private maxHistorySize = 100;
  private startTime = 0;
  private messageCount = 0;
  private lastMessageCount = 0;
  private reconnectionCount = 0;
  private monitorInterval: number | null = null;

  constructor() {
    this.metrics = this.createEmptyMetrics();
  }

  /**
   * Create empty metrics object
   */
  private createEmptyMetrics(): PerformanceMetrics {
    return {
      cpu: 0,
      memory: 0,
      audioLatency: 0,
      transcriptionLatency: 0,
      messageRate: 0,
      bufferFill: 0,
      uptime: 0,
      reconnectionCount: 0,
      timestamp: Date.now(),
    };
  }

  /**
   * Start monitoring
   */
  start(): void {
    this.startTime = Date.now();
    this.metrics = this.createEmptyMetrics();
    this.history = [];
    this.messageCount = 0;
    this.lastMessageCount = 0;
    this.reconnectionCount = 0;

    // Update metrics every second
    this.monitorInterval = window.setInterval(() => {
      this.updateMetrics();
    }, 1000);
  }

  /**
   * Stop monitoring
   */
  stop(): void {
    if (this.monitorInterval !== null) {
      clearInterval(this.monitorInterval);
      this.monitorInterval = null;
    }
  }

  /**
   * Update metrics
   */
  private updateMetrics(): void {
    const now = Date.now();

    // Calculate message rate
    const messagesSent = this.messageCount - this.lastMessageCount;
    this.lastMessageCount = this.messageCount;

    // Update metrics
    this.metrics = {
      ...this.metrics,
      messageRate: messagesSent,
      uptime: now - this.startTime,
      reconnectionCount: this.reconnectionCount,
      timestamp: now,
    };

    // Add to history
    this.history.push({ ...this.metrics });

    // Limit history size
    if (this.history.length > this.maxHistorySize) {
      this.history.shift();
    }
  }

  /**
   * Record message sent
   */
  recordMessage(): void {
    this.messageCount++;
  }

  /**
   * Record audio latency
   */
  recordAudioLatency(latencyMs: number): void {
    // Use exponential moving average
    const alpha = 0.3;
    this.metrics.audioLatency =
      alpha * latencyMs + (1 - alpha) * this.metrics.audioLatency;
  }

  /**
   * Record transcription latency
   */
  recordTranscriptionLatency(latencyMs: number): void {
    // Use exponential moving average
    const alpha = 0.3;
    this.metrics.transcriptionLatency =
      alpha * latencyMs + (1 - alpha) * this.metrics.transcriptionLatency;
  }

  /**
   * Record buffer fill level
   */
  recordBufferFill(fillPercentage: number): void {
    this.metrics.bufferFill = fillPercentage;
  }

  /**
   * Record reconnection
   */
  recordReconnection(): void {
    this.reconnectionCount++;
    this.metrics.reconnectionCount = this.reconnectionCount;
  }

  /**
   * Update memory usage (if available)
   */
  updateMemory(memoryMB: number): void {
    this.metrics.memory = memoryMB;
  }

  /**
   * Update CPU usage (if available)
   */
  updateCPU(cpuPercentage: number): void {
    this.metrics.cpu = cpuPercentage;
  }

  /**
   * Get current metrics
   */
  getMetrics(): Readonly<PerformanceMetrics> {
    return { ...this.metrics };
  }

  /**
   * Get metrics snapshot with history
   */
  getSnapshot(): PerformanceSnapshot {
    return {
      metrics: { ...this.metrics },
      history: [...this.history],
    };
  }

  /**
   * Get average metrics over history
   */
  getAverageMetrics(): PerformanceMetrics {
    if (this.history.length === 0) {
      return this.createEmptyMetrics();
    }

    const sum = this.history.reduce(
      (acc, m) => ({
        cpu: acc.cpu + m.cpu,
        memory: acc.memory + m.memory,
        audioLatency: acc.audioLatency + m.audioLatency,
        transcriptionLatency: acc.transcriptionLatency + m.transcriptionLatency,
        messageRate: acc.messageRate + m.messageRate,
        bufferFill: acc.bufferFill + m.bufferFill,
        uptime: m.uptime, // Use latest
        reconnectionCount: m.reconnectionCount, // Use latest
        timestamp: m.timestamp, // Use latest
      }),
      this.createEmptyMetrics()
    );

    const count = this.history.length;

    return {
      cpu: sum.cpu / count,
      memory: sum.memory / count,
      audioLatency: sum.audioLatency / count,
      transcriptionLatency: sum.transcriptionLatency / count,
      messageRate: sum.messageRate / count,
      bufferFill: sum.bufferFill / count,
      uptime: sum.uptime,
      reconnectionCount: sum.reconnectionCount,
      timestamp: sum.timestamp,
    };
  }

  /**
   * Check if performance is healthy
   */
  isHealthy(): boolean {
    const metrics = this.metrics;

    // Check various health indicators
    if (metrics.audioLatency > 500) {
      console.warn('High audio latency:', metrics.audioLatency);
      return false;
    }

    if (metrics.transcriptionLatency > 1000) {
      console.warn('High transcription latency:', metrics.transcriptionLatency);
      return false;
    }

    if (metrics.bufferFill > 90) {
      console.warn('Buffer nearly full:', metrics.bufferFill);
      return false;
    }

    if (metrics.messageRate === 0 && metrics.uptime > 5000) {
      console.warn('No messages being sent');
      return false;
    }

    return true;
  }

  /**
   * Reset all metrics
   */
  reset(): void {
    this.metrics = this.createEmptyMetrics();
    this.history = [];
    this.messageCount = 0;
    this.lastMessageCount = 0;
    this.reconnectionCount = 0;
  }
}

/**
 * Export a singleton instance
 */
export const performanceMonitor = new PerformanceMonitor();
