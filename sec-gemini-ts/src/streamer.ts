/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import randomUUID from "./uuid";
import WebSocket from "isomorphic-ws";
import {EndPointsEnum, ResponseStatusEnum} from "./enum"
import {RoleEnum, MimeTypeEnum, MessageTypeEnum} from "./secgeminienums";
import { Message } from "./secgeminitypes";
type UserOnMessageCallback = (message: Message) => void;
type ReconnectCallback = (success: boolean, attempt: number) => void;
type ConnectionStatusCallback = (status: 'connecting' | 'connected' | 'disconnected' | 'reconnecting') => void;

// Configuration constants
const DEFAULT_CONFIG = {
  INITIAL_RECONNECT_DELAY: 1000,
  MAX_RECONNECT_ATTEMPTS: 5,
  CONNECTION_CHECK_INTERVAL: 1000, // 1s
  CONNECTION_TIMEOUT: 60000, // 60 seconds
  PING_INTERVAL: 30000, // 30 seconds
};

interface StreamerConfig {
  maxReconnectAttempts?: number;
  initialReconnectDelay?: number;
  connectionTimeout?: number;
  connectionCheckInterval?: number;
  pingInterval?: number;
  onReconnect?: ReconnectCallback;
  onConnectionStatusChange?: ConnectionStatusCallback;
}

class Streamer {
    private ws: WebSocket;
    private url: string;
    private userOnOpen: CallableFunction | null;
    private userOnMessage: UserOnMessageCallback;
    private userOnError: CallableFunction | null;
    private userOnClose: CallableFunction | null;
    private onReconnect: ReconnectCallback | null;
    private connectionStatusCallback: ConnectionStatusCallback | null;
    public hasError: boolean = false;
    private apiKey: string;
    private sessionID: string;
    private isReconnecting: boolean = false;
    private messageQueue: {prompt: string, parentId?: string}[] = [];

    // Reconnect logic
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number;
    private reconnectDelay: number;
    private connectionTimeout: number;
    private connectionCheckInterval: number;
    private connectionTimer: NodeJS.Timeout | null = null;
    private pingIntervalId: NodeJS.Timeout | null = null;
    private pingInterval: number;

    public static async create(
        onmessage: UserOnMessageCallback,
        onopen: CallableFunction | null = null,
        onerror: CallableFunction | null = null,
        onclose: CallableFunction | null = null,
        websocket_url: string,
        sessionID: string,
        apiKey: string,
        config: StreamerConfig = {}
    ) {
        const streamer = new Streamer(onmessage, onopen, onerror, onclose, websocket_url, sessionID, apiKey, config);
        await streamer.connect();
        console.log("Waiting for WebSocket to OPEN...");

        return new Promise<Streamer>((resolve, reject) => {
            // Set a timeout for connection
            const timeout = setTimeout(() => {
                reject(new Error(`Connection timeout after ${streamer.connectionTimeout}ms`));
            }, streamer.connectionTimeout);

            // Define success handler for connection
            const checkConnection = () => {
                if (streamer.ws.readyState === WebSocket.OPEN) {
                    clearTimeout(timeout);
                    console.log("WebSocket OPEN");
                    resolve(streamer);
                } else if (streamer.hasError) {
                    clearTimeout(timeout);
                    reject(new Error("WebSocket connection failed."));
                } else {
                    setTimeout(checkConnection, streamer.connectionCheckInterval);
                }
            };

            checkConnection();
        });
    }

    private constructor(
        onmessage: UserOnMessageCallback,
        onopen: CallableFunction | null,
        onerror: CallableFunction | null,
        onclose: CallableFunction | null,
        websocket_url: string,
        sessionID: string,
        apiKey: string,
        config: StreamerConfig = {}
    ) {
        // Set user defined callbacks
        this.userOnOpen = onopen;
        this.userOnMessage = onmessage;
        this.userOnError = onerror;
        this.userOnClose = onclose;
        this.onReconnect = config.onReconnect || null;
        this.connectionStatusCallback = config.onConnectionStatusChange || null;
        this.sessionID = sessionID;
        this.apiKey = apiKey;

        // Set configuration
        this.maxReconnectAttempts = config.maxReconnectAttempts || DEFAULT_CONFIG.MAX_RECONNECT_ATTEMPTS;
        this.reconnectDelay = config.initialReconnectDelay || DEFAULT_CONFIG.INITIAL_RECONNECT_DELAY;
        this.connectionTimeout = config.connectionTimeout || DEFAULT_CONFIG.CONNECTION_TIMEOUT;
        this.connectionCheckInterval = config.connectionCheckInterval || DEFAULT_CONFIG.CONNECTION_CHECK_INTERVAL;
        this.pingInterval = config.pingInterval || DEFAULT_CONFIG.PING_INTERVAL;

        // Create websocket URL
        this.url = `${websocket_url}${EndPointsEnum.STREAM}?api_key=${apiKey}&session_id=${sessionID}`;
        console.log("Connecting to: ", this.url);
    }

    private async connect() {
        this.updateConnectionStatus('connecting');

        // Connect or reconnect to the websocket
        this.ws = new WebSocket(this.url);
        this.ws.onopen = this.onOpen.bind(this);
        this.ws.onmessage = this.onMessage.bind(this);
        this.ws.onerror = this.onError.bind(this);
        this.ws.onclose = this.onClose.bind(this);

        // Set connection timeout
        if (this.connectionTimer) {
            clearTimeout(this.connectionTimer);
        }

        this.connectionTimer = setTimeout(() => {
            if (this.ws.readyState !== WebSocket.OPEN) {
                this.handleConnectionTimeout();
            }
        }, this.connectionTimeout);
    }

    private setupHeartbeat() {
        if (this.pingIntervalId) {
            clearInterval(this.pingIntervalId);
        }

        this.pingIntervalId = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                // Use standard ping for FastAPI compatibility if available
                if (typeof this.ws.ping === 'function') {
                    this.ws.ping();
                }
            }
        }, this.pingInterval);
    }

    private handleConnectionTimeout() {
        this.hasError = true;
        if (this.ws.readyState !== WebSocket.CLOSED && this.ws.readyState !== WebSocket.CLOSING) {
            this.ws.close();
        }
        this.updateConnectionStatus('disconnected');
        this.notifyError(new Error(`Connection timeout after ${this.connectionTimeout}ms`));
    }

    public async send(prompt: string, parentId?: string): Promise<void> {
        // If not connected, queue the message if attempting to reconnect
        if (this.ws.readyState !== WebSocket.OPEN) {
            if (this.isReconnecting) {
                this.messageQueue.push({prompt, parentId});
                return Promise.resolve(); // Will be sent after reconnection
            }
            return Promise.reject(new Error("WebSocket is not connected."));
        }

        return new Promise((resolve, reject) => {
            try {
                // Validate input
                if (!prompt || typeof prompt !== 'string') {
                    throw new Error("Invalid prompt: must be a non-empty string");
                }

                const message: Message = {
                    id: randomUUID(),
                    parent_id: parentId || '3713', // Use provided parentId or default
                    role: RoleEnum.USER,
                    mime_type: MimeTypeEnum.TEXT_PLAIN,
                    message_type: MessageTypeEnum.QUERY,
                    content: prompt,
                    order: 0,
                    status_code: ResponseStatusEnum.OK,
                    status_message: '',
                    usage: null,
                };

                const serializedMessage = JSON.stringify(message);

                this.ws.send(serializedMessage);
                resolve();
            } catch (error) {
                reject(error);
            }
        });
    }

    public async close() {
        // Clear all timers
        if (this.connectionTimer) {
            clearTimeout(this.connectionTimer);
            this.connectionTimer = null;
        }

        if (this.pingIntervalId) {
            clearInterval(this.pingIntervalId);
            this.pingIntervalId = null;
        }

        if (this.ws) {
            try {
                if (this.ws.readyState === WebSocket.OPEN) {
                    await this.ws.close(1000, "Normal closure");
                }
            } catch (err) {
                console.error("Error closing WebSocket:", err);
            } finally {
                // Clean up reference
                this.ws.onopen = null;
                this.ws.onmessage = null;
                this.ws.onerror = null;
                this.ws.onclose = null;
            }
        }

        this.updateConnectionStatus('disconnected');
    }

    public resetErrorState() {
        this.hasError = false;
        this.reconnectAttempts = 0;
        this.reconnectDelay = DEFAULT_CONFIG.INITIAL_RECONNECT_DELAY;
    }

    public isConnected(): boolean {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    private updateConnectionStatus(status: 'connecting' | 'connected' | 'disconnected' | 'reconnecting') {
        if (this.connectionStatusCallback) {
            this.connectionStatusCallback(status);
        }
    }

    private async onOpen(event: WebSocket.OpenEvent) {
        this.reconnectAttempts = 0; // Reset reconnection attempts
        this.reconnectDelay = DEFAULT_CONFIG.INITIAL_RECONNECT_DELAY; // Reset reconnection delay
        this.hasError = false; // Reset error state
        this.isReconnecting = false;
        this.updateConnectionStatus('connected');

        if (this.connectionTimer) {
            clearTimeout(this.connectionTimer);
            this.connectionTimer = null;
        }

        // Setup heartbeat for keeping connection alive
        this.setupHeartbeat();

        // Process any queued messages
        while (this.messageQueue.length > 0) {
            const msg = this.messageQueue.shift();
            if (msg) {
                try {
                    await this.send(msg.prompt, msg.parentId);
                } catch (error) {
                    console.error("Failed to send queued message:", error);
                }
            }
        }

        if (this.userOnOpen) {
            this.userOnOpen(event);
        }
    }

    private async onMessage(event: WebSocket.MessageEvent) {
        try {
            const receivedData = event.data;
            if (typeof receivedData === "string") {
                if (receivedData.includes("not found")) {
                    console.error("Session not found. Closing connection.");
                    this.hasError = true;
                    this.notifyError(new Error("Session not found"));
                    this.ws.close();
                    return;
                }
                const message: Message = JSON.parse(receivedData);
                this.userOnMessage(message);
            } else {
                // should never happen
                console.warn("Binary message received", receivedData);
                this.notifyError(new Error("Unexpected binary message received"));
            }
        } catch (error) {
            console.error("Error parsing or handling message:", error);
            this.notifyError(error instanceof Error ? error : new Error("Unknown error processing message"));
        }
    }

    private async onError(event: WebSocket.ErrorEvent) {
        console.error("WebSocket error:", event);
        this.hasError = true;

        if (this.connectionTimer) {
            clearTimeout(this.connectionTimer);
            this.connectionTimer = null;
        }

        if (this.pingIntervalId) {
            clearInterval(this.pingIntervalId);
            this.pingIntervalId = null;
        }

        this.updateConnectionStatus('disconnected');

        if (this.userOnError) {
            this.userOnError(event);
        }
    }

    private onClose(event: WebSocket.CloseEvent) {
        if (this.connectionTimer) {
            clearTimeout(this.connectionTimer);
            this.connectionTimer = null;
        }

        if (this.pingIntervalId) {
            clearInterval(this.pingIntervalId);
            this.pingIntervalId = null;
        }

        if (this.userOnClose) {
            this.userOnClose(event);
        }

        // Handle FastAPI-specific close codes
        if (event.code === 1000) {
            // Normal closure, no reconnection needed
            console.log("WebSocket closed normally");
            this.updateConnectionStatus('disconnected');
            this.hasError = false;
            // No reconnection for normal closure
            return;
        }

        if (!this.hasError && !this.isReconnecting && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.isReconnecting = true;
            this.updateConnectionStatus('reconnecting');
            console.log(`Chat connection lost. Reconnecting (attempt ${this.reconnectAttempts + 1})...`);

            setTimeout(() => {
                this.reconnectAttempts++;
                this.reconnectDelay *= 2; // Exponential backoff
                this.connect().then(() => {
                    if (this.onReconnect && this.ws.readyState === WebSocket.OPEN) {
                        this.onReconnect(true, this.reconnectAttempts);
                    }
                }).catch((error) => {
                    this.isReconnecting = false;
                    this.updateConnectionStatus('disconnected');
                    if (this.onReconnect) {
                        this.onReconnect(false, this.reconnectAttempts);
                    }
                    this.notifyError(error);
                });
            }, this.reconnectDelay);
        } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.isReconnecting = false;
            this.updateConnectionStatus('disconnected');
            console.error("Max reconnection attempts reached.");
            if (this.onReconnect) {
                this.onReconnect(false, this.reconnectAttempts);
            }
            this.notifyError(new Error("Max reconnection attempts reached"));
        }
    }

    private notifyError(error: Error) {
        if (this.userOnError) {
            this.userOnError(error);
        }
    }
}

export default Streamer;
