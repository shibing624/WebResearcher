# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Example usage of ReactAgent - MultiTurn ReAct-style Agent
"""
import asyncio
from dotenv import load_dotenv

import sys
sys.path.append("..")
load_dotenv()
from webresearcher import ReactAgent, logger, set_log_level
from webresearcher.base import BaseTool
from webresearcher.prompt import TOOL_DESCRIPTIONS
from webresearcher.react_agent import TOOL_MAP


set_log_level("DEBUG")


def print_result(result, title="ReactAgent Result"):
    """Helper function to print results in a formatted way"""
    print("\n" + "="*80)
    print(title)
    print("="*80)
    print(f"\n📝 Question: {result['question']}")
    print(f"\n✅ Final Answer:")
    print("-"*80)
    print(result['prediction'])
    print("-"*80)
    print(f"\n📊 Termination Reason: {result['termination']}")
    if result.get('trajectory'):
        print(f"\n📋 Total Messages in Trajectory: {len(result['trajectory'])}")


async def example_react_with_tools():
    """ReactAgent with multiple tools including Python"""
    print("\n" + "="*80)
    print("ReactAgent - Question Requiring Multiple Tools")
    print("="*80)
    print("This example demonstrates ReactAgent using search and Python tools.\n")
    
    # Configure LLM
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            "temperature": 0.6,
            "top_p": 0.95,
        },
        "llm_timeout": 300.0,
    }
    
    # Initialize ReactAgent with more tools
    agent = ReactAgent(
        llm_config=llm_config,
        function_list=["search", "python", "visit"]
    )
    
    # Define question that might need calculation
    question = "What is the population of Paris in 2024? Calculate the square root of that number."
    logger.info(f"Question: {question}")
    
    # Run agent
    result = await agent.run(question)
    
    # Display results
    print_result(result, "example_react_with_tools Result")


async def example_react_open_ended():
    """ReactAgent handling open-ended questions"""
    print("\n" + "="*80)
    print("ReactAgent - Open-Ended Question")
    print("="*80)
    print("This example demonstrates ReactAgent handling an open-ended question\n"
          "that may use <terminate> instead of <answer>.\n")
    
    # Configure LLM
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            "temperature": 0.6,
            "top_p": 0.95,
        },
        "llm_timeout": 300.0,
    }
    
    # Initialize ReactAgent
    agent = ReactAgent(
        llm_config=llm_config,
        function_list=["search", "google_scholar", "visit"]
    )
    
    # Define open-ended question
    question = "What are the main causes of climate change?"
    logger.info(f"Question: {question}")
    
    # Run agent
    result = await agent.run(question)
    
    # Display results
    print_result(result, "example_react_open_ended Result")
    
    # Show termination type
    if 'terminate' in result['termination'].lower():
        print("\n💡 Note: This query used <terminate> signal for completion.")


async def example_react_with_custom_config():
    """ReactAgent with custom API configuration"""
    print("\n" + "="*80)
    print("ReactAgent - Custom API Configuration")
    print("="*80)
    print("This example demonstrates ReactAgent using custom API settings\n"
          "(e.g., for local vLLM or other OpenAI-compatible endpoints).\n")
    
    # Configure LLM with custom base_url (example for local vLLM)
    llm_config = {
        "model": "gpt-4o",  # or your local model name
        "openai_base_url": "http://127.0.0.1:8000/v1",  # Example local endpoint
        "openai_api_key": "EMPTY",  # May not be needed for local
        "generate_cfg": {
            "temperature": 0.6,
            "top_p": 0.95,
        },
        "llm_timeout": 600.0,  # Longer timeout for local models
    }
    
    # Initialize ReactAgent with custom config
    agent = ReactAgent(
        llm_config=llm_config,
        function_list=["search", "visit"]
    )
    
    # Define question
    question = "Who won the Nobel Prize in Physics in 2023?"
    logger.info(f"Question: {question}")
    logger.info(f"Using base_url: {llm_config['openai_base_url']}")
    
    # Run agent
    result = await agent.run(question)
    
    # Display results
    print_result(result, "example_react_with_custom_config Result")


class EchoTool(BaseTool):
    """A simple custom tool that transforms text."""
    name = "echo"
    description = "Transform text with a simple mode: upper/lower/reverse."
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text to transform."},
            "mode": {
                "type": "string",
                "enum": ["upper", "lower", "reverse"],
                "description": "Transformation mode",
            },
        },
        "required": ["text", "mode"],
    }

    def call(self, params: dict, **kwargs) -> str:
        text = params.get("text", "")
        mode = params.get("mode", "upper")
        if mode == "upper":
            return text.upper()
        if mode == "lower":
            return text.lower()
        if mode == "reverse":
            return text[::-1]
        return text


async def example_react_custom_tool():
    """ReactAgent with a custom tool registered at runtime"""
    print("\n" + "="*80)
    print("ReactAgent - Custom Tool (Echo)")
    print("="*80)
    print("This example demonstrates registering a custom tool and updating the tool schema at runtime.\n")

    # Register custom tool into the runtime TOOL_MAP used by ReactAgent
    TOOL_MAP["echo"] = EchoTool()

    # Expose the tool definition to the LLM prompt builder
    TOOL_DESCRIPTIONS["echo"] = {
        "type": "function",
        "function": {
            "name": "echo",
            "description": "Transform text with mode upper/lower/reverse.",
            "parameters": EchoTool.parameters,
        },
    }

    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6, "top_p": 0.95},
        "llm_timeout": 300.0,
    }

    agent = ReactAgent(
        llm_config=llm_config,
        function_list=["echo"]
    )

    # Encourage the agent to call the custom tool explicitly
    question = (
        "Please transform the following text using the 'echo' tool with mode=upper, then briefly explain: "
        "'Hello world from WebResearcher'."
    )
    logger.info(f"Question: {question}")

    result = await agent.run(question)
    print_result(result, "example_react_custom_tool Result")


async def main():
    """Run all ReactAgent examples"""
    print("\n" + "="*80)
    print("ReactAgent Usage Examples")
    print("="*80)
    print("Demonstrating MultiTurn ReAct-style agent with tool calling")
    print("="*80)

    # Example 1: Multiple tools
    await example_react_with_tools()
    
    # Example 2: Open-ended questions
    # await example_react_open_ended()
    
    # Example 3: Custom API config (uncomment if you have local endpoint)
    # await example_react_with_custom_config()

    # Example 4: Custom Tool (runtime registration)
    # await example_react_custom_tool()

if __name__ == "__main__":
    asyncio.run(main())