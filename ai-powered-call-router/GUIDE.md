# Guide: AI-Powered Call Router

This guide walks through the `ai-powered-call-router` example, a Flask application that uses Telnyx Call Control, the Telnyx AI Inference API, and an in-memory routing table to intelligently route inbound calls based on the caller's spoken intent.

## Architecture Overview

When a caller dials your Telnyx number, Telnyx sends a webhook to your Flask app. The application answers the call, plays a greeting, and starts gathering speech. Once the caller speaks, the audio is transcribed and sent to the Telnyx AI Inference API to classify the intent (e.g., "billing", "sales", or "support"). The app then looks up the correct destination in a route table and transfers the call.

```text
Inbound Call → Telnyx Webhook → Answer Call → Gather Speech → LLM Intent Classification → KV Route Lookup → Transfer Call
```

## Prerequisites

* Python 3.9+
* A Telnyx account with a Call Control Application configured
* A Telnyx phone number mapped to your Call Control Application
* ngrok or a similar tool to expose your local server to the internet for webhooks

## Environment Setup

1. Clone the repository and navigate to the `ai-powered-call-router` directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the example environment file and update it with your credentials:
   ```bash
   cp .env.example .env
   ```
   * `TELNYX_API_KEY`: Your Telnyx API key.
   * `TELNYX_PUBLIC_KEY`: Your Telnyx public key (used for webhook signature verification).
   * `TELNYX_CONNECTION_ID`: Your Call Control Connection ID.
   * `PORT`: The port to run the Flask app on (defaults to 5000).

## Running the Application

Start the Flask server:
```bash
python app.py
```

Expose your local server using ngrok:
```bash
ngrok http 5000
```

In your Telnyx Call Control Application settings, set the webhook URL to `https://<your-ngrok-url>.ngrok.io/webhook`.

## How It Works

### 1. Initialization and Route Table

At the top of `app.py`, the application loads environment variables, initializes the Telnyx SDK with your API key, and defines the in-memory route table.

```python
ROUTE_TABLE = {
    "billing": "+18005551234",
    "sales": "+18005556789",
    "support": "+18005550000",
}
DEFAULT_DESTINATION = "+18005550000"
```

This KV-like route table maps intent labels to phone numbers. In a production environment, you would replace this with Telnyx KV or a Redis database. The `DEFAULT_DESTINATION` is used as a fallback for unrecognized intents.

### 2. Webhook Verification

Telnyx sends call events to the `/webhook` endpoint. Security is critical, so the app verifies the Ed25519 signature of every incoming request.

```python
event = telnyx.Webhook.unwrap(
    raw_body,
    signature,
    timestamp,
    TELNYX_PUBLIC_KEY,
)
```

If the signature is invalid, the app logs the error and returns a `401 Unauthorized` response without leaking exception details.

### 3. Answering the Call

When a new inbound call arrives, Telnyx sends a `call.initiated` event. The app checks if the call direction is `incoming` and answers it using Call Control:

```python
telnyx.Call.answer(call_control_id=call_control_id)
```

### 4. Gathering Speech

Once the call is answered (`call.answered` event), the app plays a text-to-speech prompt and starts gathering speech from the caller.

```python
telnyx.Call.playback_start(
    call_control_id=call_control_id,
    payload={
        "media": [
            {
                "type": "text",
                "text": "Hello, please tell me briefly how I can help you today.",
            }
        ]
    },
)
telnyx.Call.gather_using_speech(
    call_control_id=call_control_id,
    payload={...},
)
```

### 5. LLM Intent Classification

When the gather completes (`call.gather.ended`), the transcribed speech is sent to the Telnyx AI Inference API (OpenAI binding) to classify the intent.

```python
completion = telnyx.ai.openai.chat.create_completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=10,
    temperature=0.0,
)
```

The prompt instructs the LLM to respond with exactly one of: `billing`, `sales`, or `support`. If the classification fails, the app safely catches the exception and defaults to the `support` intent.

### 6. Transferring the Call

The classified intent is used to look up the destination in the `ROUTE_TABLE`. The app then transfers the call using Call Control.

```python
destination = ROUTE_TABLE.get(intent, DEFAULT_DESTINATION)
telnyx.Call.transfer(
    call_control_id,
    to=destination,
    timeout_secs=30,
)
```

If the gather fails entirely (`call.gather.failed`), the app gracefully falls back to transferring the call to the `DEFAULT_DESTINATION`.

## Telnyx Primitives Used

* **Call Control**: Used to answer, gather speech, play audio, and transfer the call.
* **AI Inference (OpenAI binding)**: Used to classify the caller's intent from transcribed speech.
* **KV (In-Memory)**: A simple dictionary acting as a route table to map intents to destinations.

## Next Steps

* Explore the [Telnyx Call Control API Reference](https://developers.telnyx.com/docs/api/v2/call-control) for more call commands.
* Learn more about [Telnyx AI Inference](https://developers.telnyx.com/docs/ai-communications-infrastructure).
* Replace the in-memory route table with a persistent store like Telnyx KV or Redis.
* Add support for more intents and dynamic routing logic.
