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

import WebSocket from 'isomorphic-ws';

class CloseEvent extends Event {
  code = 0;
  reason = "";
  constructor(type: string, options: {code: number, reason: string}) {
    super(type, {});
    this.code = options.code;
    this.reason = options.reason;
  }
}

function getMockSocket(url: string, originalWebSocket: WebSocket, getSocketResponseMessage: Function, pingFn: Function) {
  if (url.startsWith("ws://badurl")) {
    throw new DOMException("Bad URL.");
  }
  const mockSocket = {
    _additionalErrorListeners: <Array<Function>>[],
    _additionalOpenListeners:  <Array<Function>>[],
    readyState: originalWebSocket.CONNECTING,
    removeEventListener: (type: string, listener: Function) => {
      let listeners;
      if (type === 'open') {
        listeners = mockSocket._additionalOpenListeners;
      } else if (type === 'error') {
        listeners = mockSocket._additionalErrorListeners;
      } else {
        throw new Error(`Listener type ${type} not implemented in mock object!`);
      }
      const idx = listeners.indexOf(listener);
      if (idx !== -1) {
        listeners.splice(idx, 1);
      }
    },
    addEventListener: (type: string, listener: Function) => {
      if (type === 'open') {
        mockSocket._additionalOpenListeners.push(listener);
      } else if (type === 'error') {
        mockSocket._additionalErrorListeners.push(listener);
      } else {
        throw new Error(`Listener type ${type} not implemented in mock object!`);
      }
    },
    close: (code: number, reason: string) => {
      if (code !== undefined && code !== 1000 && !(code >= 3000 && code <= 4999)) {
        throw new DOMException(`Invalid code: ${code}`);
      }
      if (reason && Buffer.from(reason).toString("utf8").length > 123) {
        throw new DOMException(`Reason must be less than 123 bytes. Reason: ${reason}`);
      }
      mockSocket.readyState = originalWebSocket.CLOSED;
      mockSocket.onclose(new CloseEvent("close", {code, reason}));
    },
    send: (msg: string) => {
      const response = getSocketResponseMessage(msg);
      mockSocket.onmessage(response);
    },
    ping: pingFn,
    onopen: () => {},
    onclose: (closeEvent: WebSocket.CloseEvent) => {},
    onerror: (errorEvent: {message: string}) => {},
    onmessage: (event: WebSocket.MessageEvent) => {},
  };
  // Set global variable to send socket's send function so that it can be spied on.
  const openSocket = () => {
    mockSocket.readyState = originalWebSocket.OPEN;
    mockSocket.onopen();
    for (const handler of mockSocket._additionalOpenListeners) {
      handler();
    }
  };
  const closeSocket = (code: number, reason: string) => {
    mockSocket.readyState = originalWebSocket.CLOSED;
    mockSocket.onclose(new CloseEvent("close", {code, reason}));
  }
  const errorSocket = (message: string) => {
    mockSocket.readyState = originalWebSocket.CLOSED;
    mockSocket.onerror({message: message});
    for (const handler of mockSocket._additionalErrorListeners) {
      handler({message: message});
    }
  }
  return {
    mockSocket,
    openSocket,
    closeSocket,
    errorSocket
  }
}

export {
  getMockSocket,
  CloseEvent
}