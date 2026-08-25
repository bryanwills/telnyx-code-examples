# Guide: ShipmentAgent — The Actor IS the Package

Welcome to the `shipment-agent` code sample! This tutorial walks you through how we built a durable, autonomous shipment agent using Telnyx's AI Communications Infrastructure. 

In traditional tracking systems, a shipment is just a row in a database. In this architecture, **the actor IS the shipment**. It is a durable entity that lives across days, carriers, and status changes. It proactively contacts the customer when things change, answers calls with full context, and even schedules its own future wake-ups to request feedback.

## Prerequisites

Before you begin, ensure you have the following:
- Python 3.9 or higher
- A Telnyx account with access to:
  - A Telnyx number capable of SMS and Voice (Call Control)
  - A Messaging Profile
  - Telnyx API Key and Public Key
- `ngrok` or another tunneling tool to expose your local Flask server to the internet for webhooks.

## Environment Setup

1. **Clone the repository and navigate to the sample folder:**
   ```bash
   git clone https://github.com/team-telnyx/telnyx-code-examples.git
   cd telnyx-code-examples/shipment-agent
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your environment variables:**
   Copy the `.env.example` file to `.env` and fill in your Telnyx credentials:
   ```bash
   cp .env.example .env
   ```
   ```env
   TELNYX_API_KEY=your_telnyx_api_key_here
   TELNYX_PUBLIC_KEY=your_telnyx_public_key_here
   TELNYX_MESSAGING_PROFILE_ID=your_messaging_profile_id_here
   TELNYX_FROM_NUMBER=+18005551212
   TELNYX_TO_NUMBER=+18005559876
   ```
   *Note: `TELNYX_TO_NUMBER` is used as the default customer phone number for demo purposes.*

5. **Start the Flask server:**
   ```bash
   python app.py
   ```

6. **Expose your local server with ngrok:**
   ```bash
   ngrok http 5000
   ```
   Use the generated ngrok URL to configure your webhooks in the Telnyx Portal.

## How the Code Works

Let's walk through the architecture of the `ShipmentAgent` and how it integrates with Telnyx primitives.

### 1. The Actor IS the Package (`ShipmentAgent` class)

At the core of this sample is the `ShipmentAgent` class. Instead of a passive tracking record, this class encapsulates the shipment's state, history, communication channels, and autonomous behaviors.

When instantiated, the agent binds itself to Telnyx communication channels (using your `TELNYX_FROM_NUMBER` for both SMS and Voice). It maintains its own state machine (`CREATED`, `IN_TRANSIT`, `DELAYED`, `OUT_FOR_DELIVERY`, `DELIVERED`) and an event history log.

### 2. Waking Up and Acting Autonomously (`wake` method)

The agent operates on a wake-driven model. It remains dormant until an event triggers it. The `wake(event_name, event_data)` method is the heart of the agent. 

When woken, the agent appends the event to its history and executes logic based on the event type:
- **`PICKED_UP`**: Updates status to `IN_TRANSIT`, calculates an ETA, and sends a proactive SMS: "Your order is on the way!"
- **`IN_TRANSIT`**: The agent intentionally stays silent. There's no change worth reporting.
- **`DELAY_DETECTED`**: Updates status to `DELAYED`, applies the new ETA, and proactively SMSs the customer.
- **`OUT_FOR_DELIVERY`**: Schedules a delivery window and notifies the customer.
- **`DELIVERED`**: Notifies the customer and schedules a self-wake for 7 days later to request feedback.

### 3. Proactive SMS (`_proactive_sms` method)

When the agent needs to reach out, it uses the Telnyx Python SDK to send an SMS:
```python
telnyx.Message.create(
    from_=self.sms_channel,
    to=self.customer_number,
    text=message,
    messaging_profile_id=TELNYX_MESSAGING_PROFILE_ID
)
```
This allows the shipment to proactively contact the customer the moment its state changes.

### 4. Self-Waking for Future Events (`schedule` method)

To handle future events like feedback requests without relying on external cron jobs, the agent implements a `schedule(delay, event_name)` method. 

In this demo, we simulate this self-waking behavior using Python's `threading` and `time.sleep` to trigger a delayed wake. In a production environment, you would implement this using a durable task queue like Celery, RQ, or a serverless scheduler. When the `DELIVERED` event fires, the agent schedules a `FEEDBACK_REQUEST` wake 7 days into the future.

### 5. Inbound Webhooks: Carrier Updates (`/webhooks/carrier`)

To simulate FedEx/UPS APIs sending status updates, we expose a `/webhooks/carrier` endpoint. 

When a carrier webhook arrives, the route:
1. Extracts the `shipment_id` and `status`.
2. Retrieves (or creates) the corresponding `ShipmentAgent`.
3. Maps the carrier status to an internal agent event (e.g., `DELAYED` -> `DELAY_DETECTED`).
4. Calls `agent.wake(event_name, event_data)`.

### 6. Inbound Webhooks: Telnyx SMS & Voice (`/webhooks/telnyx`)

This endpoint handles inbound communications from the customer (SMS replies or incoming calls). 

**Security First:** The endpoint strictly verifies the Telnyx Ed25519 signature using `telnyx.Webhook.construct_event`. If the signature is missing or invalid, the request is aborted with a 401 Unauthorized.

Once verified, it routes the payload:
- **SMS Replies (`message.received`)**: Matches the inbound `from_number` to an agent's `customer_number` and triggers `agent.handle_sms_reply(text)`.
- **Call Control (`call.*`)**: Logs the call control event. In a full production flow, you would use Telnyx Call Control to answer the call, speak context via TTS, and bridge to an AI inference loop.

### 7. Customer Calls with Full Context (`handle_call` method)

If a customer calls in, the agent answers with full shipment context. The `handle_call` method generates a context summary using `get_context_summary()`. In this demo, we expose a REST endpoint (`/api/agents/<shipment_id>/call`) to simulate this trigger. In production, this would tie directly into Telnyx Call Control Webhooks to answer the call and speak to the customer.

### 8. Natural Language Q&A via Inference (`handle_sms_reply` method)

When a customer replies to an SMS, the agent uses inference to understand and respond. The agent builds a prompt containing the shipment context and the user's query, then calls an AI inference endpoint. 

This sample includes a `_simulate_inference` method to demonstrate the flow. In a production application, you would replace this with a call to your AI provider (e.g., `this.env.TELNYX.ai.openai.chat.createCompletion()` or the Telnyx AI SDK) to generate natural, context-aware responses.

## Next Steps

Now that you understand how the ShipmentAgent works, you can extend it further:
- Replace the in-memory `SHIPMENT_AGENTS` dictionary with a durable database (Postgres/Redis).
- Implement the `schedule` method using a real task queue like Celery or Cloudflare Queues.
- Flesh out the Call Control flow to answer calls using Telnyx Call Control APIs and Text-to-Speech.
- Connect the inference loop to a live AI model for true natural language shipment Q&A.

Check out the [Telnyx Developer Documentation](https://developers.telnyx.com/) to learn more about Call Control, Messaging, and AI integrations.
