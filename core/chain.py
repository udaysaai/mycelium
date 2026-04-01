"""
⛓️ Agent Chains — Multi-agent workflows

Instead of manually calling agents one by one,
define a CHAIN and Mycelium executes it automatically.

Example:
    chain = Chain("Travel Planning")
    chain.add_step("find_flights", agent="travel_agent")
    chain.add_step("convert_currency", agent="finance_agent", 
                   input_from="find_flights")
    chain.add_step("send_email", agent="email_agent",
                   input_from="convert_currency")
    
    result = chain.execute({"origin": "Pune", "dest": "London"})
    # All 3 agents work in sequence automatically!
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
import time


class ChainStep(BaseModel):
    """A single step in an agent chain."""
    name: str
    capability: str
    agent_id: Optional[str] = None  # Specific agent
    agent_query: Optional[str] = None  # Or discover by query
    inputs: dict[str, Any] = Field(default_factory=dict)
    input_from: Optional[str] = None  # Previous step's output
    input_mapping: dict[str, str] = Field(default_factory=dict)
    timeout: int = 30
    required: bool = True  # If False, chain continues on failure
    
    # Filled after execution
    output: Optional[dict] = None
    success: bool = False
    execution_time_ms: float = 0
    error: Optional[str] = None


class Chain:
    """
    Multi-agent workflow chain.
    
    Usage:
        chain = Chain("Translate Weather Report")
        
        chain.step("get_weather") \\
             .capability("get_weather") \\
             .find_agent("weather forecast") \\
             .with_inputs({"city": "Mumbai"})
        
        chain.step("translate") \\
             .capability("translate") \\
             .find_agent("translator") \\
             .input_from("get_weather", 
                         mapping={"text": "condition"})
        
        result = await chain.execute()
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: list[ChainStep] = []
        self._current_step: Optional[StepBuilder] = None
    
    def step(self, name: str) -> StepBuilder:
        """Add a step to the chain. Returns builder for chaining."""
        builder = StepBuilder(chain=self, step_name=name)
        self._current_step = builder
        return builder
    
    def add_step(self, name: str, capability: str,
                 agent_id: Optional[str] = None,
                 agent_query: Optional[str] = None,
                 inputs: Optional[dict] = None,
                 input_from: Optional[str] = None,
                 input_mapping: Optional[dict] = None) -> Chain:
        """Add a step directly without builder pattern."""
        step = ChainStep(
            name=name,
            capability=capability,
            agent_id=agent_id,
            agent_query=agent_query,
            inputs=inputs or {},
            input_from=input_from,
            input_mapping=input_mapping or {},
        )
        self.steps.append(step)
        return self
    
    async def execute(self, initial_inputs: Optional[dict] = None,
                      network=None) -> dict:
        """Execute the entire chain."""
        if network is None:
            from mycelium.network.client import Network
            network = Network()
        
        results = {}
        chain_start = time.time()
        
        for i, step in enumerate(self.steps):
            step_start = time.time()
            
            try:
                # Resolve agent if needed
                agent_id = step.agent_id
                if not agent_id and step.agent_query:
                    agents = await network.discover_async(
                        step.agent_query
                    )
                    if agents:
                        agent_id = agents[0].agent_id
                    else:
                        raise Exception(
                            f"No agent found for: {step.agent_query}"
                        )
                
                if not agent_id:
                    raise Exception("No agent specified for step")
                
                # Build inputs
                step_inputs = dict(step.inputs)
                
                # Add initial inputs for first step
                if i == 0 and initial_inputs:
                    step_inputs.update(initial_inputs)
                
                # Map inputs from previous step
                if step.input_from and step.input_from in results:
                    prev_output = results[step.input_from]
                    
                    if step.input_mapping:
                        for target_key, source_key in \
                                step.input_mapping.items():
                            if source_key in prev_output:
                                step_inputs[target_key] = \
                                    prev_output[source_key]
                    else:
                        step_inputs.update(prev_output)
                
                # Execute
                result = await network.request_async(
                    agent_id=agent_id,
                    capability=step.capability,
                    inputs=step_inputs,
                    timeout=step.timeout,
                )
                
                step.output = result
                step.success = True
                step.execution_time_ms = \
                    (time.time() - step_start) * 1000
                results[step.name] = result
                
            except Exception as e:
                step.error = str(e)
                step.success = False
                step.execution_time_ms = \
                    (time.time() - step_start) * 1000
                
                if step.required:
                    return {
                        "chain": self.name,
                        "status": "failed",
                        "failed_at_step": step.name,
                        "error": str(e),
                        "completed_steps": i,
                        "total_steps": len(self.steps),
                        "results": results,
                    }
        
        total_time = (time.time() - chain_start) * 1000
        
        return {
            "chain": self.name,
            "status": "completed",
            "total_steps": len(self.steps),
            "completed_steps": len(self.steps),
            "total_time_ms": round(total_time, 1),
            "results": results,
            "final_output": results.get(
                self.steps[-1].name, {}
            ) if self.steps else {},
        }
    
    def visualize(self) -> str:
        """Print chain as ASCII diagram."""
        lines = [f"\n⛓️  Chain: {self.name}\n"]
        
        for i, step in enumerate(self.steps):
            agent = step.agent_id or step.agent_query or "?"
            status = "✅" if step.success else \
                     "❌" if step.error else "⏳"
            
            lines.append(
                f"   {status} Step {i+1}: [{step.name}]"
            )
            lines.append(
                f"      Agent: {agent}"
            )
            lines.append(
                f"      Capability: {step.capability}"
            )
            
            if step.input_from:
                lines.append(
                    f"      Input from: {step.input_from}"
                )
            
            if i < len(self.steps) - 1:
                lines.append("      ↓")
        
        return "\n".join(lines)


class StepBuilder:
    """Builder pattern for creating chain steps fluently."""
    
    def __init__(self, chain: Chain, step_name: str):
        self._chain = chain
        self._step = ChainStep(name=step_name, capability="")
    
    def capability(self, cap: str) -> StepBuilder:
        self._step.capability = cap
        return self
    
    def agent(self, agent_id: str) -> StepBuilder:
        self._step.agent_id = agent_id
        return self
    
    def find_agent(self, query: str) -> StepBuilder:
        self._step.agent_query = query
        return self
    
    def with_inputs(self, inputs: dict) -> StepBuilder:
        self._step.inputs = inputs
        return self
    
    def input_from(self, step_name: str,
                   mapping: Optional[dict] = None) -> StepBuilder:
        self._step.input_from = step_name
        if mapping:
            self._step.input_mapping = mapping
        return self
    
    def optional(self) -> StepBuilder:
        self._step.required = False
        return self
    
    def timeout(self, seconds: int) -> StepBuilder:
        self._step.timeout = seconds
        return self
    
    def build(self) -> Chain:
        self._chain.steps.append(self._step)
        return self._chain