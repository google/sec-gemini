// src/streamer.ts (Corrected and Complete)

/**
 * Copyright 2025 Google LLC
 * ... (License Header) ...
 */

import randomUUID from './uuid';
import WebSocket from 'isomorphic-ws'; // Use isomorphic-ws for compatibility
import { EndPointsEnum, ResponseStatusEnum } from './enum';
import { RoleEnum, MimeTypeEnum, MessageTypeEnum } from './secgeminienums';
import { Message, Role, MimeType } from './secgeminitypes';

const ROOT_MESSAGE_ID = '3713';

type UserOnMessageCallback = (message: Message) => void;
type ReconnectCallback = (success: boolean, attempt: number) => void;
type ConnectionStatusCallback = (
  status: 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'
) => void;

const DEFAULT_CONFIG = {
  INITIAL_RECONNECT_DELAY: 1000, // ms
  MAX_RECONNECT_ATTEMPTS: 5,
  CONNECTION_TIMEOUT: 15000, // ms
  PING_INTERVAL: 20000, // ms
};

interface StreamerConfig {
  maxReconnectAttempts?: number;
  initialReconnectDelay?: number;
  connectionTimeout?: number;
  pingInterval?: number;
  onReconnect?: ReconnectCallback;
  onConnectionStatusChange?: ConnectionStatusCallback;
}

class Streamer {
  private ws: WebSocket | null = null;
  private readonly url: string;
  private readonly userOnOpen: (() => void) | null;
  private readonly userOnMessage: UserOnMessageCallback;
  // Error callback receives Error object (or potentially WebSocket.ErrorEvent)
  private readonly userOnError: ((error: Error) => void) | null;
  private readonly userOnClose: ((event: WebSocket.CloseEvent) => void) | null;
  private readonly onReconnect: ReconnectCallback | null;
  private readonly connectionStatusCallback: ConnectionStatusCallback | null;
  public hasError: boolean = false;
  private readonly apiKey: string;
  private readonly sessionID: string;
  private isReconnecting: boolean = false;
  private messageQueue: { prompt: string; parentId?: string }[] = [];

  private reconnectAttempts: number = 0;
  private currentReconnectDelay: number;

  private readonly maxReconnectAttempts: number;
  private readonly initialReconnectDelay: number;
  private readonly connectionTimeout: number;
  private readonly pingInterval: number;

  private connectionTimeoutId: number | NodeJS.Timeout | null = null;
  private pingIntervalId: number | NodeJS.Timeout | null = null;

  public static async create(
    onmessage: UserOnMessageCallback,
    onopen: (() => void) | null = null,
    onerror: ((error: Error) => void) | null = null, // Expect Error object
    onclose: ((event: WebSocket.CloseEvent) => void) | null = null,
    websocketUrl: string,
    sessionID: string,
    apiKey: string,
    config: StreamerConfig = {}
  ): Promise<Streamer> {
    if (!websocketUrl.match(/^wss?:\/\//)) {
      throw new Error(`Invalid WebSocket URL: ${websocketUrl}. Must start with ws:// or wss://`);
    }
    const streamer = new Streamer(onmessage, onopen, onerror, onclose, websocketUrl, sessionID, apiKey, config);

    return new Promise<Streamer>((resolve, reject) => {
      const tempOnOpen = () => {
        cleanUpTempHandlers();
        console.info('Streamer: WebSocket connected successfully.');
        resolve(streamer);
      };

      const tempOnError = (eventOrError: WebSocket.ErrorEvent | Error) => {
        cleanUpTempHandlers();
        const error =
          eventOrError instanceof Error
            ? eventOrError
            : new Error(
                `WebSocket connection error: ${(eventOrError as WebSocket.ErrorEvent).message || (eventOrError as Event).type || 'Unknown WS Error'}`
              );
        console.error('Streamer: WebSocket connection failed.', error);
        reject(error);
      };

      streamer.connectionTimeoutId = setTimeout(() => {
        cleanUpTempHandlers();
        const error = new Error(`Streamer: Connection timeout after ${streamer.connectionTimeout}ms`);
        console.error(error.message);
        if (streamer.ws && streamer.ws.readyState === WebSocket.CONNECTING) {
          streamer.ws.close(4000, 'Connection Timeout');
        }
        reject(error);
      }, streamer.connectionTimeout);

      const cleanUpTempHandlers = () => {
        if (streamer.connectionTimeoutId) {
          clearTimeout(streamer.connectionTimeoutId);
          streamer.connectionTimeoutId = null;
        }
        if (streamer.ws) {
          streamer.ws.removeEventListener('open', tempOnOpen as any);
          streamer.ws.removeEventListener('error', tempOnError as any);
        }
      };

      try {
        streamer.connect(tempOnOpen, tempOnError);
        resolve(streamer);
      } catch (error) {
        cleanUpTempHandlers();
        reject(error);
      }
    });
  }

  private constructor(
    onmessage: UserOnMessageCallback,
    onopen: (() => void) | null,
    onerror: ((error: Error) => void) | null, // Expect Error object
    onclose: ((event: WebSocket.CloseEvent) => void) | null,
    websocketUrl: string,
    sessionID: string,
    apiKey: string,
    config: StreamerConfig = {}
  ) {
    this.userOnMessage = onmessage;
    this.userOnOpen = onopen;
    this.userOnError = onerror;
    this.userOnClose = onclose;
    this.sessionID = sessionID;
    this.apiKey = apiKey;

    this.maxReconnectAttempts = config.maxReconnectAttempts ?? DEFAULT_CONFIG.MAX_RECONNECT_ATTEMPTS;
    this.initialReconnectDelay = config.initialReconnectDelay ?? DEFAULT_CONFIG.INITIAL_RECONNECT_DELAY;
    this.connectionTimeout = config.connectionTimeout ?? DEFAULT_CONFIG.CONNECTION_TIMEOUT;
    this.pingInterval = config.pingInterval ?? DEFAULT_CONFIG.PING_INTERVAL;
    this.onReconnect = config.onReconnect ?? null;
    this.connectionStatusCallback = config.onConnectionStatusChange ?? null;

    this.currentReconnectDelay = this.initialReconnectDelay;

    const path = EndPointsEnum.STREAM;
    const endpointPath = path.startsWith('/') ? path.substring(1) : path;
    const baseUrlClean = websocketUrl.replace(/\/$/, '');
    this.url = `${baseUrlClean}/${endpointPath}?api_key=${this.apiKey}&session_id=${this.sessionID}`;

    console.debug('Streamer: Target URL:', this.url);
  }

  // Callers need to handle removing temporary open/error listeners themselves.
  private connect(tempOnOpen?: () => void, tempOnError?: (eventOrError: WebSocket.ErrorEvent | Error) => void) {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      console.warn('Streamer: connect called while already connecting or open.');
      return;
    }

    this.updateConnectionStatus('connecting');
    console.debug('Streamer: Attempting to connect...');

    try {
      this.ws = new WebSocket(this.url);

      // Assign permanent handlers using bound methods
      this.ws.onopen = this.onOpen.bind(this);
      this.ws.onmessage = this.onMessage.bind(this);
      this.ws.onerror = this.onError.bind(this);
      this.ws.onclose = this.onClose.bind(this);

      // Add temporary listeners if provided
      if (tempOnOpen) this.ws.addEventListener('open', tempOnOpen as any);
      if (tempOnError) this.ws.addEventListener('error', tempOnError as any);
    } catch (error) {
      console.error('Streamer: Error creating WebSocket instance.', error);
      this.updateConnectionStatus('error');
      this.notifyError(error instanceof Error ? error : new Error('WebSocket constructor failed'));
      throw error;
    }
  }

  private setupHeartbeat() {
    this.clearPingInterval();

    this.pingIntervalId = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        if (typeof this.ws.ping === 'function') {
          // Add optional callback for Node.js `ws` library compatibility if needed
          this.ws.ping(() => {});
        }
      }
    }, this.pingInterval);
    console.debug('Streamer: Heartbeat interval set up.');
  }

  public async send(prompt: string, parentId?: string): Promise<void> {
    const state = this.ws ? this.ws.readyState : '';
    if (this.isReconnecting || state === WebSocket.CONNECTING) {
      console.debug('Streamer: Queuing message during reconnect:', prompt.substring(0, 30) + '...');
      this.messageQueue.push({ prompt, parentId });
      return;
    } else if (state !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected.');
    }
    const currentWs = this.ws!;

    if (!prompt || typeof prompt !== 'string') {
      throw new Error('Invalid prompt: must be a non-empty string');
    }

    const message: Message = {
      id: randomUUID(),
      parent_id: parentId || ROOT_MESSAGE_ID,
      role: RoleEnum.USER as Role,
      mime_type: MimeTypeEnum.TEXT_PLAIN as MimeType,
      message_type: MessageTypeEnum.QUERY,
      content: prompt,
    };

    try {
      const serializedMessage = JSON.stringify(message);
      currentWs.send(serializedMessage);
    } catch (error) {
      console.error('Streamer: Error sending message:', error);
      this.notifyError(error instanceof Error ? error : new Error('Failed to send message'));
    }
  }

  public close(code: number = 1000, reason: string = 'Normal closure'): void {
    this.clearConnectionTimeout();
    this.clearPingInterval();
    this.isReconnecting = false;

    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        console.info(`Streamer: Closing WebSocket connection (Code: ${code}, Reason: ${reason})`);
        try {
          this.ws.close(code, reason);
        } catch (err) {
          console.error('Streamer: Error initiating WebSocket close:', err);
        }
      }
      this.cleanupWebSocketHandlers(); // Clean up handlers after initiating close
    } else {
      console.debug('Streamer: close called but no WebSocket instance exists.');
    }
  }

  public isConnected(): boolean {
    return !!this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  private updateConnectionStatus(status: 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error') {
    if (this.connectionStatusCallback) {
      try {
        this.connectionStatusCallback(status);
      } catch (error) {
        console.error("Streamer: Error in user 'onConnectionStatusChange' callback:", error);
      }
    }
  }

  private onOpen(/*event: WebSocket.OpenEvent*/): void {
    console.info('Streamer: WebSocket connection opened.');
    this.resetReconnectionState();
    this.updateConnectionStatus('connected');
    this.clearConnectionTimeout();
    this.setupHeartbeat();
    this.processMessageQueue();
    if (this.userOnOpen) {
      try {
        this.userOnOpen();
      } catch (e) {
        console.error('Err in onOpen', e);
      }
    }
  }

  private onMessage(event: WebSocket.MessageEvent): void {
    try {
      let receivedData: string;
      if (typeof event.data === 'string') {
        receivedData = event.data;
      } else if (typeof Buffer !== 'undefined' && event.data instanceof Buffer) {
        receivedData = event.data.toString('utf-8');
      } else if (typeof ArrayBuffer !== 'undefined' && event.data instanceof ArrayBuffer) {
        receivedData = new TextDecoder().decode(event.data);
      } else if (typeof Blob !== 'undefined' && event.data instanceof Blob) {
        throw new Error('Streamer: Received Blob message, async handling needed.');
      } else {
        throw new Error(`Streamer: Received message of unknown type: ${typeof event.data}`);
      }

      const message: Message = JSON.parse(receivedData);
      if (!message || typeof message !== 'object' || !message.message_type) {
        throw new Error(`Streamer: Received data doesn't look like a valid Message: ${message}`);
      }
      if ('status_message' in message && message['status_message']!.includes('not found')) {
        console.error('Streamer: Session not found message received. Closing.');
        this.hasError = true;
        this.notifyError(new Error('Session not found on server'));
        this.close(4001, 'Session Not Found');
        return;
      }
      this.userOnMessage(message);
    } catch (error) {
      console.error('Streamer: Error parsing/handling incoming message:', error);
      this.notifyError(error instanceof Error ? error : new Error('Unknown error processing message'));
    }
  }

  // Node 'ws' onerror provides Error, browser provides Event. Normalize to Error.
  private onError(errorOrEvent: WebSocket.ErrorEvent | Error): void {
    const error =
      errorOrEvent instanceof Error
        ? errorOrEvent
        : new Error(
            `WebSocket error: ${(errorOrEvent as WebSocket.ErrorEvent).message || (errorOrEvent as Event).type}`
          );
    console.error('Streamer: WebSocket error occurred.', error);
    this.hasError = true;
    this.clearConnectionTimeout();
    this.clearPingInterval();
    this.updateConnectionStatus('error');
    this.notifyError(error); // Pass the normalized Error object
  }

  private onClose(event: WebSocket.CloseEvent): void {
    console.info(
      `Streamer: WebSocket connection closed. Code: ${event.code}, Reason: "${event.reason}", Clean: ${event.wasClean}`
    );
    this.clearConnectionTimeout();
    this.clearPingInterval();

    if (this.userOnClose) {
      try {
        this.userOnClose(event);
      } catch (e) {
        console.error('Err in onClose', e);
      }
    }

    // TODO: I think we should reconnect even if there is an error?
    const shouldAttemptReconnect =
      event.code !== 1000 &&
      event.code !== 4001 &&
      this.reconnectAttempts < this.maxReconnectAttempts &&
      !this.isReconnecting;

    if (shouldAttemptReconnect) {
      this.attemptReconnection();
    } else {
      if (event.code === 1000) {
        console.info('Streamer: Normal closure.');
      } else if (event.code === 4001) {
        console.info(`Streamer: web socket closed with ${event.code}: ${event.reason}`);
      } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.log(
          `Max reconnect attempts: ${this.maxReconnectAttempts}, reconnect attempts: ${this.reconnectAttempts}`
        );
        if (!this.hasError) {
          this.notifyError(new Error('Max reconnection attempts reached'));
        }
      }
      this.isReconnecting = false;
      this.updateConnectionStatus('disconnected');
      this.ws = null;
    }
  }

  private attemptReconnection(): void {
    this.isReconnecting = true;
    this.reconnectAttempts++;
    this.updateConnectionStatus('reconnecting');
    const delay = this.currentReconnectDelay;
    console.info(
      `Streamer: Connection lost. Reconnecting in ${delay}ms (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
    );
    // Create temp variable because this.reconnectAttempts is reset in the main onOpen handler.
    const reconnectAttempts = this.reconnectAttempts;

    setTimeout(() => {
      if (!this.isReconnecting) {
        console.info('Streamer: Reconnection cancelled.');
        return;
      }
      const tempOnOpen = () => {
        cleanUpTempHandlers();
        console.info(`Streamer: Reconnection successful (Attempt ${reconnectAttempts})`);
        this.isReconnecting = false;
        if (this.onReconnect) this.onReconnect(true, reconnectAttempts);
      };

      const tempOnError = (eventOrError: WebSocket.ErrorEvent | Error) => {
        cleanUpTempHandlers();
        console.error(`Streamer: Reconnection attempt ${reconnectAttempts} failed.`);
        this.isReconnecting = false; // Ready for next attempt or failure
        this.ws = null; // Ensure WS is null on failed attempt
        this.currentReconnectDelay = Math.min(delay * 2, 30000); // Use previous delay for backoff calc
        if (this.onReconnect) this.onReconnect(false, reconnectAttempts);
        this.updateConnectionStatus('disconnected');
        // Trigger onClose manually to potentially drive the next attempt if needed
        // Create a basic event object, exact properties might not matter here
        this.onClose({
          code: 1006,
          reason: 'Reconnect Failed',
          wasClean: false,
          target: this.ws,
        } as WebSocket.CloseEvent);
      };

      const cleanUpTempHandlers = () => {
        if (this.ws) {
          this.ws.removeEventListener('open', tempOnOpen as any);
          this.ws.removeEventListener('error', tempOnError as any);
        }
      };
      try {
        this.connect(tempOnOpen, tempOnError);
      } catch (error) {
        cleanUpTempHandlers();
        console.error(`Streamer: Error during reconnection attempt ${this.reconnectAttempts}`, error);
        this.isReconnecting = false;
        this.updateConnectionStatus('disconnected');
        if (this.onReconnect) this.onReconnect(false, this.reconnectAttempts);
        this.onClose({
          code: 1006,
          reason: 'Reconnect Exception',
          wasClean: false,
          target: this.ws,
        } as WebSocket.CloseEvent);
      }
    }, delay);
  }

  private async processMessageQueue(): Promise<void> {
    console.debug(`Streamer: Processing message queue (${this.messageQueue.length} items)...`);
    const processingQueue = [...this.messageQueue];
    this.messageQueue = [];

    const sendPromises = processingQueue.map((msg) =>
      this.send(msg.prompt, msg.parentId).catch((error) => {
        console.error('Streamer: Failed to send queued message:', error);
      })
    );
    await Promise.allSettled(sendPromises);
    console.debug('Streamer: Message queue processed.');
  }

  private resetReconnectionState(): void {
    this.reconnectAttempts = 0;
    this.currentReconnectDelay = this.initialReconnectDelay;
    this.hasError = false;
    this.isReconnecting = false;
  }

  private cleanupWebSocketHandlers(): void {
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onerror = null;
      this.ws.onclose = null;
    }
  }

  private clearConnectionTimeout(): void {
    if (this.connectionTimeoutId) {
      clearTimeout(this.connectionTimeoutId);
      this.connectionTimeoutId = null;
    }
  }

  private clearPingInterval(): void {
    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
      this.pingIntervalId = null;
      console.debug('Streamer: Heartbeat interval cleared.');
    }
  }

  // Completed notifyError method
  private notifyError(error: Error | WebSocket.ErrorEvent) {
    // Ensure we always pass an Error object to the user callback
    const errorObj =
      error instanceof Error
        ? error
        : new Error(
            `WebSocket Event: ${(error as WebSocket.ErrorEvent).message || (error as Event).type || 'Unknown WS Error'}`
          );
    if (this.userOnError) {
      try {
        // Pass the normalized Error object
        this.userOnError(errorObj);
      } catch (e) {
        // Catch errors that happen *inside* the user's callback
        console.error("Streamer: Error occurred within user 'onerror' callback:", e);
      }
    }
  }
} // End of Streamer class

export default Streamer;
