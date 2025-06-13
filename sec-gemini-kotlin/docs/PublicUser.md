
# PublicUser

## Properties
| Name | Type | Description | Notes |
| ------------ | ------------- | ------------- | ------------- |
| **id** | **kotlin.String** | The user ID this session belongs to. |  |
| **orgId** | **kotlin.String** | The organization ID this session belongs to. |  |
| **type** | [**UserType**](UserType.md) | The type of user. |  [optional] |
| **neverLog** | **kotlin.Boolean** | The user session should never be logged. |  [optional] |
| **canDisableLogging** | **kotlin.Boolean** | Is user authorized to disable logging. |  [optional] |
| **keyExpireTime** | **kotlin.Int** | The Unix timestamp (in seconds) of when the key will expire. |  [optional] |
| **tpm** | **kotlin.Int** | Tokens per minute quota. |  [optional] |
| **rpm** | **kotlin.Int** | Requests per minute quota. |  [optional] |
| **allowExperimental** | **kotlin.Boolean** | Whether the user is allowed to use experimental features. |  [optional] |
| **vendors** | [**kotlin.collections.List&lt;PublicUserVendor&gt;**](PublicUserVendor.md) | The list of vendors the user has access to. |  [optional] |



