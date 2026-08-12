# 🍄 Mycelium Protocol Specification (v0.3.0)

**Version:** 0.3.0 Enterprise  
**License:** MIT  
**Transport:** HTTP / WebSocket (Nervous System Stream)  
**Security:** Enterprise API-Key Authorization (`X-Mycelium-API-Key`) + `HMAC-SHA256` Message Signing  

---

## 1. Protocol Architecture Overview

Mycelium is a decentralized **Semantic Edge Routing Protocol** designed to connect autonomous AI agents with sub-10ms intent discovery and zero Cloud LLM latency tax.

The protocol provides three core capabilities:
1. **Semantic Edge Routing (DNS Layer)** — Vector-mesh discovery powered by local ChromaDB & `all-MiniLM-L6-v2`.
2. **Direct Agent Communication (Transport Layer)** — Secure inter-agent message relay with HMAC-SHA256 signature verification.
3. **Nervous System Stream (Event Layer)** — Real-time WebSocket event broadcast (`ws://.../ws/stream`) for live network monitoring.

---

## 2. Agent Card Identity Schema

Every registered agent node exposes an immutable Agent Card identity document:

```json
{
  "agent_id": "ag_0e0e7a482683",
  "name": "CurrencyMaster",
  "description": "Provides real-time currency exchange rates and forex conversions",
  "version": "0.3.0",
  "capabilities": [
    {
      "name": "convert_currency",
      "description": "Convert currency amount between international ISO codes",
      "input_schema": {
        "fields": {
          "amount": "number",
          "from_curr": "string",
          "to_curr": "string"
        },
        "required": ["amount", "from_curr", "to_curr"]
      },
      "output_schema": {
        "fields": {
          "converted_amount": "number",
          "currency": "string"
        }
      }
    }
  ],
  "endpoint": "http://127.0.0.1:8014",
  "tags": ["currency", "forex", "finance"],
  "languages": ["english"],
  "trust_score": 4.9,
  "total_requests_served": 4812,
  "status": "online",
  "protocol_version": "0.3.0"
}
```

---

## 3. Envelope & Message Specification

### Request Envelope
Sent when initiating an agent capability invocation:

```json
{
  "envelope": {
    "message_id": "msg_8f912b4a",
    "from_agent": "ag_sender_01",
    "to_agent": "ag_0e0e7a482683",
    "timestamp": "2026-08-09T00:15:00Z",
    "message_type": "request",
    "protocol_version": "0.3.0"
  },
  "payload": {
    "capability": "convert_currency",
    "inputs": {
      "amount": 100,
      "from_curr": "USD",
      "to_curr": "EUR"
    }
  },
  "auth": {
    "signature": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "algorithm": "HMAC-SHA256"
  }
}
```

### Response Envelope
Returned by the target node upon execution:

```json
{
  "envelope": {
    "message_id": "msg_9c123d5e",
    "in_reply_to": "msg_8f912b4a",
    "from_agent": "ag_0e0e7a482683",
    "to_agent": "ag_sender_01",
    "message_type": "response",
    "protocol_version": "0.3.0"
  },
  "payload": {
    "status": "success",
    "capability": "convert_currency",
    "outputs": {
      "converted_amount": 92.45,
      "currency": "EUR"
    }
  },
  "meta": {
    "processing_time_ms": 4.12,
    "confidence": 0.99
  }
}
```

---

## 4. Discovery Engine (Semantic Vector-Mesh)

Mycelium replaces legacy keyword matching with a local vector-mesh embedding engine (`all-MiniLM-L6-v2`).

* **Cold Discovery Latency:** `<9.6 ms` (Audited on 100,000 indexed nodes)
* **P95 Bound:** `11.4 ms`
* **Intent Accuracy:** `70.7%` Top-1 Accuracy (+30.3% advantage over BM25 lexical)

```http
GET /api/v1/agents/discover?q=I+want+to+swap+dollars+for+euros&semantic=true&limit=1 HTTP/1.1
Host: 127.0.0.1:8000
X-Mycelium-API-Key: mycelium_secret_key_2026
```

---

## 5. Security & Authentication Specification

### Registry Authorization (`X-Mycelium-API-Key`)
When `MYCELIUM_ENTERPRISE_KEY` is configured in the server environment, all incoming requests to protected endpoints (`/register`, `/discover`, `/{agent_id}`) must include:

```http
X-Mycelium-API-Key: <ENTERPRISE_API_KEY>
```

### Inter-Agent Payload Signing (`HMAC-SHA256`)
To verify message authenticity during inter-agent relaying, sender agents calculate:
$$\text{Signature} = \text{HMAC-SHA256}(\text{agent\_secret}, \text{json\_payload})$$

The signature is attached in the `X-Agent-Signature` HTTP header or `auth.signature` JSON field.

---

## 6. REST API Endpoint Reference

| Method | Path | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/agents/register` | `API-Key` | Register new agent node in vector-mesh |
| `DELETE` | `/api/v1/agents/{id}` | `API-Key` | Deregister agent node |
| `GET` | `/api/v1/agents` | None | List registered agents |
| `GET` | `/api/v1/agents/{id}` | None | Retrieve specific Agent Card |
| `GET` | `/api/v1/agents/discover` | `API-Key` | Sub-10ms semantic intent discovery |
| `POST` | `/api/v1/messages/send` | `HMAC` | Relay message to target agent node |
| `GET` | `/ws/stream` | None | WebSocket Nervous System live feed |
| `GET` | `/health` | None | System health check |