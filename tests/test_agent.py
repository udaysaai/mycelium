"""Tests for Mycelium Agent."""

import pytest
from mycelium.core.agent import Agent
from mycelium.core.card import AgentCard
from mycelium.core.message import Message, MessageType, StatusCode
from mycelium.core.capability import Capability


class TestAgentCreation:
    """Test agent creation and basic properties."""

    def test_create_agent(self):
        agent = Agent(name="TestBot", description="A test agent")
        assert agent.name == "TestBot"
        assert agent.card.description == "A test agent"
        assert agent.agent_id.startswith("ag_")

    def test_agent_id_unique(self):
        agent1 = Agent(name="Bot1", description="First")
        agent2 = Agent(name="Bot2", description="Second")
        assert agent1.agent_id != agent2.agent_id

    def test_agent_default_values(self):
        agent = Agent(name="Test", description="Test")
        assert agent.card.version == "0.1.0"
        assert agent.card.status == "offline"
        assert agent.card.trust_score == 0.0
        assert agent.card.languages == ["english"]

    def test_agent_custom_values(self):
        agent = Agent(
            name="Custom",
            description="Custom agent",
            version="2.0.0",
            languages=["hindi", "english"],
            tags=["test", "custom"],
        )
        assert agent.card.version == "2.0.0"
        assert "hindi" in agent.card.languages
        assert "test" in agent.card.tags


class TestCapabilities:
    """Test capability registration and execution."""

    def test_register_capability(self):
        agent = Agent(name="Test", description="Test")

        @agent.on("greet", description="Say hello")
        def greet(name: str):
            return {"message": f"Hello {name}"}

        assert "greet" in agent._capabilities
        assert len(agent.card.capabilities) == 1

    def test_multiple_capabilities(self):
        agent = Agent(name="Test", description="Test")

        @agent.on("add")
        def add(a: int, b: int):
            return {"result": a + b}

        @agent.on("multiply")
        def multiply(a: int, b: int):
            return {"result": a * b}

        assert len(agent._capabilities) == 2
        assert "add" in agent._capabilities
        assert "multiply" in agent._capabilities

    @pytest.mark.asyncio
    async def test_execute_capability(self):
        agent = Agent(name="Test", description="Test")

        @agent.on("add")
        def add(a: int, b: int):
            return {"result": a + b}

        cap = agent._capabilities["add"]
        result = await cap.execute({"a": 5, "b": 3})
        assert result["result"] == 8

    def test_add_capability_without_decorator(self):
        agent = Agent(name="Test", description="Test")

        def my_handler(text: str):
            return {"length": len(text)}

        agent.add_capability(
            name="count",
            handler=my_handler,
            description="Count text length",
        )

        assert "count" in agent._capabilities


class TestMessages:
    """Test message creation and handling."""

    def test_create_request(self):
        msg = Message.create_request(
            from_agent="ag_sender",
            to_agent="ag_receiver",
            capability="translate",
            inputs={"text": "hello", "to": "hindi"},
        )
        assert msg.envelope.from_agent == "ag_sender"
        assert msg.envelope.to_agent == "ag_receiver"
        assert msg.envelope.message_type == MessageType.REQUEST
        assert msg.payload["capability"] == "translate"

    def test_create_response(self):
        request = Message.create_request(
            from_agent="ag_a",
            to_agent="ag_b",
            capability="test",
            inputs={},
        )
        response = Message.create_response(
            original=request,
            outputs={"result": 42},
        )
        assert response.envelope.from_agent == "ag_b"
        assert response.envelope.to_agent == "ag_a"
        assert response.envelope.message_type == MessageType.RESPONSE
        assert response.envelope.in_reply_to == request.envelope.message_id

    def test_create_error(self):
        request = Message.create_request(
            from_agent="ag_a",
            to_agent="ag_b",
            capability="test",
            inputs={},
        )
        error = Message.create_error(
            original=request,
            error_message="Something broke",
        )
        assert error.payload["status"] == StatusCode.ERROR.value
        assert error.payload["error_message"] == "Something broke"

    def test_create_ping(self):
        ping = Message.create_ping(from_agent="ag_a", to_agent="ag_b")
        assert ping.envelope.message_type == MessageType.PING

    def test_message_id_format(self):
        msg = Message.create_request(
            from_agent="ag_a",
            to_agent="ag_b",
            capability="test",
            inputs={},
        )
        assert msg.envelope.message_id.startswith("msg_")


class TestAgentCard:
    """Test AgentCard functionality."""

    def test_card_summary(self):
        card = AgentCard(
            name="TestBot",
            description="A test bot",
            capabilities=[{"name": "greet"}, {"name": "farewell"}],
        )
        summary = card.to_summary()
        assert "TestBot" in summary
        assert "greet" in summary

    def test_is_capable_of(self):
        card = AgentCard(
            name="TestBot",
            description="Test",
            capabilities=[
                {"name": "translate"},
                {"name": "detect_language"},
            ],
        )
        assert card.is_capable_of("translate") is True
        assert card.is_capable_of("fly") is False


class TestMessageHandling:
    """Test agent message handling."""

    @pytest.mark.asyncio
    async def test_handle_request(self):
        agent = Agent(name="Test", description="Test")

        @agent.on("double")
        def double(n: int):
            return {"result": n * 2}

        request = Message.create_request(
            from_agent="ag_client",
            to_agent=agent.agent_id,
            capability="double",
            inputs={"n": 21},
        )

        response = await agent.handle_message(request)
        assert response.payload["status"] == StatusCode.SUCCESS.value
        assert response.payload["outputs"]["result"] == 42

    @pytest.mark.asyncio
    async def test_handle_unknown_capability(self):
        agent = Agent(name="Test", description="Test")

        request = Message.create_request(
            from_agent="ag_client",
            to_agent=agent.agent_id,
            capability="nonexistent",
            inputs={},
        )

        response = await agent.handle_message(request)
        assert response.payload["status"] == StatusCode.CAPABILITY_NOT_FOUND.value

    @pytest.mark.asyncio
    async def test_handle_ping(self):
        agent = Agent(name="PingBot", description="Test")

        ping = Message.create_ping(
            from_agent="ag_client",
            to_agent=agent.agent_id,
        )

        response = await agent.handle_message(ping)
        assert response.payload["outputs"]["pong"] is True