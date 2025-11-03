# -*- coding: utf-8 -*-
"""
Tests for base module
"""
import pytest
import sys
sys.path.append("..")
from webresearcher.base import (
    Message,
    BaseTool,
    count_tokens,
    extract_code,
    build_text_completion_prompt,
)


def test_message_creation():
    """Test Message object creation"""
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    
    msg_dict = msg.to_dict()
    assert msg_dict["role"] == "user"
    assert msg_dict["content"] == "Hello"


def test_extract_code():
    """Test code extraction"""
    text = "Some text <code>print('hello')</code> more text"
    code = extract_code(text)
    assert code == "print('hello')"
    
    # Test without tags
    text_no_tags = "print('hello')"
    code = extract_code(text_no_tags)
    assert code == "print('hello')"


def test_count_tokens():
    """Test token counting"""
    text = "Hello world"
    tokens = count_tokens(text)
    assert isinstance(tokens, int)
    assert tokens > 0


def test_build_text_completion_prompt():
    """Test prompt building"""
    messages = [
        Message(role="system", content="You are helpful"),
        Message(role="user", content="Hello"),
    ]
    prompt = build_text_completion_prompt(messages)
    assert "system:" in prompt
    assert "user:" in prompt
    assert "Hello" in prompt


class MockTool(BaseTool):
    """Mock tool for testing"""
    name = "mock_tool"
    description = "A mock tool"
    parameters = {"type": "object", "properties": {}}
    
    def call(self, params, **kwargs):
        return "mock result"


def test_base_tool():
    """Test BaseTool functionality"""
    tool = MockTool()
    assert tool.name == "mock_tool"
    assert tool.description == "A mock tool"
    
    result = tool.call({})
    assert result == "mock result"
    
    func_def = tool.get_function_definition()
    assert func_def["name"] == "mock_tool"
    assert "description" in func_def
    assert "parameters" in func_def

