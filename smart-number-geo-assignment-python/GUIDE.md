# Smart Number Geo-Assignment

> Smart Number Geo-Assignment — automatically purchase and assign local numbers based on caller geography to maximize answer rates.

## What You'll Build

A production-ready **smart number geo-assignment** built with Python, Flask, and Migration, Number Porting, Numbers.

| | |
|---|---|
| **Lines of code** | 78 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Migration, Number Porting, Numbers |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Search Available Numbers**: `GET /v2/available_phone_numbers` — [API reference](https://developers.telnyx.com/api/numbers/list-available-phone-numbers)
- **Create Number Order**: `POST /v2/number_orders` — [API reference](https://developers.telnyx.com/api/numbers/create-number-order)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/smart-number-geo-assignment-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (78 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/assign` | Assign |
| `POST` | `/lookup-and-assign` | Lookup And Assign |
| `GET` | `/inventory` | Inventory |
| `GET` | `/assignments` | Assignments |
| `GET` | `/health` | Health check |

### Key Functions

- **`search_local_number()`** — search local number
- **`purchase_number()`** — purchase number
- **`assign_number()`** — assign number
- **`lookup_and_assign()`** — lookup and assign
- **`assign_number_internal()`** — assign number internal
- **`inventory()`** — inventory
- **`list_assignments()`** — list assignments
- **`health()`** — health

## Step 3: Run

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X POST http://localhost:5000/assign \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t smart-number-geo-assignment-python .
docker run --env-file .env -p 5000:5000 smart-number-geo-assignment-python
```

### Makefile

```bash
make setup    # Install dependencies
make run      # Start the server
make docker   # Build and run in Docker
```

## Customize & Extend

- Replace in-memory storage with PostgreSQL or Redis for production
- Add authentication to your API endpoints
- Set up monitoring and alerting
- Deploy behind a reverse proxy (nginx, Caddy) with TLS

## Resources

- [Full source code and README](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
