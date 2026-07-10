import React, { createContext, useContext } from "react";
import { useLiveSocket } from "../hooks/useLiveSocket";

const LiveSocketContext = createContext({ lastEvent: null, connected: false });

/**
 * Wraps the app with ONE shared WebSocket connection. Any page/component
 * can read the latest event via useLiveSocketContext() and react to it
 * (e.g. refetch data) without opening its own socket.
 */
export function LiveSocketProvider({ children }) {
  const socketState = useLiveSocket();
  return (
    <LiveSocketContext.Provider value={socketState}>
      {children}
    </LiveSocketContext.Provider>
  );
}

export function useLiveSocketContext() {
  return useContext(LiveSocketContext);
}
