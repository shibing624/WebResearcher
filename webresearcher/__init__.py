# -*- coding: utf-8 -*-
"""
WebResearcher: An Iterative Deep-Research Agent

A powerful research agent implementing the IterResearch paradigm,
featuring unbounded reasoning capability through iterative synthesis.

@author: XuMing(xuming624@qq.com)
"""

__version__ = "0.2.5"
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

from webresearcher.web_researcher_agent import (
    WebResearcherAgent,
    ResearchRound,
    TOOL_MAP,
)

from webresearcher.web_weaver_agent import (
    WebWeaverAgent,
    WebWeaverPlanner,
    WebWeaverWriter,
)

from webresearcher.tts_agent import (
    TestTimeScalingAgent,
)

from webresearcher.react_agent import (
    ReactAgent,
)

from webresearcher.tool_memory import (
    MemoryBank,
    RetrieveTool,
)

from webresearcher.tool_planner_search import PlannerSearchTool
from webresearcher.tool_planner_scholar import PlannerScholarTool
from webresearcher.tool_planner_visit import PlannerVisitTool
from webresearcher.tool_planner_python import PlannerPythonTool
from webresearcher.tool_planner_file import PlannerFileTool

# Logger
from webresearcher.log import (
    logger,
    set_log_level,
    add_file_logger,
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
    "WebResearcherAgent",
    "ResearchRound",
    "WebWeaverAgent",
    "WebWeaverPlanner",
    "WebWeaverWriter",
    "TestTimeScalingAgent",
    "ReactAgent",
    "TOOL_MAP",
    
    # Base classes
    "Message",
    "MessageRole",
    "BaseTool",
    "BaseToolWithFileAccess",
    
    # Utilities
    "count_tokens",
    "extract_code",
    
    # Logger
    "logger",
    "set_log_level",
    "add_file_logger",
    
    # Tools
    "Search",
    "Visit",
    "Scholar",
    "PythonInterpreter",
    "FileParser",
    "MemoryBank",
    "RetrieveTool",
    
    # Planner Tools
    "PlannerSearchTool",
    "PlannerScholarTool",
    "PlannerVisitTool",
    "PlannerPythonTool",
    "PlannerFileTool",
]


