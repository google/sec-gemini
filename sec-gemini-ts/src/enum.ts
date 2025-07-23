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

enum EndPointsEnum {
  // users
  USER_INFO = '/v1/user/info',

  // messages
  GENERATE = '/v1/session/generate',
  STREAM = '/v1/stream',

  // sessions
  REGISTER_SESSION = '/v1/session/register',
  DELETE_SESSION = '/v1/session/delete',
  LIST_SESSION = '/v1/session/list',
  GET_SESSION = '/v1/session/get',
  UPDATE_SESSION = '/v1/session/update',
  SEND_FEEDBACK = '/v1/session/feedback',

  // files
  ATTACH_FILE = '/v1/session/attach_file',
  DETACH_FILE = '/v1/session/detach_file',
}

enum ResponseStatusEnum {
  OK = 200,
  PARTIAL_CONTENT = 206,
  BAD_REQUEST = 400,
  NOT_FOUND = 404,
  AUTHENTICATION_ERROR = 401,
  ALREADY_EXISTS = 409,
  QUOTA_EXCEEDED = 429,
  SERVER_ERROR = 500,
  INTERNAL_ERROR = 500,
}

export { EndPointsEnum, ResponseStatusEnum };
