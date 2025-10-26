import os
import json
from typing import Union, List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import http.client
from contextlib import contextmanager

from webresearcher.logger import logger
from webresearcher.base import BaseTool


SERPER_API_KEY = os.environ.get('SERPER_API_KEY')


class Scholar(BaseTool):
    name = "google_scholar"
    description = "Leverage Google Scholar to retrieve relevant information from academic publications. Accepts multiple queries."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "array",
                "items": {"type": "string", "description": "The search query."},
                "minItems": 1,
                "description": "The list of search queries for Google Scholar."
            },
        },
        "required": ["query"],
    }

    @contextmanager
    def _get_connection(self):
        """上下文管理器确保连接正确关闭"""
        conn = http.client.HTTPSConnection("google.serper.dev", timeout=30)
        try:
            yield conn
        finally:
            conn.close()

    def _make_request(self, conn: http.client.HTTPSConnection, query: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """发送请求并处理重试逻辑"""
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        for attempt in range(max_retries):
            try:
                conn.request("POST", "/scholar", payload, headers)
                response = conn.getresponse()
                
                if response.status == 200:
                    data = response.read()
                    return json.loads(data.decode("utf-8"))
                else:
                    logger.warning(f"HTTP {response.status} for query '{query}', attempt {attempt + 1}")
                    
            except (http.client.HTTPException, ConnectionError, json.JSONDecodeError) as e:
                logger.warning(f"Request failed for query '{query}', attempt {attempt + 1}: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error for query '{query}', attempt {attempt + 1}: {e}")
        
        return None

    def _format_result_item(self, page: Dict[str, Any], idx: int) -> str:
        """格式化单个搜索结果"""
        # 提取各个字段
        title = page.get('title', 'No title')
        year = page.get('year', '')
        publication_info = page.get('publicationInfo', '')
        snippet = page.get('snippet', '')
        cited_by = page.get('citedBy', '')
        pdf_url = page.get('pdfUrl', '')
        
        # 构建格式化字符串
        result_parts = [f"{idx}. [{title}]"]
        
        # 添加链接信息
        if pdf_url:
            result_parts[0] += f"({pdf_url})"
        else:
            result_parts[0] += "(no available link)"
        
        # 添加其他信息
        if publication_info:
            result_parts.append(f"Publication: {publication_info}")
        if year:
            result_parts.append(f"Year: {year}")
        if cited_by:
            result_parts.append(f"Cited by: {cited_by}")
        if snippet:
            # 清理snippet中的无用内容
            clean_snippet = snippet.replace("Your browser can't play this video.", "").strip()
            if clean_snippet:
                result_parts.append(clean_snippet)
        
        return "\n".join(result_parts)

    def google_scholar_with_serp(self, query: str) -> str:
        """使用Serper API搜索Google Scholar"""
        if not SERPER_API_KEY:
            return "Error: SERPER_API_KEY environment variable is not set."
        
        if not query or not query.strip():
            return "Error: Query cannot be empty."
        
        query = query.strip()
        logger.debug(f"Searching Google Scholar for: '{query}'")
        
        try:
            with self._get_connection() as conn:
                results = self._make_request(conn, query)
                
                if not results:
                    return f"Google Scholar search failed for query: '{query}'. Please try again later."
                
                if "organic" not in results or not results["organic"]:
                    return f"No results found for query: '{query}'. Try using a more general query."
                
                # 格式化结果
                formatted_results = []
                for idx, page in enumerate(results["organic"], 1):
                    formatted_result = self._format_result_item(page, idx)
                    formatted_results.append(formatted_result)
                
                result_count = len(formatted_results)
                header = f"Google Scholar search for '{query}' found {result_count} results:\n\n## Scholar Results\n"
                
                return header + "\n\n".join(formatted_results)
                
        except Exception as e:
            logger.error(f"Unexpected error during Google Scholar search for '{query}': {e}")
            return f"An error occurred while searching for '{query}'. Please try again."

    def call(self, params: Union[str, dict], **kwargs) -> str:
        # assert GOOGLE_SEARCH_KEY is not None, "Please set the IDEALAB_SEARCH_KEY environment variable."
        try:
            params = self._verify_json_format_args(params)
            query = params["query"]
        except:
            return "[google_scholar] Invalid request format: Input must be a JSON object containing 'query' field"

        if isinstance(query, str):
            response = self.google_scholar_with_serp(query)
        else:
            assert isinstance(query, List)
            with ThreadPoolExecutor(max_workers=3) as executor:

                response = list(executor.map(self.google_scholar_with_serp, query))
            response = "\n=======\n".join(response)
        return response


# add demo
if __name__ == '__main__':
    print("SERPER_API_KEY:", SERPER_API_KEY)
    tool = Scholar()
    print(tool)
    params = {
        "query": [
            "下次奥运会在哪里举办",
        ]
    }
    r = tool.call(params)
    print(r)
