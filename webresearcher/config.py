# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Config for WebResearcher
"""

import os


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

OBS_START = '<tool_response>'
OBS_END = '\n</tool_response>'

MAX_LLM_CALL_PER_RUN = int(os.getenv('MAX_LLM_CALL_PER_RUN', 100))
AGENT_TIMEOUT = int(os.getenv('AGENT_TIMEOUT', 600))
FILE_DIR = os.getenv('FILE_DIR', './files')
