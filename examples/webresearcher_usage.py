#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Basic usage examples for WebResearcher

This script demonstrates the basic usage of WebResearcher
for answering research questions, including both factual and open-ended questions.

New features:
- Supports both <answer> and <terminate> termination signals
- Better handling of open-ended questions (e.g., "气候变暖如何治理")
"""
import asyncio
import os
from dotenv import load_dotenv

import sys
sys.path.append("..")

load_dotenv()
from webresearcher import WebResearcherAgent
from webresearcher import log


def print_result(result, title="Research Result"):
    """Helper function to print research results in a formatted way"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(f"\n📝 Question: {result['question']}")
    print(f"\n✅ Final Answer:")
    print(f"{'-'*80}")
    print(result['prediction'])
    print(f"{'-'*80}")
    print(f"\n📊 Termination Reason: {result['termination']}")
    if result.get('report') and result['report'] != result['prediction']:
        print(f"\n📋 Research Report (Full):")
        print(f"{'-'*80}")
        print(result['report'])
        print(f"{'-'*80}")


async def example_basic_research():
    """Example 1: Factual research question with specific answer"""
    print("\n" + "="*80)
    print("Example 1: Factual Research Question")
    print("="*80)
    print("This example demonstrates a factual question that requires")
    print("web search and Python code execution.\n")
    
    # Configure LLM
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            "temperature": 0.6,
        }
    }
    
    # Create agent
    agent = WebResearcherAgent(
        llm_config=llm_config,
        function_list=["search", "google_scholar", "python"]
    )
    
    print(f"Model: {agent.model}")
    print(f"Base URL: {os.getenv('OPENAI_BASE_URL', 'default')}")
    print(f"Log Level: {log.LOG_LEVEL}\n")
    
    # Run research - factual question
    question = "刘翔破纪录时候是多少岁?代码计算下。"
    print(f"🔍 Researching: {question}\n")
    result = await agent.run(question)
    
    print_result(result, "Example 1 Result")


async def example_open_ended_question():
    """Example 2: Open-ended research question (demonstrates <terminate> support)"""
    print("\n" + "="*80)
    print("Example 2: Open-Ended Research Question")
    print("="*80)
    print("This example demonstrates handling of open-ended questions.")
    print("The agent will use <terminate> when the report is complete,\n"
          "even if no explicit <answer> tag is generated.\n")
    
    # Configure LLM
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            "temperature": 0.6,
        }
    }
    
    # Create agent
    agent = WebResearcherAgent(
        llm_config=llm_config,
        function_list=["search"]
    )
    
    # Run research - open-ended question
    question = "气候变暖如何治理？"
    print(f"🔍 Researching: {question}\n")
    result = await agent.run(question)
    
    print_result(result, "Example 2 Result")
    
    # Show termination type analysis
    termination_type = result['termination']
    if 'terminate' in termination_type.lower():
        print("\n💡 Note: This query used <terminate> signal, demonstrating")
        print("   the improved handling of open-ended questions.")


async def example_tts_mode():
    """Example: Using Test-Time Scaling for higher accuracy"""
    print("\n" + "="*80)
    print("Example 3: Test-Time Scaling (TTS) Mode")
    print("="*80)
    print("⚠️  Warning: This will use 3-5x more tokens!\n")
    
    from webresearcher import TestTimeScalingAgent
    
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    
    # Create TTS agent
    agent = TestTimeScalingAgent(
        llm_config=llm_config,
        function_list=["search", "google_scholar"]
    )
    
    question = "Who won the Nobel Prize in Physics in 2024 and what was their contribution?"
    
    # Run with 3 parallel agents
    result = await agent.run(
        question=question,
        num_parallel_agents=3
    )
    
    print(f"\nQuestion: {question}")
    print(f"Final Answer (synthesized from 3 agents): {result['final_synthesized_answer']}")
    print(f"\nIndividual Agent Answers:")
    for i, run in enumerate(result['parallel_runs'], 1):
        print(f"  Agent {i}: {run.get('prediction', 'N/A')[:100]}...")


async def main():
    """Run all examples"""
    # Example 1: Basic factual research
    await example_basic_research()

    # Example 2: Open-ended research question (new feature demonstration)
    await example_open_ended_question()

    # Example 3: TTS mode (expensive - uncomment to use)
    # await example_tts_mode()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("WebResearcher Usage Examples")
    print("="*80)
    print("Demonstrating the improved termination handling with <answer> and <terminate>")
    print("="*80)
    asyncio.run(main())

