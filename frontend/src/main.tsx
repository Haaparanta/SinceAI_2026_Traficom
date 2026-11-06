import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import { applyTheme, currentTheme } from "./theme";

// The theme switches with the .dark class: the user's choice (ThemeSwitch), otherwise the operating system setting.
applyTheme(currentTheme());

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
