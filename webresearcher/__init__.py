# -*- coding: utf-8 -*-
"""
WebResearcher: An Iterative Deep-Research Agent

A powerful research agent implementing the IterResearch paradigm,
featuring unbounded reasoning capability through iterative synthesis.

@author: XuMing(xuming624@qq.com)
"""

__version__ = "0.1.1"
__author__ = "XuMing"
__email__ = "xuming624@qq.com"
__url__ = "https://github.com/shibing624/WebResearcher"
__license__ = "Apache-2.0"

# Core components
from webresearcher.base import (
    Message,
    MessageRole,
    BaseTool,
    BaseToolWithFileAccess,
    count_tokens,
    extract_code,
)

from webresearcher.react_agent import (
    MultiTurnReactAgent,
    ResearchRound,
)

from webresearcher.tts_agent import (
    TestTimeScalingAgent,
)

# Tools
from webresearcher.tool_search import Search
from webresearcher.tool_visit import Visit
from webresearcher.tool_scholar import Scholar
from webresearcher.tool_python import PythonInterpreter
from webresearcher.tool_file import FileParser

__all__ = [
    # Version
    "__version__",
    "__author__",
    "__email__",
    
    # Core classes
    "MultiTurnReactAgent",
    "ResearchRound",
    "TestTimeScalingAgent",
    
    # Base classes
    "Message",
    "MessageRole",
    "BaseTool",
    "BaseToolWithFileAccess",
    
    # Utilities
    "count_tokens",
    "extract_code",
    
    # Tools
    "Search",
    "Visit",
    "Scholar",
    "PythonInterpreter",
    "FileParser",
]


