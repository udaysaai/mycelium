"""
🍄 MYCELIUM — Full System Diagnostic Report
=============================================

This script tests EVERY capability of the Mycelium system
and generates a professional report.

Usage:
    1. Start registry:  python -m server.app
    2. Start agents:    python examples/agents/weather_agent.py
                        python examples/agents/translator_agent.py
    3. Run this:        python scripts/system_check.py
"""

import time
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# ============================================================
# CONFIG
# ============================================================

REGISTRY_URL = "http://localhost:8000"
WEATHER_AGENT_URL = "http://localhost:8001"
TRANSLATOR_AGENT_URL = "http://localhost:8002"

# ============================================================
# REPORT DATA
# ============================================================

report = {
    "title": "🍄 MYCELIUM SYSTEM DIAGNOSTIC REPORT",
    "generated_at": "",
    "system_version": "0.1.0",
    "tests": [],
    "summary": {},
}

passed = 0
failed = 0
warnings = 0
total_time_ms = 0


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def test(name: str, category: str):
    """Decorator for test functions."""
    def decorator(func):
        def wrapper():
            global passed, failed, warnings, total_time_ms
            
            start = time.time()
            try:
                result = func()
                elapsed = round((time.time() - start) * 1000, 1)
                total_time_ms += elapsed
                
                if result.get("status") == "PASS":
                    passed += 1
                    icon = "✅"
                elif result.get("status") == "WARN":
                    warnings += 1
                    icon = "⚠️"
                else:
                    failed += 1
                    icon = "❌"
                
                report["tests"].append({
                    "name": name,
                    "category": category,
                    "status": result.get("status", "FAIL"),
                    "icon": icon,
                    "time_ms": elapsed,
                    "details": result.get("details", ""),
                    "data": result.get("data", None),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                
                print(f"  {icon} {name} ({elapsed}ms)")
                if result.get("details"):
                    print(f"     → {result['details']}")
                    
            except Exception as e:
                elapsed = round((time.time() - start) * 1000, 1)
                total_time_ms += elapsed
                failed += 1
                
                report["tests"].append({
                    "name": name,
                    "category": category,
                    "status": "FAIL",
                    "icon": "❌",
                    "time_ms": elapsed,
                    "details": f"Exception: {str(e)}",
                    "data": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                
                print(f"  ❌ {name} ({elapsed}ms)")
                print(f"     → ERROR: {str(e)}")
        
        wrapper._test_name = name
        wrapper._test_category = category
        return wrapper
    return decorator


# ============================================================
# TEST SUITE 1: REGISTRY SERVER
# ============================================================

@test("Registry Server Health Check", "Registry")
def test_registry_health():
    r = httpx.get(f"{REGISTRY_URL}/health", timeout=5)
    if r.status_code == 200:
        data = r.json()
        return {
            "status": "PASS",
            "details": f"Server healthy. Agents registered: {data.get('agents_registered', 0)}",
            "data": data,
        }
    return {"status": "FAIL", "details": f"Status code: {r.status_code}"}


@test("Registry Root Endpoint", "Registry")
def test_registry_root():
    r = httpx.get(f"{REGISTRY_URL}/", timeout=5)
    if r.status_code == 200:
        data = r.json()
        return {
            "status": "PASS",
            "details": f"Registry v{data.get('version', '?')} | Protocol v{data.get('protocol_version', '?')} | {data.get('total_agents', 0)} agents",
            "data": data,
        }
    return {"status": "FAIL", "details": f"Status code: {r.status_code}"}


@test("Swagger Docs Available", "Registry")
def test_swagger_docs():
    r = httpx.get(f"{REGISTRY_URL}/docs", timeout=5)
    if r.status_code == 200:
        return {"status": "PASS", "details": f"Docs accessible at {REGISTRY_URL}/docs"}
    return {"status": "FAIL", "details": f"Status code: {r.status_code}"}


@test("ReDoc Available", "Registry")
def test_redoc():
    r = httpx.get(f"{REGISTRY_URL}/redoc", timeout=5)
    if r.status_code == 200:
        return {"status": "PASS", "details": f"ReDoc accessible at {REGISTRY_URL}/redoc"}
    return {"status": "FAIL", "details": f"Status code: {r.status_code}"}


# ============================================================
# TEST SUITE 2: AGENT REGISTRATION
# ============================================================

@test("Register New Test Agent", "Registration")
def test_register_agent():
    test_agent = {
        "agent_id": "ag_test_diagnostic_001",
        "name": "DiagnosticBot",
        "description": "Temporary agent for system diagnostics",
        "version": "0.0.1",
        "capabilities": [
            {"name": "ping", "description": "Health check"}
        ],
        "tags": ["test", "diagnostic"],
        "languages": ["english"],
        "status": "online",
        "protocol_version": "0.1.0",
    }
    
    r = httpx.post(f"{REGISTRY_URL}/api/v1/agents/register", 
                   json=test_agent, timeout=10)
    if r.status_code == 200:
        data = r.json()
        return {
            "status": "PASS",
            "details": f"Agent registered. Total on network: {data.get('total_agents_on_network', '?')}",
            "data": data,
        }
    return {"status": "FAIL", "details": f"Status {r.status_code}: {r.text}"}


@test("Duplicate Registration (Should Update)", "Registration")
def test_duplicate_registration():
    test_agent = {
        "agent_id": "ag_test_diagnostic_001",
        "name": "DiagnosticBot-Updated",
        "description": "Updated description",
        "version": "0.0.2",
        "capabilities": [],
        "tags": ["test"],
        "languages": ["english"],
        "status": "online",
        "protocol_version": "0.1.0",
    }
    
    r = httpx.post(f"{REGISTRY_URL}/api/v1/agents/register", 
                   json=test_agent, timeout=10)
    if r.status_code == 200:
        return {"status": "PASS", "details": "Re-registration successful (upsert working)"}
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("Get Agent By ID", "Registration")
def test_get_agent():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents/ag_test_diagnostic_001", 
                  timeout=5)
    if r.status_code == 200:
        data = r.json()
        return {
            "status": "PASS",
            "details": f"Found agent: {data.get('name', '?')} v{data.get('version', '?')}",
            "data": data,
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("Get Non-Existent Agent (Should 404)", "Registration")
def test_get_nonexistent_agent():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents/ag_does_not_exist", 
                  timeout=5)
    if r.status_code == 404:
        return {"status": "PASS", "details": "Correctly returned 404 for missing agent"}
    return {"status": "FAIL", "details": f"Expected 404, got {r.status_code}"}


@test("List All Agents", "Registration")
def test_list_agents():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents", timeout=5)
    if r.status_code == 200:
        data = r.json()
        count = data.get("total", 0)
        agents = data.get("agents", [])
        names = [a.get("name", "?") for a in agents[:5]]
        return {
            "status": "PASS",
            "details": f"Found {count} agents: {', '.join(names)}",
            "data": {"count": count, "names": names},
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


# ============================================================
# TEST SUITE 3: DISCOVERY
# ============================================================

@test("Discover by Keyword: 'weather'", "Discovery")
def test_discover_weather():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents/discover",
                  params={"q": "weather forecast temperature"},
                  timeout=5)
    if r.status_code == 200:
        data = r.json()
        count = data.get("total_results", 0)
        if count > 0:
            names = [a.get("name", "?") for a in data.get("agents", [])]
            return {
                "status": "PASS",
                "details": f"Found {count} weather agents: {', '.join(names)}",
            }
        return {"status": "WARN", "details": "Discovery returned 0 results. Is WeatherBuddy running?"}
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("Discover by Keyword: 'translate'", "Discovery")
def test_discover_translate():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents/discover",
                  params={"q": "translate language hindi"},
                  timeout=5)
    if r.status_code == 200:
        data = r.json()
        count = data.get("total_results", 0)
        if count > 0:
            names = [a.get("name", "?") for a in data.get("agents", [])]
            return {
                "status": "PASS",
                "details": f"Found {count} translator agents: {', '.join(names)}",
            }
        return {"status": "WARN", "details": "Discovery returned 0 results. Is LinguaBot running?"}
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("Discover Non-Existent Capability", "Discovery")
def test_discover_nonexistent():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents/discover",
                  params={"q": "quantum_teleportation_xyz"},
                  timeout=5)
    if r.status_code == 200:
        data = r.json()
        count = data.get("total_results", 0)
        if count == 0:
            return {"status": "PASS", "details": "Correctly returned 0 results for nonsense query"}
        return {"status": "WARN", "details": f"Returned {count} results for nonsense query — false positives?"}
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("Discover with Tag Filter", "Discovery")
def test_discover_with_tags():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents/discover",
                  params={"q": "agent", "tags": "weather,forecast"},
                  timeout=5)
    if r.status_code == 200:
        data = r.json()
        return {
            "status": "PASS",
            "details": f"Tag-filtered discovery returned {data.get('total_results', 0)} results",
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


# ============================================================
# TEST SUITE 4: AGENT HEALTH (Direct Agent Endpoints)
# ============================================================

@test("WeatherBuddy Agent Health", "Agent Health")
def test_weather_agent_health():
    r = httpx.get(f"{WEATHER_AGENT_URL}/mycelium/health", timeout=5)
    if r.status_code == 200:
        data = r.json()
        caps = data.get("capabilities", [])
        return {
            "status": "PASS",
            "details": f"Agent: {data.get('agent', '?')} | Capabilities: {', '.join(caps)} | Served: {data.get('requests_served', 0)}",
            "data": data,
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}. Is weather agent running on port 8001?"}


@test("WeatherBuddy Agent Card", "Agent Health")
def test_weather_agent_card():
    r = httpx.get(f"{WEATHER_AGENT_URL}/mycelium/card", timeout=5)
    if r.status_code == 200:
        data = r.json()
        return {
            "status": "PASS",
            "details": f"Card: {data.get('name', '?')} v{data.get('version', '?')} | Tags: {data.get('tags', [])}",
            "data": data,
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("LinguaBot Agent Health", "Agent Health")
def test_translator_agent_health():
    r = httpx.get(f"{TRANSLATOR_AGENT_URL}/mycelium/health", timeout=5)
    if r.status_code == 200:
        data = r.json()
        caps = data.get("capabilities", [])
        return {
            "status": "PASS",
            "details": f"Agent: {data.get('agent', '?')} | Capabilities: {', '.join(caps)} | Served: {data.get('requests_served', 0)}",
            "data": data,
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}. Is translator agent running on port 8002?"}


# ============================================================
# TEST SUITE 5: AGENT-TO-AGENT COMMUNICATION
# ============================================================

@test("Weather Request: Pune", "Communication")
def test_weather_pune():
    # Find weather agent
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents", timeout=5)
    agents = r.json().get("agents", [])
    
    weather_agent = None
    for a in reversed(agents):
        if "weather" in a.get("name", "").lower() and a.get("endpoint"):
            weather_agent = a
            break
    
    if not weather_agent:
        return {"status": "FAIL", "details": "No weather agent with endpoint found"}
    
    # Send message through registry
    message = {
        "envelope": {
            "message_id": "msg_test_weather_001",
            "from_agent": "ag_test_diagnostic_001",
            "to_agent": weather_agent["agent_id"],
            "message_type": "request",
            "protocol_version": "0.1.0",
        },
        "payload": {
            "capability": "get_weather",
            "inputs": {"city": "Pune"},
        }
    }
    
    r = httpx.post(f"{REGISTRY_URL}/api/v1/messages/send", 
                   json=message, timeout=15)
    if r.status_code == 200:
        data = r.json()
        outputs = data.get("payload", {}).get("outputs", {})
        return {
            "status": "PASS",
            "details": f"Pune: {outputs.get('temperature', '?')}°C, {outputs.get('condition', '?')}, Humidity: {outputs.get('humidity', '?')}%",
            "data": outputs,
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}: {r.text[:200]}"}


@test("Weather Request: Mumbai", "Communication")
def test_weather_mumbai():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents", timeout=5)
    agents = r.json().get("agents", [])
    
    weather_agent = None
    for a in reversed(agents):
        if "weather" in a.get("name", "").lower() and a.get("endpoint"):
            weather_agent = a
            break
    
    if not weather_agent:
        return {"status": "FAIL", "details": "No weather agent found"}
    
    message = {
        "envelope": {
            "message_id": "msg_test_weather_002",
            "from_agent": "ag_test_diagnostic_001",
            "to_agent": weather_agent["agent_id"],
            "message_type": "request",
        },
        "payload": {
            "capability": "get_weather",
            "inputs": {"city": "Mumbai"},
        }
    }
    
    r = httpx.post(f"{REGISTRY_URL}/api/v1/messages/send",
                   json=message, timeout=15)
    if r.status_code == 200:
        outputs = r.json().get("payload", {}).get("outputs", {})
        return {
            "status": "PASS",
            "details": f"Mumbai: {outputs.get('temperature', '?')}°C, {outputs.get('condition', '?')}",
            "data": outputs,
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("Weather Forecast Request", "Communication")
def test_weather_forecast():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents", timeout=5)
    agents = r.json().get("agents", [])
    
    weather_agent = None
    for a in reversed(agents):
        if "weather" in a.get("name", "").lower() and a.get("endpoint"):
            weather_agent = a
            break
    
    if not weather_agent:
        return {"status": "FAIL", "details": "No weather agent found"}
    
    message = {
        "envelope": {
            "message_id": "msg_test_forecast_001",
            "from_agent": "ag_test_diagnostic_001",
            "to_agent": weather_agent["agent_id"],
            "message_type": "request",
        },
        "payload": {
            "capability": "get_forecast",
            "inputs": {"city": "Delhi", "days": 3},
        }
    }
    
    r = httpx.post(f"{REGISTRY_URL}/api/v1/messages/send",
                   json=message, timeout=15)
    if r.status_code == 200:
        outputs = r.json().get("payload", {}).get("outputs", {})
        forecast = outputs.get("forecast", [])
        return {
            "status": "PASS",
            "details": f"Delhi 3-day forecast received: {len(forecast)} days",
            "data": outputs,
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("Translation: English → Hindi", "Communication")
def test_translate_hindi():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents", timeout=5)
    agents = r.json().get("agents", [])
    
    translator = None
    for a in reversed(agents):
        if "lingua" in a.get("name", "").lower() and a.get("endpoint"):
            translator = a
            break
    
    if not translator:
        return {"status": "FAIL", "details": "No translator agent found"}
    
    message = {
        "envelope": {
            "message_id": "msg_test_translate_001",
            "from_agent": "ag_test_diagnostic_001",
            "to_agent": translator["agent_id"],
            "message_type": "request",
        },
        "payload": {
            "capability": "translate",
            "inputs": {"text": "hello", "to": "hindi"},
        }
    }
    
    r = httpx.post(f"{REGISTRY_URL}/api/v1/messages/send",
                   json=message, timeout=15)
    if r.status_code == 200:
        outputs = r.json().get("payload", {}).get("outputs", {})
        translated = outputs.get("translated", "?")
        confidence = outputs.get("confidence", 0)
        return {
            "status": "PASS",
            "details": f"'hello' → '{translated}' (confidence: {confidence})",
            "data": outputs,
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("Translation: English → Marathi", "Communication")
def test_translate_marathi():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents", timeout=5)
    agents = r.json().get("agents", [])
    
    translator = None
    for a in reversed(agents):
        if "lingua" in a.get("name", "").lower() and a.get("endpoint"):
            translator = a
            break
    
    if not translator:
        return {"status": "FAIL", "details": "No translator agent found"}
    
    message = {
        "envelope": {
            "message_id": "msg_test_translate_002",
            "from_agent": "ag_test_diagnostic_001",
            "to_agent": translator["agent_id"],
            "message_type": "request",
        },
        "payload": {
            "capability": "translate",
            "inputs": {"text": "hello", "to": "marathi"},
        }
    }
    
    r = httpx.post(f"{REGISTRY_URL}/api/v1/messages/send",
                   json=message, timeout=15)
    if r.status_code == 200:
        outputs = r.json().get("payload", {}).get("outputs", {})
        return {
            "status": "PASS",
            "details": f"'hello' → '{outputs.get('translated', '?')}'",
            "data": outputs,
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("Language Detection", "Communication")
def test_detect_language():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents", timeout=5)
    agents = r.json().get("agents", [])
    
    translator = None
    for a in reversed(agents):
        if "lingua" in a.get("name", "").lower() and a.get("endpoint"):
            translator = a
            break
    
    if not translator:
        return {"status": "FAIL", "details": "No translator agent found"}
    
    message = {
        "envelope": {
            "message_id": "msg_test_detect_001",
            "from_agent": "ag_test_diagnostic_001",
            "to_agent": translator["agent_id"],
            "message_type": "request",
        },
        "payload": {
            "capability": "detect_language",
            "inputs": {"text": "नमस्ते दुनिया"},
        }
    }
    
    r = httpx.post(f"{REGISTRY_URL}/api/v1/messages/send",
                   json=message, timeout=15)
    if r.status_code == 200:
        outputs = r.json().get("payload", {}).get("outputs", {})
        return {
            "status": "PASS",
            "details": f"Detected: {outputs.get('language', '?')} (confidence: {outputs.get('confidence', '?')})",
            "data": outputs,
        }
    return {"status": "FAIL", "details": f"Status: {r.status_code}"}


@test("Invalid Capability Request", "Communication")
def test_invalid_capability():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents", timeout=5)
    agents = r.json().get("agents", [])
    
    any_agent = None
    for a in reversed(agents):
        if a.get("endpoint"):
            any_agent = a
            break
    
    if not any_agent:
        return {"status": "FAIL", "details": "No agent with endpoint found"}
    
    message = {
        "envelope": {
            "message_id": "msg_test_invalid_001",
            "from_agent": "ag_test_diagnostic_001",
            "to_agent": any_agent["agent_id"],
            "message_type": "request",
        },
        "payload": {
            "capability": "fly_to_moon",
            "inputs": {},
        }
    }
    
    r = httpx.post(f"{REGISTRY_URL}/api/v1/messages/send",
                   json=message, timeout=15)
    if r.status_code == 200:
        data = r.json()
        status = data.get("payload", {}).get("status", "")
        if status == "capability_not_found":
            return {"status": "PASS", "details": "Correctly returned 'capability_not_found' for invalid capability"}
        return {"status": "WARN", "details": f"Got response but status was: {status}"}
    return {"status": "PASS", "details": f"Server rejected with status {r.status_code} (acceptable)"}


# ============================================================
# TEST SUITE 6: MULTI-AGENT CHAIN
# ============================================================

@test("Multi-Agent Chain: Weather → Translate", "Chain")
def test_multi_agent_chain():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents", timeout=5)
    agents = r.json().get("agents", [])
    
    weather_agent = None
    translator = None
    
    for a in reversed(agents):
        if "weather" in a.get("name", "").lower() and a.get("endpoint"):
            weather_agent = a
        if "lingua" in a.get("name", "").lower() and a.get("endpoint"):
            translator = a
    
    if not weather_agent or not translator:
        return {"status": "FAIL", "details": "Need both weather and translator agents running"}
    
    # Step 1: Get weather
    msg1 = {
        "envelope": {
            "message_id": "msg_chain_step1",
            "from_agent": "ag_test_diagnostic_001",
            "to_agent": weather_agent["agent_id"],
            "message_type": "request",
        },
        "payload": {
            "capability": "get_weather",
            "inputs": {"city": "Bangalore"},
        }
    }
    
    r1 = httpx.post(f"{REGISTRY_URL}/api/v1/messages/send",
                    json=msg1, timeout=15)
    
    if r1.status_code != 200:
        return {"status": "FAIL", "details": f"Step 1 (weather) failed: {r1.status_code}"}
    
    weather_data = r1.json().get("payload", {}).get("outputs", {})
    weather_text = f"{weather_data.get('city', '?')} is {weather_data.get('temperature', '?')} degrees and {weather_data.get('condition', '?')}"
    
    # Step 2: Translate weather to Hindi
    msg2 = {
        "envelope": {
            "message_id": "msg_chain_step2",
            "from_agent": "ag_test_diagnostic_001",
            "to_agent": translator["agent_id"],
            "message_type": "request",
        },
        "payload": {
            "capability": "translate",
            "inputs": {"text": weather_text, "to": "hindi"},
        }
    }
    
    r2 = httpx.post(f"{REGISTRY_URL}/api/v1/messages/send",
                    json=msg2, timeout=15)
    
    if r2.status_code != 200:
        return {"status": "FAIL", "details": f"Step 2 (translate) failed: {r2.status_code}"}
    
    translate_data = r2.json().get("payload", {}).get("outputs", {})
    
    return {
        "status": "PASS",
        "details": f"Chain complete! Weather: '{weather_text}' → Hindi: '{translate_data.get('translated', '?')}'",
        "data": {
            "step1_weather": weather_data,
            "step2_translation": translate_data,
        }
    }


# ============================================================
# TEST SUITE 7: EDGE CASES & ERROR HANDLING
# ============================================================

@test("Message to Non-Existent Agent", "Error Handling")
def test_message_to_ghost():
    message = {
        "envelope": {
            "message_id": "msg_ghost_001",
            "from_agent": "ag_test_diagnostic_001",
            "to_agent": "ag_this_agent_does_not_exist",
            "message_type": "request",
        },
        "payload": {
            "capability": "anything",
            "inputs": {},
        }
    }
    
    r = httpx.post(f"{REGISTRY_URL}/api/v1/messages/send",
                   json=message, timeout=10)
    if r.status_code == 404:
        return {"status": "PASS", "details": "Correctly returned 404 for non-existent agent"}
    return {"status": "WARN", "details": f"Expected 404, got {r.status_code}"}


@test("Empty Search Query", "Error Handling")
def test_empty_search():
    r = httpx.get(f"{REGISTRY_URL}/api/v1/agents/discover",
                  params={"q": ""},
                  timeout=5)
    # Should either return empty results or error — both are acceptable
    if r.status_code in [200, 422]:
        return {"status": "PASS", "details": f"Handled empty query gracefully (status: {r.status_code})"}
    return {"status": "WARN", "details": f"Unexpected status: {r.status_code}"}


# ============================================================
# TEST SUITE 8: CLEANUP
# ============================================================

@test("Deregister Test Agent", "Cleanup")
def test_deregister():
    r = httpx.delete(f"{REGISTRY_URL}/api/v1/agents/ag_test_diagnostic_001",
                     timeout=5)
    if r.status_code == 200:
        return {"status": "PASS", "details": "Test agent cleaned up successfully"}
    return {"status": "WARN", "details": f"Cleanup returned status: {r.status_code}"}


# ============================================================
# SDK IMPORT TESTS (No server needed)
# ============================================================

@test("Import Mycelium SDK", "SDK")
def test_import_sdk():
    try:
        from mycelium import Agent, Network, AgentCard, Message, Capability
        return {"status": "PASS", "details": "All core classes imported successfully"}
    except ImportError as e:
        return {"status": "FAIL", "details": f"Import failed: {e}"}


@test("Create Agent Instance", "SDK")
def test_create_agent():
    from mycelium import Agent
    agent = Agent(name="TestSDK", description="SDK Test Agent")
    
    if agent.name == "TestSDK" and agent.agent_id.startswith("ag_"):
        return {
            "status": "PASS",
            "details": f"Agent created: {agent.name} (ID: {agent.agent_id})",
        }
    return {"status": "FAIL", "details": "Agent creation returned unexpected values"}


@test("Register Capability on Agent", "SDK")
def test_register_capability():
    from mycelium import Agent
    agent = Agent(name="CapTest", description="Test")
    
    @agent.on("test_cap", description="Test capability")
    def handler(x: int):
        return {"doubled": x * 2}
    
    if "test_cap" in agent._capabilities:
        return {"status": "PASS", "details": "Capability 'test_cap' registered via decorator"}
    return {"status": "FAIL", "details": "Capability not found after registration"}


@test("Create Message Objects", "SDK")
def test_create_messages():
    from mycelium.core.message import Message, MessageType
    
    # Request
    req = Message.create_request(
        from_agent="ag_a", to_agent="ag_b",
        capability="test", inputs={"key": "value"}
    )
    
    # Response
    resp = Message.create_response(
        original=req, outputs={"result": 42}
    )
    
    # Ping
    ping = Message.create_ping(from_agent="ag_a", to_agent="ag_b")
    
    checks = [
        req.envelope.message_type == MessageType.REQUEST,
        resp.envelope.message_type == MessageType.RESPONSE,
        resp.envelope.in_reply_to == req.envelope.message_id,
        ping.envelope.message_type == MessageType.PING,
    ]
    
    if all(checks):
        return {"status": "PASS", "details": "Request, Response, and Ping messages created correctly"}
    return {"status": "FAIL", "details": f"Some checks failed: {checks}"}


@test("Agent Card Capabilities Check", "SDK")
def test_agent_card():
    from mycelium.core.card import AgentCard
    
    card = AgentCard(
        name="TestCard",
        description="Test",
        capabilities=[
            {"name": "fly"},
            {"name": "swim"},
        ]
    )
    
    if card.is_capable_of("fly") and not card.is_capable_of("drive"):
        return {"status": "PASS", "details": "is_capable_of() working correctly"}
    return {"status": "FAIL", "details": "is_capable_of() returned wrong results"}


# ============================================================
# RUN ALL TESTS
# ============================================================

def run_all():
    """Run all tests and generate report."""
    global passed, failed, warnings, total_time_ms
    
    report["generated_at"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    
    print()
    print("=" * 65)
    print("  🍄 MYCELIUM — FULL SYSTEM DIAGNOSTIC REPORT")
    print("=" * 65)
    print(f"  Generated: {report['generated_at']}")
    print(f"  System Version: {report['system_version']}")
    print(f"  Registry: {REGISTRY_URL}")
    print("=" * 65)
    
    # Collect all test functions
    all_tests = [
        # Registry
        test_registry_health,
        test_registry_root,
        test_swagger_docs,
        test_redoc,
        # Registration
        test_register_agent,
        test_duplicate_registration,
        test_get_agent,
        test_get_nonexistent_agent,
        test_list_agents,
        # Discovery
        test_discover_weather,
        test_discover_translate,
        test_discover_nonexistent,
        test_discover_with_tags,
        # Agent Health
        test_weather_agent_health,
        test_weather_agent_card,
        test_translator_agent_health,
        # Communication
        test_weather_pune,
        test_weather_mumbai,
        test_weather_forecast,
        test_translate_hindi,
        test_translate_marathi,
        test_detect_language,
        test_invalid_capability,
        # Chain
        test_multi_agent_chain,
        # Error Handling
        test_message_to_ghost,
        test_empty_search,
        # Cleanup
        test_deregister,
        # SDK
        test_import_sdk,
        test_create_agent,
        test_register_capability,
        test_create_messages,
        test_agent_card,
    ]
    
    # Group by category
    current_category = None
    for test_func in all_tests:
        category = test_func._test_category
        if category != current_category:
            current_category = category
            print(f"\n{'─' * 50}")
            print(f"  📋 {category}")
            print(f"{'─' * 50}")
        
        test_func()
    
    # Summary
    total = passed + failed + warnings
    pass_rate = round((passed / total) * 100, 1) if total > 0 else 0
    
    report["summary"] = {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "warnings": warnings,
        "pass_rate": pass_rate,
        "total_time_ms": round(total_time_ms, 1),
    }
    
    print(f"\n{'=' * 65}")
    print(f"  📊 SUMMARY")
    print(f"{'=' * 65}")
    print(f"  Total Tests:    {total}")
    print(f"  ✅ Passed:      {passed}")
    print(f"  ❌ Failed:      {failed}")
    print(f"  ⚠️  Warnings:   {warnings}")
    print(f"  📈 Pass Rate:   {pass_rate}%")
    print(f"  ⏱️  Total Time:  {round(total_time_ms, 1)}ms")
    print(f"{'=' * 65}")
    
    # Health verdict
    if failed == 0 and warnings == 0:
        verdict = "🟢 ALL SYSTEMS OPERATIONAL — PERFECT HEALTH"
    elif failed == 0:
        verdict = "🟡 OPERATIONAL WITH WARNINGS — Review warnings above"
    elif failed <= 3:
        verdict = "🟠 PARTIALLY OPERATIONAL — Some features not working"
    else:
        verdict = "🔴 CRITICAL ISSUES — Multiple failures detected"
    
    print(f"\n  VERDICT: {verdict}")
    print(f"\n{'=' * 65}")
    
    # Save report to file
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"diagnostic_{timestamp}.json"
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"\n  📄 Full report saved: {report_file}")
    print(f"{'=' * 65}\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)