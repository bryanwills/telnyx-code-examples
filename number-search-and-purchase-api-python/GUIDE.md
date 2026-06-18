# Build a Number Search and Purchase API

Number Search and Purchase API — search, filter, and buy phone numbers programmatically.

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
           ├──► Appointment scheduling
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **Migration**
- **Number Porting** — phone number search, purchase, and configuration
- **Numbers** — phone number search, purchase, and configuration

## API Endpoints

- **Search Available Numbers**: `GET /v2/available_phone_numbers` — [API reference](https://developers.telnyx.com/api/numbers/list-available-phone-numbers)
- **Create Number Order**: `POST /v2/number_orders` — [API reference](https://developers.telnyx.com/api/numbers/create-number-order)
- **List Phone Numbers**: `GET /v2/phone_numbers` — [API reference](https://developers.telnyx.com/api/numbers/list-phone-numbers)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/number-search-and-purchase-api-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (64 lines). Here's what each piece does.

### Business Logic

- **`search_numbers()`** — Makes an API call and processes the response.
- **`purchase_number()`** — Makes an API call and processes the response.
- **`list_inventory()`** — Makes an API call and processes the response.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/numbers/search` | Search Numbers |
| `POST` | `/numbers/purchase` | Purchase Number |
| `GET` | `/numbers/inventory` | List Inventory |
| `GET` | `/health` | Health check |

The trigger endpoint kicks off the workflow:

```python
def purchase_number():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    numbers = data.get("phone_numbers", [])
    results = []
    for number in numbers:
        try:
            resp = requests.post("https://api.telnyx.com/v2/number_orders", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
                json={"phone_numbers": [{"phone_number": number}]}, timeout=15)
            if resp.ok:
                order = resp.json().get("data", {})
```

The main endpoint processes the request:

```python
def search_numbers():
    params = {"filter[country_code]": request.args.get("country", "US"), "filter[features][]": request.args.getlist("features") or ["sms", "voice"],
        "filter[number_type]": request.args.get("type", "local"), "page[size]": int(request.args.get("limit", 10))}
    area_code = request.args.get("area_code")
    if area_code:
        params["filter[national_destination_code]"] = area_code
    contains = request.args.get("contains")
    if contains:
        params["filter[phone_number][contains]"] = contains
    try:
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
curl -X POST http://localhost:5000/numbers/purchase \
  -H "Content-Type: application/json" \
  -d '{
    "phone_numbers": ["+12125551234"],
    "carrier": "Current Carrier"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/numbers/search | python3 -m json.tool
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
docker build -t number-search-and-purchase-api-python .
docker run --env-file .env -p 5000:5000 number-search-and-purchase-api-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
