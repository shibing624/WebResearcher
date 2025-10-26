# -*- coding: utf-8 -*-
"""
WebResearcher Command Line Interface

Provides command-line access to WebResearcher functionality.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

from webresearcher.logger import logger
from webresearcher.agent import WebResearcherAgent
from webresearcher.tts_agent import TestTimeScalingAgent


def setup_logger(verbose: bool = False):
    """Configure logging"""
    logger.remove()
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")


async def run_research(args):
    """Run research agent"""
    # Load environment variables
    env_file = Path(args.env_file) if args.env_file else Path('.env')
    if env_file.exists():
        load_dotenv(env_file, override=True)
        logger.info(f"Loaded environment from: {env_file}")
    
    # Build LLM config
    llm_config = {
        "model": args.model,
        "generate_cfg": {
            'max_input_tokens': args.max_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "presence_penalty": args.presence_penalty,
            "model_thinking_type": args.thinking_type,
        }
    }
    
    # Parse function list
    function_list = args.tools.split(',') if args.tools else [
        "search", "google_scholar", "PythonInterpreter"
    ]
    
    # Create agent
    if args.use_tts:
        logger.info(f"Using Test-Time Scaling mode with {args.num_agents} agents")
        agent = TestTimeScalingAgent(
            llm_config=llm_config,
            function_list=function_list,
        )
        result = await agent.run(
            question=args.question,
            num_parallel_agents=args.num_agents
        )
        answer = result['final_synthesized_answer']
    else:
        logger.info("Using single-agent mode")
        agent = WebResearcherAgent(
            llm_config=llm_config,
            function_list=function_list,
        )
        result = await agent.run(args.question)
        answer = result['prediction']
    
    # Output results
    print("\n" + "="*80)
    print("RESEARCH RESULTS")
    print("="*80)
    print(f"Question: {args.question}")
    print(f"\nAnswer: {answer}")
    
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved detailed results to: {output_file}")
    
    return result


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        prog='webresearcher',
        description='WebResearcher: An Iterative Deep-Research Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic research question
  webresearcher "What is the capital of France?"
  
  # With custom model and tools
  webresearcher "刘翔破纪录时候是多少岁?" --model gpt-4o --tools search,google_scholar
  
  # Using Test-Time Scaling for higher accuracy
  webresearcher "Complex question" --use-tts --num-agents 3
  
  # Save detailed results
  webresearcher "Question" --output results.json
  
  # Verbose logging
  webresearcher "Question" --verbose

For more information: https://github.com/shibing624/WebResearcher
        """
    )
    
    parser.add_argument(
        'question',
        type=str,
        help='Research question to answer'
    )
    
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='gpt-4o',
        help='LLM model name (default: gpt-4o)'
    )
    
    parser.add_argument(
        '--temperature', '-t',
        type=float,
        default=0.6,
        help='Sampling temperature (default: 0.6)'
    )
    
    parser.add_argument(
        '--top-p',
        type=float,
        default=0.95,
        help='Nucleus sampling threshold (default: 0.95)'
    )
    
    parser.add_argument(
        '--presence-penalty',
        type=float,
        default=1.1,
        help='Presence penalty (default: 1.1)'
    )
    
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=32000,
        help='Maximum input tokens (default: 32000)'
    )
    
    parser.add_argument(
        '--thinking-type',
        type=str,
        choices=['enabled', 'disabled', 'auto'],
        default='enabled',
        help='Model thinking mode (default: enabled)'
    )
    
    parser.add_argument(
        '--tools',
        type=str,
        default='search,google_scholar,PythonInterpreter',
        help='Comma-separated list of tools to enable (default: search,google_scholar,PythonInterpreter)'
    )
    
    parser.add_argument(
        '--use-tts',
        action='store_true',
        help='Enable Test-Time Scaling mode (higher accuracy, 3-5x cost)'
    )
    
    parser.add_argument(
        '--num-agents',
        type=int,
        default=3,
        help='Number of parallel agents for TTS mode (default: 3)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file for detailed results (JSON format)'
    )
    
    parser.add_argument(
        '--env-file',
        type=str,
        help='Path to .env file (default: .env)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(args.verbose)
    
    logger.info(f"Model: {args.model} | Mode: {'TTS' if args.use_tts else 'Single'}")
    
    try:
        # Run research
        result = asyncio.run(run_research(args))
        return 0
    except KeyboardInterrupt:
        logger.warning("\nResearch interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

