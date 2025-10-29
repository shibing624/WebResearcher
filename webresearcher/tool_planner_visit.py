# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Planner-specific Visit Tool with Memory Bank integration for WebWeaver
"""
import json5
from typing import Dict
from webresearcher.base import BaseTool
from webresearcher.tool_visit import Visit
from webresearcher.tool_memory import MemoryBank
from webresearcher.log import logger


class PlannerVisitTool(BaseTool):
    """
    Planner Agent's visit tool that integrates with Memory Bank.
    
    This tool:
    1. Visits web pages using the base Visit tool
    2. Extracts content as evidence
    3. Stores evidence in Memory Bank
    4. Returns citation IDs and summaries to Planner
    """

    def __init__(self, memory_bank: MemoryBank):
        """
        Initialize Planner visit tool with memory bank.
        
        Args:
            memory_bank: The shared MemoryBank instance
        """
        self.memory_bank = memory_bank
        self.base_visit = Visit()
        self.name = "visit"
        self.description = "Visits web pages, extracts content, and saves it to the memory bank with citation IDs."
        self.parameters = {
            "type": "object",
            "properties": {
                "url": {
                    "type": ["string", "array"],
                    "items": {"type": "string"},
                    "description": "URL(s) to visit."
                },
                "goal": {
                    "type": "string",
                    "description": "Specific information goal for visiting the webpage(s)."
                }
            },
            "required": ["url", "goal"]
        }

    def call(self, params: Dict, **kwargs) -> str:
        """
        Execute visit and store results in memory bank.
        
        Args:
            params: Dictionary with 'url' and 'goal' keys
            **kwargs: Additional arguments
            
        Returns:
            Formatted observations with citation IDs and summaries
        """
        url = params.get('url', [])
        goal = params.get('goal', '')
        
        if not url:
            return "Error: 'url' parameter is required and cannot be empty."
        
        if isinstance(url, str):
            url = [url]

        logger.debug(f"[PlannerVisitTool] Visiting: {url}")

        # Use base visit tool to get results
        visit_results_str = self.base_visit.call({"url": url, "goal": goal})
        
        # Parse visit results to extract evidence
        observations = []
        
        # The visit tool returns structured content, we'll treat each URL result as evidence
        if visit_results_str and visit_results_str.strip():
            # Create full evidence content
            full_content = f"Goal: {goal}\nURLs: {', '.join(url)}\nContent: {visit_results_str}"
            summary = f"Web content for goal '{goal}': {visit_results_str[:200]}..." if len(visit_results_str) > 200 else f"Web content for goal '{goal}': {visit_results_str}"
            
            # Add to memory bank and get citation ID
            obs = self.memory_bank.add_evidence(content=full_content, summary=summary)
            observations.append(obs)
        else:
            # If no content, still add a placeholder
            full_content = f"Goal: {goal}\nURLs: {', '.join(url)}\nContent: No content extracted"
            summary = f"No content found for goal '{goal}'"
            obs = self.memory_bank.add_evidence(content=full_content, summary=summary)
            observations.append(obs)
        
        result = "\n".join(observations)
        logger.debug(f"[PlannerVisitTool] Added {len(observations)} evidence chunks to memory bank")
        return result
