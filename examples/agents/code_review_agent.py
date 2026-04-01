"""
🔍 Code Review Agent — Reviews Python code and suggests improvements
"""

from mycelium import Agent

agent = Agent(
    name="CodeGuru",
    description="Reviews Python code for bugs, style issues, and suggests improvements",
    version="1.0.0",
    tags=["code", "review", "python", "bugs", "quality"],
    languages=["english"],
)


@agent.on(
    "review_code",
    description="Review Python code and find issues",
    input_schema={"code": "string — Python code to review"},
    output_schema={"issues": "array", "score": "number", "suggestions": "array"},
)
def review_code(code: str):
    """Review Python code for common issues."""
    issues = []
    suggestions = []
    score = 100

    lines = code.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Check for common issues
        if "eval(" in stripped:
            issues.append({
                "line": i,
                "severity": "critical",
                "message": "eval() is a security risk — never use with user input",
                "fix": "Use ast.literal_eval() or proper parsing instead"
            })
            score -= 20

        if "except:" in stripped and "except Exception" not in stripped:
            issues.append({
                "line": i,
                "severity": "warning",
                "message": "Bare 'except:' catches ALL exceptions including KeyboardInterrupt",
                "fix": "Use 'except Exception as e:' instead"
            })
            score -= 10

        if "import *" in stripped:
            issues.append({
                "line": i,
                "severity": "warning",
                "message": "Wildcard import — makes code hard to read and debug",
                "fix": "Import specific names: 'from module import name1, name2'"
            })
            score -= 5

        if "password" in stripped.lower() and "=" in stripped and ("'" in stripped or '"' in stripped):
            issues.append({
                "line": i,
                "severity": "critical",
                "message": "Possible hardcoded password detected!",
                "fix": "Use environment variables: os.environ.get('PASSWORD')"
            })
            score -= 25

        if len(line) > 120:
            issues.append({
                "line": i,
                "severity": "style",
                "message": f"Line too long ({len(line)} chars). PEP 8 recommends max 79-120",
                "fix": "Break into multiple lines"
            })
            score -= 2

        if "TODO" in stripped or "FIXME" in stripped:
            suggestions.append({
                "line": i,
                "message": f"Unresolved TODO/FIXME found: {stripped}"
            })

        if "print(" in stripped and "def " not in stripped:
            suggestions.append({
                "line": i,
                "message": "Consider using logging instead of print() for production code"
            })

    # General suggestions
    if "def " in code and '"""' not in code and "'''" not in code:
        suggestions.append({
            "line": 0,
            "message": "Functions found without docstrings. Add docstrings for documentation."
        })

    if "import typing" not in code and "from typing" not in code:
        if "def " in code:
            suggestions.append({
                "line": 0,
                "message": "Consider adding type hints to function parameters"
            })

    score = max(0, score)

    return {
        "score": score,
        "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F",
        "total_issues": len(issues),
        "issues": issues,
        "suggestions": suggestions,
        "summary": f"Found {len(issues)} issues and {len(suggestions)} suggestions. Score: {score}/100"
    }


@agent.on(
    "explain_code",
    description="Explain what a piece of Python code does in simple language",
    input_schema={"code": "string — Python code to explain"},
    output_schema={"explanation": "string", "complexity": "string"},
)
def explain_code(code: str):
    """Explain code in simple terms."""
    lines = code.strip().split("\n")
    explanations = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("def "):
            func_name = stripped.split("(")[0].replace("def ", "")
            explanations.append(f"• Defines a function called '{func_name}'")
        elif stripped.startswith("class "):
            class_name = stripped.split("(")[0].split(":")[0].replace("class ", "")
            explanations.append(f"• Defines a class called '{class_name}'")
        elif stripped.startswith("import ") or stripped.startswith("from "):
            explanations.append(f"• Imports external code: {stripped}")
        elif stripped.startswith("for "):
            explanations.append(f"• Starts a loop: {stripped}")
        elif stripped.startswith("if "):
            explanations.append(f"• Checks a condition: {stripped}")
        elif stripped.startswith("return "):
            explanations.append(f"• Returns a value: {stripped}")

    complexity = "simple" if len(lines) < 10 else "moderate" if len(lines) < 50 else "complex"

    return {
        "explanation": "\n".join(explanations) if explanations else "Code structure not recognized",
        "line_count": len(lines),
        "complexity": complexity,
    }


if __name__ == "__main__":
    agent.info()
    try:
        agent.register()
    except Exception:
        print("⚠️  Registry not available.")
    agent.serve(port=8003)