import { useState, useEffect, useRef, useCallback } from 'react';

export interface ServerMessage {
  type: 'response' | 'transcription';
  text: string;
  audio?: string | null;
}

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<ServerMessage | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;
    let activeSocket: WebSocket | null = null;

    const clearRetry = () => {
      if (retryTimer.current) {
        clearTimeout(retryTimer.current);
        retryTimer.current = null;
      }
    };

    const scheduleReconnect = (connect: () => void) => {
      clearRetry();
      retryTimer.current = setTimeout(connect, 3000);
    };

    const connect = () => {
      if (cancelled) return;

      try {
        const socket = new WebSocket(url);
        activeSocket = socket;
        ws.current = socket;

        socket.onopen = () => {
          if (cancelled || ws.current !== socket) return;
          setIsConnected(true);
          clearRetry();
        };

        socket.onmessage = (event) => {
          if (cancelled || ws.current !== socket) return;
          try {
            setLastMessage(JSON.parse(event.data));
          } catch {
            // ignore malformed messages
          }
        };

        socket.onclose = () => {
          if (cancelled || ws.current !== socket) return;
          ws.current = null;
          setIsConnected(false);
          scheduleReconnect(connect);
        };

        socket.onerror = () => {
          socket.close();
        };
      } catch {
        setIsConnected(false);
        scheduleReconnect(connect);
      }
    };

    setIsConnected(false);
    connect();

    return () => {
      cancelled = true;
      clearRetry();
      if (ws.current === activeSocket) {
        ws.current = null;
      }
      activeSocket?.close();
    };
  }, [url]);

  const sendMessage = useCallback((data: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    }
  }, []);

  return { isConnected, sendMessage, lastMessage };
}
