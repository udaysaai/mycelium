"""
US Neural: HOL (Human-On-the-Loop) Guard
Policy enforcement point between Mycelium's semantic match and tool invocation.
Mutating tools require human approval; read-only tools auto-pass.
The deny short-circuits BEFORE the tool is ever invoked.
"""
from dataclasses import dataclass
from enum import Enum


class ToolClass(Enum):
    READ_ONLY = "read_only"
    MUTATING = "mutating"
    UNKNOWN = "unknown"  # fail-safe: treated as mutating


class GuardDecision(Enum):
    APPROVED = "approved"
    DENIED = "denied"
    PENDING_HUMAN = "pending_human"


@dataclass
class GuardResult:
    decision: GuardDecision
    tool_class: ToolClass
    reason: str


class HOLGuard:
    MUTATING_KEYWORDS = [
        "send", "write", "delete", "update", "insert", "execute",
        "notify", "post", "create", "remove", "drop", "alter",
        "modify", "publish", "deploy", "transfer", "charge", "pay",
    ]
    READ_KEYWORDS = [
        "search", "get", "fetch", "query", "read", "list",
        "retrieve", "describe", "lookup", "find",
    ]

    def __init__(self, require_approval: bool = True):
        self.require_approval = require_approval
        self.explicit_mutating: set = set()
        self.explicit_read_only: set = set()
        self.decision_log: list = []

    def register_tool_class(self, tool_name: str, tool_class: ToolClass):
        """Explicit classification wins over heuristics."""
        if tool_class == ToolClass.MUTATING:
            self.explicit_mutating.add(tool_name)
        elif tool_class == ToolClass.READ_ONLY:
            self.explicit_read_only.add(tool_name)

    def classify(self, tool_name: str, tool_description: str = "") -> ToolClass:
        if tool_name in self.explicit_mutating:
            return ToolClass.MUTATING
        if tool_name in self.explicit_read_only:
            return ToolClass.READ_ONLY

        text = f"{tool_name} {tool_description}".lower()
        mutating_score = sum(1 for kw in self.MUTATING_KEYWORDS if kw in text)
        read_score = sum(1 for kw in self.READ_KEYWORDS if kw in text)

        if mutating_score > read_score:
            return ToolClass.MUTATING
        if read_score > mutating_score:
            return ToolClass.READ_ONLY
        return ToolClass.UNKNOWN  # fail-safe

    def gate(self, tool_name: str, tool_description: str = "",
             human_decision: bool | None = None) -> GuardResult:
        tool_class = self.classify(tool_name, tool_description)

        if tool_class == ToolClass.READ_ONLY:
            return self._result(tool_name, GuardDecision.APPROVED,
                                tool_class, "read-only, auto-approved")

        if not self.require_approval:
            return self._result(tool_name, GuardDecision.APPROVED,
                                tool_class, "approval disabled (dev mode)")

        if human_decision is None:
            return self._result(tool_name, GuardDecision.PENDING_HUMAN,
                                tool_class, "mutating tool: awaiting human approval")

        if human_decision:
            return self._result(tool_name, GuardDecision.APPROVED,
                                tool_class, "human approved")
        return self._result(tool_name, GuardDecision.DENIED,
                            tool_class, "human denied — tool never invoked")

    def _result(self, tool_name, decision, tool_class, reason) -> GuardResult:
        self.decision_log.append({
            "tool": tool_name, "decision": decision.value,
            "class": tool_class.value, "reason": reason,
        })
        return GuardResult(decision, tool_class, reason)