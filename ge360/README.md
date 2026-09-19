# GE360 deployment layer

This directory turns the upstream Mautic codebase into the GE360 marketing component without hard-forking Mautic internals.

## Goals

- Keep Mautic upgradeable.
- Run smoothly on the GE360 Debian host.
- Keep services private on localhost by default.
- Connect Prospex, SuiteCRM, n8n and Jarvis through stable environment variables and JSON contracts.
- Never commit production passwords or API tokens.

## Services

| Service | Purpose | Default bind |
|---|---|---|
| `db` | MySQL database | internal only |
| `mautic_web` | Mautic web UI/API | `127.0.0.1:8793` |
| `mautic_cron` | Mautic scheduled jobs | internal only |
| `mautic_worker` | Mautic async queue worker | internal only |
| `ge360_bridge` | Lightweight GE360 webhook bridge | `127.0.0.1:8794` |

The compose layout follows the current official Mautic Docker model: web, cron and worker share the persistent Mautic directories.

## Install

```bash
cd ge360
chmod +x install.sh backup.sh check.sh
./install.sh
```

The installer creates local `.env` and `.mautic_env` files from the examples and generates database/bridge secrets when they are empty.

Then open:

```text
http://127.0.0.1:8793
```

For remote access, publish it through the existing GE360 reverse proxy/Tailscale layer instead of exposing the Docker port directly to the Internet.

## Configure integrations

Edit `ge360/.env` and set the URLs that exist on the host:

```dotenv
GE360_PROSPEX_URL=http://host.docker.internal:8788
GE360_SUITECRM_URL=http://host.docker.internal:8790
GE360_N8N_URL=http://host.docker.internal:5678
GE360_JARVIS_URL=http://host.docker.internal:8000
N8N_PROSPEX_WEBHOOK_URL=
N8N_MAUTIC_WEBHOOK_URL=
```

On Linux, the compose file maps `host.docker.internal` to Docker's host gateway.

## Plugin

After the first Mautic setup, go to **Settings → Plugins** and use **Install/Upgrade Plugins**. The plugin appears as **GE360 Integration Hub**.

The private status route is:

```text
/ge360/status
```

It reports only whether endpoints are configured. It never returns tokens or passwords.

## Bridge API

Dashboard:

```text
http://127.0.0.1:8794/
```

The dashboard checks reachability of Mautic, Prospex, SuiteCRM, n8n and Jarvis without exposing credentials.

Health:

```bash
curl http://127.0.0.1:8794/health
```

Forward a Prospex event to the configured n8n webhook:

```bash
curl -X POST http://127.0.0.1:8794/webhook/prospex \
  -H "Content-Type: application/json" \
  -H "X-GE360-Token: YOUR_TOKEN" \
  -d '{"source":"prospex","event":"lead.created","data":{}}'
```

The bridge deliberately does not contain CRM business logic. n8n remains the orchestrator so flows can evolve without changing the Mautic core.

## Backup

```bash
./backup.sh
```

Backups are written under `ge360/backups/` and are ignored by Git.

## Check

```bash
./check.sh
```

## Resource policy

The stack is intentionally conservative:

- one Mautic worker;
- no RabbitMQ or Redis by default;
- MySQL limited to a moderate InnoDB buffer pool;
- local-only published ports;
- lightweight Python bridge with no third-party Python packages.

RabbitMQ/Redis can be added later if actual campaign volume justifies them.
