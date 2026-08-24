# Agent Fleet Shared Workspace (CloudFS)

Five Telnyx Agent SDK actors collaborate through one shared Telnyx CloudFS filesystem. Each actor reads artifacts produced by the previous actor, writes its own result with standard POSIX file APIs, records fleet-wide metadata in an actor-backed SQL registry, and broadcasts state changes to connected WebSocket clients.

## Architecture

```text
CloudFS mounted at /mnt/agentfs
└── shared/
    ├── report.md       ← agent-1 (writer)
    ├── analysis.json   ← agent-2 (analyst)
    ├── review.md       ← agent-3 (reviewer)
    ├── summary.md      ← agent-4 (summarizer)
    └── manifest.json   ← agent-5 (publisher)

Every FleetAgent ──RPC──► FleetRegistry
                            ├── agents table
                            └── files table

Every FleetAgent ──WebSocket──► connected dashboards receive state patches
```

CloudFS is a POSIX filesystem mounted with JuiceFS. It is not an `env` binding and does not expose a `ctx.cloudfs` API. The application receives only the mount path and uses `node:fs/promises`, so every process mounting the same filesystem sees the same artifacts with close-to-open consistency.

## What this sample demonstrates

| Requirement | Implementation |
|---|---|
| Five agent instances | `agent-1` through `agent-5`, each a separate `FleetAgent` actor |
| Shared CloudFS reads and writes | Atomic POSIX writes and ordinary reads under one configured mount |
| SQL metadata | `FleetRegistry` stores the agent registry and file operation history in embedded SQL |
| WebSocket communication | `AgentSocketServer` broadcasts every agent state patch to connected clients |
| Safe shared paths | Traversal protection prevents artifacts from escaping the shared directory |

## Prerequisites

- Node.js 22+
- Telnyx CLI and an authenticated Telnyx account
- A Telnyx CloudFS filesystem
- JuiceFS Community Edition on a Linux host/container with FUSE, or an existing CloudFS mount supplied to the application

CloudFS setup follows the official guide: <https://developers.telnyx.com/docs/edge-compute/cloudfs/quickstart>.

## 1. Create and mount CloudFS

Create a filesystem. Save the returned credential-bearing `meta_url`; it is shown only on create or token rotation.

```bash
curl -X POST https://api.telnyx.com/v2/storage/cloudfs \
  -H "Authorization: Bearer $TELNYX_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"name":"agent-fleet-workspace","region":"us-east-1"}'
```

Mount the already-formatted filesystem with JuiceFS:

```bash
export META_URL='postgres://...tokenized URL returned by create...'
export AWS_ACCESS_KEY_ID="$TELNYX_API_KEY"
export AWS_SECRET_ACCESS_KEY="cloudfs-unused"

sudo mkdir -p /mnt/agentfs
sudo chown "$(id -u):$(id -g)" /mnt/agentfs
juicefs mount --no-usage-report --background --log /tmp/juicefs.log \
  "$META_URL" /mnt/agentfs
```

Do not run `juicefs format` on a filesystem whose status is `ready`, and never edit the underlying `cloudfs-fs-*` bucket directly.

## 2. Install and configure

```bash
cd agent-fleet-shared-workspace
npm install
cp .env.example .env
```

Set `CLOUDFS_MOUNT_PATH` to the absolute mount point. `CLOUDFS_WORKSPACE_DIR` is the directory used inside that mount.

```dotenv
CLOUDFS_MOUNT_PATH=/mnt/agentfs
CLOUDFS_WORKSPACE_DIR=/shared
```

## 3. Run

```bash
npm start
```

## Demo

Run the complete five-agent handoff:

```bash
curl -X POST http://localhost:3000/demo
```

The response contains five registered agents and the read/write history. The resulting files remain in `/mnt/agentfs/shared` and are visible from every other host that mounts the same CloudFS filesystem.

Write an artifact as any agent:

```bash
curl -X POST http://localhost:3000/artifacts \
  -H 'Content-Type: application/json' \
  -d '{"agentId":"agent-6","role":"researcher","path":"research/notes.md","content":"Shared notes"}'
```

Read it from a different agent:

```bash
curl 'http://localhost:3000/artifacts/research%2Fnotes.md?agent=agent-2'
```

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/demo` | Run the five-agent handoff |
| `POST` | `/artifacts` | Initialize an agent and write an artifact |
| `GET` | `/artifacts` | List files currently present in the shared workspace |
| `GET` | `/artifacts/:path` | Read an artifact as the selected `?agent=` |
| `GET` | `/agents/:id` | Get one actor's current state |
| `GET` | `/fleet` | List registered agents and SQL file-operation history |
| `GET` | `/health/liveness` | Liveness check |
| `GET` | `/health/readiness` | Readiness check |

Agent SDK clients can connect to an individual actor's runtime WebSocket route and subscribe to state patches. The server side is implemented with `AgentSocketServer`; connected dashboards see `idle`, `reading`, `writing`, `done`, and `error` transitions in real time.

## Production notes

- Mount the same CloudFS filesystem into every process that hosts fleet actors.
- Writes use temporary files plus atomic rename, avoiding readers observing partial content.
- Concurrent writes to the same file are last-writer-wins unless clients coordinate with CloudFS-supported `flock`/`fcntl` locks.
- Treat `META_URL` and `TELNYX_API_KEY` as secrets. Do not commit either value.
