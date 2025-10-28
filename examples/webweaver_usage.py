# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Example usage of WebWeaver Agent
"""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from webresearcher import WebWeaverAgent, logger, set_log_level


set_log_level("DEBUG")


async def basic_webweaver_example():
    """Basic WebWeaver agent usage."""
    # Configure LLM
    llm_config = {
        "model": "gpt-4o",  # Recommended: GPT-4, Claude 3, or other capable models
        "generate_cfg": {
            "temperature": 0.1,  # Low temperature for factual research
            "top_p": 0.95,
            "max_tokens": 10000,
        },
        "llm_timeout": 300.0,
    }
    
    # Initialize WebWeaver agent
    agent = WebWeaverAgent(llm_config=llm_config)
    
    # Define research question
    question = "刘翔破纪录时候是多少岁?"
    logger.info(f"Starting WebWeaver research...")
    logger.info(f"Question: {question}")
    
    # Run the dual-agent workflow
    result = await agent.run(question)
    
    # Display results
    print("\n" + "="*80)
    print("RESEARCH COMPLETE")
    print("="*80)
    
    if "error" in result:
        print(f"\nError: {result['error']}")
    else:
        print(f"\nTotal Time: {result['total_time_seconds']:.2f} seconds")
        print(f"Memory Bank Size: {result['memory_bank_size']} evidence chunks")
        
        print("\n" + "-"*80)
        print("FINAL OUTLINE")
        print("-"*80)
        print(result['final_outline'])
        
        print("\n" + "-"*80)
        print("FINAL REPORT")
        print("-"*80)
        print(result['final_report'])



if __name__ == "__main__":
    asyncio.run(basic_webweaver_example())

