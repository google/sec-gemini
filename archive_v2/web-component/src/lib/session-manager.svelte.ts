// src/utils/session-manager.ts
import SecGemini, {
  InteractiveSession,
  MessageTypeEnum,
  StateEnum,
  Streamer,
  type Message,
  type State,
  type PublicUser,
} from "sec-gemini";
import {
  p9Key,
  p9URL,
  isAuth,
  modelList,
  isAdmin,
  isSessionLogging,
  logging,
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
  currentModel,
  thinking,
} from "../state/store.svelte.ts";

// Global variables
let ttl: number = 86400;
let secGemini: SecGemini;
let userInfo: PublicUser | null;
let session: InteractiveSession;
let stored_key = "";
let currentStreamer: Streamer | null = null;
let sessionStartTime = $state<number>(0);
let debugMessages = $state<
  (Message & { receivedAt: number; elapsedTime: number })[]
>([]);

type Role = "user" | "agent" | "system";

type UIMessage = {
  role: Role;
  message_type: MessageTypeEnum;
  actor: string;
  title: string | null;
  content: string;
  transitory: boolean;
  state: State;
  id: string;
  streaming: boolean;
};

function createUIMsg(
  role: Role,
  message_type: MessageTypeEnum,
  actor: string,
  title: string | null,
  content: string,
  state: State,
  transitory: boolean = false,
  id: string = "",
  streaming: boolean = false
): UIMessage {
  return {
    role,
    message_type,
    actor,
    title,
    content,
    state,
    transitory,
    id,
    streaming,
  };
}

export async function initializeSecGemini(apiKey: string): Promise<any> {
  if (sdkInitialized.get()) {
    return true;
  }
  try {
    secGemini = await SecGemini.create(apiKey);
    console.log("SecGemini initialized");
    userInfo = secGemini.getUser();
    console.log("Valid API Key for:", userInfo!.id);
    if (!userInfo) {
      console.error("Failed to get user info - invalid API key?");
      stored_key = "";
      return false;
    }
    sdkInitialized.set(true);
    console.log("User info:", userInfo);
    // extract key user properties we need
    p9Key.set(apiKey);
    p9URL.set(secGemini.getBaseUrl());
    console.log("P9 URL:", p9URL.get());
    isAdmin.set(userInfo.type === "admin");
    if (userInfo.can_disable_logging === true && userInfo.never_log === false) {
      logging.set({ showToggle: true, loggingEnabled: true });
    } else if (userInfo.never_log === true) {
      logging.set({ showToggle: false, loggingEnabled: false });
    } else if (
      userInfo.can_disable_logging === false &&
      userInfo.never_log === false
    ) {
      logging.set({ showToggle: false, loggingEnabled: true });
    }
    username.set(userInfo.id);
    organization.set(userInfo.org_id);
    const user = secGemini.getUserInfo();
    console.log(user);
    if (user) {
      sessionList.set(user.sessions || []);
      modelList.set(user.available_models || []);
      currentModel.set(modelList.get()[0]);
      sdkInitialized.set(true);
    }
    isAuth.set(true);
    return true;
  } catch (error) {
    console.error("Failed to initialize SecGemini or session:", error);
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
  // console.log(currentModel.get());
  session = await secGemini.createSession({
    logSession: isSessionLogging.get(),
    model: "stable",
  });
  streamer.set(await session.streamer(onmessage as any));
  currentSession.set(session);
  sessionID.set(session.id || "");
  sessionName.set(session.name);
  console.log(session);
  return session;
}

export async function resumeSession(session_id: string) {
  try {
    console.log(secGemini);
    session = await secGemini.resumeSession(session_id);
    console.log(session);
    currentSession.set(session);
    sessionID.set(session.id || "");
    sessionName.set(session.name);
    // @ts-ignore
    files.set(session._session.files);
    streamer.set(await session.streamer(onmessage as any));
    if (session.can_log) {
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
  console.log("received", message);
  switch (message.message_type) {
    case MessageTypeEnum.RESULT:
      // clear transitory messages
      if (message.actor === "user") {
        // temp hide last message
        // thinking.set(thinking.get().filter((msg) => !msg.transitory));
        // thinking.set([
        //   ...thinking.get(),
        //   createUIMsg(
        //     "agent",
        //     MessageTypeEnum.RESULT,
        //     message.content || "",
        //     message.state || StateEnum.START,
        //     false,
        //     message.id || "",
        //     true
        //   ),
        // ]);
      } else {
        history.set(history.get().filter((msg) => !msg.transitory));
        history.set([
          ...history.get(),
          createUIMsg(
            "agent",
            MessageTypeEnum.RESULT,
            message.actor || "",
            message.title || null,
            message.content || "",
            message.state || StateEnum.START,
            false,
            message.id || "",
            true
          ),
        ]);
      }
      break;
    case MessageTypeEnum.INFO:
      //clear previous transitory messages
      history.set(history.get().filter((msg) => !msg.transitory));
      history.set([
        ...history.get(),
        createUIMsg(
          "agent",
          MessageTypeEnum.INFO,
          "agent",
          null,
          message.content || "",
          message.state || StateEnum.START,
          true,
          message.id || ""
        ),
      ]);
      break;
    case MessageTypeEnum.THINKING:
      thinking.set([
        ...thinking.get(),
        createUIMsg(
          "agent",
          MessageTypeEnum.RESULT,
          message.actor || "",
          message.title || null,
          message.content || "",
          message.state || StateEnum.START,
          false,
          message.id || "",
          true
        ),
      ]);
      break;
    case MessageTypeEnum.ERROR:
      history.set(history.get().filter((msg) => !msg.transitory));
      history.set([
        ...history.get(),
        createUIMsg(
          "agent",
          MessageTypeEnum.ERROR,
          message.actor || "",
          message.title || null,
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
    const uimsg = createUIMsg(
      "user",
      MessageTypeEnum.QUERY,
      "user",
      null,
      input_field,
      "query",
      false,
      Math.random().toString(36).substring(2, 15)
    );
    const placeholdermsg = createUIMsg(
      "agent",
      MessageTypeEnum.INFO,
      "agent",
      null,
      "Just a sec...",
      "thinking",
      true,
      Math.random().toString(36).substring(2, 15)
    );

    history.set([...history.get(), uimsg, placeholdermsg]);
    streamer.get()!.send(input_field);
    input_field = "";

    history.set([
      ...history.get(),
      createUIMsg(
        "system",
        MessageTypeEnum.INFO,
        "orchestrator",
        null,
        "working",
        "start",
        true,
        Math.random().toString(36).substring(2, 15)
      ),
    ]);
  }
}

export function isSessionInitialized(): boolean {
  return !!currentSession.get() && !!currentStreamer;
}
