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
import Streamer from '../src/streamer';
import { MessageTypeEnum} from '../src/secgeminienums';
import { getMockSocket, CloseEvent as SocketCloseEvent } from './mock_socket';

// Method to create a response message that should be returned on the web socket. This can be spied on.
let getSocketResponseMessage = jest.fn((req: string): string|object => {
  return {data: JSON.stringify({data: `Message received: ${req}`, message_type: MessageTypeEnum.RESULT})};
});

// Helpers that allow tests to directly interact with the web socket object created by Streamer.
let openSocket = () => {};
let closeSocket = (code: number, reason: string) => {};
let errorSocket = (message: string) => {};
const pingFn = jest.fn((f: Function) => {});
// Mock needs to be in module scope.
jest.mock('isomorphic-ws', () => {
  console.log('Creating mock WebSocket');
  // Original unmocked WebSocket.
  const originalWebSocket = jest.requireActual('isomorphic-ws');
  // Mocked WebSocket.
  return Object.assign(
    jest.fn(
      // constructor
      (url: string) => {
        const socketMocks = getMockSocket(url, originalWebSocket, getSocketResponseMessage, pingFn);
        openSocket = socketMocks.openSocket;
        closeSocket = socketMocks.closeSocket;
        errorSocket = socketMocks.errorSocket;
        return socketMocks.mockSocket;
      }),
      { 
        ...originalWebSocket
       }
    );
});

// Mock the crypto functions used for generating IDs.
crypto.randomUUID = jest.fn(() => {
  return 'a-b-c-d-e';
});

jest.useFakeTimers();

// Variables to use as arguments to Streamer.create.
const onmessage = jest.fn(() => {});
const onopen = jest.fn(() => {});
const onerror = jest.fn(() => {});
const onclose = jest.fn(() => {});
const websocketUrl = 'ws://12345';
const sessionID = 'abcde';
const apiKey = 'fakeAPIKey';
const config = {
  onConnectionStatusChange: jest.fn((status: string) => {}),
  onReconnect: jest.fn((status: boolean, attempts: number) => {}),
};
describe("Streamer", () => {
  afterEach(() => {
    openSocket = () => {};
    closeSocket = (code: number, reason: string) => {}
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.clearAllTimers();
  });
  afterAll(() => {
    openSocket = () => {};
    closeSocket = (code: number, reason: string) => {}
    jest.resetAllMocks();
    jest.clearAllTimers();
  });
  test("should connect to and disconnect from server", async () => {
    const streamerPromise: Promise<Streamer> = Streamer.create(
        onmessage,
        onopen,
        onerror,
        onclose,
        websocketUrl,
        sessionID,
        apiKey,
        config,
    );
    // Check creation.
    await expect(streamerPromise).resolves.not.toThrow();
    expect(onerror).toHaveBeenCalledTimes(0);
    const streamer = await streamerPromise;
    // Check connection.
    openSocket();
    expect(onopen).toHaveBeenCalled();
    expect(streamer.isConnected()).toBe(true);
    // Fast forward and check heartbeat.
    jest.runOnlyPendingTimers();
    expect(pingFn).toHaveBeenCalledTimes(1);
    // Close.
    streamer.close();
    expect(onclose).toHaveBeenCalled();
    // Check connection.
    expect(streamer.isConnected()).toBe(false);


    // Check connection callbacks.
    expect(config.onConnectionStatusChange.mock.calls).toEqual([
      ["connecting"], ["connected"], ['disconnected']
    ]);
  });

  test("should handle bad URL", async () => {
    const streamer: Promise<Streamer> = Streamer.create(
        onmessage,
        onopen,
        onerror,
        onclose,
        '12345',
        sessionID,
        apiKey,
        config,
    );
    await expect(streamer).rejects.toThrow();
    expect(onerror).toHaveBeenCalledTimes(0);
  });

  test("should fail to connect to server", async () => {
    const streamer: Promise<Streamer> = Streamer.create(
        onmessage,
        onopen,
        onerror,
        onclose,
        'ws://badurl',
        sessionID,
        apiKey,
        config,
    );
    await expect(streamer).rejects.toEqual(new DOMException("Bad URL"));
    expect(onerror).toHaveBeenCalledTimes(1);
  });

  test("should attempt to reconnect to server", async () => {
    const streamer = await Streamer.create(
        onmessage,
        onopen,
        onerror,
        onclose,
        websocketUrl,
        sessionID,
        apiKey,
        config,
    );
    openSocket();
    // Check connection is open.
    expect(onopen).toHaveBeenCalled();
    expect(streamer.isConnected()).toBe(true);
    // Close.
    closeSocket(1001, "Going Away");
    expect(onclose).toHaveBeenCalled();
    // Check connection is closed.
    expect(streamer.isConnected()).toBe(false);
    // Fast forward to try and reconnect.
    jest.runAllTimers();
    // Make the web socket fail to connect.
    errorSocket("Failed");
    expect(onerror).toHaveBeenCalled();
    // Fast forward to try and reconnect.
    jest.runAllTimers();
    openSocket();
    expect(onopen).toHaveBeenCalled();
    expect(streamer.isConnected()).toBe(true);


    // Check connection callbacks.
    expect(config.onConnectionStatusChange.mock.calls).toEqual([
      ["connecting"], ["connected"], ["reconnecting"], ["connecting"], ['error'], ['disconnected'], ["reconnecting"], ['connecting'], ["connected"]
    ]);
    expect(config.onReconnect.mock.calls).toEqual([
      [false, 1], [true, 2]
    ]);
  });

  // TODO: send message with parent ID.
  test("should send and receive messages", async () => {
    const streamer = await Streamer.create(
        onmessage,
        onopen,
        onerror,
        onclose,
        websocketUrl,
        sessionID,
        apiKey,
        config,
    );
    // Try to send messages before connection is opened.
    streamer.send('Hello SecGemini!');
    expect(onmessage).not.toHaveBeenCalled();
    openSocket();
    expect(onopen).toHaveBeenCalled();
    // Expect previous messages to have been sent.
    expect(onmessage).toHaveBeenCalledWith({
      'data': 'Message received: {"id":"a-b-c-d-e","parent_id":"3713","role":"user","mime_type":"text/plain","message_type":"query","content":"Hello SecGemini!"}',
      'message_type': 'result'
    });
    // Try to send more messages now that the socket has been opened.
    streamer.send('How are you?');
    expect(onmessage).toHaveBeenCalledWith({
      'data': 'Message received: {"id":"a-b-c-d-e","parent_id":"3713","role":"user","mime_type":"text/plain","message_type":"query","content":"How are you?"}',
      'message_type': 'result'
    });

    // Close.
    streamer.close();


    // Check connection callbacks.
    expect(config.onConnectionStatusChange.mock.calls).toEqual([
      ["connecting"], ["connected"], ['disconnected']
    ]);
  });

  test("should gracefully handle failed messages", async () => {
    const streamer = await Streamer.create(
        onmessage,
        onopen,
        onerror,
        onclose,
        websocketUrl,
        sessionID,
        apiKey,
        config,
    );
    // Try to send messages before connection is opened.
    getSocketResponseMessage.mockImplementationOnce(() => {throw new Error('Received bad message in web socket.')})
    .mockImplementationOnce(() => {throw new Error('Received bad message in web socket.')});
    streamer.send('bad message');
    expect(onmessage).not.toHaveBeenCalled();
    openSocket();
    expect(onopen).toHaveBeenCalled();
    // Expect previous messages to have been sent.
    expect(onerror).toHaveBeenCalledWith(new Error('Received bad message in web socket.'));
    // Try to send more messages now that the socket has been opened.
    streamer.send('bad message');
    expect(onerror).toHaveBeenCalledWith(new Error('Received bad message in web socket.'));

    expect(onmessage).not.toHaveBeenCalled();

    // Close.
    streamer.close();

    // Check connection callbacks.
    expect(config.onConnectionStatusChange.mock.calls).toEqual([
      ["connecting"], ["connected"], ['disconnected']
    ]);
  });

  test("should gracefully handle bad prompts", async () => {
    const streamer = await Streamer.create(
        onmessage,
        onopen,
        onerror,
        onclose,
        websocketUrl,
        sessionID,
        apiKey,
        config,
    );
    openSocket();
    const sendRes = streamer.send('');
    expect(sendRes).rejects.toEqual(new Error('Invalid prompt: must be a non-empty string'));

    // Close.
    streamer.close();

    // Check connection callbacks.
    expect(config.onConnectionStatusChange.mock.calls).toEqual([
      ["connecting"], ["connected"], ['disconnected']
    ]);
  });

  test("should handle Buffer responses", async () => {
    const streamer = await Streamer.create(
      onmessage,
      onopen,
      onerror,
      onclose,
      websocketUrl,
      sessionID,
      apiKey,
      config,
    );
    openSocket();
    // Try to send a message.
    getSocketResponseMessage.mockImplementationOnce((req: string) => {
      return {data: Buffer.from(JSON.stringify({data: `Message received: ${req}`, message_type: MessageTypeEnum.RESULT}))}
    });
    streamer.send('send Buffer');
    expect(onmessage).toHaveBeenCalledWith({
      'data': 'Message received: {"id":"a-b-c-d-e","parent_id":"3713","role":"user","mime_type":"text/plain","message_type":"query","content":"send Buffer"}',
      'message_type': 'result'
    });

    // Close.
    streamer.close();

    // Check connection callbacks.
    expect(config.onConnectionStatusChange.mock.calls).toEqual([
      ["connecting"], ["connected"], ['disconnected']
    ]);
  });

  test("should gracefully handle bad responses", async () => {
    const streamer = await Streamer.create(
        onmessage,
        onopen,
        onerror,
        onclose,
        websocketUrl,
        sessionID,
        apiKey,
        config,
    );
    openSocket();
    // Send message.
    getSocketResponseMessage.mockReturnValue('bad response');
    streamer.send('send bad response');
    expect(onerror).toHaveBeenCalledWith(new Error('Streamer: Received message of unknown type: undefined'));
    expect(onmessage).not.toHaveBeenCalled();

    // Close.
    streamer.close();

    // Check connection callbacks.
    expect(config.onConnectionStatusChange.mock.calls).toEqual([
      ["connecting"], ["connected"], ['disconnected']
    ]);
  });

  test('should handle "not found" status message from web socket', async () => {
    const streamer = await Streamer.create(
        onmessage,
        onopen,
        onerror,
        onclose,
        websocketUrl,
        sessionID,
        apiKey,
        config,
    );
    openSocket();
    // Send message.
    getSocketResponseMessage.mockReturnValue({data: JSON.stringify({status_message: 'not found', message_type: MessageTypeEnum.ERROR})});
    streamer.send('Hello SecGemini!');
    expect(onerror).toHaveBeenCalledWith(new Error('Session not found on server'));
    expect(onclose).toHaveBeenCalledWith(new SocketCloseEvent("close", {code: 4001, reason: 'Session Not Found'}));

    // Check connection callbacks.
    expect(config.onConnectionStatusChange.mock.calls).toEqual([
      ["connecting"], ["connected"], ['disconnected']
    ]);
  });
  // TODO: status message test.

});
