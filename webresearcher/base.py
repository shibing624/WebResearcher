# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Base classes and utilities for WebResearcher
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum


# ============ Message Schema ============

class MessageRole(str, Enum):
    """Message role enum"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


# Define constants for backward compatibility
SYSTEM = "system"
USER = "user"
ASSISTANT = "assistant"
FUNCTION = "function"
DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."


@dataclass
class ContentItem:
    """Content item for multimodal messages"""
    type: str  # "text", "image_url", etc.
    text: Optional[str] = None
    image_url: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dict format"""
        result = {"type": self.type}
        if self.text:
            result["text"] = self.text
        if self.image_url:
            result["image_url"] = self.image_url
        return result


@dataclass
class Message:
    """
    Message format for LLM communication.
    """
    role: str
    content: Union[str, List[ContentItem]] = ""
    name: Optional[str] = None
    function_call: Optional[Dict] = None
    
    def __post_init__(self):
        """Validate role"""
        if self.role not in [SYSTEM, USER, ASSISTANT, FUNCTION]:
            # Allow it anyway for flexibility
            pass
    
    def to_dict(self) -> Dict:
        """Convert to OpenAI API format"""
        result = {"role": self.role}
        
        # Handle content
        if isinstance(self.content, list):
            result["content"] = [item.to_dict() if isinstance(item, ContentItem) else item 
                                for item in self.content]
        else:
            result["content"] = self.content
        
        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        """Create Message from dict"""
        return cls(
            role=data.get("role", USER),
            content=data.get("content", ""),
            name=data.get("name"),
            function_call=data.get("function_call")
        )


# ============ Tool Base Classes ============

class BaseTool(ABC):
    """
    Base class for all tools.
    """
    
    name: str = ""
    description: str = ""
    parameters: Any = None  # JSON Schema format
    
    @abstractmethod
    def call(self, params: Dict, **kwargs) -> str:
        """
        Execute the tool.
        
        Args:
            params: Tool parameters as a dictionary
            **kwargs: Additional keyword arguments
            
        Returns:
            Tool execution result as a string
        """
        raise NotImplementedError(f"Tool {self.name} must implement call() method")
    
    def get_function_definition(self) -> Dict:
        """
        Get tool definition in OpenAI Function Calling format.
        
        Returns:
            Function definition dict
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters or {
                "type": "object",
                "properties": {},
                "required": []
            }
        }


class BaseToolWithFileAccess(BaseTool):
    """
    Base class for tools that need file system access.
    """
    
    def __init__(self, file_root_path: str = "./files"):
        """
        Initialize tool with file root path.
        
        Args:
            file_root_path: Root directory for file operations
        """
        self.file_root_path = file_root_path
    
    @abstractmethod
    def call(self, params: Dict, file_root_path: Optional[str] = None, **kwargs) -> str:
        """
        Execute the tool with file access.
        
        Args:
            params: Tool parameters
            file_root_path: Override default file root path
            **kwargs: Additional arguments
            
        Returns:
            Tool execution result
        """
        raise NotImplementedError


# ============ Utility Functions ============

def extract_code(text: str, start_tag: str = "<code>", end_tag: str = "</code>") -> str:
    """
    Extract code block from text.
    
    Args:
        text: Text containing code block
        start_tag: Start tag for code block
        end_tag: End tag for code block
        
    Returns:
        Extracted code, or original text if no code block found
    """
    pattern = f"{re.escape(start_tag)}(.*?){re.escape(end_tag)}"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else text


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Count tokens in text using tiktoken.
    
    Args:
        text: Input text
        model: Model name for tokenizer
        
    Returns:
        Number of tokens
    """
    import tiktoken
    
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for unknown models
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(str(text)))


def get_tokenizer(model: str = "gpt-4o"):
    """
    Get tiktoken tokenizer for a model.
    
    Args:
        model: Model name
        
    Returns:
        Tiktoken encoding
    """
    import tiktoken
    
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


# For backward compatibility
tokenizer = get_tokenizer()


def build_text_completion_prompt(messages: List[Union[Message, Dict]], 
                                 allow_special: bool = False) -> str:
    """
    Build text completion prompt from messages (for token counting).
    
    Args:
        messages: List of Message objects or dicts
        allow_special: Whether to allow special tokens (unused, for compatibility)
        
    Returns:
        Concatenated prompt string
    """
    prompt_parts = []
    
    for msg in messages:
        if isinstance(msg, Message):
            role = msg.role
            content = msg.content
        elif isinstance(msg, dict):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
        else:
            continue
        
        # Handle content
        if isinstance(content, list):
            # Multimodal content - extract text parts
            text_parts = []
            for item in content:
                if isinstance(item, ContentItem) and item.text:
                    text_parts.append(item.text)
                elif isinstance(item, dict) and item.get("text"):
                    text_parts.append(item["text"])
            content = " ".join(text_parts)
        
        prompt_parts.append(f"{role}: {content}")
    
    return "\n".join(prompt_parts)


# ============ Settings / Constants ============

DEFAULT_WORKSPACE = "./workspace"
DEFAULT_MAX_INPUT_TOKENS = 32000


# ============ Storage (Simple Implementation) ============

class KeyNotExistsError(Exception):
    """Exception raised when key doesn't exist in storage"""
    pass


class Storage:
    """
    Simple in-memory storage.
    """
    
    def __init__(self, root_path: str = DEFAULT_WORKSPACE):
        """
        Initialize storage.
        
        Args:
            root_path: Root path for storage (for compatibility, not used in memory mode)
        """
        self.root_path = root_path
        self._data: Dict[str, Any] = {}
    
    def put(self, key: str, value: Any) -> None:
        """
        Store a value.
        
        Args:
            key: Storage key
            value: Value to store
        """
        self._data[key] = value
    
    def get(self, key: str) -> Any:
        """
        Retrieve a value.
        
        Args:
            key: Storage key
            
        Returns:
            Stored value
            
        Raises:
            KeyNotExistsError: If key doesn't exist
        """
        if key not in self._data:
            raise KeyNotExistsError(f"Key '{key}' not found in storage")
        return self._data[key]
    
    def has(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Storage key
            
        Returns:
            True if key exists
        """
        return key in self._data
    
    def delete(self, key: str) -> None:
        """
        Delete a key.
        
        Args:
            key: Storage key
        """
        if key in self._data:
            del self._data[key]
    
    def clear(self) -> None:
        """Clear all data"""
        self._data.clear()

