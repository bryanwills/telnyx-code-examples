# Guide: SMS Two-Factor Agent

This guide walks through the `sms-two-factor-agent` example, a TypeScript Edge application that implements a complete two-factor authentication (2FA) flow via SMS. 

The agent manages the entire lifecycle of a 2FA code: generating the code, storing it with a strict Time-To-Live (TTL), sending it via Telnyx SMS, verifying the user's reply, and cleaning up expired or rate-limited attempts.

## Prerequisites

- Node.js (v18 or newer)
- A Telnyx account with an SMS-enabled number
- Telnyx API Key (found in the Telnyx Portal)
- The Telnyx Edge CLI installed globally: `npm install -g @telnyx/edge-cli`

## Environment Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file and add your Telnyx API key:
   ```env
   TELNYX_API_KEY=your_telnyx_api_key_here
   ```

## Running the Sample

To run the application locally in safe demo mode:

```bash
npm run dev
```

By default, this sample runs in **Safe Demo Mode**. No real SMS messages will be sent, protecting you from accidental charges during development. Instead, the agent will log the 2FA code and the intended phone number to the console.

### Switching to Live Mode

To send real SMS messages via the Telnyx network, you must switch to live mode. 

1. Open `src/index.ts`.
2. Locate the `TwoFactorAgent` class configuration.
3. Change the `DEMO_MODE` flag from `true` to `false`.
4. Ensure your `.env` file contains a valid `TELNYX_API_KEY` and that you own the destination phone numbers.

## How It Works: Step-by-Step

The application uses the Telnyx Edge Agent SDK to orchestrate the 2FA flow. The `TwoFactorAgent` extends the base `Agent` class, giving it access to scheduling, state management, and Telnyx bindings.

### 1. The Agent and State Management

The `TwoFactorAgent` class is the core of the application. It maintains an internal `StateStore` to track authentication attempts. This prevents brute-force attacks by rate-limiting how many times a user can request or submit a code from the same phone number.

When a request is initiated, the agent checks the `StateStore` to ensure the user hasn't exceeded the attempt limit. If they are within limits, the agent proceeds to code generation.

### 2. Code Generation and KV Storage

When a user requests a 2FA code (e.g., `POST /verify { phone }`), the agent generates a cryptographically secure random numeric code. 

The code is stored in the Edge KV (Key-Value) store using a TTL (Time-To-Live) of 300 seconds (5 minutes). The KV store operation looks like this:

```typescript
ctx.kv.put('2fa:${phone}', code, { ttl: 300 });
```

This ensures the code automatically expires from the store if not used within 5 minutes, without requiring manual cleanup.

### 3. Sending the SMS via Telnyx Binding

The application uses the `[telnyx]` binding to send the SMS. Because the binding is injected directly into the Edge environment, you can send messages without manually configuring HTTP clients or passing API keys in your application code.

The SMS dispatch uses the binding's `messages.send()` method:

```typescript
await this.env.TELNYX.messages.send({
  from: '<your_telnyx_number>',
  to: phone,
  text: `Your verification code is: ${code}`
});
```

In demo mode, this step is intercepted and logged to the console instead of hitting the live Telnyx API.

### 4. Code Verification

When the user replies with their code (e.g., `POST /check { phone, code }`), the agent retrieves the stored code from the KV store:

```typescript
const storedCode = await ctx.kv.get('2fa:${phone}');
```

The agent compares the `storedCode` with the user-provided code. If they match, the authentication is successful. If they do not match, the agent increments the failed attempt counter in the `StateStore`. 

### 5. Expiry and Cleanup via `this.schedule()`

While the KV store handles its own TTL expiration, the agent also uses the Agent SDK's `schedule()` method to manage cleanup tasks. 

After a successful verification—or after the maximum failed attempts are reached—the agent schedules a task to clean up any residual state in the `StateStore`:

```typescript
this.schedule('cleanupAttempt', phone, { delay: 300 });
```

This ensures the agent's state doesn't grow indefinitely and that users can request new codes after the cooldown period expires.

## Next Steps

- Learn more about the [Telnyx Edge SDK and Agent SDK](https://developers.telnyx.com/docs/edge-sdk)
- Explore the [Telnyx SMS API Documentation](https://developers.telnyx.com/docs/messaging)
- Read about [KV and State Management on the Edge](https://developers.telnyx.com/docs/edge-kv)
