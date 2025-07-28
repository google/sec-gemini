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

import { StreamOptions, InteractiveSession } from '../src/session';
import { MessageTypeEnum } from '../src/secgeminienums';
import { getMockSocket, CloseEvent as SocketCloseEvent } from './mock_socket';
import { PublicSessionFile, PublicUser } from '../src/secgeminitypes';
import HttpClient from '../src/http';
import { ResponseStatusEnum } from '../src/enum';

// Method to create a response message that should be returned on the web socket. This can be spied on.
let getSocketResponseMessage = jest.fn((req: string, stream: boolean): string[] | object[] => {
  const msgs: any = [];
  if (stream) {
    msgs.push({
      data: JSON.stringify({
        data: '',
        message_type: MessageTypeEnum.RESULT,
        status_code: ResponseStatusEnum.PARTIAL_CONTENT,
      }),
    });
  }
  msgs.push({
    data: JSON.stringify({
      data: `Message received: ${req}`,
      message_type: MessageTypeEnum.RESULT,
      status_code: ResponseStatusEnum.OK,
    }),
  });
  return msgs;
});

// Helpers that allow tests to directly interact with the web socket object created by Streamer.
let openSocket = () => {};
let closeSocket = (code: number, reason: string) => {};
let errorSocket = (message: string) => {};
const pingFn = jest.fn((f: Function) => {});
// Tracks the URL of the most recently opened socket. Make sure to reset before each test.
let openedUrl = '';
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
        openedUrl = url;
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

jest.useFakeTimers();

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
  if (input === 'http://google.com/v1/session/register' && init!.method === 'POST') {
    registerSession(JSON.parse(init!.body! as string));
    return new Response(JSON.stringify({ ok: true, status_code: 200 }));
  }
  throw new Error(`Uncaught fetch request: ${input}, ${JSON.stringify(init)}`);
});

const onmessage = jest.fn(() => {});
const onopen = jest.fn(() => {});
const onerror = jest.fn(() => {});
const onclose = jest.fn(() => {});
const websocketUrl = 'ws://12345';
const apiKey = 'fakeAPIKey1';
const config = {
  onConnectionStatusChange: jest.fn((status: string) => {}),
  onReconnect: jest.fn((status: boolean, attempts: number) => {}),
};
const model = { model_string: 'fakeModel', version: 'v1', use_experimental: false, toolsets: [] };

let session: InteractiveSession;
describe('Session', () => {
  beforeEach(() => {
    const user = <PublicUser>{ id: 'user1' };
    const httpClient = new HttpClient('http://google.com', apiKey);
    session = new InteractiveSession(user, httpClient, websocketUrl, apiKey, true /*logSession*/);
  });
  afterEach(() => {
    openSocket = () => {};
    closeSocket = (code: number, reason: string) => {};
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.clearAllTimers();
    openedUrl = '';
  });
  afterAll(() => {
    openSocket = () => {};
    closeSocket = (code: number, reason: string) => {};
    jest.resetAllMocks();
    jest.clearAllTimers();
    openedUrl = '';
  });
  test('should throw error when registering session', async () => {
    // Throw error during post request to register session.
    registerSession.mockImplementationOnce(() => {
      throw new Error('Registration failure.');
    });
    const registerPromise = session.register({
      ttl: 301,
      model: model,
      name: 'sessionName',
      description: 'sessionDescription',
      language: 'en',
    });
    expect(registerPromise).rejects.toThrow(
      'Session registration failed due to network/HTTP error: Registration failure.'
    );
  });
  test('should fail to register session', async () => {
    // Throw error during post request to register session.
    (global.fetch as jest.Mock).mockReturnValueOnce(new Response(JSON.stringify({ ok: false, status_code: 401 })));
    const registerPromise = session.register({
      ttl: 301,
      model: model,
      name: 'sessionName',
      description: 'sessionDescription',
      language: 'en',
    });
    expect(registerPromise).rejects.toThrow('Session registration failed: Unknown API error (Status: 401)');
  });
  test('should connect to streamer', async () => {
    const register = session.register({
      ttl: 301,
      model: model,
      name: 'sessionName',
      description: 'sessionDescription',
      language: 'en',
    });
    expect(register).resolves.not.toThrow();

    await register;
    expect(registerSession).toHaveBeenCalledWith({
      id: 'a-b-c-d-e',
      user_id: 'user1',
      model: { model_string: 'fakeModel', version: 'v1', use_experimental: false, toolsets: [] },
      ttl: 301,
      name: 'sessionName',
      description: 'sessionDescription',
      can_log: true,
      language: 'en',
    });

    const streamerPromise = session.streamer(onmessage, onopen, onerror, onclose);
    openSocket();
    const streamer = await streamerPromise;
    expect(openedUrl).toBe('ws://12345/v1/stream?api_key=fakeAPIKey1&session_id=a-b-c-d-e&stream=false');
    expect(streamer.isConnected()).toBe(true);
    streamer.close();
    expect(streamer.isConnected()).toBe(false);
  });
  test('should connect to streamer and use streaming mode', async () => {
    const register = session.register({
      ttl: 301,
      model: model,
      name: 'sessionName',
      description: 'sessionDescription',
      language: 'en',
    });
    expect(register).resolves.not.toThrow();

    await register;
    expect(registerSession).toHaveBeenCalledWith({
      id: 'a-b-c-d-e',
      user_id: 'user1',
      model: { model_string: 'fakeModel', version: 'v1', use_experimental: false, toolsets: [] },
      ttl: 301,
      name: 'sessionName',
      description: 'sessionDescription',
      can_log: true,
      language: 'en',
    });

    const streamOptions: StreamOptions = { stream: true };
    const streamerPromise = session.streamer(onmessage, onopen, onerror, onclose, streamOptions);
    openSocket();
    const streamer = await streamerPromise;
    expect(openedUrl).toBe('ws://12345/v1/stream?api_key=fakeAPIKey1&session_id=a-b-c-d-e&stream=true');
    expect(streamer.isConnected()).toBe(true);
    streamer.close();
    expect(streamer.isConnected()).toBe(false);
  });
  test('should generate model response over http', async () => {
    await session.register({
      ttl: 301,
      model: model,
      name: 'sessionName',
      description: 'sessionDescription',
      language: 'en',
    });
    (global.fetch as jest.Mock).mockImplementationOnce(
      async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
        _checkHeaders(init!);
        if (input === 'http://google.com/v1/session/generate' && init!.method === 'POST') {
          return new Response(
            JSON.stringify({ ok: true, status_code: 200, messages: [{ role: 'agent', content: 'hello!' }] })
          );
        }
        throw new Error(`Invalid request: ${init}`);
      }
    );
    const respPromise = session.generate('Hello SecGemini!');
    expect(respPromise).resolves.not.toThrow();
    const resp = await respPromise;
    expect(resp).toEqual({ ok: true, status_code: 200, messages: [{ role: 'agent', content: 'hello!' }] });
  });
  test('should update the session', async () => {
    await session.register({
      ttl: 301,
      model: model,
      name: 'sessionName',
      description: 'sessionDescription',
      language: 'en',
    });
    let updateReq: string;
    (global.fetch as jest.Mock).mockImplementationOnce(
      async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
        _checkHeaders(init!);
        if (input === 'http://google.com/v1/session/update' && init!.method === 'POST') {
          updateReq = init!.body! as string;
          return new Response(JSON.stringify({ ok: true, status_code: 200 }));
        }
        throw new Error(`Invalid request: ${init}`);
      }
    );
    const respPromise = session.update('sessionName', 'new description', 302);
    expect(respPromise).resolves.not.toThrow();
    const resp = await respPromise;
    expect(updateReq!).toBeDefined();
    expect(JSON.parse(updateReq!)).toEqual({
      id: 'a-b-c-d-e',
      user_id: 'user1',
      model: { model_string: 'fakeModel', version: 'v1', use_experimental: false, toolsets: [] },
      ttl: 302,
      name: 'sessionName',
      description: 'new description',
      can_log: true,
      language: 'en',
    });
  });
  test('should update the session', async () => {
    await session.register({
      ttl: 301,
      model: model,
      name: 'sessionName',
      description: 'sessionDescription',
      language: 'en',
    });
    let updateReq: string;
    (global.fetch as jest.Mock).mockImplementationOnce(
      async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
        _checkHeaders(init!);
        if (input === 'http://google.com/v1/session/update' && init!.method === 'POST') {
          updateReq = init!.body! as string;
          return new Response(JSON.stringify({ ok: true, status_code: 200 }));
        }
        throw new Error(`Invalid request: ${init}`);
      }
    );
    const respPromise = session.update('sessionName', 'new description', 302);
    expect(respPromise).resolves.not.toThrow();
    await respPromise;
    expect(updateReq!).toBeDefined();
    expect(JSON.parse(updateReq!)).toEqual({
      id: 'a-b-c-d-e',
      user_id: 'user1',
      model: { model_string: 'fakeModel', version: 'v1', use_experimental: false, toolsets: [] },
      ttl: 302,
      name: 'sessionName',
      description: 'new description',
      can_log: true,
      language: 'en',
    });
  });
  test('should delete the session', async () => {
    await session.register({
      ttl: 301,
      model: model,
      name: 'sessionName',
      description: 'sessionDescription',
      language: 'en',
    });
    const deleteFn = async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
      _checkHeaders(init!);
      if (input === 'http://google.com/v1/session/delete' && init!.method === 'POST') {
        return new Response(JSON.stringify({ ok: true, status_code: 200 }));
      }
      return new Response(JSON.stringify({ ok: true, status_code: 200, messages: [] }));
    };
    (global.fetch as jest.Mock).mockImplementationOnce(deleteFn).mockImplementationOnce(deleteFn);
    // Send request and expect response.
    const resp = await session.generate('Hello SecGemini!');
    expect(resp).toEqual({ ok: true, status_code: 200, messages: [] });

    // Delete session.
    const delPromise = session.delete();
    expect(delPromise).resolves.not.toThrow();
    await delPromise;

    const secondRespPromise = session.generate('Hello SecGemini!');
    expect(secondRespPromise).rejects.toThrow(
      'Session operation failed: Session is not initialized. Call register() or resume() first.'
    );
  });
  test('should attach and detach a file to the session', async () => {
    const expectedSessionAfterAttach = {
      id: 'a-b-c-d-e',
      user_id: 'user1',
      org_id: undefined,
      model: { model_string: 'fakeModel', version: 'v1', use_experimental: false, toolsets: [] },
      ttl: 301,
      name: 'sessionName',
      description: 'sessionDescription',
      can_log: true,
      language: 'en',
      messages: [],
      files: [
        {
          name: 'filename1',
          size: 18,
          sha256: 'eb2eb8f9bbe4c506bd67c2a8b8f76badb0ab870b7c272fc273cd2b849281d4b9',
          mime_type: 'text/plain',
          content_type_label: 'txt',
        },
      ],
    };
    const expectedSessionAfterDetachment = {
      id: 'a-b-c-d-e',
      user_id: 'user1',
      org_id: undefined,
      model: { model_string: 'fakeModel', version: 'v1', use_experimental: false, toolsets: [] },
      ttl: 301,
      name: 'sessionName',
      description: 'sessionDescription',
      can_log: true,
      language: 'en',
      messages: [],
      files: [],
    };

    await session.register({
      ttl: 301,
      model: model,
      name: 'sessionName',
      description: 'sessionDescription',
      language: 'en',
    });
    let attachFileReq: string | undefined;
    let detachFileRequest: string | undefined;
    const mockFetchImplementation = async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
      _checkHeaders(init!);
      if (input === 'http://google.com/v1/session/attach_file' && init!.method === 'POST') {
        attachFileReq = init!.body! as string;
        return new Response(
          JSON.stringify({
            ok: true,
            status_code: 200,
            data: {
              name: 'filename1',
              size: 18,
              sha256: 'eb2eb8f9bbe4c506bd67c2a8b8f76badb0ab870b7c272fc273cd2b849281d4b9',
              mime_type: 'text/plain',
              content_type_label: 'txt',
            },
          })
        );
      }
      if (input === 'http://google.com/v1/session/get?session_id=a-b-c-d-e' && init!.method === 'GET') {
        if (detachFileRequest === undefined) {
          // This is hit after the attachment but before the deletion
          return new Response(JSON.stringify(expectedSessionAfterAttach));
        } else {
          // This is hit after the deletion
          return new Response(JSON.stringify(expectedSessionAfterDetachment));
        }
      }
      if (input === 'http://google.com/v1/session/detach_file' && init!.method === 'POST') {
        detachFileRequest = init!.body! as string;
        return new Response(JSON.stringify({ ok: true, status_code: 200 }));
      }
      throw new Error(`Expected call to attach/detach file or session fetch: ${input}, ${JSON.stringify(init)}`);
    };
    (global.fetch as jest.Mock)
      .mockImplementationOnce(mockFetchImplementation)
      .mockImplementationOnce(mockFetchImplementation)
      .mockImplementationOnce(mockFetchImplementation)
      .mockImplementationOnce(mockFetchImplementation)
      .mockImplementationOnce(mockFetchImplementation)
      .mockImplementationOnce(mockFetchImplementation);
    // Send request and expect response.

    let attachRespPromise = session.attachFile('filename1', 'filename1 contents');
    expect(attachRespPromise).resolves.not.toThrow();
    let attachedSessionFile: PublicSessionFile = await attachRespPromise;
    expect(JSON.parse(attachFileReq!)).toEqual({
      session_id: 'a-b-c-d-e',
      filename: 'filename1',
      content: 'ZmlsZW5hbWUxIGNvbnRlbnRz',
    });
    expect(detachFileRequest).not.toBeDefined();
    expect(session.files.length).toEqual(1);
    // TODO add more fields
    expect(attachedSessionFile.name === 'filename1');
    expect(attachedSessionFile.size === 18);
    expect(attachedSessionFile.sha256 === 'eb2eb8f9bbe4c506bd67c2a8b8f76badb0ab870b7c272fc273cd2b849281d4b9');
    expect(attachedSessionFile.mime_type === 'text/plain');
    expect(attachedSessionFile.content_type_label === 'txt');

    // Check that the session is being updated
    let fetchSessionPromise = session.fetchSession();
    expect(fetchSessionPromise).resolves.not.toThrow();
    const fetchedSession = await fetchSessionPromise;
    expect(fetchedSession).toEqual(expectedSessionAfterAttach);
    expect(session.files.length).toEqual(1);

    // // Test file detachment
    let detachRespPromise = session.detachFile(0);
    expect(detachRespPromise).resolves.not.toThrow();
    await detachRespPromise;
    expect(JSON.parse(detachFileRequest!)).toEqual({
      session_id: 'a-b-c-d-e',
      file_idx: 0,
    });
    expect(session.files.length).toEqual(0);

    fetchSessionPromise = session.fetchSession();
    expect(fetchSessionPromise).resolves.not.toThrow();
    const fetchedSession2 = await fetchSessionPromise;
    expect(fetchedSession2).toEqual(expectedSessionAfterDetachment);
    expect(session.files.length).toEqual(0);
  });
  test('should send feedback', async () => {
    await session.register({
      ttl: 301,
      model: model,
      name: 'sessionName',
      description: 'sessionDescription',
      language: 'en',
    });

    let feedbackReqs: string[] = [];
    const feedbackFn = async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
      _checkHeaders(init!);
      if (input === 'http://google.com/v1/session/feedback' && init!.method === 'POST') {
        feedbackReqs.push(init!.body! as string);
        return new Response(JSON.stringify({ ok: true, status_code: 200 }));
      }
      throw new Error(`Expected call to feedback: ${input}, ${JSON.stringify(init)}`);
    };
    (global.fetch as jest.Mock).mockImplementationOnce(feedbackFn).mockImplementationOnce(feedbackFn);
    const bugReportPromise = session.sendBugReport('i am bug', 'groupId1');
    expect(bugReportPromise).resolves.not.toThrow();

    const feedbackPromise = session.sendFeedback(1, 'feedback comment', 'groupId2');
    expect(feedbackPromise).resolves.not.toThrow();

    expect(feedbackReqs).toEqual([
      '{"session_id":"a-b-c-d-e","type":"bug_report","score":0,"comment":"i am bug","group_id":"groupId1"}',
      '{"session_id":"a-b-c-d-e","type":"user_feedback","score":1,"comment":"feedback comment","group_id":"groupId2"}',
    ]);
  });
});
