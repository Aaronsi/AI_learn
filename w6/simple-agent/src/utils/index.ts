/**
 * Utility functions
 */

import { v4 as uuidv4 } from "uuid";

/**
 * Generate a unique ID
 */
export function generateId(): string {
  return uuidv4();
}

/**
 * Sleep for a given duration
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry a function with exponential backoff
 */
export interface RetryConfig {
  maxRetries: number;
  baseDelay: number; // milliseconds
  maxDelay: number; // milliseconds
  retryableErrors?: string[]; // Error messages to retry on
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  config: RetryConfig
): Promise<T> {
  let lastError: Error;

  for (let i = 0; i <= config.maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      // Check if error is retryable
      if (config.retryableErrors && config.retryableErrors.length > 0) {
        const isRetryable = config.retryableErrors.some((errMsg) =>
          lastError.message.includes(errMsg)
        );
        if (!isRetryable) {
          throw lastError;
        }
      }

      // Don't sleep after the last retry
      if (i < config.maxRetries) {
        const delay = Math.min(
          config.baseDelay * Math.pow(2, i),
          config.maxDelay
        );
        await sleep(delay);
      }
    }
  }

  throw lastError!;
}
