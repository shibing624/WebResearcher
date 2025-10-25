"""
input:
    - query/goal: str
    - Docs: List[file]/List[url]
    - file type: 'pdf', 'docx', 'pptx', 'txt', 'html', 'csv', 'tsv', 'xlsx', 'xls', 'doc', 'zip', '.mp4', '.mov', '.avi', '.mkv', '.webm', '.mp3', '.wav', '.aac', '.ogg', '.flac'
output:
    - answer: str
    - useful_information: str
"""
import os
import json
import asyncio

from webresearcher.base import BaseTool
from webresearcher.file_tools.video_analysis import VideoAnalysis


async def video_analysis(params, **kwargs):
    """Modified video_analysis to handle multiple URLs"""
    print(params)
    files = params.get('files', [])
    prompt = params.get('prompt', '')

    # Ensure URLs are in a list

    # Process each URL
    results = []
    for file in files:
        try:
            # Create parameters for each URL
            single_url_params = json.dumps({
                'url': file,
                'prompt': prompt
            })
            # Call the original VideoAnalysis tool
            result = VideoAnalysis().call(single_url_params, **kwargs)
            results.append(f"# Video: {os.path.basename(file)}\n{result}")
        except Exception as e:
            results.append(f"# Error processing {os.path.basename(file)}: {str(e)}")

    return results


class VideoAgent(BaseTool):
    description = "Video/audio analysis with object detection, text extraction, scene understanding, and metadata analysis."
    parameters = [
        {
            'name': 'query',
            'type': 'string',
            'description': 'Detailed question/instruction for analysis.',
            'required': True
        },
        {
            'name': 'files',
            'type': 'array',
            'array_type': 'string',
            'description': 'The files to be analyzed.',
            'required': True
        }
    ]

    async def call(self, params):
        response = await video_analysis(params)
        return json.dumps(response, ensure_ascii=False)


if __name__ == "__main__":
    agent = VideoAgent()
    params = {
        'query': "Could you help me out with this assignment? Our professor sprung it on us at the end of class Friday, and I'm still trying to figure it out. The question he asked us was about an anagram. I've attached an audio recording of the question that he asked, so if you could please take a listen and give me the answer, I'd really appreciate the help. Please limit your response to the anagram text that could be generated from the original line which fulfills the professor's request, without any other commentary. Also, please don't include any punctuation in your response.",
        'files': ["datas/2b3ef98c-cc05-450b-a719-711aee40ac65.mp3"]
    }
    response = asyncio.run(agent.call(params))
    print(response)
