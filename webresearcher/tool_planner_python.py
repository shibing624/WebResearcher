# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Planner-specific Python Tool with Memory Bank integration for WebWeaver
"""
import json5
from typing import Dict
from webresearcher.base import BaseTool
from webresearcher.tool_python import PythonInterpreter
from webresearcher.tool_memory import MemoryBank
from webresearcher.log import logger


class PlannerPythonTool(BaseTool):
    """
    Planner Agent's Python tool that integrates with Memory Bank.
    
    This tool:
    1. Executes Python code using the base PythonInterpreter tool
    2. Stores execution results as evidence
    3. Returns citation IDs and summaries to Planner
    """

    def __init__(self, memory_bank: MemoryBank):
        """
        Initialize Planner Python tool with memory bank.
        
        Args:
            memory_bank: The shared MemoryBank instance
        """
        self.memory_bank = memory_bank
        self.base_python = PythonInterpreter()
        self.name = "python"
        self.description = "Executes Python code and saves results to the memory bank with citation IDs."
        self.parameters = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute."
                }
            },
            "required": ["code"]
        }

    def call(self, params: Dict, **kwargs) -> str:
        """
        Execute Python code and store results in memory bank.
        
        Args:
            params: Dictionary with 'code' key
            **kwargs: Additional arguments
            
        Returns:
            Formatted observations with citation IDs and summaries
        """
        code = params.get('code', '')
        
        if not code:
            return "Error: 'code' parameter is required and cannot be empty."

        logger.debug(f"[PlannerPythonTool] Executing Python code")

        # Use base Python tool to execute code
        python_results_str = self.base_python.call({"code": code})
        
        # Store execution results as evidence
        observations = []
        
        if python_results_str and python_results_str.strip():
            # Create full evidence content
            full_content = f"Python Code:\n```python\n{code}\n```\n\nExecution Result:\n{python_results_str}"
            summary = f"Python execution result: {python_results_str[:200]}..." if len(python_results_str) > 200 else f"Python execution result: {python_results_str}"
            
            # Add to memory bank and get citation ID
            obs = self.memory_bank.add_evidence(content=full_content, summary=summary)
            observations.append(obs)
        else:
            # If no output, still add a placeholder
            full_content = f"Python Code:\n```python\n{code}\n```\n\nExecution Result: No output"
            summary = f"Python code executed with no output"
            obs = self.memory_bank.add_evidence(content=full_content, summary=summary)
            observations.append(obs)
        
        result = "\n".join(observations)
        logger.debug(f"[PlannerPythonTool] Added {len(observations)} evidence chunks to memory bank")
        return result
