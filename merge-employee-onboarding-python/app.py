"""Merge Employee Onboarding — new employee webhook from Merge HRIS triggers
automated provisioning: provisions a Telnyx phone number, configures AI voicemail
greeting, sends welcome SMS with IT setup instructions, and creates an IT setup
ticket via Merge Ticketing."""
import os, json, time, base64, logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
TELNYX_PHONE = os.getenv("TELNYX_PHONE_NUMBER")
CONNECTION_ID = os.getenv("TELNYX_CONNECTION_ID", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
MERGE_API_KEY = os.getenv("MERGE_API_KEY")
MERGE_ACCOUNT_TOKEN = os.getenv("MERGE_ACCOUNT_TOKEN")
IT_ADMIN_PHONE = os.getenv("IT_ADMIN_PHONE", "")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {
    "Authorization": f"Bearer {MERGE_API_KEY}",
    "X-Account-Token": MERGE_ACCOUNT_TOKEN or "",
    "Content-Type": "application/json",
}
MERGE_BASE = "https://api.merge.dev/api"

onboarding_log = []
MAX_ENTRIES = 10000


def merge_get(path, params=None):
    try:
        resp = requests.get(
            f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, params=params
        )
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge GET %s failed: %s", path, e)
    return None


def merge_post(path, data):
    try:
        resp = requests.post(
            f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, json={"model": data}
        )
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge POST %s failed: %s", path, e)
    return None


def provision_number(area_code=""):
    """Search for and order a Telnyx phone number."""
    params = {"filter[country_code]": "US", "filter[limit]": 1}
    if area_code:
        params["filter[national_destination_code]"] = area_code
    try:
        search = requests.get(
            "https://api.telnyx.com/v2/available_phone_numbers",
            headers=HEADERS,
            timeout=10,
            params=params,
        )
        if not search.ok:
            return None
        numbers = search.json().get("data", [])
        if not numbers:
            return None
        phone = numbers[0]["phone_number"]
        order = requests.post(
            "https://api.telnyx.com/v2/number_orders",
            headers=HEADERS,
            timeout=10,
            json={"phone_numbers": [{"phone_number": phone}], "connection_id": CONNECTION_ID},
        )
        if order.ok:
            return phone
    except Exception as e:
        app.logger.error("Number provisioning failed: %s", e)
    return None


def generate_voicemail_greeting(name, department):
    """Generate a personalized voicemail greeting via AI."""
    try:
        resp = requests.post(
            INFERENCE_URL,
            headers=HEADERS,
            timeout=15,
            json={
                "model": AI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Generate a short, professional voicemail greeting (under 30 words). Include the persons name and department.",
                    },
                    {"role": "user", "content": f"Name: {name}, Department: {department}"},
                ],
            },
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        app.logger.error("Greeting generation failed: %s", e)
    return f"You have reached {name}. Please leave a message and I will return your call."


def send_welcome_sms(phone, name, new_number):
    """Send welcome SMS to new employee."""
    msg = (
        f"Welcome {name}! Your company phone number is {new_number}. "
        f"Check your email for IT setup instructions including laptop, badge, and account access."
    )
    try:
        requests.post(
            "https://api.telnyx.com/v2/messages",
            headers=HEADERS,
            timeout=10,
            json={"from": TELNYX_PHONE, "to": phone, "text": msg},
        )
        return True
    except Exception as e:
        app.logger.error("Welcome SMS failed: %s", e)
        return False


def create_it_ticket(name, start_date, department, employee_id):
    """Create IT setup ticket in Merge Ticketing."""
    ticket_data = {
        "name": f"New hire IT setup: {name}",
        "description": (
            f"Provision laptop, accounts, badge, and office access for {name}.\n"
            f"Department: {department}\n"
            f"Start date: {start_date}\n"
            f"Employee ID: {employee_id}\n\n"
            f"Checklist:\n"
            f"- [ ] Laptop ordered and configured\n"
            f"- [ ] Email and Slack accounts created\n"
            f"- [ ] Badge and office access provisioned\n"
            f"- [ ] VPN credentials issued\n"
            f"- [ ] Phone number assigned"
        ),
        "priority": "NORMAL",
    }
    return merge_post("/ticketing/v1/tickets", ticket_data)


@app.route("/webhooks/hris", methods=["POST"])
def handle_hris_webhook():
    """Merge HRIS webhook — new employee triggers full onboarding flow."""
    data = request.get_json() or {}
    employee_id = data.get("id", "")
    employee = merge_get(f"/hris/v1/employees/{employee_id}") if employee_id else data
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip() or "New Employee"
    department = employee.get("department", {}).get("name", "General") if isinstance(employee.get("department"), dict) else str(employee.get("department", "General"))
    start_date = employee.get("start_date", "TBD")
    personal_phone = None
    for pn in employee.get("phone_numbers", []):
        if pn.get("value"):
            personal_phone = pn["value"]
            break
    actions = []
    # 1. Provision phone number
    new_number = provision_number()
    if new_number:
        actions.append({"action": "number_provisioned", "number": new_number})
    else:
        actions.append({"action": "number_provisioning_failed"})
    # 2. Generate voicemail greeting
    greeting = generate_voicemail_greeting(name, department)
    actions.append({"action": "voicemail_greeting_generated", "greeting": greeting[:100]})
    # 3. Send welcome SMS
    if personal_phone and TELNYX_PHONE:
        sent = send_welcome_sms(personal_phone, name, new_number or "(pending)")
        actions.append({"action": "welcome_sms_sent" if sent else "welcome_sms_failed"})
    # 4. Create IT ticket
    ticket = create_it_ticket(name, start_date, department, employee_id)
    if ticket:
        ticket_id = ticket.get("model", {}).get("id", "")
        actions.append({"action": "it_ticket_created", "ticket_id": ticket_id})
    else:
        actions.append({"action": "it_ticket_failed"})
    # 5. Notify IT admin
    if IT_ADMIN_PHONE and TELNYX_PHONE:
        try:
            requests.post(
                "https://api.telnyx.com/v2/messages",
                headers=HEADERS,
                timeout=10,
                json={
                    "from": TELNYX_PHONE,
                    "to": IT_ADMIN_PHONE,
                    "text": f"New hire onboarding started: {name} ({department}). Start: {start_date}. Check ticket queue.",
                },
            )
            actions.append({"action": "it_admin_notified"})
        except Exception as e:
            app.logger.error("IT admin notification failed: %s", e)
    result = {"employee": name, "department": department, "start_date": start_date, "actions": actions}
    onboarding_log.append({**result, "ts": time.time()})
    if len(onboarding_log) > MAX_ENTRIES:
        onboarding_log[:] = onboarding_log[-MAX_ENTRIES:]
    return jsonify(result)


@app.route("/onboard", methods=["POST"])
def manual_onboard():
    """Manually trigger onboarding for testing."""
    data = request.get_json() or {}
    name = data.get("name", "Test Employee")
    phone = data.get("phone")
    department = data.get("department", "Engineering")
    actions = []
    new_number = provision_number()
    if new_number:
        actions.append({"action": "number_provisioned", "number": new_number})
    greeting = generate_voicemail_greeting(name, department)
    actions.append({"action": "voicemail_greeting_generated", "greeting": greeting[:100]})
    if phone and TELNYX_PHONE:
        sent = send_welcome_sms(phone, name, new_number or "(pending)")
        actions.append({"action": "welcome_sms_sent" if sent else "welcome_sms_failed"})
    return jsonify({"employee": name, "department": department, "actions": actions})


@app.route("/onboardings", methods=["GET"])
def list_onboardings():
    """List onboarding history."""
    return jsonify({"onboardings": onboarding_log[-50:]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "merge-employee-onboarding", "total_onboarded": len(onboarding_log)})


if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
