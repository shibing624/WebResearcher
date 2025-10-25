# WebResearcher Examples

This directory contains example scripts demonstrating various usage patterns of WebResearcher.

## Files

- `basic_usage.py` - Basic examples covering single-agent and TTS modes
- `custom_agent.py` - Building custom agents with custom tools
- `batch_research.py` - Processing multiple questions in batch

## Running Examples

```bash
# Make sure you have configured your .env file first
cd examples

# Run basic example
python basic_usage.py

# Run with verbose logging
python basic_usage.py --verbose
```

## Prerequisites

1. Install WebResearcher:
   ```bash
   pip install webresearcher
   ```

2. Configure environment variables in `.env`:
   ```bash
   OPENAI_API_KEY=your_key
   SERPER_API_KEY=your_key
   ```

3. Run the examples!

## Notes

- TTS mode examples are commented out by default to avoid high costs
- Uncomment them if you want to test Test-Time Scaling functionality
- Remember: TTS uses 3-5x more tokens than single-agent mode

