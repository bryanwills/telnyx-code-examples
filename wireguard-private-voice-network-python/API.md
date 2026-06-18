# API Reference — WireGuard Private Voice Network

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/networks` | Create a new network. |
| `GET` | `/networks` | List networks. |
| `POST` | `/interfaces` | Create a new interface. |
| `POST` | `/peers` | Create a new peer. |
| `GET` | `/interfaces/<iface_id>/config` | Get config. |
| `GET` | `/topology` | Topology. |
| `GET` | `/health` | Health check and service status. |

---

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

---

## `GET /networks`

List all networks.

### Response `200`

```json
{
  "error": "Error description"
}
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

---

## `GET /interfaces/<iface_id>/config`

Get a specific config by ID.

### Response `200`

```json
{
  "error": "Error description"
}
```

---

## `GET /topology`

Topology.

### Response `200`

```json
{"networks": "<string>", "interfaces": "<string>",
        "details": {"networks": "<string>"), "interfaces": "<string>")}
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
