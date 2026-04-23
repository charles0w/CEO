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
  const urlRef = useRef(url);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    try {
      const socket = new WebSocket(urlRef.current);

      socket.onopen = () => {
        setIsConnected(true);
        if (retryTimer.current) clearTimeout(retryTimer.current);
      };

      socket.onmessage = (event) => {
        try {
          setLastMessage(JSON.parse(event.data));
        } catch {
          // ignore malformed messages
        }
      };

      socket.onclose = () => {
        setIsConnected(false);
        retryTimer.current = setTimeout(connect, 3000);
      };

      socket.onerror = () => {
        socket.close();
      };

      ws.current = socket;
    } catch {
      retryTimer.current = setTimeout(connect, 3000);
    }
  }, []);

  useEffect(() => {
    urlRef.current = url;
    ws.current?.close();
    connect();
  }, [url, connect]);

  useEffect(() => {
    connect();
    return () => {
      if (retryTimer.current) clearTimeout(retryTimer.current);
      ws.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((data: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    }
  }, []);

  return { isConnected, sendMessage, lastMessage };
}
