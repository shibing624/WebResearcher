#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Basic usage examples for WebResearcher

This script demonstrates the basic usage of WebResearcher
for answering research questions.
"""
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from webresearcher import MultiTurnReactAgent


async def example_basic_research():
    """Example: Basic research question"""
    print("="*80)
    print("Example 1: Basic Research")
    print("="*80)
    
    # Configure LLM
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            "temperature": 0.6,
            "top_p": 0.95,
            "presence_penalty": 1.1,
        }
    }
    
    # Create agent
    agent = MultiTurnReactAgent(
        llm_config=llm_config,
        function_list=["search", "google_scholar", "PythonInterpreter"]
    )
    
    # Run research
    question = "刘翔破纪录时候是多少岁?"
    result = await agent.run(question)
    
    # Print results
    print(f"\nQuestion: {result['question']}")
    print(f"Answer: {result['prediction']}")
    print(f"\nResearch Report:\n{result['report']}")
    print(f"\nTermination: {result['termination']}")


async def example_custom_tools():
    """Example: Research with custom tool selection"""
    print("\n" + "="*80)
    print("Example 2: Custom Tool Selection")
    print("="*80)
    
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    
    # Only use search and scholar (no Python)
    agent = MultiTurnReactAgent(
        llm_config=llm_config,
        function_list=["search", "google_scholar"]
    )
    
    question = "What are the latest breakthroughs in quantum computing?"
    result = await agent.run(question)
    
    print(f"\nQuestion: {question}")
    print(f"Answer: {result['prediction']}")


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
    # Example 1: Basic usage
    await example_basic_research()
    
    # Example 2: Custom tools
    # await example_custom_tools()
    
    # Example 3: TTS mode (expensive!)
    # await example_tts_mode()


if __name__ == "__main__":
    asyncio.run(main())

