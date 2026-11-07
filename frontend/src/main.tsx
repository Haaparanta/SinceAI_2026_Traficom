import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { applyTheme, currentTheme } from "./theme";

// The theme switches with the .dark class: dark by default, light when chosen in ThemeSwitch.
applyTheme(currentTheme());

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary label="page">
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
