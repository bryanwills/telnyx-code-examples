# API Reference: SMS Two-Factor Agent

This document provides a typed reference for the HTTP endpoints exposed by the SMS Two-Factor Agent. The agent manages the lifecycle of 2FA codes—generation, delivery via Telnyx SMS, verification, and expiry.

## Base URL

```
http://localhost:8787
```

## Endpoints

### 1. Initiate 2FA

Generates a 6-digit verification code, stores it in KV with a 5-minute TTL, and sends it to the user via Telnyx SMS.

**Endpoint:** `POST /verify/initiate`

#### Request Body Schema

| Field   | Type   | Required | Description                                      |
|---------|--------|----------|--------------------------------------------------|
| `phone` | string | Yes      | E.164 formatted phone number (e.g., `+15551234567`) |

#### Example Request

```bash
curl -X POST http://localhost:8787/verify/initiate \
  -H "Content-Type: application/json" \
  -d '{"phone": "+15551234567"}'
```

#### Response Schema

**Status 200 OK**

```json
{
  "success": true,
  "message": "Verification code sent.",
  "attempt_id": "att_8f7d6e5c"
}
```

**Status 400 Bad Request**

```json
{
  "error": "Invalid phone number format."
}
```

**Status 429 Too Many Requests**

```json
{
  "error": "Rate limit exceeded. Please try again later."
}
```

**Status 500 Internal Server Error**

```json
{
  "error": "Failed to send verification code."
}
```

#### Status Codes

| Status Code | Description                                              |
|------------|----------------------------------------------------------|
| 200        | Code generated and SMS dispatched successfully.          |
| 400        | Missing or invalid `phone` field in request body.        |
| 429        | Rate limit exceeded for the requested phone number.      |
| 500        | Telnyx API error or internal failure during code dispatch.|

---

### 2. Verify Code

Verifies the user-provided code against the value stored in KV. Tracks attempts in StateStore and schedules cleanup.

**Endpoint:** `POST /verify/check`

#### Request Body Schema

| Field   | Type   | Required | Description                                      |
|---------|--------|----------|--------------------------------------------------|
| `phone` | string | Yes      | E.164 formatted phone number.                    |
| `code`  | string | Yes      | 6-digit verification code received via SMS.      |

#### Example Request

```bash
curl -X POST http://localhost:8787/verify/check \
  -H "Content-Type: application/json" \
  -d '{"phone": "+15551234567", "code": "123456"}'
```

#### Response Schema

**Status 200 OK**

```json
{
  "success": true,
  "verified": true,
  "message": "Phone number verified successfully."
}
```

**Status 400 Bad Request**

```json
{
  "success": false,
  "verified": false,
  "error": "Invalid or expired verification code."
}
```

#### Status Codes

| Status Code | Description                                                     |
|------------|------------------------------------------------------------------|
| 200        | Verification successful (or failed due to wrong code; see body). |
| 400        | Missing `phone` or `code`, or the code has expired/does not match.|
| 429        | Rate limit exceeded for verification attempts.                   |
| 500        | Internal server error during verification process.              |

---

### 3. Agent Health Check

Returns the current status and configuration of the Two-Factor Agent.

**Endpoint:** `GET /health`

#### Example Request

```bash
curl -X GET http://localhost:8787/health
```

#### Response Schema

**Status 200 OK**

```json
{
  "status": "ok",
  "agent": "TwoFactorAgent",
  "kv_ttl_seconds": 300,
  "mode": "live"
}
```

#### Status Codes

| Status Code | Description                       |
|------------|-----------------------------------|
| 200        | Agent is running normally.       |
| 500        | Agent failed to initialize state. |
