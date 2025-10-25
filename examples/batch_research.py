#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch Research Example

Demonstrates how to process multiple questions in batch mode.
"""
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from webresearcher import MultiTurnReactAgent


async def batch_research(questions, output_dir="./results"):
    """
    Process multiple research questions in batch.
    
    Args:
        questions: List of question strings or dicts with 'question' and 'ground_truth'
        output_dir: Directory to save results
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Configure agent
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            "temperature": 0.6,
            "top_p": 0.95,
        }
    }
    
    agent = MultiTurnReactAgent(
        llm_config=llm_config,
        function_list=["search", "google_scholar", "PythonInterpreter"]
    )
    
    # Process each question
    results = []
    for i, item in enumerate(questions, 1):
        # Parse item
        if isinstance(item, str):
            question = item
            ground_truth = None
        else:
            question = item.get('question', item)
            ground_truth = item.get('ground_truth') or item.get('answer')
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing {i}/{len(questions)}: {question[:100]}...")
        logger.info(f"{'='*80}")
        
        try:
            # Run research
            result = await agent.run(question)
            
            # Add metadata
            result['index'] = i
            result['ground_truth'] = ground_truth
            result['success'] = result.get('termination') == 'answer'
            
            results.append(result)
            
            # Save individual result
            output_file = output_path / f"result_{i:03d}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # Print summary
            print(f"\n✅ Question {i} completed")
            print(f"   Answer: {result['prediction'][:100]}...")
            if ground_truth:
                print(f"   Ground Truth: {ground_truth}")
            print(f"   Saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Question {i} failed: {e}")
            results.append({
                'index': i,
                'question': question,
                'error': str(e),
                'success': False
            })
    
    # Save summary
    summary = {
        'total': len(questions),
        'successful': sum(1 for r in results if r.get('success')),
        'failed': sum(1 for r in results if not r.get('success')),
        'results': results
    }
    
    summary_file = output_path / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Print final summary
    print(f"\n{'='*80}")
    print("BATCH RESEARCH SUMMARY")
    print(f"{'='*80}")
    print(f"Total Questions: {summary['total']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success Rate: {summary['successful']/summary['total']*100:.1f}%")
    print(f"\nResults saved to: {output_dir}/")
    
    return summary


async def main():
    """Example usage"""
    # Define questions to research
    questions = [
        {
            "question": "刘翔破纪录时候是多少岁?",
            "answer": "23岁差2天"
        },
        {
            "question": "What is the capital of France?",
            "answer": "Paris"
        },
        "Who invented the World Wide Web?",
    ]
    
    # Run batch research
    summary = await batch_research(questions, output_dir="./batch_results")
    
    return summary


if __name__ == "__main__":
    asyncio.run(main())

