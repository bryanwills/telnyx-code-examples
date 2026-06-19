package main

import (
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/team-telnyx/telnyx-go/v4"
	"github.com/team-telnyx/telnyx-go/v4/option"
)

// verifyTelnyxSignature verifies the Telnyx Ed25519 webhook signature (stdlib only).
// Requires imports: crypto/ed25519, encoding/base64, net/http, os, strconv, time.
func verifyTelnyxSignature(body []byte, header http.Header) bool {
	sigB64 := header.Get("telnyx-signature-ed25519")
	ts := header.Get("telnyx-timestamp")
	pubB64 := os.Getenv("TELNYX_PUBLIC_KEY")
	if sigB64 == "" || ts == "" || pubB64 == "" {
		return false
	}
	t, err := strconv.ParseInt(ts, 10, 64)
	if err != nil {
		return false
	}
	if d := time.Now().Unix() - t; d > 300 || d < -300 {
		return false
	}
	pub, err := base64.StdEncoding.DecodeString(pubB64)
	if err != nil || len(pub) != ed25519.PublicKeySize {
		return false
	}
	sig, err := base64.StdEncoding.DecodeString(sigB64)
	if err != nil {
		return false
	}
	return ed25519.Verify(ed25519.PublicKey(pub), []byte(ts+"|"+string(body)), sig)
}

// WebhookPayload represents the structure of a Telnyx webhook event.
// For Call Control events the event-specific fields live under
// data.payload, while data carries the envelope (event_type, id, etc.).
type WebhookPayload struct {
	Data struct {
		EventType string `json:"event_type"`
		Payload   struct {
			CallControlID  string `json:"call_control_id"`
			From           string `json:"from"`
			To             string `json:"to"`
			State          string `json:"state"`
			Direction      string `json:"direction"`
			StartTime      string `json:"start_time"`
			AnswerTime     string `json:"answer_time"`
			EndTime        string `json:"end_time"`
			DisconnectCode string `json:"disconnect_code"`
		} `json:"payload"`
	} `json:"data"`
}

func init() {
	// Load environment variables from .env file
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using system environment variables")
	}
}

func main() {
	// Initialize Telnyx client with the API key from the environment.
	// NewClient returns a value, so we take its address to share a single
	// client across handlers. Inbound webhook signatures are verified
	// separately via verifyTelnyxSignature using TELNYX_PUBLIC_KEY.
	clientValue := telnyx.NewClient(
		option.WithAPIKey(os.Getenv("TELNYX_API_KEY")),
	)
	client := &clientValue

	// Create Gin router
	router := gin.Default()

	// Middleware to log incoming requests
	router.Use(gin.Logger())

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})

	// Webhook endpoint for inbound call events
	router.POST("/webhooks/call", func(c *gin.Context) {
		handleCallWebhook(c, client)
	})

	// Start server on configured port
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Starting Gin server on port %s\n", port)
	if err := router.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

// handleCallWebhook processes inbound call events from Telnyx.
func handleCallWebhook(c *gin.Context, client *telnyx.Client) {
	// Read the raw request body. The signature is computed over the exact
	// bytes Telnyx sent, so we must verify before any JSON decoding.
	body, err := io.ReadAll(c.Request.Body)
	if err != nil {
		log.Printf("Failed to read webhook body: %v\n", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	// ENFORCE-ALWAYS: verify the Telnyx Ed25519 webhook signature using the
	// raw body and the request headers. Reject unverified requests with 401
	// before processing any event.
	if !verifyTelnyxSignature(body, c.Request.Header) {
		log.Println("Webhook signature verification failed")
		c.Writer.WriteHeader(http.StatusUnauthorized)
		return
	}

	var payload WebhookPayload

	// Parse the verified JSON payload from the raw body.
	if err := json.Unmarshal(body, &payload); err != nil {
		log.Printf("Invalid webhook payload: %v\n", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON payload"})
		return
	}

	eventType := payload.Data.EventType
	callControlID := payload.Data.Payload.CallControlID
	from := payload.Data.Payload.From
	to := payload.Data.Payload.To

	log.Printf("Received webhook: event_type=%s, call_control_id=%s, from=%s, to=%s\n",
		eventType, callControlID, from, to)

	// Handle different call lifecycle events
	switch eventType {
	case "call.initiated":
		handleCallInitiated(c, callControlID, from, to, client)

	case "call.answered":
		handleCallAnswered(c, callControlID, from, to)

	case "call.hangup":
		handleCallHangup(c, callControlID, payload.Data.Payload.DisconnectCode)

	case "call.dtmf.received":
		handleDTMFReceived(c, callControlID)

	default:
		log.Printf("Unhandled event type: %s\n", eventType)
		c.JSON(http.StatusOK, gin.H{"message": "Event received"})
	}
}

// handleCallInitiated processes the call.initiated event.
// This fires when an inbound call arrives at your Telnyx number.
func handleCallInitiated(c *gin.Context, callControlID, from, to string, client *telnyx.Client) {
	log.Printf("Call initiated from %s to %s\n", from, to)

	// Automatically answer the call. The call_control_id is a path parameter;
	// the params struct carries optional answer settings.
	// In production, you might add logic to screen calls, route to agents, etc.
	response, err := client.Calls.Actions.Answer(
		c.Request.Context(),
		callControlID,
		telnyx.CallActionAnswerParams{},
	)
	if err != nil {
		log.Printf("Failed to answer call: %v\n", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to answer call"})
		return
	}

	log.Printf("Call answered successfully: %+v\n", response)

	// Return 200 OK to acknowledge webhook receipt
	c.JSON(http.StatusOK, gin.H{
		"message":         "Call answered",
		"call_control_id": callControlID,
	})
}

// handleCallAnswered processes the call.answered event.
// This fires when the call is successfully connected.
func handleCallAnswered(c *gin.Context, callControlID, from, to string) {
	log.Printf("Call answered: from=%s, to=%s\n", from, to)

	// In production, you might:
	// - Start recording the call
	// - Play a greeting message
	// - Route to an IVR menu
	// - Log call metadata to a database

	c.JSON(http.StatusOK, gin.H{
		"message":         "Call answered event processed",
		"call_control_id": callControlID,
	})
}

// handleCallHangup processes the call.hangup event.
// This fires when either party disconnects.
func handleCallHangup(c *gin.Context, callControlID, disconnectCode string) {
	log.Printf("Call ended: call_control_id=%s, disconnect_code=%s\n", callControlID, disconnectCode)

	// In production, you might:
	// - Stop recording and save the file
	// - Update call duration in database
	// - Trigger post-call workflows (transcription, analysis, etc.)

	c.JSON(http.StatusOK, gin.H{
		"message":         "Call hangup event processed",
		"call_control_id": callControlID,
	})
}

// handleDTMFReceived processes DTMF (dial tone) events.
// This fires when the caller presses a digit during the call.
func handleDTMFReceived(c *gin.Context, callControlID string) {
	log.Printf("DTMF received on call: %s\n", callControlID)

	// In production, you might:
	// - Route based on digit pressed (IVR menu)
	// - Validate PIN entry
	// - Trigger actions based on user input

	c.JSON(http.StatusOK, gin.H{
		"message":         "DTMF event processed",
		"call_control_id": callControlID,
	})
}
