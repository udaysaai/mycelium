# 🍄 Mycelium Protocol Specification

**Version:** 0.2.0
**License:** MIT

---

## Overview

Mycelium is a networking protocol for AI agents.

Think of it as:
- **DNS** — Agent discovery by capability
- **HTTP** — Agent-to-agent communication
- **Trust system** — Agent reputation scoring

---

## Agent Card

Every agent has an Agent Card — its identity document.

```json
{
  "agent_id": "ag_0e0e7a482683",
  "name": "WeatherBuddy",
  "description": "Provides live weather data",
  "version": "1.0.0",
  "capabilities": [
    {
      "name": "get_weather",
      "description": "Get current weather for any city",
      "input_schema": {
        "fields": { "city": "string" },
        "required": ["city"]
      },
      "output_schema": {
        "fields": {
          "temperature": "number",
          "condition": "string"
        }
      }
    }
  ],
  "endpoint": "http://localhost:8001",
  "tags": ["weather", "live"],
  "languages": ["english", "hindi"],
  "trust_score": 4.8,
  "total_requests_served": 1247,
  "status": "online",
  "protocol_version": "0.2.0"
}
```

---

## Message Format

### Request

```json
{
  "envelope": {
    "message_id": "msg_abc123",
    "from_agent": "ag_sender",
    "to_agent": "ag_receiver",
    "timestamp": "2026-04-01T10:00:00Z",
    "message_type": "request",
    "protocol_version": "0.2.0"
  },
  "payload": {
    "capability": "get_weather",
    "inputs": { "city": "Mumbai" }
  }
}
```

### Response

```json
{
  "envelope": {
    "message_id": "msg_def456",
    "in_reply_to": "msg_abc123",
    "from_agent": "ag_receiver",
    "to_agent": "ag_sender",
    "message_type": "response"
  },
  "payload": {
    "status": "success",
    "capability": "get_weather",
    "outputs": {
      "temperature": 32,
      "condition": "Humid"
    }
  },
  "meta": {
    "processing_time_ms": 145,
    "confidence": 0.99
  }
}
```

---

## Message Types

| Type | Description |
|------|-------------|
| `request` | Ask agent to perform a capability |
| `response` | Reply to a request |
| `error` | Error response |
| `ping` | Health check |
| `pong` | Ping response |

---

## Status Codes

| Code | Description |
|------|-------------|
| `success` | Request completed |
| `error` | General error |
| `timeout` | Agent took too long |
| `capability_not_found` | Capability does not exist |
| `unauthorized` | Authentication failed |

---

## Discovery

### v0.1 — Keyword Search

Matches words against agent name, description, capabilities, tags.

### v0.2 — Semantic Search (Current)

Uses ChromaDB + sentence-transformers.

```
"I need temperature data" → WeatherAgent ✅
"Speak Hindi please"      → TranslatorAgent ✅
"Bitcoin price"           → CryptoAgent ✅
```

---

## Trust Scoring

Score 0.0 to 5.0 based on:

| Factor | Weight |
|--------|--------|
| Success rate | 40% |
| Response consistency | 20% |
| Peer ratings | 15% |
| Volume | 15% |
| Account age | 10% |

---

## REST API

### Registry

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/agents/register` | Register agent |
| DELETE | `/api/v1/agents/{id}` | Remove agent |
| GET | `/api/v1/agents` | List all agents |
| GET | `/api/v1/agents/{id}` | Get agent card |
| GET | `/api/v1/agents/discover?q=...` | Discover agents |
| POST | `/api/v1/messages/send` | Send message |
| GET | `/health` | Registry health |

### Agent

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mycelium/handle` | Receive message |
| GET | `/mycelium/card` | Get agent card |
| GET | `/mycelium/health` | Agent health |