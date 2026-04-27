# 📖 API Reference

Base URL: `http://localhost:8000`

---

## GET /

Registry info.

**Response:**
```json
{
  "name": "🍄 Mycelium Registry",
  "version": "0.2.0",
  "total_agents": 5,
  "online_agents": 5,
  "total_messages_relayed": 142
}
```

---

## GET /health

Health check.

**Response:**
```json
{
  "status": "healthy",
  "agents_registered": 5,
  "timestamp": "2026-04-01T10:00:00Z"
}
```

---

## POST /api/v1/agents/register

Register a new agent.

**Body:**
```json
{
  "agent_id": "ag_abc123",
  "name": "MyAgent",
  "description": "Does amazing things",
  "version": "1.0.0",
  "capabilities": [
    {
      "name": "greet",
      "description": "Greets a person"
    }
  ],
  "endpoint": "http://localhost:8001",
  "tags": ["greeting"],
  "languages": ["english"]
}
```

**Response:**
```json
{
  "status": "registered",
  "agent_id": "ag_abc123",
  "message": "Agent 'MyAgent' registered! 🍄",
  "total_agents_on_network": 6
}
```

---

## GET /api/v1/agents

List all agents.

**Query Params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 50 | Max results |
| status | string | - | Filter by status |

---

## GET /api/v1/agents/discover

Discover agents by query.

**Query Params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| q | string | required | Search query |
| semantic | bool | true | Use semantic search |
| capability | string | - | Filter by capability |
| tags | string | - | Comma-separated tags |
| min_trust | float | 0.0 | Minimum trust score |
| limit | int | 10 | Max results |

**Example:**
```
GET /api/v1/agents/discover?q=I need weather data&semantic=true
```

**Response:**
```json
{
  "query": "I need weather data",
  "search_type": "semantic_v2",
  "agents": [...],
  "total_results": 1,
  "semantic_enabled": true
}
```

---

## GET /api/v1/agents/{agent_id}

Get specific agent card.

---

## DELETE /api/v1/agents/{agent_id}

Remove agent from network.

**Response:**
```json
{
  "status": "deregistered",
  "message": "Agent 'MyAgent' removed."
}
```

---

## POST /api/v1/messages/send

Send message to an agent.

**Body:**
```json
{
  "envelope": {
    "message_id": "msg_abc123",
    "from_agent": "ag_sender",
    "to_agent": "ag_receiver",
    "message_type": "request"
  },
  "payload": {
    "capability": "get_weather",
    "inputs": { "city": "Mumbai" }
  }
}
```

---

## Agent Endpoints

Each agent runs its own server:

### POST /mycelium/handle

Receive and process a message.

### GET /mycelium/card

Get this agent's card.

### GET /mycelium/health

```json
{
  "status": "healthy",
  "agent": "WeatherBuddy",
  "agent_id": "ag_abc123",
  "capabilities": ["get_weather"],
  "requests_served": 142
}
```

---

## Python SDK

### Agent

```python
from mycelium import Agent

agent = Agent(
    name="MyAgent",
    description="Does things",
    version="1.0.0",
    tags=["example"],
    languages=["english"],
    endpoint="http://localhost:8001"
)

@agent.on("my_capability")
def handler(input1: str):
    return {"result": "done"}

agent.register()
agent.serve(port=8001)
```

### Network

```python
from mycelium import Network

network = Network()

agents = network.discover("I need a translator")
agent = network.get_agent("ag_abc123")

result = network.request(
    agent_id="ag_abc123",
    capability="translate",
    inputs={"text": "Hello", "to": "hindi"}
)

all_agents = network.list_agents()
network.show_agents()
```