# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Tests for WebWeaver Agent
"""
import pytest
import asyncio
import os
from webresearcher.tool_memory import MemoryBank, RetrieveTool
from webresearcher.tool_planner_search import PlannerSearchTool
from webresearcher.web_weaver_agent import (
    WebWeaverAgent,
    WebWeaverPlanner,
    WebWeaverWriter,
)


def test_memory_bank_basic():
    """Test basic MemoryBank operations."""
    memory = MemoryBank()

    # Test add_evidence
    result = memory.add_evidence(
        content="Full evidence content here",
        summary="Short summary"
    )

    assert "id_1" in result
    assert "Short summary" in result
    assert memory.size() == 1

    # Test retrieve
    retrieved = memory.retrieve(["id_1"])
    assert "Full evidence content here" in retrieved
    assert "id='id_1'" in retrieved

    # Test retrieve non-existent ID
    retrieved_error = memory.retrieve(["id_999"])
    assert "not found" in retrieved_error

    # Test get_all_ids
    ids = memory.get_all_ids()
    assert ids == ["id_1"]

    # Test clear
    memory.clear()
    assert memory.size() == 0


def test_retrieve_tool():
    """Test RetrieveTool."""
    memory = MemoryBank()
    memory.add_evidence("Content 1", "Summary 1")
    memory.add_evidence("Content 2", "Summary 2")

    tool = RetrieveTool(memory)

    # Test tool properties
    assert tool.name == "retrieve"
    assert "citation_ids" in tool.parameters["properties"]

    # Test call method
    result = tool.call({"citation_ids": ["id_1", "id_2"]})
    assert "Content 1" in result
    assert "Content 2" in result


def test_planner_parse_output():
    """Test Planner's output parsing."""
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.1}
    }

    memory = MemoryBank()
    # Mock OpenAI client to avoid API key requirement
    with pytest.MonkeyPatch().context() as m:
        m.setenv("OPENAI_API_KEY", "test-key")
        m.setenv("OPENAI_BASE_URL", "http://test")
        planner = WebWeaverPlanner(llm_config, memory)

        # Test tool_call parsing
        output1 = """
<think>I need to search for information</think>
<tool_call>
{"name": "search", "arguments": {"query": ["test query"]}}
</tool_call>
"""
        parsed1 = planner.parse_output(output1)
        assert parsed1["action_type"] == "tool_call"
        assert "search" in parsed1["action_content"]
        assert "I need to search" in parsed1["think"]

        # Test write_outline parsing
        output2 = """
<think>Now I'll create the outline</think>
<write_outline>
1. Introduction <citation>id_1</citation>
2. Methods <citation>id_2</citation>
</write_outline>
"""
        parsed2 = planner.parse_output(output2)
        assert parsed2["action_type"] == "write_outline"
        assert "Introduction" in parsed2["action_content"]

        # Test terminate parsing
        output3 = """
<think>The outline is complete</think>
<terminate>
"""
        parsed3 = planner.parse_output(output3)
        assert parsed3["action_type"] == "terminate"


def test_writer_parse_output():
    """Test Writer's output parsing."""
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.1}
    }

    memory = MemoryBank()
    # Mock OpenAI client to avoid API key requirement
    with pytest.MonkeyPatch().context() as m:
        m.setenv("OPENAI_API_KEY", "test-key")
        m.setenv("OPENAI_BASE_URL", "http://test")
        writer = WebWeaverWriter(llm_config, memory)

        # Test retrieve parsing
        output1 = """
<think>I need to retrieve evidence</think>
<tool_call>
{"name": "retrieve", "arguments": {"citation_ids": ["id_1"]}}
</tool_call>
"""
        parsed1 = writer.parse_output(output1)
        assert parsed1["action_type"] == "tool_call"
        assert "retrieve" in parsed1["action_content"]

        # Test write parsing
        output2 = """
<think>Now I'll write the section</think>
<write>
## Introduction

This is the introduction [cite:id_1]. More text here [cite:id_2].
</write>
"""
        parsed2 = writer.parse_output(output2)
        assert parsed2["action_type"] == "write"
        assert "Introduction" in parsed2["action_content"]
        assert "[cite:id_1]" in parsed2["action_content"]


def test_webweaver_agent_initialization():
    """Test WebWeaverAgent initialization."""
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.1}
    }

    # Mock OpenAI client to avoid API key requirement
    with pytest.MonkeyPatch().context() as m:
        m.setenv("OPENAI_API_KEY", "test-key")
        m.setenv("OPENAI_BASE_URL", "http://test")
        agent = WebWeaverAgent(llm_config)

        assert agent.memory_bank is not None
        assert agent.planner is not None
        assert agent.writer is not None
        assert agent.memory_bank == agent.planner.memory_bank
        assert agent.memory_bank == agent.writer.memory_bank


if __name__ == "__main__":
    test_memory_bank_basic()

    test_retrieve_tool()

    test_planner_parse_output()

    test_writer_parse_output()

    test_webweaver_agent_initialization()
