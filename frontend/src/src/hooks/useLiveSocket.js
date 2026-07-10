import { useEffect, useRef, useState } from "react";
import { WS_URL } from "../services/apiClient";

/**
 * Connects to the backend's /ws/live endpoint and exposes the latest event.
 * Auto-reconnects if the connection drops (demo-safe: UI never gets stuck
 * on a dead socket).
 */
export function useLiveSocket() {
  const [lastEvent, setLastEvent] = useState(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    let reconnectTimer;

    function connect() {
      try {
        const socket = new WebSocket(WS_URL);
        socketRef.current = socket;

        socket.onopen = () => setConnected(true);
        socket.onclose = () => {
          setConnected(false);
          reconnectTimer = setTimeout(connect, 3000);
        };
        socket.onerror = () => socket.close();
        socket.onmessage = (event) => {
          try {
            setLastEvent(JSON.parse(event.data));
          } catch {
            // ignore malformed messages
          }
        };
      } catch {
        reconnectTimer = setTimeout(connect, 3000);
      }
    }

    connect();
    return () => {
      clearTimeout(reconnectTimer);
      socketRef.current?.close();
    };
  }, []);

  return { lastEvent, connected };
}
