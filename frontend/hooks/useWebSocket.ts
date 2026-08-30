'use client';
import { useEffect, useState, useCallback } from 'react';
import { wsClient, WebSocketMessage, WebSocketListener } from '@/lib/websocket';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error' | 'polling';

export function useWebSocket(onMessage?: WebSocketListener) {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');

  useEffect(() => {
    wsClient.connect();

    const statusInterval = setInterval(() => {
      const s = wsClient.connectionStatus;
      setStatus(s === 'connected' ? 'connected' : s === 'connecting' ? 'connecting' : 'polling');
    }, 1000);

    return () => {
      clearInterval(statusInterval);
    };
  }, []);

  useEffect(() => {
    if (!onMessage) return;
    wsClient.addListener(onMessage);
    return () => wsClient.removeListener(onMessage);
  }, [onMessage]);

  return { status };
}
