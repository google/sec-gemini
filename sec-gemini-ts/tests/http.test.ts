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

import HttpClient from '../src/http';

describe("HttpClient", () => {
  test('should fail to send get request with invalid URL', async () => {
    const client = new HttpClient('google.com', '1234');
    expect(client.get('google.com')).rejects.toThrow('Invalid URL');
  });
  test('should fail to send post request with invalid URL', async () => {
    const client = new HttpClient('google.com', '1234');
    expect(client.post('google.com')).rejects.toThrow('Invalid URL');
  });

  test('should successfully complete get request', async () => {
    const expected = {hello: 'secgemini'};
    jest.spyOn(global, 'fetch').mockImplementation(async (input: string|URL|Request, init?: RequestInit): Promise<Response> => {
      if (init!.method !== 'GET') {
        throw new Error('Expected GET request.');
      }
      const headers = init!.headers! as Headers;
      if (headers.get('x-api-key') !== '1234') {
        throw new Error(`Incorrect header API key: ${headers.get('x-api-key')}`);
      }
      return new Response(JSON.stringify(expected));
    });
    const client = new HttpClient('http://google.com', '1234');
    const res = client.get('google.com');
    expect(res).resolves.toEqual(expected);
  });
  test('should successfully complete post request', async() => {
    const expected = {hello: 'secgemini'};
    jest.spyOn(global, 'fetch').mockImplementation(async (input: string|URL|Request, init?: RequestInit): Promise<Response> => {
      if (init!.method !== 'POST') {
        throw new Error('Expected POST request.');
      }
      const headers = init!.headers! as Headers;
      if (headers.get('x-api-key') !== '1234') {
        throw new Error(`Incorrect header API key: ${headers.get('x-api-key')}`);
      }
      if (init!.body !== JSON.stringify({'me': 'secgemini'})) {
        throw new Error(`Expected different body from ${init!.body}`);
      }
      return new Response(JSON.stringify(expected));
    });
    const client = new HttpClient('http://google.com', '1234');
    const res = client.post('google.com', {'me': 'secgemini'});
    expect(res).resolves.toEqual(expected);
  });
});