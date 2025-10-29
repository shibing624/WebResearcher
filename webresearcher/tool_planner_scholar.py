# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Planner-specific Scholar Tool with Memory Bank integration for WebWeaver
"""
import json5
from typing import Dict
from webresearcher.base import BaseTool
from webresearcher.tool_scholar import Scholar
from webresearcher.tool_memory import MemoryBank
from webresearcher.log import logger


class PlannerScholarTool(BaseTool):
    """
    Planner Agent's scholar search tool that integrates with Memory Bank.
    
    This tool:
    1. Performs academic search using the base Scholar tool
    2. Extracts paper information as evidence
    3. Stores evidence in Memory Bank
    4. Returns citation IDs and summaries to Planner
    """

    def __init__(self, memory_bank: MemoryBank):
        """
        Initialize Planner scholar tool with memory bank.
        
        Args:
            memory_bank: The shared MemoryBank instance
        """
        self.memory_bank = memory_bank
        self.base_scholar = Scholar()
        self.name = "google_scholar"
        self.description = "Searches academic papers using Google Scholar, extracts evidence from results, and saves it to the memory bank with citation IDs."
        self.parameters = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of academic search query strings."
                },
            },
            "required": ["query"]
        }

    def call(self, params: Dict, **kwargs) -> str:
        """
        Execute scholar search and store results in memory bank.
        
        Args:
            params: Dictionary with 'query' key (can be string or list)
            **kwargs: Additional arguments
            
        Returns:
            Formatted observations with citation IDs and summaries
        """
        query = params.get('query', [])
        if isinstance(query, str):
            query = [query]
        
        if not query:
            return "Error: 'query' parameter is required and cannot be empty."

        logger.debug(f"[PlannerScholarTool] Searching for: {query}")

        # Use base scholar tool to get results
        scholar_results_str = self.base_scholar.call({"query": query})
        
        # Parse scholar results to extract evidence
        observations = []
        
        # Split by query separators if multiple queries
        result_sections = scholar_results_str.split("\n=======\n") if "\n=======\n" in scholar_results_str else [scholar_results_str]
        
        for section in result_sections:
            # Extract individual paper results
            # Format: "1. [Title](URL)\nAuthors: ...\nAbstract: ..."
            lines = section.split("\n")
            
            current_paper = {}
            for i, line in enumerate(lines):
                # Look for numbered results like "1. [Title](URL)"
                if line.strip() and line[0].isdigit() and ". [" in line:
                    # Extract title and URL
                    try:
                        # Parse markdown link format: [Title](URL)
                        title_start = line.find("[") + 1
                        title_end = line.find("](")
                        url_start = title_end + 2
                        url_end = line.find(")", url_start)
                        
                        if title_end > title_start and url_end > url_start:
                            title = line[title_start:title_end]
                            url = line[url_start:url_end]
                            
                            # Collect following lines as paper content
                            content_lines = []
                            for j in range(i + 1, min(i + 15, len(lines))):
                                next_line = lines[j].strip()
                                # Stop if we hit the next numbered result
                                if next_line and next_line[0].isdigit() and ". [" in next_line:
                                    break
                                if next_line:
                                    content_lines.append(next_line)
                            
                            content = " ".join(content_lines).strip()
                            
                            if content:  # Only add if we have actual content
                                # Create full evidence content
                                full_content = f"Title: {title}\nURL: {url}\nContent: {content}"
                                summary = f"[{title}] {content[:200]}..." if len(content) > 200 else f"[{title}] {content}"
                                
                                # Add to memory bank and get citation ID
                                obs = self.memory_bank.add_evidence(content=full_content, summary=summary)
                                observations.append(obs)
                    except Exception as e:
                        logger.warning(f"[PlannerScholarTool] Failed to parse paper line: {line}, error: {e}")
                        continue
        
        if not observations:
            # If parsing failed, treat entire result as single evidence
            summary = scholar_results_str[:300] + "..." if len(scholar_results_str) > 300 else scholar_results_str
            obs = self.memory_bank.add_evidence(content=scholar_results_str, summary=summary)
            observations.append(obs)
        
        result = "\n".join(observations)
        logger.debug(f"[PlannerScholarTool] Added {len(observations)} evidence chunks to memory bank")
        return result
