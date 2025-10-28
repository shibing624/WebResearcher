# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Memory Bank and Retrieve Tool for WebWeaver
"""
from typing import Dict, List
from webresearcher.base import BaseTool
from webresearcher.log import logger


class MemoryBank:
    """
    Memory Bank for storing evidence found by Planner Agent.
    
    Based on WebWeaver paper Section 3.1.2 and Section 3.2.
    The Planner writes evidence (add_evidence), and the Writer retrieves it (retrieve).
    """

    def __init__(self):
        """Initialize empty memory bank."""
        # Structure: { "id_1": "evidence content...", "id_2": "summary..." }
        self.evidence: Dict[str, str] = {}
        self.id_counter = 0

    def add_evidence(self, content: str, summary: str) -> str:
        """
        Add new evidence to the memory bank and return a unique citation ID.
        
        Args:
            content: Full detailed evidence content
            summary: Query-relevant summary of the evidence
            
        Returns:
            Formatted observation string with ID and summary
        """
        self.id_counter += 1
        citation_id = f"id_{self.id_counter}"

        # Store detailed content for Writer to retrieve later
        self.evidence[citation_id] = content

        # Return ID and summary as observation for Planner
        # This follows the format from WebWeaver paper Appendix B.2
        return f"<evidence_chunk>\n<id>{citation_id}</id>\n<summary>{summary}</summary>\n</evidence_chunk>"

    def retrieve(self, citation_ids: List[str]) -> str:
        """
        Retrieve evidence from memory bank using citation IDs.
        
        This is the core tool for Writer Agent (Section 3.3).
        
        Args:
            citation_ids: List of citation IDs to retrieve
            
        Returns:
            Retrieved evidence content formatted with IDs
        """
        retrieved_content = []
        for cid in citation_ids:
            if cid in self.evidence:
                retrieved_content.append(f"<evidence id='{cid}'>\n{self.evidence[cid]}\n</evidence>")
            else:
                retrieved_content.append(f"<error>Citation ID '{cid}' not found in Memory Bank.</error>")
                logger.warning(f"Citation ID '{cid}' not found in Memory Bank")

        if not retrieved_content:
            return "No evidence found for the provided citation IDs."

        return "\n\n".join(retrieved_content)

    def get_all_ids(self) -> List[str]:
        """Get all citation IDs in the memory bank."""
        return list(self.evidence.keys())

    def size(self) -> int:
        """Get the number of evidence items in memory bank."""
        return len(self.evidence)

    def clear(self):
        """Clear all evidence from memory bank."""
        self.evidence.clear()
        self.id_counter = 0


class RetrieveTool(BaseTool):
    """
    Writer Agent's exclusive tool for retrieving evidence from Memory Bank.
    
    Based on WebWeaver paper Section 3.3 (lines 150-151, 275).
    """

    def __init__(self, memory_bank: MemoryBank):
        """
        Initialize retrieve tool with memory bank reference.
        
        Args:
            memory_bank: The shared MemoryBank instance
        """
        self.memory_bank = memory_bank
        self.name = "retrieve"
        self.description = "Retrieves specific evidence chunks from the Memory Bank using their citation IDs. Use this to get the content needed to write a specific section."
        self.parameters = {
            "type": "object",
            "properties": {
                "citation_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of citation IDs (e.g., ['id_1', 'id_5']) to retrieve from the Memory Bank."
                }
            },
            "required": ["citation_ids"]
        }

    def call(self, params: Dict, **kwargs) -> str:
        """
        Execute retrieve operation.
        
        Args:
            params: Dictionary with 'citation_ids' key
            **kwargs: Additional arguments (unused)
            
        Returns:
            Retrieved evidence content
        """
        citation_ids = params.get('citation_ids', [])
        logger.debug(f"[RetrieveTool] Retrieving IDs: {citation_ids}")
        return self.memory_bank.retrieve(citation_ids)

