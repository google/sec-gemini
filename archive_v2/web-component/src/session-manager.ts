// src/utils/session-manager.ts
import P9SDK, {
  InteractiveSession,
  MessageTypeEnum,
  StateEnum,
  Streamer,
  type Message,
  type State,
  type UserInfo,
} from "p9sdk";
import {
  p9Key,
  p9URL,
  isAuth,
  modelList,
  isAdmin,
  isSessionLogging,
  canDisableLogging,
  username,
  sessionName,
  organization,
  sessionID,
  sessionList,
  sdkInitialized,
  streamer,
  history,
  currentSession,
  files,
} from "../state/store.svelte.ts";

// Global variables
let ttl: number = 86400;
let p9: P9SDK;
let userInfo: UserInfo;
let session: InteractiveSession;
let stored_key = "";
let currentStreamer: Streamer | null = null;
let sessionStartTime = $state<number>(0);
let debugMessages = $state<
  (Message & { receivedAt: number; elapsedTime: number })[]
>([]);

type Role = "user" | "assistant" | "tools" | "ui";

type UIMessage = {
  role: Role;
  message_type: MessageTypeEnum;
  content: string;
  transitory: boolean;
  state: State;
  id: string;
};

function createUIMsg(
  role: Role,
  message_type: MessageTypeEnum,
  content: string,
  state: State,
  transitory: boolean = false,
  id: string = ""
): UIMessage {
  return {
    role,
    message_type,
    content,
    state,
    transitory,
    id,
  };
}

export async function initializeP9SDK(apiKey: string): Promise<any> {
  if (sdkInitialized.get()) {
    return true;
  }
  try {
    p9 = await P9SDK.create(apiKey);
    console.log("P9SDK initialized");
    userInfo = (await p9.getUserInfo()) as UserInfo;
    console.log("Valid API Key for:", userInfo.user.id);
    if (!userInfo) {
      console.error("Failed to get user info - invalid API key?");
      stored_key = "";
      return false;
    }
    sdkInitialized.set(true);
    console.log("User info:", userInfo);
    // extract key user properties we need
    p9Key.set(apiKey);
    p9URL.set(p9.getBaseUrl());
    console.log("P9 URL:", p9URL.get());
    isAdmin.set(userInfo.user.type === "admin");
    canDisableLogging.set(userInfo.user.can_disable_logging as boolean);
    username.set(userInfo.user.id);
    organization.set(userInfo.user.org_id);
    sessionList.set(userInfo.sessions || []);
    modelList.set(["P9-latest"]); // FIXME: export in typescript sdk
    isAuth.set(true);
    if (
      userInfo &&
      userInfo.sessions &&
      userInfo.sessions?.length > 0 &&
      userInfo.sessions[0]?.id
    ) {
      sdkInitialized.set(true);
    }
    return true;
  } catch (error) {
    console.error("Failed to initialize P9SDK or session:", error);
    stored_key = "";
    localStorage.removeItem("p9_api_key");
    error = "Invalid API key. Please try again.";
    isAuth.set(false);
    sdkInitialized.set(false);
    return false;
  }
}

export async function createSession(
  name: string = "",
  description: string = ""
) {
  console.log(ttl, name, description, isSessionLogging.get());
  session = await p9.newSession(ttl, name, description, isSessionLogging.get());
  streamer.set(await session.streamer(onmessage as any));
  currentSession.set(session);
  sessionID.set(session.id || "");
  sessionName.set(session.name);
  console.log(session);
  return session;
}

export async function resumeSession(session_id: string) {
  try {
    session = await p9.resumeSession(session_id);
    console.log(session);
    currentSession.set(session);
    sessionID.set(session.id || "");
    sessionName.set(session.name);
    // @ts-ignore
    files.set(session._session.files);
    streamer.set(await session.streamer(onmessage as any));
    if (session.canLog) {
      isSessionLogging.set(true);
    } else {
      isSessionLogging.set(false);
    }
    return session;
  } catch (error) {
    console.error("Failed to resume session:", error);
    return null;
  }
}

function onmessage(message: Message) {
  let now = Date.now();
  console.log("received", message.state, message.message_type);
  switch (message.message_type) {
    case MessageTypeEnum.RESULT:
      // clear transitory messages
      history.set(history.get().filter((msg) => !msg.transitory));

      history.set([
        ...history.get(),
        createUIMsg(
          "assistant",
          MessageTypeEnum.RESULT,
          message.content || "",
          message.state || StateEnum.START,
          false,
          message.id || ""
        ),
      ]);
      break;
    case MessageTypeEnum.INFO:
      //clear previous transitory messages
      history.set(history.get().filter((msg) => !msg.transitory));
      history.set([
        ...history.get(),
        createUIMsg(
          "assistant",
          MessageTypeEnum.INFO,
          message.content || "",
          message.state || StateEnum.START,
          true,
          message.id || ""
        ),
      ]);
      break;
    case MessageTypeEnum.ERROR:
      history.set(history.get().filter((msg) => !msg.transitory));
      history.set([
        ...history.get(),
        createUIMsg(
          "assistant",
          MessageTypeEnum.ERROR,
          message.content || "",
          message.state || StateEnum.START,
          false,
          message.id || ""
        ),
      ]);
      break;
    case MessageTypeEnum.DEBUG:
      // Add message with timing information
      const messageWithTiming = {
        ...message,
        receivedAt: now,
        elapsedTime: now - sessionStartTime,
      };
      debugMessages = [...debugMessages, messageWithTiming];
      break;
    default:
      console.debug("Received message type", message.message_type);
  }
}

export function handleSend(input_field: string) {
  if (input_field.trim().length >= 3) {
    var msgState = StateEnum.QUERY;
    if (history.get().length < 2) {
      sessionStartTime = Date.now();
      // @ts-ignore
      msgState = StateEnum.INITIAL_QUERY;
    }

    const uimsg = createUIMsg(
      "user",
      MessageTypeEnum.QUERY,
      input_field,
      msgState,
      false
    );

    history.set([...history.get(), uimsg]);
    streamer.get()!.send(input_field);
    input_field = "";

    history.set([
      ...history.get(),
      createUIMsg("ui", MessageTypeEnum.INFO, "working", msgState, true),
    ]);
  }
}

export function isSessionInitialized(): boolean {
  return !!currentSession.get() && !!currentStreamer;
}
