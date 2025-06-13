
# Message

## Properties
| Name | Type | Description | Notes |
| ------------ | ------------- | ------------- | ------------- |
| **messageType** | [**MessageType**](MessageType.md) | The type of message - Generation, Tool Call, or Info. |  |
| **id** | **kotlin.String** | A unique identifier for the message - uuid4 int. |  [optional] |
| **parentId** | **kotlin.String** | The ID of the parent message. |  [optional] |
| **turn** | **kotlin.String** | The turn identifier is used to group/message are part of the same conversation turn. |  [optional] |
| **group** | **kotlin.String** | The Group ID (UUID4) identify messages part of the same generation or action. |  [optional] |
| **actor** | **kotlin.String** | The actor of the message - user or agent. |  [optional] |
| **role** | [**Role**](Role.md) | The role of the messages author. |  [optional] |
| **timestamp** | **kotlin.Int** | The Unix timestamp (in seconds) of when the message was created. |  [optional] |
| **messageSubType** | **kotlin.String** |  |  [optional] |
| **state** | [**State**](State.md) | The state the message belongs to. |  [optional] |
| **content** | **kotlin.String** |  |  [optional] |
| **mimeType** | [**MimeType**](MimeType.md) |  |  [optional] |
| **statusCode** | **kotlin.Int** | The status code of the message. 2xx is Okay, 4xx is a client error, 5xx is a server error. |  [optional] |
| **statusMessage** | **kotlin.String** | Explain status code reason. |  [optional] |
| **usage** | [**Usage**](Usage.md) |  |  [optional] |



