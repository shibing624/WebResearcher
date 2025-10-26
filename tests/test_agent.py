# -*- coding: utf-8 -*-
"""
Tests for agent module
"""
import pytest
from webresearcher.agent import WebResearcherAgent, ResearchRound


def test_research_round_init():
    """Test ResearchRound initialization"""
    question = "Test question"
    round = ResearchRound(question)
    
    assert round.question == question
    assert round.prev_report == "无"
    assert round.last_tool_res is None
    assert round.pending_tool_res is None


def test_research_round_get_context():
    """Test context generation"""
    round = ResearchRound("Test question")
    context = round.get_context("System prompt")
    
    assert len(context) >= 3
    assert context[0]["role"] == "system"
    assert context[1]["role"] == "user"
    assert "Test question" in context[1]["content"]


def test_research_round_set_pending_data():
    """Test setting pending data"""
    round = ResearchRound("Test")
    round.set_pending_data("think content", "tool result")
    
    assert round.pending_think == "think content"
    assert round.pending_tool_res == "tool result"


def test_agent_parse_output_answer():
    """Test parsing answer output"""
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    agent = WebResearcherAgent(llm_config=llm_config)
    
    text = "<think>Reasoning here</think>\n<answer>Final answer</answer>"
    parsed = agent.parse_output(text)
    
    assert parsed["think"] == "Reasoning here"
    assert parsed["answer"] == "Final answer"
    assert parsed["tool_call"] is None


def test_agent_parse_output_tool_call():
    """Test parsing tool call output"""
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    agent = WebResearcherAgent(llm_config=llm_config)
    
    text = '<think>Need to search</think>\n<tool_call>{"name": "search", "arguments": {"query": "test"}}</tool_call>'
    parsed = agent.parse_output(text)
    
    assert parsed["think"] == "Need to search"
    assert parsed["tool_call"] is not None
    assert "search" in parsed["tool_call"]
    assert parsed["answer"] is None


def test_agent_parse_output_nested_answer():
    """Test parsing nested answer (answer inside think)"""
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    agent = WebResearcherAgent(llm_config=llm_config)
    
    # Case where answer appears after think
    text = "<think>Reasoning</think>\n<answer>Final answer</answer>"
    parsed = agent.parse_output(text)
    
    assert parsed["answer"] == "Final answer"
    assert parsed["think"] == "Reasoning"


def test_model_supports_thinking():
    """Test model thinking support detection"""
    # Test GPT models (should not support thinking)
    gpt_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    gpt_agent = WebResearcherAgent(llm_config=gpt_config)
    assert not gpt_agent._model_supports_thinking()
    
    # Test DeepSeek-R1 models (should support thinking)
    deepseek_config = {
        "model": "deepseek-r1",
        "generate_cfg": {"temperature": 0.6}
    }
    deepseek_agent = WebResearcherAgent(llm_config=deepseek_config)
    assert deepseek_agent._model_supports_thinking()
    