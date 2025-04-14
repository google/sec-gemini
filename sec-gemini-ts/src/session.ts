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

import randomUUID from "./uuid";
import HttpClient from "./http";
import Streamer from "./streamer";
import { EndPointsEnum, ResponseStatusEnum } from "./enum"; // handcrafted enums

// autogerated enums
import {
  RoleEnum,
  MessageTypeEnum,
  StateEnum,
  UserTypeEnum,
  ModelNameEnum,
  MimeTypeEnum,
  FeedbackTypeEnum,
} from "./secgeminienums";
import {
  Attachment,
  ModelName,
  SessionRequest,
  SessionResponse,
  OpResult,
  Message,
  Usage,
  SessionOutput,
  User,
  Feedback,
} from "./secgeminitypes";

import { log } from "console";
import { measureMemory } from "vm";
type Session = SessionOutput;

interface StreamOptions {
  reconnect?: boolean;
  maxRetries?: number;
  delay?: number;
}

/** Convert an array into its base64 version **/
function uint8ArrayToBase64Promise(uint8array: Uint8Array): Promise<string> {
  return new Promise((resolve, reject) => {
    const blob = new Blob([uint8array]);
    const reader = new FileReader();
    reader.onload = (evt) => {
      const dataUrl = evt?.target?.result;
      if (!dataUrl) {
        reject("Could not read");
        return;
      }
      if (typeof dataUrl != "string") {
        reject("Could not read");
        return;
      }
      const base64String: string = dataUrl.substring(dataUrl.indexOf(",") + 1);
      resolve(base64String);
    };
    reader.onerror = (evt) => {
      reject(evt.target?.error);
    };
    reader.readAsDataURL(blob);
  });
}

class InteractiveSession implements Session {
  public id!: string | undefined;
  public user_id!: string;
  public org_id!: string;
  public ttl!: number;
  public name!: string;
  public description!: string;
  public canLog!: boolean;

  private modelName: ModelName;
  private user: User;
  private http: HttpClient;
  private apiKey: string;
  private websocketURL: string;
  private _session: Session | null;
  private messageQueue: Message[];

  constructor(
    modelName: ModelNameEnum = ModelNameEnum.P9_LATEST_LATEST,
    user: User,
    http: HttpClient,
    websocketURL: string,
    apiKey: string,
    logSession: boolean = true
  ) {
    this.modelName = modelName;
    this.user = user;
    this.http = http;
    this.websocketURL = websocketURL;
    this.apiKey = apiKey;
    this.id = undefined;
    this._session = null;
    this.messageQueue = [];
    this.canLog = logSession;
  }
  public async streamer(
    onmessage: (message: Message) => void,
    onopen: CallableFunction | null = null,
    onerror: CallableFunction | null = null,
    onclose: CallableFunction | null = null,
    options: StreamOptions = {}
  ): Promise<Streamer> {
    if (!this.id) {
      throw new Error("Session must be initialized - no valid id found");
    }
    const streamer = await Streamer.create(
      onmessage,
      onopen,
      onerror,
      onclose,
      this.websocketURL,
      this.id,
      this.apiKey
    );
    return streamer;
  }

  public async detachFile(filename: string): Promise<boolean> {
    "detach a file from the session";
    if (!this.id) {
      throw new Error("Session must be initialized - no valid id found");
    }
    // check if the file exists
    if (!filename) {
      throw new Error("Filename is required");
    }
    const session = await this._getSession();
    if (!session) {
      throw new Error("Session not found");
    }
    const file = session.files?.find((f) => f.filename === filename);
    if (!file) {
      throw new Error(`File ${filename} not found in session`);
    }
    // delete the file
    const resp = await this.http.post<OpResult>(
      EndPointsEnum.DELETE_FILE,
      file
    );
    if (!resp.ok) {
      console.error(`[Session][Delete][HTTP]: ${resp.status_message}`);
      return false;
    }
    if (resp.status_code !== ResponseStatusEnum.OK) {
      console.error(`[Session][Delete][Session]: ${resp.status_message}`);
      return false;
    }
    console.info(
      `[Session][Delete][Session]: File ${filename} detached from session ${this.id}`
    );
    return true;
  }

  public async attachFile(
    filename: string,
    mimeType: MimeTypeEnum,
    content: string | ArrayBuffer
  ): Promise<boolean> {
    "attach a file to the session";
    if (!this.id) {
      throw new Error("Session must be initialized - no valid id found");
    }

    // encode the content if needed
    // let encoded_content: string;
    // if (typeof content === "string") {
    //   encoded_content = content;
    // } else
    // Browser-compatible base64 encoding for binary data
    let bytes: Uint8Array;
    if (typeof content === "string") {
      const encoder = new TextEncoder();
      bytes = encoder.encode(content);
    } else {
      bytes = new Uint8Array(content);
    }
    // encoded_content = btoa(String.fromCharCode.apply(null, Array.from(bytes)));
    const encoded_content: string = await uint8ArrayToBase64Promise(bytes);
    // }

    const attachment: Attachment = {
      session_id: this.id,
      filename: filename,
      mime_type: mimeType,
      content: encoded_content,
    };

    const resp = await this.http.post<OpResult>(
      EndPointsEnum.ATTACH_FILE,
      attachment
    );
    if (!resp.ok) {
      console.error(`[Session][Attachment][HTTP]: ${resp.status_message}`);
      return false;
    }
    if (resp.status_code !== ResponseStatusEnum.OK) {
      console.error(`[Session][Attachment][Session]: ${resp.status_message}`);
      return false;
    }
    console.info(
      `[Session][Attachment][Session]: File ${filename} attached to session ${this.id}`
    );
    return true;
  }

  public async sendBugReport(
    bug: string,
    groupId: string = ""
  ): Promise<boolean> {
    "send a bug report";
    if (!this.id) {
      throw new Error("Session must be initialized - no valid id found");
    }
    const feedback: Feedback = {
      session_id: this.id,
      type: FeedbackTypeEnum.BUG_REPORT,
      score: 0,
      comment: bug,
      group_id: groupId,
    };
    return await this._uploadFeedback(feedback);
  }

  public async sendFeedback(
    score: number,
    comment: string,
    groupId: string = ""
  ): Promise<boolean> {
    "send session/span feedback";

    if (!this.id) {
      throw new Error("Session must be initialized - no valid id found");
    }

    const feedback: Feedback = {
      session_id: this.id,
      type: FeedbackTypeEnum.USER_FEEDBACK,
      score: score,
      comment: comment,
      group_id: groupId,
    };

    return await this._uploadFeedback(feedback);
  }

  private async _uploadFeedback(feedback: Feedback): Promise<boolean> {
    "send feedback to the server";
    const resp = await this.http.post<OpResult>(
      EndPointsEnum.SEND_FEEDBACK,
      feedback
    );
    if (!resp.ok) {
      console.error(`[Session][Feedback][HTTP]: ${resp.status_message}`);
      return false;
    }
    if (resp.status_code !== ResponseStatusEnum.OK) {
      console.error(`[Session][Feedback][Session]: ${resp.status_message}`);
      return false;
    }
    return true;
  }

  public async update(
    name: string = "",
    description: string = "",
    ttl: number = 0
  ): Promise<boolean> {
    "update session information";
    if (!this.id) {
      throw new Error("Session must be initialized - no valid id found");
    }
    const session = await this._getSession();
    if (!session) {
      throw new Error("Session not found");
    }
    // update the session object
    if (name) {
      session.name = name;
    }
    if (description) {
      session.description = description;
    }
    if (ttl) {
      if (ttl <= 300) {
        throw new Error("TTL must be greater than 300 seconds");
      } else {
        session.ttl = ttl;
      }
    }
    const resp = await this.http.post<OpResult>(
      EndPointsEnum.UPDATE_SESSION,
      session
    );
    if (!resp.ok) {
      console.error(`[Session][Update][HTTP]: ${resp.status_message}`);
      return false;
    }
    if (resp.status_code !== ResponseStatusEnum.OK) {
      console.error(`[Session][Update][Session]: ${resp.status_message}`);
      return false;
    }
    console.info(
      `[Session][Update][Session]: Session ${this.id} (${this.name}) updated`
    );
    this._session = {
      id: this.id,
      name: session.name,
      description: session.description,
      user_id: session.user_id,
      org_id: session.org_id,
      ttl: session.ttl,
      can_log: session.can_log,
    };
    return true;
  }

  public async delete(): Promise<boolean> {
    "delete the current session";
    if (!this.id) {
      throw new Error("Session must be initialized - no valid id found");
    }
    const session = await this._getSession();

    const resp = await this.http.post<OpResult>(
      EndPointsEnum.DELETE_SESSION,
      session
    );
    if (resp.status_code !== ResponseStatusEnum.OK) {
      console.error(`[Session][Delete][Session]: ${resp.status_message}`);
      return false;
    }
    console.info(`[Session][Delete][Session]: Session ${this.id} deleted`);
    return true;
  }

  public async resume(sessionId: string): Promise<boolean> {
    this.id = sessionId;
    const session = await this._getSession();
    if (session) {
      this._session = session;
      this.ttl = session.ttl;
      this.name = session.name;
      this.description = session.description;
      this.canLog = session.can_log as boolean;
      console.info(
        `[Session][Register][Session]: Session ${this.id} (${this.name}) resumed`
      );
      return true;
    }
    return false;
  }

  public async history(): Promise<Message[]> {
    const session = await this._getSession();
    if (!session) {
      return [];
    } else {
      return session.messages || []; // Handle potential undefined
    }
  }

  public async visualize(): Promise<object> {
    const session = await this._getSession();
    if (!session) {
      return {};
    }

    const treeData: { [key: string]: any } = {};

    treeData["3713"] = {
      name: `${session.name} - tokens: ${session.usage?.total_tokens || 0}`,
      children: [],
    };

    // FIXME later
    // for (const msg of session.messages || []) {
    //   let node: any;
    //   if (msg.mime_type === MimeType.TEXT) {
    //     const prefix = `[${msg.role}][${msg.message_type}]`;
    //     if (msg.message_type === MessageType.PROMPT) {
    //       node = {
    //         name: `${prefix}[yellow]\n${msg.content}[/yellow]`,
    //         children: [],
    //       };
    //     } else if (msg.message_type === MessageType.GENERATION) {
    //       node = {
    //         name: `${prefix}[green]\n${msg.content}[/green]`,
    //         children: [],
    //       };
    //     } else {
    //       node = { name: `[grey]${prefix}${msg.content}[/grey]`, children: [] };
    //     }
    //   } else {
    //     // FIXME more info here
    //     node = {
    //       name: `[${msg.role}][${msg.message_type}][magenta][File]${msg.mime_type}File[/magenta]`,
    //       children: [],
    //     };
    //   }
    //   if (!treeData[msg.parent_id]) {
    //     console.log(msg.parent_id);
    //   }
    //   treeData[msg.parent_id].children.push(node);
    // }

    return treeData["3713"];
  }

  public async register(
    ttl: number,
    name: string = "",
    description: string = "",
    logSession: boolean = true
  ): Promise<void> {
    this.ttl = ttl;
    this.name = name;
    this.description = description;
    this.id = randomUUID();

    if (ttl <= 300) {
      throw new Error("TTL must be greater than 300 seconds");
    }

    if (!this.name) {
      this.name = this._generateSessionName();
    }

    if (!this.user.can_disable_logging && !logSession) {
      throw new Error("User cannot disable Session logging");
    }

    const req: Session = {
      id: this.id,
      user_id: this.user.id,
      org_id: this.user.org_id,
      name: this.name,
      description: this.description,
      ttl: this.ttl,
      can_log: logSession,
    };

    const resp = await this.http.post<OpResult>(
      EndPointsEnum.REGISTER_SESSION,
      req
    );
    if (!resp.ok) {
      console.error(`[Session][Register][HTTP]: ${resp.status_message}`);
      return;
    }

    if (resp.status_code !== ResponseStatusEnum.OK) {
      console.error(`[Session][Register][Session]: ${resp.status_message}`);
      return;
    }

    console.info(
      `[Session][Register][Session]: Session ${this.id} (${this.name}) registered`
    );

    this._session = {
      id: this.id,
      name: this.name,
      description: this.description,
      user_id: this.user.id,
      org_id: this.user.org_id,
      ttl: this.ttl,
      can_log: this.canLog,
    };
  }

  public async generate(
    prompt: string,
    files: any = []
  ): Promise<SessionResponse | null> {
    if (files.length > 0) {
      // FIXME files support
      throw new Error("Files support is not implemented");
    }
    if (!prompt) {
      throw new Error("Prompt is required");
    }

    const message = this._buildPromptMessage(prompt);
    const req: SessionRequest = {
      id: this.id,
      messages: [message],
      model: this.modelName,
    };
    const resp = await this.http.post<SessionResponse>(
      EndPointsEnum.GENERATE,
      req
    );

    if (resp.status_code !== ResponseStatusEnum.OK) {
      const msg = `[Session][Generate][Response] ${resp.status_code}:${resp.status_message}`;
      console.error(msg);
      return null;
    }
    return resp;
  }

  private async _getSession(): Promise<Session | null> {
    const queryParams = { session_id: this.id };
    const resp = await this.http.get<Session>(
      EndPointsEnum.GET_SESSION,
      queryParams
    );
    return resp;
  }

  private _buildPromptMessage(prompt: string): Message {
    const msg: Message = {
      id: randomUUID(),
      parent_id: "3713",
      role: RoleEnum.USER,
      mime_type: MimeTypeEnum.TEXT_PLAIN,
      state: StateEnum.QUERY,
      message_type: MessageTypeEnum.QUERY,
      content: prompt,
      order: 0,
      status_code: ResponseStatusEnum.OK,
      status_message: "",
      usage: null,
    };
    return msg;
  }

  private _generateSessionName(): string {
    const terms = [
      "firewall",
      "xss",
      "sql-injection",
      "csrf",
      "dos",
      "botnet",
      "rsa",
      "aes",
      "sha",
      "hmac",
      "xtea",
      "twofish",
      "serpent",
      "dh",
      "ecc",
      "dsa",
      "pgp",
      "vpn",
      "tor",
      "dns",
      "tls",
      "ssl",
      "https",
      "ssh",
      "sftp",
      "snmp",
      "ldap",
      "kerberos",
      "oauth",
      "bcrypt",
      "scrypt",
      "argon2",
      "pbkdf2",
      "ransomware",
      "trojan",
      "rootkit",
      "keylogger",
      "adware",
      "spyware",
      "worm",
      "virus",
      "antivirus",
      "sandbox",
      "ids",
      "ips",
      "honeybot",
      "honeypot",
      "siem",
      "nids",
      "hids",
      "waf",
      "dast",
      "sast",
      "vulnerability",
      "exploit",
      "0day",
      "logjam",
      "heartbleed",
      "shellshock",
      "poodle",
      "spectre",
      "meltdown",
      "rowhammer",
      "sca",
      "padding",
      "oracle",
    ];

    const adjs = [
      "beautiful",
      "creative",
      "dangerous",
      "elegant",
      "fancy",
      "gorgeous",
      "handsome",
      "intelligent",
      "jolly",
      "kind",
      "lovely",
      "magnificent",
      "nice",
      "outstanding",
      "perfect",
      "quick",
      "reliable",
      "smart",
      "talented",
      "unique",
      "vibrant",
      "wonderful",
      "young",
      "zany",
      "amazing",
      "brave",
      "calm",
      "delightful",
      "eager",
      "faithful",
      "gentle",
      "happy",
      "incredible",
      "jovial",
      "keen",
      "lucky",
      "merry",
      "nice",
      "optimistic",
      "proud",
      "quiet",
      "reliable",
      "scary",
      "thoughtful",
      "upbeat",
      "victorious",
      "witty",
      "zealous",
      "adorable",
      "brilliant",
      "charming",
      "daring",
      "eager",
      "fearless",
      "graceful",
      "honest",
      "intelligent",
      "jolly",
      "kind",
      "lively",
      "modest",
      "nice",
      "optimistic",
      "proud",
      "quiet",
      "reliable",
      "silly",
      "thoughtful",
      "upbeat",
      "victorious",
      "witty",
    ];

    return `${adjs[Math.floor(Math.random() * adjs.length)]}-${
      terms[Math.floor(Math.random() * terms.length)]
    }`;
  }
}

export default InteractiveSession;
