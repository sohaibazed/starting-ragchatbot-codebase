"""Tests for AIGenerator tool-calling behavior."""
from unittest.mock import MagicMock, patch
import pytest

from ai_generator import AIGenerator


def _text_response(text="final answer"):
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp.content = [block]
    return resp


def _tool_use_response(tool_name="search_course_content", tool_input=None, tool_id="tu_1"):
    resp = MagicMock()
    resp.stop_reason = "tool_use"
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input or {"query": "what is MCP"}
    block.id = tool_id
    resp.content = [block]
    return resp


def _tool_use_with_leading_text_response(tool_input=None, tool_id="tu_1"):
    """Realistic Claude response: text block FIRST, then tool_use."""
    resp = MagicMock()
    resp.stop_reason = "tool_use"
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Let me search for that."
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.input = tool_input or {"query": "MCP"}
    tool_block.id = tool_id
    resp.content = [text_block, tool_block]
    return resp


@patch("ai_generator.anthropic.Anthropic")
def test_generate_response_without_tools_returns_text(mock_anthropic):
    client = MagicMock()
    client.messages.create.return_value = _text_response("hi")
    mock_anthropic.return_value = client

    gen = AIGenerator("key", "model")
    out = gen.generate_response(query="hello")
    assert out == "hi"
    assert client.messages.create.call_count == 1


@patch("ai_generator.anthropic.Anthropic")
def test_generate_response_invokes_search_tool_and_returns_final_text(mock_anthropic):
    client = MagicMock()
    client.messages.create.side_effect = [
        _tool_use_response(tool_input={"query": "MCP"}),
        _text_response("synthesized"),
    ]
    mock_anthropic.return_value = client

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "search results text"

    gen = AIGenerator("key", "model")
    out = gen.generate_response(
        query="what is MCP?",
        tools=[{"name": "search_course_content"}],
        tool_manager=tool_manager,
    )

    assert out == "synthesized"
    tool_manager.execute_tool.assert_called_once_with(
        "search_course_content", query="MCP"
    )
    # two API calls: initial + post-tool
    assert client.messages.create.call_count == 2
    # Final call should NOT include tools
    final_kwargs = client.messages.create.call_args_list[1].kwargs
    assert "tools" not in final_kwargs


@patch("ai_generator.anthropic.Anthropic")
def test_tools_and_tool_choice_passed_on_initial_call(mock_anthropic):
    client = MagicMock()
    client.messages.create.return_value = _text_response()
    mock_anthropic.return_value = client

    gen = AIGenerator("key", "model")
    tools = [{"name": "search_course_content"}]
    gen.generate_response(query="q", tools=tools, tool_manager=MagicMock())

    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["tools"] == tools
    assert kwargs["tool_choice"] == {"type": "auto"}


@patch("ai_generator.anthropic.Anthropic")
def test_tool_result_message_structure(mock_anthropic):
    client = MagicMock()
    client.messages.create.side_effect = [
        _tool_use_response(tool_id="abc"),
        _text_response("done"),
    ]
    mock_anthropic.return_value = client

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "RESULT"

    gen = AIGenerator("key", "model")
    gen.generate_response(query="q", tools=[{}], tool_manager=tool_manager)

    second_call_messages = client.messages.create.call_args_list[1].kwargs["messages"]
    # user(query), assistant(tool_use), user(tool_result)
    assert len(second_call_messages) == 3
    tool_result_msg = second_call_messages[2]
    assert tool_result_msg["role"] == "user"
    assert tool_result_msg["content"][0]["type"] == "tool_result"
    assert tool_result_msg["content"][0]["tool_use_id"] == "abc"
    assert tool_result_msg["content"][0]["content"] == "RESULT"


@patch("ai_generator.anthropic.Anthropic")
def test_handles_text_block_before_tool_use_block(mock_anthropic):
    """Real Claude responses often emit a text block BEFORE the tool_use block."""
    client = MagicMock()
    client.messages.create.side_effect = [
        _tool_use_with_leading_text_response(tool_input={"query": "MCP"}),
        _text_response("final"),
    ]
    mock_anthropic.return_value = client

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "R"

    gen = AIGenerator("k", "m")
    out = gen.generate_response(
        query="q", tools=[{"name": "search_course_content"}], tool_manager=tool_manager
    )
    assert out == "final"
    tool_manager.execute_tool.assert_called_once_with("search_course_content", query="MCP")


@patch("ai_generator.anthropic.Anthropic")
def test_tool_execution_exception_propagates(mock_anthropic):
    """If tool execution raises, it surfaces as an exception (becomes HTTP 500 upstream)."""
    client = MagicMock()
    client.messages.create.return_value = _tool_use_response()
    mock_anthropic.return_value = client

    tool_manager = MagicMock()
    tool_manager.execute_tool.side_effect = RuntimeError("tool crashed")

    gen = AIGenerator("k", "m")
    with pytest.raises(RuntimeError, match="tool crashed"):
        gen.generate_response(query="q", tools=[{}], tool_manager=tool_manager)
