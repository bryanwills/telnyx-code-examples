# Build an AI Changelog Generator

AI Changelog Generator — turn git commits and diffs into a clean, human-readable changelog via Telnyx AI Inference.

## How It Works

```
  Git history / diff
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx AI Inference
           │
           ├──► Grouping + summarization
           │
           ▼
     Structured changelog (JSON)
```

## Telnyx Products Used

- **AI Inference** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/changelog-generator-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py`. Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends the changelog prompt to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.
- **`build_changelog_prompt()`** — Constructs the prompt that groups commit messages under Features, Bug Fixes, Improvements, Breaking Changes, and Documentation, and asks the model for JSON.

### Business Logic

- **`generate_changelog()`** — Accepts a list of commit messages, asks the LLM to produce a structured changelog, and stores the result.
- **`generate_from_diff()`** — Accepts a raw git diff and produces a grouped changelog.
- **`list_changelogs()`** — Returns the most recent 50 generated changelogs.
- **`get_changelog()`** — Returns a single changelog by ID.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/generate` | Generate changelog from commits |
| `POST` | `/generate/from-diff` | Generate changelog from a git diff |
| `GET` | `/changelogs` | List changelogs |
| `GET` | `/changelogs/<id>` | Get a changelog |
| `GET` | `/health` | Health check |

The inference helper sends the prompt to Telnyx AI and returns the response:

```python
def call_inference(messages, max_tokens=800):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3}, timeout=20)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
```

The generate endpoint groups commits into a structured changelog:

```python
@app.route("/generate", methods=["POST"])
def generate_changelog():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    commits = data.get("commits", [])
    if not commits:
        return jsonify({"error": "commits field is required"}), 400
    version = data.get("version")
    prompt = build_changelog_prompt(commits, version, data.get("repo_name"))
    result = call_inference([
        {"role": "system", "content": "You generate developer-friendly changelogs from git history."},
        {"role": "user", "content": prompt},
    ])
    changelog = json.loads(result)
    changelog["id"] = f"cl-{int(time.time())}"
    changelogs[changelog["id"]] = changelog
    return jsonify(changelog), 200
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

**Generate a changelog from commits:**

```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "version": "v1.4.0",
    "repo_name": "billing-service",
    "commits": [
      "feat: add Stripe webhook retry with exponential backoff",
      "fix: correct tax calculation for EU VAT exemption",
      "docs: update API reference for invoice endpoint"
    ]
  }'
```

**Generate from a git diff:**

```bash
git diff HEAD~5 HEAD > /tmp/recent.diff
DIFF=$(jq -Rs . < /tmp/recent.diff)
curl -X POST http://localhost:5000/generate/from-diff \
  -H "Content-Type: application/json" \
  -d "{\"version\":\"v1.4.1\",\"diff\":$DIFF}"
```

**List generated changelogs:**

```bash
curl http://localhost:5000/changelogs | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Git integration** — wire `/generate` to read directly from `git log` in CI
- **Prompt engineering** — tune the prompt for your repo's commit message conventions
- **Rate limiting** — protect your endpoints from abuse
- **Diff size limits** — chunk very large diffs before sending to inference

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/changelog-generator-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
