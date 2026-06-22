# Guide: Chat with a Telnyx AI Assistant in Go

This walkthrough builds a small Gin server that lets a client chat with a
Telnyx AI assistant over HTTP, keeping multi-turn context with a
`conversation_id`. By the end you will understand how the two Telnyx
endpoints — create a conversation and chat with an assistant — fit together.

## Prerequisites

- Go 1.22 or newer
- A Telnyx account and API key — [portal.telnyx.com/api-keys](https://portal.telnyx.com/api-keys)
- An AI assistant created in the Portal — [AI Assistants](https://portal.telnyx.com/#/ai/assistants). Copy its ID.

## 1. Project setup

Create a module and add the dependencies:

```bash
mkdir chat-with-ai-assistant-go && cd chat-with-ai-assistant-go
go mod init telnyx-example
go get github.com/team-telnyx/telnyx-go/v4@v4.80.0
go get github.com/gin-gonic/gin@v1.10.0
go get github.com/joho/godotenv@v1.5.1
```

Create `.env` from the template and fill in your values:

```bash
TELNYX_API_KEY=KEY_your_telnyx_api_key_here
TELNYX_ASSISTANT_ID=assistant-abc123
PORT=8080
```

## 2. Initialize the client

The Telnyx Go SDK reads your API key through an option. `NewClient` returns a
value, so take its address to share one client across requests:

```go
clientValue := telnyx.NewClient(option.WithAPIKey(os.Getenv("TELNYX_API_KEY")))
client := &clientValue
```

Fail fast at startup if the API key or assistant ID is missing, rather than
discovering it on the first request:

```go
apiKey := os.Getenv("TELNYX_API_KEY")
if apiKey == "" {
    log.Fatal("TELNYX_API_KEY is required")
}
assistantID := os.Getenv("TELNYX_ASSISTANT_ID")
if assistantID == "" {
    log.Fatal("TELNYX_ASSISTANT_ID is required")
}
```

## 3. Start a conversation on the first turn

A conversation gives the assistant a stable thread to remember context. On the
first turn the client has no `conversation_id`, so create one. The
`assistant_id` metadata makes it easy to find the thread later:

```go
conversation, err := client.AI.Conversations.New(ctx, telnyx.AIConversationNewParams{
    Metadata: map[string]string{"assistant_id": assistantID},
})
if err != nil {
    respondTelnyxError(c, err, "Failed to start conversation")
    return
}
conversationID = conversation.ID
```

## 4. Chat with the assistant

Send the user's message along with the `conversation_id`. The assistant uses
that id to keep context across turns, and the reply text comes back on
`resp.Content`:

```go
resp, err := client.AI.Assistants.Chat(ctx, assistantID, telnyx.AIAssistantChatParams{
    Content:        req.Message,
    ConversationID: conversationID,
})
if err != nil {
    respondTelnyxError(c, err, "Failed to chat with assistant")
    return
}

c.JSON(http.StatusOK, ChatResponse{
    ConversationID: conversationID,
    Reply:          resp.Content,
})
```

Return the `conversation_id` to the client so it can echo it on the next
request — that is how the thread stays continuous.

## 5. Handle errors safely

Never leak upstream error detail to the client. Log the full error
server-side, and return a generic message with the upstream status code when
available:

```go
func respondTelnyxError(c *gin.Context, err error, message string) {
    log.Printf("%s: %v\n", message, err)

    var apiErr *telnyx.Error
    if errors.As(err, &apiErr) {
        status := apiErr.StatusCode
        if status < 400 || status > 599 {
            status = http.StatusBadGateway
        }
        c.JSON(status, gin.H{"error": message})
        return
    }

    c.JSON(http.StatusInternalServerError, gin.H{"error": message})
}
```

`*telnyx.Error` carries `StatusCode`; matching it with `errors.As` lets you
mirror Telnyx's status (for example `401` or `404`) without exposing the raw
response body.

## 6. Run and test

```bash
go run .
```

Start a thread:

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{ "message": "What are your support hours?" }'
```

Continue it by reusing the returned `conversation_id`:

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{ "message": "And on weekends?", "conversation_id": "<id-from-previous-response>" }'
```

The assistant's second reply should reflect the context of the first turn.

## Next steps

- Persist the `conversation_id` per user so chats survive across sessions.
- Add the optional `name` field to `AIAssistantChatParams` to label who is speaking.
- Move the same assistant to phone or SMS — see [route-phone-calls-to-ai-agent-go](../route-phone-calls-to-ai-agent-go/).
