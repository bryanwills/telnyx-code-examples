# Build a Semantic Search for Support Tickets

Semantic Search — index support tickets via Telnyx embeddings API and find similar issues by meaning, not keywords. Includes a bundled sample ticket dataset.

## How It Works

```
  Support tickets
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  │ (embed + index)   │
  └────────┬─────────┘
           │
           ├──► Telnyx Embeddings API
           │
           ├──► In-memory vector store (numpy)
           │
           ▼
  Query ──► Embed ──► Cosine similarity ──► Top-k tickets
```

## Telnyx Products Used

- **AI Inference (Embeddings)** — Generate embedding vectors from text, runs on Telnyx infrastructure

## API Endpoints

- **AI Embeddings**: `POST /v2/ai/openai/embeddings` — [API reference](https://developers.telnyx.com/api/inference/create-embeddings)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/semantic-search-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py`. Here's what each piece does.

### Helper Functions

- **`get_embeddings()`** — Sends text to the Telnyx embeddings API and returns vector representations. Batches requests to handle large ticket sets efficiently.
- **`cosine_similarity()`** — Computes cosine similarity between a query vector and all indexed ticket vectors using numpy. Returns a ranked similarity score array.
- **`load_sample_tickets()`** — Loads the bundled `sample_tickets.json` file.
- **`build_index()`** — Embeds all tickets, stores vectors in a numpy matrix, and indexes them in memory.

### Sample Dataset

The bundled `sample_tickets.json` contains 15 realistic support tickets across categories:
- **messaging** — SMS delivery failures, international routing, MMS size limits, sticky sender, DLR delays
- **voice** — audio quality, conference limits, call forwarding
- **sip** — trunk registration failures
- **api** — webhook signatures, API key rotation
- **porting** — US number port delays
- **fax** — rendering issues
- **billing** — overcharge disputes
- **webrtc** — connection drops

### Business Logic

- **`index_tickets()`** — Builds the embedding index from sample tickets or a provided list.
- **`search_tickets()`** — Embeds the query, computes cosine similarity against all indexed tickets, returns top-k results with scores.
- **`add_ticket()`** — Embeds a new ticket and appends it to the in-memory vector store.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/index` | Build the embedding index |
| `POST` | `/search` | Search by meaning |
| `POST` | `/tickets` | Add a ticket to the index |
| `GET` | `/tickets/<id>` | Fetch a ticket |
| `GET` | `/stats` | Index stats |
| `GET` | `/health` | Health check |

The embeddings helper sends text to Telnyx and returns vectors:

```python
def get_embeddings(texts, batch_size=8):
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = requests.post(EMBEDDINGS_URL,
            headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"input": batch, "model": EMBEDDING_MODEL}, timeout=40)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        all_embeddings.extend([d["embedding"] for d in data])
    return all_embeddings
```

The search endpoint embeds the query and ranks tickets by similarity:

```python
@app.route("/search", methods=["POST"])
def search_tickets():
    data = request.get_json()
    query = data.get("query", "").strip()
    top_k = int(data.get("top_k", 5))
    query_vec = np.array(get_embeddings([query])[0], dtype=np.float32)
    scores = cosine_similarity(query_vec, vectors)
    ranked = np.argsort(scores)[::-1][:top_k]
    results = [{"ticket_id": ..., "score": float(scores[idx]), ...} for idx in ranked]
    return jsonify({"query": query, "results": results})
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

**Build the index:**

```bash
curl -X POST http://localhost:5000/index
```

**Search for tickets by meaning:**

```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"I cannot send text messages to international phone numbers","top_k":3}' | python3 -m json.tool
```

**Try more queries:**

```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"audio quality problems on calls","top_k":3}' | python3 -m json.tool

curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"my API key stopped working after I changed it","top_k":3}' | python3 -m json.tool

curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"phone number transfer is taking too long","top_k":3}' | python3 -m json.tool
```

**Add a new ticket:**

```bash
curl -X POST http://localhost:5000/tickets \
  -H "Content-Type: application/json" \
  -d '{"subject":"New issue","body":"Cannot receive faxes from certain senders.","category":"fax","priority":"medium"}'
```

**Check stats:**

```bash
curl http://localhost:5000/stats | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Vector database** — replace the numpy matrix with a dedicated vector DB (Pinecone, Weaviate, pgvector, Qdrant) for scale
- **Persistence** — store embeddings and tickets in PostgreSQL or Redis so they survive restarts
- **Authentication** — add API key validation on your endpoints
- **Incremental indexing** — embed new tickets on creation instead of re-indexing everything
- **Rate limiting** — protect your endpoints from abuse
- **Hybrid search** — combine semantic search with keyword/SQL filters for category, date range, priority
- **Deduplication** — use similarity scores to surface duplicate tickets before they're filed

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/semantic-search-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
