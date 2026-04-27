# ❓ FAQ

## General

**What is Mycelium?**

An open-source networking protocol for AI agents. Agents register, discover each other by natural language, and communicate using a standard format.

**How is it different from LangChain or CrewAI?**

LangChain and CrewAI handle agents within one application. Mycelium handles agents across different systems and developers. They are complementary — you can build a LangChain agent and register it on Mycelium.

**How is it different from Google A2A?**

| | Mycelium | Google A2A |
|--|---------|------------|
| Install | pip install | Complex |
| Focus | Developer-first | Enterprise |
| Discovery | Yes (semantic) | No |
| Status | Working | Spec only |
| Control | Community | Google |

**Is it free?**

Yes. MIT licensed. Free forever for self-hosting.

---

## Technical

**What Python version is required?**

Python 3.9 or higher.

**Does it need internet to run?**

No. Runs fully on localhost for development.

**What database does the registry use?**

SQLite by default. PostgreSQL support planned for v0.3.

**How does semantic search work?**

ChromaDB stores vector embeddings of agent descriptions. Your query is embedded and compared against all agents using cosine similarity. Agents are found by meaning, not exact keywords.

**Is it secure?**

v0.2 has no authentication — suitable for development. HMAC message signing and API keys are planned for v0.3.

**Can I run multiple registries?**

Yes, each registry is independent. Federation is planned for v0.5.

---

## Troubleshooting

**ModuleNotFoundError: No module named mycelium**

```bash
pip install -e .
```

Run from the project root directory with venv active.

**TypeError: Router got unexpected keyword argument on_startup**

FastAPI version issue. Fix:

```bash
pip install "fastapi==0.104.1" "uvicorn==0.24.0" --force-reinstall
```

**Dashboard shows no agents**

Make sure registry is running:

```bash
python -m server.app
```

Dashboard shows demo agents automatically when registry is unreachable.

**twine not recognized**

Use:

```bash
python -m twine upload dist/*
```

**Agents not showing endpoint in registry**

Add `endpoint` parameter when creating agent:

```python
agent = Agent(
    name="MyAgent",
    description="Does things",
    endpoint="http://localhost:8001"
)
```

---

## Contributing

**How do I contribute?**

1. Fork the repo
2. Create a branch
3. Make changes
4. Write tests
5. Submit PR

See CONTRIBUTING.md for details.

**What should I build first?**

Good first issues:
- Add a new example agent
- Improve docs
- Write more tests
- Fix a bug from the Issues tab