# DefaultApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
| ------------- | ------------- | ------------- |
| [**attachV1SessionAttachFilePost**](DefaultApi.md#attachV1SessionAttachFilePost) | **POST** /v1/session/attach_file | Attach |
| [**completeChatCompletionsPost**](DefaultApi.md#completeChatCompletionsPost) | **POST** /chat/completions | Complete |
| [**deleteFileV1SessionDeleteFilePost**](DefaultApi.md#deleteFileV1SessionDeleteFilePost) | **POST** /v1/session/delete_file | Delete File |
| [**deleteV1SessionDeletePost**](DefaultApi.md#deleteV1SessionDeletePost) | **POST** /v1/session/delete | Delete |
| [**diagnosticsV1SystemDiagnosticGet**](DefaultApi.md#diagnosticsV1SystemDiagnosticGet) | **GET** /v1/system/diagnostic | Diagnostics |
| [**feedbackV1SessionFeedbackPost**](DefaultApi.md#feedbackV1SessionFeedbackPost) | **POST** /v1/session/feedback | Feedback |
| [**generateV1SessionGeneratePost**](DefaultApi.md#generateV1SessionGeneratePost) | **POST** /v1/session/generate | Generate |
| [**getAgentGraphV1SystemAgentGraphGet**](DefaultApi.md#getAgentGraphV1SystemAgentGraphGet) | **GET** /v1/system/agent_graph | Get Agent Graph |
| [**getAgentV1SystemAgentGet**](DefaultApi.md#getAgentV1SystemAgentGet) | **GET** /v1/system/agent | Get Agent |
| [**getGet**](DefaultApi.md#getGet) | **GET** / | Get |
| [**getV1SessionGetGet**](DefaultApi.md#getV1SessionGetGet) | **GET** /v1/session/get | Get |
| [**healthCheckHealthGet**](DefaultApi.md#healthCheckHealthGet) | **GET** /health | Health Check |
| [**infoV1UserInfoGet**](DefaultApi.md#infoV1UserInfoGet) | **GET** /v1/user/info | Info |
| [**listV1SessionListGet**](DefaultApi.md#listV1SessionListGet) | **GET** /v1/session/list | List |
| [**registerV1SessionRegisterPost**](DefaultApi.md#registerV1SessionRegisterPost) | **POST** /v1/session/register | Register |
| [**tsMockV1ExperimentalTsGet**](DefaultApi.md#tsMockV1ExperimentalTsGet) | **GET** /v1/experimental/ts | Ts Mock |
| [**updateV1SessionUpdatePost**](DefaultApi.md#updateV1SessionUpdatePost) | **POST** /v1/session/update | Update |


<a id="attachV1SessionAttachFilePost"></a>
# **attachV1SessionAttachFilePost**
> OpResult attachV1SessionAttachFilePost(attachment)

Attach

Upload a file to cloud bucket and attach it to the session

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
val attachment : Attachment =  // Attachment | 
try {
    val result : OpResult = apiInstance.attachV1SessionAttachFilePost(attachment)
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#attachV1SessionAttachFilePost")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#attachV1SessionAttachFilePost")
    e.printStackTrace()
}
```

### Parameters
| Name | Type | Description  | Notes |
| ------------- | ------------- | ------------- | ------------- |
| **attachment** | [**Attachment**](Attachment.md)|  | |

### Return type

[**OpResult**](OpResult.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a id="completeChatCompletionsPost"></a>
# **completeChatCompletionsPost**
> ChatCompletionResponse completeChatCompletionsPost(chatCompletionRequest)

Complete

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
val chatCompletionRequest : ChatCompletionRequest =  // ChatCompletionRequest | 
try {
    val result : ChatCompletionResponse = apiInstance.completeChatCompletionsPost(chatCompletionRequest)
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#completeChatCompletionsPost")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#completeChatCompletionsPost")
    e.printStackTrace()
}
```

### Parameters
| Name | Type | Description  | Notes |
| ------------- | ------------- | ------------- | ------------- |
| **chatCompletionRequest** | [**ChatCompletionRequest**](ChatCompletionRequest.md)|  | |

### Return type

[**ChatCompletionResponse**](ChatCompletionResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a id="deleteFileV1SessionDeleteFilePost"></a>
# **deleteFileV1SessionDeleteFilePost**
> OpResult deleteFileV1SessionDeleteFilePost(attachment)

Delete File

Delete a file from the session

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
val attachment : Attachment =  // Attachment | 
try {
    val result : OpResult = apiInstance.deleteFileV1SessionDeleteFilePost(attachment)
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#deleteFileV1SessionDeleteFilePost")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#deleteFileV1SessionDeleteFilePost")
    e.printStackTrace()
}
```

### Parameters
| Name | Type | Description  | Notes |
| ------------- | ------------- | ------------- | ------------- |
| **attachment** | [**Attachment**](Attachment.md)|  | |

### Return type

[**OpResult**](OpResult.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a id="deleteV1SessionDeletePost"></a>
# **deleteV1SessionDeletePost**
> OpResult deleteV1SessionDeletePost(publicSessionInput)

Delete

Delete a session

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
val publicSessionInput : PublicSessionInput =  // PublicSessionInput | 
try {
    val result : OpResult = apiInstance.deleteV1SessionDeletePost(publicSessionInput)
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#deleteV1SessionDeletePost")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#deleteV1SessionDeletePost")
    e.printStackTrace()
}
```

### Parameters
| Name | Type | Description  | Notes |
| ------------- | ------------- | ------------- | ------------- |
| **publicSessionInput** | [**PublicSessionInput**](PublicSessionInput.md)|  | |

### Return type

[**OpResult**](OpResult.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a id="diagnosticsV1SystemDiagnosticGet"></a>
# **diagnosticsV1SystemDiagnosticGet**
> kotlin.Any diagnosticsV1SystemDiagnosticGet()

Diagnostics

Returns the diagnostics information for the application.

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
try {
    val result : kotlin.Any = apiInstance.diagnosticsV1SystemDiagnosticGet()
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#diagnosticsV1SystemDiagnosticGet")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#diagnosticsV1SystemDiagnosticGet")
    e.printStackTrace()
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**kotlin.Any**](kotlin.Any.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

<a id="feedbackV1SessionFeedbackPost"></a>
# **feedbackV1SessionFeedbackPost**
> OpResult feedbackV1SessionFeedbackPost(feedback)

Feedback

Record user feedback

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
val feedback : Feedback =  // Feedback | 
try {
    val result : OpResult = apiInstance.feedbackV1SessionFeedbackPost(feedback)
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#feedbackV1SessionFeedbackPost")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#feedbackV1SessionFeedbackPost")
    e.printStackTrace()
}
```

### Parameters
| Name | Type | Description  | Notes |
| ------------- | ------------- | ------------- | ------------- |
| **feedback** | [**Feedback**](Feedback.md)|  | |

### Return type

[**OpResult**](OpResult.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a id="generateV1SessionGeneratePost"></a>
# **generateV1SessionGeneratePost**
> SessionResponse generateV1SessionGeneratePost(sessionRequest)

Generate

Handles generation requests.

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
val sessionRequest : SessionRequest =  // SessionRequest | 
try {
    val result : SessionResponse = apiInstance.generateV1SessionGeneratePost(sessionRequest)
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#generateV1SessionGeneratePost")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#generateV1SessionGeneratePost")
    e.printStackTrace()
}
```

### Parameters
| Name | Type | Description  | Notes |
| ------------- | ------------- | ------------- | ------------- |
| **sessionRequest** | [**SessionRequest**](SessionRequest.md)|  | |

### Return type

[**SessionResponse**](SessionResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a id="getAgentGraphV1SystemAgentGraphGet"></a>
# **getAgentGraphV1SystemAgentGraphGet**
> kotlin.Any getAgentGraphV1SystemAgentGraphGet()

Get Agent Graph

Return SecGemini full graph Returns:     _description_

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
try {
    val result : kotlin.Any = apiInstance.getAgentGraphV1SystemAgentGraphGet()
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#getAgentGraphV1SystemAgentGraphGet")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#getAgentGraphV1SystemAgentGraphGet")
    e.printStackTrace()
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**kotlin.Any**](kotlin.Any.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

<a id="getAgentV1SystemAgentGet"></a>
# **getAgentV1SystemAgentGet**
> kotlin.Any getAgentV1SystemAgentGet(height, experimental)

Get Agent

Provide an overview of sec-gemini agent current configuration

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
val height : kotlin.Int = 56 // kotlin.Int | 
val experimental : kotlin.Boolean = true // kotlin.Boolean | 
try {
    val result : kotlin.Any = apiInstance.getAgentV1SystemAgentGet(height, experimental)
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#getAgentV1SystemAgentGet")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#getAgentV1SystemAgentGet")
    e.printStackTrace()
}
```

### Parameters
| **height** | **kotlin.Int**|  | [optional] [default to 500] |
| Name | Type | Description  | Notes |
| ------------- | ------------- | ------------- | ------------- |
| **experimental** | **kotlin.Boolean**|  | [optional] [default to false] |

### Return type

[**kotlin.Any**](kotlin.Any.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

<a id="getGet"></a>
# **getGet**
> kotlin.Any getGet()

Get

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
try {
    val result : kotlin.Any = apiInstance.getGet()
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#getGet")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#getGet")
    e.printStackTrace()
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**kotlin.Any**](kotlin.Any.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

<a id="getV1SessionGetGet"></a>
# **getV1SessionGetGet**
> PublicSessionOutput getV1SessionGetGet(sessionId)

Get

Get a session

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
val sessionId : kotlin.String = sessionId_example // kotlin.String | 
try {
    val result : PublicSessionOutput = apiInstance.getV1SessionGetGet(sessionId)
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#getV1SessionGetGet")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#getV1SessionGetGet")
    e.printStackTrace()
}
```

### Parameters
| Name | Type | Description  | Notes |
| ------------- | ------------- | ------------- | ------------- |
| **sessionId** | **kotlin.String**|  | |

### Return type

[**PublicSessionOutput**](PublicSessionOutput.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

<a id="healthCheckHealthGet"></a>
# **healthCheckHealthGet**
> kotlin.collections.Map&lt;kotlin.String, kotlin.Any&gt; healthCheckHealthGet()

Health Check

Performs health checks and returns the status of the application and its dependencies.

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
try {
    val result : kotlin.collections.Map<kotlin.String, kotlin.Any> = apiInstance.healthCheckHealthGet()
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#healthCheckHealthGet")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#healthCheckHealthGet")
    e.printStackTrace()
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**kotlin.collections.Map&lt;kotlin.String, kotlin.Any&gt;**](kotlin.Any.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

<a id="infoV1UserInfoGet"></a>
# **infoV1UserInfoGet**
> UserInfo infoV1UserInfoGet()

Info

Handles generation requests.

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
try {
    val result : UserInfo = apiInstance.infoV1UserInfoGet()
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#infoV1UserInfoGet")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#infoV1UserInfoGet")
    e.printStackTrace()
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**UserInfo**](UserInfo.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

<a id="listV1SessionListGet"></a>
# **listV1SessionListGet**
> kotlin.collections.List&lt;PublicSessionOutput&gt; listV1SessionListGet()

List

List all sessions

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
try {
    val result : kotlin.collections.List<PublicSessionOutput> = apiInstance.listV1SessionListGet()
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#listV1SessionListGet")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#listV1SessionListGet")
    e.printStackTrace()
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**kotlin.collections.List&lt;PublicSessionOutput&gt;**](PublicSessionOutput.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

<a id="registerV1SessionRegisterPost"></a>
# **registerV1SessionRegisterPost**
> OpResult registerV1SessionRegisterPost(publicSessionInput)

Register

Register a new session

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
val publicSessionInput : PublicSessionInput =  // PublicSessionInput | 
try {
    val result : OpResult = apiInstance.registerV1SessionRegisterPost(publicSessionInput)
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#registerV1SessionRegisterPost")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#registerV1SessionRegisterPost")
    e.printStackTrace()
}
```

### Parameters
| Name | Type | Description  | Notes |
| ------------- | ------------- | ------------- | ------------- |
| **publicSessionInput** | [**PublicSessionInput**](PublicSessionInput.md)|  | |

### Return type

[**OpResult**](OpResult.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

<a id="tsMockV1ExperimentalTsGet"></a>
# **tsMockV1ExperimentalTsGet**
> kotlin.Any tsMockV1ExperimentalTsGet()

Ts Mock

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
try {
    val result : kotlin.Any = apiInstance.tsMockV1ExperimentalTsGet()
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#tsMockV1ExperimentalTsGet")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#tsMockV1ExperimentalTsGet")
    e.printStackTrace()
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**kotlin.Any**](kotlin.Any.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

<a id="updateV1SessionUpdatePost"></a>
# **updateV1SessionUpdatePost**
> OpResult updateV1SessionUpdatePost(publicSessionInput)

Update

Update session based of client

### Example
```kotlin
// Import classes:
//import org.openapitools.client.infrastructure.*
//import org.openapitools.client.models.*

val apiInstance = DefaultApi()
val publicSessionInput : PublicSessionInput =  // PublicSessionInput | 
try {
    val result : OpResult = apiInstance.updateV1SessionUpdatePost(publicSessionInput)
    println(result)
} catch (e: ClientException) {
    println("4xx response calling DefaultApi#updateV1SessionUpdatePost")
    e.printStackTrace()
} catch (e: ServerException) {
    println("5xx response calling DefaultApi#updateV1SessionUpdatePost")
    e.printStackTrace()
}
```

### Parameters
| Name | Type | Description  | Notes |
| ------------- | ------------- | ------------- | ------------- |
| **publicSessionInput** | [**PublicSessionInput**](PublicSessionInput.md)|  | |

### Return type

[**OpResult**](OpResult.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

