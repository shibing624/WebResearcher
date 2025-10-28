#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Custom Agent Example

Demonstrates how to create custom tools and integrate them
with WebResearcher.
"""
import asyncio
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

from webresearcher import WebResearcherAgent, BaseTool


class WikipediaTool(BaseTool):
    """
    Custom tool: Wikipedia search
    
    This is an example of how to create your own tools.
    """
    name = "wikipedia"
    description = "Search Wikipedia for information. Provide a search query to get a summary."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Wikipedia search query"
            }
        },
        "required": ["query"]
    }
    
    def call(self, params: Dict, **kwargs) -> str:
        """
        Execute Wikipedia search.
        
        Args:
            params: Dict with 'query' key
            
        Returns:
            Wikipedia search result
        """
        import requests
        
        query = params.get('query', '')
        if not query:
            return "Error: No query provided"
        
        try:
            # Wikipedia API
            url = "https://en.wikipedia.org/w/api.php"
            params_api = {
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": query
            }
            
            response = requests.get(url, params=params_api, timeout=10)
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return f"No Wikipedia results found for '{query}'"
            
            # Get first page
            page = list(pages.values())[0]
            
            if 'extract' in page:
                title = page.get('title', query)
                extract = page['extract'][:1000]  # Limit length
                return f"# Wikipedia: {title}\n\n{extract}"
            else:
                return f"No Wikipedia article found for '{query}'"
                
        except Exception as e:
            return f"Wikipedia search error: {str(e)}"


async def example_custom_tool():
    """Example: Using custom Wikipedia tool"""
    print("="*80)
    print("Custom Tool Example: Wikipedia Integration")
    print("="*80)
    
    # Configure LLM
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    
    # Import standard tools
    from webresearcher.web_researcher_agent import TOOL_MAP
    
    # Register custom tool
    wiki_tool = WikipediaTool()
    TOOL_MAP['wikipedia'] = wiki_tool
    
    # Create agent with custom tool
    agent = WebResearcherAgent(
        llm_config=llm_config,
        function_list=["search", "wikipedia"]  # Use both standard and custom tools
    )
    
    # Run research
    question = "Who invented the World Wide Web and when?"
    result = await agent.run(question)
    
    print(f"\nQuestion: {question}")
    print(f"Answer: {result['prediction']}")
    print(f"\nNote: This used both Google Search and Wikipedia!")


class CalculatorTool(BaseTool):
    """Simple calculator tool example"""
    name = "calculator"
    description = "Perform basic arithmetic calculations. Supports +, -, *, /, ** (power)"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 ** 3')"
            }
        },
        "required": ["expression"]
    }
    
    def call(self, params: Dict, **kwargs) -> str:
        """Execute calculation"""
        expression = params.get('expression', '')
        
        try:
            # Safely evaluate (restrict to basic math)
            allowed_names = {"__builtins__": {}}
            result = eval(expression, allowed_names)
            return f"Result: {expression} = {result}"
        except Exception as e:
            return f"Calculation error: {str(e)}"


async def example_multi_custom_tools():
    """Example: Using multiple custom tools"""
    print("\n" + "="*80)
    print("Multiple Custom Tools Example")
    print("="*80)
    
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {"temperature": 0.6}
    }
    
    from webresearcher.web_researcher_agent import TOOL_MAP
    
    # Register multiple custom tools
    TOOL_MAP['wikipedia'] = WikipediaTool()
    TOOL_MAP['calculator'] = CalculatorTool()
    
    agent = WebResearcherAgent(
        llm_config=llm_config,
        function_list=["search", "wikipedia", "calculator"]
    )
    
    question = "What is the population of Tokyo in millions, and what is 10% of that number?"
    result = await agent.run(question)
    
    print(f"\nQuestion: {question}")
    print(f"Answer: {result['prediction']}")


async def main():
    """Run custom tool examples"""
    # Example 1: Single custom tool
    await example_custom_tool()
    
    # Example 2: Multiple custom tools
    # await example_multi_custom_tools()


if __name__ == "__main__":
    asyncio.run(main())

