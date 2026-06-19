# Build an E911 Address Validator — validate and provision E911 addresses via API

Validate and provision E911 emergency addresses via the Telnyx API.

## How It Works

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx Number Management
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **E911**
- **Migration**
- **Number Porting** — phone number search, purchase, and configuration

## API Endpoints

- **List Phone Numbers**: `GET /v2/phone_numbers` — [API reference](https://developers.telnyx.com/api/numbers/list-phone-numbers)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/e911-address-validator-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (50 lines). Here's what each piece does.

### Business Logic

- **`validate_address()`** — Makes an API call and processes the response.
- **`assign_e911()`** — Processes assign e911 request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/e911/validate` | Validate Address |
| `POST` | `/e911/assign` | Assign E911 |
| `GET` | `/e911/addresses` | List Addresses |
| `GET` | `/health` | Health check |

The trigger endpoint kicks off the workflow:

```python
def validate_address():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    address = {"street_address": data.get("street"), "extended_address": data.get("street2", ""),
        "locality": data.get("city"), "administrative_area": data.get("state"), "postal_code": data.get("zip"), "country_code": data.get("country", "US")}
    try:
        resp = requests.post("https://api.telnyx.com/v2/addresses", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={**address, "address_book": True, "business_name": data.get("business_name", "", timeout=10)}, timeout=15)
        if resp.ok:
            result = resp.json().get("data", {})
            validated_addresses.append(result)
```

The main endpoint processes the request:

```python
def validate_address():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    address = {"street_address": data.get("street"), "extended_address": data.get("street2", ""),
        "locality": data.get("city"), "administrative_area": data.get("state"), "postal_code": data.get("zip"), "country_code": data.get("country", "US")}
    try:
        resp = requests.post("https://api.telnyx.com/v2/addresses", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={**address, "address_book": True, "business_name": data.get("business_name", "", timeout=10)}, timeout=15)
        if resp.ok:
```

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Trigger the workflow:**

```bash
curl -X POST http://localhost:5000/e911/validate \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/e911/addresses | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Deploy

```bash
# Docker
docker build -t e911-address-validator-python .
docker run --env-file .env -p 5000:5000 e911-address-validator-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
