import { WS_URL } from './constants';

export type WebSocketEvent =
  | 'PATIENT_UPDATED'
  | 'QUEUE_UPDATED'
  | 'ALERT_CREATED'
  | 'DETERIORATION'
  | 'CAPACITY_UPDATED'
  | 'OVERRIDE_APPLIED'
  | 'CONNECTED'
  | 'SYSTEM';

export interface WebSocketMessage {
  event: WebSocketEvent;
  patientId?: string;
  previousPriority?: string;
  newPriority?: string;
  deteriorating?: boolean;
  safetyFlags?: string[];
  reason?: string;
  severity?: string;
  message?: string;
  [key: string]: unknown;
}

export type WebSocketListener = (message: WebSocketMessage) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Set<WebSocketListener> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;
  public connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error' = 'disconnected';

  connect() {
    if (typeof window === 'undefined') return;
    this.shouldReconnect = true;
    this.connectionStatus = 'connecting';
    try {
      this.ws = new WebSocket(WS_URL);

      this.ws.onopen = () => {
        this.connectionStatus = 'connected';
        this.notifyListeners({ event: 'CONNECTED', message: 'Connected' });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketMessage;
          this.notifyListeners(data);
        } catch {}
      };

      this.ws.onclose = () => {
        this.connectionStatus = 'disconnected';
        if (this.shouldReconnect) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = () => {
        this.connectionStatus = 'error';
      };
    } catch {
      this.connectionStatus = 'error';
      this.scheduleReconnect();
    }
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectionStatus = 'disconnected';
  }

  addListener(listener: WebSocketListener) {
    this.listeners.add(listener);
  }

  removeListener(listener: WebSocketListener) {
    this.listeners.delete(listener);
  }

  private notifyListeners(message: WebSocketMessage) {
    this.listeners.forEach((l) => l(message));
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => this.connect(), 5000);
  }
}

export const wsClient = new WebSocketClient();
