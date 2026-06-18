## `POST /networks`

Create a new network.

### Request

```json
{
  "name": "Jane Smith"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | no | Display name or label |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/networks \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith"}'
```

---

## `GET /networks`

List all networks.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/networks
```

---

## `POST /interfaces`

Create a new interface.

### Request

```json
{
  "error": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `network_id` | `string` | **yes** | Network id |
| `region` | `string` | no | Region |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/interfaces \
  -H "Content-Type: application/json" \
  -d '{"error": "example-value"}'
```

---

## `POST /peers`

Create a new peer.

### Request

```json
{
  "error": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `interface_id` | `string` | **yes** | Interface id |
| `public_key` | `string` | **yes** | Public key |
| `name` | `string` | no | Display name or label |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/peers \
  -H "Content-Type: application/json" \
  -d '{"error": "example-value"}'
```

---

## `GET /interfaces/<iface_id>/config`

Get a specific config by ID.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/interfaces/example-id/config
```

---

## `GET /topology`

Topology.

### Response `200`

```json
{"networks": "<string>", "interfaces": "<string>",
        "details": {"networks": "<string>"), "interfaces": "<string>")}
```

**Try it:**

```bash
curl http://localhost:5000/topology
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "networks": "<string>",
  "interfaces": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "networks": "example-value",
  "interfaces": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
