# WebResearcher

WebResearcher: Unleashing unbounded reasoning capability in Long-Horizon Agents

## Overview

WebResearcher is a Python-based research assistant that demonstrates multi-step reasoning capabilities for long-horizon tasks. It features an intuitive Gradio web interface for interactive research queries and analysis.

## Features

- 🔬 **Multi-Step Reasoning**: Break down complex research questions into manageable steps
- 🌐 **Gradio Web UI**: Beautiful, interactive web interface for research tasks
- 📊 **Research History**: Track and review past research queries
- ⚙️ **Configurable Models**: Choose from different reasoning models
- 🎯 **Step-by-Step Analysis**: Transparent reasoning process with detailed steps

## Installation

1. Clone the repository:
```bash
git clone https://github.com/shibing624/WebResearcher.git
cd WebResearcher
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Web Interface

Launch the Gradio web UI:

```bash
python -m webresearcher.app
```

Then open your browser and navigate to `http://localhost:7860`

Alternatively, you can use the demo script:

```bash
python examples/demo.py web
```

### Programmatic Usage

```python
from webresearcher import WebResearcher

# Create a researcher instance
researcher = WebResearcher(model="default", max_steps=10)

# Perform research
result = researcher.research("What are the key trends in artificial intelligence?")

# Access results
print(f"Query: {result['query']}")
print(f"Model: {result['model']}")
print(f"Timestamp: {result['timestamp']}")

# View reasoning steps
for step in result['steps']:
    print(f"Step {step['step']}: {step['action']}")
    print(f"  {step['detail']}")

# Get conclusion
print(result['conclusion'])

# View research history
history = researcher.get_history()
```

### Example Script

Run the basic example:

```bash
python examples/demo.py
```

## Web UI Features

The Gradio interface includes:

- **Research Tab**: 
  - Enter research questions
  - Select reasoning model
  - Configure max reasoning steps
  - View step-by-step analysis
  - See final conclusions

- **History Tab**: 
  - View all past research queries
  - Track timestamps and models used
  - Clear history when needed

- **Example Queries**: Pre-populated examples to get started quickly

## Project Structure

```
WebResearcher/
├── webresearcher/
│   ├── __init__.py          # Package initialization
│   ├── researcher.py        # Core research logic
│   └── app.py              # Gradio web interface
├── examples/
│   └── demo.py             # Usage examples
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Requirements

- Python 3.7+
- gradio >= 4.0.0

## Development

To contribute to WebResearcher:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Acknowledgments

WebResearcher demonstrates the power of multi-step reasoning in AI agents, providing a foundation for building more sophisticated long-horizon research assistants.
