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

type RequestConfig = {
  params?: Record<string, any>;
  headers?: Record<string, string>;
};

class HttpClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private createUrl(entrypoint: string, params?: Record<string, any>): string {
    const url = new URL(entrypoint, this.baseUrl);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, String(value));
      });
    }
    return url.toString();
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  private getHeaders(additionalHeaders?: Record<string, string>): Headers {
    return new Headers({
      "x-api-key": this.apiKey,
      "Content-Type": "application/json",
      ...additionalHeaders,
    });
  }

  public async get<T>(
    entrypoint: string,
    params?: Record<string, any>
  ): Promise<T> {
    const url = this.createUrl(entrypoint, params);
    const response = await fetch(url, {
      method: "GET",
      headers: this.getHeaders(),
    });
    return this.handleResponse<T>(response);
  }

  public async post<T>(
    entrypoint: string,
    data?: any,
    config?: RequestConfig
  ): Promise<T> {
    const url = this.createUrl(entrypoint, config?.params);
    const response = await fetch(url, {
      method: "POST",
      headers: this.getHeaders(config?.headers),
      body: data ? JSON.stringify(data) : undefined,
    });
    return this.handleResponse<T>(response);
  }
}

export default HttpClient;
