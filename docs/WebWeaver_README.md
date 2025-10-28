# WebWeaver Agent

WebWeaver is a dual-agent research framework implementing the dynamic outline paradigm from the WebWeaver paper. It provides a more structured approach to research compared to the single-agent WebResearcher.

## Architecture

WebWeaver consists of three main components:

### 1. Memory Bank
A shared evidence storage that bridges the Planner and Writer agents:
- **Add Evidence**: Planner stores findings with citation IDs
- **Retrieve Evidence**: Writer fetches specific evidence by ID
- **Decoupled Storage**: Keeps agents focused on their specific tasks

### 2. Planner Agent
Explores research questions and builds a citation-grounded outline:
- **Actions**: 
  - `search`: Gather information from web
  - `write_outline`: Create/update research outline with citations
  - `terminate`: Finish planning phase
- **Output**: A structured outline with citation IDs linking to evidence

### 3. Writer Agent
Writes comprehensive reports section-by-section:
- **Actions**:
  - `retrieve`: Fetch evidence from Memory Bank
  - `write`: Write report sections with inline citations
  - `terminate`: Finish writing phase
- **Output**: A complete research report with proper citations

## Key Features

### Dynamic Outline
Unlike traditional static outlines, WebWeaver's outline evolves as new evidence is discovered:
1. Planner searches and discovers evidence
2. Each finding gets a unique citation ID
3. Outline is updated to incorporate new evidence
4. Process repeats until outline is comprehensive

### Citation-Grounded Reports
All claims in the final report are backed by specific evidence:
- Evidence is stored with full context in Memory Bank
- Writer retrieves only relevant evidence for each section
- Citations are embedded inline (e.g., `[cite:id_1]`)

### Hierarchical Workflow
The dual-agent design separates concerns:
- **Planner**: Focus on exploration and organization
- **Writer**: Focus on synthesis and presentation
- **Memory Bank**: Ensures consistency and traceability

## Usage

### Basic Usage

```python
import asyncio
from webresearcher import WebWeaverAgent

async def main():
    # Configure LLM
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            "temperature": 0.1,  # Low temperature for factual research
            "top_p": 0.95,
            "max_tokens": 10000,
        },
        "llm_timeout": 300.0,
    }
    
    # Initialize agent
    agent = WebWeaverAgent(llm_config=llm_config)
    
    # Run research
    question = "What are the main causes of climate change?"
    result = await agent.run(question)
    
    # Access results
    print("Final Outline:", result['final_outline'])
    print("Final Report:", result['final_report'])
    print("Memory Bank Size:", result['memory_bank_size'])

if __name__ == "__main__":
    asyncio.run(main())
```

### Command Line Interface

```bash
# Use WebWeaver mode
webresearcher "What are the causes of climate change?" --use-webweaver

# Save results to file
webresearcher "Research question" --use-webweaver --output report.json

# Verbose logging
webresearcher "Question" --use-webweaver --verbose
```

### Advanced Usage

See `examples/webweaver_usage.py` for more examples:
- Basic research
- Medical research (from WebWeaver paper)
- Comparison with WebResearcher

## Comparison with WebResearcher

| Feature | WebResearcher | WebWeaver |
|---------|---------------|-----------|
| Architecture | Single-agent | Dual-agent |
| Paradigm | IterResearch | Dynamic Outline |
| Memory | Stateless workspace | Memory Bank |
| Output | Direct answer | Outline + Report |
| Citations | Implicit | Explicit with IDs |
| Structure | Iterative synthesis | Hierarchical |
| Best for | Quick answers | Comprehensive reports |

## When to Use WebWeaver

Choose **WebWeaver** when you need:
- ✅ Long-form, comprehensive research reports
- ✅ Explicit citation tracking
- ✅ Structured outline with evidence mapping
- ✅ Reproducible research process
- ✅ Multi-section documents

Choose **WebResearcher** when you need:
- ✅ Quick, focused answers
- ✅ Simpler architecture
- ✅ Direct question-answer format
- ✅ Lower token usage
- ✅ Faster results

## Configuration

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional

# Optional
export SERPER_API_KEY="your-serper-key"  # For web search
export MAX_LLM_CALL_PER_RUN=100  # Max iterations per agent
export AGENT_TIMEOUT=600  # Timeout in seconds
```

### LLM Configuration

```python
llm_config = {
    "model": "gpt-4o",  # Recommended: GPT-4, Claude 3, or similar
    "generate_cfg": {
        "temperature": 0.1,  # 0.0-0.2 for factual research
        "top_p": 0.95,
        "max_tokens": 10000,
    },
    "llm_timeout": 300.0,
}
```

## Paper Reference

WebWeaver implements the dual-agent framework described in:
- **Paper**: WebWeaver (Section 3.2 - Planner, Section 3.3 - Writer)
- **Memory Bank**: Section 3.1.2
- **Dynamic Outline**: Section 3.2 (lines 242-265)
- **Citation Grounding**: Section 3.3 (lines 266-282)

## Extending WebWeaver

### Adding Custom Tools to Planner

```python
from webresearcher.tool_memory import MemoryBank
from webresearcher.base import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self, memory_bank: MemoryBank):
        self.memory_bank = memory_bank
        self.name = "my_tool"
        # ... implement call method
        
# Modify WebWeaverPlanner.__init__ to include your tool
```

### Custom Evidence Processing

```python
# Extend MemoryBank to add custom evidence processing
class CustomMemoryBank(MemoryBank):
    def add_evidence(self, content: str, summary: str) -> str:
        # Add custom processing (e.g., deduplication, filtering)
        processed_content = self.preprocess(content)
        return super().add_evidence(processed_content, summary)
```

## Troubleshooting

### Planner doesn't terminate
- Increase `MAX_LLM_CALL_PER_RUN`
- Check if the question is too broad
- Try a more capable model (e.g., GPT-4)

### Writer produces incomplete reports
- Ensure Planner created comprehensive outline
- Check Memory Bank has sufficient evidence
- Increase `max_tokens` in LLM config

### Memory Bank errors
- Check citation IDs are being generated correctly
- Verify evidence is being stored before retrieval
- Enable verbose logging with `--verbose`

## Contributing

See `CONTRIBUTING.md` for guidelines on extending WebWeaver with:
- New tools for Planner
- Custom evidence processors
- Alternative Writer strategies
- Different citation formats

## License

Apache 2.0 License - see LICENSE file for details.

