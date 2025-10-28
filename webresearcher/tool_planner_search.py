# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Planner-specific Search Tool with Memory Bank integration for WebWeaver
"""
import json5
from typing import Dict
from webresearcher.base import BaseTool
from webresearcher.tool_search import Search
from webresearcher.tool_memory import MemoryBank
from webresearcher.log import logger


class PlannerSearchTool(BaseTool):
    """
    Planner Agent's search tool that integrates with Memory Bank.
    
    This tool:
    1. Performs web search using the base Search tool
    2. Extracts snippets as evidence
    3. Stores evidence in Memory Bank
    4. Returns citation IDs and summaries to Planner
    
    Based on WebWeaver paper Section 3.2 (lines 147-148, 253-259).
    """

    def __init__(self, memory_bank: MemoryBank):
        """
        Initialize Planner search tool with memory bank.
        
        Args:
            memory_bank: The shared MemoryBank instance
        """
        self.memory_bank = memory_bank
        self.base_search = Search()
        self.name = "search"
        self.description = "Searches the web for information, extracts evidence from results, and saves it to the memory bank with citation IDs."
        self.parameters = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of search query strings. Include multiple complementary search queries in a single call."
                },
            },
            "required": ["query"]
        }

    def call(self, params: Dict, **kwargs) -> str:
        """
        Execute search and store results in memory bank.
        
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

        logger.debug(f"[PlannerSearchTool] Searching for: {query}")

        # Use base search tool to get results
        search_results_str = self.base_search.call({"query": query})
        
        # Parse search results to extract evidence
        # The search_results_str contains formatted results with URLs, titles, and snippets
        observations = []
        
        # Split by query separators if multiple queries
        result_sections = search_results_str.split("\n=======\n") if "\n=======\n" in search_results_str else [search_results_str]
        
        for section in result_sections:
            # Extract individual search results
            # Format: "1. [Title](URL)\nDate published: ...\nSource: ...\nSnippet"
            lines = section.split("\n")
            
            current_result = {}
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
                            
                            # Collect following lines as snippet/content
                            snippet_lines = []
                            for j in range(i + 1, min(i + 10, len(lines))):
                                next_line = lines[j].strip()
                                # Stop if we hit the next numbered result
                                if next_line and next_line[0].isdigit() and ". [" in next_line:
                                    break
                                if next_line and not next_line.startswith("Date published:") and not next_line.startswith("Source:"):
                                    snippet_lines.append(next_line)
                            
                            snippet = " ".join(snippet_lines).strip()
                            
                            if snippet:  # Only add if we have actual content
                                # Create full evidence content
                                full_content = f"Title: {title}\nURL: {url}\nSnippet: {snippet}"
                                summary = f"[{title}] {snippet[:200]}..." if len(snippet) > 200 else f"[{title}] {snippet}"
                                
                                # Add to memory bank and get citation ID
                                obs = self.memory_bank.add_evidence(content=full_content, summary=summary)
                                observations.append(obs)
                    except Exception as e:
                        logger.warning(f"[PlannerSearchTool] Failed to parse result line: {line}, error: {e}")
                        continue
        
        if not observations:
            # If parsing failed, treat entire result as single evidence
            summary = search_results_str[:300] + "..." if len(search_results_str) > 300 else search_results_str
            obs = self.memory_bank.add_evidence(content=search_results_str, summary=summary)
            observations.append(obs)
        
        result = "\n".join(observations)
        logger.debug(f"[PlannerSearchTool] Added {len(observations)} evidence chunks to memory bank")
        return result

