"""
🔢 Math Agent — Solves math problems
"""

from mycelium import Agent
import math

agent = Agent(
    name="MathWiz",
    description="Solves math problems — arithmetic, algebra basics, statistics, and conversions",
    version="1.0.0",
    tags=["math", "calculator", "statistics", "convert", "numbers"],
    languages=["english"],
)


@agent.on(
    "calculate",
    description="Calculate a math expression",
    input_schema={"expression": "string — math expression like '2 + 3 * 4'"},
    output_schema={"result": "number", "expression": "string"},
)
def calculate(expression: str):
    """Safely evaluate a math expression."""
    # Only allow safe characters
    allowed_chars = set("0123456789+-*/().% ")
    if not all(c in allowed_chars for c in expression):
        return {"error": "Invalid characters in expression. Only numbers and +-*/().% allowed."}

    try:
        # Safe eval with no builtins
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "expression": expression,
            "result": round(result, 10) if isinstance(result, float) else result,
        }
    except Exception as e:
        return {"error": f"Cannot calculate: {str(e)}"}


@agent.on(
    "statistics",
    description="Calculate statistics for a list of numbers",
    input_schema={"numbers": "array of numbers"},
    output_schema={"mean": "number", "median": "number", "std_dev": "number"},
)
def statistics(numbers: list):
    """Calculate basic statistics."""
    if not numbers:
        return {"error": "Empty list provided"}

    nums = [float(n) for n in numbers]
    n = len(nums)

    mean = sum(nums) / n

    sorted_nums = sorted(nums)
    if n % 2 == 0:
        median = (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2
    else:
        median = sorted_nums[n // 2]

    variance = sum((x - mean) ** 2 for x in nums) / n
    std_dev = math.sqrt(variance)

    return {
        "count": n,
        "sum": round(sum(nums), 4),
        "mean": round(mean, 4),
        "median": round(median, 4),
        "min": min(nums),
        "max": max(nums),
        "range": round(max(nums) - min(nums), 4),
        "std_dev": round(std_dev, 4),
        "variance": round(variance, 4),
    }


@agent.on(
    "convert",
    description="Convert between units",
    input_schema={"value": "number", "from_unit": "string", "to_unit": "string"},
    output_schema={"result": "number", "conversion": "string"},
)
def convert(value: float, from_unit: str, to_unit: str):
    """Convert between common units."""
    conversions = {
        ("km", "miles"): 0.621371,
        ("miles", "km"): 1.60934,
        ("kg", "lbs"): 2.20462,
        ("lbs", "kg"): 0.453592,
        ("celsius", "fahrenheit"): lambda v: v * 9 / 5 + 32,
        ("fahrenheit", "celsius"): lambda v: (v - 32) * 5 / 9,
        ("meters", "feet"): 3.28084,
        ("feet", "meters"): 0.3048,
        ("liters", "gallons"): 0.264172,
        ("gallons", "liters"): 3.78541,
        ("inr", "usd"): 0.012,
        ("usd", "inr"): 83.5,
    }

    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        factor = conversions[key]
        if callable(factor):
            result = factor(value)
        else:
            result = value * factor

        return {
            "original": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "result": round(result, 4),
            "conversion": f"{value} {from_unit} = {round(result, 4)} {to_unit}",
        }
    else:
        available = [f"{f} → {t}" for f, t in conversions.keys()]
        return {
            "error": f"Conversion from '{from_unit}' to '{to_unit}' not supported",
            "available_conversions": available,
        }


if __name__ == "__main__":
    agent.info()
    try:
        agent.register()
    except Exception:
        print("⚠️  Registry not available.")
    agent.serve(port=8005)