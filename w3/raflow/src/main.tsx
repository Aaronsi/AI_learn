import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// Note: React.StrictMode is disabled in development to avoid conflicts with Tauri's IPC initialization
// StrictMode causes components to mount twice which can interfere with Tauri event listeners
const isDev = import.meta.env.DEV;

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  isDev ? (
    <App />
  ) : (
    <React.StrictMode>
      <App />
    </React.StrictMode>
  )
);
