# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import sys
from time import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, Field

from .enums import SDKInfo

# Define a TypeVar for subclasses of HTTPResponse
T = TypeVar("T", bound="BaseModel")


class NetResponse(BaseModel):
  url: str = Field(title="Request URL")
  ok: bool
  error_message: str = Field("", title="Error Message")
  data: dict = Field(default_factory=dict, title="Response Data")
  latency: float = Field(
    0.0,
    title="Latency",
    description="The time taken to complete the request in seconds.",
  )


class NetworkClient:
  def __init__(self, base_url: str, api_key: str):
    self.base_url = base_url
    self.api_key = api_key
    self.client = httpx.Client(timeout=90)

  def post(
    self, endpoint: str, model: T, headers: dict | None = None
  ) -> NetResponse:
    """Post Request to the API.

    Args:
        endpoint: The API endpoint to post to.
        model: The pydantic model to be posted.
        headers: The headers specific to the requests to be sent along.

    Returns:
        HTTPResponse: The response from the API.
    """
    if headers is None:
      headers = {}

    data = model.model_dump()
    url = self._make_url(endpoint)
    headers = self._make_headers(headers)

    logging.debug("POST URL: %s, Headers:%s", url, headers)
    logging.debug("Request: %s", model.model_dump_json())
    start_time = time()
    response = self.client.post(url, headers=headers, json=data)
    latency = time() - start_time
    nr = None
    if response.status_code != 200:
      nr = NetResponse(
        url=url,
        ok=False,
        error_message=self._make_error_message(url, response),
        latency=latency,
      )
    else:
      nr = NetResponse(url=url, ok=True, data=response.json(), latency=latency)
    logging.debug("[HTTP][POST] %s -> latency: %s", url, latency)
    logging.debug("Response: %s", nr.model_dump_json())
    return nr

  def get(
    self, endpoint: str, query_params: dict = {}, headers: dict = {}
  ) -> NetResponse:
    """Get Request to the API

    Args:
        endpoint: The API endpoint to get from.
        query_params: The query parameters to be sent along.
        headers: The headers specific to the requests to be sent along.

    Returns:
        HTTPResponse: The response from the API.
    """
    url = self._make_url(endpoint)
    headers = self._make_headers(headers)

    logging.debug("GET URL: %s, Headers:%s", url, headers)
    logging.debug("Request: %s", json.dumps(query_params))

    start_time = time()
    response = self.client.get(url, params=query_params, headers=headers)
    latency = time() - start_time
    nr = None
    if response.status_code != 200:
      nr = NetResponse(
        url=url,
        ok=False,
        error_message=self._make_error_message(url, response),
        latency=latency,
      )
    else:
      nr = NetResponse(url=url, ok=True, data=response.json(), latency=latency)
    logging.debug("[HTTP][GET] %s -> latency: %s", url, latency)
    logging.debug("Response: %s", nr.model_dump_json())
    return nr

  def _make_url(self, endpoint: str) -> str:
    return f"{self.base_url}/{endpoint.lstrip('/')}"

  def _make_headers(self, headers: dict) -> dict:
    # User-Agent: Mozilla/5.0 (<system-information>) <platform> (<platform-details>) <extensions>

    # request specific headers
    headers = headers or {}

    additional_headers = {
      "User-Agent": f"{SDKInfo.NAME.value}/{SDKInfo.VERSION.value} ({sys.platform}) {sys.version} ({sys.version_info})",
      "x-sdk-version": SDKInfo.VERSION.value,
      "x-sdk": "python",
      "x-api-key": self.api_key,
      "Content-Type": "application/json",
    }
    headers.update(additional_headers)
    return headers

  def _make_error_message(self, url: str, response: httpx.Response) -> str:
    return f"[HTTP] {url} -> {response.status_code}:{response.text}"
