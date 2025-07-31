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

import { SecGemini } from '../src/index';

import { MessageTypeEnum } from '../src/secgeminienums';
import { getMockSocket } from './mock_socket';
import { UserInfo } from '../src/secgeminitypes';

// Mock WebSocket.
// Method to create a response message that should be returned on the web socket. This can be spied on.
let getSocketResponseMessage = jest.fn((req: string): string | object => {
  return { data: JSON.stringify({ data: `Message received: ${req}`, message_type: MessageTypeEnum.RESULT }) };
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
      }
    ),
    { ...originalWebSocket }
  );
});

// Mock the crypto functions used for generating IDs.
crypto.randomUUID = jest.fn(() => {
  return 'a-b-c-d-e';
});

// Mock fetch.
let registerSession = jest.fn((body: object) => {});
function _checkHeaders(init: RequestInit) {
  if (init.method !== 'GET' && init.method !== 'POST') {
    throw new Error('Expected GET or POST request.');
  }
  const headers = init.headers! as Headers;
  if (headers.get('x-api-key') !== 'fakeAPIKey1') {
    throw new Error(`Incorrect header API key: ${headers.get('x-api-key')}`);
  }
}
global.fetch = jest.fn(async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
  _checkHeaders(init!);
  if (input === 'http://google.com/v1/user/info' && init!.method === 'GET') {
    const userInfo: UserInfo = {
      user: { id: '12345', org_id: 'security' },
      sessions: [],
      available_models: [{ model_string: 'stable', version: 'v1' }],
    };
    return new Response(JSON.stringify(userInfo));
  }
  if (input === 'http://google.com/v1/session/register' && init!.method === 'POST') {
    registerSession(JSON.parse(init!.body! as string));
    return new Response(JSON.stringify({ ok: true, status_code: 200 }));
  }
  return new Response(JSON.stringify({ hello: 'secgemini' }));
});

jest.useFakeTimers();

describe('SecGeminiSDK', () => {
  afterEach(() => {
    openSocket = () => {};
    closeSocket = (code: number, reason: string) => {};
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.clearAllTimers();
  });
  afterAll(() => {
    openSocket = () => {};
    closeSocket = (code: number, reason: string) => {};
    jest.resetAllMocks();
    jest.clearAllTimers();
  });
  test('should fail to initialize SecGemini without API key', async () => {
    expect(SecGemini.create()).rejects.toThrowError(
      'API Key is required. Provide it directly or set SEC_GEMINI_API_KEY environment variable.'
    );
  });
  test('should create session', async () => {
    // Create SecGemini instance.
    const sdkPromise = SecGemini.create('fakeAPIKey1', 'http://google.com', 'ws://12345', 'http://example.com');
    expect(sdkPromise).resolves.not.toThrow();
    const sdk = await sdkPromise;

    // Create session.
    const sessionPromise = sdk.createSession({
      ttl: 301,
      name: 'sessionName',
      description: 'sessionDescription',
      logSession: true,
      model: 'stable',
      language: 'en',
    });
    expect(sessionPromise).resolves.not.toThrow();
    expect(await sessionPromise).toEqual({
      _session: {
        can_log: true,
        description: 'sessionDescription',
        files: [],
        id: 'a-b-c-d-e',
        language: 'en',
        messages: [],
        model: { model_string: 'stable', version: 'v1' },
        name: 'sessionName',
        org_id: 'security',
        ttl: 301,
        user_id: '12345',
      },
      apiKey: 'fakeAPIKey1',
      http: { apiKey: 'fakeAPIKey1', baseUrl: 'http://google.com' },
      logsHttp: { apiKey: 'fakeAPIKey1', baseUrl: 'http://example.com'},
      initialLogPreference: true,
      user: { id: '12345', org_id: 'security' },
      websocketURL: 'ws://12345',
    });
  });
});
