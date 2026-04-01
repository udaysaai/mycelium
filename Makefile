.PHONY: install dev server test lint clean

install:
	pip install -e .

dev:
	pip install -e ".[dev,server]"

server:
	python -m server.app

test:
	pytest tests/ -v

lint:
	black mycelium/ server/ examples/ tests/
	ruff check mycelium/ server/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/

demo:
	@echo "🍄 Starting Mycelium Demo..."
	@echo "1. Starting registry server..."
	@python -m server.app &
	@sleep 2
	@echo "2. Starting weather agent..."
	@python examples/agents/weather_agent.py &
	@sleep 2
	@echo "3. Starting translator agent..."
	@python examples/agents/translator_agent.py &
	@sleep 2
	@echo "4. Running discovery tutorial..."
	@python examples/tutorials/02_discover_agents.py
	@echo "\n🍄 Demo complete!"

publish:
	python -m build
	twine upload dist/*