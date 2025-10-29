# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Planner-specific File Parser Tool with Memory Bank integration for WebWeaver
"""
import json5
from typing import Dict
from webresearcher.base import BaseTool
from webresearcher.tool_file import FileParser
from webresearcher.tool_memory import MemoryBank
from webresearcher.log import logger


class PlannerFileTool(BaseTool):
    """
    Planner Agent's file parser tool that integrates with Memory Bank.
    
    This tool:
    1. Parses files using the base FileParser tool
    2. Extracts file content as evidence
    3. Stores evidence in Memory Bank
    4. Returns citation IDs and summaries to Planner
    """

    def __init__(self, memory_bank: MemoryBank):
        """
        Initialize Planner file tool with memory bank.
        
        Args:
            memory_bank: The shared MemoryBank instance
        """
        self.memory_bank = memory_bank
        self.base_file_parser = FileParser()
        self.name = "parse_file"
        self.description = "Parses files (PDF, DOCX, etc.) and saves content to the memory bank with citation IDs."
        self.parameters = {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of file names to parse."
                }
            },
            "required": ["files"]
        }

    def call(self, params: Dict, **kwargs) -> str:
        """
        Execute file parsing and store results in memory bank.
        
        Args:
            params: Dictionary with 'files' key
            **kwargs: Additional arguments
            
        Returns:
            Formatted observations with citation IDs and summaries
        """
        files = params.get('files', [])
        
        if not files:
            return "Error: 'files' parameter is required and cannot be empty."

        logger.debug(f"[PlannerFileTool] Parsing files: {files}")

        # Use base file parser tool to parse files
        file_results_str = self.base_file_parser.call({"files": files})
        
        # Store file content as evidence
        observations = []
        
        if file_results_str and file_results_str.strip():
            # Create full evidence content
            full_content = f"Files: {', '.join(files)}\nContent: {file_results_str}"
            summary = f"File content from {len(files)} file(s): {file_results_str[:200]}..." if len(file_results_str) > 200 else f"File content from {len(files)} file(s): {file_results_str}"
            
            # Add to memory bank and get citation ID
            obs = self.memory_bank.add_evidence(content=full_content, summary=summary)
            observations.append(obs)
        else:
            # If no content, still add a placeholder
            full_content = f"Files: {', '.join(files)}\nContent: No content extracted"
            summary = f"No content found in {len(files)} file(s)"
            obs = self.memory_bank.add_evidence(content=full_content, summary=summary)
            observations.append(obs)
        
        result = "\n".join(observations)
        logger.debug(f"[PlannerFileTool] Added {len(observations)} evidence chunks to memory bank")
        return result
