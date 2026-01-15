/**
 * RAFlow Application
 * Phase 1: Basic infrastructure and UI
 */

import './App.css';
import { FloatingWindow } from './components/raflow/FloatingWindow';
import { useEffect, useState } from 'react';
import { invoke, getTauriDebugInfo, isTauriEnvironment } from './utils/tauri';

function App() {
  const [isTauri, setIsTauri] = useState<boolean | null>(null);

  useEffect(() => {
    async function initialize() {
      try {
        // Log Tauri environment info
        const debugInfo = getTauriDebugInfo();
        console.log('Tauri environment:', debugInfo);
        
        const inTauri = isTauriEnvironment();
        setIsTauri(inTauri);
        
        // Check if we're in Tauri environment
        if (!inTauri) {
          console.error('⚠️ CRITICAL: Running in browser mode. Tauri APIs will not work.');
          console.error('Please run the app using: cargo tauri dev');
          console.error('Do NOT open http://localhost:1420 directly in a browser!');
          return;
        }

        console.log('✅ RAFlow initialized - Phase 1');

        // Test backend connection
        try {
          const state = await invoke<string>('get_recording_state');
          console.log('Initial recording state:', state);
        } catch (error) {
          console.error('Failed to connect to backend:', error);
        }
      } catch (error) {
        console.error('Failed to initialize:', error);
      }
    }

    initialize();
  }, []);

  // Show warning if not in Tauri environment
  if (isTauri === false) {
    return (
      <div className="w-full h-screen bg-red-50 dark:bg-red-900/20 flex items-center justify-center p-8">
        <div className="max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border-2 border-red-500">
          <h1 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">
            ⚠️ 运行环境错误
          </h1>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            应用当前在浏览器中运行，而不是在 Tauri 窗口中。
          </p>
          <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded mb-4">
            <p className="text-sm font-mono text-gray-800 dark:text-gray-200 mb-2">
              正确的启动方式：
            </p>
            <code className="text-sm bg-gray-800 text-green-400 p-2 rounded block">
              cargo tauri dev
            </code>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            <strong>不要</strong>直接在浏览器中打开{' '}
            <code className="bg-gray-200 dark:bg-gray-700 px-1 rounded">
              http://localhost:1420
            </code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-transparent">
      <FloatingWindow />
    </div>
  );
}

export default App;
