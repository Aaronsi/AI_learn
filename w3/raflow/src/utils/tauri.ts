/**
 * Tauri Utilities
 *
 * Helper functions for Tauri API usage in Tauri v2
 *
 * In Tauri v2, the IPC system is automatically initialized and
 * APIs can be imported directly without waiting for global objects.
 * However, we need to use dynamic imports to avoid loading Tauri APIs
 * in browser environments where they will fail.
 */

/**
 * Check if we're running in a Tauri environment
 * This is a simple runtime check, not a initialization check
 */
export function isTauriEnvironment(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  // In Tauri v2, check for the presence of Tauri internals
  try {
    // @ts-ignore - accessing Tauri internal
    const hasInternals = window.__TAURI_INTERNALS__ !== undefined;
    // @ts-ignore - accessing Tauri internal
    const hasInvoke = window.__TAURI_INVOKE__ !== undefined;
    // @ts-ignore - accessing Tauri internal
    const hasMetadata = window.__TAURI_METADATA__ !== undefined;
    
    return hasInternals || hasInvoke || hasMetadata;
  } catch {
    return false;
  }
}

// Cache for dynamically imported APIs
let tauriCoreModule: typeof import('@tauri-apps/api/core') | null = null;
let tauriEventModule: typeof import('@tauri-apps/api/event') | null = null;
let apiLoadPromise: Promise<void> | null = null;

/**
 * Ensure Tauri APIs are loaded (only in Tauri environment)
 */
async function ensureTauriAPIs(): Promise<void> {
  // Check environment first - this is synchronous and safe
  if (!isTauriEnvironment()) {
    const error = new Error(
      'Tauri APIs are not available. Make sure you are running the app using "cargo tauri dev", not in a browser.'
    );
    console.error(error.message);
    console.warn('Current environment:', {
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'N/A',
      location: typeof window !== 'undefined' ? window.location.href : 'N/A',
    });
    throw error;
  }

  // If already loaded, return immediately
  if (tauriCoreModule && tauriEventModule) {
    return;
  }

  // If currently loading, wait for it
  if (apiLoadPromise) {
    await apiLoadPromise;
    return;
  }

  // Start loading
  apiLoadPromise = (async () => {
    try {
      // Use dynamic imports to avoid loading in browser environment
      const [coreModule, eventModule] = await Promise.all([
        import('@tauri-apps/api/core'),
        import('@tauri-apps/api/event'),
      ]);
      
      tauriCoreModule = coreModule;
      tauriEventModule = eventModule;
    } catch (error) {
      console.error('Failed to import Tauri APIs:', error);
      throw new Error(
        `Failed to load Tauri APIs: ${error instanceof Error ? error.message : 'Unknown error'}. ` +
        'Make sure @tauri-apps/api is installed correctly and you are running in a Tauri window.'
      );
    }
  })();

  await apiLoadPromise;
}

/**
 * Invoke a Tauri command
 * In Tauri v2, invoke is always available in Tauri context
 */
export async function invoke<T>(command: string, args?: unknown): Promise<T> {
  await ensureTauriAPIs();
  
  if (!tauriCoreModule) {
    throw new Error('Tauri core API is not available');
  }

  try {
    return await tauriCoreModule.invoke<T>(command, args);
  } catch (error) {
    console.error(`Failed to invoke command '${command}':`, error);
    throw error;
  }
}

/**
 * Listen to a Tauri event
 * In Tauri v2, listen is always available in Tauri context
 */
export async function listen<T>(
  event: string,
  handler: (event: { payload: T }) => void
): Promise<() => void> {
  await ensureTauriAPIs();
  
  if (!tauriEventModule) {
    throw new Error('Tauri event API is not available');
  }

  try {
    return await tauriEventModule.listen<T>(event, handler);
  } catch (error) {
    console.error(`Failed to setup listener for event '${event}':`, error);
    throw error;
  }
}

/**
 * Get environment info for debugging
 */
export function getTauriDebugInfo(): Record<string, any> {
  if (typeof window === 'undefined') {
    return { environment: 'ssr', isTauri: false };
  }

  return {
    environment: 'browser',
    isTauri: isTauriEnvironment(),
    // @ts-ignore
    hasTauriInternals: typeof window.__TAURI_INTERNALS__ !== 'undefined',
    // @ts-ignore
    hasTauriInvoke: typeof window.__TAURI_INVOKE__ !== 'undefined',
    // @ts-ignore
    hasGlobalTauri: typeof window.__TAURI__ !== 'undefined',
  };
}
