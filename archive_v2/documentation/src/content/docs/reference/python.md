---
title: Python Reference
description: Sec-Gemini SDK Python Reference
---

#### `SecGemini`
 - `()`: instantiates the SecGemini object.
    - `api_key` (required): the API key to use when connecting to Sec-Gemini.
 - `create_session()`: Creates a new session. Returns an `InteractiveSession`.
    - `name` (optional): a name for the session; If not specified, a name will be automatically generated.
    - `description` (optional): a description for the session. Default: ""
    - `ttl` (optional): time-to-live value for the session, in seconds; the session will automatically deleted after this many seconds. Default: 86400
    - `enable_logging` (optional): if True, prompts and responses will be retained and may be analyzed to improve the service. if False, **and the API key allows for it**, prompts and responses will not be retained. Default: True

 - `list_sessions()`: returns a list of `InteractiveSession` of all active user sessions.

 - `resume_session()`: resumes an existing session. Returns an `InteractiveSesion`.
    - `session_id` (Required): ID of the session to resume

#### `InteractiveSession`
 - `files`: list of files attached to the session
 - `can_log`: whether or not prompts/responses in the session will be retained.

 - `attach_file_from_disk()`: Attach a file from disk to the session.
    - `file_path` (str, required): the full path of the local file to attach. The file will be attached to the session with the name matching its local filename.

 - `attach_file()`: Attach a file to the session.
    - `filename` (str, required): name used to refer to the file in the session
    - `content` (bytes, required): file content
    - `mime_type_hint` (str, optional):  

 - `detach_file()`: Detach a file from the session.
    - `session_id` (str, required): the ID of the session to detach the file from
    - `file_idx` (int, required): the index of the file to detach in the `files` list.

 - `delete()`: Delete the session.

 - `update()`: Make changes to the session.
   - `name` (str, optional): new name for the session.
   - `description`: new description for the session.
   - `ttl` (int, optional): new time-to-live value for the session, in seconds, from the current time. Minimum 300 seconds.

- `query()`: send a message to SecGemini. Returns `SessionResponse`.
   - `prompt` (str, required): The message to send.

- `stream()` (async): streaming generation/completion request
   - `prompt` (str, required): The message to send.

- `history()`: List of messages in the session.

- `visualize()`: Tree view of session history.

- `send_bug_report()`: Submit a bug report.
   - `bug` (str, required): the descriptive text of the bug report.
   - `group_id` (str, optional): 

- `send_feedback()`: Submit feedback about an interaction with Sec-Gemini.
   - `score` (int, required): integer value representing the sentiment of the feedback. >0 is positive feedback, <=0 is negative feedback.
   - `group_id` (str, optional): 


#### `SessionResponse`
   - `messages`: a list of `Message` in the session.
   - `status_code`: status of the latest response; 2xx is OK, 4xx is a client error, 5xx is a server error.
   - `status_message`: a message explaining the `status_code`.
   - `usage`: usage statistics of the latest response.

   - `text()`: Create a list of `messages.content` in the session.

`
