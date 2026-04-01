"""
🍄 Mycelium Tutorial 01: Your First Agent

This tutorial shows you how to:
1. Create an agent
2. Add capabilities
3. Register on the network
4. Handle requests

Prerequisites:
    pip install mycelium-ai

    # Start the registry server first:
    python -m server.app
"""

from mycelium import Agent

# =============================================
# STEP 1: Create your agent
# =============================================

agent = Agent(
    name="MathHelper",
    description="A simple math agent that can add, multiply, and solve equations",
    tags=["math", "calculator", "education"],
)

# =============================================
# STEP 2: Add capabilities using @agent.on()
# =============================================


@agent.on(
    "add",
    description="Add two numbers",
    input_schema={"a": "number", "b": "number"},
    output_schema={"result": "number"},
)
def add_numbers(a: float, b: float):
    return {"result": a + b}


@agent.on(
    "multiply",
    description="Multiply two numbers",
    input_schema={"a": "number", "b": "number"},
    output_schema={"result": "number"},
)
def multiply_numbers(a: float, b: float):
    return {"result": a * b}


@agent.on(
    "factorial",
    description="Calculate factorial of a number",
    input_schema={"n": "integer"},
    output_schema={"result": "integer"},
)
def factorial(n: int):
    if n < 0:
        return {"error": "Cannot calculate factorial of negative number"}
    result = 1
    for i in range(2, n + 1):
        result *= i
    return {"result": result, "expression": f"{n}! = {result}"}


# =============================================
# STEP 3: Show agent info
# =============================================

agent.info()

# =============================================
# STEP 4: Register and serve
# =============================================

if __name__ == "__main__":
    try:
        agent.register()
        print("\n✅ Agent registered! Now serving requests...\n")
    except Exception as e:
        print(f"\n⚠️  Skipping registration: {e}")
        print("Tip: Start the registry first with 'python -m server.app'\n")

    agent.serve(port=8003)