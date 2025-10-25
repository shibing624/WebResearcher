# Changelog

All notable changes to WebResearcher will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-25

### Added
- Initial release of WebResearcher
- Implemented IterResearch paradigm for unbounded reasoning
- Core agent: `MultiTurnReactAgent` with iterative synthesis
- Test-Time Scaling (TTS) agent for enhanced accuracy
- Comprehensive tool suite:
  - Web search (via Serper API)
  - Webpage visiting and summarization
  - Google Scholar integration
  - Python code execution in sandbox
  - File parsing (PDF, DOCX, etc.)
- Command-line interface (`webresearcher` command)
- Full async/await support
- Custom base classes (removed qwen-agent dependency)
- Robust error handling and retry logic
- Token counting and context management
- PyPI package with proper setup.py and pyproject.toml

### Features
- **IterResearch Paradigm**: Discrete research rounds with workspace synthesis
- **Unbounded Reasoning**: Iterative report generation prevents context overflow
- **Flexible Tool Use**: Extensible BaseTool interface for custom tools
- **TTS Mode**: Optional parallel research with synthesis for critical questions
- **CLI Support**: Easy command-line usage for quick research tasks
- **Production Ready**: Comprehensive logging, error handling, and configuration

### Technical Highlights
- Zero external agent framework dependencies
- Pure Python 3.8+ implementation
- Async-first design for performance
- Type hints throughout
- Comprehensive documentation

## [Unreleased]

### Planned
- More example notebooks
- Video/audio analysis improvements
- Streaming output support
- Web UI interface
- More tool integrations
- Performance optimizations

---

[0.1.0]: https://github.com/shibing624/WebResearcher/releases/tag/v0.1.0

