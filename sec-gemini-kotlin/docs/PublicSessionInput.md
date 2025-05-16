
# PublicSessionInput

## Properties
| Name | Type | Description | Notes |
| ------------ | ------------- | ------------- | ------------- |
| **userId** | **kotlin.String** | The user ID this session belongs to. |  |
| **orgId** | **kotlin.String** | The organization ID this session belongs to. |  |
| **model** | [**ModelInfoInput**](ModelInfoInput.md) | Model configuration used in the session. |  |
| **ttl** | **kotlin.Int** | The time to live of the session in seconds. |  |
| **name** | **kotlin.String** | Human readable session name. |  |
| **description** | **kotlin.String** | A brief description to help users remember what the session is about. |  |
| **id** | **kotlin.String** | Session unique ramdom identifier. |  [optional] |
| **language** | **kotlin.String** | The iso-code of the session language. |  [optional] |
| **turns** | **kotlin.Int** | The number of turns in the session. |  [optional] |
| **createTime** | **kotlin.Int** | The Unix timestamp (in seconds) of when the session was created. |  [optional] |
| **updateTime** | **kotlin.Int** | The Unix timestamp (in seconds) of when the session was last updated. |  [optional] |
| **numMessages** | **kotlin.Int** | The number of messages in the session. |  [optional] |
| **messages** | [**kotlin.collections.List&lt;Message&gt;**](Message.md) | The list of messages comprising the session so far. |  [optional] |
| **usage** | [**Usage**](Usage.md) | Session usage statistics. |  [optional] |
| **canLog** | **kotlin.Boolean** | Whether the session can be logged or not. |  [optional] |
| **state** | [**State**](State.md) | The state the session belongs to. |  [optional] |
| **files** | [**kotlin.collections.List&lt;PublicSessionFile&gt;**](PublicSessionFile.md) | The list of files uploaded to the session. |  [optional] |



