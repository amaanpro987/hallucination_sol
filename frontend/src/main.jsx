import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App";
import Landing from "./pages/Landing";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<App />} />
        <Route path="/projects" element={<App />} />
        <Route path="/analytics" element={<App />} />
        <Route path="/reports" element={<App />} />
        <Route path="/docs" element={<App />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
