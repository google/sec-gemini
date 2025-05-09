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