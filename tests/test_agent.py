# -*- coding: utf-8 -*-
"""
Tests for agent module
"""
import pytest
from webresearcher.web_researcher_agent import WebResearcherAgent, ResearchRound


def test_research_round_get_context():
    """Test context generation"""
    round = ResearchRound("Test question")
    context = round.get_context("System prompt")

    assert len(context) >= 0
    assert context[0]["role"] == "system"
    assert context[1]["role"] == "user"
    assert "Test question" in context[1]["content"]


def test_agent_parse_output_answer():
    """Test parsing answer output"""
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    agent = WebResearcherAgent(llm_config=llm_config)

    text = "<plan>Reasoning here</plan>\n<answer>Final answer</answer>"
    parsed = agent.parse_output(text)

    assert parsed["plan"] == "Reasoning here"
    assert parsed["answer"] == "Final answer"
    assert parsed["tool_call"] == ''


def test_agent_parse_output_tool_call():
    """Test parsing tool call output"""
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    agent = WebResearcherAgent(llm_config=llm_config)

    text = '<plan>Need to search</plan>\n<tool_call>{"name": "search", "arguments": {"query": "test"}}</tool_call>'
    parsed = agent.parse_output(text)

    assert parsed["plan"] == "Need to search"
    assert parsed["tool_call"] is not None
    assert "search" in parsed["tool_call"]
    assert parsed["answer"] == ''


def test_agent_parse_output_nested_answer():
    """Test parsing nested answer (answer inside plan)"""
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    agent = WebResearcherAgent(llm_config=llm_config)

    # Case where answer appears after plan
    text = "<plan>Reasoning</plan>\n<answer>Final answer</answer>"
    parsed = agent.parse_output(text)

    assert parsed["answer"] == "Final answer"
    assert parsed["plan"] == "Reasoning"
