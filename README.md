# Network Telemetry & Detection Pipeline

A security monitoring mini-pipeline built in Python — combining concurrent TCP scanning, structured telemetry, rule-based alerting, and a batched log export system into a cohesive end-to-end workflow.

Designed to mirror the architecture patterns found in real SIEM/EDR tooling: events flow from a scanner through a detection engine, get written to a managed spool, and are forwarded to an ingestion backend with retry logic and checkpointing.

---

## What This Demonstrates

- **Threat detection logic** — rule-based engine flags exposed remote admin ports (SSH/RDP/VNC), exposed database ports, and excessive open port counts with structured severity levels
- **Structured telemetry** — all scan activity emitted as JSONL events with run IDs, timestamps, and enriched metadata — queryable and pipeline-friendly
- **Log rotation & spooling** — size-based log rotation moves completed files to a `spool/ready` directory, decoupling collection from export
- **Reliable export with backoff** — checkpoint-based exporter batches telemetry and forwards it with exponential backoff + jitter on 429/5xx, preventing data loss on transient failures
- **Mock ingest server** — simulates a real ingestion endpoint with API key auth, field validation, and randomized failure injection (overload/server error scenarios)
- **Concurrent scanning** — thread pool-based TCP connect scanner with latency measurement and DNS resolution

---

## Pipeline Architecture
```
scanner → detection engine → telemetry logger → spool/ready → exporter → ingest server
```

| Component | File | Role |
|---|---|---|
| Scanner | `scanner.py` | Concurrent TCP connect scans with latency tracking |
| Detection Engine | `detection.py` | Rule-based alerting on scan results |
| Telemetry Logger | `telemetry.py` | Thread-safe JSONL writer with size-based rotation |
| Exporter | `exporter.py` | Checkpoint-tracked batch forwarder with retry logic |
| Ingest Server | `cloud_ingest_stub.py` | Mock receiver with auth, validation, failure simulation |
| Entry Point | `main.py` | Interactive CLI for scan mode and target selection |

---

## Detection Rules

| Rule ID | Severity | Trigger |
|---|---|---|
| `OPEN_REMOTE_ADMIN_PORT` | High | SSH (22), RDP (3389), or VNC (5900) found open |
| `OPEN_REMOTE_DATABASE_PORT` | High | MySQL (3306), Postgres (5432), or Redis (6379) found open |
| `EXCESSIVE_OPEN_PORTS` | Medium | Open port count exceeds configurable threshold |

---

## Telemetry Event Schema

Events are written as JSON Lines for stream-compatible processing:
```json
{
  "timestamp": "2026-02-23T21:18:10Z",
  "event": "port_scanned",
  "run_id": "...",
  "ip": "127.0.0.1",
  "port": 22,
  "is_open": true,
  "latency_ms": 1.24
}
```

Event types: `scan_started`, `port_scanned`, `alert`, `scan_ended`

---

## Quickstart
```bash
# Start the mock ingest server
python cloud_ingest_stub.py

# Run the scanner (interactive CLI)
python main.py

# Run the exporter loop
python exporter.py
```

---

## Planned Improvements

- CLI flag interface (argparse)
- UDP / SYN scan variants
- Additional detection rules
- True remote ingestion backend

---

## Legal & Ethical Use

For educational purposes and authorized testing only. Only scan systems you own or have explicit written permission to test.

---

## License

MIT
