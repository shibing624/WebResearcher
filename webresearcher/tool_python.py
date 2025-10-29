from typing import Dict, List, Optional, Union
import re
import sys
import io
import traceback
import json5
import os
import random
import time
from sandbox_fusion import run_code, RunCodeRequest
from requests.exceptions import Timeout

from webresearcher.base import BaseToolWithFileAccess, extract_code
from webresearcher.log import logger

SANDBOX_FUSION_ENDPOINTS = os.environ.get('SANDBOX_FUSION_ENDPOINTS', '').split(',')


def has_chinese_chars(texts: List[str]) -> bool:
    """Check if any text contains Chinese characters"""
    for text in texts:
        if any('\u4E00' <= char <= '\u9FFF' for char in text):
            return True
    return False


class PythonInterpreter(BaseToolWithFileAccess):
    name = "python"
    description = 'Execute Python code in a sandboxed environment. Use this to run Python code and get the execution results.\n**Make sure to use print() for any output you want to see in the results.**\nFor code parameters, use placeholders first, and then put the code within <code></code> XML tags, such as:\n<tool_call>\n{"purpose": <detailed-purpose-of-this-tool-call>, "name": <tool-name>, "arguments": {"code": ""}}\n<code>\nHere is the code.\n</code>\n</tool_call>\n'

    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute. Must be provided within <code></code> XML tags. Remember to use print() statements for any output you want to see.",
            }
        },
        "required": ["code"],
    }

    def __init__(self,
                 base_dir: Optional[str] = None,
                 safe_globals: Optional[dict] = None,
                 safe_locals: Optional[dict] = None):
        super().__init__()
        self.base_dir: str = base_dir if base_dir else os.path.curdir
        # Restricted global and local scope
        self.safe_globals: dict = safe_globals or {}
        self.safe_locals: dict = safe_locals or {}

    def run_python_code_locally(self, python_code: str) -> str:
        """
        Run Python code locally in the current environment (fallback when sandbox is unavailable).
        
        :param python_code: The code to run.
        :return: Execution result or error message.
        """
        logger.debug(f"Running code locally:\n\n{python_code}\n\n")
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout

        try:
            # Compile the code to check for syntax errors
            code = compile(python_code, '<string>', 'exec')
            namespace = {}
            # Execute the code
            exec(code, namespace)
            result = str(new_stdout.getvalue().strip())
            return f"stdout:\n{result}" if result else "Finished execution."
        except Exception as e:
            error = str(e)
            error_traceback = traceback.format_exc()
            logger.error(f"Error: {error}\n\nTraceback:\n{error_traceback}")
            return f"stderr:\nError: {error}\n\nTraceback:\n{error_traceback}"
        finally:
            sys.stdout = old_stdout
            new_stdout.close()

    @property
    def function(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
        }

    def call(self, params, files=None, timeout=10, **kwargs) -> str:
        try:
            # Extract code from params dict
            if isinstance(params, dict):
                code = params.get('code', '')
                if not code:
                    code = params.get('raw', '')
            else:
                code = str(params)

            # Extract code from triple backticks if present
            triple_match = re.search(r'```[^\n]*\n(.+?)```', code, re.DOTALL)
            if triple_match:
                code = triple_match.group(1)

            if not code.strip():
                return '[Python Interpreter Error]: Empty code.'

            # Check if endpoints are available, fallback to local execution
            if not SANDBOX_FUSION_ENDPOINTS or SANDBOX_FUSION_ENDPOINTS == ['']:
                logger.debug('No sandbox fusion endpoints available, falling back to local execution')
                return self.run_python_code_locally(code)

            last_error = None
            for attempt in range(2):
                endpoint = None  # Initialize endpoint
                try:
                    # Randomly sample an endpoint for each attempt
                    endpoint = random.choice(SANDBOX_FUSION_ENDPOINTS)
                    logger.debug(f"Attempt {attempt + 1}/2 using endpoint: {endpoint}")
                    logger.debug(f"Running code:\n{code}, \nendpoint: {endpoint}")

                    code_result = run_code(RunCodeRequest(code=code, language='python', run_timeout=timeout),
                                           max_attempts=1, client_timeout=timeout, endpoint=endpoint)
                    logger.debug(f"[Python] Code Result:{code_result}\nstdout:\n{code_result.run_result.stdout}")
                    result = []
                    if code_result.run_result.stdout:
                        result.append(f"stdout:\n{code_result.run_result.stdout}")
                    if code_result.run_result.stderr:
                        result.append(f"stderr:\n{code_result.run_result.stderr}")
                    if code_result.run_result.execution_time >= timeout - 1:
                        result.append(f"[PythonInterpreter Error] TimeoutError: Execution timed out.")
                    result = '\n'.join(result)
                    logger.debug('SUCCESS RUNNING TOOL')
                    return result if result.strip() else 'Finished execution.'

                except Timeout as e:
                    endpoint_info = f" on endpoint {endpoint}" if endpoint else ""
                    last_error = f'[Python Interpreter Error] TimeoutError: Execution timed out{endpoint_info}.'
                    logger.error(f"Timeout on attempt {attempt + 1}: {last_error}")
                    if attempt == 1:  # Last attempt (0-indexed, so 1 is the second attempt)
                        return last_error
                    continue

                except Exception as e:
                    endpoint_info = f" on endpoint {endpoint}" if endpoint else ""
                    last_error = f'[Python Interpreter Error]: {str(e)}{endpoint_info}'
                    logger.error(f"Error on attempt {attempt + 1}: {last_error}")
                    if attempt == 1:  # Last attempt
                        return last_error
                    continue

            return last_error if last_error else '[Python Interpreter Error]: All attempts failed.'

        except Exception as e:
            return f"[Python Interpreter Error]: {str(e)}"

    def call_specific_endpoint(self, params: Union[str, dict], endpoint: str, timeout: Optional[int] = 30,
                               **kwargs) -> tuple:
        """Test a specific endpoint directly"""
        try:
            if type(params) is str:
                params = json5.loads(params)
            code = params.get('code', '')
            if not code:
                code = params.get('raw', '')
            triple_match = re.search(r'```[^\n]*\n(.+?)```', code, re.DOTALL)
            if triple_match:
                code = triple_match.group(1)
        except Exception:
            code = extract_code(params)

        if not code.strip():
            return False, '[Python Interpreter Error]: Empty code.'

        try:
            start_time = time.time()
            code_result = run_code(RunCodeRequest(code=code, language='python', run_timeout=timeout),
                                   max_attempts=1, client_timeout=timeout, endpoint=endpoint)
            end_time = time.time()

            result = []
            if code_result.run_result.stdout:
                result.append(f"stdout:\n{code_result.run_result.stdout}")
            if code_result.run_result.stderr:
                result.append(f"stderr:\n{code_result.run_result.stderr}")

            result = '\n'.join(result)
            execution_time = end_time - start_time
            return True, result if result.strip() else 'Finished execution.', execution_time

        except Timeout as e:
            return False, f'[Python Interpreter Error] TimeoutError: Execution timed out.', None
        except Exception as e:
            return False, f'[Python Interpreter Error]: {str(e)}', None


if __name__ == '__main__':
    logger.info(f"Sandbox Fusion Endpoints: {SANDBOX_FUSION_ENDPOINTS}")
    interpreter = PythonInterpreter()
    code = """print("Hello, World!")\nfor i in range(5):\n    print(i)"""
    result = interpreter.call({'code': code})
    print("Result:", result)
