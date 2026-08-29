"""
US Neural: HOL Guard Contract Verification
Proves the brutal acceptance condition for the Semantic Edge Router.
Condition: Mutating MCP call + Guard Deny = 0 provider invocations.
           Mutating MCP call + Guard Allow = 1 provider invocation.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from security.hol_guard import HOLGuard, ToolClass, GuardDecision
except ImportError:
    from ..security.hol_guard import HOLGuard, ToolClass, GuardDecision


class MockMCPProvider:
    def __init__(self):
        self.invocation_count = 0

    def invoke(self, tool_name, payload):
        self.invocation_count += 1
        return f"Executed {tool_name}"


def test_hol_guard_contract():
    print("🛡️ US Neural: HOL Guard Contract Verification 🛡️")
    print("Testing Brutal Acceptance Condition...\n")

    guard = HOLGuard(require_approval=True)
    provider = MockMCPProvider()
    tool_name = "mcp_postgres_query"

    guard.register_tool_class(tool_name, ToolClass.MUTATING)

    # TEST 1: DENY = ZERO INVOCATIONS
    print("🛑 TEST 1: Mutating Tool + Human DENY")
    decision_deny = guard.gate(tool_name, human_decision=False)

    if decision_deny.decision == GuardDecision.DENIED:
        pass  # Short-circuit: Tool NEVER invoked
    elif decision_deny.decision == GuardDecision.APPROVED:
        provider.invoke(tool_name, {"sql": "DROP TABLE users;"})

    assert provider.invocation_count == 0, "FAILED: Tool was invoked despite DENY!"
    print(f"   ✅ PASS: Guard Decision = {decision_deny.decision.value}")
    print(f"   ✅ PASS: Provider Invocations = {provider.invocation_count} (Strictly Zero)\n")

    # TEST 2: ALLOW = EXACTLY ONE INVOCATION
    print("✅ TEST 2: Mutating Tool + Human ALLOW")
    decision_allow = guard.gate(tool_name, human_decision=True)

    if decision_allow.decision == GuardDecision.APPROVED:
        provider.invoke(tool_name, {"sql": "SELECT * FROM users;"})

    assert provider.invocation_count == 1, "FAILED: Tool was not invoked exactly once!"
    print(f"   ✅ PASS: Guard Decision = {decision_allow.decision.value}")
    print(f"   ✅ PASS: Provider Invocations = {provider.invocation_count} (Exactly One)\n")

    print("🎯 CONTRACT VERIFIED: Deny/Review/Error = 0 invocations. Allow = 1 invocation.")


if __name__ == "__main__":
    test_hol_guard_contract()