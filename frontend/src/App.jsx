import React from "react";
import { HashRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import { LiveSocketProvider, useLiveSocketContext } from "./context/LiveSocketContext";
import Header from "./components/layout/Header";

import OverviewPage from "./pages/OverviewPage";
import DevCollabPage from "./pages/DevCollabPage";
import AIOpsPage from "./pages/AIOpsPage";

function AppShell() {
  const { connected } = useLiveSocketContext();

  return (
    <div className="min-h-screen bg-base-bg text-ink-primary">
      <Header connected={connected} />
      <main>
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/dev-collab" element={<DevCollabPage />} />
          <Route path="/aiops" element={<AIOpsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <LiveSocketProvider>
          <HashRouter>
            <AppShell />
          </HashRouter>
        </LiveSocketProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
