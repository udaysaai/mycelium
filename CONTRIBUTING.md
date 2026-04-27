# 🤝 Contributing to Mycelium

Thank you for your interest! 🍄

Mycelium is community-driven. Every contribution matters.

---

## Ways to Contribute

- 🐛 Bug fixes
- ✨ New features
- 📖 Documentation
- 🧪 Tests
- 🤖 New agents
- 🌍 Translations

---

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/mycelium.git
cd mycelium

python -m venv venv
source venv/bin/activate

pip install -e ".[dev,server]"

python -m server.app
```

---

## Workflow

```bash
git checkout -b feature/your-feature-name

# Make changes

pytest tests/ -v

python scripts/system_check.py

git add .
git commit -m "feat: describe your change"
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

---

## Adding a New Agent

Create a file in `examples/agents/`:

```python
from mycelium import Agent

agent = Agent(
    name="YourAgent",
    description="What your agent does",
    version="1.0.0",
    tags=["tag1", "tag2"],
    languages=["english"],
    endpoint="http://localhost:PORT",
)

@agent.on(
    "your_capability",
    description="What this does",
    input_schema={"input1": "string"},
    output_schema={"output1": "string"},
)
def your_handler(input1: str):
    return {"output1": "result"}

if __name__ == "__main__":
    agent.info()
    try:
        agent.register()
    except Exception:
        print("Registry not available")
    agent.serve(port=PORT)
```

---

## Commit Messages

```
feat: add new feature
fix: fix a bug
docs: update documentation
test: add tests
refactor: code changes
chore: maintenance
```

---

## PR Checklist

- [ ] Tests pass
- [ ] Diagnostic passes
- [ ] Code is documented
- [ ] No API keys or passwords committed
- [ ] Commit messages are clear

---

## Code Style

```bash
black mycelium/ server/ examples/ tests/
ruff check mycelium/ server/
```

---

## License

By contributing, you agree your code will be licensed under MIT.