# Network Scanner

A Python-based TCP port scanner designed for lightweight network reconnaissance and telemetry-driven analysis.

This project explores how a scanning engine, structured telemetry logging, and a simple detection pipeline can be composed into a mini security monitoring workflow.

---

## 🔧 Core Capabilities

- Concurrent TCP port scanning
- Domain name resolution (DNS → IPv4)
- Flexible port specifications (single values & ranges)
- Structured JSONL telemetry logging
- Basic rule-based detection engine
- Spool-based log rotation model
- Mock cloud ingestion pipeline

---

## 🏗 Architecture Overview

The scanner is intentionally designed as a small pipeline rather than a single script:


scanner → telemetry logger → spool/ready → exporter → ingest server


**Components**

- **Scanner Engine** 
  Performs concurrent TCP connect scans and records latency / state.

- **Telemetry Logger** 
  Writes structured JSONL events with rotation into a spool directory.

- **Detection Engine** 
  Evaluates scan results for security-relevant conditions (e.g., exposed admin ports).

- **Exporter** 
  Batches completed telemetry files and forwards them to a mock ingestion endpoint.

- **Cloud Ingest Stub** 
  Simulates a remote telemetry receiver with validation and failure scenarios.

---

## 🚀 Running the Project

Start the mock ingest server:

```bash
python cloud_ingest_stub.py

Run the scanner:

python main.py

(Optional) Run exporter loop:

python exporter.py

```
📄 Telemetry Model

Events are written as JSON Lines (JSONL) for stream-friendly processing.

Example event:

{
  "timestamp": "2026-02-23T21:18:10Z",
  "event": "port_scanned",
  "run_id": "...",
  "ip": "127.0.0.1",
  "port": 22,
  "is_open": true,
  "latency_ms": 1.24
}
🎯 Design Goals

This project focuses on:

Deterministic behavior

Minimal dependencies

Readable data flow

Explicit state transitions

Simple but realistic security tooling patterns

It is not intended as a full-featured scanner, but as an exploration of telemetry and pipeline-oriented design.

⚠️ Legal & Ethical Use

This tool is provided for educational purposes and authorized security testing only.

Only scan systems and networks you own or have explicit permission to test.

📌 Project Status

🚧 Work in Progress — iterative improvements planned:

CLI interface

UDP / SYN scanning variants

Enhanced detection rules

True remote ingestion backend

📝 License

MIT License
