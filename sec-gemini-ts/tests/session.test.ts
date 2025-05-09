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

import InteractiveSession from '../src/session';
import { MessageTypeEnum} from '../src/secgeminienums';
import { getMockSocket, CloseEvent as SocketCloseEvent } from './mock_socket';
import {PublicUser} from '../src/secgeminitypes';
import HttpClient from '../src/http';

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
global.fetch = jest.fn(async (input: string|URL|Request, init?: RequestInit): Promise<Response> => {
  _checkHeaders(init!);
  if (input === 'http://google.com/v1/session/register' && init!.method === 'POST') {
    registerSession(JSON.parse(init!.body! as string));
    return new Response(JSON.stringify({ok: true, 'status_code': 200}));
  }
  return new Response(JSON.stringify({'hello': 'secgemini'}));
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
const model = {
  model_string: 'fakeModel',
  version: 'v1',
  is_experimental: false,
  toolsets: [],
};

let session: InteractiveSession;
describe('Session', () => {
  beforeEach(() => {
    const user = <PublicUser>{id: 'user1'};
    const httpClient = new HttpClient('http://google.com', apiKey);
    session = new InteractiveSession(
      user,
      httpClient,
      websocketUrl,
      apiKey,
      true /*logSession*/
    );
  });
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
  test("should throw error when registering session", async () => {
    // Throw error during post request to register session.
    registerSession.mockImplementationOnce(() => {throw new Error('Registration failure.')});
    const registerPromise = session.register({
        ttl: 301,
        model: model,
        name: 'sessionName',
        description: 'sessionDescription',
        language: 'en'
    });
    expect(registerPromise).rejects.toThrow('Session registration failed due to network/HTTP error: Registration failure.');
  });
  test("should fail to register session", async () => {
    // Throw error during post request to register session.
    (global.fetch as jest.Mock).mockReturnValueOnce(new Response(JSON.stringify({ok: false, 'status_code': 401})));
    const registerPromise = session.register({
        ttl: 301,
        model: model,
        name: 'sessionName',
        description: 'sessionDescription',
        language: 'en'
    });
    expect(registerPromise).rejects.toThrow('Session registration failed: Unknown API error (Status: 401)');
  });
  test("should connect to streamer", async () => {
    const register = session.register({
        ttl: 301,
        model: model,
        name: 'sessionName',
        description: 'sessionDescription',
        language: 'en'
    });
    expect(register).resolves.not.toThrow();

    await register;
    expect(registerSession).toHaveBeenCalledWith(
      {"id":"a-b-c-d-e","user_id":"user1","model":{"model_string":"fakeModel","version":"v1","is_experimental":false,"toolsets":[]},"ttl":301,"name":"sessionName","description":"sessionDescription","can_log":true,"language":"en"}
    );

    const streamer = await session.streamer(onmessage, onopen, onerror, onclose);
    openSocket();
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
        language: 'en'
    });
    (global.fetch as jest.Mock).mockImplementationOnce((async (input: string|URL|Request, init?: RequestInit): Promise<Response> => {
      _checkHeaders(init!);
      if (input === 'http://google.com/v1/session/generate' && init!.method === 'POST') {
        return new Response(JSON.stringify({ok: true, status_code: 200, messages: [{role: 'agent', content: 'hello!'}]}));
      }
      throw new Error(`Invalid request: ${init}`);
    }));
    const respPromise = session.generate('Hello SecGemini!');
    expect(respPromise).resolves.not.toThrow();
    const resp = await respPromise;
    expect(resp).toEqual({ok: true, status_code: 200, messages: [{role: 'agent', content: 'hello!'}]});
  });
  test('should update the session', async () => {
    await session.register({
        ttl: 301,
        model: model,
        name: 'sessionName',
        description: 'sessionDescription',
        language: 'en'
    });
    let updateReq: string;
    (global.fetch as jest.Mock).mockImplementationOnce((async (input: string|URL|Request, init?: RequestInit): Promise<Response> => {
      _checkHeaders(init!);
      if (input === 'http://google.com/v1/session/update' && init!.method === 'POST') {
        updateReq = init!.body! as string;
        return new Response(JSON.stringify({ok: true, status_code: 200}));
      }
      throw new Error(`Invalid request: ${init}`);
    }));
    const respPromise = session.update('sessionName', 'new description', 302);
    expect(respPromise).resolves.not.toThrow();
    const resp = await respPromise;
    expect(updateReq!).toBeDefined();
    expect(JSON.parse(updateReq!)).toEqual(
      {"id":"a-b-c-d-e","user_id":"user1","model":{"model_string":"fakeModel","version":"v1","is_experimental":false,"toolsets":[]},"ttl":302,"name":"sessionName","description":"new description","can_log":true,"language":"en"}
    );
  });
  test('should update the session', async () => {
    await session.register({
        ttl: 301,
        model: model,
        name: 'sessionName',
        description: 'sessionDescription',
        language: 'en'
    });
    let updateReq: string;
    (global.fetch as jest.Mock).mockImplementationOnce((async (input: string|URL|Request, init?: RequestInit): Promise<Response> => {
      _checkHeaders(init!);
      if (input === 'http://google.com/v1/session/update' && init!.method === 'POST') {
        updateReq = init!.body! as string;
        return new Response(JSON.stringify({ok: true, status_code: 200}));
      }
      throw new Error(`Invalid request: ${init}`);
    }));
    const respPromise = session.update('sessionName', 'new description', 302);
    expect(respPromise).resolves.not.toThrow();
    await respPromise;
    expect(updateReq!).toBeDefined();
    expect(JSON.parse(updateReq!)).toEqual(
      {"id":"a-b-c-d-e","user_id":"user1","model":{"model_string":"fakeModel","version":"v1","is_experimental":false,"toolsets":[]},"ttl":302,"name":"sessionName","description":"new description","can_log":true,"language":"en"}
    );
  });
  test('should delete the session', async () => {
    await session.register({
        ttl: 301,
        model: model,
        name: 'sessionName',
        description: 'sessionDescription',
        language: 'en'
    });
    const deleteFn = (async (input: string|URL|Request, init?: RequestInit): Promise<Response> => {
      _checkHeaders(init!);
      if (input === 'http://google.com/v1/session/delete' && init!.method === 'POST') {
        return new Response(JSON.stringify({ok: true, status_code: 200}));
      }
      return new Response(JSON.stringify({ok: true, status_code: 200, messages: []}));
    });
    (global.fetch as jest.Mock).mockImplementationOnce(deleteFn).mockImplementationOnce(deleteFn);
    // Send request and expect response.
    const resp = await session.generate('Hello SecGemini!');
    expect(resp).toEqual({ok: true, status_code: 200, messages: []});

    // Delete session.
    const delPromise = session.delete();
    expect(delPromise).resolves.not.toThrow();
    await delPromise;

    const secondRespPromise = session.generate('Hello SecGemini!');
    expect(secondRespPromise).rejects.toThrow('Session operation failed: Session is not initialized. Call register() or resume() first.');
  });
  test('should attach and detach a file to the session', async () => {
    const expectedSession = {
      id: 'a-b-c-d-e',
      user_id: 'user1',
      org_id: undefined,
      model: {
        model_string: 'fakeModel',
        version: 'v1',
        is_experimental: false,
        toolsets: []
      },
      ttl: 301,
      name: 'sessionName',
      description: 'sessionDescription',
      can_log: true,
      language: 'en',
      messages: [],
      files: [{name: 'filename1', mime_type: 'text/plain'}]
    };

    await session.register({
        ttl: 301,
        model: model,
        name: 'sessionName',
        description: 'sessionDescription',
        language: 'en'
    });
    let attachedFileReq: string|undefined;
    let detachedFileReq: string|undefined;
    const mockFetchImplementation = (async (input: string|URL|Request, init?: RequestInit): Promise<Response> => {
      _checkHeaders(init!);
      if (input === 'http://google.com/v1/session/attach_file' && init!.method === 'POST') {
        attachedFileReq = init!.body! as string;
        return new Response(JSON.stringify({ok: true, status_code: 200}));
      }
      if (input === 'http://google.com/v1/session/get?session_id=a-b-c-d-e' && init!.method === 'GET') {
        // filename1 should already be attached if the tests above pass.
        return new Response(JSON.stringify(expectedSession));
      }
      if (input === 'http://google.com/v1/session/delete_file' && init!.method === 'POST') {
        detachedFileReq = init!.body! as string;
        return new Response(JSON.stringify({ok: true, status_code: 200}));
      }
      throw new Error(`Expected call to attach/detach file or session fetch: ${input}, ${JSON.stringify(init)}`);
    });
    (global.fetch as jest.Mock).mockImplementationOnce(mockFetchImplementation).mockImplementationOnce(mockFetchImplementation).mockImplementationOnce(mockFetchImplementation);
    // Send request and expect response.
    let respPromise = session.attachFile('filename1', 'text/plain', 'filename1 contents');
    expect(respPromise).resolves.not.toThrow();
    await respPromise;
    expect(JSON.parse(attachedFileReq!)).toEqual({"session_id":"a-b-c-d-e","filename":"filename1","mime_type":"text/plain","content":"ZmlsZW5hbWUxIGNvbnRlbnRz"});
    expect(detachedFileReq).not.toBeDefined();

    // Detach file before fetching session cache.
    // TODO: Not sure if we should need to fetch the session cache first. May want to update session.ts code to store some sort of cache locally.
    respPromise = session.detachFile('filename1');
    expect(respPromise).rejects.toThrow("File 'filename1' not found in session cache. Cannot detach.");    

    let fetchSessionPromise = session.fetchSession();
    expect(fetchSessionPromise).resolves.not.toThrow();
    const fetchedSession = await fetchSessionPromise;
    expect(fetchedSession).toEqual(expectedSession);

    respPromise = session.detachFile('filename1');
    expect(respPromise).resolves.not.toThrow();
    await respPromise;
    expect(JSON.parse(detachedFileReq!)).toEqual({"session_id":"a-b-c-d-e","filename":"filename1",'content': '', 'mime_type': 'text/plain'});
  });
  test('should send feedback', async () => {
    await session.register({
        ttl: 301,
        model: model,
        name: 'sessionName',
        description: 'sessionDescription',
        language: 'en'
    });

    let feedbackReqs: string[] = [];
    const feedbackFn = (async (input: string|URL|Request, init?: RequestInit): Promise<Response> => {
      _checkHeaders(init!);
      if (input === 'http://google.com/v1/session/feedback' && init!.method === 'POST') {
        feedbackReqs.push(init!.body! as string);
        return new Response(JSON.stringify({ok: true, status_code: 200}));
      }
      throw new Error(`Expected call to feedback: ${input}, ${JSON.stringify(init)}`);
    });
    (global.fetch as jest.Mock).mockImplementationOnce(feedbackFn).mockImplementationOnce(feedbackFn);
    const bugReportPromise = session.sendBugReport('i am bug', 'groupId1');
    expect(bugReportPromise).resolves.not.toThrow();

    const feedbackPromise = session.sendFeedback(1, 'feedback comment', 'groupId2');
    expect(feedbackPromise).resolves.not.toThrow();

    expect(feedbackReqs).toEqual([
      '{"session_id":"a-b-c-d-e","type":"bug_report","score":0,"comment":"i am bug","group_id":"groupId1"}',
      '{"session_id":"a-b-c-d-e","type":"user_feedback","score":1,"comment":"feedback comment","group_id":"groupId2"}'
    ])
  });
});
