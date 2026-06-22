package main

import (
	"errors"
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/team-telnyx/telnyx-go/v4"
	"github.com/team-telnyx/telnyx-go/v4/option"
)

func init() {
	// Load environment variables from .env when present. In production the
	// values are typically injected by the platform, so a missing file is
	// not an error.
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using system environment variables")
	}
}

// ChatRequest is the JSON body accepted by POST /chat.
//
// Message is the end-user's turn. ConversationID is optional: omit it on the
// first request to start a new thread, then echo back the value returned by
// the server on every subsequent request to keep the assistant's context.
type ChatRequest struct {
	Message        string `json:"message"`
	ConversationID string `json:"conversation_id"`
}

// ChatResponse is returned by POST /chat. ConversationID must be sent back on
// the next request to maintain conversation context.
type ChatResponse struct {
	ConversationID string `json:"conversation_id"`
	Reply          string `json:"reply"`
}

func main() {
	apiKey := os.Getenv("TELNYX_API_KEY")
	if apiKey == "" {
		log.Fatal("TELNYX_API_KEY is required")
	}
	assistantID := os.Getenv("TELNYX_ASSISTANT_ID")
	if assistantID == "" {
		log.Fatal("TELNYX_ASSISTANT_ID is required")
	}

	// NewClient returns a value; take its address so a single client is
	// shared across requests.
	clientValue := telnyx.NewClient(option.WithAPIKey(apiKey))
	client := &clientValue

	router := gin.Default()

	// Liveness probe.
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})

	// Chat endpoint.
	router.POST("/chat", func(c *gin.Context) {
		handleChat(c, client, assistantID)
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Starting Gin server on port %s\n", port)
	if err := router.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

// handleChat sends one user turn to the AI assistant and returns its reply.
//
// On the first turn (no conversation_id supplied), it creates a conversation
// via the Conversations API so the assistant can maintain context across
// turns. The conversation id is returned to the client and must be supplied
// on every subsequent request.
func handleChat(c *gin.Context, client *telnyx.Client, assistantID string) {
	var req ChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}
	if req.Message == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "message is required"})
		return
	}

	ctx := c.Request.Context()
	conversationID := req.ConversationID

	// Start a new conversation thread when the client did not supply one.
	if conversationID == "" {
		conversation, err := client.AI.Conversations.New(ctx, telnyx.AIConversationNewParams{
			Metadata: map[string]string{"assistant_id": assistantID},
		})
		if err != nil {
			respondTelnyxError(c, err, "Failed to start conversation")
			return
		}
		conversationID = conversation.ID
	}

	// Send the user turn to the assistant. The assistant uses the
	// conversation id to maintain context across turns.
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
}

// respondTelnyxError maps a Telnyx API error to a safe HTTP response. The
// full error is logged server-side; the client only receives a generic
// message and, when available, the upstream status code — never raw
// exception or response details.
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
