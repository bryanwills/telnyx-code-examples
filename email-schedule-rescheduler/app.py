"""
Email Schedule Rescheduler — Telnyx Code Sample

This script demonstrates how to schedule an email, reschedule it to a new
future time, and verify that invalid reschedule attempts are rejected with
a 422 error.

Demo flow:
  1. Create a scheduled email via POST /v2/email_messages with a future
     scheduled_at timestamp (the API responds 202 with a message ID).
  2. Reschedule the email to a new future time via
     PATCH /v2/email_messages/{id}/schedule (expected 200).
  3. Attempt to reschedule to a past timestamp and verify the API returns
     a 422 error whose errors array references the rejected scheduled_at.
  4. Retrieve the message via GET /v2/email_messages/{id} to confirm the
     updated scheduled_at value.

Cleanup: after verification, the scheduled message is cancelled via
DELETE /v2/email_messages/{id}/schedule so the demo leaves nothing behind.

ASSUMPTION: The Telnyx Python SDK (v4.181.0) exposes create/retrieve/
delete_schedule for email messages via the instance client but has NO
patch-schedule method. The reschedule call is therefore implemented as a
raw HTTP PATCH to https://api.telnyx.com/v2/email_messages/{id}/schedule,
which is the documented API endpoint.

ASSUMPTION: DEMO_MODE=true (default) prints the requests it would make
without hitting the API. Set DEMO_MODE=false to run against the live
Telnyx API.

KNOWN LIMITATION (verified against the live API 2026-09-24): the PATCH
/v2/email_messages/{id}/schedule route is documented in the developer
docs and OpenAPI spec, but the live API currently returns 404 (code
10005) for it while the sibling DELETE route works. If you see that
error, the platform-side endpoint is not yet available; steps 2-4 cannot
be exercised live until it ships.

Security: credentials are read from environment variables only. Never
hardcode API keys. Sender/recipient addresses come from env vars.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import requests
import telnyx
from dotenv import load_dotenv
from telnyx import APIError

# Load environment variables from .env file if present
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
TELNYX_EMAIL_FROM = os.getenv("TELNYX_EMAIL_FROM", "")
TELNYX_EMAIL_TO = os.getenv("TELNYX_EMAIL_TO", "")

# DEMO_MODE defaults to "true" — safe mode that logs requests without
# hitting the live API. Set to "false" for live mode.
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

TELNYX_API_BASE = "https://api.telnyx.com/v2"

# Configure the Telnyx SDK (v4.x uses an instance-based client)
client = telnyx.Telnyx(api_key=TELNYX_API_KEY)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iso_future(minutes: int) -> str:
    """Return an ISO 8601 UTC timestamp `minutes` from now (Z suffix, no microseconds)."""
    return (
        (datetime.now(timezone.utc) + timedelta(minutes=minutes))
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _iso_past(minutes: int = 5) -> str:
    """Return an ISO 8601 UTC timestamp `minutes` in the past (Z suffix, no microseconds)."""
    return (
        (datetime.now(timezone.utc) - timedelta(minutes=minutes))
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _same_instant(value, expected) -> bool:
    """Compare two timestamps as instants.

    Handles both ISO 8601 strings (demo mode) and the parsed datetime
    objects the SDK returns (live mode); tolerates Z vs +00:00 formats.
    """

    def _to_dt(v):
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))

    parsed_value = _to_dt(value)
    parsed_expected = _to_dt(expected)
    if parsed_value.tzinfo is None:
        parsed_value = parsed_value.replace(tzinfo=timezone.utc)
    if parsed_expected.tzinfo is None:
        parsed_expected = parsed_expected.replace(tzinfo=timezone.utc)
    return parsed_value == parsed_expected


def _demo_log(message: str) -> None:
    """Print a demo-mode message."""
    print(f"[DEMO] {message}")


def _auth_headers() -> dict:
    """Return the Authorization header for raw HTTP calls."""
    return {"Authorization": f"Bearer {TELNYX_API_KEY}"}


def _error_detail(exc: APIError) -> str:
    """Extract a readable message from an SDK APIError."""
    parts = [getattr(exc, "title", None), getattr(exc, "description", None)]
    return " — ".join(p for p in parts if p) or str(exc)


# ---------------------------------------------------------------------------
# Demo steps
# ---------------------------------------------------------------------------


def schedule_email() -> str:
    """
    Step 1: Create a scheduled email with a future scheduled_at timestamp.

    Returns the email message ID.
    """
    scheduled_at = _iso_future(30)  # 30 minutes from now
    print(f"[1] Scheduling email for {scheduled_at}")

    if DEMO_MODE:
        _demo_log(
            f"POST /v2/email_messages "
            f"from={TELNYX_EMAIL_FROM} to={TELNYX_EMAIL_TO} "
            f"scheduled_at={scheduled_at}"
        )
        return "demo-message-id-12345"

    try:
        response = client.email_messages.create(
            from_=TELNYX_EMAIL_FROM,
            to=[TELNYX_EMAIL_TO],
            subject="Scheduled Email Demo",
            text_body="This email was scheduled and then rescheduled.",
            scheduled_at=scheduled_at,
        )
    except APIError as exc:
        print(f"ERROR: Failed to schedule email: {_error_detail(exc)}")
        sys.exit(1)

    message_id = response.data.id
    print(f"OK (202) -> Scheduled email created with ID: {message_id}")
    print(f"        status={response.data.status} scheduled_at={response.data.scheduled_at}")
    return message_id


def reschedule_email(message_id: str, new_scheduled_at: str) -> dict:
    """
    Step 2: Reschedule the email to a new future time.

    Uses raw HTTP PATCH to /v2/email_messages/{id}/schedule because the
    SDK does not expose a patch-schedule method.

    Returns the API response JSON.
    """
    print(f"[2] Rescheduling email {message_id} to {new_scheduled_at}")

    if DEMO_MODE:
        _demo_log(
            f"PATCH /v2/email_messages/{message_id}/schedule "
            f"body={{'scheduled_at': '{new_scheduled_at}'}}"
        )
        return {"data": {"id": message_id, "scheduled_at": new_scheduled_at}}

    url = f"{TELNYX_API_BASE}/email_messages/{message_id}/schedule"
    payload = {"scheduled_at": new_scheduled_at}

    try:
        response = requests.patch(url, json=payload, headers=_auth_headers(), timeout=30)
    except requests.RequestException as exc:
        print(f"ERROR: reschedule request failed: {exc}")
        sys.exit(1)

    if response.status_code == 404:
        print(
            "BLOCKED: PATCH /v2/email_messages/{id}/schedule is documented but not "
            "deployed on the live API yet (404, code 10005). Steps 2-4 cannot be "
            "verified live until the endpoint ships. The scheduled message is "
            "cancelled in cleanup so it does not send. See the README Known limitation."
        )
        sys.exit(1)

    if response.status_code != 200:
        print(f"ERROR: reschedule failed with status {response.status_code}")
        print(response.text)
        sys.exit(1)

    data = response.json()
    print(f"OK (200) -> Rescheduled. New scheduled_at: {data['data']['scheduled_at']}")
    return data


def attempt_invalid_reschedule(message_id: str) -> None:
    """
    Step 3: Attempt to reschedule to a past timestamp and verify the API
    returns a 422 error with a non-empty errors array that references the
    rejected scheduled_at field.
    """
    past_time = _iso_past(5)
    print(f"[3] Attempting invalid reschedule to {past_time} (expect 422)")

    if DEMO_MODE:
        _demo_log(
            f"PATCH /v2/email_messages/{message_id}/schedule "
            f"body={{'scheduled_at': '{past_time}'}} -> would return 422"
        )
        return

    url = f"{TELNYX_API_BASE}/email_messages/{message_id}/schedule"
    payload = {"scheduled_at": past_time}

    try:
        resp = requests.patch(url, json=payload, headers=_auth_headers(), timeout=30)
    except requests.RequestException as exc:
        print(f"ERROR: invalid-reschedule request failed: {exc}")
        sys.exit(1)

    if resp.status_code == 404:
        print(
            "BLOCKED: PATCH /v2/email_messages/{id}/schedule is documented but not "
            "deployed on the live API yet (404, code 10005), so the 422 rejection "
            "cannot be exercised. See the README Known limitation."
        )
        sys.exit(1)

    # Assert the 422 status code
    if resp.status_code != 422:
        print(f"FAIL: expected 422, got {resp.status_code}")
        print(resp.text)
        sys.exit(1)

    # Assert the error body contains a non-empty errors array whose first
    # entry references the rejected scheduled_at field (the API does not
    # echo the timestamp value itself, so do not assert exact wording).
    try:
        body = resp.json()
    except ValueError:
        print("FAIL: response body is not valid JSON")
        sys.exit(1)

    errors = body.get("errors", [])
    if not errors:
        print("FAIL: expected non-empty errors array")
        sys.exit(1)

    first_error = errors[0]
    error_text = str(first_error)
    if "scheduled_at" not in error_text:
        print("FAIL: first error entry does not reference the scheduled_at field")
        print(f"     error: {error_text}")
        sys.exit(1)

    print(f"OK (422) -> rejected as expected: {first_error.get('title', first_error)}")


def verify_scheduled_at(message_id: str, expected_scheduled_at: str) -> None:
    """
    Step 4: Retrieve the message and confirm the updated scheduled_at value.
    """
    print(f"[4] Verifying scheduled_at for message {message_id}")

    if DEMO_MODE:
        _demo_log(
            f"GET /v2/email_messages/{message_id} "
            f"-> scheduled_at={expected_scheduled_at}"
        )
        return

    try:
        response = client.email_messages.retrieve(message_id)
    except APIError as exc:
        print(f"ERROR: failed to retrieve email: {_error_detail(exc)}")
        sys.exit(1)

    actual = response.data.scheduled_at
    if not _same_instant(actual, expected_scheduled_at):
        print(f"FAIL: expected scheduled_at={expected_scheduled_at}, got {actual}")
        sys.exit(1)

    print(f"OK -> scheduled_at confirmed as {actual}")


def cleanup_schedule(message_id: str) -> None:
    """
    Post-demo cleanup: cancel the scheduled message so it doesn't send.
    This is not one of the four demo steps.
    """
    print(f"[cleanup] Cancelling scheduled email {message_id}")

    if DEMO_MODE:
        _demo_log(f"DELETE /v2/email_messages/{message_id}/schedule")
        return

    try:
        response = client.email_messages.delete_schedule(email_id=message_id)
        print(f"OK (200) -> scheduled email cancelled, status={response.data.status}")
    except APIError as exc:
        print(f"WARN: cleanup failed (non-fatal): {_error_detail(exc)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the four demo steps sequentially."""
    if not DEMO_MODE:
        if not TELNYX_API_KEY:
            print("ERROR: TELNYX_API_KEY is required when DEMO_MODE=false")
            sys.exit(1)
        if not TELNYX_EMAIL_FROM or not TELNYX_EMAIL_TO:
            print("ERROR: TELNYX_EMAIL_FROM and TELNYX_EMAIL_TO are required in live mode")
            sys.exit(1)

    print("=" * 60)
    print("Email Schedule Rescheduler Demo")
    print(f"Mode: {'DEMO (no API calls)' if DEMO_MODE else 'LIVE'}")
    print("=" * 60)

    # Step 1: schedule
    message_id = schedule_email()

    # Steps 2-4: reschedule, invalid reschedule, verify.
    # Cleanup always runs (even when a step fails) so no scheduled email is left behind.
    try:
        # Step 2: reschedule to a new future time
        new_scheduled_at = _iso_future(60)  # 60 minutes from now
        reschedule_email(message_id, new_scheduled_at)

        # Step 3: invalid reschedule (expect 422)
        attempt_invalid_reschedule(message_id)

        # Step 4: verify the updated scheduled_at
        verify_scheduled_at(message_id, new_scheduled_at)
    finally:
        # Cleanup: cancel the scheduled email
        cleanup_schedule(message_id)

    print("\nDemo completed successfully.")


if __name__ == "__main__":
    main()
